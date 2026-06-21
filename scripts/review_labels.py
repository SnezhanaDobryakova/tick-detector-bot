import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import os

BASE = r"D:\PersonalData\Desktop\1"
CLASS_NAMES = {0: "Клещ"}

def load_all():
    items = []
    for split in ["train", "val"]:
        img_dir = os.path.join(BASE, "images", split)
        lbl_dir = os.path.join(BASE, "labels", split)
        for f in sorted(os.listdir(img_dir)):
            if not f.endswith((".jpg", ".png")):
                continue
            base = f.rsplit(".", 1)[0]
            lbl_path = os.path.join(lbl_dir, base + ".txt")
            has = os.path.exists(lbl_path) and os.path.getsize(lbl_path) > 0
            items.append((os.path.join(img_dir, f), lbl_path, split, has))
    return items

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Tick Label Tool")
        self.root.geometry("1000x800")

        self.items = load_all()
        self.idx = 0
        self.orig = None       # original PIL image
        self.display = None    # display PIL image (resized)
        self.img_tk = None
        self.scale = 1.0       # orig_w * scale = display_w
        self.off_x = 0.0       # offset if we center the image
        self.off_y = 0.0

        # boxes in ORIGINAL image coords: [(x1,y1,x2,y2,cls)]
        self.boxes = []
        self.sel = -1
        self.modified = False

        # Drawing state
        self.drag_start = None
        self.drag_rect = None

        # Top bar
        top = ttk.Frame(root)
        top.pack(fill=tk.X, pady=5)
        self.info = ttk.Label(top, text="", font=("Arial", 11))
        self.info.pack(side=tk.LEFT, padx=10)
        self.progress = ttk.Label(top, text="", font=("Arial", 11))
        self.progress.pack(side=tk.RIGHT, padx=10)

        # Navigation
        nav = ttk.Frame(root)
        nav.pack(fill=tk.X, pady=3)
        for txt, cmd in [("<<", lambda: self.go(0)), ("<", self.prev),
                         (">", self.next), (">>", lambda: self.go(len(self.items)-1))]:
            ttk.Button(nav, text=txt, command=cmd, width=3).pack(side=tk.LEFT, padx=1)
        self.jump_e = ttk.Entry(nav, width=6)
        self.jump_e.pack(side=tk.LEFT, padx=5)
        ttk.Button(nav, text="Go", command=self.jump).pack(side=tk.LEFT, padx=1)
        ttk.Button(nav, text="First unlabeled", command=self.first_unlabeled).pack(side=tk.LEFT, padx=10)

        # Actions
        act = ttk.Frame(root)
        act.pack(fill=tk.X, pady=3)
        ttk.Button(act, text="S - Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(act, text="D - Delete selected", command=self.del_sel).pack(side=tk.LEFT, padx=5)
        ttk.Button(act, text="R - Clear all & redo", command=self.redo).pack(side=tk.LEFT, padx=5)
        ttk.Button(act, text="X - Delete box near cursor", command=self.del_near).pack(side=tk.LEFT, padx=5)

        # Canvas
        self.canvas = tk.Canvas(root, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Status
        self.status = ttk.Label(root, text="", font=("Arial", 10))
        self.status.pack(fill=tk.X, padx=10, pady=2)
        self.counter = ttk.Label(root, text="", font=("Arial", 9))
        self.counter.pack(fill=tk.X, padx=10)

        # Keyboard
        root.bind("<Left>", lambda e: self.prev())
        root.bind("<Right>", lambda e: self.next())
        root.bind("s", lambda e: self.save())
        root.bind("d", lambda e: self.del_sel())
        root.bind("r", lambda e: self.redo())
        root.bind("x", lambda e: self.del_near())
        root.bind("q", lambda e: self.quit())
        root.bind("<Escape>", lambda e: self.quit())
        root.bind("<Return>", lambda e: self.jump())

        self.show()

    def msg(self, text):
        self.status.config(text=text)
        self.root.update()

    def load_boxes_from_file(self, path):
        boxes = []
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return boxes
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != 5:
                    continue
                try:
                    cls, cx, cy, bw, bh = map(float, parts)
                except:
                    continue
                w, h = self.orig.size
                x1 = (cx - bw / 2) * w
                y1 = (cy - bh / 2) * h
                x2 = (cx + bw / 2) * w
                y2 = (cy + bh / 2) * h
                boxes.append((x1, y1, x2, y2, int(cls)))
        return boxes

    def save_boxes_to_file(self, path, boxes):
        if not boxes:
            open(path, 'w').close()
            return
        w, h = self.orig.size
        with open(path, 'w') as f:
            for (x1, y1, x2, y2, cls) in boxes:
                cx = ((x1 + x2) / 2) / w
                cy = ((y1 + y2) / 2) / h
                bw = (x2 - x1) / w
                bh = (y2 - y1) / h
                f.write(f"{cls} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")

    # Coordinate transforms
    def orig_to_disp(self, x, y):
        return x * self.scale + self.off_x, y * self.scale + self.off_y

    def disp_to_orig(self, x, y):
        return (x - self.off_x) / self.scale, (y - self.off_y) / self.scale

    def draw_image(self):
        if self.orig is None:
            return
        draw = self.orig.copy()
        d = ImageDraw.Draw(draw)
        for i, (x1, y1, x2, y2, cls) in enumerate(self.boxes):
            name = CLASS_NAMES.get(cls, str(cls))
            color = "red" if i == self.sel else "lime"
            width = 4 if i == self.sel else 3
            d.rectangle([x1, y1, x2, y2], outline=color, width=width)
            d.text((x1 + 2, max(0, y1 - 20)), name, fill=color)
        # Resize for display
        cw = self.canvas.winfo_width() or 800
        ch = self.canvas.winfo_height() or 600
        self.display = draw.copy()
        self.display.thumbnail((cw, ch), Image.LANCZOS)
        dw, dh = self.display.size
        ow, oh = self.orig.size
        self.scale = dw / ow
        self.off_x = 0
        self.off_y = 0
        self.img_tk = ImageTk.PhotoImage(self.display)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)

    def show(self):
        if not self.items:
            return
        if self.modified:
            if messagebox.askyesno("Not saved", "Save changes?"):
                self.save()

        ip, lp, split, has = self.items[self.idx]
        self.img_path = ip
        self.lbl_path = lp
        self.split = split

        self.orig = Image.open(ip)
        self.boxes = self.load_boxes_from_file(lp)
        self.sel = -1
        self.modified = False
        self.draw_image()

        n = len(self.boxes)
        labeled = sum(1 for _ in self.items if _[3])
        total = len(self.items)
        self.info.config(text=f"{split.upper()} | {os.path.basename(ip)} | {n} box(es)")
        self.progress.config(text=f"{self.idx+1}/{total}")
        self.counter.config(text=f"Total: {total} | Labeled: {labeled} | Unlabeled: {total-labeled}")
        self.msg(f"{'Labelled' if has else 'NO LABEL'} | {n} boxes | S=save  D=del  X=del near  R=redo")

    # --- Mouse ---
    def on_press(self, event):
        ox, oy = self.disp_to_orig(event.x, event.y)
        # Check if clicked on a box
        for i, (x1, y1, x2, y2, _) in enumerate(self.boxes):
            if x1 <= ox <= x2 and y1 <= oy <= y2:
                self.sel = i
                self.draw_image()
                self.msg(f"Selected box #{i+1}  D=delete")
                self.drag_start = None
                return
        self.sel = -1
        self.draw_image()
        self.drag_start = (ox, oy)

    def on_drag(self, event):
        if self.drag_start is None:
            return
        ox, oy = self.disp_to_orig(event.x, event.y)
        sx, sy = self.drag_start
        # Draw temp rectangle on canvas directly (faster)
        if self.drag_rect:
            self.canvas.delete(self.drag_rect)
        # Convert to display coords for drawing
        dx1, dy1 = self.orig_to_disp(min(sx, ox), min(sy, oy))
        dx2, dy2 = self.orig_to_disp(max(sx, ox), max(sy, oy))
        self.drag_rect = self.canvas.create_rectangle(
            dx1, dy1, dx2, dy2, outline="yellow", width=3
        )

    def on_release(self, event):
        if self.drag_rect:
            self.canvas.delete(self.drag_rect)
            self.drag_rect = None
        if self.drag_start is None:
            return
        sx, sy = self.drag_start
        ox, oy = self.disp_to_orig(event.x, event.y)
        self.drag_start = None
        x1, y1 = min(sx, ox), min(sy, oy)
        x2, y2 = max(sx, ox), max(sy, oy)
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            self.boxes.append((x1, y1, x2, y2, 0))
            self.modified = True
            self.draw_image()
            self.msg(f"Box #{len(self.boxes)} added. S to save")

    # --- Actions ---
    def save(self):
        self.save_boxes_to_file(self.lbl_path, self.boxes)
        self.modified = False
        base = os.path.basename(self.img_path).rsplit(".", 1)[0]
        for i, (ip, lp, sp, _) in enumerate(self.items):
            if lp == self.lbl_path:
                self.items[i] = (ip, lp, sp, len(self.boxes) > 0)
                break
        self.msg(f"Saved {len(self.boxes)} box(es)")

    def del_sel(self):
        if 0 <= self.sel < len(self.boxes):
            del self.boxes[self.sel]
            self.sel = -1
            self.modified = True
            self.draw_image()
            self.msg("Deleted. S to save")

    def del_near(self):
        """Delete box closest to cursor"""
        # Get cursor position
        x = self.canvas.winfo_pointerx() - self.canvas.winfo_rootx()
        y = self.canvas.winfo_pointery() - self.canvas.winfo_rooty()
        ox, oy = self.disp_to_orig(x, y)
        best = None
        best_d = 30
        for i, (x1, y1, x2, y2, _) in enumerate(self.boxes):
            if x1 <= ox <= x2 and y1 <= oy <= y2:
                best = i
                break
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            d = ((cx - ox) ** 2 + (cy - oy) ** 2) ** 0.5
            if d < best_d:
                best_d = d
                best = i
        if best is not None:
            del self.boxes[best]
            self.sel = -1
            self.modified = True
            self.draw_image()
            self.msg("Deleted nearest box. S to save")

    def redo(self):
        self.boxes = []
        self.sel = -1
        self.modified = True
        self.draw_image()
        self.msg("Cleared. Draw new boxes, then S")

    def prev(self):
        if self.idx > 0:
            self.idx -= 1
            self.show()

    def next(self):
        if self.idx < len(self.items) - 1:
            self.idx += 1
            self.show()

    def go(self, n):
        if 0 <= n < len(self.items):
            self.idx = n
            self.show()

    def jump(self):
        try:
            self.go(int(self.jump_e.get()) - 1)
        except:
            pass

    def first_unlabeled(self):
        for i, (_, _, _, h) in enumerate(self.items):
            if not h:
                self.go(i)
                return
        messagebox.showinfo("OK", "All images labeled!")

    def quit(self):
        if self.modified:
            if messagebox.askyesno("Not saved", "Save?"):
                self.save()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
