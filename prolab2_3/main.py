import sys
import bcrypt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QMessageBox, QStackedWidget, QGroupBox, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon, QFont, QPalette, QColor
import psycopg2
from dotenv import load_dotenv
import os
from doctor_panel import DoctorPanel
from patient_panel import PatientPanel

# .env dosyasını yükle
load_dotenv()

# Veritabanı bağlantısı için gerekli bilgiler
DB_NAME = os.getenv('DB_NAME', 'diabetes_monitoring_system')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

class LoginWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Başlık
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background-color: #4a90e2;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        title_layout = QVBoxLayout()
        
        title = QLabel("Diyabet Takip Sistemi")
        title.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Sağlığınız için yanınızdayız")
        subtitle.setStyleSheet("""
            color: white;
            font-size: 16px;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_frame.setLayout(title_layout)
        layout.addWidget(title_frame)

        # Giriş seçenekleri
        login_options = QHBoxLayout()
        
        self.doctor_btn = QPushButton("👨‍⚕️ Doktor Girişi")
        self.patient_btn = QPushButton("👤 Hasta Girişi")
        
        for btn in [self.doctor_btn, self.patient_btn]:
            btn.setCheckable(True)
            btn.setMinimumHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    border: 2px solid #e1e1e1;
                    border-radius: 5px;
                    font-size: 16px;
                    font-weight: bold;
                    color: #666666;
                }
                QPushButton:checked {
                    background-color: #4a90e2;
                    border-color: #4a90e2;
                    color: white;
                }
                QPushButton:hover:!checked {
                    background-color: #e9ecef;
                }
            """)
            login_options.addWidget(btn)
        
        self.doctor_btn.setChecked(True)
        self.doctor_btn.clicked.connect(lambda: self.toggle_login_type(self.doctor_btn))
        self.patient_btn.clicked.connect(lambda: self.toggle_login_type(self.patient_btn))
        
        layout.addLayout(login_options)

        # Giriş formu
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        form_layout = QVBoxLayout()
        
        # TC Kimlik No
        tc_layout = QVBoxLayout()
        tc_label = QLabel("T.C. Kimlik No:")
        tc_label.setStyleSheet("font-weight: bold; color: #666666;")
        self.tc_input = QLineEdit()
        self.tc_input.setPlaceholderText("T.C. Kimlik Numaranızı Girin")
        self.tc_input.setMaxLength(11)
        self.tc_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #e1e1e1;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
            }
        """)
        tc_layout.addWidget(tc_label)
        tc_layout.addWidget(self.tc_input)
        form_layout.addLayout(tc_layout)
        
        # Şifre
        password_layout = QVBoxLayout()
        password_label = QLabel("Şifre:")
        password_label.setStyleSheet("font-weight: bold; color: #666666;")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifrenizi Girin")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #e1e1e1;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
            }
        """)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        form_layout.addLayout(password_layout)
        
        # Giriş butonu
        login_btn = QPushButton("Giriş Yap")
        login_btn.setMinimumHeight(50)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2d6da3;
            }
        """)
        login_btn.clicked.connect(self.login)
        form_layout.addWidget(login_btn)
        
        form_frame.setLayout(form_layout)
        layout.addWidget(form_frame)
        
        self.setLayout(layout)

    def toggle_login_type(self, clicked_button):
        if clicked_button == self.doctor_btn:
            self.doctor_btn.setChecked(True)
            self.patient_btn.setChecked(False)
        else:
            self.doctor_btn.setChecked(False)
            self.patient_btn.setChecked(True)

    def login(self):
        tc = self.tc_input.text()
        password = self.password_input.text()
        
        if not tc or not password:
            QMessageBox.warning(self, "Uyarı", "Lütfen T.C. Kimlik No ve şifrenizi girin!")
            return
        
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            cursor = conn.cursor()
            
            if self.doctor_btn.isChecked():
                # Doktor girişi
                cursor.execute("""
                    SELECT u.user_id, d.doctor_id, u.password_hash
                    FROM users u
                    JOIN doctors d ON u.user_id = d.user_id
                    WHERE u.tc_identity_number = %s
                """, (tc,))
            else:
                # Hasta girişi
                cursor.execute("""
                    SELECT u.user_id, p.patient_id, u.password_hash
                    FROM users u
                    JOIN patients p ON u.user_id = p.user_id
                    WHERE u.tc_identity_number = %s AND p.is_active = true
                """, (tc,))
            
            result = cursor.fetchone()
            
            if result and bcrypt.checkpw(password.encode('utf-8'), result[2].encode('utf-8')):
                if self.doctor_btn.isChecked():
                    self.main_window.show_main_window(result[1], "doctor")
                else:
                    self.main_window.show_main_window(result[1], "patient")
            else:
                QMessageBox.warning(self, "Hata", "T.C. Kimlik No veya şifre hatalı!")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Giriş yapılırken bir hata oluştu: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diyabet Takip Sistemi")
        self.setMinimumSize(1200, 800)
        
        # Ana widget ve layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Stacked widget
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Login ekranı
        self.login_window = LoginWindow(self)
        self.stacked_widget.addWidget(self.login_window)
        
        # Başlangıçta login ekranını göster
        self.stacked_widget.setCurrentWidget(self.login_window)

    def show_main_window(self, user_id, user_type):
        # Mevcut doktor panelini temizle
        for i in range(self.stacked_widget.count() - 1):
            self.stacked_widget.removeWidget(self.stacked_widget.widget(1))
        
        if user_type == "doctor":
            # Doktor paneli
            doctor_panel = DoctorPanel(user_id)
            self.stacked_widget.addWidget(doctor_panel)
            self.stacked_widget.setCurrentWidget(doctor_panel)
        else:
            # Hasta paneli
            patient_panel = PatientPanel(user_id)
            self.stacked_widget.addWidget(patient_panel)
            self.stacked_widget.setCurrentWidget(patient_panel)

    def logout(self):
        # Mevcut paneli temizle
        for i in range(self.stacked_widget.count() - 1):
            self.stacked_widget.removeWidget(self.stacked_widget.widget(1))
        
        # Login ekranına dön
        self.stacked_widget.setCurrentWidget(self.login_window)

    def show_login_menu(self):
        """Giriş menüsünü göster"""
        # Mevcut paneli temizle
        for i in range(self.stacked_widget.count() - 1):
            self.stacked_widget.removeWidget(self.stacked_widget.widget(1))
        
        # Login ekranına dön
        self.stacked_widget.setCurrentWidget(self.login_window)
        
        # Giriş formunu temizle
        self.login_window.tc_input.clear()
        self.login_window.password_input.clear()

def main():
    app = QApplication(sys.argv)
    
    # Uygulama genel stili
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 