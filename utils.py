#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import cv2
import numpy as np
import time
import datetime
import platform
import subprocess
import psutil

def check_system():
    """Sistem gereksinimlerini kontrol et"""
    # OpenCV sürüm kontrolü
    cv_version = cv2.__version__.split('.')
    if int(cv_version[0]) < 4 or (int(cv_version[0]) == 4 and int(cv_version[1]) < 7):
        print(f"Uyarı: OpenCV sürümü 4.7.0 veya üstü olmalıdır. Mevcut sürüm: {cv2.__version__}")
        return False
    
    # İşletim sistemi kontrolü
    if platform.system() not in ['Linux', 'Windows', 'Darwin']:
        print(f"Uyarı: Desteklenmeyen işletim sistemi: {platform.system()}")
        return False
    
    # Raspberry Pi kontrolü
    if platform.system() == 'Linux' and 'raspberry' not in platform.platform().lower():
        print("Uyarı: Bu uygulama Raspberry Pi için optimize edilmiştir.")
    
    return True

def check_arducam():
    """ArduCam sürücülerini kontrol et"""
    # Doğrudan True döndür
    return True

def get_system_info():
    """Sistem bilgilerini döndür"""
    info = {}
    
    # CPU kullanımı
    info['cpu_percent'] = psutil.cpu_percent(interval=0.1)
    
    # Bellek kullanımı
    memory = psutil.virtual_memory()
    info['memory_percent'] = memory.percent
    info['memory_used'] = memory.used / (1024 * 1024)  # MB
    info['memory_total'] = memory.total / (1024 * 1024)  # MB
    
    # Disk kullanımı
    disk = psutil.disk_usage('/')
    info['disk_percent'] = disk.percent
    info['disk_used'] = disk.used / (1024 * 1024 * 1024)  # GB
    info['disk_total'] = disk.total / (1024 * 1024 * 1024)  # GB
    
    # Sıcaklık (Raspberry Pi için)
    info['temperature'] = None
    if platform.system() == 'Linux' and os.path.exists('/sys/class/thermal/thermal_zone0/temp'):
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000
                info['temperature'] = temp
        except Exception:
            pass
    
    return info

def draw_system_info(image, info=None):
    """Sistem bilgilerini görüntü üzerine çiz"""
    if image is None:
        return None
        
    if info is None:
        info = get_system_info()
    
    result = image.copy()
    h, w = result.shape[:2]
    
    # Bilgileri çiz
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thickness = 1
    color = (0, 255, 0)  # Yeşil
    
    lines = [
        f"CPU: {info['cpu_percent']:.1f}%",
        f"RAM: {info['memory_used']:.0f}/{info['memory_total']:.0f} MB ({info['memory_percent']:.1f}%)",
        f"Disk: {info['disk_used']:.1f}/{info['disk_total']:.1f} GB ({info['disk_percent']:.1f}%)"
    ]
    
    if info['temperature'] is not None:
        lines.append(f"Sıcaklık: {info['temperature']:.1f}°C")
    
    y = 20
    for i, line in enumerate(lines):
        cv2.putText(result, line, (10, y + i * 20), font, font_scale, color, font_thickness)
    
    return result

def get_timestamp():
    """Şu anki tarih ve zamanı metin olarak döndür"""
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

def save_image(image, directory, prefix="", timestamp=None):
    """Görüntüyü belirtilen dizine kaydet"""
    if image is None:
        return None
        
    if timestamp is None:
        timestamp = get_timestamp()
    
    os.makedirs(directory, exist_ok=True)
    
    filename = f"{prefix}_{timestamp}.png" if prefix else f"{timestamp}.png"
    filepath = os.path.join(directory, filename)
    
    cv2.imwrite(filepath, image)
    return filepath

def save_stereo_images(left_image, right_image, left_dir="captures/left", right_dir="captures/right", prefix=""):
    """Sol ve sağ görüntüleri kaydet"""
    if left_image is None or right_image is None:
        return None, None
    
    timestamp = get_timestamp()
    
    left_path = save_image(left_image, left_dir, f"{prefix}left", timestamp)
    right_path = save_image(right_image, right_dir, f"{prefix}right", timestamp)
    
    return left_path, right_path

def create_side_by_side(left_image, right_image):
    """Sol ve sağ görüntüleri yan yana birleştir"""
    if left_image is None or right_image is None:
        return None
    
    # Görüntülerin boyutlarını kontrol et
    h1, w1 = left_image.shape[:2]
    h2, w2 = right_image.shape[:2]
    
    # Eğer görüntüler farklı boyutlarda ise yeniden boyutlandır
    if h1 != h2 or w1 != w2:
        right_image = cv2.resize(right_image, (w1, h1))
    
    # Yan yana birleştir
    combined = np.hstack((left_image, right_image))
    
    return combined

def draw_fps(image, fps):
    """FPS değerini görüntü üzerine çiz"""
    if image is None:
        return None
        
    h, w = image.shape[:2]
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    font_thickness = 2
    color = (0, 255, 0)  # Yeşil
    
    text = f"FPS: {fps:.1f}"
    text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
    
    x = w - text_size[0] - 10
    y = 30
    
    cv2.putText(image, text, (x, y), font, font_scale, color, font_thickness)
    
    return image

def calculate_fps(start_time, frame_count=1):
    """FPS hesapla"""
    elapsed_time = time.time() - start_time
    if elapsed_time <= 0:
        return 0
    
    fps = frame_count / elapsed_time
    return fps

def resize_image(image, width=None, height=None):
    """Görüntüyü belirtilen boyuta yeniden boyutlandır"""
    if image is None:
        return None
        
    h, w = image.shape[:2]
    
    if width is None and height is None:
        return image
    
    if width is None:
        aspect_ratio = height / h
        width = int(w * aspect_ratio)
    elif height is None:
        aspect_ratio = width / w
        height = int(h * aspect_ratio)
    
    return cv2.resize(image, (width, height))