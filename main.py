"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           INSTAGRAM REELS BOT - MINIMUM VERSİYON                           ║
║                                                                              ║
║  Bu bot, Render'da sorunsuz çalışacak minimum versiyondur.                  ║
║  Video özellikleri devre dışı bırakılmıştır.                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ═══════════════════════════════════════════════════════════════════════════════
# TEMEL İMPORTLAR
# ═══════════════════════════════════════════════════════════════════════════════

import os
import sys
import re
import sqlite3
from pathlib import Path
from typing import List

import httpx
import feedparser
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
)
from loguru import logger

# ═══════════════════════════════════════════════════════════════════════════════
# LOGLAMA - Önce loglamayı kur
# ═══════════════════════════════════════════════════════════════════════════════

def setup_logging():
    """Loglama sistemini kurar"""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG"
    )
    logger.add(
        "bot.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
    )
    return logger

# ═══════════════════════════════════════════════════════════════════════════════
# YAPILANDIRMA - Ortam değişkenlerini yükle
# ═══════════════════════════════════════════════════════════════════════════════

def load_env():
    """Ortam değişkenlerini .env dosyasından yükle"""
    env_path = Path(".env")
    if env_path.exists():
        logger.info(".env dosyası bulundu, yükleniyor...")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    try:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())
                        logger.debug(f"  {key.strip()} = ***")
                    except:
                        pass
    else:
        logger.warning(".env dosyası bulunamadı")

# Ortam değişkenlerini yükle
load_env()

# Telegram Ayarları
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Groq AI Ayarları
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

# Pexels Ayarları
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# İçerik Kaynakları
RSS_FEEDS = os.getenv(
    "RSS_FEEDS",
    "https://www.theverge.com/rss/index.xml,https://feeds.feedburner.com/TechCrunch/"
).split(",")

REDDIT_SUBREDDITS = os.getenv("REDDIT_SUBREDDITS", "technology,programming,artificial").split(",")

CONTENT_NICHE = os.getenv("CONTENT_NICHE", "technology")

# ═══════════════════════════════════════════════════════════════════════════════
# YARDIMCI SINIFLAR
# ═══════════════════════════════════════════════════════════════════════════════

class ContentItem:
    """İçerik öğesi"""
    def __init__(self, title: str, description: str, url: str, source: str):
        self.title = title
        self.description = description
        self.url = url
        self.source = source


class GeneratedContent:
    """Üretilen içerik"""
    def __init__(self, original: ContentItem, headline: str, script: str, hashtags: List[str]):
        self.original_content = original
        self.headline = headline
        self.script = script
        self.hashtags = hashtags
        self.caption = f"{headline}\n\n{' '.join(hashtags[:10])}"


# ═══════════════════════════════════════════════════════════════════════════════
# VERİTABANI
# ═══════════════════════════════════════════════════════════════════════════════

class Database:
    """Basit SQLite veritabanı"""

    def __init__(self):
        logger.info("Veritabanı başlatılıyor...")
        self.db_path = Path("data") / "bot.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Veritabanı yolu: {self.db_path}")
        self.init_db()
        logger.info("Veritabanı hazır")

    def init_db(self):
        """Veritabanını başlatır"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS contents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        description TEXT,
                        url TEXT,
                        source TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.debug("Veritabanı tabloları oluşturuldu")
        except Exception as e:
            logger.error(f"Veritabanı hatası: {e}")
            raise

    def save_content(self, content: ContentItem) -> int:
        """İçeriği kaydeder"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO contents (title, description, url, source) VALUES (?, ?, ?, ?)",
                    (content.title, content.description, content.url, content.source)
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"İçerik kaydetme hatası: {e}")
            return -1

    def get_recent_content(self, limit: int = 10) -> List[ContentItem]:
        """Son içerikleri getirir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT title, description, url, source FROM contents ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
                rows = cursor.fetchall()
                return [ContentItem(r[0], r[1], r[2], r[3]) for r in rows]
        except Exception as e:
            logger.error(f"İçerik getirme hatası: {e}")
            return []


# ═══════════════════════════════════════════════════════════════════════════════
# İÇERİK TOPLAYICI
# ═══════════════════════════════════════════════════════════════════════════════

class ContentFetcher:
    """RSS feed'lerden içerik toplayıcı"""

    def __init__(self):
        self.rss_feeds = RSS_FEEDS
        self.subreddits = REDDIT_SUBREDDITS
        self.keywords = self._get_keywords()
        logger.info(f"Anahtar kelimeler: {self.keywords}")

    def _get_keywords(self) -> List[str]:
        """Nişe göre anahtar kelimeleri döndürür"""
        keywords_map = {
            "technology": ["tech", "ai", "software", "digital", "innovation", "startup"],
            "business": ["business", "finance", "market", "investment", "economy"],
            "science": ["science", "research", "discovery", "study", "experiment"],
        }
        return keywords_map.get(CONTENT_NICHE, keywords_map["technology"])

    async def fetch_all(self) -> List[ContentItem]:
        """Tüm kaynaklardan içerik toplar"""
        logger.info("İçerik toplama başladı")
        contents = []

        # RSS feed'lerden çek
        logger.info(f"RSS feed'leri taranıyor: {len(self.rss_feeds)} feed")
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:
                    title = entry.get("title", "")
                    summary = self._clean_html(entry.get("summary", ""))
                    if self._matches_keywords(title, summary):
                        contents.append(ContentItem(
                            title=title[:200],
                            description=summary[:500],
                            url=entry.get("link", ""),
                            source=self._extract_domain(feed_url)
                        ))
            except Exception as e:
                logger.error(f"RSS hatası ({feed_url}): {e}")

        # Reddit'ten çek
        logger.info(f"Reddit subreddit'leri taranıyor: {len(self.subreddits)}")
        for subreddit in self.subreddits:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                headers = {"User-Agent": "InstagramReelsBot/1.0"}
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers, timeout=10.0)
                    data = response.json()
                    posts = data.get("data", {}).get("children", [])
                    for post in posts[:5]:
                        post_data = post.get("data", {})
                        title = post_data.get("title", "")
                        self_text = post_data.get("selftext", "")
                        if self._matches_keywords(title, self_text):
                            contents.append(ContentItem(
                                title=title[:200],
                                description=self_text[:500] if self_text else "Reddit post",
                                url=f"https://reddit.com{post_data.get('permalink', '')}",
                                source=f"r/{subreddit}"
                            ))
            except Exception as e:
                logger.error(f"Reddit hatası (r/{subreddit}): {e}")

        # Benzersiz olanları döndür
        seen = set()
        unique = []
        for c in contents:
            if c.title not in seen:
                seen.add(c.title)
                unique.append(c)

        logger.info(f"Toplam {len(unique)} benzersiz içerik bulundu")
        return unique[:20]

    def _matches_keywords(self, title: str, text: str) -> bool:
        """Anahtar kelime eşleşmesi kontrol eder"""
        combined = (title + " " + text).lower()
        return any(kw.lower() in combined for kw in self.keywords)

    def _clean_html(self, html: str) -> str:
        """HTML temizler"""
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text().strip()

    def _extract_domain(self, url: str) -> str:
        """Domain çıkarır"""
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else url


# ═══════════════════════════════════════════════════════════════════════════════
# AI İÇERİK ÜRETİCİ
# ═══════════════════════════════════════════════════════════════════════════════

class AIContentGenerator:
    """Groq API ile içerik üretici"""

    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL
        logger.info(f"AI Generator başlatıldı (model: {self.model})")

    async def generate(self, content: ContentItem) -> GeneratedContent:
        """İçerikten senaryo üretir"""
        logger.info(f"AI içerik üretiyor: {content.title[:50]}...")

        prompt = f"""Aşağıdaki haber veya bilgiyi Instagram Reels formatında içeriğe dönüştür:

BAŞLIK: {content.title}
İÇERİK: {content.description}
KAYNAK: {content.source}

Lütfen şu formatta yanıt ver:

## BAŞLIK
[Dikkat çekici bir başlık - max 100 karakter]

## SENARYO
[Video için voiceover metni - 30-60 saniye, Türkçe, konuşma dili]

## HASHTAGLER
[10 adet hashtag, virgülle ayrılmış]"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "Sen profesyonel bir içerik üreticisisin. Instagram Reels için ilgi çekici ve bilgilendirici içerikler üretirsin."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 1024,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )

                result = response.json()
                content_text = result["choices"][0]["message"]["content"]
                logger.info("AI içerik üretimi başarılı")
                return self._parse_response(content_text, content)

        except Exception as e:
            logger.error(f"Groq API hatası: {e}")
            # Fallback: basit içerik döndür
            return GeneratedContent(
                original=content,
                headline=content.title[:100],
                script=content.description[:300],
                hashtags=["#teknoloji", "#haber", "#reels", "#viral", "#trend"]
            )

    def _parse_response(self, response: str, original: ContentItem) -> GeneratedContent:
        """AI yanıtını ayrıştırır"""
        lines = response.strip().split("\n")

        headline = original.title[:100]
        script = original.description[:300]
        hashtags = ["#teknoloji", "#haber", "#reels", "#viral", "#trend", "#instagood", "#ai", "#future"]

        for line in lines:
            line = line.strip()
            if line.startswith("## BAŞLIK"):
                continue
            elif line.startswith("## SENARYO"):
                continue
            elif line.startswith("## HASHTAGLER"):
                continue
            elif line and not line.startswith("#"):
                if not headline or headline == original.title[:100]:
                    headline = line[:100]
                elif not script or script == original.description[:300]:
                    script = line
                elif len(hashtags) == 8:
                    hashtags = [f"#{tag.strip().replace('#', '')}" for tag in line.split(",") if tag.strip()]
                    hashtags = [h for h in hashtags if h] or ["#teknoloji", "#haber", "#reels", "#viral", "#trend"]

        return GeneratedContent(original, headline, script, hashtags)


# ═══════════════════════════════════════════════════════════════════════════════
# PEXELS ARAÇLARI
# ═══════════════════════════════════════════════════════════════════════════════

class PexelsSearch:
    """Pexels video arama (video indirme devre dışı)"""

    def __init__(self):
        self.api_key = PEXELS_API_KEY
        logger.info(f"Pexels başlatıldı (API Key: {'Var' if self.api_key else 'Yok'})")

    async def search_videos(self, query: str, limit: int = 5) -> List[dict]:
        """Video arar"""
        if not self.api_key:
            logger.warning("Pexels API anahtarı yok, video aranamıyor")
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.pexels.com/videos/search",
                    headers={"Authorization": self.api_key},
                    params={"query": query, "per_page": limit, "orientation": "portrait"},
                    timeout=15.0
                )
                data = response.json()
                return data.get("videos", [])
        except Exception as e:
            logger.error(f"Pexels arama hatası: {e}")
            return []


# ═══════════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT
# ═══════════════════════════════════════════════════════════════════════════════

class TelegramBot:
    """Ana Telegram bot sınıfı"""

    def __init__(self):
        logger.info("Telegram Bot başlatılıyor...")
        self.app = None
        self.db = Database()
        self.fetcher = ContentFetcher()
        self.ai = AIContentGenerator()
        self.pexels = PexelsSearch()
        self.user_data = {}
        logger.info("Tüm modüller başarıyla yüklendi")

    async def start(self):
        """Botu başlatır"""
        logger.info("Bot başlatılıyor...")
        logger.info(f"TELEGRAM_BOT_TOKEN uzunluğu: {len(TELEGRAM_BOT_TOKEN)} karakter")

        # Token kontrolü
        if not TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN ayarlanmamış!")
            raise ValueError("TELEGRAM_BOT_TOKEN ayarlanmamış!")

        logger.info("Telegram Application oluşturuluyor...")

        # Application oluştur
        try:
            self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
            logger.info("Telegram Application oluşturuldu")
        except Exception as e:
            logger.error(f"Application oluşturma hatası: {e}")
            raise

        # Handler'ları kaydet
        logger.info("Handler'lar kaydediliyor...")
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("fetch", self.cmd_fetch))
        self.app.add_handler(CommandHandler("generate", self.cmd_generate))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        logger.info("Handler'lar kaydedildi")

        logger.info("Bot çalışmaya başlıyor...")
        await self.app.run_polling(allowed_updates=Update.ALL_TYPES)

    async def cmd_start(self, update: Update, context: CallbackContext):
        """Başlangıç komutu"""
        welcome = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║  Merhaba! Instagram Reels Botuna hoş geldin!                    ║
║                                                               ║
║  /start   - Bu menüyü gösterir                                 ║
║  /help    - Kullanım kılavuzunu gösterir                       ║
║  /status  - Sistem durumunu gösterir                            ║
║  /fetch   - İçerik araştırır                                  ║
║  /generate - AI ile içerik üretir                              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
        """
        await update.message.reply_text(welcome)

    async def cmd_help(self, update: Update, context: CallbackContext):
        """Yardım komutu"""
        help_text = """
📚 KULLANIM KILAVUZU

1. /fetch yazın → Bot RSS ve Reddit'ten içerik bulur
2. /generate yazın → Seçtiğiniz içerikten AI senaryo üretir
3. Senaryoyu kullanarak video oluşturabilirsiniz

⚙️ NOT: Video oluşturma özellikleri yakında eklenecek.
        """
        await update.message.reply_text(help_text)

    async def cmd_status(self, update: Update, context: CallbackContext):
        """Durum komutu"""
        status = f"""
📊 SİSTEM DURUMU

🤖 Bot: ✅ Aktif
📡 Groq AI: {'✅ Bağlı' if GROQ_API_KEY else '❌ Bağlı Değil'}
🎬 Pexels: {'✅ Bağlı' if PEXELS_API_KEY else '⚠️ API Anahtarı Yok'}
📸 Instagram: ⚠️ Yapılandırılmadı (Video özellikleri devre dışı)
📦 Veritabanı: ✅ Hazır
        """
        await update.message.reply_text(status)

    async def cmd_fetch(self, update: Update, context: CallbackContext):
        """İçerik bulma komutu"""
        user_id = update.effective_user.id
        await update.message.reply_text("📡 İçerikler araştırılıyor...")

        try:
            contents = await self.fetcher.fetch_all()

            if not contents:
                await update.message.reply_text("❌ Hiç içerik bulunamadı.")
                return

            # Veritabanına kaydet
            for c in contents:
                self.db.save_content(c)

            # İçerikleri göster
            keyboard = []
            for i, content in enumerate(contents[:10]):
                title = content.title[:50] + "..." if len(content.title) > 50 else content.title
                keyboard.append([
                    InlineKeyboardButton(f"📰 {title}", callback_data=f"view_{i}")
                ])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"✅ **{len(contents)} içerik bulundu!**\n\nBir içerik seçin:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

            self.user_data[user_id] = {"contents": contents}

        except Exception as e:
            logger.error(f"İçerik bulma hatası: {e}")
            await update.message.reply_text(f"❌ Hata: {str(e)}")

    async def cmd_generate(self, update: Update, context: CallbackContext):
        """İçerik üretme komutu"""
        user_id = update.effective_user.id

        contents = self.db.get_recent_content(limit=10)

        if not contents:
            await update.message.reply_text(
                "❌ Henüz içerik yok.\n\nLütfen önce /fetch komutunu kullanın."
            )
            return

        keyboard = []
        for i, content in enumerate(contents):
            title = content.title[:40] + "..." if len(content.title) > 40 else content.title
            keyboard.append([
                InlineKeyboardButton(f"✍️ {title}", callback_data=f"gen_{i}")
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "✍️ **İçerik Üretimi**\n\nBir içerik seçin ve AI senaryo üretsin:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

        self.user_data[user_id] = {"contents": contents}

    async def handle_callback(self, update: Update, context: CallbackContext):
        """Callback işleyici"""
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()

        data = query.data

        if data.startswith("view_"):
            # İçerik görüntüleme
            index = int(data.split("_")[1])
            if user_id in self.user_data and "contents" in self.user_data[user_id]:
                contents = self.user_data[user_id]["contents"]
                if index < len(contents):
                    c = contents[index]
                    text = f"""
📰 **{c.title}**

{c.description[:200]}...

🔗 Kaynak: {c.source}
🔗 URL: {c.url}

✍️ Bu içerikten senaryo üretmek için /generate yazın.
                    """
                    await query.message.edit_text(text, parse_mode="Markdown")

        elif data.startswith("gen_"):
            # AI ile içerik üretme
            index = int(data.split("_")[1])
            if user_id in self.user_data and "contents" in self.user_data[user_id]:
                contents = self.user_data[user_id]["contents"]
                if index < len(contents):
                    await query.message.edit_text("🤖 **AI içerik üretiyor...**")

                    try:
                        generated = await self.ai.generate(contents[index])

                        text = f"""
✅ **İçerik Üretildi!**

📌 **Başlık:** {generated.headline}

📝 **Senaryo:**
{generated.script[:300]}...

🏷️ **Hashtag'ler:**
{' '.join(generated.hashtags[:5])}...

⚙️ NOT: Video oluşturma özellikleri yakında eklenecek.
                        """
                        await query.message.edit_text(text, parse_mode="Markdown")

                    except Exception as e:
                        logger.error(f"İçerik üretme hatası: {e}")
                        await query.message.edit_text(f"❌ Hata: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# ANA FONKSİYON
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Ana asenkron fonksiyon"""
    logger.info("main() fonksiyonu başladı")
    bot = TelegramBot()
    try:
        logger.info("Bot.start() çağrılıyor...")
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot kapatılıyor (KeyboardInterrupt)...")
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

# ═══════════════════════════════════════════════════════════════════════════════
# BAŞLANGIÇ
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║           INSTAGRAM REELS BOT - MINIMUM VERSİYON                    ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝")
    print()
    print("Bot başlatılıyor...")
    print()

    # Loglamayı kur
    setup_logging()
    logger.info("=== BOT BAŞLATILIYOR ===")
    logger.info(f"Python sürümü: {sys.version}")
    logger.info(f"Çalışma dizini: {os.getcwd()}")
    logger.info(f"TELEGRAM_BOT_TOKEN mevcut: {'Evet' if TELEGRAM_BOT_TOKEN else 'Hayır'}")
    logger.info(f"GROQ_API_KEY mevcut: {'Evet' if GROQ_API_KEY else 'Hayır'}")

    if not TELEGRAM_BOT_TOKEN:
        print("❌ HATA: TELEGRAM_BOT_TOKEN ayarlanmamış!")
        print("   Lütfen .env dosyasını oluşturun veya ortam değişkenlerini ayarlayın.")
        print("   Render'da Environment Variables bölümünde TELEGRAM_BOT_TOKEN ekleyin.")
        exit(1)

    print("✅ Yapılandırma doğrulandı")
    print("📡 Bot başlatılıyor...")
    print()

    import asyncio
    asyncio.run(main())
