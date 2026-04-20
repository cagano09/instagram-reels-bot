import os
import sys
import asyncio
import threading
import http.server
import socketserver
import feedparser
import httpx
from pathlib import Path
from loguru import logger
from gtts import gTTS
from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# --- YAPILANDIRMA ---
class Config:
    def __init__(self):
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# --- İÇERİK MOTORU ---
class ContentEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        # Hatalı 'proxies' parametresinden kaçınmak için en sade kurulum
        if cfg.GROQ_API_KEY:
            self.groq_client = Groq(api_key=cfg.GROQ_API_KEY)
        else:
            self.groq_client = None

    async def get_reddit_news(self):
        url = "https://www.reddit.com/r/technology/top/.rss?t=day"
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                feed = feedparser.parse(response.text)
                if feed.entries:
                    return {"title": feed.entries[0].title, "link": feed.entries[0].link}
        except Exception as e:
            logger.error(f"Reddit hatası: {e}")
        return None

    def process_with_groq(self, news_title):
        if not self.groq_client:
            return "API Hatası: Groq anahtarı bulunamadı."
        
        prompt = f"Aşağıdaki teknoloji haberini heyecanlı, viral bir Reels videosu için Türkçe özetle. Sadece seslendirilecek metni ver. Haber: {news_title}"
        try:
            completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq hatası: {e}")
            return f"Günün önemli teknoloji haberi: {news_title}"

    async def fetch_pexels_video(self, query="modern technology"):
        if not self.cfg.PEXELS_API_KEY:
            return None
        
        headers = {"Authorization": self.cfg.PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation=portrait"
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                data = response.json()
                if data.get('videos'):
                    return data['videos'][0]['video_files'][0]['link']
        except Exception as e:
            logger.error(f"Pexels hatası: {e}")
        return None

# --- RENDER PORT DİNLEYİCİ ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            logger.info(f"✅ Port {port} üzerinden Render bağlantısı aktif.")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Sunucu hatası: {e}")

# --- TELEGRAM BOT ---
class TelegramBot:
    def __init__(self, cfg):
        self.cfg = cfg
        self.engine = ContentEngine(cfg)
        self.app = Application.builder().token(cfg.TELEGRAM_BOT_TOKEN).build()
        
        # Komutlar
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("teknoviral", self.cmd_teknoviral))

    async def cmd_start(self, update: Update, context: CallbackContext):
        await update.message.reply_text("🤖 Protokolos Viral Bot Aktif!\n\n/teknoviral yazarak Reddit gündemini sesli video olarak alabilirsin.")

    async def cmd_teknoviral(self, update: Update, context: CallbackContext):
        status = await update.message.reply_text("🌐 Reddit taranıyor...")
        
        try:
            # 1. Haber Çek
            news = await self.engine.get_reddit_news()
            if not news:
                await status.edit_text("❌ Haber alınamadı.")
                return

            # 2. İşle ve Seslendir
            await status.edit_text("🎙️ Türkçe seslendirme hazırlanıyor...")
            metin = self.engine.process_with_groq(news['title'])
            
            file_id = update.message.message_id
            audio_path = f"audio_{file_id}.mp3"
            
            tts = gTTS(text=metin, lang='tr')
            tts.save(audio_path)

            # 3. Video Bul
            await status.edit_text("🎬 Arka plan videosu seçiliyor...")
            video_url = await self.engine.fetch_pexels_video()

            # 4. Gönder
            caption = f"📰 **Gündem:** {news['title']}\n\n🔗 [Reddit Kaynağı]({news['link']})"
            
            if video_url:
                await update.message.reply_video(video=video_url, caption=caption, parse_mode="Markdown")
            
            with open(audio_path, "rb") as audio:
                await update.message.reply_audio(audio=audio, title="Tekno Haber Sesli")

            # Temizlik
            if os.path.exists(audio_path):
                os.remove(audio_path)
            await status.delete()

        except Exception as e:
            logger.error(f"İşlem hatası: {e}")
            await status.edit_text(f"⚠️ Bir hata oluştu: {e}")

    def run(self):
        logger.info("🚀 Bot polling modunda başlatıldı.")
        self.app.run_polling(drop_pending_updates=True)

# --- ANA GİRİŞ ---
if __name__ == "__main__":
    cfg = Config()
    
    if not cfg.TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN eksik!")
        sys.exit(1)

    # Arka planda sunucuyu başlat (Render çökmemesi için)
    threading.Thread(target=run_dummy_server, daemon=True).start()

    # Botu çalıştır
    bot = TelegramBot(cfg)
    bot.run()
