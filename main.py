import os
import sys
import threading
import http.server
import socketserver
import feedparser
import httpx
import random
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

class ContentEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        self.groq_client = Groq(api_key=cfg.GROQ_API_KEY) if cfg.GROQ_API_KEY else None

    async def get_google_tech_news(self):
        url = "https://news.google.com/rss/search?q=technology+when:1d&hl=en-US&gl=US&ceid=US:en"
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    feed = feedparser.parse(response.text)
                    if feed.entries:
                        return {"title": feed.entries[0].title, "link": feed.entries[0].link}
            except Exception as e:
                logger.error(f"Haber çekme hatası: {e}")
        return None

    def process_with_groq(self, news_title):
        prompt = f"Şu haberi viral bir kısa video için heyecanlı bir dille Türkçe özetle. Sadece seslendirilecek metni ver: {news_title}"
        try:
            completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            return completion.choices[0].message.content
        except:
            return f"Yeni bir teknoloji gelişmesi: {news_title}"

    async def fetch_pexels_video(self, query="artificial intelligence"):
        if not self.cfg.PEXELS_API_KEY: return None
        headers = {"Authorization": self.cfg.PEXELS_API_KEY}
        # HD ve Portrait (Dikey) videoları zorla
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=5&orientation=portrait&size=medium"
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.get(url, headers=headers)
                data = response.json()
                if data.get('videos'):
                    # Filtreleme: En az 10 saniyelik ve video dosyası olanları seç
                    valid_videos = [v for v in data['videos'] if v['duration'] > 5]
                    video = random.choice(valid_videos if valid_videos else data['videos'])
                    # En yüksek kaliteli mp4 linkini bul (genellikle linklerin içinde hd/sd yazar)
                    video_files = video['video_files']
                    best_link = sorted(video_files, key=lambda x: x.get('width', 0), reverse=True)[0]['link']
                    return best_link
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
        await update.message.reply_text("🚀 Protokolos Hazır! /teknoviral komutunu kullanın.")

    async def cmd_teknoviral(self, update: Update, context: CallbackContext):
        status = await update.message.reply_text("🎬 Video ve Ses hazırlanıyor...")
        
        try:
            news = await self.engine.get_google_tech_news()
            if not news:
                await status.edit_text("⚠️ Haber alınamadı.")
                return

            metin = self.engine.process_with_groq(news['title'])
            video_url = await self.engine.fetch_pexels_video()
            
            # Ses dosyasını geçici olarak oluştur
            audio_path = f"audio_{update.message.message_id}.mp3"
            tts = gTTS(text=metin, lang='tr')
            tts.save(audio_path)

            caption = f"📰 **Gündem:** {news['title']}\n\n🎙️ **Özet:** {metin}"

            # --- GÖNDERİM STRATEJİSİ ---
            # Birleştirme işlemi (Render'da riskli olduğu için) yerine 
            # videoyu gönderip sesi onun 'ses izi' gibi algılanması için hemen peşine atıyoruz.
            # Şimdilik kullanıcı deneyimi için videoyu üstte, sesi altta tutuyoruz.
            
            if video_url:
                # Videoyu gönder
                sent_video = await update.message.reply_video(
                    video=video_url, 
                    caption=caption, 
                    parse_mode="Markdown"
                )
                # Sesi, videonun altına 'cevap' olarak gönder (Böylece daha bütünleşik görünür)
                with open(audio_path, "rb") as audio:
                    await update.message.reply_audio(
                        audio=audio, 
                        title="Haber Seslendirmesi",
                        reply_to_message_id=sent_video.message_id
                    )
            
            if os.path.exists(audio_path): os.remove(audio_path)
            await status.delete()

        except Exception as e:
            logger.error(f"Hata: {e}")
            await status.edit_text("⚠️ Bir hata oluştu.")

    def run(self):
        self.app.run_polling(drop_pending_updates=True)

# --- PORT VE START ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    cfg = Config()
    threading.Thread(target=run_dummy_server, daemon=True).start()
    TelegramBot(cfg).run()
