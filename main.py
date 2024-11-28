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
                update_file = "berk_new_new.exe"
                
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

def get_window_handle():
    return win32gui.FindWindow(None, "Knight Evolution")
class MacroThread(QThread):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.running = False
        self.active_skills = [s for s in settings['skills'] if s['active']]
        
        print("\nAktif skill sırası:")
        for i, skill in enumerate(self.active_skills):
            print(f"Sıra {i+1}: Skill {skill['key']}, Delay={skill['delay']}ms")

    def find_image(self, template_path):
        try:
            hwnd = get_window_handle()
            if not hwnd:
                return None

            window_rect = win32gui.GetWindowRect(hwnd)
            screenshot = ImageGrab.grab(bbox=window_rect)
            screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            template = cv2.imread(f'skills/{template_path}.png')
            result = cv2.matchTemplate(screenshot_np, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > 0.8:
                return True
            return False
        except Exception as e:
            print(f"Find image error: {e}")
            return False

    def press_skill(self, skill_key):
        try:
            hwnd = get_window_handle()
            if hwnd:
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.1)
                pydirectinput.press(str(skill_key))
                print(f"Skill {skill_key} basıldı")
                return True
            return False
        except Exception as e:
            print(f"Press skill error: {e}")
            return False

    def click_at_coords(self, x, y):
        try:
            hwnd = get_window_handle()
            if hwnd:
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.1)
                win32api.SetCursorPos((x, y))
                time.sleep(0.1)
                lParam = win32api.MAKELONG(x, y)
                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                time.sleep(0.1)
                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                print(f"Clicked at coordinates: {x}, {y}")
                return True
            return False
        except Exception as e:
            print(f"Click error: {e}")
            return False

    def toggle_genie(self, action):
        coords = self.settings['genie_coords'].get(action)
        if coords:
            x, y = coords
            if self.click_at_coords(x, y):
                print(f"Genie {action} tıklandı: {coords}")
                return True
        return False

    def run(self):
        self.running = True
        genie_active = False
        genie_control_enabled = self.settings.get('genie_control_active', False)
        current_skill_index = 0
        last_skill_time = 0
        last_db_check_time = 0
        same_db_count = 0
        
        while self.running:
            try:
                current_time = time.time() * 1000

                found_db1 = self.find_image("db1")
                found_db2 = self.find_image("db2")
                found_db3 = self.find_image("db3")

                if found_db1 or found_db2 or found_db3:
                    print("DB bulundu!")
                    
                    if current_time - last_db_check_time >= 2000:
                        if same_db_count >= 3:
                            print("DB aynı yerde takılı kaldı!")
                            
                            if genie_active and genie_control_enabled:
                                if self.toggle_genie('stop'):
                                    genie_active = False
                                    print("Genie durduruldu!")
                                    time.sleep(0.5)
                                    
                                if self.toggle_genie('start'):
                                    genie_active = True
                                    print("Genie yeniden başlatıldı!")
                            
                            if self.active_skills:
                                if self.press_skill(self.active_skills[0]['key']):
                                    print("CC Skill yeniden basıldı!")
                            
                            same_db_count = 0
                        else:
                            same_db_count += 1
                        
                        last_db_check_time = current_time
                    
                    if genie_control_enabled and not genie_active:
                        if self.toggle_genie('start'):
                            genie_active = True
                            print("Genie başlatıldı!")
                    
                    if self.active_skills and current_time - last_skill_time >= self.active_skills[current_skill_index]['delay']:
                        current_skill = self.active_skills[current_skill_index]
                        
                        if self.press_skill(current_skill['key']):
                            print(f"Skill {current_skill['key']} basıldı")
                            last_skill_time = current_time
                            current_skill_index = (current_skill_index + 1) % len(self.active_skills)
                            print(f"Sıradaki skill: {self.active_skills[current_skill_index]['key']}")
                
                else:
                    print("DB kayboldu, işlem durduruluyor...")
                    if genie_active and genie_control_enabled:
                        if self.toggle_genie('stop'):
                            genie_active = False
                            print("Genie durduruldu!")
                    
                    current_skill_index = 0
                    last_skill_time = 0
                    same_db_count = 0
                
                time.sleep(0.1)

            except Exception as e:
                print(f"Macro error: {e}")
                time.sleep(0.1)
class MageTestThread(QThread):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.running = False
        
    def click_at_coords(self, x, y):
        try:
            hwnd = get_window_handle()
            if hwnd:
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.1)
                win32api.SetCursorPos((x, y))
                time.sleep(0.1)
                lParam = win32api.MAKELONG(x, y)
                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
                time.sleep(0.1)
                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
                print(f"Clicked at coordinates: {x}, {y}")
                return True
            return False
        except Exception as e:
            print(f"Click error: {e}")
            return False

    def press_skill(self, skill_key):
        try:
            hwnd = get_window_handle()
            if hwnd:
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.1)
                keyboard.press_and_release(str(skill_key))
                print(f"Skill {skill_key} basıldı")
                return True
            return False
        except Exception as e:
            print(f"Press skill error: {e}")
            return False

    def run(self):
        self.running = True
        
        while self.running:
            try:
                if keyboard.is_pressed('f11'):
                    time.sleep(0.3)
                    print("\nMakro başlatıldı")
                    
                    active_coords = [(i, coord) for i, (coord, active) in 
                                   enumerate(zip(self.settings['teleport_coords'], 
                                               self.settings['coord_active'])) 
                                   if active and coord is not None]
                    
                    if active_coords:
                        for index, coords in active_coords:
                            if not self.running:
                                break
                                
                            print(f"\nKoordinat {index+1} işleniyor")
                            
                            if self.click_at_coords(coords[0], coords[1]):
                                print(f"Koordinat {index+1} tıklandı: {coords}")
                                time.sleep(0.2)
                                
                                if self.press_skill(self.settings['skill_number']):
                                    print(f"TP Skill basıldı")
                                    
                                    if index != active_coords[-1][0]:
                                        delay = self.settings['delay'] / 1000.0
                                        print(f"Bekleniyor: {delay} saniye")
                                        time.sleep(delay)
                    
                    print("Makro tamamlandı")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Test error: {e}")
                time.sleep(0.1)

class CaptureThread(QThread):
    capture_complete = pyqtSignal(bool, str)
    
    def __init__(self, skill_type):
        super().__init__()
        self.skill_type = skill_type
        
    def run(self):
        try:
            while True:
                if keyboard.is_pressed('ctrl'):
                    x, y = win32api.GetCursorPos()
                    screenshot = ImageGrab.grab(bbox=(x-10, y-10, x+10, y+10))
                    
                    if not os.path.exists('skills'):
                        os.makedirs('skills')
                    
                    screenshot.save(f'skills/{self.skill_type}.png')
                    self.capture_complete.emit(True, self.skill_type)
                    break
                    
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Capture error: {e}")
            self.capture_complete.emit(False, self.skill_type)

class CoordCaptureThread(QThread):
    coord_captured = pyqtSignal(bool, tuple, str)
    
    def __init__(self, coord_type):
        super().__init__()
        self.coord_type = coord_type
        
    def run(self):
        try:
            while True:
                if keyboard.is_pressed('ctrl'):
                    x, y = win32api.GetCursorPos()
                    self.coord_captured.emit(True, (x, y), self.coord_type)
                    break
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Koordinat yakalama hatası: {e}")
            self.coord_captured.emit(False, None, self.coord_type)
class MageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.teleport_coords = [None] * 7
        self.coord_active = [False] * 7
        self.initUI()
        self.load_settings()

    def initUI(self):
        self.setWindowTitle('Mage Ayarı')
        self.setGeometry(100, 100, 500, 500)
        
        main_layout = QVBoxLayout()

        # Teleport Skill Ayarı
        skill_group = QGroupBox("Teleport Skill Ayarı")
        skill_layout = QHBoxLayout()
        
        skill_layout.addWidget(QLabel("TP Skilli:"))
        self.skill_combo = QComboBox()
        self.skill_combo.addItems([str(x) for x in range(1, 10)])
        self.skill_combo.setFixedWidth(50)
        skill_layout.addWidget(self.skill_combo)
        
        skill_layout.addWidget(QLabel("Gecikme (ms):"))
        self.delay_input = QLineEdit()
        self.delay_input.setPlaceholderText("1000")
        self.delay_input.setFixedWidth(70)
        skill_layout.addWidget(self.delay_input)
        
        skill_group.setLayout(skill_layout)
        skill_group.setFixedHeight(80)
        main_layout.addWidget(skill_group)
        
        # Teleport Koordinatları
        teleport_group = QGroupBox("Teleport Edilecek Koordinatlar")
        teleport_layout = QVBoxLayout()
        
        self.coord_buttons = []
        self.coord_labels = []
        self.coord_checkboxes = []
        
        for i in range(7):
            coord_container = QHBoxLayout()
            
            coord_checkbox = QCheckBox()
            coord_checkbox.setChecked(False)
            self.coord_checkboxes.append(coord_checkbox)
            coord_container.addWidget(coord_checkbox)
            
            coord_button = QPushButton(f'Koordinat {i+1}')
            coord_button.clicked.connect(lambda checked, x=i: self.start_coord_capture(x))
            self.coord_buttons.append(coord_button)
            coord_container.addWidget(coord_button)
            
            coord_label = QLabel('Konum: -')
            self.coord_labels.append(coord_label)
            coord_container.addWidget(coord_label)
            
            delete_button = QPushButton('Sil')
            delete_button.clicked.connect(lambda checked, x=i: self.delete_coord(x))
            coord_container.addWidget(delete_button)
            
            coord_container.addStretch()
            teleport_layout.addLayout(coord_container)
        
        teleport_group.setLayout(teleport_layout)
        main_layout.addWidget(teleport_group)
        
        # Kaydet butonu
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        save_button = QPushButton('KAYDET')
        save_button.clicked.connect(self.save_settings_with_message)
        bottom_layout.addWidget(save_button)
        main_layout.addLayout(bottom_layout)
        
        self.setLayout(main_layout)

    def start_coord_capture(self, index):
        self.coord_capture_thread = CoordCaptureThread(str(index))
        self.coord_capture_thread.coord_captured.connect(
            lambda success, coords, idx: self.on_coord_capture_complete(success, coords, int(idx)))
        self.coord_capture_thread.start()

    def delete_coord(self, index):
        self.teleport_coords[index] = None
        self.coord_labels[index].setText('Konum: -')
        self.coord_checkboxes[index].setChecked(False)

    def on_coord_capture_complete(self, success, coords, index):
        if success:
            self.teleport_coords[index] = coords
            self.coord_labels[index].setText(f'Konum: {coords}')

    def save_settings_with_message(self):
        self.save_settings()
        QMessageBox.information(self, 'Bilgi', 'Ayarlar kaydedildi!')

    def save_settings(self):
        try:
            delay = int(self.delay_input.text().strip() or "1000")
        except ValueError:
            delay = 1000
            
        settings = {
            'teleport_coords': self.teleport_coords,
            'coord_active': [cb.isChecked() for cb in self.coord_checkboxes],
            'skill_number': self.skill_combo.currentText(),
            'delay': delay
        }
        
        with open('mage_settings.json', 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open('mage_settings.json', 'r') as f:
                settings = json.load(f)
                
                if 'teleport_coords' in settings:
                    self.teleport_coords = settings['teleport_coords']
                    for i, coords in enumerate(self.teleport_coords):
                        if coords:
                            self.coord_labels[i].setText(f'Konum: {coords}')
                
                if 'coord_active' in settings:
                    for i, active in enumerate(settings['coord_active']):
                        self.coord_checkboxes[i].setChecked(active)
                
                if 'skill_number' in settings:
                    self.skill_combo.setCurrentText(settings['skill_number'])
                
                if 'delay' in settings:
                    self.delay_input.setText(str(settings['delay']))
                
        except Exception as e:
            print(f"Ayarlar yüklenirken hata: {e}")

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)
class SkillDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.skill_settings = []
        self.genie_coords = {'start': None, 'stop': None}
        self.db_images = {}
        self.initUI()
        self.load_settings()

    def initUI(self):
        self.setWindowTitle('Priest Ayarı')
        self.setGeometry(100, 100, 400, 300)
        
        main_layout = QVBoxLayout()
        
        # DB Seçim Grubu
        db_group = QGroupBox("DB Seçimi")
        db_layout = QHBoxLayout()
        
        # DB butonları ve resimleri
        self.db_buttons = []
        self.db_labels = {}
        for i in range(3):
            db_container = QHBoxLayout()
            
            db_button = QPushButton(f'DB {i+1}')
            db_button.clicked.connect(lambda checked, x=i: self.start_capture(f'db{x+1}'))
            self.db_buttons.append(db_button)
            db_container.addWidget(db_button)
            
            image_label = QLabel()
            image_label.setFixedSize(20, 20)
            self.db_labels[f'db{i+1}'] = image_label
            db_container.addWidget(image_label)
            
            db_layout.addLayout(db_container)
        
        db_group.setLayout(db_layout)
        main_layout.addWidget(db_group)

        # Genie Kontrol
        genie_group = QGroupBox("Genie")
        genie_layout = QVBoxLayout()
        
        self.genie_control_check = QCheckBox("Genie Açık")
        genie_layout.addWidget(self.genie_control_check)
        
        coord_layout = QHBoxLayout()
        
        # Başlat koordinatı
        start_layout = QVBoxLayout()
        self.genie_start_button = QPushButton('Başlat')
        self.genie_start_button.clicked.connect(lambda: self.start_coord_capture('start'))
        self.genie_start_status = QLabel('Konum: -')
        start_layout.addWidget(self.genie_start_button)
        start_layout.addWidget(self.genie_start_status)
        coord_layout.addLayout(start_layout)
        
        # Durdur koordinatı
        stop_layout = QVBoxLayout()
        self.genie_stop_button = QPushButton('Durdur')
        self.genie_stop_button.clicked.connect(lambda: self.start_coord_capture('stop'))
        self.genie_stop_status = QLabel('Konum: -')
        stop_layout.addWidget(self.genie_stop_button)
        stop_layout.addWidget(self.genie_stop_status)
        coord_layout.addLayout(stop_layout)
        
        genie_layout.addLayout(coord_layout)
        genie_group.setLayout(genie_layout)
        main_layout.addWidget(genie_group)
        
        # Skill ayarları
        skill_group = QGroupBox("Skill Ayarları")
        skill_layout = QVBoxLayout()
        
        self.skill_groups = []
        
        # Sadece CC Skilli
        skill_row = QHBoxLayout()
        
        skill_check = QCheckBox("CC Skilli")
        skill_row.addWidget(skill_check)
        
        skill_num_combo = QComboBox()
        skill_num_combo.addItems([str(x) for x in range(1, 10)])
        skill_num_combo.setFixedWidth(50)
        skill_row.addWidget(skill_num_combo)
        
        delay_input = QLineEdit()
        delay_input.setPlaceholderText("Delay")
        delay_input.setFixedWidth(70)
        skill_row.addWidget(delay_input)
        
        skill_row.addStretch()
        skill_layout.addLayout(skill_row)
        
        self.skill_groups.append({
            'checkbox': skill_check,
            'combo': skill_num_combo,
            'delay': delay_input
        })
        
        skill_group.setLayout(skill_layout)
        main_layout.addWidget(skill_group)
        
        # Alt kısım - Kaydet butonu
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        save_button = QPushButton('KAYDET')
        save_button.clicked.connect(self.save_settings_with_message)
        bottom_layout.addWidget(save_button)
        main_layout.addLayout(bottom_layout)
        
        self.setLayout(main_layout)
        
        # Mevcut DB resimlerini yükle
        self.load_db_images()

    def load_db_images(self):
        for i in range(3):
            db_name = f'db{i+1}'
            image_path = f'skills/{db_name}.png'
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                self.db_labels[db_name].setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio))

    def start_capture(self, skill_type):
        self.capture_thread = CaptureThread(skill_type)
        self.capture_thread.capture_complete.connect(
            lambda success, st=skill_type: self.on_capture_complete(success, st))
        self.capture_thread.start()

    def start_coord_capture(self, coord_type):
        self.coord_capture_thread = CoordCaptureThread(coord_type)
        self.coord_capture_thread.coord_captured.connect(self.on_coord_capture_complete)
        self.coord_capture_thread.start()

    def on_capture_complete(self, success, skill_type):
        if success:
            pixmap = QPixmap(f'skills/{skill_type}.png')
            if skill_type.startswith('db'):
                self.db_labels[skill_type].setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio))

    def on_coord_capture_complete(self, success, coords, coord_type):
        if success:
            self.genie_coords[coord_type] = coords
            status_label = self.genie_start_status if coord_type == 'start' else self.genie_stop_status
            status_label.setText(f'Konum: {coords}')

    def save_settings_with_message(self):
        self.save_settings()
        QMessageBox.information(self, 'Bilgi', 'Ayarlar kaydedildi!')

    def save_settings(self):
        settings = {
            'skills': [],
            'genie_coords': self.genie_coords,
            'genie_control_active': self.genie_control_check.isChecked()
        }
        
        for group in self.skill_groups:
            try:
                delay_text = group['delay'].text().strip()
                delay = int(delay_text) if delay_text else 1000
            except ValueError:
                delay = 1000
                
            settings['skills'].append({
                'active': group['checkbox'].isChecked(),
                'key': group['combo'].currentText(),
                'delay': delay
            })
        
        with open('skill_settings.json', 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open('skill_settings.json', 'r') as f:
                settings = json.load(f)
                
                if 'genie_control_active' in settings:
                    self.genie_control_check.setChecked(settings['genie_control_active'])
                
                if 'genie_coords' in settings:
                    self.genie_coords = settings['genie_coords']
                    if self.genie_coords.get('start'):
                        self.genie_start_status.setText(f'Konum: {self.genie_coords["start"]}')
                    if self.genie_coords.get('stop'):
                        self.genie_stop_status.setText(f'Konum: {self.genie_coords["stop"]}')
                
                for i, skill in enumerate(settings['skills']):
                    group = self.skill_groups[i]
                    group['checkbox'].setChecked(skill['active'])
                    group['combo'].setCurrentText(str(skill['key']))
                    group['delay'].setText(str(skill['delay']))
        except Exception as e:
            print(f"Ayarlar yüklenirken hata: {e}")

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)
class SkillDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.skill_settings = []
        self.genie_coords = {'start': None, 'stop': None}
        self.db_images = {}
        self.initUI()
        self.load_settings()

    def initUI(self):
        self.setWindowTitle('Priest Ayarı')
        self.setGeometry(100, 100, 400, 300)
        
        main_layout = QVBoxLayout()
        
        # DB Seçim Grubu
        db_group = QGroupBox("DB Seçimi")
        db_layout = QHBoxLayout()
        
        # DB butonları ve resimleri
        self.db_buttons = []
        self.db_labels = {}
        for i in range(3):
            db_container = QHBoxLayout()
            
            db_button = QPushButton(f'DB {i+1}')
            db_button.clicked.connect(lambda checked, x=i: self.start_capture(f'db{x+1}'))
            self.db_buttons.append(db_button)
            db_container.addWidget(db_button)
            
            image_label = QLabel()
            image_label.setFixedSize(20, 20)
            self.db_labels[f'db{i+1}'] = image_label
            db_container.addWidget(image_label)
            
            db_layout.addLayout(db_container)
        
        db_group.setLayout(db_layout)
        main_layout.addWidget(db_group)

        # Genie Kontrol
        genie_group = QGroupBox("Genie")
        genie_layout = QVBoxLayout()
        
        self.genie_control_check = QCheckBox("Genie Açık")
        genie_layout.addWidget(self.genie_control_check)
        
        coord_layout = QHBoxLayout()
        
        # Başlat koordinatı
        start_layout = QVBoxLayout()
        self.genie_start_button = QPushButton('Başlat')
        self.genie_start_button.clicked.connect(lambda: self.start_coord_capture('start'))
        self.genie_start_status = QLabel('Konum: -')
        start_layout.addWidget(self.genie_start_button)
        start_layout.addWidget(self.genie_start_status)
        coord_layout.addLayout(start_layout)
        
        # Durdur koordinatı
        stop_layout = QVBoxLayout()
        self.genie_stop_button = QPushButton('Durdur')
        self.genie_stop_button.clicked.connect(lambda: self.start_coord_capture('stop'))
        self.genie_stop_status = QLabel('Konum: -')
        stop_layout.addWidget(self.genie_stop_button)
        stop_layout.addWidget(self.genie_stop_status)
        coord_layout.addLayout(stop_layout)
        
        genie_layout.addLayout(coord_layout)
        genie_group.setLayout(genie_layout)
        main_layout.addWidget(genie_group)
        
        # Skill ayarları
        skill_group = QGroupBox("Skill Ayarları")
        skill_layout = QVBoxLayout()
        
        self.skill_groups = []
        
        # Sadece CC Skilli
        skill_row = QHBoxLayout()
        
        skill_check = QCheckBox("CC Skilli")
        skill_row.addWidget(skill_check)
        
        skill_num_combo = QComboBox()
        skill_num_combo.addItems([str(x) for x in range(1, 10)])
        skill_num_combo.setFixedWidth(50)
        skill_row.addWidget(skill_num_combo)
        
        delay_input = QLineEdit()
        delay_input.setPlaceholderText("Delay")
        delay_input.setFixedWidth(70)
        skill_row.addWidget(delay_input)
        
        skill_row.addStretch()
        skill_layout.addLayout(skill_row)
        
        self.skill_groups.append({
            'checkbox': skill_check,
            'combo': skill_num_combo,
            'delay': delay_input
        })
        
        skill_group.setLayout(skill_layout)
        main_layout.addWidget(skill_group)
        
        # Alt kısım - Kaydet butonu
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        save_button = QPushButton('KAYDET')
        save_button.clicked.connect(self.save_settings_with_message)
        bottom_layout.addWidget(save_button)
        main_layout.addLayout(bottom_layout)
        
        self.setLayout(main_layout)
        
        # Mevcut DB resimlerini yükle
        self.load_db_images()

    def load_db_images(self):
        for i in range(3):
            db_name = f'db{i+1}'
            image_path = f'skills/{db_name}.png'
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                self.db_labels[db_name].setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio))

    def start_capture(self, skill_type):
        self.capture_thread = CaptureThread(skill_type)
        self.capture_thread.capture_complete.connect(
            lambda success, st=skill_type: self.on_capture_complete(success, st))
        self.capture_thread.start()

    def start_coord_capture(self, coord_type):
        self.coord_capture_thread = CoordCaptureThread(coord_type)
        self.coord_capture_thread.coord_captured.connect(self.on_coord_capture_complete)
        self.coord_capture_thread.start()

    def on_capture_complete(self, success, skill_type):
        if success:
            pixmap = QPixmap(f'skills/{skill_type}.png')
            if skill_type.startswith('db'):
                self.db_labels[skill_type].setPixmap(pixmap.scaled(20, 20, Qt.KeepAspectRatio))

    def on_coord_capture_complete(self, success, coords, coord_type):
        if success:
            self.genie_coords[coord_type] = coords
            status_label = self.genie_start_status if coord_type == 'start' else self.genie_stop_status
            status_label.setText(f'Konum: {coords}')

    def save_settings_with_message(self):
        self.save_settings()
        QMessageBox.information(self, 'Bilgi', 'Ayarlar kaydedildi!')

    def save_settings(self):
        settings = {
            'skills': [],
            'genie_coords': self.genie_coords,
            'genie_control_active': self.genie_control_check.isChecked()
        }
        
        for group in self.skill_groups:
            try:
                delay_text = group['delay'].text().strip()
                delay = int(delay_text) if delay_text else 1000
            except ValueError:
                delay = 1000
                
            settings['skills'].append({
                'active': group['checkbox'].isChecked(),
                'key': group['combo'].currentText(),
                'delay': delay
            })
        
        with open('skill_settings.json', 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open('skill_settings.json', 'r') as f:
                settings = json.load(f)
                
                if 'genie_control_active' in settings:
                    self.genie_control_check.setChecked(settings['genie_control_active'])
                
                if 'genie_coords' in settings:
                    self.genie_coords = settings['genie_coords']
                    if self.genie_coords.get('start'):
                        self.genie_start_status.setText(f'Konum: {self.genie_coords["start"]}')
                    if self.genie_coords.get('stop'):
                        self.genie_stop_status.setText(f'Konum: {self.genie_coords["stop"]}')
                
                for i, skill in enumerate(settings['skills']):
                    group = self.skill_groups[i]
                    group['checkbox'].setChecked(skill['active'])
                    group['combo'].setCurrentText(str(skill['key']))
                    group['delay'].setText(str(skill['delay']))
        except Exception as e:
            print(f"Ayarlar yüklenirken hata: {e}")

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)
