[Güncelleme sistemi importları]
import sys
import cv2
import numpy as np
...
[Diğer tüm importlar]

# Güncelleme sistemi için
CURRENT_VERSION = "1.0.0"
VERSION_URL = "https://raw.githubusercontent.com/w1907s/berko/main/version.txt"

def check_for_updates():
    [Güncelleme sistemi kodu]

# Makro kodunuz
[Tüm makro sınıfları ve fonksiyonlar]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f'Discord v{CURRENT_VERSION}')  # Versiyon numarasını ekleyin
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

        [Geri kalan initUI kodunuz]

    def show_version(self):
        QMessageBox.information(self, 'Version Bilgisi', 
                              f'Knight Macro\nVersion: {CURRENT_VERSION}')

    [Geri kalan tüm metodlar]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
