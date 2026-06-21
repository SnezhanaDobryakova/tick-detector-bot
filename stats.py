import os
BASE = r"D:\PersonalData\Desktop\1"

total_boxes_all = 0
for split in ['train', 'val']:
    img_dir = os.path.join(BASE, 'images', split)
    lbl_dir = os.path.join(BASE, 'labels', split)
    imgs = [f for f in os.listdir(img_dir) if f.endswith(('.jpg','.png'))]
    lbls = [f for f in os.listdir(lbl_dir) if f.endswith('.txt')]
    nonempty = sum(1 for l in lbls if os.path.getsize(os.path.join(lbl_dir, l)) > 0)
    empty = sum(1 for l in lbls if os.path.getsize(os.path.join(lbl_dir, l)) == 0)
    missing = [f.rsplit('.',1)[0] for f in imgs if f.rsplit('.',1)[0]+'.txt' not in lbls]
    total_boxes = 0
    for l in lbls:
        p = os.path.join(lbl_dir, l)
        if os.path.getsize(p) > 0:
            with open(p) as f:
                total_boxes += sum(1 for line in f if line.strip())
    total_boxes_all += total_boxes
    print(f'{split}:')
    print(f'  Images: {len(imgs)}')
    print(f'  Labels: {len(lbls)} (non-empty: {nonempty}, empty: {empty})')
    print(f'  Without labels: {len(missing)}')
    print(f'  Bounding boxes: {total_boxes}')

print(f'\nTotal boxes: {total_boxes_all}')
