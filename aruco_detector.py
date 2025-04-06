#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import os

class ArucoDetector:
    def __init__(self, dictionary_id=cv2.aruco.DICT_4X4_50):
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary_id)
        self.parameters = cv2.aruco.DetectorParameters()
        
    def create_marker(self, marker_id, size=200, output_file=None):
        """ArUco marker oluştur ve kaydedilmesi istenirse dosyaya kaydet"""
        marker = np.zeros((size, size), dtype=np.uint8)
        marker = cv2.aruco.generateImageMarker(self.aruco_dict, marker_id, size, marker, 1)
        
        if output_file is not None:
            # Klasörü oluştur
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            # Markeri kaydet
            cv2.imwrite(output_file, marker)
            print(f"Marker {output_file} dosyasına kaydedildi.")
        
        return marker
    
    def create_marker_set(self, start_id, count, size=200, output_dir="aruco_markers"):
        """Birden çok ArUco marker oluştur ve kaydet"""
        os.makedirs(output_dir, exist_ok=True)
        
        markers = []
        for i in range(count):
            marker_id = start_id + i
            output_file = os.path.join(output_dir, f"marker_{marker_id}.png")
            marker = self.create_marker(marker_id, size, output_file)
            markers.append(marker)
        
        print(f"{count} adet marker oluşturuldu ve {output_dir} klasörüne kaydedildi.")
        return markers
        
    def detect_markers(self, image):
        """Görüntüdeki ArUco markerları tespit et"""
        if image is None:
            return [], None, []
            
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = cv2.aruco.detectMarkers(gray, self.aruco_dict, parameters=self.parameters)
        return corners, ids, rejected
    
    def draw_detected_markers(self, image, corners, ids):
        """Tespit edilen markerları görüntü üzerine çiz"""
        if image is None:
            return None
            
        if ids is not None and len(ids) > 0:
            image = cv2.aruco.drawDetectedMarkers(image.copy(), corners, ids)
        return image
    
    def estimate_pose(self, corners, ids, camera_matrix, dist_coeffs, marker_length=0.05):
        """Marker'ların pozisyonunu tahmin et"""
        if ids is None or len(ids) == 0:
            return [], []
        
        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(corners, marker_length, 
                                                             camera_matrix, dist_coeffs)
        return rvecs, tvecs
    
    def draw_axes(self, image, camera_matrix, dist_coeffs, rvecs, tvecs, marker_length=0.05):
        """Her marker için koordinat eksenlerini çiz"""
        if image is None or len(rvecs) == 0:
            return image if image is not None else None
        
        result_image = image.copy()
        for i in range(len(rvecs)):
            cv2.drawFrameAxes(result_image, camera_matrix, dist_coeffs, 
                            rvecs[i], tvecs[i], marker_length/2)
        
        return result_image
        
    def calculate_distance(self, tvecs):
        """Kamera ile marker arasındaki mesafeyi hesapla (metre cinsinden)"""
        if len(tvecs) == 0:
            return []
        
        distances = []
        for tvec in tvecs:
            # 3D vektörün büyüklüğü (Euclidean mesafe)
            distance = np.linalg.norm(tvec)
            distances.append(distance)
        
        return distances
    
    def detect_and_draw(self, image, camera_matrix=None, dist_coeffs=None, draw_axes=False, marker_length=0.05):
        """Markerları tespit et ve görüntü üzerine çiz, isteğe bağlı olarak poz hesapla"""
        if image is None:
            return None, [], None, []
            
        # Markerları tespit et
        corners, ids, rejected = self.detect_markers(image)
        
        # Eğer hiç marker tespit edilmediyse
        if ids is None or len(ids) == 0:
            return image, [], None, []
        
        # Tespit edilen markerları çiz
        result_image = self.draw_detected_markers(image, corners, ids)
        
        rvecs, tvecs = [], []
        distances = []
        
        # Eğer kamera matrisi ve distorsiyon katsayıları verildiyse poz tahmini yap
        if camera_matrix is not None and dist_coeffs is not None:
            rvecs, tvecs = self.estimate_pose(corners, ids, camera_matrix, dist_coeffs, marker_length)
            
            # Koordinat eksenlerini çiz
            if draw_axes and len(rvecs) > 0:
                result_image = self.draw_axes(result_image, camera_matrix, dist_coeffs, rvecs, tvecs, marker_length)
            
            # Mesafeleri hesapla
            distances = self.calculate_distance(tvecs)
        
        return result_image, corners, ids, distances