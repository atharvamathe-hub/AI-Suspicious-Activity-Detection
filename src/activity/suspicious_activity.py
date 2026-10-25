from collections import defaultdict, deque

from src.activity.theft import TheftDetector
from src.activity.fight import detect_fight
from src.activity.weapon import detect_weapon


class SuspiciousActivityDetector:
    FIGHT_WINDOW_FRAMES = 10
    FIGHT_REQUIRED_HITS = 7

    def __init__(self):
        self.frame_number = 0
        self.fight_history = defaultdict(
            lambda: deque(maxlen=self.FIGHT_WINDOW_FRAMES)
        )
        self.theft_detector = TheftDetector()

    def detect(self, persons, objects, weapons):
        self.frame_number += 1
        candidates = []

        # Temporally confirmed fight evidence.
        for i in range(len(persons)):
            for j in range(i + 1, len(persons)):
                person1 = persons[i]
                person2 = persons[j]
                result = detect_fight(person1, person2)
                if result is None:
                    continue

                id1 = person1.get("id")
                id2 = person2.get("id")
                if id1 is None or id2 is None:
                    continue

                pair_key = tuple(sorted((id1, id2)))
                history = self.fight_history[pair_key]
                history.append(self.frame_number)

                while (
                    history
                    and self.frame_number - history[0] >= self.FIGHT_WINDOW_FRAMES
                ):
                    history.popleft()

                if len(history) >= self.FIGHT_REQUIRED_HITS:
                    candidates.append(result)

        # Prune old fight histories.
        for pair_key in list(self.fight_history.keys()):
            history = self.fight_history[pair_key]
            while (
                history
                and self.frame_number - history[0] >= self.FIGHT_WINDOW_FRAMES
            ):
                history.popleft()
            if not history:
                del self.fight_history[pair_key]

        # Temporal suspicious-removal detector replaces immediate proximity alerts.
        candidates.extend(self.theft_detector.update(persons, objects))

        # Preserve weapon detection behavior.
        for person in persons:
            for weapon in weapons:
                result = detect_weapon(person, weapon)
                if result is not None:
                    candidates.append(result)

        if not candidates:
            return {"detected": False, "activity": None}

        priority = {"WEAPON": 3, "THEFT": 2, "FIGHT": 1}
        return max(
            candidates,
            key=lambda result: priority.get(result.get("activity"), 0),
        )
