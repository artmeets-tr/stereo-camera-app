#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import time
import threading
import os
import sys

# ArduCam SDK desteği (opsiyonel)
ARDUCAM_AVAILABLE = False
try:
    import arducam_mipicamera as arducam
    ARDUCAM_AVAILABLE = True
except ImportError:
    print("ArduCam SDK bulunamadı. OpenCV tabanlı kamera desteği kullanılacak.")

class CameraController:
    def __init__(self):
        self.left_camera = None
        self.right_camera = None
        self.is_running = False
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 30
        self.capture_thread = None
        self.lock = threading.Lock()
        self.last_frame_left = None
        self.last_frame_right = None
        
    def init_cameras(self, left_id=0, right_id=1):
        """Kamera sistemini başlat (ArduCam veya standart OpenCV)"""
        
        # ArduCam SDK mevcut ise onu kullan
        if ARDUCAM_AVAILABLE:
            try:
                print("ArduCam kameraları başlatılıyor...")
                return self._init_arducam_cameras()
            except Exception as e:
                print(f"ArduCam kamera başlatma hatası: {e}")
                print("Standart OpenCV kamera desteğine geçiliyor...")
        
        # ArduCam yoksa veya başlatma hatası varsa OpenCV kullan
        return self._init_opencv_cameras(left_id, right_id)
    
    def _init_arducam_cameras(self):
        """ArduCam kameralarını başlat"""
        try:
            print("Sol ArduCam kamera bağlanıyor...")
            self.left_camera = arducam.mipi_camera()
            self.left_camera.init_camera()
            
            print("Sağ ArduCam kamera bağlanıyor...")
            self.right_camera = arducam.mipi_camera(1)  # İkinci kamera 
            self.right_camera.init_camera()
            
            # Ayarlar
            for camera in [self.left_camera, self.right_camera]:
                camera.set_mode(0)  # Siyah-beyaz mod
                camera.set_resolution(self.frame_width, self.frame_height)
                camera.set_control(arducam.v4l2.V4L2_CID_FRAME_RATE, self.fps)
            
            print("ArduCam kameralar başarıyla başlatıldı.")
            return True
        except Exception as e:
            print(f"ArduCam kamera başlatma hatası: {e}")
            if hasattr(self, 'left_camera') and self.left_camera:
                self.left_camera.close_camera()
                self.left_camera = None
            if hasattr(self, 'right_camera') and self.right_camera:
                self.right_camera.close_camera()
                self.right_camera = None
            return False
    
    def _init_opencv_cameras(self, left_id=0, right_id=1):
        """Standart OpenCV kameralarını başlat"""
        try:
            # Önce tek kamera ile deneme yapalım
            self.left_camera = cv2.VideoCapture(left_id)
            
            # İlk kamera açılabildiyse, sağ kamerayı deneyelim
            if self.left_camera.isOpened():
                print("Sol kamera başarıyla başlatıldı.")
                # Kamera ayarlarını yap
                self.left_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.left_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
                self.left_camera.set(cv2.CAP_PROP_FPS, self.fps)
                
                try:
                    self.right_camera = cv2.VideoCapture(right_id)
                    if self.right_camera.isOpened():
                        # Kamera ayarlarını yap
                        self.right_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                        self.right_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
                        self.right_camera.set(cv2.CAP_PROP_FPS, self.fps)
                        print("Sağ kamera başarıyla başlatıldı.")
                    else:
                        print("Sağ kamera başlatılamadı, test moduna geçiliyor.")
                        # Sahte sağ kamera oluşturalım
                        self.right_camera = None
                except Exception as e:
                    print(f"Sağ kamera başlatma hatası: {e}")
                    self.right_camera = None
            else:
                print("Sol kamera başlatılamadı!")
                # Demo modu için sahte kamera oluştur
                self.left_camera = None
                self.right_camera = None
                print("Demo modu etkinleştiriliyor (kamerasız çalışma).")
                
            print("Kamera ayarları yapılandırıldı.")
            return True
        except Exception as e:
            print(f"Kamera başlatma hatası: {e}")
            return False
    
    def _capture_thread_function(self):
        """Arka planda sürekli kameralardan görüntü yakala"""
        while self.is_running:
            if ARDUCAM_AVAILABLE and isinstance(self.left_camera, arducam.mipi_camera):
                self._capture_arducam_frames()
            else:
                self._capture_opencv_frames()
            
            time.sleep(1.0 / self.fps)  # FPS değerine göre bekle
    
    def _capture_arducam_frames(self):
        """ArduCam kameralarından görüntü yakala"""
        try:
            if self.left_camera:
                # Sol kameradan görüntü al
                frame = self.left_camera.capture(arducam.FORMAT_GRAY, 1)
                frame_buffer = frame.as_array
                left_frame = cv2.imdecode(frame_buffer, cv2.IMREAD_GRAYSCALE)
                # Renkli görüntüye dönüştür
                left_frame = cv2.cvtColor(left_frame, cv2.COLOR_GRAY2BGR)
            else:
                left_frame = self._create_dummy_frame("Sol Kamera Yok")
            
            if self.right_camera:
                # Sağ kameradan görüntü al
                frame = self.right_camera.capture(arducam.FORMAT_GRAY, 1)
                frame_buffer = frame.as_array
                right_frame = cv2.imdecode(frame_buffer, cv2.IMREAD_GRAYSCALE)
                # Renkli görüntüye dönüştür
                right_frame = cv2.cvtColor(right_frame, cv2.COLOR_GRAY2BGR)
            else:
                right_frame = self._create_dummy_frame("Sağ Kamera Yok")
            
            with self.lock:
                self.last_frame_left = left_frame
                self.last_frame_right = right_frame
        except Exception as e:
            print(f"ArduCam görüntü yakalama hatası: {e}")
    
    def _capture_opencv_frames(self):
        """OpenCV kameralarından görüntü yakala"""
        try:
            if self.left_camera is not None and self.left_camera.isOpened():
                ret_left, left_frame = self.left_camera.read()
                if not ret_left:
                    left_frame = self._create_dummy_frame("Sol Kamera Hatası")
            else:
                left_frame = self._create_dummy_frame("Sol Kamera Yok")
            
            if self.right_camera is not None and self.right_camera.isOpened():
                ret_right, right_frame = self.right_camera.read()
                if not ret_right:
                    right_frame = self._create_dummy_frame("Sağ Kamera Hatası")
            else:
                right_frame = self._create_dummy_frame("Sağ Kamera Yok")
            
            with self.lock:
                self.last_frame_left = left_frame
                self.last_frame_right = right_frame
        except Exception as e:
            print(f"OpenCV görüntü yakalama hatası: {e}")
    
    def _create_dummy_frame(self, message):
        """Test modu için sahte kare oluştur"""
        dummy_frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        # Mesaj metnini ekranın ortasına yerleştir
        text_size = cv2.getTextSize(message, font, 1, 2)[0]
        text_x = (self.frame_width - text_size[0]) // 2
        text_y = (self.frame_height + text_size[1]) // 2
        cv2.putText(dummy_frame, message, (text_x, text_y), font, 1, (255, 255, 255), 2)
        
        # Çerçeveye bir grid ekle (demo görsel ilgi için)
        for x in range(0, self.frame_width, 50):
            cv2.line(dummy_frame, (x, 0), (x, self.frame_height), (50, 50, 50), 1)
        for y in range(0, self.frame_height, 50):
            cv2.line(dummy_frame, (0, y), (self.frame_width, y), (50, 50, 50), 1)
            
        return dummy_frame
    
    def get_stereo_frame(self):
        """Sol ve sağ kameralardan son görüntüleri getir"""
        if not self.is_running:
            if ARDUCAM_AVAILABLE and isinstance(self.left_camera, arducam.mipi_camera):
                return self._get_arducam_frames()
            else:
                return self._get_opencv_frames()
        else:
            # Thread çalışıyorsa son kaydedilen frame'leri döndür
            with self.lock:
                if self.last_frame_left is None or self.last_frame_right is None:
                    left_frame = self._create_dummy_frame("Sol Görüntü Yok")
                    right_frame = self._create_dummy_frame("Sağ Görüntü Yok")
                    return left_frame, right_frame
                
                return self.last_frame_left.copy(), self.last_frame_right.copy()
    
    def _get_arducam_frames(self):
        """ArduCam kameralarından anlık görüntü al"""
        try:
            if self.left_camera:
                frame = self.left_camera.capture(arducam.FORMAT_GRAY, 1)
                frame_buffer = frame.as_array
                left_frame = cv2.imdecode(frame_buffer, cv2.IMREAD_GRAYSCALE)
                left_frame = cv2.cvtColor(left_frame, cv2.COLOR_GRAY2BGR)
            else:
                left_frame = self._create_dummy_frame("Sol Kamera Yok")
            
            if self.right_camera:
                frame = self.right_camera.capture(arducam.FORMAT_GRAY, 1)
                frame_buffer = frame.as_array
                right_frame = cv2.imdecode(frame_buffer, cv2.IMREAD_GRAYSCALE)
                right_frame = cv2.cvtColor(right_frame, cv2.COLOR_GRAY2BGR)
            else:
                right_frame = self._create_dummy_frame("Sağ Kamera Yok")
            
            return left_frame, right_frame
        except Exception as e:
            print(f"ArduCam görüntü yakalama hatası: {e}")
            return self._create_dummy_frame("Kamera Hatası"), self._create_dummy_frame("Kamera Hatası")
    
    def _get_opencv_frames(self):
        """OpenCV kameralarından anlık görüntü al"""
        # Kameralar yoksa veya açılamadıysa sahte görüntü üret
        if self.left_camera is None or not self.left_camera.isOpened():
            left_frame = self._create_dummy_frame("Sol Kamera Yok")
        else:
            ret_left, left_frame = self.left_camera.read()
            if not ret_left:
                left_frame = self._create_dummy_frame("Sol Kamera Hatası")
        
        if self.right_camera is None or not self.right_camera.isOpened():
            right_frame = self._create_dummy_frame("Sağ Kamera Yok") 
        else:
            ret_right, right_frame = self.right_camera.read()
            if not ret_right:
                right_frame = self._create_dummy_frame("Sağ Kamera Hatası")
        
        return left_frame, right_frame
    
    def start_capture(self):
        """Sürekli görüntü yakalama modunu başlat"""
        if self.is_running:
            return True
        
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_thread_function)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        print("Kamera yakalama başlatıldı.")
        return True
    
    def stop_capture(self):
        """Sürekli görüntü yakalama modunu durdur"""
        self.is_running = False
        if self.capture_thread is not None:
            self.capture_thread.join(timeout=1.0)
            self.capture_thread = None
        print("Kamera yakalama durduruldu.")
    
    def release(self):
        """Kamera kaynaklarını serbest bırak"""
        self.stop_capture()
        
        if ARDUCAM_AVAILABLE:
            if hasattr(self, 'left_camera') and self.left_camera:
                if isinstance(self.left_camera, arducam.mipi_camera):
                    self.left_camera.close_camera()
                else:
                    self.left_camera.release()
                self.left_camera = None
            
            if hasattr(self, 'right_camera') and self.right_camera:
                if isinstance(self.right_camera, arducam.mipi_camera):
                    self.right_camera.close_camera()
                else:
                    self.right_camera.release()
                self.right_camera = None
        else:
            if self.left_camera is not None:
                self.left_camera.release()
                self.left_camera = None
            
            if self.right_camera is not None:
                self.right_camera.release()
                self.right_camera = None
        
        print("Kameralar kapatıldı.")