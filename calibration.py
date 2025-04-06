#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import os
import pickle

class StereoCalibration:
    def __init__(self):
        self.calibrated = False
        self.camera_matrix_left = None
        self.dist_coeffs_left = None
        self.camera_matrix_right = None
        self.dist_coeffs_right = None
        self.R = None  # Rotasyon matrisi
        self.T = None  # Translasyon vektörü
        self.E = None  # Essential matrix
        self.F = None  # Fundamental matrix
        self.img_size = None
        self.rect_map_left = None
        self.rect_map_right = None
        
    def calibrate(self, images_left, images_right, board_size=(9, 6), square_size=25.0):
        """Stereo kamera kalibrasyonu"""
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        
        # Satranç tahtası köşe noktaları için dünya koordinatları
        objp = np.zeros((board_size[0] * board_size[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:board_size[0], 0:board_size[1]].T.reshape(-1, 2) * square_size
        
        # Her iki kamera için köşe noktalarını ve obje noktalarını sakla
        objpoints = []
        imgpoints_left = []
        imgpoints_right = []
        
        for img_left, img_right in zip(images_left, images_right):
            gray_left = cv2.cvtColor(img_left, cv2.COLOR_BGR2GRAY)
            gray_right = cv2.cvtColor(img_right, cv2.COLOR_BGR2GRAY)
            
            self.img_size = gray_left.shape[::-1]
            
            # Her iki görüntüde de köşeleri bul
            ret_left, corners_left = cv2.findChessboardCorners(gray_left, board_size, None)
            ret_right, corners_right = cv2.findChessboardCorners(gray_right, board_size, None)
            
            # Eğer her iki görüntüde de köşeler bulunduysa
            if ret_left and ret_right:
                # Alt piksel doğruluk için köşeleri iyileştir
                corners_left_refined = cv2.cornerSubPix(gray_left, corners_left, (11, 11), (-1, -1), criteria)
                corners_right_refined = cv2.cornerSubPix(gray_right, corners_right, (11, 11), (-1, -1), criteria)
                
                objpoints.append(objp)
                imgpoints_left.append(corners_left_refined)
                imgpoints_right.append(corners_right_refined)
        
        if not objpoints:
            print("Kalibrasyon için yeterli veri bulunamadı!")
            return False
        
        # Her kamera için ayrı ayrı kalibrasyon yap
        ret_left, self.camera_matrix_left, self.dist_coeffs_left, rvecs_left, tvecs_left = cv2.calibrateCamera(
            objpoints, imgpoints_left, self.img_size, None, None)
        
        ret_right, self.camera_matrix_right, self.dist_coeffs_right, rvecs_right, tvecs_right = cv2.calibrateCamera(
            objpoints, imgpoints_right, self.img_size, None, None)
        
        # Stereo kalibrasyon
        retval, self.camera_matrix_left, self.dist_coeffs_left, self.camera_matrix_right, self.dist_coeffs_right, \
        self.R, self.T, self.E, self.F = cv2.stereoCalibrate(
            objpoints, imgpoints_left, imgpoints_right,
            self.camera_matrix_left, self.dist_coeffs_left,
            self.camera_matrix_right, self.dist_coeffs_right,
            self.img_size, None, None, None, None,
            cv2.CALIB_FIX_INTRINSIC, criteria)
        
        # Stereo rektifikasyon
        R1, R2, P1, P2, Q, roi_left, roi_right = cv2.stereoRectify(
            self.camera_matrix_left, self.dist_coeffs_left,
            self.camera_matrix_right, self.dist_coeffs_right,
            self.img_size, self.R, self.T,
            flags=cv2.CALIB_ZERO_DISPARITY, alpha=0.9)
        
        # Rektifikasyon haritaları
        self.rect_map_left = cv2.initUndistortRectifyMap(
            self.camera_matrix_left, self.dist_coeffs_left, R1, P1, self.img_size, cv2.CV_32FC1)
        
        self.rect_map_right = cv2.initUndistortRectifyMap(
            self.camera_matrix_right, self.dist_coeffs_right, R2, P2, self.img_size, cv2.CV_32FC1)
        
        self.calibrated = True
        return True
    
    def rectify_images(self, img_left, img_right):
        """Görüntüleri rektifiye et"""
        if not self.calibrated or self.rect_map_left is None or self.rect_map_right is None:
            return img_left, img_right
        
        rect_left = cv2.remap(img_left, self.rect_map_left[0], self.rect_map_left[1], cv2.INTER_LINEAR)
        rect_right = cv2.remap(img_right, self.rect_map_right[0], self.rect_map_right[1], cv2.INTER_LINEAR)
        
        return rect_left, rect_right
    
    def save_calibration(self, filename="calibration/stereo_calibration.pkl"):
        """Kalibrasyon verilerini kaydet"""
        if not self.calibrated:
            print("Kaydedilecek kalibrasyon verisi yok!")
            return False
        
        calibration_data = {
            'camera_matrix_left': self.camera_matrix_left,
            'dist_coeffs_left': self.dist_coeffs_left,
            'camera_matrix_right': self.camera_matrix_right,
            'dist_coeffs_right': self.dist_coeffs_right,
            'R': self.R,
            'T': self.T,
            'E': self.E,
            'F': self.F,
            'img_size': self.img_size,
            'rect_map_left': self.rect_map_left,
            'rect_map_right': self.rect_map_right
        }
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'wb') as f:
            pickle.dump(calibration_data, f)
        
        print(f"Kalibrasyon verileri {filename} dosyasına kaydedildi.")
        return True
    
    def load_calibration(self, filename="calibration/stereo_calibration.pkl"):
        """Kalibrasyon verilerini yükle"""
        try:
            with open(filename, 'rb') as f:
                calibration_data = pickle.load(f)
            
            self.camera_matrix_left = calibration_data['camera_matrix_left']
            self.dist_coeffs_left = calibration_data['dist_coeffs_left']
            self.camera_matrix_right = calibration_data['camera_matrix_right']
            self.dist_coeffs_right = calibration_data['dist_coeffs_right']
            self.R = calibration_data['R']
            self.T = calibration_data['T']
            self.E = calibration_data['E']
            self.F = calibration_data['F']
            self.img_size = calibration_data['img_size']
            self.rect_map_left = calibration_data.get('rect_map_left', None)
            self.rect_map_right = calibration_data.get('rect_map_right', None)
            
            # Eğer rektifikasyon haritaları yoksa oluştur
            if self.rect_map_left is None or self.rect_map_right is None:
                R1, R2, P1, P2, Q, roi_left, roi_right = cv2.stereoRectify(
                    self.camera_matrix_left, self.dist_coeffs_left,
                    self.camera_matrix_right, self.dist_coeffs_right,
                    self.img_size, self.R, self.T,
                    flags=cv2.CALIB_ZERO_DISPARITY, alpha=0.9)
                
                self.rect_map_left = cv2.initUndistortRectifyMap(
                    self.camera_matrix_left, self.dist_coeffs_left, R1, P1, self.img_size, cv2.CV_32FC1)
                
                self.rect_map_right = cv2.initUndistortRectifyMap(
                    self.camera_matrix_right, self.dist_coeffs_right, R2, P2, self.img_size, cv2.CV_32FC1)
            
            self.calibrated = True
            print(f"Kalibrasyon verileri {filename} dosyasından yüklendi.")
            return True
        except Exception as e:
            print(f"Kalibrasyon verileri yüklenemedi: {e}")
            return False