# Render.com'a Deploy Etme Rehberi

Bu rehber, Instagram Reels Botunu Render.com'da 7/24 çalışacak şekilde deploy etmenizi sağlar.

## Ön Koşullar

Deploy işlemine başlamadan önce aşağıdaki hazırlıkları yapın:

1. **GitHub Hesabı**: github.com adresinden kayıt olun
2. **Git Kurulumu**: Bilgisayarınızda Git kurulu olmalı
3. **API Anahtarları**: Aşağıdaki anahtarları hazırlayın:
   - Telegram Bot Token (@BotFather'dan)
   - Groq API Key (console.groq.com'dan - ÜCRETSİZ)
   - Pexels API Key (pexels.com/api'den - ÜCRETSİZ)
   - Instagram Kullanıcı adı ve şifre

---

## Adım 1: GitHub Repository Oluşturma

### 1.1 GitHub'da Yeni Repository Oluşturma

GitHub.com'a giriş yapın. Sağ üst köşedeki "+" ikonuna tıklayın ve "New repository" seçin. Repository adı olarak "instagram-reels-bot" yazın. Description olarak "Telegram ile kontrol edilen Instagram Reels botu" yazın. "Public" seçeneğini işaretleyin. "Add a README file" seçeneğini işaretleyin. "Create repository" butonuna tıklayın.

### 1.2 Proje Dosyalarını Yükleme

Yeni oluşturduğunuz repository sayfasında, indirdiğiniz bot dosyalarını yükleyin. "Add file" butonuna tıklayın ve "Upload files" seçin. Aşağıdaki dosyaları sürükleyip bırakın: main.py, config.py, requirements.txt, .env.example, Procfile, README.md, DEPLOY_RENDER.md (bu dosya). "Commit changes" butonuna tıklayın.

Alternatif olarak, bilgisayarınızda Git kullanarak dosyaları yükleyebilirsiniz:

```bash
git init
git add .
git commit -m "Instagram Reels Bot - İlk sürüm"
git branch -M main
git remote add origin https://github.com/KULLANICI_ADI/instagram-reels-bot.git
git push -u origin main
```

---

## Adım 2: Render.com Hesabı Oluşturma

### 2.1 Render.com'a Kayıt

Tarayıcınızda render.com adresine gidin. "Get Started" veya "Sign Up" butonuna tıklayın. GitHub hesabınızla giriş yapın (bu, repository'nize erişim için gereklidir). İzinleri onaylayın.

### 2.2 GitHub Bağlantısı

Render dashboard'unda sol menüden "GitHub" seçeneğine tıklayın. "Connect GitHub" butonuna tıklayın. Açılan pencerede repository'nize erişim izni verin. Artık GitHub'daki repository'niz Render'a bağlı.

---

## Adım 3: Web Service Oluşturma

### 3.1 Yeni Service Oluşturma

Render dashboard'unda sağ üstteki "New +" butonuna tıklayın. "Web Service" seçeneğini seçin.

### 3.2 Repository Seçme

GitHub hesabınızı bağladıysanız, GitHub sekmesinde repository'nizi görürsünüz. "instagram-reels-bot" repository'sini seçin.

### 3.3 Temel Ayarlar

Name bölümüne "instagram-reels-bot" yazın. Bu, servisinizin URL'sinin bir parçası olacak. Region olarak "Frankfurt (EU Central)" seçin (Türkiye'ye yakın ve düşük gecikme). Branch olarak "main" seçili kalın. Runtime olarak "Python 3" seçin.

### 3.4 Build ve Start Komutları

Build Command olarak `pip install -r requirements.txt` yazılı olmalı (varsayılan). Start Command olarak `python main.py` yazılı olmalı (varsayılan).

### 3.5 Instance Type Seçme

Plan olarak "Free" seçin. Free tier, bu proje için yeterlidir ve kredi kartı gerektirmez.

---

## Adım 4: Environment Variables (Çevre Değişkenleri)

Bu adım çok önemli! Tüm API anahtarlarınızı buraya ekleyeceksiniz.

### 4.1 Environment Variables Bölümü

Aşağı kaydırarak "Environment Variables" bölümünü bulun. Buraya aşağıdaki değişkenleri tek tek ekleyin:

**TELEGRAM_BOT_TOKEN** değeri olarak BotFather'dan aldığınız tokeni yapıştırın. Örnek: `7123456789:ABCDefGHIjklMNOpqrsTUVwxyz123456789`

**GROQ_API_KEY** değeri olarak console.groq.com'dan aldığınız anahtarı yapıştırın. Örnek: `gsk_xxxxxxxxxxxxxxxxxxxxxxxx`

**PEXELS_API_KEY** değeri olarak pexels.com/api'den aldığınız anahtarı yapıştırın. Örnek: `xxxxxxxxxxxxxxxxxxxxxxxx`

**INSTAGRAM_USERNAME** değeri olarak Instagram kullanıcı adınızı yazın. Örnek: `teknolojireels`

**INSTAGRAM_PASSWORD** değeri olarak Instagram şifrenizi yazın. Örnek: `Sifre123!`

**RSS_FEEDS** değeri olarak `https://www.theverge.com/rss/index.xml,https://feeds.feedburner.com/TechCrunch/` yazın.

**REDDIT_SUBREDDITS** değeri olarak `technology,programming,artificial` yazın.

**CONTENT_NICHE** değeri olarak `technology` yazın (veya istediğiniz niş).

**TTS_LANGUAGE** değeri olarak `tr` yazın (Türkçe seslendirme için).

**SEND_PREVIEW** değeri olarak `True` yazın (videoyu önce size göndermek için).

**MANUAL_APPROVAL** değeri olarak `True` yazın (paylaşım için onayınızı almak için).

**LOG_LEVEL** değeri olarak `INFO` yazın.

**GROQ_MODEL** değeri olarak `llama-3.1-70b-versatile` yazın.

**MAX_TOKENS** değeri olarak `2048` yazın.

### 4.2 Değişkenleri Kaydetme

Tüm değişkenleri ekledikten sonra, sayfanın en altındaki "Create Web Service" butonuna tıklayın.

---

## Adım 5: Deploy Sürecini İzleme

### 5.1 Build Log'larını İzleme

Deploy başladığında, Build log'ları ekranda görünecek. Bu log'lar, kurulum sürecinin nasıl gittiğini gösterir. Hata varsa log'larda görünür.

### 5.2 Başarılı Deploy

Yeşil renkli "Live" yazısını ve "Your service is live" mesajını görürseniz, deploy başarılı olmuş demektir.

### 5.3 Olası Hatalar ve Çözümleri

"Build failed" hatası alırsanız, log'larda hatanın nedenini okuyun. Genellikle eksik Environment Variable veya syntax hatasından kaynaklanır.

"Import Error" hatası alırsanız, requirements.txt'deki paket adlarını kontrol edin ve Render'ın paketleri doğru kurduğundan emin olun.

---

## Adım 6: Telegram Botunu Başlatma

### 6.1 Botu Test Etme

Render deploy tamamlandıktan sonra, Telegram uygulamanızda botunuzu açın. "/start" yazın ve gönderin. Bot hoşgeldin mesajıyla yanıt vermeli.

### 6.2 Botu Kullanma

"/fetch" yazın — bot RSS ve Reddit'ten içerik bulmaya başlar. İstediğiniz içeriği seçin. Bot video oluşturmaya başlar. Video hazır olduğunda Telegram'da önizlemesini görürsünüz. "✅ Paylaş" butonuna tıklayarak Instagram'da paylaşabilirsiniz.

---

## Önemli Notlar

### Render Free Tier Sınırlamaları

Free tier'da service 90 gün boyunca kullanılmazsa uyku moduna girer. Uyku modundan çıkmak için Telegram'da botunuza bir mesaj göndermeniz yeterli. Service uyandıktan sonra yaklaşık 30 saniye içinde tekrar çalışmaya başlar.

### 7/24 Çalışma İpucu

Botun sürekli çalışmasını sağlamak için, UptimeRobot gibi ücretsiz bir servis kullanarak Render URL'nizi düzenli olarak pingleyebilirsiniz. Bu, service'in uyku moduna girmesini önler.

### Render Dashboard URL

Deploy sonrası, service'inizin URL'si şu formatta olacak: `https://instagram-reels-bot.onrender.com`. Bu URL'yi tarayıcınızda açarak botun çalışıp çalışmadığını kontrol edebilirsiniz.

### Log'lara Erişim

Render dashboard'unda service'inizi seçin ve "Logs" sekmesine tıklayın. Burada botun tüm log'larını görebilirsiniz. Hata ayıklama için bu log'lar çok faydalıdır.

### Yeni Sürüm Deploy Etme

Kodda bir değişiklik yaptığınızda, Render otomatik olarak GitHub'daki değişiklikleri algılar ve yeniden deploy eder. Manuel olarak deploy etmek için "Manual Deploy" butonuna tıklayıp "Deploy latest commit" seçebilirsiniz.

---

## Sorun Giderme

### "Instagram login failed" Hatası

Instagram hesap bilgilerinizin doğru olduğunu kontrol edin. Hesabınızda iki faktörlü doğrulama (2FA) açıksa kapatın. Instagram, sizi yeni bir cihazdan giriş yapmaya çalıştığınızda uyarabilir, bu durumda Instagram hesabınızdan giriş izni vermeniz gerekebilir.

### "Groq API Error" Hatası

Groq API anahtarınızın doğru olduğundan emin olun. console.groq.com adresinden anahtarınızı kontrol edin. Hesabınızın aktif olduğundan emin olun.

### Video Oluşturma Hatası

FFmpeg'in kurulu olduğundan emin olun. moviepy ve diğer bağımlılıkların doğru kurulduğunu log'lardan kontrol edin. Yeterli disk alanı olduğundan emin olun.

### Telegram Bot Yanıt Vermiyor

Render logs'larından botun çalışıp çalışmadığını kontrol edin. Service'in "Live" durumunda olduğundan emin olun. Telegram'da botu durdurup yeniden "/start" yazın.
