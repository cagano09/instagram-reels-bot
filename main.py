"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           INSTAGRAM REELS BOT - RENDER OPTİMİZE VERSİYON                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import re
import sqlite3
import traceback
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any

# Loglama Sistemi
def setup_logging() -> None:
    try:
        from loguru import logger
        logger.remove()
        logger.add(sys.stderr, format="<red>{time:YYYY-MM-DD HH:mm:ss}</red> | <level>{level: <8}</level> | <level>{message}</level>", level="DEBUG", colorize=True)
    except ImportError:
        import logging
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s | %(levelname)-8s | %(message)s", handlers=[logging.StreamHandler(sys.stderr)])

setup_logging()

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger("bot")

import httpx
import feedparser
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackContext, CallbackQueryHandler, CommandHandler

# --- YAPILANDIRMA SINIFI ---
class Config:
    def __init__(self):
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        self.GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
        self.PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
        self.RSS_FEEDS = [f.strip() for f in os.getenv("RSS_FEEDS", "https://www.theverge.com/rss/index.xml").split(",") if f.strip()]
        self.REDDIT_SUBREDDITS = [s.strip() for s in os.getenv("REDDIT_SUBREDDITS", "technology").split(",") if s.strip()]
        self.CONTENT_NICHE = os.getenv("CONTENT_NICHE", "technology")
        self.DB_PATH = Path("data") / "bot.db"
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    def validate(self):
        if not self.TELEGRAM_BOT_TOKEN: return False, "TELEGRAM_BOT_TOKEN eksik!"
        return True, "Yapılandırma OK"

    def get_keywords(self):
        return ["tech", "ai", "software", "innovation"]

# --- YARDIMCI SINIFLAR ---
class ContentItem:
    def __init__(self, title, description, url, source):
        self.title, self.description, self.url, self.source = title, description, url, source

class GeneratedContent:
    def __init__(self, original, headline, script, hashtags):
        self.headline, self.script, self.hashtags = headline, script, hashtags

# --- VERİTABANI ---
class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS contents (id INTEGER PRIMARY KEY, title TEXT, description TEXT, url TEXT, source TEXT)")

    def save_content(self, c):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO contents (title, description, url, source) VALUES (?, ?, ?, ?)", (c.title, c.description, c.url, c.source))

    def get_recent_content(self, limit=10):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT title, description, url, source FROM contents ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [ContentItem(r[0], r[1], r[2], r[3]) for r in rows]

# --- İÇERİK TOPLAYICI ---
class ContentFetcher:
    def __init__(self, cfg):
        self.rss_feeds = cfg.RSS_FEEDS
        self.keywords = cfg.get_keywords()

    async def fetch_all(self):
        contents = []
        for url in self.rss_feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]:
                    contents.append(ContentItem(entry.title, entry.get("summary", ""), entry.link, "RSS"))
            except Exception as e: logger.error(f"RSS Hatası: {e}")
        return contents

# --- AI ÜRETİCİ ---
class AIContentGenerator:
    def __init__(self, cfg):
        self.api_key = cfg.GROQ_API_KEY
        self.model = cfg.GROQ_MODEL

    async def generate(self, content):
        if not self.api_key: return self._fallback(content)
        # Basitleştirilmiş Groq isteği
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "messages": [{"role": "user", "content": f"Translate this tech news to viral Turkish Reels script: {content.title}"}], "temperature": 0.7},
                    timeout=20.0)
                data = res.json()
                text = data["choices"][0]["message"]["content"]
                return GeneratedContent(content, "Başlık", text, ["#tech"])
        except: return self._fallback(content)

    def _fallback(self, content):
        return GeneratedContent(content, content.title, content.description, ["#tech"])

# --- ANA BOT SINIFI ---
class TelegramBot:
    def __init__(self, cfg):
        self.config = cfg
        self.db = Database(cfg.DB_PATH)
        self.fetcher = ContentFetcher(cfg)
        self.ai = AIContentGenerator(cfg)
        self.app = Application.builder().token(cfg.TELEGRAM_BOT_TOKEN).build()
        self.user_data = {}

        # Handler'lar
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("fetch", self.cmd_fetch))
        self.app.add_handler(CommandHandler("generate", self.cmd_generate))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

    async def start(self):
        """Render ve Asyncio için optimize edilmiş başlatma"""
        logger.info("Bot ayağa kalkıyor...")
        
        async with self.app:
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            
            logger.info("🤖 BOT AKTİF VE MESAJ BEKLİYOR")
            
            # Botun açık kalmasını sağlayan döngü
            try:
                while True:
                    await asyncio.sleep(3600)
            except (KeyboardInterrupt, asyncio.CancelledError):
                logger.info("Bot kapatılıyor...")
                await self.app.updater.stop()
                await self.app.stop()

    async def cmd_start(self, update: Update, context: CallbackContext):
        await update.message.reply_text("🤖 Reels Bot Aktif!\n\n/fetch - İçerik Bul\n/generate - Senaryo Üret")

    async def cmd_fetch(self, update: Update, context: CallbackContext):
        await update.message.reply_text("📡 İçerikler çekiliyor...")
        items = await self.fetcher.fetch_all()
        for item in items[:5]: self.db.save_content(item)
        
        keyboard = [[InlineKeyboardButton(f"📰 {c.title[:40]}", callback_data=f"v_{i}")] for i, c in enumerate(items[:5])]
        self.user_data[update.effective_user.id] = items
        await update.message.reply_text("İçerik seçin:", reply_markup=InlineKeyboardMarkup(keyboard))

    async def cmd_generate(self, update: Update, context: CallbackContext):
        contents = self.db.get_recent_content(5)
        if not contents:
            await update.message.reply_text("Önce /fetch yapın.")
            return
        keyboard = [[InlineKeyboardButton(f"✍️ {c.title[:40]}", callback_data=f"g_{i}")] for i, c in enumerate(contents)]
        self.user_data[update.effective_user.id] = contents
        await update.message.reply_text("Senaryo için seçin:", reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_callback(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        data = query.data

        if user_id not in self.user_data: return

        index = int(data.split("_")[1])
        content = self.user_data[user_id][index]

        if data.startswith("v_"):
            await query.message.edit_text(f"📰 {content.title}\n\n{content.url}")
        elif data.startswith("g_"):
            await query.message.edit_text("🤖 AI senaryo yazıyor...")
            gen = await self.ai.generate(content)
            await query.message.edit_text(f"✅ SENARYO:\n\n{gen.script}")

# --- ENTRY POINT ---
async def main():
    cfg = Config()
    valid, msg = cfg.validate()
    if not valid:
        logger.error(msg)
        return
    
    bot = TelegramBot(cfg)
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
