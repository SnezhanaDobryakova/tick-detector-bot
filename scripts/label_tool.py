import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os

BASE = r"D:\PersonalData\Desktop\1"

def get_unlabeled(split):
    img_dir = os.path.join(BASE, "images", split)
    lbl_dir = os.path.join(BASE, "labels", split)
    imgs = []
    for f in sorted(os.listdir(img_dir)):
        if not f.endswith((".jpg", ".png")):
            continue
        base = f.rsplit(".", 1)[0]
        lbl_path = os.path.join(lbl_dir, base + ".txt")
        if not os.path.exists(lbl_path) or os.path.getsize(lbl_path) == 0:
            imgs.append((os.path.join(img_dir, f), lbl_dir))
    return imgs

class LabelTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Tick Label Tool")
        self.root.geometry("950x750")

        self.splits = ["train", "val"]
        self.split_idx = 0
        self.items = []
        self.idx = 0
        self.boxes = []    # list of (x1, y1, x2, y2) in image coords
        self.rect_ids = []
        self.start_x = self.start_y = 0
        self.img_tk = None
        self.pil_img = None

        top = ttk.Frame(root)
        top.pack(fill=tk.X, pady=5)

        self.info = ttk.Label(top, text="Loading...", font=("Arial", 12))
        self.info.pack(side=tk.LEFT, padx=10)

        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="S - Save boxes & Next", command=self.save_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="D - No tick & Next", command=self.no_tick).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="N - Skip Next", command=self.next_img).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="B - Back", command=self.prev_img).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="R - Undo last box", command=self.undo_box).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="C - Clear all boxes", command=self.clear_boxes).pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(root, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.status = ttk.Label(root, text="", font=("Arial", 10))
        self.status.pack(fill=tk.X, padx=10, pady=5)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        root.bind("<KeyPress-s>", lambda e: self.save_next())
        root.bind("<KeyPress-d>", lambda e: self.no_tick())
        root.bind("<KeyPress-n>", lambda e: self.next_img())
        root.bind("<KeyPress-b>", lambda e: self.prev_img())
        root.bind("<KeyPress-r>", lambda e: self.undo_box())
        root.bind("<KeyPress-c>", lambda e: self.clear_boxes())
        root.bind("<KeyPress-q>", lambda e: self.quit())
        root.bind("<Escape>", lambda e: self.quit())

        self.load_split()

    def set_status(self, msg):
        self.status.config(text=msg)
        self.root.update()

    def load_split(self):
        if self.split_idx >= len(self.splits):
            messagebox.showinfo("Done", "Все фото размечены!")
            self.root.quit()
            return
        self.items = get_unlabeled(self.splits[self.split_idx])
        if not self.items:
            self.set_status(f"{self.splits[self.split_idx]}: нет неподписанных")
            self.split_idx += 1
            self.load_split()
            return
        self.idx = 0
        self.show_image()

    def show_image(self):
        if self.idx < 0 or self.idx >= len(self.items):
            self.split_idx += 1
            self.load_split()
            return
        img_path, self.lbl_dir = self.items[self.idx]
        base = os.path.basename(img_path).rsplit(".", 1)[0]
        lbl_path = os.path.join(self.lbl_dir, base + ".txt")
        if os.path.exists(lbl_path) and os.path.getsize(lbl_path) > 0:
            self.idx += 1
            self.show_image()
            return

        self.info.config(text=f"{self.splits[self.split_idx]} [{self.idx+1}/{len(self.items)}] {os.path.basename(img_path)}")
        self.set_status("Клик-тащи = новая рамка. S=сохранить все рамки, R=отменить последнюю, C=очистить всё")

        self.pil_img = Image.open(img_path)
        self.canvas.update()
        cw = self.canvas.winfo_width() or 800
        ch = self.canvas.winfo_height() or 600
        self.pil_img.thumbnail((cw, ch), Image.LANCZOS)
        self.img_tk = ImageTk.PhotoImage(self.pil_img)
        self.canvas.delete("all")
        self.canvas.config(width=self.pil_img.width, height=self.pil_img.height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)
        self.boxes = []
        self.rect_ids = []
        self.drawing_rect = None

    def redraw_boxes(self):
        # Remove all rects and redraw
        for rid in self.rect_ids:
            self.canvas.delete(rid)
        self.rect_ids = []
        for b in self.boxes:
            rid = self.canvas.create_rectangle(b[0], b[1], b[2], b[3],
                                               outline="green", width=3)
            self.rect_ids.append(rid)

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.drawing_rect:
            self.canvas.delete(self.drawing_rect)
            self.drawing_rect = None

    def on_drag(self, event):
        if self.drawing_rect:
            self.canvas.delete(self.drawing_rect)
        self.drawing_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline="lime", width=3
        )

    def on_release(self, event):
        if self.drawing_rect:
            self.canvas.delete(self.drawing_rect)
            self.drawing_rect = None
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            self.boxes.append((x1, y1, x2, y2))
            rid = self.canvas.create_rectangle(x1, y1, x2, y2,
                                                outline="green", width=3)
            self.rect_ids.append(rid)
            self.set_status(f"Рамок: {len(self.boxes)}. Продолжай или нажми S")

    def save_boxes_to_file(self, has_tick=True):
        img_path, _ = self.items[self.idx]
        base = os.path.basename(img_path).rsplit(".", 1)[0]
        lbl_path = os.path.join(self.lbl_dir, base + ".txt")
        if has_tick and self.boxes:
            w_img, h_img = self.pil_img.size
            with open(lbl_path, 'w') as f:
                for b in self.boxes:
                    x1, y1, x2, y2 = b
                    cx = ((x1 + x2) / 2) / w_img
                    cy = ((y1 + y2) / 2) / h_img
                    bw = (x2 - x1) / w_img
                    bh = (y2 - y1) / h_img
                    f.write(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")
            self.set_status(f"Сохранено {len(self.boxes)} bbox(ов) -> {base}.txt")
        else:
            open(lbl_path, 'w').close()
            self.set_status(f"Сохранён пустой -> {base}.txt (нет клеща)")

    def save_next(self):
        self.save_boxes_to_file(True)
        self.idx += 1
        self.show_image()

    def no_tick(self):
        self.save_boxes_to_file(False)
        self.idx += 1
        self.show_image()

    def next_img(self):
        self.idx += 1
        self.show_image()

    def prev_img(self):
        if self.idx > 0:
            self.idx -= 1
            self.show_image()

    def undo_box(self):
        if self.boxes:
            self.boxes.pop()
            self.redraw_boxes()
            self.set_status(f"Отменено. Рамок: {len(self.boxes)}")

    def clear_boxes(self):
        self.boxes = []
        self.redraw_boxes()
        self.set_status("Все рамки очищены")

    def quit(self):
        if messagebox.askyesno("Выход", "Точно выйти?"):
            self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = LabelTool(root)
    root.mainloop()
