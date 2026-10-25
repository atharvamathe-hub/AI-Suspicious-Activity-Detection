
from src.utils.geometry import calculate_iou
from src.config.settings import (
    FIGHT_IOU_THRESHOLD,
    FIGHT_SPEED_THRESHOLD,
)

# Require stronger overlap than the original 0.15 threshold.
MIN_FIGHT_IOU = max(FIGHT_IOU_THRESHOLD, 0.25)


def detect_fight(person1, person2):
    box1 = person1["bbox"]
    box2 = person2["bbox"]

    iou = calculate_iou(box1, box2)

    speed1 = float(person1.get("speed", 0.0))
    speed2 = float(person2.get("speed", 0.0))

    overlapping = iou >= MIN_FIGHT_IOU

    both_moving_fast = (
        speed1 > FIGHT_SPEED_THRESHOLD
        and speed2 > FIGHT_SPEED_THRESHOLD
    )

    if not (overlapping and both_moving_fast):
        return None

    return {
        "detected": True,
        "activity": "FIGHT",
        "person1_id": person1["id"],
        "person2_id": person2["id"],
        "iou": iou,
        "speed1": speed1,
        "speed2": speed2,
    }
