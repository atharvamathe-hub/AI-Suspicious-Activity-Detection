import math


def calculate_iou(box1, box2):
    """
    Calculate Intersection over Union (IoU)
    between two bounding boxes.

    Box format:
    [x1, y1, x2, y2]
    """

    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])

    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection_width = max(0, x2 - x1)
    intersection_height = max(0, y2 - y1)

    intersection_area = (
        intersection_width * intersection_height
    )

    if intersection_area == 0:
        return 0.0

    box1_area = (
        (box1[2] - box1[0]) *
        (box1[3] - box1[1])
    )

    box2_area = (
        (box2[2] - box2[0]) *
        (box2[3] - box2[1])
    )

    union_area = box1_area + box2_area - intersection_area

    if union_area == 0:
        return 0.0

    return intersection_area / union_area


def calculate_center(box):
    """
    Return center point of bounding box.
    """

    x1, y1, x2, y2 = box

    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    return center_x, center_y


def calculate_distance(box1, box2):
    """
    Calculate Euclidean distance between
    the centers of two bounding boxes.
    """

    center1 = calculate_center(box1)
    center2 = calculate_center(box2)

    return math.sqrt(
        (center1[0] - center2[0]) ** 2 +
        (center1[1] - center2[1]) ** 2
    )