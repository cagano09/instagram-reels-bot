import os
import sys
import threading
import http.server
import socketserver
import feedparser
import httpx
import random
import asyncio
import edge_tts  # Yeni ses kütüphanesi
from loguru import logger
from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# --- YAPILANDIRMA ---
class Config:
    def __init__(self):
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

class ContentEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        self.groq_client = Groq(api_key=cfg.GROQ_API_KEY) if cfg.GROQ_API_KEY else None

    async def get_google_tech_news(self):
        url = "https://news.google.com/rss/search?q=technology+breakthrough+OR+ai+news+when:1d&hl=tr&gl=TR&ceid=TR:tr"
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    feed = feedparser.parse(response.text)
                    if feed.entries:
                        entry = random.choice(feed.entries[:5])
                        return {"title": entry.title, "link": entry.link}
            except Exception as e:
                logger.error(f"Haber çekme hatası: {e}")
        return None

    def process_with_groq(self, news_title):
        # Tamamen Türkçe ve doğal konuşma akışı için güncellenen prompt
        prompt = (
            f"Sen bir teknoloji içerik üreticisisin. Aşağıdaki haberi, YouTube Shorts veya Instagram Reels videosu için "
            f"tamamen doğal, heyecanlı ve akıcı bir Türkçeyle anlat. "
            f"Cümleler kısa ve etkileyici olsun. Yabancı terimleri Türkçe karşılıklarıyla kullanmaya çalış. "
            f"Sadece seslendirilecek konuşma metnini ver, 'Merhaba' veya 'Giriş' gibi başlıklar ekleme. "
            f"Haber başlığı: {news_title}"
        )
        try:
            completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            return completion.choices[0].message.content
        except:
            return f"Teknoloji dünyasında bugün çok önemli bir gelişme var. İşte detaylar: {news_title}"

    async def fetch_pexels_video(self, query="high tech"):
        if not self.cfg.PEXELS_API_KEY: return None
        headers = {"Authorization": self.cfg.PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=20&orientation=portrait&size=large"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers)
                data = response.json()
                if data.get('videos'):
                    # En az 30 saniyelik videoları bul
                    long_videos = [v for v in data['videos'] if v.get('duration', 0) >= 30]
                    if not long_videos:
                        long_videos = sorted(data['videos'], key=lambda x: x.get('duration', 0), reverse=True)
                    
                    chosen_video = long_videos[0]
                    video_files = chosen_video.get('video_files', [])
                    mp4_files = [f for f in video_files if '.mp4' in f.get('link', '').lower()]
                    
                    if mp4_files:
                        best_file = sorted(mp4_files, key=lambda x: x.get('width', 0), reverse=True)[0]
                        return best_file['link']
            except Exception as e:
                logger.error(f"Pexels Hatası: {e}")
        return None

# --- TELEGRAM BOT ---
class TelegramBot:
    def __init__(self, cfg):
        self.cfg = cfg
        self.engine = ContentEngine(cfg)
        self.app = Application.builder().token(cfg.TELEGRAM_BOT_TOKEN).job_queue(None).build()
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("teknoviral", self.cmd_teknoviral))

    async def cmd_start(self, update: Update, context: CallbackContext):
        await update.message.reply_text("🚀 Protokolos Hazır! /teknoviral ile profesyonel Türkçe içerikler üretebilirsin.")

    async def cmd_teknoviral(self, update: Update, context: CallbackContext):
        status = await update.message.reply_text("🎬 Profesyonel video ve erkek sesi hazırlanıyor...")
        
        try:
            news = await self.engine.get_google_tech_news()
            if not news:
                await status.edit_text("⚠️ Haber kaynağına ulaşılamadı.")
                return

            metin = self.engine.process_with_groq(news['title'])
            audio_path = f"audio_{update.message.message_id}.mp3"
            
            # --- PROFESYONEL ERKEK SESİ (Microsoft Ahmet) ---
            communicate = edge_tts.Communicate(metin, "tr-TR-AhmetNeural")
            await communicate.save(audio_path)

            video_url = await self.engine.fetch_pexels_video()
            
            caption = f"📹 **Günün Gündemi:** {news['title']}\n\n🎙️ **Özet:** {metin}"
            
            if video_url:
                sent_video = await update.message.reply_video(
                    video=video_url, 
                    caption=caption, 
                    parse_mode="Markdown"
                )
                
                with open(audio_path, "rb") as audio:
                    await update.message.reply_audio(
                        audio=audio, 
                        title="Protokolos Seslendirme",
                        reply_to_message_id=sent_video.message_id
                    )
            else:
                await update.message.reply_text("Video bulunamadı, haber metni hazırlandı.")

            if os.path.exists(audio_path): os.remove(audio_path)
            await status.delete()

        except Exception as e:
            logger.error(f"Hata: {e}")
            await status.edit_text(f"⚠️ Bir hata oluştu: {str(e)}")

    def run(self):
        self.app.run_polling(drop_pending_updates=True)

# --- RENDER SERVER ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    cfg = Config()
    threading.Thread(target=run_dummy_server, daemon=True).start()
    TelegramBot(cfg).run()
