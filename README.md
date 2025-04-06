# Stereo Kamera Uygulaması

Raspberry Pi 5 için geliştirilmiş stereo kamera kalibrasyon ve ArUco marker tespit uygulaması.

## Özellikler

- İki kamerayı eşzamanlı kontrol
- Dama tahtası ile stereo kalibrasyon
- ArUco marker oluşturma ve tespit
- Kamera ayarlarını yapılandırma
- Stereo görüntüleri yakalama ve kaydetme
- Sistem durumu izleme (CPU, bellek, sıcaklık)
- Kullanıcı dostu arayüz

## Raspberry Pi Kurulum

### 1. Repository'yi Klonlayın

```bash
git clone https://github.com/artmeets-tr/stereo-camera-app.git
cd stereo-camera-app
```

### 2. ArduCam SDK'yı Yükleyin

```bash
# ArduCam SDK kurulumu
wget -O install_pivariety_pkgs.sh https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver/releases/download/install_script/install_pivariety_pkgs.sh
chmod +x install_pivariety_pkgs.sh
./install_pivariety_pkgs.sh -p libcamera_dev
./install_pivariety_pkgs.sh -p libcamera_apps
```

Kamera modelinize özel sürücüleri yükleyin:
```bash
# Kamera modeline göre uygun sürücüyü seçin
./install_pivariety_pkgs.sh -p kernel_driver
```

### 3. Python Virtual Environment Oluşturun

```bash
sudo apt install python3-venv python3-full
python3 -m venv ~/stereo_env
source ~/stereo_env/bin/activate
```

### 4. Gerekli Paketleri Yükleyin

```bash
pip install -r requirements.txt
```

### 5. Uygulamayı Çalıştırın

```bash
python main.py
```

## Kullanım

### Ana Menü

Ana menüde üç ana bölüm bulunur:
- Kalibrasyon
- ArUco Tespit
- Ayarlar

### Kalibrasyon

1. Kamera ayarlarını yapılandırın (çözünürlük, FPS)
2. Kalibrasyon ayarlarını belirleyin (dama tahtası boyutu, kare boyutu)
3. "Kalibrasyonu Başlat" tuşuna basın
4. Dama tahtasını kameralardan görünecek şekilde farklı pozisyonlarda tutun
5. Yeterli sayıda kare yakalandığında kalibrasyon otomatik hesaplanır
6. "Kalibrasyonu Test Et" tuşuna basarak sonucu kontrol edin

### ArUco Tespit

1. ArUco sözlüğünü seçin ve ayarları uygulayın
2. "Marker Oluştur" tuşuna basarak tekil ArUco marker oluşturun
3. "Marker Seti Oluştur" tuşuna basarak marker takımı oluşturun
4. "Tespiti Başlat" tuşuna basın
5. Markerları kameralara gösterin
6. "Görüntü Yakala" tuşuna basarak tespitleri kaydedin

## Sorun Giderme

1. **Kamera Bağlantı Hatası**
   - Kameraların doğru bağlandığından emin olun
   - ArduCam SDK'nın düzgün kurulduğunu kontrol edin
   - `libcamera-hello` komutu ile kameraları test edin

2. **Uygulama Çalışmazsa**
   - Python sanal ortamınızın aktif olduğundan emin olun (`source ~/stereo_env/bin/activate`)
   - Gerekli tüm paketlerin kurulduğunu kontrol edin
   - Uygulamayı `python -v main.py` ile detaylı hata mesajları alarak çalıştırın

## Lisans

MIT Lisansı