# 🤖 Tam Otomatik Instagram Reels Botu

## Proje Özeti

Bu proje, Telegram üzerinden kontrol edilen ve Instagram Reels videolarını tam otomatik olarak oluşturup paylaşabilen kapsamlı bir içerik üretim sistemidir. Sistem, RSS feed'leri ve Reddit'ten içerik toplar, Groq Llama 3.1 ile senaryo üretir, Pexels API'den stok video çeker, seslendirme oluşturur ve son olarak oluşturulan videoyu Instagram'da paylaşır.

## 🎯 Temel Özellikler

### İçerik Yönetimi

- **Çoklu Kaynak Desteği**: RSS feed'leri ve Reddit subreddit'lerinden otomatik içerik toplama
- **Niş Odaklı İçerik**: Teknoloji, iş dünyası, yaşam, bilim, oyun ve haber kategorilerinde içerik arama
- **Akıllı Filtreleme**: Anahtar kelime bazlı içerik eşleştirme ve tekrarları önleme
- **Veritabanı Entegrasyonu**: SQLite ile içerik geçmişi ve durum takibi

### Yapay Zeka Entegrasyonu

- **Groq Llama 3.1 70B**: Tamamen ücretsiz, GPU hızında LLM servisi
- **Otomatik Başlık Üretimi**: Dikkat çekici ve tıklanabilir başlıklar
- **Hashtag Optimizasyonu**: SEO uyumlu ve trend hashtag önerileri
- **Konuşma Dili Senaryo**: Doğal ve akıcı Türkçe voiceover metinleri

### Video Üretimi

- **Pexels Video API**: Yüksek kaliteli stok video kütüphanesi
- **Portrait Format Desteği**: Instagram Reels için 9:16 aspect ratio
- **Akıllı Video Kırpma**: Arka plan videosunu otomatik boyutlandırma
- **Altyazı Ekleme**: MoviePy ile profesyonel altyazılar
- **gTTS Seslendirme**: Google Text-to-Speech ile doğal ses

### Instagram Paylaşımı

- **İnstagrapi Entegrasyonu**: Güvenli Instagram API kullanımı
- **Oturum Yönetimi**: Otomatik giriş ve oturum saklama
- **Reels Desteği**: Dikey video formatında paylaşım
- **Zamanlama Seçeneği**: En iyi yayın saatlerinde paylaşım

### Telegram Arayüzü

- **Kullanıcı Dostu Komutlar**: Basit ve anlaşılır komut yapısı
- **İnteraktif Butonlar**: Hızlı ve sezgisel navigasyon
- **İlerleme Takibi**: Video oluşturma sürecinde görsel geri bildirim
- **Çoklu Kullanıcı Desteği**: Yetkili kullanıcı yönetimi

## 📁 Proje Yapısı

```
instagram_reels_bot/
├── main.py                 # Ana bot dosyası ve tüm modüller
├── config.py               # Yapılandırma ayarları
├── requirements.txt        # Python bağımlılıkları
├── .env.example            # Ortam değişkenleri şablonu
├── README.md               # Bu dosya
├── temp/                   # Geçici dosyalar için
├── output/                 # Üretilen videolar için
├── media/                  # İndirilen medya dosyaları için
├── logs/                   # Log dosyaları için
├── sessions/               # Instagram oturum dosyaları için
├── data/                   # Veritabanı dosyaları için
└── cache/                  # Önbellek dosyaları için
```

## 🔧 Kurulum Adımları

### İki Seçenek: Yerel Bilgisayar veya Render.com

Bu botu iki farklı şekilde çalıştırabilirsiniz:

**Seçenek 1: Render.com (Önerilen - 7/24 Çalışır)**
Telefonunuzdan sadece Telegram üzerinden botu kontrol edersiniz. Bot sürekli çalışır ve mesajlarınızı yanıtlar. Detaylı kurulum için `DEPLOY_RENDER.md` dosyasına bakın.

**Seçenek 2: Yerel Bilgisayar**
Botu kendi bilgisayarınızda çalıştırırsınız. Bilgisayar açık olduğu sürece bot çalışır.

### Gereksinimler

Kuruluma başlamadan önce aşağıdaki gereksinimlerin karşılandığından emin olun:

- **Python 3.10 veya üzeri**: Python programlama dili
- **FFmpeg**: Video işleme için gerekli multimedya framework'ü
- **API Anahtarları**: Groq (ücretsiz), Pexels (ücretsiz) ve Instagram hesap bilgileri
- **GitHub Hesabı**: Render.com deploy için gerekli

### Adım 1: Python Ortamı Hazırlama

İlk olarak, Python sanal ortamını oluşturun ve aktifleştirin. Bu, projenin bağımlılıklarının sistem genelinde yüklü paketlerle çakışmasını önleyecektir.

```bash
# Proje klasörüne gidin
cd instagram_reels_bot

# Sanal ortam oluşturun
python -m venv venv

# Sanal ortamı aktifleştirin
# Linux veya macOS için:
source venv/bin/activate

# Windows için:
venv\Scripts\activate
```

### Adım 2: Bağımlılıkları Kurma

Sanal ortam aktifken, projenin gerektirdiği Python paketlerini yükleyin:

```bash
pip install -r requirements.txt
```

Bu işlem tüm gerekli paketleri kuracaktır. Kurulum birkaç dakika sürebilir çünkü moviepy gibi büyük paketler de dahildir.

### Adım 3: FFmpeg Kurulumu

Video işleme için FFmpeg'in sisteminizde kurulu olması gerekmektedir:

**Ubuntu veya Debian tabanlı sistemler:**

```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS (Homebrew ile):**

```bash
brew install ffmpeg
```

**Windows:**

1. [FFmpeg resmi sitesinden](https://ffmpeg.org/download.html) Windows sürümünü indirin
2. ZIP dosyasını çıkartın
3. `ffmpeg/bin` klasörünü sistem PATH'ine ekleyin

Kurulumun başarılı olduğunu doğrulamak için terminalde şu komutu çalıştırın:

```bash
ffmpeg -version
```

### Adım 4: Ortam Değişkenlerini Yapılandırma

`.env.example` dosyasını `.env` olarak kopyalayın ve tüm API anahtarlarınızı doldurun:

```bash
cp .env.example .env
```

Ardından, `.env` dosyasını bir metin editörüyle açarak aşağıdaki bilgileri doldurun:

**Telegram Bot Token:**

1. Telegram'da [@BotFather](https://t.me/BotFather) hesabına mesaj gönderin
2. `/newbot` komutuyla yeni bir bot oluşturun
3. Aldığınız token'ı `TELEGRAM_BOT_TOKEN` değerine yapıştırın

**OpenAI API Anahtarı:**

1. [OpenAI Platform](https://platform.openai.com/) sitesine gidin
2. API Keys bölümünden yeni bir anahtar oluşturun
3. Anahtarı `OPENAI_API_KEY` değerine yapıştırın
4. Kullandığınız modeli `OPENAI_MODEL` olarak belirtin (varsayılan: gpt-4o)

**Pexels API Anahtarı:**

1. [Pexels API](https://www.pexels.com/api/) sayfasına gidin
2. Hesap oluşturun ve API anahtarınızı alın
3. Anahtarı `PEXELS_API_KEY` değerine yapıştırın

**Instagram Hesap Bilgileri:**

Instagram hesap bilgilerinizi `INSTAGRAM_USERNAME` ve `INSTAGRAM_PASSWORD` alanlarına girin. Bu bilgiler yalnızca yerel oturum dosyasında saklanır ve sunucuya gönderilmez.

**İçerik Kaynakları:**

RSS feed URL'lerini ve takip etmek istediğiniz Reddit subreddit'lerini virgülle ayırarak listeleyin. Örnek olarak:

```
RSS_FEEDS=https://www.theverge.com/rss/index.xml,https://feeds.feedburner.com/TechCrunch/
REDDIT_SUBREDDITS=technology,programming,artificial
```

### Adım 5: Botu Başlatma

Tüm yapılandırma tamamlandıktan sonra botu başlatın:

```bash
python main.py
```

Bot başarıyla başlatıldığında, Telegram'da oluşturduğunuz bota mesaj göndererek `/start` komutunu kullanın.

## 📖 Kullanım Kılavuzu

### Temel Komutlar

Bot, Telegram üzerinden aşağıdaki komutları desteklemektedir:

**`/start`** — Botu başlatır ve hoşgeldin mesajını gösterir. Bu komut, botla ilk etkileşiminizde veya herhangi bir zaman botun durumunu sıfırlamak istediğinizde kullanılır.

**`/help`** — Kullanım kılavuzunu ve detaylı açıklamaları görüntüler. Bu komut, botun nasıl kullanılacağı hakkında adım adım talimatlar sunar.

**`/status`** — Sistemin mevcut durumunu gösterir. OpenAI, Pexels ve Instagram bağlantı durumlarını kontrol edebilir, ayrıca mevcut ayarlarınızı görüntüleyebilirsiniz.

**`/fetch`** — RSS feed'leri ve Reddit'ten içerik araştırır. Bot, belirlediğiniz niş ile ilgili güncel içerikleri bulur ve size liste halinde sunar.

**`/generate`** — Seçilen içerikten tam bir Reels videosu oluşturur. Bu komut, AI ile senaryo üretir, stok video indirir, seslendirme oluşturur ve tüm bunları profesyonel bir video dosyasına dönüştürür.

**`/post`** — Oluşturulan videoyu Instagram hesabınızda paylaşır. Video hazır değilse, önce `/generate` komutuyla video oluşturmanız gerektiğini hatırlatır.

**`/settings`** — Ayarlar menüsünü açar. Burada içerik nişinizi değiştirebilir, otomatik paylaşımı açıp kapatabilir ve paylaşım saatlerinizi ayarlayabilirsiniz.

**`/cancel`** — Devam eden bir işlemi iptal eder. Video oluşturma veya paylaşım sürecinde herhangi bir sorun olduğunda bu komutu kullanabilirsiniz.

### Çalışma Akışı

Botun temel çalışma akışı şu şekildedir:

**Adım 1 — İçerik Bulma:**
`/fetch` komutunu kullanarak içerik araştırması yapın. Bot, belirlediğiniz RSS feed'leri ve Reddit subreddit'lerini tarayarak ilgili içerikleri listeleyecektir. Listeden beğendiğiniz bir içeriği seçin.

**Adım 2 — Video Oluşturma:**
Seçtiğiniz içeriğin üzerine tıklayarak video oluşturmayı başlatın. Bot, Groq Llama 3.1 API'sini kullanarak dikkat çekici bir başlık, akıcı bir Türkçe senaryo ve uygun hashtag'ler üretir. Ardından Pexels'tan ilgili bir stok video indirir, Google Text-to-Speech ile Türkçe seslendirme oluşturur ve son olarak moviepy ile tüm bu öğeleri birleştirerek profesyonel bir Reels videosu hazırlar.

**Adım 3 — Önizleme ve Onay:**
Video hazır olduğunda, Telegram'da önizleme olarak gönderilir. İnceleyin ve beğendiyseniz "✅ Paylaş" butonuna tıklayın. Beğenmediyseniz "❌ İptal" ile yeni video oluşturabilirsiniz.

**Adım 4 — Paylaşım:**
Paylaş butonuna tıkladığınızda, bot videoyu Instagram hesabınızda Reels olarak paylaşır ve size Instagram linkini gönderir.

### Ayarlar Menüsü

`/settings` komutuyla erişilen ayarlar menüsü, bot davranışını özelleştirmenize olanak tanır. İçerik nişi seçeneği, botun hangi konularda içerik arayacağını belirler. Teknoloji, iş dünyası, yaşam tarzı, bilim, oyun ve haber olmak üzere altı farklı niş arasından seçim yapabilirsiniz.

Otomatik paylaşım özelliği, botun belirlenen saatlerde otomatik olarak video oluşturup paylaşmasını sağlar. Bu özellik açıkken, bot her saat başı içerik kontrolü yapar ve uygun içerik bulursa video oluşturarak Instagram'da paylaşır.

Paylaşım saatleri, videoların hangi zamanlarda paylaşılacağını belirler. Varsayılan olarak Türkiye saatiyle 09:00, 12:30, 19:00 ve 21:00 saatleri ayarlanmıştır. Bu saatleri istediğiniz gibi değiştirebilirsiniz.

## ⚙️ Yapılandırma Seçenekleri

### Ortam Değişkenleri Referansı

`.env` dosyasında aşağıdaki değişkenleri özelleştirebilirsiniz:

**Video Ayarları:**

| Değişken | Varsayılan | Açıklama |
|----------|------------|----------|
| VIDEO_WIDTH | 1080 | Video genişliği (piksel) |
| VIDEO_HEIGHT | 1920 | Video yüksekliği (piksel) |
| VIDEO_FPS | 30 | Saniye başına kare sayısı |
| VIDEO_QUALITY | 1080 | Video kalitesi (1080, 720, 480) |
| TTS_LANGUAGE | tr | Seslendirme dili (tr, en, es, fr, de) — **Türkçe için: tr** |
| SEND_PREVIEW | True | Video oluşturulduktan sonra önizleme gönderilsin mi? |
| MANUAL_APPROVAL | True | Paylaşım için manuel onay gereksin mi? |

**İçerik Ayarları:**

| Değişken | Varsayılan | Açıklama |
|----------|------------|----------|
| CONTENT_NICHE | technology | İçerik nişi |
| CONTENT_CHECK_INTERVAL | 60 | Otomatik kontrol aralığı (dakika) |
| AUTO_CONTENT_ENABLED | False | Otomatik içerik üretimi |
| AUTO_POST_ENABLED | False | Otomatik paylaşım |

**Zamanlama Ayarları:**

| Değişken | Varsayılan | Açıklama |
|----------|------------|----------|
| BEST_POST_TIMES | 09:00,12:30,19:00,21:00 | En iyi paylaşım saatleri |

### Niş Anahtar Kelimeleri

Her niş için otomatik olarak eşleştirilecek anahtar kelimeler `config.py` dosyasında tanımlıdır. Kendi anahtar kelimelerinizi eklemek veya mevcut olanları değiştirmek için `ContentSourcesConfig.NICHE_KEYWORDS` sözlüğünü düzenleyebilirsiniz.

## 🔐 Güvenlik Notları

Bot güvenliği açısından aşağıdaki noktalara dikkat edilmelidir:

**API Anahtarlarının Korunması:** `.env` dosyası asla git deposuna eklenmemeli veya başkalarıyla paylaşılmamalıdır. Bu dosya `.gitignore` listesine eklenmiştir.

**Instagram Hesabı:** Instagram oturum bilgileriniz yalnızca yerel bir JSON dosyasında saklanır. Hassas bir hesap kullanıyorsanız, iki faktörlü doğrulamayı geçici olarak devre dışı bırakmanız gerekebilir.

**Otomatik Paylaşım:** Otomatik paylaşım özelliğini kullanmadan önce, üretilen içeriğin Instagram'ın topluluk kurallarına uygun olduğundan emin olun.

## 🐛 Sorun Giderme

### Yaygın Hatalar ve Çözümleri

**"FFmpeg not found" hatası:** FFmpeg kurulmamış veya PATH'e eklenmemiş demektir. Kurulum adımlarını takip edin ve sisteminizi yeniden başlatın.

**"Groq API error" hatası:** API anahtarının doğru olduğundan ve Groq hesabınızın aktif olduğundan emin olun. Ücretsiz API anahtarı için console.groq.com adresini ziyaret edin.

**"Instagram login failed" hatası:** Instagram hesap bilgilerinin doğru olduğunu kontrol edin. Hesabınızda olağandışı giriş denemeleri engellenmiş olabilir, bu durumda Instagram'dan e-posta ile giriş izni vermeniz gerekebilir.

**"Video generation failed" hatası:** İndirilen videonun bozuk olması veya seslendirme oluşturma sırasında bir hata oluşması bu hataya neden olabilir. `/fetch` ile farklı bir içerik seçmeyi deneyin.

### Log Dosyaları

Hata ayıklama için `logs/bot.log` dosyasını inceleyebilirsiniz. Log seviyesini `.env` dosyasında `LOG_LEVEL=DEBUG` olarak değiştirerek daha detaylı log'lar alabilirsiniz.

## 📝 Lisans

Bu proje eğitim ve kişisel kullanım amaçlı geliştirilmiştir. Ticari kullanım için lütfen ilgili API sağlayıcılarının kullanım şartlarını kontrol edin.

## 🤝 Katkıda Bulunma

Bu proje açık kaynaklıdır ve katkılarınızı memnuniyetle karşılıyoruz. İyileştirme önerileriniz veya hata düzeltmeleriniz için pull request gönderebilirsiniz.

## 📞 Destek

Herhangi bir sorunuz veya yardıma ihtiyacınız varsa, GitHub repository'sinde bir issue açarak bizimle iletişime geçebilirsiniz.

---

**Geliştirici Notu:** Bu bot, içerik üretimi sürecini otomatikleştirmek için tasarlanmıştır. Üretilen içeriğin doğruluğu ve kalitesi, kullanılan API'lerin kapasitesine bağlıdır. Her zaman üretilen içeriği paylaşmadan önce kontrol etmeniz önerilir.


## 💚 Ücretsiz API Alternatifleri

Bu proje, tamamen ücretsiz API'ler kullanacak şekilde tasarlanmıştır. Aşağıda kullanılan ve alternatif olabilecek ücretsiz API'lerin karşılaştırmasını bulabilirsiniz.

### Groq API — Kullanımdaki Seçenek (Önerilen)

**Durum:** Aktif olarak kullanılıyor

**Maliyet:** Tamamen ücretsiz

**Özellikler:**
- Llama 3.1 70B modeli — GPT-4'e yakın kalite
- GPU hızında yanıt süreleri
- Dakikada 30 istek limiti
- Açık kaynak modellerin gücü

**Kurulum:**
1. console.groq.com adresine gidin
2. Google veya GitHub ile kayıt olun
3. Sol menüden "API Keys" seçin
4. "Create API Key" ile yeni anahtar oluşturun
5. Anahtarı .env dosyasına `GROQ_API_KEY` olarak ekleyin

**Kullanılan Model:**
```env
GROQ_MODEL=llama-3.1-70b-versatile
```

### Diğer Ücretsiz Alternatifler

**Google Gemini API:**
- Gemini 1.5 Flash — Önemli miktarda ücretsiz istek
- Çoklu modalite desteği
- Uzun bağlam penceresi
- Kurulum: ai.google.dev

**Hugging Face Inference API:**
- Yüzlerce açık kaynak model
- Tamamen ücretsiz tier
- Daha yavaş yanıt süreleri
- Kurulum: huggingface.co/inference-api

**Ollama (Yerel):**
- Tamamen ücretsiz, veriler cihazda kalır
- Güçlü bilgisayar gerektirir
- Bulut sunucularında çalışmaz
- Kurulum: ollama.com

### Maliyet Karşılaştırması

| API Sağlayıcı | Aylık Maliyet | Günlük Video Limiti |
|---------------|---------------|---------------------|
| Groq (Llama 3.1 70B) | 0 TL | ~100+ video |
| OpenAI (GPT-4o-mini) | ~50-200 TL | ~500-1000 video |
| OpenAI (GPT-4o) | ~500-2000 TL | ~100-500 video |
| Google Gemini | 0-50 TL | ~500+ video |

### Neden Groq?

Groq, bu proje için en iyi seçimdir çünkü tamamen ücretsiz olması, GPU hızında çalışması, yüksek kaliteli açık kaynak modeller kullanması ve karmaşık kurulum gerektirmemesi gibi avantajlara sahiptir. Llama 3.1 70B modeli, video senaryosu oluşturma gibi görevler için GPT-4'e yakın sonuçlar üretir.
