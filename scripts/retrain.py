from ultralytics import YOLO

DATA_YAML = r"D:\PersonalData\Desktop\1\data.yaml"
PRETRAINED = r"D:\PersonalData\Desktop\new new tick\runs\tick_detector_gpu\weights\best.pt"
OUTPUT_DIR = r"D:\PersonalData\Desktop\new new tick\runs\retrain"

model = YOLO(PRETRAINED)
results = model.train(
    data=DATA_YAML,
    epochs=100,
    imgsz=640,
    batch=16,
    name="retrain",
    project=r"D:\PersonalData\Desktop\new new tick\runs",
    patience=20,
    device=0,
    workers=4,
    lr0=0.001,
    close_mosaic=10,
)
