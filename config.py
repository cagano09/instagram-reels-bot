"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           INSTAGRAM REELS BOT - YAPILANDİRMA MODÜLÜ                         ║
║                                                                              ║
║  Bu modül, botun tüm yapılandırma ayarlarını ve sabitlerini içerir.        ║
║  Ortam değişkenlerini okur ve uygulama genelinde kullanılabilir hale getirir ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ═══════════════════════════════════════════════════════════════════════════════
# ORTAM DEĞİŞKENLERİ YÜKLEME
# ═══════════════════════════════════════════════════════════════════════════════

from pathlib import Path
from dotenv import load_dotenv
import os

# Proje kök dizinini bul
BASE_DIR = Path(__file__).resolve().parent

# .env dosyasını yükle (eğer varsa)
load_dotenv(BASE_DIR / ".env")


# ═══════════════════════════════════════════════════════════════════════════════
# TEMEL YOL AYARLARI
# ═══════════════════════════════════════════════════════════════════════════════

# Proje kök dizini
PROJECT_ROOT = BASE_DIR

# Alt dizinler
TEMP_DIR = PROJECT_ROOT / os.getenv("TEMP_DIR", "temp")
OUTPUT_DIR = PROJECT_ROOT / os.getenv("OUTPUT_DIR", "output")
MEDIA_DIR = PROJECT_ROOT / os.getenv("MEDIA_DIR", "media")
LOG_DIR = PROJECT_ROOT / os.getenv("LOG_DIR", "logs")
SESSIONS_DIR = PROJECT_ROOT / os.getenv("INSTAGRAM_SESSION_FILE", "sessions").rsplit("/", 1)[0] if "/" in os.getenv("INSTAGRAM_SESSION_FILE", "") else PROJECT_ROOT / "sessions"

# Dizinleri oluştur (yoksa)
for directory in [TEMP_DIR, OUTPUT_DIR, MEDIA_DIR, LOG_DIR, SESSIONS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT AYARLARI
# ═══════════════════════════════════════════════════════════════════════════════

class TelegramConfig:
    """Telegram bot yapılandırma sınıfı"""

    # Bot token'ı (BotFather'dan alınır)
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Yetkili kullanıcı ID'leri (birden fazla ise liste olarak saklanır)
    _user_ids = os.getenv("AUTHORIZED_USER_IDS", "")
    AUTHORIZED_USER_IDS = (
        [int(uid.strip()) for uid in _user_ids.split(",") if uid.strip()]
        if _user_ids
        else []
    )

    # Komutlar
    COMMANDS = {
        "start": "Botu başlatır ve hoşgeldin mesajı gösterir",
        "help": "Kullanım kılavuzunu gösterir",
        "status": "Sistem durumunu gösterir",
        "settings": "Ayarlar menüsünü açar",
        "fetch": "Yeni içerik araştırır",
        "generate": "İçerikten video oluşturur",
        "post": "Videoyu Instagram'da paylaşır",
        "schedule": "Zamanlama ayarlarını gösterir",
        "cancel": "Devam eden işlemi iptal eder",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GROQ API AYARLARI (ÜCRETSİZ LLM - KESİNLİKLE ÖNERİLEN)
# ═══════════════════════════════════════════════════════════════════════════════

class GroqConfig:
    """Groq API yapılandırma sınıfı - Ücretsiz ve GPU hızında LLM servisi"""

    # API anahtarı (console.groq.com adresinden ücretsiz alınır)
    API_KEY = os.getenv("GROQ_API_KEY", "")

    # Kullanılacak model
    # llama-3.1-70b-versatile: En güçlü ücretsiz model (önerilen)
    # llama-3.1-8b-instant: Daha hızlı, daha az RAM
    # mixtral-8x7b-32768: Dengeli performans
    MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

    # API URL'si
    BASE_URL = "https://api.groq.com/openai/v1"

    # Maksimum token sayısı
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))

    # Sıcaklık değeri (0-2 arası, daha yaratıcı yanıtlar için artırın)
    TEMPERATURE = 0.7

    # Sistem mesajı (Türkçe prompt)
    SYSTEM_PROMPT = """Sen, Instagram Reels videoları için içerik üreten profesyonel bir yapay zeka asistanısın.
Görevin, verilen haber veya bilgiyi dikkat çekici bir Reels içeriğine dönüştürmek.

Her içerik için şunları üret:
1. **Başlık**: Dikkat çekici, merak uyandıran bir başlık (max 100 karakter)
2. **Senaryo**: Video için voiceover metni (30-60 saniye, doğal ve akıcı, Türkçe konuşma dili)
3. **Hashtag'ler**: 10-15 adet alakalı hashtag
4. **Açıklama**: Instagram paylaşımı için kısa bir açıklama

Kurallar:
- Senaryoyu konuşma dilinde yaz, Türkçe olsun
- Her cümleyi kısa tut (maksimum 15 kelime)
- Dikkat çekici giriş cümleleri kullan
- Bilgiyi net ve anlaşılır şekilde aktar
- Sansasyonel ifadelerden kaçın, gerçekçi ol
- Reels formatına uygun, hızlı tempoda içerik hazırla"""

    @classmethod
    def validate(cls):
        """Yapılandırma geçerliliğini kontrol eder"""
        if not cls.API_KEY:
            raise ValueError(
                "Groq API anahtarı bulunamadı!\n\n"
                "Ücretsiz API anahtarı almak için:\n"
                "1. console.groq.com adresine gidin\n"
                "2. Kayıt olun (Google/GitHub ile)\n"
                "3. Sol menüden 'API Keys' seçin\n"
                "4. 'Create API Key' ile yeni anahtar oluşturun\n"
                "5. Anahtarı .env dosyasına GROQ_API_KEY olarak ekleyin"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# OPENAI API AYARLARI (YEDEK - ÜCRETLİ)
# ═══════════════════════════════════════════════════════════════════════════════

class OpenAIConfig:
    """OpenAI API yapılandırma sınıfı - Yedek olarak kullanılabilir"""

    # API anahtarı (platform.openai.com adresinden alınır - ücretli)
    API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Kullanılacak model
    MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Maksimum token sayısı
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))

    # Sıcaklık değeri
    TEMPERATURE = 0.7

    # Sistem mesajı
    SYSTEM_PROMPT = GroqConfig.SYSTEM_PROMPT  # Groq ile aynı prompt

    @classmethod
    def validate(cls):
        """Yapılandırma geçerliliğini kontrol eder"""
        if not cls.API_KEY:
            raise ValueError(
                "OpenAI API anahtarı bulunamadı. "
                "Ücretsiz Groq API kullanmanızı öneririz."
            )


# ═══════════════════════════════════════════════════════════════════════════════
# PEXELS API AYARLARI
# ═══════════════════════════════════════════════════════════════════════════════

class PexelsConfig:
    """Pexels video API yapılandırma sınıfı"""

    # API anahtarı
    API_KEY = os.getenv("PEXELS_API_KEY", "")

    # API URL'leri
    BASE_URL = "https://api.pexels.com/videos"
    SEARCH_URL = f"{BASE_URL}/search"
    POPULAR_URL = f"{BASE_URL}/popular"
    CURATED_URL = f"{BASE_URL}/curated"

    # Arama sonuç limiti
    RESULTS_PER_PAGE = 15

    # Video özellikleri
    VIDEO_ORIENTATION = "portrait"  # 9:16 aspect ratio için
    VIDEO_MIN_DURATION = 15  # Minimum saniye
    VIDEO_MAX_DURATION = 60  # Maksimum saniye

    @classmethod
    def validate(cls):
        """Yapılandırma geçerliliğini kontrol eder"""
        if not cls.API_KEY:
            raise ValueError("Pexels API anahtarı bulunamadı. Lütfen .env dosyasını kontrol edin.")


# ═══════════════════════════════════════════════════════════════════════════════
# İNSTAGRAM API AYARLARI
# ═══════════════════════════════════════════════════════════════════════════════

class InstagramConfig:
    """Instagram API yapılandırma sınıfı"""

    # Hesap bilgileri
    USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
    PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")

    # Session dosyası yolu
    SESSION_FILE = PROJECT_ROOT / os.getenv("INSTAGRAM_SESSION_FILE", "sessions/instagram_session.json")

    # Video ayarları
    CAPTION_MAX_LENGTH = 2200  # Instagram maksimum karakter limiti
    AUTO_POST = os.getenv("AUTO_POST_ENABLED", "False").lower() == "true"

    @classmethod
    def validate(cls):
        """Yapılandırma geçerliliğini kontrol eder"""
        if not cls.USERNAME or not cls.PASSWORD:
            raise ValueError("Instagram hesap bilgileri bulunamadı. Lütfen .env dosyasını kontrol edin.")


# ═══════════════════════════════════════════════════════════════════════════════
# İÇERİK KAYNAKLARI AYARLARI
# ═══════════════════════════════════════════════════════════════════════════════

class ContentSourcesConfig:
    """İçerik kaynakları yapılandırma sınıfı"""

    # RSS Feed URL'leri
    _rss_feeds = os.getenv("RSS_FEEDS", "")
    RSS_FEEDS = [url.strip() for url in _rss_feeds.split(",") if url.strip()]

    # Reddit subreddit'leri
    _subreddits = os.getenv("REDDIT_SUBREDDITS", "")
    REDDIT_SUBREDDITS = [sub.strip() for sub in _subreddits.split(",") if sub.strip()]

    # Reddit API ayarları
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "InstagramReelsBot/1.0")
    REDDIT_BASE_URL = "https://www.reddit.com"

    # İçerik nişi
    CONTENT_NICHE = os.getenv("CONTENT_NICHE", "technology")

    # Niş bazlı anahtar kelimeler
    NICHE_KEYWORDS = {
        "technology": ["tech", "AI", "software", "startup", "innovation", "gadget", "digital", "coding"],
        "business": ["startup", "entrepreneur", "success", "money", "investment", "career", "leadership"],
        "lifestyle": ["life", "health", "fitness", "travel", "food", "fashion", "beauty", "home"],
        "science": ["science", "research", "discovery", "space", "NASA", "physics", "biology", "study"],
        "gaming": ["game", "gaming", "esports", "playstation", "xbox", "nintendo", "steam", "pc gaming"],
        "news": ["news", "breaking", "update", "report", "announcement", "latest", "trending"],
    }

    @classmethod
    def get_keywords(cls):
        """Mevcut niş için anahtar kelimeleri döndürür"""
        return cls.NICHE_KEYWORDS.get(cls.CONTENT_NICHE, cls.NICHE_KEYWORDS["technology"])


# ═══════════════════════════════════════════════════════════════════════════════
# VİDEO AYARLARI
# ═══════════════════════════════════════════════════════════════════════════════

class VideoConfig:
    """Video işleme yapılandırma sınıfı"""

    # Boyutlar (Instagram Reels için 9:16 portrait)
    WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
    HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))
    FPS = int(os.getenv("VIDEO_FPS", "30"))

    # Kalite
    QUALITY = os.getenv("VIDEO_QUALITY", "1080")
    BITRATE = "8M" if QUALITY == "1080" else "5M" if QUALITY == "720" else "2.5M"

    # Seslendirme
    TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "tr")  # Türkçe varsayılan
    TTS_SPEED = 1.0  # 1.0 normal hız

    # Video önizleme ayarı (True = video oluşturulduktan sonra kullanıcıya gönderilir)
    SEND_PREVIEW = os.getenv("SEND_PREVIEW", "True").lower() == "true"

    # Manuel onay modu (True = paylaşım için kullanıcı onayı gerekir)
    MANUAL_APPROVAL = os.getenv("MANUAL_APPROVAL", "True").lower() == "true"

    # Renkler
    TEXT_COLOR = "white"
    TEXT_BACKGROUND_COLOR = (0, 0, 0, 180)  # Yarı saydam siyah
    ACCENT_COLOR = "#FF6B6B"  # Vurgu rengi

    # Font
    FONT_SIZE_TITLE = 60
    FONT_SIZE_SUBTITLE = 40
    FONT_SIZE_HASHTAG = 32

    # Video formatları
    OUTPUT_FORMAT = "mp4"
    CODEC = "libx264"
    AUDIO_CODEC = "aac"


# ═══════════════════════════════════════════════════════════════════════════════
# ZAMANLAMA AYARLARI
# ═══════════════════════════════════════════════════════════════════════════════

class SchedulerConfig:
    """Zamanlama yapılandırma sınıfı"""

    # Otomatik içerik kontrol aralığı (dakika)
    CONTENT_CHECK_INTERVAL = int(os.getenv("CONTENT_CHECK_INTERVAL", "60"))

    # Otomatik içerik üretimi aktif mi?
    AUTO_CONTENT_ENABLED = os.getenv("AUTO_CONTENT_ENABLED", "False").lower() == "true"

    # En iyi paylaşım saatleri
    _best_times = os.getenv("BEST_POST_TIMES", "09:00,12:30,19:00,21:00")
    BEST_POST_TIMES = [time.strip() for time in _best_times.split(",")]

    # Zaman dilimi
    TIMEZONE = "Europe/Istanbul"


# ═══════════════════════════════════════════════════════════════════════════════
# LOGLAMA AYARLARI
# ═══════════════════════════════════════════════════════════════════════════════

class LoggingConfig:
    """Loglama yapılandırma sınıfı"""

    # Log seviyesi
    LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Log dosyası yolu
    FILE_PATH = LOG_DIR / "bot.log"

    # Format
    FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Rotasyon
    ROTATION = "500 MB"
    RETENTION = "30 days"

    @classmethod
    def setup(cls):
        """Loglama sistemini yapılandırır"""
        from loguru import logger

        # Mevcut handler'ları temizle
        logger.remove()

        # Konsola log ekle (eğer aktifse)
        if os.getenv("LOG_TO_CONSOLE", "True").lower() == "true":
            logger.add(
                sink=lambda msg: print(msg),
                format=cls.FORMAT,
                level=cls.LEVEL,
                colorize=True,
            )

        # Dosyaya log ekle (eğer aktifse)
        if os.getenv("LOG_TO_FILE", "True").lower() == "true":
            logger.add(
                sink=str(cls.FILE_PATH),
                format=cls.FORMAT,
                level=cls.LEVEL,
                rotation=cls.ROTATION,
                retention=cls.RETENTION,
                compression="zip",
                enqueue=True,
            )

        return logger


# ═══════════════════════════════════════════════════════════════════════════════
# VERİTABANI VE ÖNBELLEK AYARLARI
# ═══════════════════════════════════════════════════════════════════════════════

class DatabaseConfig:
    """Veritabanı yapılandırma sınıfı"""

    # SQLite veritabanı dosyası
    DB_PATH = PROJECT_ROOT / "data" / "bot_database.db"

    # Önbellek ayarları
    CACHE_DIR = PROJECT_ROOT / "cache"
    CACHE_EXPIRY_MINUTES = 30

    @classmethod
    def init(cls):
        """Veritabanı ve önbellek dizinlerini oluşturur"""
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# YAPILANDIRMA DOĞRULAMA
# ═══════════════════════════════════════════════════════════════════════════════

def validate_all_config():
    """
    Tüm yapılandırma ayarlarını doğrular.
    Eksik veya hatalı ayarlar varsa ValueError fırlatır.
    """
    errors = []

    # Telegram kontrolü
    if not TelegramConfig.BOT_TOKEN:
        errors.append("Telegram Bot Token bulunamadı")

    # OpenAI kontrolü
    if not OpenAIConfig.API_KEY:
        errors.append("OpenAI API Key bulunamadı")

    # Pexels kontrolü
    if not PexelsConfig.API_KEY:
        errors.append("Pexels API Key bulunamadı")

    # İçerik kaynakları kontrolü
    if not ContentSourcesConfig.RSS_FEEDS and not ContentSourcesConfig.REDDIT_SUBREDDITS:
        errors.append("En az bir içerik kaynağı (RSS veya Reddit) tanımlanmalı")

    if errors:
        raise ValueError(
            "Yapılandırma hataları bulundu:\n" + "\n".join(f"- {e}" for e in errors)
        )

    return True


# ═══════════════════════════════════════════════════════════════════════════════
# MODÜL İÇARAK
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║           INSTAGRAM REELS BOT - YAPILANDIRMA MODÜLÜ                            ║")
    print("╠══════════════════════════════════════════════════════════════════════════════╣")
    print("║  Bu modül, botun tüm yapılandırma ayarlarını içerir.                         ║")
    print("║  Doğrudan çalıştırılmak için tasarlanmamıştır.                               ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")

    # Yapılandırmayı doğrula
    try:
        validate_all_config()
        print("\n✅ Yapılandırma doğrulaması başarılı!")
    except ValueError as e:
        print(f"\n❌ Yapılandırma hatası: {e}")
