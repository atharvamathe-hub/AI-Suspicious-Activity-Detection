import cv2
import os
from collections import deque
from datetime import datetime


class EventRecorder:
    def __init__(
        self,
        output_dir="output/clips",
        pre_event_seconds=3,
        post_event_seconds=3,
    ):
        self.output_dir = output_dir
        self.pre_event_seconds = pre_event_seconds
        self.post_event_seconds = post_event_seconds
        self.buffer = deque()
        self.recording = False
        self.current_event = None
        self.frames = []
        self.remaining_post_frames = 0
        os.makedirs(self.output_dir, exist_ok=True)

    def update(self, frame, event, fps):
        fps = fps if fps > 0 else 30.0
        max_buffer_frames = max(1, int(fps * self.pre_event_seconds))

        self.buffer.append(frame.copy())
        while len(self.buffer) > max_buffer_frames:
            self.buffer.popleft()

        detected = bool(event and event.get("detected"))
        activity = event.get("activity") if detected else None

        if detected:
            if not self.recording:
                self.recording = True
                self.current_event = activity or "SUSPICIOUS_ACTIVITY"
                self.frames = list(self.buffer)
                print(f"[EVENT] Recording {self.current_event} incident...")
            else:
                # Avoid switching activity folders mid-recording.
                self.frames.append(frame.copy())

            # Reset the post-event countdown while evidence continues.
            self.remaining_post_frames = int(
                fps * self.post_event_seconds
            )
            return None

        if self.recording:
            self.frames.append(frame.copy())
            self.remaining_post_frames -= 1

            if self.remaining_post_frames <= 0:
                saved_path = self.save_clip(fps)
                self._reset_recording()
                return saved_path

        return None

    def save_clip(self, fps):
        if not self.frames:
            return None

        activity = (self.current_event or "SUSPICIOUS_ACTIVITY").lower()
        activity_dir = os.path.join(self.output_dir, activity)
        os.makedirs(activity_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_path = os.path.join(
            activity_dir, f"{activity}_{timestamp}.mp4"
        )

        height, width = self.frames[0].shape[:2]
        writer = cv2.VideoWriter(
            output_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )

        try:
            if not writer.isOpened():
                raise RuntimeError(f"Could not create clip: {output_path}")
            for frame in self.frames:
                # Ensure all frames match the first frame's dimensions.
                if frame.shape[:2] != (height, width):
                    frame = cv2.resize(frame, (width, height))
                writer.write(frame)
        finally:
            writer.release()

        print(f"[SAVED] Event clip: {output_path}")
        return output_path

    def _reset_recording(self):
        self.recording = False
        self.current_event = None
        self.frames = []
        self.remaining_post_frames = 0

    def finish(self, fps):
        """Save an active clip once when the application exits."""
        if not self.recording or not self.frames:
            return None

        saved_path = self.save_clip(fps)
        self._reset_recording()
        return saved_path