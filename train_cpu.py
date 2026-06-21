from ultralytics import YOLO
import torch

device = "cpu"
print(f"Device: {device}")

model = YOLO("yolov8n.pt")

results = model.train(
    data=r"D:\PersonalData\Desktop\1\data.yaml",
    epochs=30,
    imgsz=320,
    batch=8,
    device=device,
    patience=15,
    save=True,
    project=r"D:\PersonalData\Desktop\new new tick\runs",
    name="cpu_test",
    exist_ok=True,
    pretrained=True,
    optimizer="auto",
    seed=42,
    workers=2,
)

print("CPU test complete!")
print(f"Model: {results.save_dir / 'weights' / 'best.pt'}")
