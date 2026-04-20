#!/bin/bash

# Instagram Reels Bot - Build Script
# Bu script Render'da build sürecini yönetir

set -e  # Hata durumunda script'i durdur

echo "=========================================="
echo "Instagram Reels Bot - Build Script"
echo "=========================================="
echo ""

# Sistem paketlerini güncelle
echo "[1/4] Sistem paketleri güncelleniyor..."
apt-get update -qq || { echo "apt-get update başarısız!"; exit 1; }

# Gerekli sistem paketlerini kur
echo "[2/4] Gerekli sistem paketleri kuruluyor..."
apt-get install -y --no-install-recommends \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    ffmpeg \
    libmagickwand-dev \
    || { echo "Sistem paketleri kurulumu başarısız!"; exit 2; }

# Python paketlerini kur
echo "[3/4] Python bağımlılıkları kuruluyor..."
pip install --no-cache-dir -r requirements.txt || { echo "Python paketleri kurulumu başarısız!"; exit 3; }

echo "[4/4] Build tamamlandı!"
echo "=========================================="
echo "Build başarılı! Uygulama başlatılabilir."
echo "=========================================="
