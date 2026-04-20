import os
import sys
import asyncio
import threading
import http.server
import socketserver
from pathlib import Path
from loguru import logger
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# --- YAPILANDIRMA ---
class Config:
    def __init__(self):
        # Render'dan gelen veya manuel girilen Token
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        # Veritabanı yolu
        self.DB_PATH = Path("data") / "bot.db"
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# --- RENDER PORT KANDIRMA SİSTEMİ (DUMMY SERVER) ---
def run_dummy_server():
    """Render'ın 'Port scan timeout' hatasını önlemek için basit bir HTTP sunucusu başlatır."""
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    # 'Allow reuse address' hatayı önlemek için önemli
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            logger.info(f"🚀 Render Port Dinleyici {port} üzerinde aktif.")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Sahte sunucu başlatılamadı: {e}")

# --- BOT SINIFI ---
class TelegramBot:
    def __init__(self, cfg):
        self.config = cfg
        # Application nesnesi
        self.app = Application.builder().token(cfg.TELEGRAM_BOT_TOKEN).build()
        
        # Komutları kaydet
        self.app.add_handler(CommandHandler("start", self.cmd_start))

    async def cmd_start(self, update: Update, context: CallbackContext):
        await update.message.reply_text("🤖 Protokolos Bot Aktif!\n\nSistem Render üzerinde stabil çalışıyor.")

    async def run(self):
        """Asenkron polling başlatıcı."""
        logger.info("Modüller başlatılıyor...")
        
        await self.app.initialize()
        await self.app.start()
        
        # start_polling, mevcut event loop içinde çalışır
        await self.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("🤖 BOT ŞU AN AKTİF VE DİNLİYOR!")

        # Kapanmayı engelle
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.warning("Bot kapatılıyor...")
        finally:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()

# --- ANA GİRİŞ ---
async def main():
    logger.info("Ana uygulama başlatıldı.")
    cfg = Config()
    
    if not cfg.TELEGRAM_BOT_TOKEN:
        logger.error("HATA: TELEGRAM_BOT_TOKEN eksik!")
        return

    # 1. Adım: Render'ı kandırmak için HTTP sunucusunu ayrı bir thread'de başlat
    threading.Thread(target=run_dummy_server, daemon=True).start()

    # 2. Adım: Botu asenkron olarak çalıştır
    bot = TelegramBot(cfg)
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Kritik hata: {e}")
        sys.exit(1)
