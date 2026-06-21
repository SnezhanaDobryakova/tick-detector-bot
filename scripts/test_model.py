from ultralytics import YOLO
import cv2
import os

MODEL_PATH = r"D:\PersonalData\Desktop\new new tick\runs\tick_detector_gpu\weights\best.pt"
TEST_DIR = r"D:\PersonalData\Desktop\new new tick\test_results"
VAL_IMAGES = r"D:\PersonalData\Desktop\1\images\val"
CONF = 0.25

os.makedirs(TEST_DIR, exist_ok=True)

model = YOLO(MODEL_PATH)

# Pick a few val images with different amounts of ticks
test_files = [
    "tick_100.png", "tick_4.jpg", "tick_11.jpg", "tick_101.png",
    "tick_8.jpg", "tick_37.jpg", "tick_235.png", "tick_95.png",
]

print(f"{'File':20s} {'Ticks':6s} {'Confidences':20s}")
print("-" * 50)

for fname in test_files:
    path = os.path.join(VAL_IMAGES, fname)
    if not os.path.exists(path):
        print(f"{fname:20s} NOT FOUND")
        continue

    results = model(path, conf=CONF)[0]
    boxes = results.boxes

    if boxes:
        confs = [f"{b.conf.item():.0%}" for b in boxes]
        print(f"{fname:20s} {len(boxes):6d} {', '.join(confs):20s}")
    else:
        print(f"{fname:20s} {'0':6s} {'-':20s}")

    # Save annotated image
    annotated = results.plot()
    out_path = os.path.join(TEST_DIR, fname)
    cv2.imwrite(out_path, annotated)

print(f"\nAnnotated images saved to: {TEST_DIR}")
