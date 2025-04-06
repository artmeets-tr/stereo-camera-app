#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import time
import threading
import os
from camera import CameraController
from calibration import StereoCalibration
from aruco_detector import ArucoDetector
import settings
import utils

class GUI:
    def __init__(self):
        self.window_title = settings.APP_SETTINGS['window_title']
        self.window_width = settings.APP_SETTINGS['window_width']
        self.window_height = settings.APP_SETTINGS['window_height']
        
        # Ana pencereyi oluştur
        cv2.namedWindow(self.window_title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_title, self.window_width, self.window_height)
        
        # Kamera, kalibrasyon ve ArUco kontrolcüleri
        self.camera = CameraController()
        self.calibration = StereoCalibration()
        self.aruco = ArucoDetector(settings.ARUCO_SETTINGS['dictionary'])
        
        # Uygulama durumu
        self.running = False
        self.view_mode = settings.APP_SETTINGS['view_mode']
        self.show_fps = settings.APP_SETTINGS['show_fps']
        self.show_system_info = settings.APP_SETTINGS['show_system_info']
        
        # FPS hesaplama için değişkenler
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        self.fps_update_interval = 1.0  # saniye
        
        # Kalibrasyon durumu
        self.calibration_images_left = []
        self.calibration_images_right = []
        self.calibration_in_progress = False
        
        # ArUco tespit durumu
        self.aruco_detection_enabled = False
        
        print("GUI başlatıldı.")
    
    def init_camera(self):
        """Kameraları başlat"""
        camera_settings = settings.CAMERA_SETTINGS
        
        # Kamera parametrelerini ayarla
        self.camera.frame_width = camera_settings['width']
        self.camera.frame_height = camera_settings['height']
        self.camera.fps = camera_settings['fps']
        
        # Kameraları başlat
        if not self.camera.init_cameras(camera_settings['left_id'], camera_settings['right_id']):
            print("Kameralar başlatılamadı!")
            return False
        
        # Kamera yakalamayı başlat
        if not self.camera.start_capture():
            print("Kamera yakalama başlatılamadı!")
            return False
        
        return True
    
    def load_calibration(self):
        """Kalibrasyon verilerini yükle"""
        calibration_file = settings.CALIBRATION_SETTINGS['calibration_file']
        if os.path.exists(calibration_file):
            if self.calibration.load_calibration(calibration_file):
                print("Kalibrasyon verileri yüklendi.")
                return True
        
        print("Kalibrasyon verileri yüklenemedi. Lütfen önce kalibrasyon yapın.")
        return False
    
    def capture_calibration_image(self):
        """Kalibrasyon için görüntü yakala"""
        if not self.calibration_in_progress:
            return False
        
        # Stereo görüntü al
        left_frame, right_frame = self.camera.get_stereo_frame()
        
        if left_frame is None or right_frame is None:
            print("Görüntü alınamadı!")
            return False
        
        # Görüntüleri listeye ekle
        self.calibration_images_left.append(left_frame.copy())
        self.calibration_images_right.append(right_frame.copy())
        
        # Görüntüleri kaydet
        timestamp = utils.get_timestamp()
        utils.save_image(left_frame, "calibration", f"calib_left_{len(self.calibration_images_left)}", timestamp)
        utils.save_image(right_frame, "calibration", f"calib_right_{len(self.calibration_images_right)}", timestamp)
        
        print(f"Kalibrasyon görüntüsü yakalandı: {len(self.calibration_images_left)}")
        return True
    
    def start_calibration(self):
        """Kalibrasyon işlemini başlat"""
        self.calibration_images_left = []
        self.calibration_images_right = []
        self.calibration_in_progress = True
        print("Kalibrasyon başlatıldı. Lütfen dama tahtasını farklı açılardan gösterin.")
        return True
    
    def perform_calibration(self):
        """Kalibrasyon işlemini gerçekleştir"""
        if len(self.calibration_images_left) < settings.CALIBRATION_SETTINGS['min_captures']:
            print(f"Kalibrasyon için en az {settings.CALIBRATION_SETTINGS['min_captures']} görüntü gerekli!")
            return False
        
        print("Kalibrasyon hesaplanıyor...")
        board_size = settings.CALIBRATION_SETTINGS['board_size']
        square_size = settings.CALIBRATION_SETTINGS['square_size']
        
        if self.calibration.calibrate(self.calibration_images_left, self.calibration_images_right, board_size, square_size):
            print("Kalibrasyon başarılı!")
            
            # Otomatik kaydet
            if settings.APP_SETTINGS['auto_save_calibration']:
                self.calibration.save_calibration()
            
            self.calibration_in_progress = False
            return True
        else:
            print("Kalibrasyon başarısız!")
            return False
    
    def stop_calibration(self):
        """Kalibrasyon işlemini durdur"""
        self.calibration_in_progress = False
        print("Kalibrasyon durduruldu.")
        return True
    
    def enable_aruco_detection(self, enable=True):
        """ArUco marker tespitini etkinleştir/devre dışı bırak"""
        self.aruco_detection_enabled = enable
        return True
    
    def create_aruco_marker(self, marker_id, size=None):
        """ArUco marker oluştur"""
        if size is None:
            size = settings.ARUCO_SETTINGS['marker_size']
        
        output_file = os.path.join(settings.ARUCO_SETTINGS['output_dir'], f"marker_{marker_id}.png")
        self.aruco.create_marker(marker_id, size, output_file)
        print(f"ArUco marker oluşturuldu: {output_file}")
        return True
    
    def create_aruco_marker_set(self, start_id, count, size=None):
        """ArUco marker seti oluştur"""
        if size is None:
            size = settings.ARUCO_SETTINGS['marker_size']
        
        self.aruco.create_marker_set(start_id, count, size, settings.ARUCO_SETTINGS['output_dir'])
        return True
    
    def process_frame(self):
        """Kameradan gelen görüntüleri işle"""
        # Stereo görüntü al
        left_frame, right_frame = self.camera.get_stereo_frame()
        
        if left_frame is None or right_frame is None:
            print("Görüntü alınamadı!")
            return None
        
        # Eğer kalibrasyon yapıldıysa, görüntüleri rektifiye et
        if self.calibration.calibrated:
            left_frame, right_frame = self.calibration.rectify_images(left_frame, right_frame)
        
        # ArUco tespit etkinse
        if self.aruco_detection_enabled and self.calibration.calibrated:
            # Sol görüntüdeki markerları tespit et
            left_frame, corners_left, ids_left, distances_left = self.aruco.detect_and_draw(
                left_frame, 
                self.calibration.camera_matrix_left, 
                self.calibration.dist_coeffs_left,
                True,  # Eksen çiz
                settings.ARUCO_SETTINGS['marker_length']
            )
            
            # Sağ görüntüdeki markerları tespit et
            right_frame, corners_right, ids_right, distances_right = self.aruco.detect_and_draw(
                right_frame, 
                self.calibration.camera_matrix_right, 
                self.calibration.dist_coeffs_right,
                True,  # Eksen çiz
                settings.ARUCO_SETTINGS['marker_length']
            )
        
        # Görüntüleri birleştir
        if self.view_mode == 'side_by_side':
            result = utils.create_side_by_side(left_frame, right_frame)
        elif self.view_mode == 'left_only':
            result = left_frame
        elif self.view_mode == 'right_only':
            result = right_frame
        else:
            result = utils.create_side_by_side(left_frame, right_frame)
        
        # FPS ve sistem bilgilerini ekle
        if self.show_fps:
            result = utils.draw_fps(result, self.fps)
        
        if self.show_system_info:
            result = utils.draw_system_info(result)
        
        return result
    
    def run(self):
        """Ana döngü"""
        if not self.init_camera():
            print("Kamera başlatılamadı! Çıkılıyor...")
            return
        
        self.running = True
        self.start_time = time.time()
        
        try:
            while self.running:
                # Görüntüyü işle
                frame = self.process_frame()
                
                if frame is not None:
                    # Görüntüyü göster
                    cv2.imshow(self.window_title, frame)
                
                # FPS hesapla
                self.frame_count += 1
                elapsed_time = time.time() - self.start_time
                
                if elapsed_time > self.fps_update_interval:
                    self.fps = self.frame_count / elapsed_time
                    self.frame_count = 0
                    self.start_time = time.time()
                
                # Klavye girdisini kontrol et
                key = cv2.waitKey(1) & 0xFF
                
                # ESC veya q tuşu ile çık
                if key == 27 or key == ord('q'):
                    self.running = False
                    break
                
                # Space tuşu ile görüntü yakala
                elif key == 32:  # Space
                    if self.calibration_in_progress:
                        self.capture_calibration_image()
                    else:
                        left_frame, right_frame = self.camera.get_stereo_frame()
                        utils.save_stereo_images(left_frame, right_frame)
                        print("Görüntüler kaydedildi.")
                
                # c tuşu ile kalibrasyon başlat/durdur
                elif key == ord('c'):
                    if self.calibration_in_progress:
                        self.stop_calibration()
                    else:
                        self.start_calibration()
                
                # Enter tuşu ile kalibrasyonu hesapla
                elif key == 13:  # Enter
                    if self.calibration_in_progress:
                        self.perform_calibration()
                
                # a tuşu ile ArUco tespitini aç/kapat
                elif key == ord('a'):
                    self.aruco_detection_enabled = not self.aruco_detection_enabled
                    print(f"ArUco tespit: {'Açık' if self.aruco_detection_enabled else 'Kapalı'}")
                
                # m tuşu ile görüntüleme modunu değiştir
                elif key == ord('m'):
                    modes = ['side_by_side', 'left_only', 'right_only']
                    current_index = modes.index(self.view_mode)
                    self.view_mode = modes[(current_index + 1) % len(modes)]
                    print(f"Görüntüleme modu: {self.view_mode}")
                
                # f tuşu ile FPS gösterimini aç/kapat
                elif key == ord('f'):
                    self.show_fps = not self.show_fps
                    print(f"FPS gösterimi: {'Açık' if self.show_fps else 'Kapalı'}")
                
                # i tuşu ile sistem bilgisi gösterimini aç/kapat
                elif key == ord('i'):
                    self.show_system_info = not self.show_system_info
                    print(f"Sistem bilgisi gösterimi: {'Açık' if self.show_system_info else 'Kapalı'}")
        
        finally:
            # Temizlik
            self.camera.stop_capture()
            self.camera.release()
            cv2.destroyAllWindows()
            print("Uygulama kapatıldı.")