import json
from pathlib import Path

import cv2
from ultralytics import YOLO


FACE_MODEL_PATH = Path(
    "/Users/atharvashyammathe/Desktop/OpenCV/yolo26n-face.pt"
)

LBPH_MODEL_PATH = Path(
    "/Users/atharvashyammathe/Desktop/OpenCV/Face_Detection/"
    "face_recogn/face_recognizer.yml"
)

LABELS_PATH = Path(
    "/Users/atharvashyammathe/Desktop/OpenCV/Face_Detection/"
    "face_recogn/labels.json"
)

FACE_SIZE = (200, 200)


class FaceRecognizer:
    def __init__(self, threshold=75, confidence=0.30):
        for path in (FACE_MODEL_PATH, LBPH_MODEL_PATH, LABELS_PATH):
            if not path.is_file():
                raise FileNotFoundError(
                    f"Required face recognition file not found: {path}"
                )

        if not hasattr(cv2, "face"):
            raise RuntimeError(
                "OpenCV face module unavailable. Install "
                "opencv-contrib-python in the active environment."
            )

        self.detector = YOLO(str(FACE_MODEL_PATH))

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.recognizer.read(str(LBPH_MODEL_PATH))

        with LABELS_PATH.open("r", encoding="utf-8") as file:
            raw_labels = json.load(file)

        self.labels = {
            int(key): str(value) for key, value in raw_labels.items()
        }

        self.threshold = float(threshold)
        self.confidence = float(confidence)

    def recognize(self, frame):
        results = self.detector.predict(
            frame,
            conf=self.confidence,
            verbose=False
        )

        detections = []

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                x1, y1, x2, y2 = map(
                    int, box.xyxy[0].cpu().tolist()
                )

                height, width = frame.shape[:2]
                x1 = max(0, min(x1, width - 1))
                y1 = max(0, min(y1, height - 1))
                x2 = max(0, min(x2, width))
                y2 = max(0, min(y2, height))

                if x2 <= x1 or y2 <= y1:
                    continue

                face = frame[y1:y2, x1:x2]

                if face.size == 0:
                    continue

                gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                normalized = cv2.resize(gray, FACE_SIZE)

                label_id, distance = self.recognizer.predict(normalized)

                if distance <= self.threshold:
                    name = self.labels.get(label_id, "Unknown")
                else:
                    name = "Unknown"

                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "name": name,
                    "distance": float(distance),
                })

        return detections
