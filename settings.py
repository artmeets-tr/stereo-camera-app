#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import os

# Gerekli klasör yapısı
REQUIRED_DIRS = [
    'captures/left',
    'captures/right',
    'calibration',
    'aruco_markers',
    'aruco_detections'
]

# Kamera ayarları
CAMERA_SETTINGS = {
    'width': 640,
    'height': 480,
    'fps': 30,
    'left_id': 0,
    'right_id': 1,
    'exposure': -1,    # -1: Otomatik
    'gain': -1,        # -1: Otomatik
    'brightness': 50,
    'contrast': 50,
    'saturation': 50,
    'white_balance': -1, # -1: Otomatik
    'auto_focus': True
}

# Kalibrasyon ayarları
CALIBRATION_SETTINGS = {
    'board_size': (9, 6),     # Köşe sayısı (genişlik, yükseklik)
    'square_size': 25.0,      # Kare boyutu (mm)
    'min_captures': 20,       # Minimum görüntü sayısı
    'capture_delay': 2,       # Görüntü yakalama arasındaki gecikme (saniye)
    'calibration_file': 'calibration/stereo_calibration.pkl'
}

# ArUco Marker ayarları
ARUCO_SETTINGS = {
    'dictionary': cv2.aruco.DICT_4X4_50,
    'marker_size': 200,       # Piksel cinsinden
    'marker_length': 0.05,    # Metre cinsinden
    'output_dir': 'aruco_markers',
    'detection_dir': 'aruco_detections'
}

# ArUco Dictionary seçenekleri
ARUCO_DICT_OPTIONS = {
    'DICT_4X4_50': cv2.aruco.DICT_4X4_50,
    'DICT_4X4_100': cv2.aruco.DICT_4X4_100,
    'DICT_4X4_250': cv2.aruco.DICT_4X4_250,
    'DICT_4X4_1000': cv2.aruco.DICT_4X4_1000,
    'DICT_5X5_50': cv2.aruco.DICT_5X5_50,
    'DICT_5X5_100': cv2.aruco.DICT_5X5_100,
    'DICT_5X5_250': cv2.aruco.DICT_5X5_250,
    'DICT_5X5_1000': cv2.aruco.DICT_5X5_1000,
    'DICT_6X6_50': cv2.aruco.DICT_6X6_50,
    'DICT_6X6_100': cv2.aruco.DICT_6X6_100,
    'DICT_6X6_250': cv2.aruco.DICT_6X6_250,
    'DICT_6X6_1000': cv2.aruco.DICT_6X6_1000,
    'DICT_7X7_50': cv2.aruco.DICT_7X7_50,
    'DICT_7X7_100': cv2.aruco.DICT_7X7_100,
    'DICT_7X7_250': cv2.aruco.DICT_7X7_250,
    'DICT_7X7_1000': cv2.aruco.DICT_7X7_1000
}

# Çözünürlük seçenekleri
RESOLUTION_OPTIONS = [
    (640, 480),
    (800, 600),
    (1280, 720),
    (1920, 1080)
]

# FPS seçenekleri
FPS_OPTIONS = [15, 30, 60]

# Uygulama ayarları
APP_SETTINGS = {
    'window_title': 'Stereo Kamera Uygulaması',
    'window_width': 1280,
    'window_height': 720,
    'view_mode': 'side_by_side',  # 'side_by_side', 'left_only', 'right_only', 'overlay'
    'show_fps': True,
    'show_system_info': True,
    'capture_format': 'png',      # 'png', 'jpg'
    'capture_quality': 95,        # JPEG kalitesi (0-100)
    'auto_save_calibration': True,
    'auto_name_captures': True,
    'language': 'tr'
}

# GUI renkleri
GUI_COLORS = {
    'background': (240, 240, 240),
    'text': (10, 10, 10),
    'button': (220, 220, 220),
    'button_hover': (200, 200, 200),
    'button_active': (180, 180, 180),
    'highlight': (0, 120, 215),
    'error': (200, 0, 0),
    'success': (0, 180, 0),
    'warning': (255, 140, 0),
    'info': (0, 120, 215)
}

# Ayarları kaydet
def save_settings():
    """Tüm ayarları bir dosyaya kaydet"""
    settings = {
        'camera': CAMERA_SETTINGS,
        'calibration': CALIBRATION_SETTINGS,
        'aruco': ARUCO_SETTINGS,
        'app': APP_SETTINGS
    }
    
    settings_file = 'settings.pkl'
    
    import pickle
    with open(settings_file, 'wb') as f:
        pickle.dump(settings, f)
    
    print(f"Ayarlar {settings_file} dosyasına kaydedildi.")

# Ayarları yükle
def load_settings():
    """Kaydedilmiş ayarları yükle"""
    settings_file = 'settings.pkl'
    
    if not os.path.exists(settings_file):
        print("Ayar dosyası bulunamadı, varsayılan ayarlar kullanılıyor.")
        return False
    
    import pickle
    try:
        with open(settings_file, 'rb') as f:
            settings = pickle.load(f)
        
        # Ayarları güncelle
        CAMERA_SETTINGS.update(settings.get('camera', {}))
        CALIBRATION_SETTINGS.update(settings.get('calibration', {}))
        ARUCO_SETTINGS.update(settings.get('aruco', {}))
        APP_SETTINGS.update(settings.get('app', {}))
        
        print(f"Ayarlar {settings_file} dosyasından yüklendi.")
        return True
    except Exception as e:
        print(f"Ayarlar yüklenirken hata oluştu: {e}")
        return False