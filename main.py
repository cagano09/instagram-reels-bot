"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           INSTAGRAM REELS BOT - ANA DOSYA                                    ║
║                                                                              ║
║  Bu bot, Telegram üzerinden kontrol edilen ve Instagram Reels               ║
║  videolarını otomatik olarak oluşturup paylaşabilen bir sistemdir.          ║
║                                                                              ║
║  Özellikler:                                                                 ║
║  • RSS feed'leri ve Reddit'ten içerik toplama                               ║
║  • OpenAI GPT-4 ile senaryo ve başlık üretme                                 ║
║  • Pexels API'den stok video çekme                                           ║
║  • gTTS ile seslendirme oluşturma                                            ║
║  • FFmpeg/moviepy ile video montajı                                          ║
║  • İnstagrapi ile Instagram'da otomatik paylaşım                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ═══════════════════════════════════════════════════════════════════════════════
# TEMEL İMPORTLAR
# ═══════════════════════════════════════════════════════════════════════════════

import asyncio
import logging
import os
import random
import re
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import feedparser
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from loguru import logger

# Yapılandırma modülünü içe aktar
import config as cfg


# ═══════════════════════════════════════════════════════════════════════════════
# YARDIMCI SINIFLAR VE FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ContentItem:
    """İçerik öğesi veri sınıfı"""
    title: str
    description: str
    url: str
    source: str
    published_date: Optional[str] = None
    thumbnail: Optional[str] = None


@dataclass
class GeneratedContent:
    """Üretilen içerik veri sınıfı"""
    original_content: ContentItem
    headline: str
    script: str
    hashtags: List[str]
    caption: str


@dataclass
class VideoProject:
    """Video projesi veri sınıfı"""
    content: GeneratedContent
    video_path: Optional[Path] = None
    audio_path: Optional[Path] = None
    final_path: Optional[Path] = None
    status: str = "pending"


# ═══════════════════════════════════════════════════════════════════════════════
# LOGLAMA SİSTEMİ
# ═══════════════════════════════════════════════════════════════════════════════

def setup_logging():
    """Loglama sistemini yapılandırır"""
    cfg.LoggingConfig.setup()
    return logger


# ═══════════════════════════════════════════════════════════════════════════════
# VERİTABANI İŞLEMLERİ
# ═══════════════════════════════════════════════════════════════════════════════

class Database:
    """SQLite veritabanı işlemleri sınıfı"""

    def __init__(self):
        """Veritabanını başlatır"""
        cfg.DatabaseConfig.init()
        self.db_path = cfg.DatabaseConfig.DB_PATH
        self.init_db()

    def init_db(self):
        """Veritabanı tablolarını oluşturur"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # İçerikler tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    url TEXT,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    used BOOLEAN DEFAULT FALSE
                )
            """)

            # Üretilen içerikler tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generated_contents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id INTEGER,
                    headline TEXT,
                    script TEXT,
                    hashtags TEXT,
                    caption TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (content_id) REFERENCES contents (id)
                )
            """)

            # Videolar tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generated_content_id INTEGER,
                    video_path TEXT,
                    status TEXT DEFAULT 'pending',
                    posted BOOLEAN DEFAULT FALSE,
                    instagram_post_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    posted_at TIMESTAMP,
                    FOREIGN KEY (generated_content_id) REFERENCES generated_contents (id)
                )
            """)

            # Kullanıcı ayarları tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    niche TEXT DEFAULT 'technology',
                    auto_post BOOLEAN DEFAULT FALSE,
                    post_times TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def save_content(self, content: ContentItem) -> int:
        """İçeriği veritabanına kaydeder"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO contents (title, description, url, source, published_date, thumbnail)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (content.title, content.description, content.url, content.source,
                 content.published_date, content.thumbnail)
            )
            conn.commit()
            return cursor.lastrowid

    def get_unused_content(self, limit: int = 10) -> List[ContentItem]:
        """Kullanılmamış içerikleri getirir"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, title, description, url, source, published_date, thumbnail
                FROM contents
                WHERE used = FALSE
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            return [
                ContentItem(
                    title=row[1],
                    description=row[2],
                    url=row[3],
                    source=row[4],
                    published_date=row[5],
                    thumbnail=row[6]
                )
                for row in rows
            ]

    def mark_content_used(self, content_id: int):
        """İçeriği kullanıldı olarak işaretler"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE contents SET used = TRUE WHERE id = ?", (content_id,))
            conn.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT YARDIMCI FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════════════════════

async def send_long_message(update: Update, text: str, max_length: int = 4096):
    """Uzun mesajları parçalara bölerek gönderir"""
    if len(text) <= max_length:
        await update.message.reply_text(text)
        return

    parts = []
    current_part = ""

    for line in text.split("\n"):
        if len(current_part) + len(line) + 1 <= max_length:
            current_part += line + "\n"
        else:
            if current_part:
                parts.append(current_part.strip())
            current_part = line + "\n"

    if current_part:
        parts.append(current_part.strip())

    for part in parts:
        await update.message.reply_text(part)


def format_status_table(items: List[Tuple[str, str]]) -> str:
    """Durum bilgisi için tablo formatında mesaj oluşturur"""
    lines = ["📊 **Sistem Durumu**\n"]
    lines.append("─" * 40)

    for label, value in items:
        lines.append(f"  {label}: {value}")

    lines.append("─" * 40)
    return "\n".join(lines)


def format_progress_bar(current: int, total: int, width: int = 20) -> str:
    """İlerleme çubuğu oluşturur"""
    filled = int(width * current / total) if total > 0 else 0
    bar = "▓" * filled + "░" * (width - filled)
    percentage = int(100 * current / total) if total > 0 else 0
    return f"[{bar}] {percentage}%"


# ═══════════════════════════════════════════════════════════════════════════════
# İÇERİK TOPLAMA MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

class ContentFetcher:
    """RSS feed'leri ve Reddit'ten içerik toplama sınıfı"""

    def __init__(self):
        """Fetcher'ı başlatır"""
        self.rss_feeds = cfg.ContentSourcesConfig.RSS_FEEDS
        self.subreddits = cfg.ContentSourcesConfig.REDDIT_SUBREDDITS
        self.keywords = cfg.ContentSourcesConfig.get_keywords()

    async def fetch_all(self) -> List[ContentItem]:
        """Tüm kaynaklardan içerik toplar"""
        contents = []

        # RSS feed'lerden içerik çek
        rss_contents = await self._fetch_rss_feeds()
        contents.extend(rss_contents)

        # Reddit'ten içerik çek
        reddit_contents = await self._fetch_reddit()
        contents.extend(reddit_contents)

        # Benzersiz içerikleri döndür
        return self._deduplicate_contents(contents)

    async def _fetch_rss_feeds(self) -> List[ContentItem]:
        """RSS feed'lerden içerik çeker"""
        contents = []

        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:10]:
                    # Anahtar kelime kontrolü
                    title = entry.get("title", "")
                    summary = self._clean_html(entry.get("summary", ""))

                    if self._matches_keywords(title, summary):
                        content = ContentItem(
                            title=title,
                            description=summary[:500],
                            url=entry.get("link", ""),
                            source=self._extract_domain(feed_url),
                            published_date=entry.get("published", "")
                        )
                        contents.append(content)

            except Exception as e:
                logger.error(f"RSS feed hatası ({feed_url}): {e}")

        return contents

    async def _fetch_reddit(self) -> List[ContentItem]:
        """Reddit'ten içerik çeker"""
        contents = []

        for subreddit in self.subreddits:
            try:
                url = f"{cfg.ContentSourcesConfig.REDDIT_BASE_URL}/r/{subreddit}/hot.json"
                headers = {"User-Agent": cfg.ContentSourcesConfig.REDDIT_USER_AGENT}

                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers, timeout=10.0)
                    data = response.json()

                    posts = data.get("data", {}).get("children", [])

                    for post in posts[:10]:
                        post_data = post.get("data", {})
                        title = post_data.get("title", "")
                        self_text = post_data.get("selftext", "")

                        if self._matches_keywords(title, self_text):
                            content = ContentItem(
                                title=title,
                                description=self_text[:500] if self_text else post_data.get("preview", {}).get("body", ""),
                                url=f"https://reddit.com{post_data.get('permalink', '')}",
                                source=f"r/{subreddit}",
                                published_date=datetime.fromtimestamp(post_data.get("created_utc", 0)).isoformat()
                            )
                            contents.append(content)

            except Exception as e:
                logger.error(f"Reddit hatası (r/{subreddit}): {e}")

        return contents

    def _matches_keywords(self, title: str, text: str) -> bool:
        """Metnin anahtar kelimelerle eşleşip eşleşmediğini kontrol eder"""
        combined = (title + " " + text).lower()
        return any(keyword.lower() in combined for keyword in self.keywords)

    def _clean_html(self, html: str) -> str:
        """HTML etiketlerini temizler"""
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text().strip()

    def _extract_domain(self, url: str) -> str:
        """URL'den domain adını çıkarır"""
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else url

    def _deduplicate_contents(self, contents: List[ContentItem]) -> List[ContentItem]:
        """Tekrarlanan içerikleri kaldırır"""
        seen = set()
        unique = []

        for content in contents:
            key = content.title[:100]  # Başlığın ilk 100 karakteri
            if key not in seen:
                seen.add(key)
                unique.append(content)

        return unique


# ═══════════════════════════════════════════════════════════════════════════════
# YAPAY ZEKA İÇERİK ÜRETİCİ (GROQ - ÜCRETSİZ)
# ═══════════════════════════════════════════════════════════════════════════════

class AIContentGenerator:
    """Groq API kullanarak içerik üreten sınıf - Ücretsiz ve hızlı"""

    def __init__(self):
        """Generatör'ü başlatır"""
        import groq
        self.client = groq.Groq(api_key=cfg.GroqConfig.API_KEY)
        self.model = cfg.GroqConfig.MODEL
        self.max_tokens = cfg.GroqConfig.MAX_TOKENS
        self.temperature = cfg.GroqConfig.TEMPERATURE

    async def generate(self, content: ContentItem) -> GeneratedContent:
        """Verilen içerikten Reels için senaryo üretir"""

        prompt = f"""Aşağıdaki haber veya bilgiyi Instagram Reels formatında içeriğe dönüştür:

BAŞLIK: {content.title}
İÇERİK: {content.description}
KAYNAK: {content.source}
URL: {content.url}

Lütfen şu formatta yanıt ver:

## BAŞLIK
[Dikkat çekici, merak uyandıran bir başlık - max 100 karakter]

## SENARYO
[Video için voiceover metni - 30-60 saniye, konuşma dili, kısa cümleler, Türkçe]

## HASHTAGLER
[10-15 adet hashtag, virgülle ayrılmış]

## AÇIKLAMA
[Instagram paylaşımı için kısa açıklama - max 200 karakter]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": cfg.GroqConfig.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            result = response.choices[0].message.content
            return self._parse_ai_response(result, content)

        except Exception as e:
            logger.error(f"Groq API hatası: {e}")
            raise

    def _parse_ai_response(self, response: str, original: ContentItem) -> GeneratedContent:
        """AI yanıtını ayrıştırır"""
        lines = response.strip().split("\n")

        headline = ""
        script = ""
        hashtags = []
        caption = ""

        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("## BAŞLIK"):
                current_section = "headline"
            elif line.startswith("## SENARYO"):
                current_section = "script"
            elif line.startswith("## HASHTAGLER"):
                current_section = "hashtags"
            elif line.startswith("## AÇIKLAMA"):
                current_section = "caption"
            elif line and current_section:
                if current_section == "headline":
                    headline = line
                elif current_section == "script":
                    script += line + "\n"
                elif current_section == "hashtags":
                    hashtags = [tag.strip() for tag in line.split(",") if tag.strip()]
                elif current_section == "caption":
                    caption = line

        return GeneratedContent(
            original_content=original,
            headline=headline or original.title,
            script=script.strip(),
            hashtags=hashtags,
            caption=caption
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PEXELS VİDEO ÇEKİCİ
# ═══════════════════════════════════════════════════════════════════════════════

class PexelsVideoFetcher:
    """Pexels API'den video çeken sınıf"""

    def __init__(self):
        """Fetcher'ı başlatır"""
        self.api_key = cfg.PexelsConfig.API_KEY
        self.base_url = cfg.PexelsConfig.SEARCH_URL
        self.headers = {"Authorization": self.api_key}

    async def search_videos(self, query: str, limit: int = 10) -> List[Dict]:
        """Anahtar kelimeye göre video arar"""
        params = {
            "query": query,
            "per_page": limit,
            "orientation": cfg.PexelsConfig.VIDEO_ORIENTATION,
            "min_duration": cfg.PexelsConfig.VIDEO_MIN_DURATION,
            "max_duration": cfg.PexelsConfig.VIDEO_MAX_DURATION
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                data = response.json()
                return data.get("videos", [])

        except Exception as e:
            logger.error(f"Pexels API hatası: {e}")
            return []

    async def download_video(self, video_url: str, output_path: Path) -> bool:
        """Videoyu indirir"""
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", video_url, timeout=60.0) as response:
                    response.raise_for_status()

                    with open(output_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)

            return True

        except Exception as e:
            logger.error(f"Video indirme hatası: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# SESLENDİRME OLUŞTURUCU
# ═══════════════════════════════════════════════════════════════════════════════

class VoiceOverGenerator:
    """gTTS kullanarak seslendirme oluşturan sınıf"""

    def __init__(self):
        """Generator'ü başlatır"""
        self.language = cfg.VideoConfig.TTS_LANGUAGE
        self.speed = cfg.VideoConfig.TTS_SPEED

    def generate(self, text: str, output_path: Path) -> bool:
        """Metni seslendirme dosyasına dönüştürür"""
        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang=self.language, slow=False)
            tts.save(str(output_path))

            logger.info(f"Seslendirme oluşturuldu: {output_path}")
            return True

        except Exception as e:
            logger.error(f"gTTS hatası: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# VİDEO OLUŞTURUCU
# ═══════════════════════════════════════════════════════════════════════════════

class VideoCreator:
    """MoviePy kullanarak video oluşturan sınıf"""

    def __init__(self):
        """Creator'ı başlatır"""
        self.width = cfg.VideoConfig.WIDTH
        self.height = cfg.VideoConfig.HEIGHT
        self.fps = cfg.VideoConfig.FPS
        self.font_size_title = cfg.VideoConfig.FONT_SIZE_TITLE
        self.font_size_subtitle = cfg.VideoConfig.FONT_SIZE_SUBTITLE

    async def create_video(
        self,
        background_video_path: Path,
        audio_path: Path,
        content: GeneratedContent,
        output_path: Path
    ) -> bool:
        """Tam Reels videosu oluşturur"""
        try:
            from moviepy.editor import (
                AudioFileClip,
                ColorClip,
                CompositeVideoClip,
                TextClip,
                VideoFileClip,
                vfx
            )

            # Arka plan videosunu yükle
            video = VideoFileClip(str(background_video_path))

            # Videoyu hedef boyuta kırp veya yeniden boyutlandır
            video = self._resize_video(video)

            # Seslendirmeyi yükle
            audio = AudioFileClip(str(audio_path))
            video = video.set_audio(audio)

            # Videonun süresini sesle eşleştir
            video_duration = audio.duration
            video = video.subclip(0, min(video_duration, video.duration))

            # Sesin sonunda video bitsin
            if video.duration < audio.duration:
                video = video.loop(duration=audio.duration)
            else:
                video = video.subclip(0, audio.duration)

            # Altyazıları ekle
            video = self._add_subtitles(video, content.script)

            # Çıktı dosyasını kaydet
            video.write_videofile(
                str(output_path),
                fps=self.fps,
                codec=cfg.VideoConfig.CODEC,
                audio_codec=cfg.VideoConfig.AUDIO_CODEC,
                bitrate=cfg.VideoConfig.BITRATE,
                threads=4,
                logger=None
            )

            # Kaynakları serbest bırak
            video.close()
            audio.close()

            logger.info(f"Video oluşturuldu: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Video oluşturma hatası: {e}")
            return False

    def _resize_video(self, video) -> VideoFileClip:
        """Videoyu hedef boyuta uyarlar"""
        from moviepy.video.fx import all as vfx

        # Video boyutlarını hesapla
        target_ratio = self.width / self.height
        video_ratio = video.w / video.h

        if video_ratio > target_ratio:
            # Video çok geniş - yanları kırp
            new_width = int(video.h * target_ratio)
            x_center = video.w / 2
            video = video.crop(
                x1=x_center - new_width / 2,
                x2=x_center + new_width / 2,
                y1=0,
                y2=video.h
            )
        else:
            # Video çok uzun - alt/üst kırp
            new_height = int(video.w / target_ratio)
            y_center = video.h / 2
            video = video.crop(
                x1=0,
                x2=video.w,
                y1=y_center - new_height / 2,
                y2=y_center + new_height / 2
            )

        # Hedef boyuta ölçeklendir
        video = video.resize((self.width, self.height))

        return video

    def _add_subtitles(self, video, script: str) -> VideoFileClip:
        """Videoya altyazı ekler"""
        from moviepy.editor import TextClip, CompositeVideoClip

        # Senaryoyu cümlelere böl
        sentences = [s.strip() for s in script.split(".") if s.strip()]

        if not sentences:
            return video

        # Her cümle için altyazı oluştur
        clips = []

        for i, sentence in enumerate(sentences[:6]):  # En fazla 6 altyazı
            start_time = i * (video.duration / min(len(sentences), 6))
            end_time = start_time + (video.duration / min(len(sentences), 6))

            txt_clip = TextClip(
                sentence,
                fontsize=self.font_size_subtitle,
                font="DejaVu-Sans-Bold",
                color="white",
                stroke_color="black",
                stroke_width=2,
                method="caption",
                size=(self.width - 100, None)
            )

            txt_clip = txt_clip.set_start(start_time)
            txt_clip = txt_clip.set_duration(end_time - start_time)

            # Altyazıyı alt kısma konumlandır
            txt_clip = txt_clip.set_position(("center", self.height - 300))

            clips.append(txt_clip)

        # Kompozit video oluştur
        result = CompositeVideoClip([video] + clips)

        return result


# ═══════════════════════════════════════════════════════════════════════════════
# İNSTAGRAM PAYLAŞIMCI
# ═══════════════════════════════════════════════════════════════════════════════

class InstagramPoster:
    """İnstagrapi kullanarak Instagram'da paylaşım yapan sınıf"""

    def __init__(self):
        """Poster'ı başlatır"""
        self.username = cfg.InstagramConfig.USERNAME
        self.password = cfg.InstagramConfig.PASSWORD
        self.session_file = cfg.InstagramConfig.SESSION_FILE
        self.client = None

    async def connect(self) -> bool:
        """Instagram hesabına bağlanır"""
        try:
            from instagrapi import Client

            self.client = Client()

            # Önceki oturumu yükle (varsa)
            if self.session_file.exists():
                self.client.load_settings(str(self.session_file))

            # Giriş yap
            self.client.login(self.username, self.password)

            # Oturumu kaydet
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            self.client.dump_settings(str(self.session_file))

            logger.info(f"Instagram hesabına giriş yapıldı: {self.username}")
            return True

        except Exception as e:
            logger.error(f"Instagram bağlantı hatası: {e}")
            return False

    async def post_reel(self, video_path: Path, caption: str) -> Optional[str]:
        """Reels videosu paylaşır"""
        if not self.client:
            await self.connect()

        try:
            # Hashtag'leri ayrı satır olarak ekle
            hashtag_text = "\n\n#reels #viral #trending #instagood"

            full_caption = f"{caption}{hashtag_text}"

            # Videoyu kırp (Reels için gerekli)
            from instagrapi.exceptions import ClientError

            media = self.client.clip_upload(
                str(video_path),
                caption=full_caption[:cfg.InstagramConfig.CAPTION_MAX_LENGTH]
            )

            logger.info(f"Reels paylaşıldı: {media.code}")
            return media.code

        except Exception as e:
            logger.error(f"Reels paylaşım hatası: {e}")
            return None

    async def logout(self):
        """Oturumu kapatır"""
        if self.client:
            try:
                self.client.logout()
                logger.info("Instagram oturumu kapatıldı")
            except Exception as e:
                logger.error(f"Çıkış hatası: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT KOMUTLARI VE HANDLER'LAR
# ═══════════════════════════════════════════════════════════════════════════════

class TelegramBot:
    """Telegram bot ana sınıfı"""

    # Konuşma durumları
    WAITING_FOR_NICHE, WAITING_FOR_CONTENT, WAITING_FOR_CAPTION = range(3)

    def __init__(self):
        """Botu başlatır"""
        self.app = None
        self.db = Database()
        self.content_fetcher = ContentFetcher()
        self.ai_generator = AIContentGenerator()
        self.pexels_fetcher = PexelsVideoFetcher()
        self.voice_generator = VoiceOverGenerator()
        self.video_creator = VideoCreator()
        self.instagram_poster = InstagramPoster()

        # Geçici veri depolama
        self.user_data = {}
        self.processing_status = {}

    async def start(self):
        """Botu başlatır"""
        # Loglama sistemini kur
        setup_logging()

        # Yapılandırmayı doğrula
        try:
            cfg.validate_all_config()
        except ValueError as e:
            logger.error(f"Yapılandırma hatası: {e}")
            raise

        # Application oluştur
        self.app = Application.builder().token(cfg.TelegramConfig.BOT_TOKEN).build()

        # Handler'ları ekle
        self._register_handlers()

        # Botu başlat
        logger.info("Telegram bot başlatılıyor...")
        await self.app.run_polling(allowed_updates=Update.ALL_TYPES)

    def _register_handlers(self):
        """Komut handler'larını kaydeder"""

        # Komut handler'ları
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("settings", self.cmd_settings))
        self.app.add_handler(CommandHandler("fetch", self.cmd_fetch))
        self.app.add_handler(CommandHandler("generate", self.cmd_generate))
        self.app.add_handler(CommandHandler("post", self.cmd_post))
        self.app.add_handler(CommandHandler("cancel", self.cmd_cancel))

        # Callback query handler
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

        # Message handler (devam eden işlemler için)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    # ═══════════════════════════════════════════════════════════════════════════
    # KOMUT HANDLER'LARI
    # ═══════════════════════════════════════════════════════════════════════════

    async def cmd_start(self, update: Update, context: CallbackContext):
        """Başlangıç komutu"""
        user = update.effective_user

        welcome_text = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  Merhaba {user.first_name}! 👋                                                          ║
║                                                                              ║
║  Instagram Reels Botuna hoş geldin! Bu bot, Telegram üzerinden             ║
║  kontrol edebileceğiniz tam otomatik bir içerik üretim sistemidir.         ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  📋 KULLANILABİLİR KOMUTLAR:                                                ║
║                                                                              ║
║  /start   - Botu yeniden başlatır                                           ║
║  /help    - Kullanım kılavuzunu gösterir                                    ║
║  /status  - Sistem durumunu gösterir                                        ║
║  /fetch   - İçerik araştırır ve listeler                                    ║
║  /generate - Seçilen içerikten video oluşturur                             ║
║  /post    - Oluşturulan videoyu Instagram'da paylaşır                       ║
║  /settings - Ayarlar menüsünü açar                                          ║
║  /cancel  - Devam eden işlemi iptal eder                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """

        await update.message.reply_text(welcome_text)

        # Kullanıcı ayarlarını oluştur (yoksa)
        self._init_user_settings(user.id)

    async def cmd_help(self, update: Update, context: CallbackContext):
        """Yardım komutu"""
        help_text = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                         📚 KULLANIM KILAVUZU                                 ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  📌 ADIM 1: İÇERİK BULMA                                                    ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║  /fetch yazın ve bot RSS feed'leri ile Reddit'ten güncel içerikleri          ║
║  bulup size listelesin. Beğendiğiniz içeriği seçin.                          ║
║                                                                              ║
║  📌 ADIM 2: VİDEO OLUŞTURMA                                                 ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║  /generate yazın ve bot seçtiğiniz içerikten:                                ║
║  • Dikkat çekici bir başlık                                                     ║
║  • Video senaryosu (voiceover)                                                ║
║  • Instagram hashtag'leri                                                      ║
║  • Açıklama metni                                                              ║
║  oluşturur ve otomatik olarak video dosyasını hazırlar.                       ║
║                                                                              ║
║  📌 ADIM 3: PAYLAŞIM                                                         ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║  /post yazın ve bot videoyu Instagram Reels olarak paylaşır.                 ║
║                                                                              ║
║  ⚙️ AYARLAR                                                                  ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║  /settings ile:                                                              ║
║  • İçerik nişini değiştirebilirsiniz (teknoloji, iş, yaşam, vb.)            ║
║  • Otomatik paylaşımı açıp kapatabilirsiniz                                  ║
║  • Paylaşım saatlerini ayarlayabilirsiniz                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """

        await update.message.reply_text(help_text)

    async def cmd_status(self, update: Update, context: CallbackContext):
        """Durum komutu"""
        user_id = update.effective_user.id

        # API bağlantı durumları
        status_items = [
            ("🤖 Bot Durumu", "✅ Aktif"),
            ("📡 OpenAI Bağlantı", "✅ Bağlı" if cfg.OpenAIConfig.API_KEY else "❌ Bağlı Değil"),
            ("🎬 Pexels Bağlantı", "✅ Bağlı" if cfg.PexelsConfig.API_KEY else "❌ Bağlı Değil"),
            ("📸 Instagram", "🔄 Bağlanıyor..." if self.instagram_poster.client else "⏳ Bekliyor"),
            ("📦 Veritabanı", "✅ Hazır"),
        ]

        status_text = format_status_table(status_items)

        # Kullanıcı ayarlarını göster
        settings = self._get_user_settings(user_id)
        niche_text = f"\n\n📌 **Mevcut Niş:** {settings.get('niche', 'technology')}"
        auto_post_text = f"🔄 **Otomatik Paylaşım:** {'Aktif' if settings.get('auto_post') else 'Pasif'}"

        await update.message.reply_text(status_text + niche_text + auto_post_text)

    async def cmd_settings(self, update: Update, context: CallbackContext):
        """Ayarlar komutu"""
        keyboard = [
            [
                InlineKeyboardButton("🔧 İçerik Nişi", callback_data="setting_niche"),
                InlineKeyboardButton("⏰ Paylaşım Saatleri", callback_data="setting_times"),
            ],
            [
                InlineKeyboardButton("🔄 Otomatik Paylaşım", callback_data="setting_auto"),
            ],
            [
                InlineKeyboardButton("📋 Mevcut Ayarlar", callback_data="settings_view"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "⚙️ **Ayarlar Menüsü**\n\nBir seçenek seçin:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def cmd_fetch(self, update: Update, context: CallbackContext):
        """İçerik bulma komutu"""
        user_id = update.effective_user.id
        message = await update.message.reply_text("📡 İçerikler araştırılıyor...")

        try:
            # İçerikleri çek
            contents = await self.content_fetcher.fetch_all()

            if not contents:
                await message.edit_text("❌ Hiç içerik bulunamadı. Lütfen RSS feed veya Reddit ayarlarınızı kontrol edin.")
                return

            # Veritabanına kaydet
            for content in contents:
                self.db.save_content(content)

            # İçerikleri butonlarla göster
            keyboard = []
            for i, content in enumerate(contents[:10]):
                # Başlığı kısalt
                title = content.title[:50] + "..." if len(content.title) > 50 else content.title
                keyboard.append([
                    InlineKeyboardButton(
                        f"📰 {title}",
                        callback_data=f"content_{i}"
                    )
                ])

            keyboard.append([
                InlineKeyboardButton("🔄 Yenile", callback_data="fetch_refresh")
            ])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await message.edit_text(
                f"✅ **{len(contents)} içerik bulundu!**\n\n"
                f"Video oluşturmak için bir içerik seçin:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

            # İçerikleri user_data'ya kaydet
            self.user_data[user_id] = {"contents": contents}

        except Exception as e:
            logger.error(f"İçerik bulma hatası: {e}")
            await message.edit_text(f"❌ Hata oluştu: {str(e)}")

    async def cmd_generate(self, update: Update, context: CallbackContext):
        """Video oluşturma komutu"""
        user_id = update.effective_user.id

        # Kayıtlı içerik var mı kontrol et
        contents = self.db.get_unused_content(limit=10)

        if not contents:
            await update.message.reply_text(
                "❌ Henüz içerik bulunamadı.\n\n"
                "Lütfen önce /fetch komutuyla içerik araştırın."
            )
            return

        # İçerikleri göster
        keyboard = []
        for i, content in enumerate(contents):
            title = content.title[:40] + "..." if len(content.title) > 40 else content.title
            keyboard.append([
                InlineKeyboardButton(
                    f"📝 {title}",
                    callback_data=f"generate_{i}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🎬 **Video Oluşturma**\n\n"
            "Video oluşturmak için bir içerik seçin:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def cmd_post(self, update: Update, context: CallbackContext):
        """Paylaşım komutu"""
        user_id = update.effective_user.id

        # Instagram'a bağlan
        await update.message.reply_text("📸 Instagram hesabına bağlanılıyor...")

        if not await self.instagram_poster.connect():
            await update.message.reply_text("❌ Instagram hesabına bağlanılamadı. Lütfen .env dosyasındaki bilgileri kontrol edin.")
            return

        await update.message.reply_text("✅ Instagram hesabına bağlanıldı!\n\n🎬 Video paylaşmak için /generate komutuyla önce video oluşturmalısınız.")

    async def cmd_cancel(self, update: Update, context: CallbackContext):
        """İptal komutu"""
        user_id = update.effective_user.id

        if user_id in self.processing_status:
            self.processing_status[user_id] = {"cancelled": True}
            await update.message.reply_text("✅ İşlem iptal edildi.")
        else:
            await update.message.reply_text("ℹ️ İptal edilecek bir işlem bulunmuyor.")

    # ═══════════════════════════════════════════════════════════════════════════
    # CALLBACK HANDLER
    # ═══════════════════════════════════════════════════════════════════════════

    async def handle_callback(self, update: Update, context: CallbackContext):
        """Callback query handler"""
        query = update.callback_query
        user_id = query.from_user.id

        await query.answer()

        data = query.data

        if data.startswith("content_"):
            # İçerik seçimi
            await self._handle_content_selection(query, user_id, data)

        elif data.startswith("generate_"):
            # Video oluşturma başlatma
            await self._handle_generate_request(query, user_id, data)

        elif data.startswith("setting_"):
            # Ayarlar
            await self._handle_settings(query, user_id, data)

        elif data.startswith("post_approve_"):
            # Manuel paylaşım onayı
            await self._handle_post_approve(query, user_id, data)

        elif data == "post_reject":
            # Paylaşımı iptal et
            await self._handle_post_reject(query, user_id)

        elif data == "fetch_refresh":
            # İçerikleri yenile
            await query.message.edit_text("📡 İçerikler yeniden araştırılıyor...")
            await self.cmd_fetch(update, context)

    async def _handle_content_selection(self, query, user_id: int, data: str):
        """İçerik seçimi işleyicisi"""
        index = int(data.split("_")[1])

        if user_id not in self.user_data or "contents" not in self.user_data[user_id]:
            await query.message.edit_text("❌ İçerik verisi bulunamadı. Lütfen /fetch komutunu tekrar çalıştırın.")
            return

        contents = self.user_data[user_id]["contents"]

        if index >= len(contents):
            await query.message.edit_text("❌ Geçersiz içerik seçimi.")
            return

        content = contents[index]

        # İçerik detaylarını göster
        detail_text = f"""
📰 **İçerik Detayları**

**Başlık:** {content.title}

**Açıklama:** {content.description[:200]}...

**Kaynak:** {content.source}

**URL:** {content.url}

🎬 Bu içerikten video oluşturmak için /generate yazın.
        """

        keyboard = [
            [InlineKeyboardButton("🎬 Video Oluştur", callback_data=f"generate_{index}")],
            [InlineKeyboardButton("📋 Diğer İçerikler", callback_data="fetch_refresh")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(
            detail_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def _handle_generate_request(self, query, user_id: int, data: str):
        """Video oluşturma isteği işleyicisi"""
        index = int(data.split("_")[1])

        # Seçilen içeriği al
        contents = self.db.get_unused_content(limit=10)

        if index >= len(contents):
            await query.message.edit_text("❌ Geçersiz içerik seçimi.")
            return

        content = contents[index]
        progress_msg = await query.message.edit_text(
            "🤖 **AI İçerik Üretiyor...**\n\n"
            f"{format_progress_bar(0, 100)}\n\n"
            "Senaryo ve başlık oluşturuluyor..."
        )

        try:
            # AI ile içerik üret
            generated = await self.ai_generator.generate(content)

            await progress_msg.edit_text(
                f"✅ **İçerik Üretildi!**\n\n"
                f"**Başlık:** {generated.headline}\n\n"
                f"**Senaryo:** {generated.script[:200]}...\n\n"
                f"**Hashtag'ler:** {' '.join(generated.hashtags[:5])}...\n\n"
                f"{format_progress_bar(30, 100)}\n\n"
                "🎬 Video arka planı aranıyor..."
            )

            # Pexels'tan video ara
            search_query = generated.headline[:30] + " " + cfg.ContentSourcesConfig.CONTENT_NICHE
            videos = await self.pexels_fetcher.search_videos(search_query)

            if not videos:
                # Anahtar kelimelerle dene
                videos = await self.pexels_fetcher.search_videos(
                    random.choice(cfg.ContentSourcesConfig.get_keywords())
                )

            await progress_msg.edit_text(
                f"✅ **İçerik Üretildi!**\n\n"
                f"**Başlık:** {generated.headline}\n\n"
                f"**Senaryo:** {generated.script[:200]}...\n\n"
                f"**Hashtag'ler:** {' '.join(generated.hashtags[:5])}...\n\n"
                f"{format_progress_bar(40, 100)}\n\n"
                "🎬 Video bulundu! İndiriliyor..."
            )

            # Video indir
            if videos:
                video_data = videos[0]
                video_url = video_data["video_files"][0]["link"]
                video_path = cfg.TEMP_DIR / f"video_{uuid.uuid4().hex[:8]}.mp4"

                success = await self.pexels_fetcher.download_video(video_url, video_path)

                if not success:
                    await progress_msg.edit_text(
                        "❌ Video indirilemedi. Lütfen daha sonra tekrar deneyin."
                    )
                    return
            else:
                await progress_msg.edit_text(
                    "❌ Uygun video bulunamadı. Lütfen daha sonra tekrar deneyin."
                )
                return

            await progress_msg.edit_text(
                f"✅ **İçerik Üretildi!**\n\n"
                f"**Başlık:** {generated.headline}\n\n"
                f"**Senaryo:** {generated.script[:200]}...\n\n"
                f"**Hashtag'ler:** {' '.join(generated.hashtags[:5])}...\n\n"
                f"{format_progress_bar(60, 100)}\n\n"
                "🔊 Seslendirme oluşturuluyor..."
            )

            # Seslendirme oluştur
            audio_path = cfg.TEMP_DIR / f"audio_{uuid.uuid4().hex[:8]}.mp3"
            self.voice_generator.generate(generated.script, audio_path)

            await progress_msg.edit_text(
                f"✅ **İçerik Üretildi!**\n\n"
                f"**Başlık:** {generated.headline}\n\n"
                f"**Senaryo:** {generated.script[:200]}...\n\n"
                f"**Hashtag'ler:** {' '.join(generated.hashtags[:5])}...\n\n"
                f"{format_progress_bar(80, 100)}\n\n"
                "🎞️ Video düzenleniyor..."
            )

            # Video oluştur
            output_path = cfg.OUTPUT_DIR / f"reels_{uuid.uuid4().hex[:8]}.mp4"
            video_success = await self.video_creator.create_video(
                video_path, audio_path, generated, output_path
            )

            if not video_success:
                await progress_msg.edit_text(
                    "❌ Video oluşturulamadı. Lütfen FFmpeg'in kurulu olduğundan emin olun."
                )
                return

            # Temizlik
            video_path.unlink(missing_ok=True)
            audio_path.unlink(missing_ok=True)

            # Video önizlemesi gönder
            if cfg.VideoConfig.SEND_PREVIEW:
                # Videoyu kullanıcıya gönder
                await progress_msg.edit_text(
                    f"✅ **Video Hazır!**\n\n"
                    f"**Başlık:** {generated.headline}\n\n"
                    f"**Senaryo:** {generated.script[:200]}...\n\n"
                    f"**Hashtag'ler:** {' '.join(generated.hashtags[:5])}...\n\n"
                    f"{format_progress_bar(100, 100)}\n\n"
                    "📹 Video gönderiliyor..."
                )

                # Videoyu Telegram üzerinden gönder
                try:
                    with open(output_path, "rb") as video_file:
                        await context.bot.send_video(
                            chat_id=user_id,
                            video=video_file,
                            caption=f"🎬 **Video Önizlemesi**\n\n"
                                    f"**Başlık:** {generated.headline}\n\n"
                                    f"Beğenmediyseniz /generate ile yeni video oluşturabilirsiniz."
                        )
                except Exception as e:
                    logger.error(f"Video gönderme hatası: {e}")
                    await progress_msg.edit_text(
                        f"✅ **Video Hazır!**\n\n"
                        f"Video dosyası: {output_path}\n\n"
                        "Not: Video önizlemesi gönderilemedi. Dosyayı kontrol edin."
                    )

            # Manuel onay bekleyen paylaşım
            if cfg.VideoConfig.MANUAL_APPROVAL:
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Paylaş", callback_data=f"post_approve_{index}"),
                        InlineKeyboardButton("❌ İptal", callback_data="post_reject")
                    ],
                    [
                        InlineKeyboardButton("🔄 Yeni Video Oluştur", callback_data="fetch_refresh")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await progress_msg.edit_text(
                    f"✅ **Video Hazır!**\n\n"
                    f"**Başlık:** {generated.headline}\n\n"
                    f"**Senaryo:** {generated.script[:200]}...\n\n"
                    f"**Hashtag'ler:** {' '.join(generated.hashtags[:5])}...\n\n"
                    f"{format_progress_bar(100, 100)}\n\n"
                    "📸 Instagram'da paylaşmak için aşağıdaki butonları kullanın:\n"
                    "✅ 'Paylaş' → Videoyu Instagram'da paylaşır\n"
                    "❌ 'İptal' → Paylaşımı iptal eder\n"
                    "🔄 'Yeni Video' → Yeni içerik araştırır",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                # Otomatik paylaşım modu
                await progress_msg.edit_text(
                    f"✅ **Video Hazır!**\n\n"
                    f"**Başlık:** {generated.headline}\n\n"
                    f"**Senaryo:** {generated.script[:200]}...\n\n"
                    f"**Hashtag'ler:** {' '.join(generated.hashtags[:5])}...\n\n"
                    f"{format_progress_bar(100, 100)}\n\n"
                    "📸 Video otomatik olarak Instagram'da paylaşılıyor..."
                )

                # Otomatik olarak paylaş
                post_id = await self._auto_post_video(query.message.chat_id, output_path, generated)

                if post_id:
                    await progress_msg.edit_text(
                        f"🎉 **Video Paylaşıldı!**\n\n"
                        f"**Başlık:** {generated.headline}\n\n"
                        f"Instagram Link: https://www.instagram.com/p/{post_id}/\n\n"
                        "✅ Başarıyla Instagram'da paylaşıldı!"
                    )
                else:
                    await progress_msg.edit_text(
                        f"⚠️ **Video Hazır ama Paylaşılamadı**\n\n"
                        f"**Başlık:** {generated.headline}\n\n"
                        f"Video dosyası: {output_path}\n\n"
                        "Instagram paylaşımı başarısız oldu. Lütfen /post ile tekrar deneyin."
                    )

            # Kullanıcı verilerine kaydet
            self.user_data[user_id] = {
                "generated_content": generated,
                "video_path": output_path
            }

            # İçeriği kullanıldı olarak işaretle
            self.db.mark_content_used(index + 1)

        except Exception as e:
            logger.error(f"Video oluşturma hatası: {e}")
            await progress_msg.edit_text(f"❌ Hata oluştu: {str(e)}")

    async def _handle_settings(self, query, user_id: int, data: str):
        """Ayarlar handler'ı"""
        setting = data.split("_")[1]

        if setting == "niche":
            keyboard = []
            niches = ["technology", "business", "lifestyle", "science", "gaming", "news"]

            for niche in niches:
                keyboard.append([
                    InlineKeyboardButton(f"#{niche}", callback_data=f"niche_set_{niche}")
                ])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(
                "🔧 **İçerik Nişini Seçin**\n\n"
                "Bot hangi konularda içerik arayacak?",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        elif setting == "auto":
            current = self._get_user_settings(user_id).get("auto_post", False)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ Aktif" if not current else "❌ Pasif",
                        callback_data=f"auto_toggle_{'true' if not current else 'false'}"
                    )
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.edit_text(
                f"🔄 **Otomatik Paylaşım**\n\n"
                f"Mevcut durum: {'Aktif' if current else 'Pasif'}\n\n"
                "Otomatik paylaşım açıkken, bot belirlenen saatlerde "
                "otomatik olarak video oluşturup paylaşır.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        elif setting == "view":
            settings = self._get_user_settings(user_id)

            view_text = f"""
📋 **Mevcut Ayarlar**

🔹 **Niş:** {settings.get('niche', 'technology')}
🔹 **Otomatik Paylaşım:** {'Aktif' if settings.get('auto_post') else 'Pasif'}
🔹 **Paylaşım Saatleri:** {', '.join(cfg.SchedulerConfig.BEST_POST_TIMES)}

📌 **Değiştirmek için /settings yazın.**
            """

            await query.message.edit_text(view_text, parse_mode="Markdown")

    async def handle_message(self, update: Update, context: CallbackContext):
        """Mesaj handler'ı"""
        # Devam eden konuşmalar için mesaj işleme
        pass

    async def _handle_post_approve(self, query, user_id: int, data: str):
        """Manuel paylaşım onayı işleyicisi"""
        await query.message.edit_text("📸 **Instagram'da Paylaşılıyor...**\n\nLütfen bekleyin, bu işlem birkaç dakika sürebilir.")

        try:
            # Kullanıcı verilerinden video bilgisini al
            if user_id not in self.user_data or "video_path" not in self.user_data[user_id]:
                await query.message.edit_text(
                    "❌ **Hata:** Video bilgisi bulunamadı.\n\n"
                    "Lütfen önce /generate komutuyla video oluşturun."
                )
                return

            video_path = self.user_data[user_id]["video_path"]
            generated = self.user_data[user_id]["generated_content"]

            if not video_path or not video_path.exists():
                await query.message.edit_text(
                    "❌ **Hata:** Video dosyası bulunamadı.\n\n"
                    "Lütfen /generate ile yeniden video oluşturun."
                )
                return

            # Instagram'a bağlan
            if not await self.instagram_poster.connect():
                await query.message.edit_text(
                    "❌ **Hata:** Instagram hesabına bağlanılamadı.\n\n"
                    "Lütfen .env dosyasındaki Instagram bilgilerini kontrol edin."
                )
                return

            # Videoyu paylaş
            post_id = await self.instagram_poster.post_reel(video_path, generated.caption)

            if post_id:
                # Başarılı paylaşım
                keyboard = [
                    [InlineKeyboardButton("🔗 Instagram'da Görüntüle", url=f"https://www.instagram.com/p/{post_id}/")],
                    [InlineKeyboardButton("🎬 Yeni Video Oluştur", callback_data="fetch_refresh")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.message.edit_text(
                    f"🎉 **Video Paylaşıldı!**\n\n"
                    f"**Başlık:** {generated.headline}\n\n"
                    f"✅ Video başarıyla Instagram'da paylaşıldı!\n\n"
                    f"📎 Instagram Linki: https://www.instagram.com/p/{post_id}/\n\n"
                    "🎬 Yeni bir video oluşturmak için butonları kullanabilirsiniz.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )

                # Kullanıcı verilerini temizle
                if user_id in self.user_data:
                    del self.user_data[user_id]

            else:
                await query.message.edit_text(
                    "❌ **Paylaşım Başarısız!**\n\n"
                    "Instagram paylaşımı sırasında bir hata oluştu.\n"
                    "Lütfen Instagram hesabınızı kontrol edin ve tekrar deneyin.\n\n"
                    "📌 İpuçları:\n"
                    "• Instagram hesabınızda giriş yapık durumda olduğundan emin olun\n"
                    "• Hesabınızda 2FA (iki faktörlü doğrulama) açıksa kapatın\n"
                    "• Hesabınızın spam olarak işaretlenmediğinden emin olun"
                )

        except Exception as e:
            logger.error(f"Paylaşım hatası: {e}")
            await query.message.edit_text(f"❌ **Hata:** {str(e)}\n\nLütfen daha sonra tekrar deneyin.")

    async def _handle_post_reject(self, query, user_id: int):
        """Paylaşımı iptal et"""
        keyboard = [
            [InlineKeyboardButton("🔄 Yeni Video Oluştur", callback_data="fetch_refresh")],
            [InlineKeyboardButton("📋 İçerikleri Görüntüle", callback_data="fetch_refresh")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(
            "❌ **Paylaşım İptal Edildi**\n\n"
            "Video Instagram'da paylaşılmadı.\n\n"
            "🎬 Yeni bir video oluşturmak veya içerikleri görüntülemek için "
            "aşağıdaki butonları kullanabilirsiniz:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

        # Kullanıcı verilerini temizle
        if user_id in self.user_data:
            del self.user_data[user_id]

    async def _auto_post_video(self, chat_id, video_path: Path, generated: GeneratedContent) -> Optional[str]:
        """Videoyu otomatik olarak paylaşır"""
        try:
            # Instagram'a bağlan
            if not await self.instagram_poster.connect():
                return None

            # Videoyu paylaş
            post_id = await self.instagram_poster.post_reel(video_path, generated.caption)
            return post_id

        except Exception as e:
            logger.error(f"Otomatik paylaşım hatası: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # YARDIMCI FONKSİYONLAR
    # ═══════════════════════════════════════════════════════════════════════════

    def _init_user_settings(self, user_id: int):
        """Kullanıcı ayarlarını başlatır"""
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO user_settings (user_id)
                VALUES (?)
                """,
                (user_id,)
            )
            conn.commit()

    def _get_user_settings(self, user_id: int) -> Dict:
        """Kullanıcı ayarlarını getirir"""
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT niche, auto_post, post_times FROM user_settings WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()

            if row:
                return {
                    "niche": row[0],
                    "auto_post": bool(row[1]),
                    "post_times": row[2].split(",") if row[2] else []
                }

            return {"niche": "technology", "auto_post": False, "post_times": []}


# ═══════════════════════════════════════════════════════════════════════════════
# ANA FONKSİYON
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Ana asenkron fonksiyon"""
    bot = TelegramBot()

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot kapatılıyor...")
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")
        raise


# ═══════════════════════════════════════════════════════════════════════════════
# MODÜL İÇERAK
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                              ║")
    print("║           INSTAGRAM REELS BOT                                                ║")
    print("║           Telegram Kontrollü Otomatik İçerik Üretim Sistemi                  ║")
    print("║                                                                              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("Bot başlatılıyor...")
    print()
    print("Kurulum talimatları:")
    print("1. .env.example dosyasını .env olarak kopyalayın")
    print("2. Tüm API anahtarlarınızı ve kimlik bilgilerinizi doldurun")
    print("3. requirements.txt'deki paketleri kurun: pip install -r requirements.txt")
    print("4. FFmpeg'in kurulu olduğundan emin olun")
    print("5. Botu çalıştırın: python main.py")
    print()

    asyncio.run(main())
