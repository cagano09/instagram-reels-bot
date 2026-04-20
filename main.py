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
        if cfg.GROQ_API_KEY:
            self.groq_client = Groq(api_key=cfg.GROQ_API_KEY)
        else:
            self.groq_client = None

    async def get_google_tech_news(self):
        # Reddit engelini aşmak için Google News RSS kullanıyoruz (Çok daha stabil)
        url = "https://news.google.com/rss/search?q=technology+when:1d&hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                logger.info("Google News taranıyor...")
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    feed = feedparser.parse(response.text)
                    if feed.entries:
                        # En güncel haberi al
                        entry = feed.entries[0]
                        logger.info(f"✅ Haber çekildi: {entry.title}")
                        return {"title": entry.title, "link": entry.link}
                else:
                    logger.error(f"Google News Hatası: {response.status_code}")
            except Exception as e:
                logger.error(f"Haber çekme hatası: {e}")
        
        return None

    def process_with_groq(self, news_title):
        if not self.groq_client:
            return "Haber detayı analiz edilemedi."
        
        prompt = f"Şu teknoloji haberini viral bir kısa video için heyecanlı, akıcı bir Türkçe ile özetle. Sadece seslendirilecek metni ver, ek açıklama yapma: {news_title}"
        try:
            completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq Hatası: {e}")
            return f"Teknoloji dünyasında yeni gelişme: {news_title}"

    async def fetch_pexels_video(self, query="future technology"):
        if not self.cfg.PEXELS_API_KEY:
            return None
        
        headers = {"Authorization": self.cfg.PEXELS_API_KEY}
        # Arama terimini çeşitlendiriyoruz
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=3&orientation=portrait"
        try:
            async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                data = response.json()
                if data.get('videos'):
                    # Rastgele bir video seç (hep aynısı gelmesin)
                    import random
                    video = random.choice(data['videos'])
                    return video['video_files'][0]['link']
        except Exception as e:
            logger.error(f"Pexels Hatası: {e}")
        return None

# --- RENDER PORT DİNLEYİCİ ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            logger.info(f"✅ Port {port} aktif.")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Sunucu Hatası: {e}")

# --- TELEGRAM BOT ---
class TelegramBot:
    def __init__(self, cfg):
        self.cfg = cfg
        self.engine = ContentEngine(cfg)
        self.app = (
            Application.builder()
            .token(cfg.TELEGRAM_BOT_TOKEN)
            .job_queue(None) 
            .build()
        )
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("teknoviral", self.cmd_teknoviral))

    async def cmd_start(self, update: Update, context: CallbackContext):
        await update.message.reply_text("🚀 Protokolos Bot Hazır!\n\n/teknoviral yazarak en güncel teknoloji haberini video olarak alabilirsin.")

    async def cmd_teknoviral(self, update: Update, context: CallbackContext):
        status = await update.message.reply_text("🔍 Güncel haberler taranıyor...")
        
        try:
            # 1. Google News'ten Haber Çek
            news = await self.engine.get_google_tech_news()
            if not news:
                await status.edit_text("⚠️ Haber kaynağına şu an ulaşılamıyor.")
                return

            # 2. İşleme ve Seslendirme
            await status.edit_text("🎙️ Haber seslendiriliyor...")
            metin = self.engine.process_with_groq(news['title'])
            
            audio_file = f"audio_{update.message.message_id}.mp3"
            tts = gTTS(text=metin, lang='tr')
            tts.save(audio_file)

            # 3. Video Bulma
            await status.edit_text("🎬 Video hazırlanıyor...")
            video_url = await self.engine.fetch_pexels_video()

            # 4. Gönderim
            caption = f"🔥 **Günün Teknoloji Gündemi**\n\n{news['title']}\n\n#teknoloji #haber #protokolos"
            
            if video_url:
                await update.message.reply_video(video=video_url, caption=caption, parse_mode="Markdown")
            
            with open(audio_file, "rb") as audio:
                await update.message.reply_audio(audio=audio, title="Teknoloji Özeti")

            if os.path.exists(audio_file):
                os.remove(audio_file)
            await status.delete()

        except Exception as e:
            logger.error(f"Hata: {e}")
            await status.edit_text("⚠️ Bir hata oluştu, tekrar deneniyor...")

    def run(self):
        logger.info("📡 Bot çalışıyor...")
        self.app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    cfg = Config()
    if not cfg.TELEGRAM_BOT_TOKEN:
        sys.exit(1)

    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot = TelegramBot(cfg)
    bot.run()
