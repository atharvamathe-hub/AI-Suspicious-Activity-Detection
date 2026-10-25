def extract_tracks(result):

    tracks = []

    if result.boxes is None:
        return tracks

    names = result.names

    for box in result.boxes:

        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0]
        )

        confidence = float(box.conf[0])

        class_id = int(box.cls[0])

        class_name = names[class_id]

        track_id = None

        if box.id is not None:
            track_id = int(box.id[0])

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        tracks.append({
            "id": track_id,
            "class": class_name,
            "class_id": class_id,
            "confidence": confidence,
            "bbox": [x1, y1, x2, y2],
            "center": [center_x, center_y]
        })

    return tracks



from src.config.settings import (
    PERSON_CLASS,
    OBJECT_CLASSES,
    WEAPON_CLASSES
)


def classify_tracks(tracks):

    persons = []
    objects = []
    weapons = []

    for track in tracks:

        class_name = track["class"]

        if class_name == PERSON_CLASS:

            persons.append(track)

        elif class_name in WEAPON_CLASSES:

            weapons.append(track)

        elif class_name in OBJECT_CLASSES:

            objects.append(track)

    return persons, objects, weapons