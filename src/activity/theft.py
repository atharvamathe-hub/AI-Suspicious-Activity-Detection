
from collections import defaultdict, deque
from math import hypot

from src.utils.geometry import calculate_center


class TheftDetector:
    """Detect suspicious removal of a previously stationary object."""

    TARGET_CLASSES = {
        "backpack", "handbag", "suitcase", "cell phone"
    }

    STATIONARY_FRAMES = 12
    MOVEMENT_PIXELS = 35.0
    PERSON_DISTANCE_PIXELS = 180.0
    HISTORY_LENGTH = 24
    STALE_FRAMES = 90
    ALERT_COOLDOWN_FRAMES = 90

    def __init__(self):
        self.frame_number = 0
        self.object_history = defaultdict(
            lambda: deque(maxlen=self.HISTORY_LENGTH)
        )
        self.stationary_counts = defaultdict(int)
        self.stationary_positions = {}
        self.last_object_seen = {}
        self.last_alert_frame = {}

    @staticmethod
    def _distance(a, b):
        return hypot(a[0] - b[0], a[1] - b[1])

    def update(self, persons, objects):
        self.frame_number += 1
        if self.frame_number % 15 == 0:
            print(
                "[THEFT DEBUG] Objects:",
                [
                    (o.get("id"), o.get("class"), o.get("bbox"))
                    for o in objects
                ],
    )
        candidates = []

        for obj in objects:
            object_id = obj.get("id")
            object_class = str(obj.get("class", "")).lower()

            if object_id is None or object_class not in self.TARGET_CLASSES:
                continue

            object_id = int(object_id)
            center = calculate_center(obj["bbox"])
            history = self.object_history[object_id]
            previous = history[-1] if history else None

            history.append(center)
            self.last_object_seen[object_id] = self.frame_number

            if previous is None:
                self.stationary_counts[object_id] = 1
                self.stationary_positions[object_id] = center
                continue

            baseline = self.stationary_positions.get(object_id, previous)
            step = self._distance(center, previous)
            displacement = self._distance(center, baseline)

            if step <= 4 and displacement <= 12:
                self.stationary_counts[object_id] += 1
            elif self.stationary_counts[object_id] < self.STATIONARY_FRAMES:
                self.stationary_counts[object_id] = 0
                self.stationary_positions[object_id] = center

            stationary = (
                self.stationary_counts[object_id] >= self.STATIONARY_FRAMES
            )

            if self.frame_number % 5 == 0:
                print(
                    f"[THEFT DEBUG] id={object_id} "
                    f"class={object_class} "
                    f"stationary_frames={self.stationary_counts[object_id]} "
                    f"displacement={displacement:.1f}px "
                    f"stationary={stationary} "
                    f"persons={len(persons)}"
                )

            # Measure movement from the established baseline.
            if not stationary or displacement < self.MOVEMENT_PIXELS:
                continue

            nearest_person = None
            nearest_distance = float("inf")

            for person in persons:
                if person.get("id") is None:
                    continue

                person_center = calculate_center(person["bbox"])
                distance = self._distance(center, person_center)

                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_person = person

            if (
                nearest_person is None
                or nearest_distance > self.PERSON_DISTANCE_PIXELS
            ):
                continue

            last_alert = self.last_alert_frame.get(object_id, -10**9)
            if (
                self.frame_number - last_alert
                < self.ALERT_COOLDOWN_FRAMES
            ):
                continue

            self.last_alert_frame[object_id] = self.frame_number

            candidates.append({
                "detected": True,
                "activity": "THEFT",
                "person_id": int(nearest_person["id"]),
                "object_id": object_id,
                "object_class": object_class,
                "distance": nearest_distance,
                "evidence": "STATIONARY_OBJECT_MOVED_NEAR_PERSON",
                "message": "Suspicious object removal",
            })

        for object_id, last_seen in list(self.last_object_seen.items()):
            if self.frame_number - last_seen > self.STALE_FRAMES:
                self.last_object_seen.pop(object_id, None)
                self.object_history.pop(object_id, None)
                self.stationary_counts.pop(object_id, None)
                self.stationary_positions.pop(object_id, None)
                self.last_alert_frame.pop(object_id, None)

        return candidates


def detect_theft(person, obj):
    """Legacy compatibility helper; proximity alone is not theft evidence."""
    return None
