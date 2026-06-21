import cv2
import numpy as np
import os
import random
from pathlib import Path

BASE = r"D:\PersonalData\Desktop\1"

def draw_bboxes(img, label_path, color=(0, 255, 0)):
    h, w = img.shape[:2]
    if not os.path.exists(label_path):
        return img
    with open(label_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 5:
                continue
            cls, cx, cy, bw, bh = parts
            cx, cy, bw, bh = float(cx) * w, float(cy) * h, float(bw) * w, float(bh) * h
            x1 = int(cx - bw / 2)
            y1 = int(cy - bh / 2)
            x2 = int(cx + bw / 2)
            y2 = int(cy + bh / 2)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, cls, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return img

def validate_labels():
    issues = []
    for split in ["train", "val"]:
        img_dir = os.path.join(BASE, "images", split)
        lbl_dir = os.path.join(BASE, "labels", split)
        for fname in os.listdir(lbl_dir):
            if not fname.endswith(".txt"):
                continue
            lbl_path = os.path.join(lbl_dir, fname)
            base = fname.replace(".txt", "")
            img_path = os.path.join(img_dir, base + ".jpg")
            if not os.path.exists(img_path):
                img_path = os.path.join(img_dir, base + ".png")
            if not os.path.exists(img_path):
                issues.append(f"{split}/{fname}: no matching image")
                continue
            img = cv2.imread(img_path)
            if img is None:
                issues.append(f"{split}/{fname}: cannot read image")
                continue
            h, w = img.shape[:2]
            with open(lbl_path) as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) != 5:
                        issues.append(f"{split}/{fname}:{lineno} expected 5 values, got {len(parts)}")
                        continue
                    try:
                        vals = list(map(float, parts))
                    except:
                        issues.append(f"{split}/{fname}:{lineno} non-numeric values")
                        continue
                    cls, cx, cy, bw, bh = vals
                    if cls != 0:
                        issues.append(f"{split}/{fname}:{lineno} class is {cls}, expected 0")
                    for name, val in [("cx", cx), ("cy", cy), ("bw", bw), ("bh", bh)]:
                        if not (0 <= val <= 1):
                            issues.append(f"{split}/{fname}:{lineno} {name}={val} out of [0,1]")
                    # Check if bbox makes sense (non-zero size)
                    if bw <= 0 or bh <= 0:
                        issues.append(f"{split}/{fname}:{lineno} zero/negative size {bw}x{bh}")
    return issues

print("=== Проверка корректности label файлов ===")
issues = validate_labels()
if issues:
    for i in issues:
        print(f"  ISSUE: {i}")
else:
    print("  Все лейблы корректны!")

# Generate annotated samples for manual review
print("\n=== Генерация примеров с разметкой ===")
out_dir = os.path.join(BASE, "_annotated_preview")
os.makedirs(out_dir, exist_ok=True)

# Clear previous
for f in os.listdir(out_dir):
    os.remove(os.path.join(out_dir, f))

for split in ["train", "val"]:
    img_dir = os.path.join(BASE, "images", split)
    lbl_dir = os.path.join(BASE, "labels", split)
    files = [f for f in os.listdir(img_dir) if f.endswith((".jpg", ".png"))]
    if split == "val":
        files = sorted(files)
    else:
        files = sorted(files)[:50]  # sample 50 from train
    for fname in files:
        img_path = os.path.join(img_dir, fname)
        base = fname.rsplit(".", 1)[0]
        lbl_path = os.path.join(lbl_dir, base + ".txt")
        img = cv2.imread(img_path)
        if img is None:
            continue
        has_label = os.path.exists(lbl_path) and os.path.getsize(lbl_path) > 0
        annotated = draw_bboxes(img.copy(), lbl_path)
        # Add status text
        if not has_label:
            cv2.putText(annotated, "NO LABEL", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imwrite(os.path.join(out_dir, f"{split}_{fname}"), annotated)

print(f"  Аннотированные превью сохранены в: {out_dir}")
print(f"  Файлов сгенерировано: {len(os.listdir(out_dir))}")

# Summary
print("\n=== Сводка ===")
for split in ["train", "val"]:
    img_dir = os.path.join(BASE, "images", split)
    lbl_dir = os.path.join(BASE, "labels", split)
    imgs = [f for f in os.listdir(img_dir) if f.endswith((".jpg", ".png"))]
    lbls = [f for f in os.listdir(lbl_dir) if f.endswith(".txt")]
    nonempty = 0
    for l in lbls:
        if os.path.getsize(os.path.join(lbl_dir, l)) > 0:
            nonempty += 1
    missing = [f.rsplit(".", 1)[0] for f in imgs if f.rsplit(".", 1)[0] + ".txt" not in lbls]
    print(f"  {split}: {len(imgs)} images, {len(lbls)} labels ({nonempty} non-empty), {len(missing)} without labels")
    if missing:
        print(f"    Missing labels: {', '.join(sorted(missing))}")

print("\nГотово! Открой папку _annotated_preview и проверь:")
print("  - Красные надписи 'NO LABEL' — фото без разметки")
print("  - Зелёные рамки — имеющаяся разметка")
