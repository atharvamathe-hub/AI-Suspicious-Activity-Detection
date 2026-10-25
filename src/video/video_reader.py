
import os
import time
import threading
import cv2


class VideoReader:

    def __init__(self, source):
        self.source = source
        self.is_rtsp = (
            isinstance(source, str)
            and source.lower().startswith("rtsp://")
        )

        # Prefer TCP for RTSP streams to reduce packet-loss artifacts.
        if self.is_rtsp:
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                "rtsp_transport;tcp"
            )

        # Explicitly use FFmpeg for RTSP.
        if self.is_rtsp:
            self.cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        else:
            self.cap = cv2.VideoCapture(source)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Unable to open video source: {source}"
            )

        # Keep the capture buffer small where supported.
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self._lock = threading.Lock()
        self._latest_frame = None
        self._latest_success = False
        self._stopped = False
        self._thread = None
        self._last_read_time = time.monotonic()

        if self.is_rtsp:
            self._thread = threading.Thread(
                target=self._capture_loop,
                daemon=True
            )
            self._thread.start()

    def _capture_loop(self):
        """Continuously read RTSP frames; retain only the newest."""
        while not self._stopped:
            success, frame = self.cap.read()

            if success and frame is not None:
                with self._lock:
                    self._latest_frame = frame
                    self._latest_success = True
                    self._last_read_time = time.monotonic()
            else:
                # Avoid a busy loop if the stream stops delivering frames.
                with self._lock:
                    self._latest_success = False
                time.sleep(0.01)

    def read(self):
        # Preserve normal sequential reading for video files.
        if not self.is_rtsp:
            return self.cap.read()

        with self._lock:
            if self._latest_frame is None:
                return False, None

            # Return a copy so callers cannot modify the shared frame.
            return True, self._latest_frame.copy()

    def get_fps(self):
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        return fps if fps > 0 else 15.0

    def get_width(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    def get_height(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def get_frame_count(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def release(self):
        self._stopped = True

        if self._thread is not None:
            self._thread.join(timeout=2.0)

        self.cap.release()

    def show(self, window_name="Video"):
        try:
            while True:
                success, frame = self.read()

                if not success:
                    if self.is_rtsp:
                        time.sleep(0.01)
                        continue
                    break

                cv2.imshow(window_name, frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            self.release()
            cv2.destroyAllWindows()
