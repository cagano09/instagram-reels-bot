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
        # API anahtarı boşsa burada hata fırlatmasını engelleyelim
        self.groq_client = Groq(api_key=cfg.GROQ_API_KEY) if cfg.GROQ_API_KEY else None

    async def get_reddit_news(self):
        url = "https://www.reddit.com/r/technology/top/.rss?t=day"
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                feed = feedparser.parse(response.text)
                if feed.entries:
                    return {"title": feed.entries[0].title, "link": feed.entries[0].link}
        except Exception as e:
            logger.error(f"Reddit çekme hatası: {e}")
        return None

    def process_with_groq(self, news_title):
        if not self.groq_client:
            return "API Key eksik olduğu için metin oluşturulamadı."
        
        prompt = f"Teknoloji haberini Reels için heyecanlı bir Türkçe özete dönüştür. Sadece seslendirilecek metni ver. Haber: {news_title}"
        try:
            completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API hatası: {e}")
            return f"Metin oluşturulurken hata oluştu: {news_title}"

    async def fetch_pexels_video(self, query="future technology"):
        headers = {"Authorization": self.cfg.PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation=portrait"
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(url, headers=headers)
                data = response.json()
                if data.get('videos'):
                    return data['videos'][0]['video_files'][0]['link']
        except Exception as e:
            logger.error(f"Pexels API hatası: {e}")
        return None

# --- RENDER PORT DİNLEYİCİ ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            logger.info(f"✅ Render için Port {port} dinleniyor...")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Sunucu hatası: {e}")

# --- BOT SINIFI ---
class TelegramBot:
    def __init__(self, cfg):
        self.cfg = cfg
        self.engine = ContentEngine(cfg)
        self.app = Application.builder().token(cfg.TELEGRAM_BOT_TOKEN).build()
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("teknoviral", self.cmd_teknoviral))

    async def cmd_start(self, update: Update, context: CallbackContext):
        await update.message.reply_text("🤖 Protokolos Hazır! /teknoviral komutunu kullan.")

    async def cmd_teknoviral(self, update: Update, context: CallbackContext):
        # İşlem başladı mesajı
        status_msg = await update.message.reply_text("🌐 Veriler çekiliyor...")
        
        try:
            # 1. Reddit
            news = await self.engine.get_reddit_news()
            if not news:
                await status_msg.edit_text("❌ Reddit haberi alınamadı.")
                return

            # 2. Groq & TTS
            await status_msg.edit_text("🎙️ Seslendiriliyor...")
            turkce_metin = self.engine.process_with_groq(news['title'])
            audio_path = f"news_{update.message.message_id}.mp3"
            tts = gTTS(text=turkce_metin, lang='tr')
            tts.save(audio_path)

            # 3. Pexels
            await status_msg.edit_text("🎬 Video getiriliyor...")
            video_url = await self.engine.fetch_pexels_video()

            # 4. Gönderim
            caption = f"📰 **Haber:** {news['title']}\n\n🔗 [Kaynağa Git]({news['link']})"
            if video_url:
                await update.message.reply_video(video=video_url, caption=caption, parse_mode="Markdown")
            
            with open(audio_path, "rb") as audio:
                await update.message.reply_audio(audio=audio, title="Haber Özeti")

            if os.path.exists(audio_path):
                os.remove(audio_path)
            await status_msg.delete()

        except Exception as e:
            logger.error(f"Komut hatası: {e}")
            await status_msg.edit_text(f"⚠️ Bir hata oluştu: {str(e)}")

    def run(self):
        logger.info("🤖 Bot başlatılıyor...")
        self.app.run_polling(drop_pending_updates=True)

# --- ANA GİRİŞ ---
if __name__ == "__main__":
    cfg = Config()
    
    if not cfg.TELEGRAM_BOT_TOKEN:
        logger.critical("HATA: TELEGRAM_BOT_TOKEN bulunamadı!")
        sys.exit(1)

    # Port dinleyicisi arka planda
    threading.Thread(target=run_dummy_server, daemon=True).start()

    # Bot ana thread'de
    bot = TelegramBot(cfg)
    try:
        bot.run()
    except Exception as e:
        logger.critical(f"Bot çalışırken durdu: {e}")
