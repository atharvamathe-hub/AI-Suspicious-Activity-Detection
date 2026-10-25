import cv2


def draw_detections(frame, result):

    boxes = result.boxes

    if boxes is None:
        return frame

    names = result.names

    for box in boxes:

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        confidence = float(box.conf[0])

        class_id = int(box.cls[0])

        class_name = names[class_id]

        label = f"{class_name} {confidence:.2f}"

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    return frame



def draw_tracking(frame, result):

    boxes = result.boxes

    if boxes is None:
        return frame

    names = result.names

    for box in boxes:

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        confidence = float(box.conf[0])

        class_id = int(box.cls[0])

        class_name = names[class_id]

        # Get tracking ID
        if box.id is not None:
            track_id = int(box.id[0])
            label = f"{class_name} ID:{track_id} {confidence:.2f}"
        else:
            label = f"{class_name} {confidence:.2f}"

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    return frame