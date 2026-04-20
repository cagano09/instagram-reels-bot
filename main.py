import os
import sys
import asyncio
import threading
import http.server
import socketserver
from loguru import logger

# Kritik: Başlangıç logu (Kodun çalışıp çalışmadığını anlamak için)
logger.info("🚀 Uygulama başlatma süreci başladı...")

try:
    import feedparser
    import httpx
    from gtts import gTTS
    from groq import Groq
    from telegram import Update
    from telegram.ext import Application, CommandHandler, CallbackContext
    logger.info("✅ Kütüphaneler başarıyla yüklendi.")
except ImportError as e:
    logger.error(f"❌ Kütüphane yükleme hatası: {e}")
    sys.exit(1)

# --- YAPILANDIRMA ---
class Config:
    def __init__(self):
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# --- RENDER PORT DİNLEYİCİ ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
            logger.info(f"🌐 Port {port} aktif edildi.")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Port hatası: {e}")

# --- BOT SINIFI (Minimal Yapı) ---
class TelegramBot:
    def __init__(self, cfg):
        try:
            self.app = Application.builder().token(cfg.TELEGRAM_BOT_TOKEN).build()
            self.app.add_handler(CommandHandler("start", self.cmd_start))
            logger.info("🤖 Bot motoru kuruldu.")
        except Exception as e:
            logger.error(f"Bot kurulum hatası: {e}")
            raise

    async def cmd_start(self, update: Update, context: CallbackContext):
        await update.message.reply_text("Merhaba! Bot çalışıyor.")

    def run(self):
        logger.info("📡 Polling başlatılıyor...")
        self.app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    cfg = Config()
    
    if not cfg.TELEGRAM_BOT_TOKEN:
        logger.critical("❌ HATA: TELEGRAM_BOT_TOKEN bulunamadı!")
        sys.exit(1)

    # Arka planda portu aç
    threading.Thread(target=run_dummy_server, daemon=True).start()

    # Botu çalıştır
    try:
        bot = TelegramBot(cfg)
        bot.run()
    except Exception as e:
        logger.critical(f"💥 KRİTİK ÇÖKME: {e}")
        sys.exit(1)
