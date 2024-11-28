import sys
import cv2
import numpy as np
import win32gui
import win32api
import win32con
import time
import keyboard
import json
from ctypes import *
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTabWidget, 
                            QMessageBox, QDialog, QCheckBox, QComboBox, QLineEdit,
                            QGroupBox, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from PIL import ImageGrab, Image
import pydirectinput
import os
from datetime import datetime
import requests
import subprocess
from packaging import version

# Güncelleme sistemi için
CURRENT_VERSION = "1.0.0"
VERSION_URL = "https://raw.githubusercontent.com/w1907s/berko/main/version.txt"

def check_for_updates():
    try:
        response = requests.get(VERSION_URL)
        version_info = {}
        for line in response.text.splitlines():
            if '=' in line:
                key, value = line.split('=')
                version_info[key.strip()] = value.strip()
        
        if version.parse(version_info['version']) > version.parse(CURRENT_VERSION):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Yeni güncelleme mevcut!")
            msg.setInformativeText(f"Mevcut versiyon: {CURRENT_VERSION}\nYeni versiyon: {version_info['version']}\n\nGüncellemek ister misiniz?")
            msg.setWindowTitle("Güncelleme")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            
            if msg.exec_() == QMessageBox.Yes:
                new_exe = requests.get(version_info['download_url'])
                update_file = "KnightMacro_new.exe"
                
                with open(update_file, 'wb') as f:
                    f.write(new_exe.content)
                
                with open('update.bat', 'w') as f:
                    f.write('@echo off\n')
                    f.write('timeout /t 1 /nobreak\n')
                    f.write(f'del "{sys.executable}"\n')
                    f.write(f'move /y "{update_file}" "{sys.executable}"\n')
                    f.write(f'start "" "{sys.executable}"\n')
                    f.write('del "%~f0"\n')
                
                subprocess.Popen('update.bat')
                sys.exit()
                
    except Exception as e:
        print(f"Güncelleme kontrolü hatası: {e}")

# pydirectinput yapılandırması
pydirectinput.PAUSE = 0.1

[Buraya geri kalan tüm kodunuzu yapıştırın...]

# Ana pencere sınıfının __init__ metodunda güncelleme kontrolünü ekleyin
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f'Discord v{CURRENT_VERSION}')
        self.initUI()
        self.running = False
        self.macro_thread = None
        self.skill_dialog = None
        self.mage_thread = None
        self.selected_job = None
        
        # Başlangıçta güncelleme kontrolü
        check_for_updates()

    def initUI(self):
        # Menü bar ekle
        menubar = self.menuBar()
        helpMenu = menubar.addMenu('Yardım')
        
        # Güncelleme kontrolü için action
        checkUpdate = QAction('Güncelleme Kontrol Et', self)
        checkUpdate.triggered.connect(check_for_updates)
        helpMenu.addAction(checkUpdate)
        
        # Version bilgisi için action
        versionAction = QAction('Version Bilgisi', self)
        versionAction.triggered.connect(self.show_version)
        helpMenu.addAction(versionAction)

        [Geri kalan initUI kodunuz...]

    def show_version(self):
        QMessageBox.information(self, 'Version Bilgisi', 
                              f'Discord\nVersion: {CURRENT_VERSION}')

[Geri kalan tüm kodunuz...]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
