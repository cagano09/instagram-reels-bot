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
        # Render panelindeki Environment Variables'dan çekilir
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# --- İÇERİK MOTORU ---
class ContentEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        # Groq istemcisini en sade haliyle başlatıyoruz
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
            logger.error(f"Reddit Hatası: {e}")
        return None

    def process_with_groq(self, news_title):
        if not self.groq_client:
            return "Gündem haberi oluşturulamadı, anahtar eksik."
        
        prompt = f"Şu haberi viral bir Reels videosu için heyecanlı bir dille Türkçe özetle. Sadece seslendirilecek metni ver: {news_title}"
        try:
            completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq Hatası: {e}")
            return f"Günün öne çıkan haberi: {news_title}"

    async def fetch_pexels_video(self, query="cyberpunk technology"):
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
            logger.error(f"Pexels Hatası: {e}")
        return None

# --- RENDER PORT DİNLEYİCİ (8080 yerine 10000 denemesi) ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            logger.info(f"✅ Port {port} aktif. Render hazır.")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Sunucu Hatası: {e}")

# --- TELEGRAM BOT SINIFI ---
class TelegramBot:
    def __init__(self, cfg):
        self.cfg = cfg
        self.engine = ContentEngine(cfg)
        
        # KRİTİK GÜNCELLEME: Python 3.14 uyumluluğu için job_queue(None) eklendi
        self.app = (
            Application.builder()
            .token(cfg.TELEGRAM_BOT_TOKEN)
            .job_queue(None) 
            .build()
        )
        
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("teknoviral", self.cmd_teknoviral))

    async def cmd_start(self, update: Update, context: CallbackContext):
        await update.message.reply_text("🚀 Protokolos Hazır!\n\n/teknoviral yazarak Reddit gündemini sesli video olarak alabilirsin.")

    async def cmd_teknoviral(self, update: Update, context: CallbackContext):
        status = await update.message.reply_text("🌐 Veriler çekiliyor...")
        
        try:
            # 1. Reddit
            news = await self.engine.get_reddit_news()
            if not news:
                await status.edit_text("❌ Haber bulunamadı.")
                return

            # 2. Groq & TTS
            await status.edit_text("🎙️ Seslendiriliyor...")
            metin = self.engine.process_with_groq(news['title'])
            audio_file = f"audio_{update.message.message_id}.mp3"
            tts = gTTS(text=metin, lang='tr')
            tts.save(audio_file)

            # 3. Pexels Video
            await status.edit_text("🎬 Video arka planı hazırlanıyor...")
            video_url = await self.engine.fetch_pexels_video()

            # 4. Gönderim
            caption = f"📰 **Gündem:** {news['title']}\n\n🔗 [Kaynağa Git]({news['link']})"
            
            if video_url:
                await update.message.reply_video(video=video_url, caption=caption, parse_mode="Markdown")
            
            with open(audio_file, "rb") as audio:
                await update.message.reply_audio(audio=audio, title="Teknoloji Gündemi")

            # Temizlik
            if os.path.exists(audio_file):
                os.remove(audio_file)
            await status.delete()

        except Exception as e:
            logger.error(f"İşlem Hatası: {e}")
            await status.edit_text(f"⚠️ Hata oluştu: {str(e)}")

    def run(self):
        logger.info("📡 Bot dinlemeye başladı...")
        self.app.run_polling(drop_pending_updates=True)

# --- ANA PROGRAM ---
if __name__ == "__main__":
    cfg = Config()
    
    if not cfg.TELEGRAM_BOT_TOKEN:
        logger.critical("HATA: Bot Token bulunamadı!")
        sys.exit(1)

    # Render için HTTP sunucusunu arka planda başlat
    threading.Thread(target=run_dummy_server, daemon=True).start()

    # Bot motorunu çalıştır
    bot = TelegramBot(cfg)
    try:
        bot.run()
    except Exception as e:
        logger.error(f"Bot durduruldu: {e}")
