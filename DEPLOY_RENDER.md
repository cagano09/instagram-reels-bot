# Instagram Reels Bot - Render Deployment Rehberi

## İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Gereksinimler](#gereksinimler)
3. [Adım Adım Kurulum](#adım-adım-kurulum)
4. [Render Ayarları](#render-ayarları)
5. [Çevre Değişkenleri](#çevre-değişkenleri)
6. [Yaygın Hatalar ve Çözümler](#yaygın-hatalar-ve-çözümler)
7. [Doğrulama ve Test](#doğrulama-ve-test)

---

## Genel Bakış

Bu rehber, Instagram Reels Bot'unu Render.com üzerinde nasıl deploy edeceğinizi adım adım açıklamaktadır. Bot, Telegram üzerinden kontrol edilen ve Instagram Reels videolarını otomatik olarak oluşturup paylaşabilen bir sistemdir. Sistem tamamen otomatik çalışır: içerik araştırır, AI ile senaryo üretir, video oluşturur ve Instagram'da paylaşır.

### Bot Özellikleri

Instagram Reels Bot, birçok gelişmiş özellik sunmaktadır. Otomatik içerik toplama modülü, RSS feed'leri ve Reddit'ten güncel içerikleri çeker ve bunları nişinize göre filtreler. AI içerik üretimi, Groq API kullanarak ilgi çekici senaryolar, başlıklar ve hashtag'ler oluşturur. Video oluşturma özelliği, Pexels'tan stok videolar çeker, Türkçe seslendirme ekler ve profesyonel altyazılar hazırlar. Instagram paylaşımı ise manuel onay ile veya tam otomatik olarak Reels formatında paylaşım yapar.

---

## Gereksinimler

### Gerekli Hesaplar

Deployment işlemine başlamadan önce aşağıdaki hesapların hazır olması gerekmektedir. Her bir hesap için kayıt işlemlerini tamamlayın ve gerekli API anahtarlarını güvenli bir yerde saklayın.

**GitHub Hesabı**: Kod depolamak ve versiyon kontrolü için gereklidir. GitHub, ücretsiz hesapla sınırsız public ve private repository oluşturmanıza olanak tanır. GitHub mobil uygulamasını kullanarak dosyaları iOS cihazınızdan da yükleyebilirsiniz.

**Render Hesabı**: Cloud hosting hizmeti için gereklidir. Render, ücretsiz planla 750 saat ayda sunar ve Python, Node.js, Ruby ve diğer dilleri destekler. Ücretsiz planda kredi kartı gerekmez ancak ek özellikler için ücretli planlar mevcuttur.

**Telegram Bot Token**: BotFather'dan alınabilir. Telegram botu, sistemin kullanıcı arayüzü olarak çalışır ve tüm komutları buradan alırsınız. BotFather'da /newbot komutunu kullanarak yeni bir bot oluşturabilir ve token'ı alabilirsiniz.

**Groq API Anahtarı**: GroqCloud'dan alınabilir ve tamamen ücretsizdir. Groq, yüksek hızlı AI inference hizmeti sunar ve Llama, Mixtral gibi modelleri destekler. console.groq.com adresinden kayıt olarak API anahtarınızı alabilirsiniz.

**Pexels API Anahtarı**: Pexels'tan alınabilir ve ücretsiz planda aylık 200 API isteği sunar. Pexels, yüksek kaliteli stok videolar ve fotoğraflar için mükemmel bir kaynaktır. pexels.com/api adresinden kayıt olarak anahtarınızı alabilirsiniz.

**Instagram Hesabı**: Video paylaşımı için gereklidir. Instagram hesabınızda iki faktörlü doğrulama (2FA) açıksa, instagrapi'nin çalışması için bir uygulama şifresi oluşturmanız gerekebilir.

### Teknik Gereksinimler

Sistemin düzgün çalışması için aşağıdaki teknik gereksinimlerin karşılanması gerekmektedir. Bu gereksinimler, Render'ın altyapısı tarafından büyük ölçüde karşılanır ancak build sürecinde doğru komutların kullanılması önemlidir.

Python 3.10 veya üzeri sürüm gereklidir ve Render varsayılan olarak Python 3.11 veya 3.12 sunar. FFmpeg, video işleme için sistem düzeyinde kurulu olmalıdır ve moviepy kütüphanesi buna bağımlıdır. Görüntü işleme için libjpeg-dev, zlib1g-dev ve libpng-dev paketleri gereklidir; bu paketler Pillow kütüphanesinin düzgün çalışması için zorunludur. Minimum 512MB RAM, Render'ın free tier için yeterli olan varsayılan bellek miktarıdır.

---

## Adım Adım Kurulum

### Adım 1: GitHub Deposu Oluşturma

#### iOS Cihazdan GitHub Deposu Oluşturma

GitHub kullanarak projenizi yönetmek için iOS cihazınızdan bir repository oluşturabilirsiniz. Bu yöntem, bilgisayar kullanmadan tüm deployment sürecini tamamlamanızı sağlar.

İlk olarak, App Store'dan GitHub mobil uygulamasını indirin ve GitHub hesabınızla giriş yapın. Uygulama açıldığında, sağ üst köşedeki "+" ikonuna dokunun ve "Create repository" seçeneğini seçin. Repository adı olarak "instagram-reels-bot" yazın ve açıklama alanına "Telegram ile kontrol edilen Instagram Reels botu" yazın. Gizlilik ayarını "Private" olarak bırakın; bu, API anahtarlarınızın güvende kalmasını sağlar. "Add a README file" seçeneğini işaretleyin ve ardından "Create repository" butonuna dokunun.

Repository oluşturulduktan sonra, proje dosyalarını yüklemeniz gerekmektedir. Repository sayfasında "Add file" butonuna dokunun ve "Upload files" seçeneğini seçin. Proje klasöründeki tüm dosyaları seçin ve yükleyin. Commit mesajı olarak "Initial commit - Instagram Reels Bot" yazın ve "Commit changes" butonuna dokunun.

#### Yüklenecek Dosyalar

Proje klasöründeki aşağıdaki dosyaları yükleyin:

```
instagram_reels_bot/
├── main.py              # Ana uygulama dosyası - tüm bot mantığı burada
├── config.py            # Yapılandırma modülü - API ayarları ve sabitler
├── requirements.txt    # Python bağımlılıkları - pip ile kurulacak paketler
├── Procfile            # Render deployment ayarları - build ve start komutları
├── build.sh            # Build script - sistem paketi kurulumu (YENİ)
├── README.md           # Proje dokümantasyonu
├── DEPLOY_RENDER.md    # Bu deployment rehberi
├── .env.example        # Ortam değişkenleri şablonu - API anahtarları için
└── config/             # Konfigürasyon klasörü (varsa)
```

**Kritik Güvenlik Uyarısı**: `.env` dosyasını **ASLA** GitHub'a yüklemeyin! Bu dosya gerçek API anahtarlarınızı içerir ve public repository'ye yüklenmesi durumunda kötüye kullanılabilir. Sadece `.env.example` dosyasını yükleyin ve gerçek değerleri Render'ın Environment Variables bölümüne girin.

### Adım 2: Render'da Web Servisi Oluşturma

#### Render.com'a Giriş ve Hesap Oluşturma

Render.com adresine gidin ve GitHub hesabınızla giriş yapın. "Get Started" butonuna tıklayın ve temel bilgilerinizi girin. GitHub entegrasyonunu onaylayın; bu, Render'ın repository'nize erişmesini sağlayacaktır.

#### Yeni Servis Oluşturma

Dashboard'da sağ üst köşedeki "New +" butonuna tıklayın. Açılan menüden "Web Service" seçeneğini seçin. Bu, Python uygulamanızı barındıracak web servisini oluşturacaktır.

GitHub sekmesinde, "instagram-reels-bot" repository'nizi göreceksiniz. Bu repository'yi seçin ve "Connect" butonuna tıklayın. Açılan sayfada aşağıdaki temel ayarları yapılandırın.

**Name (İsim)**: `instagram-reels-bot` olarak girin. Bu isim, servisinizin URL'sinin bir parçası olacaktır (örneğin: instagram-reels-bot.onrender.com).

**Region (Bölge)**: "Frankfurt (EU Central)" seçin. Bu, Türkiye'ye yakın olduğu için düşük gecikme süresi sağlar.

**Branch (Dal)**: "main" olarak bırakın. Kodunuzu main dalına yüklediğinizden emin olun.

**Runtime (Çalışma Zamanı)**: "Python 3" seçin. Render otomatik olarak uygun Python sürümünü seçecektir.

**Instance Type (Örnek Tipi)**: "Free" seçin. Ücretsiz plan, bu proje için yeterlidir ve kredi kartı gerektirmez.

---

## Render Ayarları

### Build ve Start Komutları

Build ve Start komutları, uygulamanın Render'da nasıl çalışacağını belirler. Doğru komutların kullanılması, deployment başarısı için kritik öneme sahiptir.

**Build Command (Derleme Komutu)**: Bu komut, uygulama başlatılmadan önce çalışır ve gerekli bağımlılıkları kurar. Varsayılan olarak `pip install -r requirements.txt` gelir ancak sistem paketleri için ek komutlar gerekebilir.

**Start Command (Başlatma Komutu)**: Bu komut, uygulama başlatıldığında çalışır. `python main.py` olarak ayarlanmalıdır.

### Instance ve Kaynak Ayarları

Render'ın free tier'ı, belirli kaynak sınırlamalarıyla gelir. Bu sınırlamaları anlamak, performans sorunlarını önlemenize yardımcı olur.

Memory (Bellek) değeri 512 MB olarak ayarlanmıştır ve free tier'da değiştirilemez. Bu, video işleme gibi bellek yoğun işlemler için yeterli olabilir ancak büyük videolarla çalışırken sorun yaşayabilirsiniz. Swap (Takas) alanı free tier'da 0 MB'dır ve ek bellek kullanımı mümkün değildir. CPU değeri 0.5 vCPU olarak ayarlanmıştır ve bu, temel işlemler için yeterlidir.

---

## Çevre Değişkenleri

### Environment Variables Bölümü

Çevre değişkenleri, uygulamanın çalışması için gerekli API anahtarlarını ve yapılandırma değerlerini içerir. Bu değişkenler, Render'ın arayüzünden eklenir ve uygulama başlatıldığında otomatik olarak yüklenir.

** kritik not**: Çevre değişkenlerini eklerken "Secret" seçeneğini işaretlemeyin; bu, değişkenlerin log'larda görünmesini engeller ve güvenliği artırır.

### Zorunlu Değişkenler

Aşağıdaki değişkenler, botun düzgün çalışması için mutlaka ayarlanmalıdır. Her bir değişken için doğru değerleri girin ve aralarında boşluk bırakmadan kaydedin.

| Değişken Adı | Açıklama | Örnek Değer |
|--------------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `GROQ_API_KEY` | Groq API anahtarı (ücretsiz) | `gsk_xxxxxxxxxxxx` |
| `PEXELS_API_KEY` | Pexels API anahtarı | `xxxxxxxxxxxx` |
| `INSTAGRAM_USERNAME` | Instagram kullanıcı adı | `kullanici_adi` |
| `INSTAGRAM_PASSWORD` | Instagram şifresi | `sifre123` |

### Opsiyonel Değişkenler

Bu değişkenler, varsayılan değerleriyle çalışır ancak ihtiyacınıza göre özelleştirebilirsiniz.

| Değişken Adı | Açıklama | Varsayılan Değer |
|--------------|----------|------------------|
| `GROQ_MODEL` | Groq modeli | `llama-3.1-70b-versatile` |
| `TTS_LANGUAGE` | Seslendirme dili | `tr` (Türkçe) |
| `SEND_PREVIEW` | Video önizleme gönder | `True` |
| `MANUAL_APPROVAL` | Manuel onay gerekli | `True` |
| `LOG_LEVEL` | Log seviyesi | `INFO` |
| `MAX_TOKENS` | Maksimum token sayısı | `2048` |

### Çevre Değişkenlerini Ekleme Adımları

Render dashboard'unda servisizi seçin ve "Environment" sekmesine gidin. Her değişken için aşağıdaki adımları tekrarlayın:

"Key" alanına değişken adını büyük harflerle yazın. "Value" alanına ilgili değeri yapıştırın. Değişken adı ve değeri arasında boşluk veya özel karakter kullanmayın. "+ Add Environment Variable" butonuna tıklayarak değişkeni kaydedin. Tüm değişkenleri ekledikten sonra "Save Changes" butonuna tıklayın.

---

## Yaygın Hatalar ve Çözümler

### Hata 1: "Exited with status 1" - Pillow Build Hatası

**Hata Mesajı**: `ERROR: Failed to build 'Pillow' when getting requirements to build wheel`

**Sebep**: Pillow paketi, kurulum sırasında C derleyicisi kullanarak görüntü işleme kütüphanelerini derler. Sistemde gerekli başlık dosyaları (header files) yoksa, derleme başarısız olur. libjpeg-dev, zlib1g-dev ve libpng-dev paketleri bu başlık dosyalarını içerir.

**Çözüm**:

Build Command'i şu şekilde değiştirin:

```
apt-get update && apt-get install -y libjpeg-dev zlib1g-dev libpng-dev && pip install --no-cache-dir -r requirements.txt
```

Bu komut sırasıyla şunları yapar: Sistem paket listesini günceller, gerekli görüntü işleme kütüphanelerini kurar ve Python bağımlılıklarını yükler.

"Clear build cache & deploy" seçeneğini işaretleyin. Bu, önceki başarısız build'lerin cache'ini temizler ve temiz bir kurulum sağlar. Ardından "Deploy" butonuna tıklayın.

### Hata 2: "Exited with status 100" - Build Timeout

**Hata Mesajı**: `Exited with status 100 while building your code`

**Sebep**: Status 100 hatası, Render'ın build işlemi sırasında belirli bir hata kodu döndürdüğünü gösterir. Bu hata genellikle şu durumlarda ortaya çıkar: apt-get komutlarının çalışması sırasında ağ bağlantısı sorunları, sistem paketlerinin kurulumunda yaşanan timeout hataları, komut zincirinin herhangi bir noktasında başarısızlık veya Render'ın ücretsiz planındaki kaynak sınırlamaları.

**Çözümler**:

**Çözüm A - Basit pip komutu (Önerilen)**:

Sistem paketlerini atlayarak sadece Python paketlerini kurun:

```
pip install --no-cache-dir -r requirements.txt
```

Bu komut, önceden derlenmiş wheel dosyalarını kullanmaya çalışır ve daha hızlı tamamlanır. Pillow ve moviepy gibi paketler, wheel dosyaları mevcutsa sorunsuz kurulabilir.

**Çözüm B - Optimize edilmiş sistem paketi kurulumu**:

Sistem paketlerini daha az bağımlılıkla kurun:

```
apt-get update && apt-get install -y --no-install-recommends libjpeg-dev zlib1g-dev libpng-dev ffmpeg && pip install --no-cache-dir -r requirements.txt
```

`--no-install-recommends` parametresi, gereksiz bağımlılıkların kurulmasını engeller ve kurulum süresini önemli ölçüde kısaltır. Ayrıca kurulum sırasında oluşabilecek hata olasılığını azaltır.

**Çözüm C - Build script kullanımı**:

Projeye dahil ettiğimiz `build.sh` scriptini kullanın. Bu script, kurulum sürecini daha kontrollü bir şekilde yönetir ve hata durumunda daha açık hata mesajları verir.

Build Command'i şu şekilde değiştirin:

```
bash build.sh
```

"Clear build cache & deploy" seçeneğini işaretleyin ve "Deploy" butonuna tıklayın.

**Çözüm D - Alternatif build script**:

Eğer build.sh da çalışmazsa, aşağıdaki daha basit script'i deneyin. Bu script, her adımı ayrı ayrı çalıştırır ve hata durumunda hangi adımın başarısız olduğunu gösterir:

```
#!/bin/bash
set -e
apt-get update -qq
apt-get install -y libjpeg-dev zlib1g-dev libpng-dev ffmpeg
pip install --no-cache-dir -r requirements.txt
```

### Hata 3: "Module not found" - Eksik Bağımlılık

**Hata Mesajı**: `ModuleNotFoundError: No module named 'moviepy'`

**Sebep**: Python paketleri düzgün kurulmamış veya yanlış sırayla kurulmuş olabilir. Bu genellikle, build komutunun başarısız olmasından sonra eksik paketlerle uygulamanın başlatılmaya çalışılmasından kaynaklanır.

**Çözüm**:

İlk olarak, build komutunun doğru olduğundan emin olun ve "Clear build cache & deploy" seçeneğini işaretleyin. requirements.txt dosyasındaki paket adlarını ve sürümlerini kontrol edin. Render'ın build log'larında paket kurulumunun başarılı olup olmadığını doğrulayın.

### Hata 4: "ffmpeg not found"

**Hata Mesajı**: `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'`

**Sebep**: FFmpeg, video işleme için gerekli bir araçtır ve moviepy kütüphanesi buna bağımlıdır. FFmpeg sistem düzeyinde kurulu değilse, video işleme başarısız olur.

**Çözüm**: Build Command'e FFmpeg kurulumunu ekleyin:

```
apt-get update && apt-get install -y ffmpeg && pip install --no-cache-dir -r requirements.txt
```

### Hata 5: Instagram Login Hatası

**Hata Mesajı**: "Instagram login failed" veya "Challenge required"

**Sebep**: Instagram, hesabınıza giriş yapan yeni cihazları (instagrapi) algılayabilir ve ek doğrulama isteyebilir. Ayrıca, iki faktörlü doğrulama (2FA) açıksa, instagrapi giriş yapamaz.

**Çözümler**:

Instagram hesabınızda 2FA açıksa, kapatın veya bir uygulama şifresi oluşturun. Uygulama şifresi, 2FA etkinken bile instagrapi'nin çalışmasını sağlar. Instagram hesabınızda "Yeni cihaz girişi onay" gibi bir uyarı gelirse, e-postanızı kontrol edin ve girişi onaylayın. Hesabınızda "Şüpheli giriş engellendi" gibi bir uyarı varsa, Instagram'ın güvenlik e-postasındaki bağlantıyla girişi onaylayın.

### Hata 6: Telegram Bot Yanıt Vermiyor

**Hata Mesajı**: Bot çalışıyor gibi görünüyor ama Telegram'dan mesajlara cevap vermiyor.

**Sebep**: Bot token yanlış veya Telegram botu silinmiş olabilir. Ayrıca, Render'da bot başarıyla başlatılmamış olabilir.

**Çözümler**:

Telegram Bot Token'ın doğru olduğunu kontrol edin. Render logs'unu kontrol edin ve botun başarıyla başlatılıp başlatılmadığını doğrulayın. BotFather'da botun aktif olduğundan emin olun. Telegram'da botu durdurun ve "/start" yazın.

---

## Doğrulama ve Test

### Deployment Başarılı mı Kontrol Etme

Deployment tamamlandıktan sonra, sistemin düzgün çalışıp çalışmadığını doğrulamanız önemlidir. Bu adımları sırayla izleyerek, olası sorunları erken tespit edebilirsiniz.

**Render Dashboard Kontrolü**: Servis durumunun "Live" olduğunu kontrol edin. Yeşil renkli bir nokta veya "Live" yazısı, servisin aktif olduğunu gösterir. Durum "Building" veya "Deploying" ise, işlemin tamamlanmasını bekleyin.

**Logs Kontrolü**: Render'da "Logs" sekmesine gidin. Burada, botun başlatılma sürecini ve çalışma log'larını görebilirsiniz. Aşağıdaki mesajları arayın:

```
Telegram bot başlatılıyor...
Bot başarıyla çalışıyor
```

Bu mesajları görüyorsanız, bot başarıyla başlatılmış demektir. Hata mesajları görüyorsanız, "Yaygın Hatalar ve Çözümler" bölümüne bakın.

**Telegram Test**: Telegram uygulamanızda bot'unuza gidin. "/start" yazın ve gönderin. Bot, hoşgeldin mesajıyla yanıt vermelidir. Yanıt almıyorsanız, bot token'ın doğru olduğundan ve Render'da botun çalıştığından emin olun.

### Bot Komutlarını Test Etme

Bot çalıştıktan sonra, aşağıdaki komutları sırayla test edin:

**1. /start Komutu**: Botu başlatır ve hoşgeldin mesajı gönderir. Bu komut, botun düzgün çalışıp çalışmadığını doğrular.

**2. /help Komutu**: Kullanım kılavuzunu gösterir. Botun tüm komutlarının listelendiğini doğrulayın.

**3. /status Komutu**: Sistem durumunu gösterir. API bağlantı durumlarını ve yapılandırma ayarlarını görüntüler.

**4. /settings Komutu**: Ayarlar menüsünü açar. Niş değiştirme, otomatik paylaşım açma/kapama gibi ayarları yapabilirsiniz.

**5. /fetch Komutu**: İçerik araştırır ve RSS feed'lerinden ile Reddit'ten içerik bulur. Birkaç saniye içinde içerik listesi gelmelidir.

### Video Oluşturma Testi

Video oluşturma özelliğini test etmek için aşağıdaki adımları izleyin:

"/fetch" komutunu çalıştırın ve gelen içerik listesinden birini seçin. İçerik seçtikten sonra, bot otomatik olarak video oluşturmaya başlayacaktır. İlerleme mesajlarını takip edin: AI içerik üretiyor, video aranıyor, video indiriliyor, seslendirme oluşturuluyor ve video düzenleniyor.

Video hazır olduktan sonra, önizlemesi Telegram'da gönderilecektir. Videoyu izleyin ve beğenip beğenmediğinizi kontrol edin. Beğendiyseniz, "Paylaş" butonuna tıklayın. Instagram hesabınızda paylaşımı kontrol edin.

---

## Hızlı Kontrol Listesi

Deployment öncesi ve sonrası kontrol etmeniz gerekenler:

**Deployment Öncesi Kontroller**:

- GitHub repository oluşturuldu ve tüm dosyalar yüklendi
- Render'da Web Service oluşturuldu ve GitHub repository bağlandı
- Tüm Environment Variables (çevre değişkenleri) doğru girildi
- Build Command doğru ayarlandı (sistem paketleri dahil)
- Start Command "python main.py" olarak ayarlandı
- "Clear build cache & deploy" seçeneği işaretlendi (varsa)

**Deployment Sonrası Kontroller**:

- Render dashboard'da servis durumu "Live" olarak görünüyor
- Render logs'larında "Bot başarıyla çalışıyor" mesajı var
- Telegram botu "/start" komutuna yanıt veriyor
- "/fetch" komutu içerik buluyor ve listeliyor
- "/status" komutu tüm API bağlantılarının aktif olduğunu gösteriyor

---

## Önemli Notlar

### Güvenlik Uyarıları

API anahtarlarınızı asla GitHub'a yüklemeyin. `.env` dosyasını `.gitignore`'a ekleyin ve sadece Render ortam değişkenlerinde saklayın. `.env.example` dosyasını kullanarak, hangi değişkenlerin gerekli olduğunu belgeleyebilirsiniz.

Instagram hesabı oturum açma bilgilerinizi güvenli tutun. 2FA kullanıyorsanız, bot için bir uygulama şifresi oluşturun. Bu, hem güvenliği artırır hem de instagrapi'nin düzgün çalışmasını sağlar.

Telegram bot token'ınızı herkesle paylaşmayın. Bu token ile botunuz kontrol edilebilir ve istenmeyen mesajlar gönderilebilir.

### Performans İpuçları

Render'ın free tier'ında instance, 15 dakika işlem yapılmazsa uyku moduna girer. İlk istekte 30 saniyeye kadar bekleme süresi olabilir. Botun sürekli çalışmasını istiyorsanız, UptimeRobot gibi ücretsiz bir servis kullanarak Render URL'nizi düzenli olarak pingleyebilirsiniz.

Build süresi, ilk deployment'da 5-10 dakika sürebilir. Sonraki deployment'lar, Render'ın cache kullanması sayesinde daha hızlı olacaktır.

Video işleme memory yoğun bir işlemdir. Memory hatası alırsanız, daha küçük boyutlu videolar kullanmayı deneyin veya Pexels'tan daha kısa süreli videolar seçin.

### Destek ve Sorun Giderme

Herhangi bir sorunla karşılaşırsanız, öncelikle Render logs'unu kontrol edin. Bu log'lar, hatanın nedenini genellikle açıkça gösterir. Ardından bu rehberin "Yaygın Hatalar ve Çözümler" bölümünü inceleyin. GitHub repository'nizin güncel olduğundan emin olun ve tüm değişikliklerin Render'a yansıdığını doğrulayın.

---

**Son Güncelleme**: 21 Nisan 2026

**Sürüm**: 2.0

**Yazar**: MiniMax Agent
