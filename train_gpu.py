from ultralytics import YOLO
import torch

print(f"CUDA: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

model = YOLO("yolov8n.pt")

results = model.train(
    data=r"D:\PersonalData\Desktop\1\data.yaml",
    epochs=150,
    imgsz=640,
    batch=16,
    device=0,
    patience=30,
    save=True,
    project=r"D:\PersonalData\Desktop\new new tick\runs",
    name="tick_detector_gpu",
    exist_ok=True,
    pretrained=True,
    optimizer="auto",
    seed=42,
)

print("Training complete!")
print(f"Best model: {results.save_dir / 'weights' / 'best.pt'}")
