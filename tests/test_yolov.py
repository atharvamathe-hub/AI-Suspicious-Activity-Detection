from ultralytics import YOLO

# Load the general-purpose YOLO26 Nano detector
model = YOLO("yolo26n.pt")

# Test on a video
results = model.predict(
    source="input/videos/fight/fight.mp4",
    imgsz=640,
    conf=0.25,
    save=True,
    verbose=False
)

print("YOLO26n test completed.")