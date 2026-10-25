from src.utils.geometry import (
    calculate_iou,
    calculate_distance
)

from src.config.settings import (
    WEAPON_IOU_THRESHOLD,
    WEAPON_DISTANCE_THRESHOLD
)


def detect_weapon(person, weapon):

    person_box = person["bbox"]
    weapon_box = weapon["bbox"]

    iou = calculate_iou(
        person_box,
        weapon_box
    )

    distance = calculate_distance(
        person_box,
        weapon_box
    )

    detected = (
        distance < WEAPON_DISTANCE_THRESHOLD
        or
        iou > WEAPON_IOU_THRESHOLD
    )

    if detected:

        return {
            "detected": True,
            "activity": "WEAPON",
            "person_id": person["id"],
            "weapon_id": weapon["id"],
            "iou": iou,
            "distance": distance
        }

    return None