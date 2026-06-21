from ultralytics import YOLO
import torch

# Check GPU
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    device = 0
else:
    print("Training on CPU (will be slow)")
    device = "cpu"

# Load a pretrained YOLOv8n model
model = YOLO("yolov8n.pt")

# Train
results = model.train(
    data=r"D:\PersonalData\Desktop\1\data.yaml",
    epochs=150,
    imgsz=640,
    batch=16,
    device=device,
    patience=30,
    save=True,
    project=r"D:\PersonalData\Desktop\new new tick\runs",
    name="tick_detector",
    exist_ok=True,
    pretrained=True,
    optimizer="auto",
    seed=42,
)

print("Training complete!")
print(f"Best model saved to: {results.save_dir / 'weights' / 'best.pt'}")
