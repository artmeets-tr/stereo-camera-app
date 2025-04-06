#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import cv2
import numpy as np
import time
from camera import CameraController
from calibration import StereoCalibration
from aruco_detector import ArucoDetector
from gui import GUI
import settings
import utils

def main():
    # Gerekli klasörleri oluştur
    for directory in settings.REQUIRED_DIRS:
        os.makedirs(directory, exist_ok=True)
    
    # Sistem kontrolü
    if not utils.check_system():
        print("Sistem gereksinimleri karşılanmıyor!")
        return
    
    # ArduCam kontrolü
    if not utils.check_arducam():
        print("ArduCam sürücüleri bulunamadı!")
        print("Lütfen README dosyasındaki kurulum adımlarını takip edin.")
        return
    
    # Ana uygulamayı başlat
    try:
        app = GUI()
        app.run()
    except KeyboardInterrupt:
        print("\nUygulama kapatılıyor...")
    except Exception as e:
        print(f"Hata: {e}")
    finally:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()