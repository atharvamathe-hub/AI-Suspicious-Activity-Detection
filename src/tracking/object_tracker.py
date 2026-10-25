class ObjectTracker:

    def __init__(self, model):
        self.model = model

    def track(self, frame):
        results = self.model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )

        return results[0]