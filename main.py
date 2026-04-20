import os
import sys
import asyncio
import sqlite3
from pathlib import Path
from loguru import logger
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# --- YAPILANDIRMA ---
class Config:
    def __init__(self):
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.DB_PATH = Path("data") / "bot.db"
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# --- BOT SINIFI ---
class TelegramBot:
    def __init__(self, cfg):
        self.config = cfg
        # Application nesnesini oluşturuyoruz ama henüz başlatmıyoruz
        self.app = Application.builder().token(cfg.TELEGRAM_BOT_TOKEN).build()
        
        # Handler'ları ekle
        self.app.add_handler(CommandHandler("start", self.cmd_start))

    async def cmd_start(self, update: Update, context: CallbackContext):
        await update.message.reply_text("🚀 Bot başarıyla çalıştı! Emirlerinizi bekliyorum.")

    async def run(self):
        """
        Render için optimize edilmiş asenkron başlatıcı.
        run_polling() yerine initialize/start metodlarını manuel çağırır.
        """
        logger.info("Bot modülleri başlatılıyor...")
        
        # 1. Uygulamayı hazırla
        await self.app.initialize()
        
        # 2. Botu başlat
        await self.app.start()
        
        # 3. Mesajları dinlemeye başla (Polling)
        # Burası kritik: run_polling yerine start_polling kullanıyoruz
        await self.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        logger.info("🤖 BOT ŞU AN AKTİF!")

        # 4. Botun kapanmasını engelle (Sonsuz döngü)
        # Render'ın botu kapatmaması için asenkron bir bekleme ekliyoruz
        try:
            while True:
                await asyncio.sleep(3600)  # Her saat başı döngüyü kontrol et
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.warning("Bot kapatılma sinyali aldı...")
        finally:
            # Temiz bir kapanış yap
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()

# --- ANA GİRİŞ ---
async def main():
    logger.info("Ana uygulama başlatıldı.")
    cfg = Config()
    
    if not cfg.TELEGRAM_BOT_TOKEN:
        logger.error("HATA: TELEGRAM_BOT_TOKEN ortam değişkeni bulunamadı!")
        return

    bot = TelegramBot(cfg)
    await bot.run()

if __name__ == "__main__":
    # Python 3.14+ ve Render uyumluluğu için
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Beklenmeyen bir hata oluştu: {e}")
        sys.exit(1)
