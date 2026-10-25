import cv2
import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from dotenv import load_dotenv
from src.recognition.face_recognizer import FaceRecognizer
from src.alerts.telegram_alert import TelegramAlert
from src.video.video_reader import VideoReader
from src.detection.detector import ObjectDetector
from src.tracking.object_tracker import ObjectTracker
from src.tracking.tracking_utils import extract_tracks, classify_tracks
from src.tracking.movement_tracker import MovementTracker
from src.activity.suspicious_activity import SuspiciousActivityDetector
from src.events.event_recorder import EventRecorder


load_dotenv()

VIDEO_PATH = os.getenv(
    "EZVIZ_RTSP_URL",
    "input/videos/fight/fight.mp4"
)
VIDEO_PATH =  0
MODEL_PATH = "models/yolo26n.pt"

EVENT_GRACE_SECONDS = 3.0
DIAGNOSTIC_INTERVAL = 30


def send_telegram_evidence(saved_path, telegram_alert):
    """Send one message and one video for a finalized event clip."""
    if not saved_path:
        return

    activity = os.path.basename(
        os.path.dirname(saved_path)
    ).upper()

    try:
        telegram_alert.send_message(activity, saved_path)
        telegram_alert.send_video(saved_path, activity)
        print(f"[TELEGRAM] Sent one {activity} incident alert.")

    except (requests.RequestException, OSError, RuntimeError) as error:
        print(f"[TELEGRAM ERROR] {error}")


def smooth_event(raw_event, state, now):
    """Keep an incident active through brief detection gaps."""

    detected = bool(raw_event and raw_event.get("detected"))
    activity = raw_event.get("activity") if detected else None

    if detected:
        if not state["active"]:
            state["activity"] = activity
            state["active"] = True
            print(f"[INCIDENT] Started {activity} incident.")

        elif activity != state["activity"]:
            # Do not change incident type in the middle of a clip.
            activity = state["activity"]

        state["last_seen"] = now

        return {
            "detected": True,
            "activity": state["activity"]
        }

    if (
        state["active"]
        and now - state["last_seen"] < EVENT_GRACE_SECONDS
    ):
        return {
            "detected": True,
            "activity": state["activity"]
        }

    if state["active"]:
        print(f"[INCIDENT] {state['activity']} incident ended.")
        state["active"] = False
        state["activity"] = None
        state["last_seen"] = 0.0

    return {"detected": False, "activity": None}



def associate_faces_with_persons(face_detections, persons):
    """
    Associate a face with a tracked person when its center lies in the
    upper portion of that person's bounding box. Returns face detections
    enriched with person_id; ambiguous faces remain unassigned.
    """
    associated = []

    for face in face_detections:
        fx1, fy1, fx2, fy2 = face["bbox"]
        face_cx = (fx1 + fx2) / 2.0
        face_cy = (fy1 + fy2) / 2.0
        face_height = max(1.0, fy2 - fy1)

        candidates = []
        for person in persons:
            px1, py1, px2, py2 = person["bbox"]
            person_width = max(1.0, px2 - px1)
            person_height = max(1.0, py2 - py1)

            # A face should be in the upper 55% of the person box.
            if not (px1 <= face_cx <= px2):
                continue
            if not (py1 <= face_cy <= py1 + 0.55 * person_height):
                continue

            # Reject faces implausibly large relative to the person box.
            if face_height > 0.65 * person_height:
                continue

            person_cx = (px1 + px2) / 2.0
            normalized_x = abs(face_cx - person_cx) / person_width
            normalized_y = max(0.0, face_cy - py1) / person_height
            score = normalized_x + normalized_y

            candidates.append((score, person["id"]))

        enriched = dict(face)
        enriched["person_id"] = min(candidates)[1] if candidates else None
        associated.append(enriched)

    return associated


def update_identity_memory(face_detections, identity_history, identity_last_seen,
                           frame_count, max_age_frames=60):
    """
    Update identity votes only on fresh face-inference frames, not on
    cached frames. Return stable names keyed by person track ID.
    """
    for face in face_detections:
        person_id = face.get("person_id")
        name = face.get("name", "Unknown")

        if person_id is None or name == "Unknown":
            continue

        person_id = int(person_id)
        if person_id not in identity_history:
            identity_history[person_id] = deque(maxlen=5)

        identity_history[person_id].append(name)
        identity_last_seen[person_id] = frame_count

    # Forget stale track IDs so an old name cannot be reused indefinitely.
    stale_ids = [
        person_id
        for person_id, last_seen in identity_last_seen.items()
        if frame_count - last_seen > max_age_frames
    ]
    for person_id in stale_ids:
        identity_last_seen.pop(person_id, None)
        identity_history.pop(person_id, None)

    stable_names = {}
    for person_id, votes in identity_history.items():
        if votes:
            # Most common recent recognized label; deterministic tie-break.
            counts = {}
            for name in votes:
                counts[name] = counts.get(name, 0) + 1
            stable_names[person_id] = max(
                counts,
                key=lambda name: (counts[name], name)
            )

    return stable_names

def main():
    print("=" * 60)
    print("AI SUSPICIOUS ACTIVITY DETECTION")
    print("PHASE 2 - SUSPICIOUS ACTIVITY DETECTION")
    print("=" * 60)

    video = VideoReader(VIDEO_PATH)

    fps = video.get_fps()
    if fps <= 0:
        fps = 30.0

    print(f"Video Source : {VIDEO_PATH}")
    print(
        f"Resolution   : "
        f"{video.get_width()} x {video.get_height()}"
    )
    print(f"Source FPS   : {fps:.2f}")

    detector = ObjectDetector(MODEL_PATH)

    face_recognizer = FaceRecognizer(
            threshold=75,
            confidence=0.30
    )

    print("[FACE] Face recognition models loaded.")

    tracker = ObjectTracker(detector.model)
    movement_tracker = MovementTracker()
    suspicious_detector = SuspiciousActivityDetector()

    event_recorder = EventRecorder(
        output_dir="output/clips",
        pre_event_seconds=3,
        post_event_seconds=3,
    )

    telegram_alert = TelegramAlert()
    telegram_executor = ThreadPoolExecutor(max_workers=1)

    incident_state = {
        "active": False,
        "activity": None,
        "last_seen": 0.0,
    }

    frame_count = 0
    processing_start = time.perf_counter()
    last_read_warning = 0.0

    # Cache face detections between recognition runs (every 3 frames).
    face_detections = []
    identity_history = {}
    identity_last_seen = {}
    stable_names = {}

    print("\nStarting detection...")
    print("Press Q to exit.\n")
    try:
        while True:
            success, frame = video.read()

            if not success or frame is None:
                if VIDEO_PATH.lower().startswith("rtsp://"):
                    time.sleep(0.01)
                    continue

                print("\n[VIDEO] Video file ended or frame read failed.")
                break

            # Log frame properties once, then periodically report
            # processing performance.
            if frame_count == 0:
                print(
                    f"[FRAME] Shape: {frame.shape}, "
                    f"dtype: {frame.dtype}, "
                    f"contiguous: "
                    f"{frame.flags['C_CONTIGUOUS']}"
                )

            # Keep a clean copy for event recording.
            # Detection overlays will be drawn on another copy.
            recording_frame = frame.copy()
            # Run face recognition every 3 frames to reduce processing overhead.
            if frame_count % 3 == 0:
                face_detections = face_recognizer.recognize(frame)

            # Measure the expensive detection/tracking stage.
            inference_start = time.perf_counter()

            result = tracker.track(frame)

            inference_seconds = (
                time.perf_counter() - inference_start
            )

            tracks = extract_tracks(result)
            persons, objects, weapons = classify_tracks(tracks)

            for person in persons:
                person["speed"] = (
                    movement_tracker.calculate_speed(person)
                )

            # Link face detections to person-track IDs using bounding boxes.
            associated_faces = associate_faces_with_persons(
                face_detections, persons
            )

            # Face detections are refreshed every 3 frames. Only add a new
            # identity vote on those frames, not on every cached display frame.
            if frame_count % 3 == 0:
                stable_names = update_identity_memory(
                    associated_faces,
                    identity_history,
                    identity_last_seen,
                    frame_count
                )

            raw_event = suspicious_detector.detect(
                persons,
                objects,
                weapons
            )

            event = smooth_event(
                raw_event,
                incident_state,
                time.monotonic()
            )

            # Record the clean camera image, not the display overlays.
            saved_path = event_recorder.update(
                recording_frame,
                event,
                fps
            )

            if saved_path:
                telegram_executor.submit(
                    send_telegram_evidence,
                    saved_path,
                    telegram_alert
                )

            # Draw overlays on a separate image.
            display_frame = recording_frame.copy()

            for person in persons:
                x1, y1, x2, y2 = person["bbox"]
                person_name = stable_names.get(person["id"], "Unknown")
                label = (
                    f"Person ID:{person['id']} | {person_name} "
                    f"{person['confidence']:.2f}"
                )

                cv2.rectangle(
                    display_frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )
                cv2.putText(
                    display_frame,
                    label,
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

            for obj in objects:
                x1, y1, x2, y2 = obj["bbox"]
                label = (
                    f"{obj['class']} ID:{obj['id']} "
                    f"{obj['confidence']:.2f}"
                )

                cv2.rectangle(
                    display_frame,
                    (x1, y1),
                    (x2, y2),
                    (255, 255, 0),
                    2
                )
                cv2.putText(
                    display_frame,
                    label,
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2
                )

            for weapon in weapons:
                x1, y1, x2, y2 = weapon["bbox"]
                label = (
                    f"{weapon['class']} ID:{weapon['id']} "
                    f"{weapon['confidence']:.2f}"
                )

                cv2.rectangle(
                    display_frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 255),
                    2
                )
                cv2.putText(
                    display_frame,
                    label,
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )

            # Draw face boxes; the associated person box shows the stable name.
            for face in associated_faces:
                x1, y1, x2, y2 = face["bbox"]
                person_id = face.get("person_id")
                name = (
                    stable_names.get(person_id, "Unknown")
                    if person_id is not None
                    else face.get("name", "Unknown")
                )
                color = (0, 255, 0) if name != "Unknown" else (0, 165, 255)

                cv2.rectangle(
                    display_frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2
                )
                cv2.putText(
                    display_frame,
                    name,
                    (x1, max(20, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

            cv2.putText(
                display_frame,
                f"Persons: {len(persons)}",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
            cv2.putText(
                display_frame,
                f"Objects: {len(objects)}",
                (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
            cv2.putText(
                display_frame,
                f"Weapons: {len(weapons)}",
                (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            if event["detected"]:
                status = f"{event['activity']} INCIDENT ACTIVE"
                color = (0, 0, 255)
            else:
                status = "STATUS: NORMAL"
                color = (0, 255, 0)

            cv2.putText(
                display_frame,
                status,
                (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2
            )
            frame
            frame_count += 1

            # Report performance every 30 frames, not every frame.
            if frame_count % DIAGNOSTIC_INTERVAL == 0:
                elapsed = time.perf_counter() - processing_start
                processing_fps = (
                    frame_count / elapsed if elapsed > 0 else 0
                )

                print(
                    f"[PERFORMANCE] "
                    f"YOLO/tracking: {inference_seconds:.3f}s "
                    f"| Processing FPS: {processing_fps:.2f}"
                )

            
            cv2.imshow(
                "AI Suspicious Activity Detection",
                display_frame
     
            )
            
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("\nExiting...")
                break

    finally:
        try:
            saved_path = event_recorder.finish(fps)

            if saved_path:
                telegram_executor.submit(
                    send_telegram_evidence,
                    saved_path,
                    telegram_alert
                )

        finally:
            video.release()
            cv2.destroyAllWindows()
            telegram_executor.shutdown(wait=True)
            print("System stopped.")


if __name__ == "__main__":
    main()
