"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           INSTAGRAM REELS BOT - GÜVENİLİR VERSİYON                          ║
║                                                                              ║
║  Render deployment için optimize edilmiş, hata yakalayıcılı versiyon.       ║
║  Tüm modüller ayrı ayrı başlatılır ve hatalar detaylı loglanır.             ║
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
import traceback
from pathlib import Path
from typing import List, Optional, Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# LOGLAMA SİSTEMİ - ÖNCE KURULMALIDIR
# ═══════════════════════════════════════════════════════════════════════════════

def setup_logging() -> None:
    """
    Loglama sistemini kurar.
    Render'da görünmesi için sys.stderr'e yazar.
    """
    try:
        # Varolan handler'ları temizle
        try:
            from loguru import logger
            logger.remove()
        except:
            pass
        
        # Konsola (stderr) yaz - Render loglarında görünür
        sys.stderr.write(">>> Loglama sistemi kuruluyor...\n")
        sys.stderr.flush()
        
        try:
            from loguru import logger
            
            # Konsol çıktısı
            logger.add(
                sys.stderr,
                format="<red>{time:YYYY-MM-DD HH:mm:ss}</red> | <level>{level: <8}</level> | <level>{message}</level>",
                level="DEBUG",
                colorize=True
            )
            
            # Dosya çıktısı (opsiyonel)
            log_file = Path("logs") / "bot.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            logger.add(
                str(log_file),
                rotation="10 MB",
                retention="7 days",
                level="DEBUG",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
            )
            
            sys.stderr.write(">>> Loglama sistemi başarıyla kuruldu\n")
            sys.stderr.flush()
            
        except ImportError:
            # loguru yoksa standart logging kullan
            import logging
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s | %(levelname)-8s | %(message)s",
                handlers=[
                    logging.StreamHandler(sys.stderr),
                    logging.FileHandler("bot.log", encoding="utf-8")
                ]
            )
            sys.stderr.write(">>> loguru bulunamadı, standart logging kullanılıyor\n")
            sys.stderr.flush()
            
    except Exception as e:
        sys.stderr.write(f"!!! Loglama kurulum hatası: {e}\n")
        sys.stderr.flush()

# Loglamayı hemen kur
setup_logging()

# Loguru import et veya yoksa standart logger kullan
try:
    from loguru import logger
    logger.info("Loguru loglama sistemi aktif")
except ImportError:
    import logging
    logger = logging.getLogger("bot")
    logger.info("Standart logging sistemi aktif")

# ═══════════════════════════════════════════════════════════════════════════════
# YAPILANDIRMA - ORTAM DEĞİŞKENLERİ
# ═══════════════════════════════════════════════════════════════════════════════

def load_env_file() -> None:
    """Ortam değişkenlerini .env dosyasından yükle"""
    env_path = Path(".env")
    
    if env_path.exists():
        logger.info(".env dosyası bulundu, yükleniyor...")
        sys.stderr.write(">>> .env dosyası yükleniyor...\n")
        sys.stderr.flush()
        
        loaded_count = 0
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    try:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())
                        loaded_count += 1
                    except Exception as e:
                        logger.warning(f".env satırı atlandı: {line[:30]}... ({e})")
        
        logger.info(f"{loaded_count} ortam değişkeni .env'den yüklendi")
        sys.stderr.write(f">>> {loaded_count} ortam değişkeni yüklendi\n")
        sys.stderr.flush()
    else:
        logger.warning(".env dosyası bulunamadı, sadece sistem ortam değişkenleri kullanılacak")
        sys.stderr.write(">>> .env dosyası bulunamadı\n")
        sys.stderr.flush()

# Ortam değişkenlerini yükle
load_env_file()

# ═══════════════════════════════════════════════════════════════════════════════
# YAPILANDIRMA - DEĞİŞKENLERİ AL
# ═══════════════════════════════════════════════════════════════════════════════

class Config:
    """Yapılandırma sınıfı - tüm ortam değişkenlerini yönetir"""
    
    def __init__(self):
        logger.info("Yapılandırma yükleniyor...")
        sys.stderr.write(">>> Yapılandırma yükleniyor...\n")
        sys.stderr.flush()
        
        # Telegram
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        # Groq AI
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        self.GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
        
        # Pexels
        self.PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
        
        # RSS Feeds
        rss_raw = os.getenv(
            "RSS_FEEDS",
            "https://www.theverge.com/rss/index.xml,https://feeds.feedburner.com/TechCrunch/"
        )
        self.RSS_FEEDS = [f.strip() for f in rss_raw.split(",") if f.strip()]
        
        # Reddit
        reddit_raw = os.getenv("REDDIT_SUBREDDITS", "technology,programming,artificial")
        self.REDDIT_SUBREDDITS = [s.strip() for s in reddit_raw.split(",") if s.strip()]
        
        # Niş
        self.CONTENT_NICHE = os.getenv("CONTENT_NICHE", "technology")
        
        # Veritabanı yolu
        self.DB_PATH = Path("data") / "bot.db"
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Log yapılandırması
        self._log_config()
        
    def _log_config(self) -> None:
        """Yapılandırmayı logla"""
        logger.info("=" * 50)
        logger.info("YAPILANDIRMA DURUMU")
        logger.info("=" * 50)
        
        # Token durumlarını logla (değerleri değil, sadece mevcut mu yok mu)
        logger.info(f"TELEGRAM_BOT_TOKEN: {'✓ Mevcut' if self.TELEGRAM_BOT_TOKEN else '✗ BULUNAMADI'}")
        logger.info(f"GROQ_API_KEY: {'✓ Mevcut' if self.GROQ_API_KEY else '✗ BULUNAMADI'}")
        logger.info(f"PEXELS_API_KEY: {'✓ Mevcut' if self.PEXELS_API_KEY else '✗ BULUNAMADI'}")
        logger.info(f"Groq Model: {self.GROQ_MODEL}")
        logger.info(f"RSS Feed Sayısı: {len(self.RSS_FEEDS)}")
        logger.info(f"Reddit Subreddit Sayısı: {len(self.REDDIT_SUBREDDITS)}")
        logger.info(f"İçerik Nişi: {self.CONTENT_NICHE}")
        logger.info(f"Veritabanı: {self.DB_PATH}")
        logger.info("=" * 50)
        
        # stderr'ye de yaz (Render için)
        sys.stderr.write(f">>> TELEGRAM_BOT_TOKEN: {'OK' if self.TELEGRAM_BOT_TOKEN else 'MISSING'}\n")
        sys.stderr.write(f">>> GROQ_API_KEY: {'OK' if self.GROQ_API_KEY else 'MISSING'}\n")
        sys.stderr.write(f">>> PEXELS_API_KEY: {'OK' if self.PEXELS_API_KEY else 'MISSING'}\n")
        sys.stderr.write(f">>> RSS_FEEDS: {len(self.RSS_FEEDS)} adet\n")
        sys.stderr.write(f">>> REDDIT_SUBREDDITS: {len(self.REDDIT_SUBREDDITS)} adet\n")
        sys.stderr.flush()
    
    def validate(self) -> tuple[bool, str]:
        """Yapılandırmayı doğrula, gerekli değerleri kontrol et"""
        errors = []
        
        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN ayarlanmamış!")
        elif len(self.TELEGRAM_BOT_TOKEN) < 10:
            errors.append("TELEGRAM_BOT_TOKEN geçersiz!")
            
        if not self.GROQ_API_KEY:
            errors.append("GROQ_API_KEY ayarlanmamış!")
            
        if not self.RSS_FEEDS:
            errors.append("RSS_FEEDS boş!")
            
        if errors:
            return False, "\n".join(errors)
        return True, "Tüm gerekli yapılandırma mevcut"
    
    def get_keywords(self) -> List[str]:
        """Nişe göre anahtar kelimeleri döndürür"""
        keywords_map = {
            "technology": ["tech", "ai", "software", "digital", "innovation", "startup", "app"],
            "business": ["business", "finance", "market", "investment", "economy", "company"],
            "science": ["science", "research", "discovery", "study", "experiment", "space"],
        }
        return keywords_map.get(self.CONTENT_NICHE, keywords_map["technology"])

# Global config
config: Optional[Config] = None

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
    
    def __repr__(self) -> str:
        return f"<ContentItem: {self.title[:30]}...>"


class GeneratedContent:
    """Üretilen içerik"""
    def __init__(self, original: ContentItem, headline: str, script: str, hashtags: List[str]):
        self.original_content = original
        self.headline = headline
        self.script = script
        self.hashtags = hashtags
        self.caption = f"{headline}\n\n{' '.join(hashtags[:10])}"


# ═══════════════════════════════════════════════════════════════════════════════
# VERİTABANI MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

class Database:
    """Basit SQLite veritabanı - hata yakalayıcılı"""
    
    def __init__(self, db_path: Path):
        logger.info(f"Veritabanı başlatılıyor: {db_path}")
        sys.stderr.write(f">>> Veritabanı başlatılıyor: {db_path}\n")
        sys.stderr.flush()
        
        self.db_path = db_path
        self._initialized = False
        
        try:
            self.init_db()
            self._initialized = True
            logger.info("Veritabanı başarıyla başlatıldı")
        except Exception as e:
            logger.error(f"Veritabanı başlatma hatası: {e}")
            sys.stderr.write(f">>> Veritabanı HATASI: {e}\n")
            sys.stderr.flush()
            raise
    
    def init_db(self) -> None:
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
            logger.debug("Veritabanı tabloları hazır")
        except Exception as e:
            logger.error(f"Tablo oluşturma hatası: {e}")
            raise
    
    def save_content(self, content: ContentItem) -> int:
        """İçeriği kaydeder"""
        if not self._initialized:
            logger.error("Veritabanı henüz başlatılmadı!")
            return -1
            
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
        if not self._initialized:
            logger.error("Veritabanı henüz başlatılmadı!")
            return []
            
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
# İÇERİK TOPLAYICI MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

class ContentFetcher:
    """RSS feed'lerden içerik toplayıcı"""
    
    def __init__(self, cfg: Config):
        logger.info("ContentFetcher başlatılıyor...")
        sys.stderr.write(">>> ContentFetcher başlatılıyor...\n")
        sys.stderr.flush()
        
        self.rss_feeds = cfg.RSS_FEEDS
        self.subreddits = cfg.REDDIT_SUBREDDITS
        self.keywords = cfg.get_keywords()
        
        logger.info(f"Anahtar kelimeler: {self.keywords}")
        logger.info("ContentFetcher başarıyla başlatıldı")
    
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
# AI İÇERİK ÜRETİCİ MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

class AIContentGenerator:
    """Groq API ile içerik üretici"""
    
    def __init__(self, cfg: Config):
        logger.info("AIContentGenerator başlatılıyor...")
        sys.stderr.write(">>> AIContentGenerator başlatılıyor...\n")
        sys.stderr.flush()
        
        self.api_key = cfg.GROQ_API_KEY
        self.model = cfg.GROQ_MODEL
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY ayarlanmamış, AI içerik üretimi çalışmayacak!")
        
        logger.info(f"AI Generator başlatıldı (model: {self.model})")
    
    async def generate(self, content: ContentItem) -> GeneratedContent:
        """İçerikten senaryo üretir"""
        logger.info(f"AI içerik üretiyor: {content.title[:50]}...")
        
        if not self.api_key:
            logger.warning("Groq API anahtarı yok, fallback içerik döndürülüyor")
            return self._fallback_content(content)
        
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
            sys.stderr.write(f">>> Groq API HATASI: {e}\n")
            sys.stderr.flush()
            return self._fallback_content(content)
    
    def _fallback_content(self, content: ContentItem) -> GeneratedContent:
        """API başarısız olduğunda fallback içerik döndürür"""
        logger.info("Fallback içerik üretiliyor")
        return GeneratedContent(
            original=content,
            headline=content.title[:100],
            script=content.description[:300] if content.description else "Bu konuda daha fazla bilgi için kaynağa göz atın.",
            hashtags=["#teknoloji", "#haber", "#reels", "#viral", "#trend", "#instagood", "#ai", "#future"]
        )
    
    def _parse_response(self, response: str, original: ContentItem) -> GeneratedContent:
        """AI yanıtını ayrıştırır"""
        lines = response.strip().split("\n")
        
        headline = original.title[:100]
        script = original.description[:300] if original.description else ""
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
# PEXELS MODÜLÜ (Video indirme devre dışı)
# ═══════════════════════════════════════════════════════════════════════════════

class PexelsSearch:
    """Pexels video arama (video indirme devre dışı)"""
    
    def __init__(self, cfg: Config):
        logger.info("PexelsSearch başlatılıyor...")
        self.api_key = cfg.PEXELS_API_KEY
        logger.info(f"Pexels başlatıldı (API Key: {'Var' if self.api_key else 'Yok'})")
    
    async def search_videos(self, query: str, limit: int = 5) -> List[dict]:
        """Video arar - şu anda devre dışı"""
        if not self.api_key:
            logger.debug("Pexels API anahtarı yok, video aranamıyor")
            return []
        
        logger.debug(f"Pexels arama (devre dışı): {query}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

class TelegramBot:
    """Ana Telegram bot sınıfı - hata yakalayıcılı"""
    
    def __init__(self, cfg: Config):
        logger.info("=" * 50)
        logger.info("TELEGRAM BOT BAŞLATILIYOR")
        logger.info("=" * 50)
        sys.stderr.write("\n")
        sys.stderr.write("╔═══════════════════════════════════════════════════════╗\n")
        sys.stderr.write("║     TELEGRAM BOT BAŞLATILIYOR                          ║\n")
        sys.stderr.write("╚═══════════════════════════════════════════════════════╝\n")
        sys.stderr.flush()
        
        self.config = cfg
        self.app = None
        self.db: Optional[Database] = None
        self.fetcher: Optional[ContentFetcher] = None
        self.ai: Optional[AIContentGenerator] = None
        self.pexels: Optional[PexelsSearch] = None
        self.user_data: Dict[int, Dict[str, Any]] = {}
        
        # Modülleri başlat
        self._initialize_modules()
    
    def _initialize_modules(self) -> None:
        """Tüm modülleri başlatır"""
        logger.info("Modüller başlatılıyor...")
        sys.stderr.write(">>> Modüller başlatılıyor...\n")
        sys.stderr.flush()
        
        try:
            # Veritabanı
            logger.info("  - Veritabanı başlatılıyor...")
            self.db = Database(self.config.DB_PATH)
            logger.info("  ✓ Veritabanı hazır")
            
            # Content Fetcher
            logger.info("  - ContentFetcher başlatılıyor...")
            self.fetcher = ContentFetcher(self.config)
            logger.info("  ✓ ContentFetcher hazır")
            
            # AI Generator
            logger.info("  - AIContentGenerator başlatılıyor...")
            self.ai = AIContentGenerator(self.config)
            logger.info("  ✓ AIContentGenerator hazır")
            
            # Pexels
            logger.info("  - PexelsSearch başlatılıyor...")
            self.pexels = PexelsSearch(self.config)
            logger.info("  ✓ PexelsSearch hazır")
            
            logger.info("Tüm modüller başarıyla başlatıldı")
            sys.stderr.write(">>> Tüm modüller başarıyla başlatıldı\n")
            sys.stderr.flush()
            
        except Exception as e:
            logger.error(f"Modül başlatma hatası: {e}")
            sys.stderr.write(f">>> MODÜL HATASI: {e}\n")
            sys.stderr.write(f">>> {traceback.format_exc()}\n")
            sys.stderr.flush()
            raise
    
    async def start(self) -> None:
        """Botu başlatır"""
        logger.info("Bot başlatılıyor...")
        sys.stderr.write(">>> Bot başlatılıyor...\n")
        sys.stderr.flush()
        
        # Token kontrolü
        if not self.config.TELEGRAM_BOT_TOKEN:
            error_msg = "TELEGRAM_BOT_TOKEN ayarlanmamış!"
            logger.error(error_msg)
            sys.stderr.write(f">>> HATA: {error_msg}\n")
            sys.stderr.flush()
            raise ValueError(error_msg)
        
        logger.info(f"TELEGRAM_BOT_TOKEN mevcut ({len(self.config.TELEGRAM_BOT_TOKEN)} karakter)")
        
        try:
            # Application oluştur
            logger.info("Telegram Application oluşturuluyor...")
            sys.stderr.write(">>> Telegram Application oluşturuluyor...\n")
            sys.stderr.flush()
            
            from telegram import Update
            from telegram.ext import (
                Application,
                CallbackContext,
                CallbackQueryHandler,
                CommandHandler,
            )
            
            self.app = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
            
            logger.info("Telegram Application oluşturuldu")
            sys.stderr.write(">>> Telegram Application oluşturuldu\n")
            sys.stderr.flush()
            
        except Exception as e:
            error_msg = f"Application oluşturma hatası: {e}"
            logger.error(error_msg)
            sys.stderr.write(f">>> HATA: {error_msg}\n")
            sys.stderr.write(f">>> {traceback.format_exc()}\n")
            sys.stderr.flush()
            raise
        
        # Handler'ları kaydet
        logger.info("Handler'lar kaydediliyor...")
        sys.stderr.write(">>> Handler'lar kaydediliyor...\n")
        sys.stderr.flush()
        
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("fetch", self.cmd_fetch))
        self.app.add_handler(CommandHandler("generate", self.cmd_generate))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        logger.info("Handler'lar kaydedildi")
        sys.stderr.write(">>> Handler'lar kaydedildi\n")
        sys.stderr.flush()
        
        logger.info("=" * 50)
        logger.info("🤖 BOT ÇALIŞMAYA BAŞLIYOR")
        logger.info("=" * 50)
        sys.stderr.write("\n")
        sys.stderr.write("╔═══════════════════════════════════════════════════════╗\n")
        sys.stderr.write("║     🤖 BOT ÇALIŞMAYA BAŞLIYOR                          ║\n")
        sys.stderr.write("╚═══════════════════════════════════════════════════════╝\n")
        sys.stderr.flush()
        
        try:
            await self.app.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logger.error(f"Polling hatası: {e}")
            sys.stderr.write(f">>> POLLING HATASI: {e}\n")
            sys.stderr.write(f">>> {traceback.format_exc()}\n")
            sys.stderr.flush()
            raise
    
    async def cmd_start(self, update: Update, context: CallbackContext) -> None:
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
        try:
            await update.message.reply_text(welcome)
        except Exception as e:
            logger.error(f"Start komutu hatası: {e}")
    
    async def cmd_help(self, update: Update, context: CallbackContext) -> None:
        """Yardım komutu"""
        help_text = """
📚 KULLANIM KILAVUZU

1. /fetch yazın → Bot RSS ve Reddit'ten içerik bulur
2. /generate yazın → Seçtiğiniz içerikten AI senaryo üretir
3. Senaryoyu kullanarak video oluşturabilirsiniz

⚙️ NOT: Video oluşturma özellikleri yakında eklenecek.
        """
        try:
            await update.message.reply_text(help_text)
        except Exception as e:
            logger.error(f"Help komutu hatası: {e}")
    
    async def cmd_status(self, update: Update, context: CallbackContext) -> None:
        """Durum komutu"""
        status = f"""
📊 SİSTEM DURUMU

🤖 Bot: ✅ Aktif
📡 Groq AI: {'✅ Bağlı' if self.config.GROQ_API_KEY else '❌ Bağlı Değil'}
🎬 Pexels: {'✅ Bağlı' if self.config.PEXELS_API_KEY else '⚠️ API Anahtarı Yok'}
📸 Instagram: ⚠️ Yapılandırılmadı (Video özellikleri devre dışı)
📦 Veritabanı: ✅ Hazır
        """
        try:
            await update.message.reply_text(status)
        except Exception as e:
            logger.error(f"Status komutu hatası: {e}")
    
    async def cmd_fetch(self, update: Update, context: CallbackContext) -> None:
        """İçerik bulma komutu"""
        user_id = update.effective_user.id
        
        try:
            await update.message.reply_text("📡 İçerikler araştırılıyor...")
            
            if not self.fetcher:
                await update.message.reply_text("❌ İçerik toplayıcı hazır değil.")
                return
            
            contents = await self.fetcher.fetch_all()
            
            if not contents:
                await update.message.reply_text("❌ Hiç içerik bulunamadı.")
                return
            
            # Veritabanına kaydet
            for c in contents:
                if self.db:
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
            logger.error(f"Fetch komutu hatası: {e}")
            try:
                await update.message.reply_text(f"❌ Hata: {str(e)}")
            except:
                pass
    
    async def cmd_generate(self, update: Update, context: CallbackContext) -> None:
        """İçerik üretme komutu"""
        user_id = update.effective_user.id
        
        try:
            if not self.db:
                await update.message.reply_text("❌ Veritabanı hazır değil.")
                return
            
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
            
        except Exception as e:
            logger.error(f"Generate komutu hatası: {e}")
            try:
                await update.message.reply_text(f"❌ Hata: {str(e)}")
            except:
                pass
    
    async def handle_callback(self, update: Update, context: CallbackContext) -> None:
        """Callback işleyici"""
        query = update.callback_query
        
        try:
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
                    if index < len(contents) and self.ai:
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
                            
        except Exception as e:
            logger.error(f"Callback işleme hatası: {e}")
            try:
                await query.message.reply_text(f"❌ Bir hata oluştu: {str(e)}")
            except:
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# ANA FONKSİYON
# ═══════════════════════════════════════════════════════════════════════════════

async def main() -> None:
    """Ana asenkron fonksiyon"""
    global config
    
    logger.info("=" * 60)
    logger.info(">>> main() FONKSİYONU BAŞLADI")
    logger.info("=" * 60)
    sys.stderr.write("\n>>> main() başladı\n")
    sys.stderr.flush()
    
    try:
        # Yapılandırmayı oluştur
        logger.info("Yapılandırma oluşturuluyor...")
        config = Config()
        
        # Yapılandırmayı doğrula
        logger.info("Yapılandırma doğrulanıyor...")
        is_valid, message = config.validate()
        
        if not is_valid:
            logger.error(f"YAPILANDIRMA HATASI: {message}")
            sys.stderr.write(f">>> YAPILANDIRMA HATASI: {message}\n")
            sys.stderr.flush()
            raise ValueError(f"Yapılandırma hatası: {message}")
        
        logger.info(f"✓ {message}")
        sys.stderr.write(f">>> {message}\n")
        sys.stderr.flush()
        
        # Botu oluştur ve başlat
        logger.info("Bot oluşturuluyor...")
        sys.stderr.write(">>> Bot oluşturuluyor...\n")
        sys.stderr.flush()
        
        bot = TelegramBot(config)
        
        logger.info("Bot.start() çağrılıyor...")
        sys.stderr.write(">>> Bot.start() çağrılıyor...\n")
        sys.stderr.flush()
        
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Bot kapatılıyor (KeyboardInterrupt)...")
        sys.stderr.write(">>> Bot kapatılıyor (KeyboardInterrupt)...\n")
        sys.stderr.flush()
        
    except ValueError as e:
        logger.error(f"Değer hatası: {e}")
        sys.stderr.write(f">>> DEĞER HATASI: {e}\n")
        sys.stderr.flush()
        raise
        
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")
        sys.stderr.write(f">>> BEKLENMEYEN HATA: {e}\n")
        sys.stderr.write(f">>> Traceback:\n{traceback.format_exc()}\n")
        sys.stderr.flush()
        raise


# ═══════════════════════════════════════════════════════════════════════════════
# BAŞLANGIÇ NOKTASI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Banner
    print("╔═══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║           INSTAGRAM REELS BOT - GÜVENİLİR VERSİYON                   ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Sistem bilgileri
    sys.stderr.write(f">>> Python: {sys.version}\n")
    sys.stderr.write(f">>> Çalışma dizini: {os.getcwd()}\n")
    sys.stderr.write(f">>> Platform: {sys.platform}\n")
    sys.stderr.flush()
    
    logger.info("=" * 60)
    logger.info("INSTAGRAM REELS BOT BAŞLATILIYOR")
    logger.info("=" * 60)
    
    # Ana modülleri import et
    logger.info("Ana modüller import ediliyor...")
    sys.stderr.write(">>> Modüller import ediliyor...\n")
    sys.stderr.flush()
    
    try:
        import httpx
        logger.info(f"✓ httpx {httpx.__version__}")
    except ImportError as e:
        logger.error(f"httpx import hatası: {e}")
        sys.stderr.write(f">>> httpx HATASI: {e}\n")
        sys.stderr.flush()
        sys.exit(1)
    
    try:
        import feedparser
        logger.info("✓ feedparser")
    except ImportError as e:
        logger.error(f"feedparser import hatası: {e}")
        sys.stderr.write(f">>> feedparser HATASI: {e}\n")
        sys.stderr.flush()
        sys.exit(1)
    
    try:
        from bs4 import BeautifulSoup
        logger.info("✓ BeautifulSoup")
    except ImportError as e:
        logger.error(f"BeautifulSoup import hatası: {e}")
        sys.stderr.write(f">>> BeautifulSoup HATASI: {e}\n")
        sys.stderr.flush()
        sys.exit(1)
    
    try:
        import telegram
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
        from telegram.ext import (
            Application,
            CallbackContext,
            CallbackQueryHandler,
            CommandHandler,
        )
        logger.info(f"✓ python-telegram-bot {telegram.__version__}")
    except ImportError as e:
        logger.error(f"python-telegram-bot import hatası: {e}")
        sys.stderr.write(f">>> telegram HATASI: {e}\n")
        sys.stderr.flush()
        sys.exit(1)
    
    logger.info("Tüm modüller başarıyla import edildi")
    sys.stderr.write(">>> Tüm modüller import edildi\n")
    sys.stderr.flush()
    
    # Asenkron ana döngüyü çalıştır
    logger.info("Asenkron ana döngü başlatılıyor...")
    sys.stderr.write(">>> Asenkron ana döngü başlatılıyor...\n")
    sys.stderr.flush()
    
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot kapatıldı (Ctrl+C)")
        sys.stderr.write(">>> Bot kapatıldı (Ctrl+C)\n")
        sys.stderr.flush()
    except Exception as e:
        logger.critical(f"Kritik hata: {e}")
        sys.stderr.write(f">>> KRİTİK HATA: {e}\n")
        sys.stderr.write(f">>> {traceback.format_exc()}\n")
        sys.stderr.flush()
        sys.exit(1)
    
    logger.info("Bot kapatıldı")
    sys.stderr.write(">>> Bot kapatıldı\n")
    sys.stderr.flush()
