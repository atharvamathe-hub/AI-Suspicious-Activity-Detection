VIDEO_SOURCE = (
    "rtsp://YOUR_USERNAME:YOUR_NEW_PASSWORD@YOUR_CAMERA_IP:554/ch1/main"
)

CAMERA_INDEX = 0

MODEL_PATH = "models/yolov26n.pt"

CONFIDENCE_THRESHOLD = 0.25

WINDOW_NAME = "AI Suspicious Activity Detection"

# --------------------------------------------------
# YOLO classes
# --------------------------------------------------

PERSON_CLASS = "person"

# Classes we will consider as general objects
OBJECT_CLASSES = {
    "backpack",
    "handbag",
    "suitcase",
    "cell phone",
}

# Weapon classes
# The standard YOLOv8 COCO model does NOT contain
# knife/gun classes, so this remains empty for now.
WEAPON_CLASSES = set()

# --------------------------------------------------
# Suspicious activity thresholds
# --------------------------------------------------

# Theft
THEFT_IOU_THRESHOLD = 0.30
THEFT_DISTANCE_THRESHOLD = 100.0

# Fight
FIGHT_IOU_THRESHOLD = 0.15
FIGHT_SPEED_THRESHOLD = 10.0

# Weapon
WEAPON_IOU_THRESHOLD = 0.30
WEAPON_DISTANCE_THRESHOLD = 100.0