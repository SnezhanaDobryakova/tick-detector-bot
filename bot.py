import logging
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ultralytics import YOLO
import cv2
import numpy as np

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
MODEL_PATH = os.environ.get("MODEL_PATH", "best.pt")
CONF_THRESHOLD = 0.25

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

logger.info(f"Loading model from {MODEL_PATH}")
model = YOLO(MODEL_PATH)
logger.info("Model loaded")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь фото, и я скажу — есть на нём клещ или нет."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    nparr = np.frombuffer(photo_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        await update.message.reply_text("Не удалось прочитать изображение.")
        return

    results = model(img, conf=CONF_THRESHOLD)
    detections = results[0].boxes

    if len(detections) > 0:
        n = len(detections)
        confs = [f"{b.conf.item():.0%}" for b in detections]
        await update.message.reply_text(
            f"✅ Да, на фото клещ!\n"
            f"Найдено: {n}\n"
            f"Уверенность: {', '.join(confs)}"
        )
    else:
        await update.message.reply_text(
            "❌ Нет, это не клещ."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    try:
        await update.message.reply_text("Произошла ошибка. Попробуйте ещё раз.")
    except:
        pass

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        logger.info(f"Health check: {format % args}")

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info(f"Health server listening on port {port}")
    server.serve_forever()

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Set BOT_TOKEN environment variable or edit the script!")
        sys.exit(1)

    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_error_handler(error_handler)

    logger.info("Bot started. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
