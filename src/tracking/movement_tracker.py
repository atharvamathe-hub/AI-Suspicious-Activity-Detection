import math


class MovementTracker:

    def __init__(self):

        self.previous_positions = {}

    def calculate_speed(self, track):

        track_id = track["id"]
        center = track["center"]

        if track_id is None:
            return 0.0

        if track_id not in self.previous_positions:

            self.previous_positions[track_id] = center

            return 0.0

        previous = self.previous_positions[track_id]

        distance = math.sqrt(
            (center[0] - previous[0]) ** 2 +
            (center[1] - previous[1]) ** 2
        )

        self.previous_positions[track_id] = center

        return distance