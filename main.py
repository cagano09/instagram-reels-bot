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
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        self.PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# --- İÇERİK MOTORU ---
class ContentEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        self.groq_client = Groq(api_key=cfg.GROQ_API_KEY)

    async def get_reddit_news(self):
        """Reddit r/technology üzerindeki en popüler haberi çeker."""
        url = "https://www.reddit.com/r/technology/top/.rss?t=day"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                feed = feedparser.parse(response.text)
                if feed.entries:
                    return {"title": feed.entries[0].title, "link": feed.entries[0].link}
        except Exception as e:
            logger.error(f"Reddit hatası: {e}")
        return None

    def process_with_groq(self, news_title):
        """Haber başlığını viral bir Reels metnine dönüştürür."""
        prompt = f"""
        Aşağıdaki teknoloji haberini Instagram Reels için çok dikkat çekici, heyecanlı bir Türkçe metne dönüştür. 
        Sadece seslendirilecek metni ver, ek açıklama yapma. 
        Haber: {news_title}
        """
        completion = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        return completion.choices[0].message.content

    async def fetch_pexels_video(self, query="future technology"):
        """Pexels üzerinden dikey video linki getirir."""
        headers = {"Authorization": self.cfg.PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation=portrait"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                data = response.json()
                if data.get('videos'):
                    return data['videos'][0]['video_files'][0]['link']
        except Exception as e:
            logger.error(f"Pexels hatası: {e}")
        return None

# --- RENDER PORT KANDIRMA ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()

# --- BOT SINIFI ---
class TelegramBot:
    def __init__(self, cfg):
        self.cfg = cfg
        self.engine = ContentEngine(cfg)
        self.app = Application.builder().token(cfg.TELEGRAM_BOT_TOKEN).build()
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("teknoviral", self.cmd_teknoviral))

    async def cmd_start(self, update: Update, context: CallbackContext):
        await update.message.reply_text("🤖 Protokolos Viral Motoru Hazır!\n\n/teknoviral yazarak günün haberini oluşturabilirsin.")

    async def cmd_teknoviral(self, update: Update, context: CallbackContext):
        msg = await update.message.reply_text("🌐 Reddit taranıyor ve seslendiriliyor...")
        
        # 1. Haber Çek
        news = await self.engine.get_reddit_news()
        if not news:
            await msg.edit_text("❌ Haber bulunamadı.")
            return

        # 2. Metinleştir ve Seslendir
        turkce_metin = self.engine.process_with_groq(news['title'])
        audio_path = "haber_ses.mp3"
        tts = gTTS(text=turkce_metin, lang='tr')
        tts.save(audio_path)

        # 3. Video Bul
        video_url = await self.engine.fetch_pexels_video()

        # 4. Gönder
        caption = f"📰 **Haber:** {news['title']}\n\n🔗 {news['link']}"
        if video_url:
            await update.message.reply_video(video=video_url, caption=caption, parse_mode="Markdown")
        
        with open(audio_path, "rb") as audio:
            await update.message.reply_audio(audio=audio, title="Günün Haberi")

        # Temizlik
        if os.path.exists(audio_path): os.remove(audio_path)
        await msg.delete()

    async def run(self):
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        logger.info("🤖 BOT AKTİF!")
        while True: await asyncio.sleep(3600)

async def main():
    cfg = Config()
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot = TelegramBot(cfg)
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
