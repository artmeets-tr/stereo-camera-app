#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import time
import threading

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
        try:
            self.left_camera = cv2.VideoCapture(left_id)
            self.right_camera = cv2.VideoCapture(right_id)
            
            # Kamera ayarlarını yap
            self.left_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.left_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.left_camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            self.right_camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.right_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.right_camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Kameraların açık olup olmadığını kontrol et
            if not self.left_camera.isOpened() or not self.right_camera.isOpened():
                print("Kameralar açılamadı!")
                return False
                
            print("Kameralar başarıyla başlatıldı.")
            return True
        except Exception as e:
            print(f"Kamera başlatma hatası: {e}")
            return False
    
    def _capture_thread_function(self):
        while self.is_running:
            if self.left_camera is None or self.right_camera is None:
                time.sleep(0.1)
                continue
                
            ret_left, frame_left = self.left_camera.read()
            ret_right, frame_right = self.right_camera.read()
            
            if ret_left and ret_right:
                with self.lock:
                    self.last_frame_left = frame_left
                    self.last_frame_right = frame_right
            
            time.sleep(1.0 / self.fps)  # FPS değerine göre bekle
    
    def get_stereo_frame(self):
        if not self.is_running:
            if self.left_camera is None or self.right_camera is None:
                return np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8), \
                       np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
            
            # Eğer thread çalışmıyorsa doğrudan kameralardan görüntü al
            ret_left, frame_left = self.left_camera.read()
            ret_right, frame_right = self.right_camera.read()
            
            if not ret_left or not ret_right:
                return np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8), \
                       np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
            
            return frame_left, frame_right
        else:
            # Thread çalışıyorsa son kaydedilen frame'leri döndür
            with self.lock:
                if self.last_frame_left is None or self.last_frame_right is None:
                    return np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8), \
                           np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
                
                return self.last_frame_left.copy(), self.last_frame_right.copy()
    
    def start_capture(self):
        if self.left_camera is None or self.right_camera is None:
            return False
        
        if not self.is_running:
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._capture_thread_function)
            self.capture_thread.daemon = True
            self.capture_thread.start()
        
        return True
    
    def stop_capture(self):
        self.is_running = False
        if self.capture_thread is not None:
            self.capture_thread.join(timeout=1.0)
            self.capture_thread = None
    
    def release(self):
        self.stop_capture()
        
        if self.left_camera is not None:
            self.left_camera.release()
        
        if self.right_camera is not None:
            self.right_camera.release()
        
        self.left_camera = None
        self.right_camera = None
        print("Kameralar kapatıldı.")