#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Stereo Kamera Uygulaması - Basit Test Programı
ArduCam SDK veya kamera olmadan da çalışabilir
"""

import cv2
import numpy as np
import time
import os

def main():
    """Basit kamera testi"""
    print("Stereo Kamera Test Uygulaması")
    print("-----------------------------")
    
    # Kamera nesnesi
    cap = None
    dummy_mode = False
    
    try:
        # Kamerayı başlat
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Kamera bulunamadı! Demo modunda çalışılıyor.")
            dummy_mode = True
        else:
            print("Kamera başarıyla başlatıldı.")
            
            # Kamera özelliklerini ayarla
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Kamera özelliklerini göster
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            print(f"Kamera çözünürlüğü: {width}x{height}")
            print(f"Kamera FPS: {fps}")
        
        print("\nÇıkmak için 'q' tuşuna basın")
        print("Görüntü kaydetmek için 'space' tuşuna basın\n")
        
        # Görüntü dışarı aktarma için klasör
        os.makedirs("test_captures", exist_ok=True)
        
        # Ana döngü
        last_time = time.time()
        frame_count = 0
        
        while True:
            # Görüntü al veya sahte görüntü oluştur
            if dummy_mode:
                frame = create_dummy_frame(640, 480, f"Demo Modu - FPS: {calculate_fps(last_time, frame_count):.1f}")
            else:
                ret, frame = cap.read()
                if not ret:
                    print("Görüntü alınamadı!")
                    break
            
            # FPS hesapla
            frame_count += 1
            if frame_count % 10 == 0:
                fps = calculate_fps(last_time, frame_count)
                last_time = time.time()
                frame_count = 0
                
                # FPS göster
                if not dummy_mode:
                    frame = draw_text(frame, f"FPS: {fps:.1f}", pos=(10, 30))
            
            # Görüntüyü göster
            cv2.imshow("Kamera Test", frame)
            
            # Tuş kontrolü
            key = cv2.waitKey(1) & 0xFF
            
            # Çıkış için q tuşu
            if key == ord('q'):
                break
                
            # Görüntü kaydetmek için space tuşu
            elif key == 32:  # Space
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"test_captures/capture_{timestamp}.png"
                cv2.imwrite(filename, frame)
                print(f"Görüntü kaydedildi: {filename}")
                
    finally:
        # Temizlik
        if cap and not dummy_mode:
            cap.release()
        cv2.destroyAllWindows()
        print("Test uygulaması kapatıldı.")

def create_dummy_frame(width, height, message="Test Modu"):
    """Demo modu için sahte çerçeve oluştur"""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Animasyon için zaman
    t = time.time() * 2
    
    # Hareketli arka plan
    for y in range(0, height, 10):
        color_val = int(127 + 127 * np.sin(y / 30 + t))
        cv2.line(frame, (0, y), (width, y), (0, 0, color_val), 1)
    
    for x in range(0, width, 10):
        color_val = int(127 + 127 * np.sin(x / 30 + t))
        cv2.line(frame, (x, 0), (x, height), (0, color_val, 0), 1)
    
    # Şekiller
    radius = int(50 + 20 * np.sin(t))
    center_x = int(width/2 + 100 * np.sin(t/2))
    center_y = int(height/2 + 50 * np.cos(t/3))
    
    cv2.circle(frame, (center_x, center_y), radius, (0, 255, 255), -1)
    cv2.rectangle(frame, (int(width/4), int(height/4)), 
                 (int(width/4 + 100), int(height/4 + 100)), 
                 (255, 0, 0), -1)
    
    # Metin
    return draw_text(frame, message, (int(width/2 - 100), height - 50))

def draw_text(frame, text, pos=(10, 30), scale=1.0):
    """Görüntü üzerine metin çiz"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, text, pos, font, scale, (255, 255, 255), 2)
    return frame

def calculate_fps(start_time, frame_count):
    """FPS hesapla"""
    elapsed_time = time.time() - start_time
    if elapsed_time <= 0:
        return 0
    return frame_count / elapsed_time

if __name__ == "__main__":
    main()