from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QFormLayout, QLineEdit, QTextEdit, QComboBox,
                            QMessageBox, QDialog, QDateEdit, QTabWidget,
                            QSpinBox, QDoubleSpinBox, QFrame, QGroupBox,
                            QListWidget, QListWidgetItem, QFileDialog)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QPixmap, QImage, QPainter, QPainterPath
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis, QPieSeries
from PyQt6.QtCore import QDateTime
import psycopg2
from datetime import datetime, timedelta
import bcrypt
from blood_sugar_dialog import BloodSugarMeasurementDialog
import base64
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

# Veritabanı bağlantı bilgileri
DB_CONFIG = {
    'dbname': 'diabetes_monitoring_system',
    'user': 'postgres',
    'password': 'your_password',  # PostgreSQL kurulumunda belirlediğiniz şifre
    'host': 'localhost',
    'port': '5432'
}

# Şifreleme anahtarı oluşturma
def generate_encryption_key():
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(b"your-secret-password"))
    return key

# Veri şifreleme
def encrypt_data(data):
    key = generate_encryption_key()
    f = Fernet(key)
    encrypted_data = f.encrypt(data.encode())
    return encrypted_data, key

# Veri şifre çözme
def decrypt_data(encrypted_data, key):
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data)
    return decrypted_data.decode()

# Hassas veriyi şifrele ve kaydet
def save_encrypted_data(table_name, record_id, data):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Veriyi şifrele
        encrypted_value, key = encrypt_data(data)
        
        # Şifrelenmiş veriyi kaydet
        cursor.execute("""
            INSERT INTO encrypted_data (table_name, record_id, encrypted_value, iv)
            VALUES (%s, %s, %s, %s)
        """, (table_name, record_id, encrypted_value, key))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Veri şifreleme hatası: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Şifrelenmiş veriyi oku
def read_encrypted_data(table_name, record_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT encrypted_value, iv
            FROM encrypted_data
            WHERE table_name = %s AND record_id = %s
        """, (table_name, record_id))
        
        result = cursor.fetchone()
        if result:
            encrypted_value, key = result
            return decrypt_data(encrypted_value, key)
        return None
    except Exception as e:
        print(f"Veri şifre çözme hatası: {str(e)}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Kullanıcı izinlerini kontrol et
def check_user_permission(user_id, permission_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*)
            FROM user_roles ur
            JOIN role_permissions rp ON ur.role_id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.permission_id
            WHERE ur.user_id = %s AND p.permission_name = %s
        """, (user_id, permission_name))
        
        return cursor.fetchone()[0] > 0
    except Exception as e:
        print(f"İzin kontrolü hatası: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# E-posta gönderme fonksiyonu
def send_welcome_email(recipient_email, tc_number, password):
    try:
        # E-posta ayarları
        sender_email = "projemail04@gmail.com"
        sender_password = "uqli foqs ijkl aaei"  # Gmail'den aldığınız 16 haneli uygulama şifresi
        
        # E-posta içeriği
        subject = "Diyabet Takip Sistemi - Hoş Geldiniz"
        body = f"""
        Sayın Kullanıcı,

        Diyabet Takip Sistemi'ne hoş geldiniz. Hesabınız başarıyla oluşturulmuştur.

        Giriş bilgileriniz:
        Kullanıcı Adı (T.C. Kimlik No): {tc_number}
        Şifre: {password}

        Güvenliğiniz için lütfen ilk girişinizde şifrenizi değiştirmeyi unutmayın.

        Sağlıklı günler dileriz.
        Diyabet Takip Sistemi
        """
        
        # E-posta oluşturma
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        
        message.attach(MIMEText(body, "plain"))
        
        # E-posta gönderme (SSL ile güvenli bağlantı)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
            
        return True
    except Exception as e:
        print(f"E-posta gönderme hatası: {str(e)}")
        return False

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Tabloları oluştur
        cursor = conn.cursor()
        
        # Kullanıcı rolleri tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                role_id SERIAL PRIMARY KEY,
                role_name VARCHAR(50) NOT NULL UNIQUE,
                description TEXT
            )
        """)
        
        # Kullanıcı-rol ilişki tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER REFERENCES users(user_id),
                role_id INTEGER REFERENCES roles(role_id),
                PRIMARY KEY (user_id, role_id)
            )
        """)
        
        # İzinler tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                permission_id SERIAL PRIMARY KEY,
                permission_name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT
            )
        """)
        
        # Rol-izin ilişki tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER REFERENCES roles(role_id),
                permission_id INTEGER REFERENCES permissions(permission_id),
                PRIMARY KEY (role_id, permission_id)
            )
        """)
        
        # Şifrelenmiş veri tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS encrypted_data (
                data_id SERIAL PRIMARY KEY,
                table_name VARCHAR(100) NOT NULL,
                record_id INTEGER NOT NULL,
                encrypted_value BYTEA NOT NULL,
                iv BYTEA NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Varsayılan rolleri ekle
        cursor.execute("""
            INSERT INTO roles (role_name, description) 
            VALUES 
                ('admin', 'Sistem yöneticisi'),
                ('doctor', 'Doktor'),
                ('patient', 'Hasta'),
                ('nurse', 'Hemşire')
            ON CONFLICT (role_name) DO NOTHING
        """)
        
        # Varsayılan izinleri ekle
        cursor.execute("""
            INSERT INTO permissions (permission_name, description) 
            VALUES 
                ('view_patient_data', 'Hasta verilerini görüntüleme'),
                ('edit_patient_data', 'Hasta verilerini düzenleme'),
                ('view_measurements', 'Ölçümleri görüntüleme'),
                ('add_measurements', 'Ölçüm ekleme'),
                ('view_recommendations', 'Önerileri görüntüleme'),
                ('add_recommendations', 'Öneri ekleme'),
                ('manage_users', 'Kullanıcı yönetimi'),
                ('view_reports', 'Raporları görüntüleme')
            ON CONFLICT (permission_name) DO NOTHING
        """)
        
        # Rol-izin ilişkilerini ekle
        cursor.execute("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.role_id, p.permission_id
            FROM roles r
            CROSS JOIN permissions p
            WHERE r.role_name = 'admin'
            ON CONFLICT DO NOTHING
        """)
        
        # Doktor izinlerini ekle
        cursor.execute("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.role_id, p.permission_id
            FROM roles r
            CROSS JOIN permissions p
            WHERE r.role_name = 'doctor'
            AND p.permission_name IN (
                'view_patient_data', 'edit_patient_data', 
                'view_measurements', 'add_measurements',
                'view_recommendations', 'add_recommendations',
                'view_reports'
            )
            ON CONFLICT DO NOTHING
        """)
        
        # Hasta izinlerini ekle
        cursor.execute("""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.role_id, p.permission_id
            FROM roles r
            CROSS JOIN permissions p
            WHERE r.role_name = 'patient'
            AND p.permission_name IN (
                'view_patient_data', 'view_measurements',
                'view_recommendations'
            )
            ON CONFLICT DO NOTHING
        """)
        
        conn.commit()
        cursor.close()
        
        return conn
    except psycopg2.Error as e:
        QMessageBox.critical(None, "Veritabanı Bağlantı Hatası", 
                           f"Veritabanına bağlanırken hata oluştu:\n{str(e)}")
        return None

class PatientManagement(QWidget):
    def __init__(self, doctor_id):
        super().__init__()
        self.doctor_id = doctor_id
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Başlık
        title = QLabel("Hasta Yönetimi")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        
        # Yeni hasta ekle butonu
        add_patient_btn = QPushButton("Yeni Hasta Ekle")
        add_patient_btn.clicked.connect(self.show_add_patient_dialog)
        
        # Hasta tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["T.C. No", "Ad Soyad", "E-posta", "Tanı Tarihi", "Diyabet Tipi", "Durum"])
        self.load_patients()
        
        layout.addWidget(title)
        layout.addWidget(add_patient_btn)
        layout.addWidget(self.table)
        
        self.setLayout(layout)

    def show_add_patient_dialog(self):
        dialog = AddPatientDialog(self.doctor_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_patients()

    def load_patients(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.tc_identity_number, u.email, p.diagnosis_date, p.diabetes_type, p.is_active
                FROM patients p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.doctor_id = %s
                ORDER BY p.diagnosis_date DESC
            """, (self.doctor_id,))
            
            patients = cursor.fetchall()
            
            self.table.setRowCount(len(patients))
            for row, patient in enumerate(patients):
                for col, value in enumerate(patient):
                    if col == 4:  # is_active
                        status = "Aktif" if value else "Pasif"
                        item = QTableWidgetItem(status)
                    else:
                        item = QTableWidgetItem(str(value))
                    self.table.setItem(row, col, item)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

class AddPatientDialog(QDialog):
    def __init__(self, doctor_id, parent=None):
        super().__init__(parent)
        self.doctor_id = doctor_id
        self.setWindowTitle("Yeni Hasta Ekle")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # TC Kimlik No
        self.tc_input = QLineEdit()
        self.tc_input.setPlaceholderText("T.C. Kimlik Numarası")
        layout.addWidget(QLabel("T.C. Kimlik No:"))
        layout.addWidget(self.tc_input)

        # Şifre
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Şifre:"))
        layout.addWidget(self.password_input)

        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email_input)

        # Doğum Tarihi
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setDate(QDate.currentDate())
        layout.addWidget(QLabel("Doğum Tarihi:"))
        layout.addWidget(self.birth_date_input)

        # Cinsiyet
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["E", "K"])
        layout.addWidget(QLabel("Cinsiyet:"))
        layout.addWidget(self.gender_combo)

        # Diyabet Tipi
        self.diabetes_type_combo = QComboBox()
        self.diabetes_type_combo.addItems(["Tip 1", "Tip 2", "Gestasyonel"])
        layout.addWidget(QLabel("Diyabet Tipi:"))
        layout.addWidget(self.diabetes_type_combo)

        # Teşhis Tarihi
        self.diagnosis_date_input = QDateEdit()
        self.diagnosis_date_input.setDate(QDate.currentDate())
        layout.addWidget(QLabel("Teşhis Tarihi:"))
        layout.addWidget(self.diagnosis_date_input)

        # Kaydet Butonu
        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.save_patient)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def save_patient(self):
        tc = self.tc_input.text()
        password = self.password_input.text()
        email = self.email_input.text()
        birth_date = self.birth_date_input.date().toPyDate()
        gender = self.gender_combo.currentText()
        diabetes_type = self.diabetes_type_combo.currentText()
        diagnosis_date = self.diagnosis_date_input.date().toPyDate()
        
        if not all([tc, password, email, birth_date, gender, diabetes_type, diagnosis_date]):
            QMessageBox.warning(self, "Hata", "Lütfen tüm alanları doldurun!")
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # TC kimlik numarası kontrolü
            cursor.execute("SELECT user_id FROM users WHERE tc_identity_number = %s", (tc,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Hata", "Bu TC kimlik numarası zaten kullanımda!")
                return
            
            # Email kontrolü
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Hata", "Bu email adresi zaten kullanımda!")
                return
            
            # Şifreyi hashle
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Kullanıcıyı ekle
            cursor.execute("""
                INSERT INTO users (tc_identity_number, password_hash, email, birth_date, gender)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING user_id
            """, (tc, password_hash.decode('utf-8'), email, birth_date, gender))
            
            user_id = cursor.fetchone()[0]
            
            # Hastayı ekle
            cursor.execute("""
                INSERT INTO patients (user_id, doctor_id, diagnosis_date, diabetes_type, is_active)
                VALUES (%s, %s, %s, %s, true)
            """, (user_id, self.doctor_id, diagnosis_date, diabetes_type))
            
            conn.commit()
            
            # Hoş geldin e-postası gönder
            if send_welcome_email(email, tc, password):
                QMessageBox.information(self, "Başarılı", 
                    "Hasta başarıyla eklendi ve giriş bilgileri e-posta ile gönderildi!")
            else:
                QMessageBox.warning(self, "Uyarı", 
                    "Hasta başarıyla eklendi ancak e-posta gönderilemedi. Lütfen giriş bilgilerini manuel olarak iletin.")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veritabanı hatası: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

class PatientMeasurements(QWidget):
    def __init__(self, doctor_id):
        super().__init__()
        self.doctor_id = doctor_id
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Başlık
        title = QLabel("Hasta Ölçümleri")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        
        # Hasta seçimi
        self.patient_combo = QComboBox()
        self.load_patients()
        self.patient_combo.currentIndexChanged.connect(self.load_measurements)
        
        # Ölçüm tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Tarih", "Kan Şekeri"])
        
        layout.addWidget(title)
        layout.addWidget(QLabel("Hasta Seçin:"))
        layout.addWidget(self.patient_combo)
        layout.addWidget(self.table)
        
        self.setLayout(layout)

    def load_patients(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.patient_id, u.tc_identity_number, u.email
                FROM patients p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.doctor_id = %s AND p.is_active = true
                ORDER BY u.tc_identity_number
            """, (self.doctor_id,))
            
            patients = cursor.fetchall()
            
            self.patient_combo.clear()
            self.patients_data = {f"{patient[1]} - {patient[2]}": patient[0] for patient in patients}
            self.patient_combo.addItems(self.patients_data.keys())
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hastalar yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def load_measurements(self):
        try:
            if not self.patient_combo.currentText():
                self.table.setRowCount(0)
                return
                
            patient_id = self.patient_combo.currentData()
            
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Son 7 günün ölçümlerini al
            cursor.execute("""
                SELECT 
                    DATE(m.measurement_date) as measurement_day,
                    EXTRACT(HOUR FROM m.measurement_date) as measurement_hour,
                    m.blood_sugar_level
                FROM measurements m
                WHERE m.patient_id = %s 
                AND m.measurement_date >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY measurement_day DESC, measurement_hour ASC
            """, (patient_id,))
            
            measurements = cursor.fetchall()
            
            # Son 7 günü oluştur
            today = datetime.now().date()
            days = [(today - timedelta(days=i)) for i in range(7)]
            
            # Ölçüm saatleri
            measurement_hours = [7, 12, 15, 18, 22]  # Sabah, Öğle, İkindi, Akşam, Gece
            
            # Tabloyu hazırla
            self.table.setColumnCount(len(measurement_hours) + 1)  # +1 for date column
            self.table.setRowCount(len(days))
            
            # Başlıkları ayarla
            headers = ["Tarih"]
            for hour in measurement_hours:
                if hour == 7:
                    headers.append("Sabah (07:00)")
                elif hour == 12:
                    headers.append("Öğle (12:00)")
                elif hour == 15:
                    headers.append("İkindi (15:00)")
                elif hour == 18:
                    headers.append("Akşam (18:00)")
                elif hour == 22:
                    headers.append("Gece (22:00)")
            headers.append("Günlük Ortalama")
            self.table.setHorizontalHeaderLabels(headers)
            
            # Ölçümleri düzenle
            measurements_dict = {}
            for day, hour, value in measurements:
                if day not in measurements_dict:
                    measurements_dict[day] = {}
                measurements_dict[day][hour] = value
            
            # Tabloyu doldur
            for row, day in enumerate(days):
                # Tarih
                date_item = QTableWidgetItem(day.strftime("%d.%m.%Y"))
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, date_item)
                
                # Günlük değerleri toplamak için
                daily_values = []
                
                # Her saat için ölçüm değerini kontrol et
                for col, hour in enumerate(measurement_hours, start=1):
                    if day in measurements_dict and hour in measurements_dict[day]:
                        blood_sugar = measurements_dict[day][hour]
                        if blood_sugar is not None:
                            sugar_item = QTableWidgetItem(f"{blood_sugar} mg/dL")
                            sugar_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            daily_values.append(blood_sugar)
                            
                            # Kan şekeri seviyesine göre renklendirme
                            if blood_sugar < 70:
                                sugar_item.setBackground(QColor("#dc3545"))  # Kırmızı - Düşük
                                sugar_item.setForeground(QColor("white"))
                            elif 70 <= blood_sugar <= 99:
                                sugar_item.setBackground(QColor("#28a745"))  # Yeşil - Normal
                                sugar_item.setForeground(QColor("white"))
                            elif 100 <= blood_sugar <= 125:
                                sugar_item.setBackground(QColor("#ffc107"))  # Sarı - Orta
                                sugar_item.setForeground(QColor("black"))
                            else:
                                sugar_item.setBackground(QColor("#dc3545"))  # Kırmızı - Yüksek
                                sugar_item.setForeground(QColor("white"))
                        else:
                            sugar_item = QTableWidgetItem("Ölçüm yok")
                            sugar_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            sugar_item.setBackground(QColor("#6c757d"))  # Gri
                            sugar_item.setForeground(QColor("white"))
                    else:
                        sugar_item = QTableWidgetItem("⚠️ Ölçüm yapılmamış")
                        sugar_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        sugar_item.setBackground(QColor("#ffc107"))  # Sarı - Uyarı
                        sugar_item.setForeground(QColor("black"))
                    
                    self.table.setItem(row, col, sugar_item)
                
                # Günlük ortalama hesapla ve göster
                if daily_values:
                    daily_avg = sum(daily_values) / len(daily_values)
                    avg_item = QTableWidgetItem(f"{daily_avg:.1f} mg/dL")
                    avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # Ortalama değere göre renklendirme
                    if daily_avg < 70:
                        avg_item.setBackground(QColor("#dc3545"))  # Kırmızı - Düşük
                        avg_item.setForeground(QColor("white"))
                    elif 70 <= daily_avg <= 99:
                        avg_item.setBackground(QColor("#28a745"))  # Yeşil - Normal
                        avg_item.setForeground(QColor("white"))
                    elif 100 <= daily_avg <= 125:
                        avg_item.setBackground(QColor("#ffc107"))  # Sarı - Orta
                        avg_item.setForeground(QColor("black"))
                    else:
                        avg_item.setBackground(QColor("#dc3545"))  # Kırmızı - Yüksek
                        avg_item.setForeground(QColor("white"))
                else:
                    avg_item = QTableWidgetItem("Ölçüm yok")
                    avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    avg_item.setBackground(QColor("#6c757d"))  # Gri
                    avg_item.setForeground(QColor("white"))
                
                self.table.setItem(row, len(measurement_hours) + 1, avg_item)
            
            # Sütun genişliklerini ayarla
            self.table.resizeColumnsToContents()
            self.table.horizontalHeader().setStretchLastSection(True)
            
            # Minimum sütun genişliklerini ayarla
            for i in range(self.table.columnCount()):
                self.table.setColumnWidth(i, 120)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ölçümler yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

class Recommendations(QWidget):
    def __init__(self, doctor_id):
        super().__init__()
        self.doctor_id = doctor_id
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Başlık
        title = QLabel("Hasta Önerileri")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        
        # Hasta seçimi
        self.patient_combo = QComboBox()
        self.load_patients()
        
        # Öneri formu
        form_layout = QFormLayout()
        
        self.recommendation_type = QComboBox()
        self.recommendation_type.addItems([
            "💊 İlaç", "🥗 Beslenme", "🏃‍♂️ Egzersiz", 
            "📋 Kontrol", "📝 Diğer"
        ])
        self.recommendation_type.setMinimumHeight(35)
        self.recommendation_type.currentTextChanged.connect(self.update_recommendation_content)
        
        # Alt tür seçimi için ComboBox
        self.subtype_combo = QComboBox()
        self.subtype_combo.setMinimumHeight(35)
        self.subtype_combo.currentTextChanged.connect(self.update_subtype_content)
        
        self.recommendation_content = QTextEdit()
        self.recommendation_content.setMinimumHeight(100)
        
        send_btn = QPushButton("📤 Öneri Gönder")
        send_btn.setMinimumHeight(40)
        send_btn.clicked.connect(self.save_recommendation)
        
        form_layout.addRow("Hasta:", self.patient_combo)
        form_layout.addRow("Öneri Tipi:", self.recommendation_type)
        form_layout.addRow("Alt Tür:", self.subtype_combo)
        form_layout.addRow("İçerik:", self.recommendation_content)
        form_layout.addRow(send_btn)
        
        # Öneri tablosu
        self.recommendations_table = QTableWidget()
        self.recommendations_table.setColumnCount(4)
        self.recommendations_table.setHorizontalHeaderLabels(["Tarih", "Hasta", "Tür", "İçerik"])
        self.load_recommendations()
        
        layout.addWidget(title)
        layout.addLayout(form_layout)
        layout.addWidget(self.recommendations_table)
        
        self.setLayout(layout)

    def load_patients(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.patient_id, u.tc_identity_number
                FROM patients p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.doctor_id = %s
                ORDER BY u.tc_identity_number
            """, (self.doctor_id,))
            
            patients = cursor.fetchall()
            
            self.patient_combo.clear()
            self.patients_data = {f"{patient[1]}": patient[0] for patient in patients}
            self.patient_combo.addItems(self.patients_data.keys())
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hastalar yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def save_recommendation(self):
        if not self.patient_combo.currentText():
            QMessageBox.warning(self, "Uyarı", "Lütfen bir hasta seçin!")
            return
            
        patient_id = self.patients_data[self.patient_combo.currentText()]
        
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO doctor_recommendations (doctor_id, patient_id, recommendation_type, content)
                VALUES (%s, %s, %s, %s)
            """, (self.doctor_id, patient_id, self.recommendation_type.currentText(),
                  self.recommendation_content.toPlainText()))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            QMessageBox.information(self, "Başarılı", "Öneri başarıyla gönderildi!")
            self.load_recommendations()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Öneri gönderilirken hata oluştu: {str(e)}")

    def load_recommendations(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT r.created_at, u.tc_identity_number, r.recommendation_type, r.content
                FROM doctor_recommendations r
                JOIN patients p ON r.patient_id = p.patient_id
                JOIN users u ON p.user_id = u.user_id
                WHERE r.doctor_id = %s
                ORDER BY r.created_at DESC
            """, (self.doctor_id,))
            
            recommendations = cursor.fetchall()
            
            self.recommendations_table.setRowCount(len(recommendations))
            for row, recommendation in enumerate(recommendations):
                # Tarih
                date_item = QTableWidgetItem(recommendation[0].strftime("%d.%m.%Y %H:%M"))
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.recommendations_table.setItem(row, 0, date_item)
                
                # Hasta
                patient_item = QTableWidgetItem(recommendation[1])
                patient_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.recommendations_table.setItem(row, 1, patient_item)
                
                # Tür
                type_item = QTableWidgetItem(recommendation[2])
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.recommendations_table.setItem(row, 2, type_item)
                
                # İçerik
                content_item = QTableWidgetItem(recommendation[3])
                content_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # İçeriği daha okunaklı hale getir
                content = recommendation[3].replace('\n', ' | ')
                content_item = QTableWidgetItem(content)
                content_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.recommendations_table.setItem(row, 3, content_item)
            
            # Sütun genişliklerini ayarla
            self.recommendations_table.resizeColumnsToContents()
            self.recommendations_table.horizontalHeader().setStretchLastSection(True)
            
            # Minimum sütun genişliklerini ayarla
            self.recommendations_table.setColumnWidth(0, 150)  # Tarih
            self.recommendations_table.setColumnWidth(1, 150)  # Hasta
            self.recommendations_table.setColumnWidth(2, 200)  # Tür
            self.recommendations_table.setColumnWidth(3, 400)  # İçerik
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Öneriler yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def update_recommendation_content(self, recommendation_type):
        """Öneri türüne göre alt türleri güncelle"""
        self.subtype_combo.clear()
        
        if recommendation_type == "🥗 Beslenme":
            self.subtype_combo.addItems([
                "Az Şekerli Diyet",
                "Şekersiz Diyet",
                "Dengeli Beslenme"
            ])
            self.subtype_combo.setVisible(True)
            
        elif recommendation_type == "🏃‍♂️ Egzersiz":
            self.subtype_combo.addItems([
                "Yürüyüş",
                "Bisiklet",
                "Klinik Egzersiz"
            ])
            self.subtype_combo.setVisible(True)
            
        else:
            self.subtype_combo.setVisible(False)
            self.recommendation_content.clear()

    def update_subtype_content(self, subtype):
        """Seçilen alt türe göre içerik şablonunu güncelle"""
        if not subtype:
            return
            
        if self.recommendation_type.currentText() == "🥗 Beslenme":
            if subtype == "Az Şekerli Diyet":
                content = """Az Şekerli Diyet Önerileri:
- Şekerli gıdalar sınırlanmalıdır
- Kompleks karbonhidratlara öncelik verilmelidir
- Lifli gıdalar ve düşük glisemik indeksli besinler tercih edilmelidir

Lütfen hastanız için özel önerilerinizi ekleyin:"""
                
            elif subtype == "Şekersiz Diyet":
                content = """Şekersiz Diyet Önerileri:
- Rafine şeker ve şeker katkılı tüm ürünler tamamen dışlanmalıdır
- Doğal tatlandırıcılar kullanılabilir
- Meyve tüketimi kontrollü olmalıdır

Lütfen hastanız için özel önerilerinizi ekleyin:"""
                
            else:  # Dengeli Beslenme
                content = """Dengeli Beslenme Önerileri:
- Tüm besin gruplarından yeterli miktarda alınmalıdır
- Porsiyon kontrolü önemlidir
- Mevsimsel taze ürünler tercih edilmelidir
- Su tüketimi günlük en az 2-2.5 litre olmalıdır

Lütfen hastanız için özel önerilerinizi ekleyin:"""
                
        elif self.recommendation_type.currentText() == "🏃‍♂️ Egzersiz":
            if subtype == "Yürüyüş":
                content = """Yürüyüş Programı:
- Hafif tempolu, günlük yapılabilecek bir egzersizdir
- Başlangıç için ideal bir seçenektir
- Günde 30 dakika önerilir
- Sabah veya akşam saatlerinde yapılabilir

Lütfen hastanız için özel önerilerinizi ekleyin:"""
                
            elif subtype == "Bisiklet":
                content = """Bisiklet Programı:
- Alt vücut kaslarını çalıştırır
- Dış mekanda veya sabit bisikletle uygulanabilir
- Haftada 3-4 gün, 20-30 dakika önerilir
- Başlangıçta düşük tempo ile başlanmalıdır

Lütfen hastanız için özel önerilerinizi ekleyin:"""
                
            else:  # Klinik Egzersiz
                content = """Klinik Egzersiz Programı:
- Doktor tarafından verilen belirli hareketleri içerir
- Stresi azaltmaya yardımcı olur
- Hareket kabiliyetini artırır
- Düzenli olarak yapılmalıdır
- Her hareket 10-15 tekrar ile başlanmalıdır

Lütfen hastanız için özel önerilerinizi ekleyin:"""
                
        else:
            content = ""
            
        self.recommendation_content.setPlainText(content)

class SymptomManagement(QWidget):
    def __init__(self, doctor_id):
        super().__init__()
        self.doctor_id = doctor_id
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Başlık
        title = QLabel("Hasta Belirtileri")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px;")
        
        # Hasta seçimi
        self.patient_combo = QComboBox()
        self.load_patients()
        
        # Belirti seçimi için liste
        self.symptom_list = QListWidget()
        self.symptom_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.load_symptoms()
        
        # Notlar
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notlar...")
        
        # Kaydet butonu
        save_btn = QPushButton("Belirtileri Kaydet")
        save_btn.clicked.connect(self.save_symptoms)
        
        # Belirti tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Tarih", "Hasta", "Belirti", "Notlar"])
        
        # Layout düzenleme
        form_layout = QFormLayout()
        form_layout.addRow("Hasta:", self.patient_combo)
        form_layout.addRow("Belirtiler (Birden fazla seçebilirsiniz):", self.symptom_list)
        form_layout.addRow("Notlar:", self.notes_edit)
        
        layout.addWidget(title)
        layout.addLayout(form_layout)
        layout.addWidget(save_btn)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
        # Hasta seçildiğinde belirtileri güncelle
        self.patient_combo.currentIndexChanged.connect(self.load_patient_symptoms)

    def load_patients(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.patient_id, u.tc_identity_number, u.email 
                FROM patients p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.doctor_id = %s
                ORDER BY u.tc_identity_number
            """, (self.doctor_id,))
            
            patients = cursor.fetchall()
            self.patient_combo.clear()
            for patient in patients:
                self.patient_combo.addItem(f"{patient[1]} - {patient[2]}", patient[0])
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veriler yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def load_symptoms(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("SELECT symptom_id, name, description FROM symptoms ORDER BY name")
            symptoms = cursor.fetchall()
            
            self.symptom_list.clear()
            for symptom in symptoms:
                item = QListWidgetItem(f"{symptom[1]} - {symptom[2]}")
                item.setData(Qt.ItemDataRole.UserRole, symptom[0])  # symptom_id'yi item'a ekle
                self.symptom_list.addItem(item)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Belirtiler yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def load_patient_symptoms(self):
        try:
            patient_id = self.patient_combo.currentData()
            if not patient_id:
                return
                
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ps.date_added, u.tc_identity_number, u.email, s.name, ps.notes
                FROM patient_symptoms ps
                JOIN patients p ON ps.patient_id = p.patient_id
                JOIN users u ON p.user_id = u.user_id
                JOIN symptoms s ON ps.symptom_id = s.symptom_id
                WHERE ps.patient_id = %s
                ORDER BY ps.date_added DESC
            """, (patient_id,))
            
            symptoms = cursor.fetchall()
            
            self.table.setRowCount(len(symptoms))
            for row, symptom in enumerate(symptoms):
                for col, value in enumerate(symptom):
                    if col == 0:  # Tarih
                        value = value.strftime("%Y-%m-%d %H:%M")
                    elif col == 1:  # TC No
                        value = f"{symptom[1]} - {symptom[2]}"
                        continue
                    elif col == 2:  # Belirti
                        value = symptom[3]
                        continue
                    elif col == 3:  # Notlar
                        value = symptom[4]
                        continue
                    item = QTableWidgetItem(str(value))
                    self.table.setItem(row, col, item)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Belirtiler yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def save_symptoms(self):
        patient_id = self.patient_combo.currentData()
        selected_items = self.symptom_list.selectedItems()
        notes = self.notes_edit.toPlainText()
        
        if not patient_id or not selected_items:
            QMessageBox.warning(self, "Hata", "Lütfen hasta ve en az bir belirti seçin!")
            return
        
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Seçilen her belirti için kayıt ekle
            for item in selected_items:
                symptom_id = item.data(Qt.ItemDataRole.UserRole)
                cursor.execute("""
                    INSERT INTO patient_symptoms (patient_id, symptom_id, notes)
                    VALUES (%s, %s, %s)
                """, (patient_id, symptom_id, notes))
            
            conn.commit()
            QMessageBox.information(self, "Başarılı", f"{len(selected_items)} belirti başarıyla kaydedildi!")
            self.notes_edit.clear()
            self.symptom_list.clearSelection()
            self.load_patient_symptoms()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Belirtiler kaydedilirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

class DoctorPanel(QWidget):
    def __init__(self, doctor_id):
        super().__init__()
        self.doctor_id = doctor_id
        self.setup_styles()
        self.setup_ui()
        self.load_doctor_info()
        self.load_patients()
        self.load_recommendations()

    def setup_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f2f5;
                font-family: 'Segoe UI', Arial;
            }
            QLabel {
                color: #1a1a1a;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #e1e1e1;
                border-radius: 5px;
                gridline-color: #f0f0f0;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 10px;
                min-height: 40px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #4a90e2;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton {
                padding: 10px 20px;
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2d6da3;
            }
            QPushButton#addButton {
                background-color: #28a745;
                min-width: 180px;
                font-size: 15px;
            }
            QPushButton#addButton:hover {
                background-color: #218838;
            }
            QPushButton#addButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton#measurementButton {
                background-color: #17a2b8;
                min-width: 140px;
                font-size: 14px;
            }
            QPushButton#measurementButton:hover {
                background-color: #138496;
            }
            QPushButton#measurementButton:pressed {
                background-color: #117a8b;
            }
            QPushButton#recommendationButton {
                background-color: #6f42c1;
                min-width: 140px;
                font-size: 14px;
            }
            QPushButton#recommendationButton:hover {
                background-color: #5a32a3;
            }
            QPushButton#recommendationButton:pressed {
                background-color: #4b2e8a;
            }
            QPushButton#historyButton {
                background-color: #fd7e14;
                min-width: 140px;
                font-size: 14px;
            }
            QPushButton#historyButton:hover {
                background-color: #e76a00;
            }
            QPushButton#historyButton:pressed {
                background-color: #d65f00;
            }
            QPushButton#deleteButton {
                background-color: #dc3545;
                min-width: 140px;
                font-size: 14px;
            }
            QPushButton#deleteButton:hover {
                background-color: #c82333;
            }
            QPushButton#deleteButton:pressed {
                background-color: #bd2130;
            }
            QTabWidget::pane {
                border: 1px solid #e1e1e1;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                color: #666666;
                padding: 10px 25px;
                border: 1px solid #e1e1e1;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #4a90e2;
                border-bottom: 2px solid #4a90e2;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e9ecef;
            }
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
                padding: 10px;
                border: 2px solid #e1e1e1;
                border-radius: 4px;
                background-color: white;
                font-size: 14px;
                min-height: 40px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 2px solid #4a90e2;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 15px;
                height: 15px;
            }
        """)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # ComboBox'ları tanımla
        self.patient_combo = QComboBox()
        self.recommendation_patient = QComboBox()
        self.analysis_patient_combo = QComboBox()

        # Üst Bilgi Paneli
        info_panel = QFrame()
        info_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        """)
        info_layout = QHBoxLayout()
        
        # Profil Resmi
        self.profile_image_label = QLabel()
        self.profile_image_label.setFixedSize(100, 100)
        self.profile_image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #4a90e2;
                border-radius: 50px;
                background-color: #f8f9fa;
            }
        """)
        self.profile_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_profile_image()
        
        # Profil resmi değiştirme butonu
        change_photo_btn = QPushButton("📷 Fotoğraf Değiştir")
        change_photo_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        change_photo_btn.clicked.connect(self.change_profile_image)
        
        # Profil resmi ve buton için container
        profile_container = QVBoxLayout()
        profile_container.addWidget(self.profile_image_label)
        profile_container.addWidget(change_photo_btn)
        profile_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        info_layout.addLayout(profile_container)
        
        # Doktor Bilgileri
        self.doctor_info_label = QLabel()
        self.doctor_info_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #4a90e2;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
        """)
        info_layout.addWidget(self.doctor_info_label)
        
        # Çıkış Butonu
        logout_btn = QPushButton("🚪 Çıkış Yap")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        logout_btn.clicked.connect(self.logout)
        info_layout.addWidget(logout_btn)
        
        info_panel.setLayout(info_layout)
        layout.addWidget(info_panel)

        # Tab Widget
        tabs = QTabWidget()
        
        # Hasta Listesi Tab'ı
        patients_tab = QWidget()
        patients_layout = QVBoxLayout()
        
        # Hasta arama
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Hasta Ara (T.C. Kimlik No veya İsim)")
        self.search_input.textChanged.connect(self.filter_patients)
        search_layout.addWidget(self.search_input)
        patients_layout.addLayout(search_layout)
        
        # Hasta tablosu
        self.patients_table = QTableWidget()
        self.patients_table.setColumnCount(6)
        self.patients_table.setHorizontalHeaderLabels([
            "T.C. Kimlik No", "İsim", "Diyabet Tipi", 
            "Teşhis Tarihi", "Son Ölçüm", "İşlemler"
        ])
        self.patients_table.horizontalHeader().setStretchLastSection(True)
        self.patients_table.itemDoubleClicked.connect(self.show_patient_details)
        patients_layout.addWidget(self.patients_table)
        
        patients_tab.setLayout(patients_layout)
        tabs.addTab(patients_tab, "👥 Hastalarım")

        # Hasta Takip Tab'ı
        tracking_tab = QWidget()
        tracking_layout = QVBoxLayout()
        
        # Hasta seçimi
        patient_select_layout = QHBoxLayout()
        patient_label = QLabel("Hasta Seçin:")
        self.tracking_patient_combo = QComboBox()
        self.tracking_patient_combo.setMinimumHeight(35)
        self.tracking_patient_combo.currentIndexChanged.connect(self.load_patient_tracking)
        patient_select_layout.addWidget(patient_label)
        patient_select_layout.addWidget(self.tracking_patient_combo)
        tracking_layout.addLayout(patient_select_layout)
        
        # İstatistik kartları
        stats_layout = QHBoxLayout()
        
        # Egzersiz istatistikleri
        exercise_group = QGroupBox("Egzersiz İstatistikleri")
        exercise_layout = QVBoxLayout()
        self.exercise_chart = QChart()
        self.exercise_chart.setTitle("Egzersiz Uygulama Oranı")
        self.exercise_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.exercise_view = QChartView(self.exercise_chart)
        self.exercise_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        exercise_layout.addWidget(self.exercise_view)
        exercise_group.setLayout(exercise_layout)
        stats_layout.addWidget(exercise_group)
        
        # Diyet istatistikleri
        diet_group = QGroupBox("Diyet İstatistikleri")
        diet_layout = QVBoxLayout()
        self.diet_chart = QChart()
        self.diet_chart.setTitle("Diyet Uygulama Oranı")
        self.diet_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.diet_view = QChartView(self.diet_chart)
        self.diet_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        diet_layout.addWidget(self.diet_view)
        diet_group.setLayout(diet_layout)
        stats_layout.addWidget(diet_group)
        
        tracking_layout.addLayout(stats_layout)
        
        # Detaylı takip tablosu
        self.tracking_table = QTableWidget()
        self.tracking_table.setColumnCount(4)
        self.tracking_table.setHorizontalHeaderLabels([
            "Tarih", "Egzersiz", "Diyet", "Notlar"
        ])
        self.tracking_table.horizontalHeader().setStretchLastSection(True)
        tracking_layout.addWidget(self.tracking_table)
        
        tracking_tab.setLayout(tracking_layout)
        tabs.addTab(tracking_tab, "📊 Hasta Takibi")

        # Hasta Yönetimi Tab'ı
        patient_management_tab = QWidget()
        patient_management_layout = QVBoxLayout()
        
        # Hasta Ekleme Butonu
        add_patient_btn = QPushButton("➕ Yeni Hasta Ekle")
        add_patient_btn.setMinimumHeight(40)
        add_patient_btn.clicked.connect(self.show_add_patient_dialog)
        patient_management_layout.addWidget(add_patient_btn)
        
        # Hasta Bilgileri Tablosu
        self.patient_info_table = QTableWidget()
        self.patient_info_table.setColumnCount(6)
        self.patient_info_table.setHorizontalHeaderLabels([
            "TC Kimlik No", "E-posta", "Diyabet Tipi", 
            "Teşhis Tarihi", "Belirtiler", "İşlemler"
        ])
        self.patient_info_table.horizontalHeader().setStretchLastSection(True)
        
        patient_management_layout.addWidget(self.patient_info_table)
        patient_management_tab.setLayout(patient_management_layout)
        tabs.addTab(patient_management_tab, "👥 Hasta Yönetimi")

        # Ölçümler Tab'ı
        measurements_tab = QWidget()
        measurements_layout = QVBoxLayout()
        
        # Hasta Seçimi ve Ölçüm Ekleme
        measurement_header = QHBoxLayout()
        self.patient_combo.setMinimumHeight(35)
        self.patient_combo.currentIndexChanged.connect(self.load_measurements)
        
        add_measurement_btn = QPushButton("➕ Yeni Ölçüm Ekle")
        add_measurement_btn.setMinimumHeight(35)
        add_measurement_btn.clicked.connect(self.show_add_measurement_dialog)
        
        measurement_header.addWidget(QLabel("Hasta:"))
        measurement_header.addWidget(self.patient_combo)
        measurement_header.addWidget(add_measurement_btn)
        
        measurements_layout.addLayout(measurement_header)
        
        # Ölçüm Tablosu
        self.measurements_table = QTableWidget()
        self.measurements_table.setColumnCount(2)
        self.measurements_table.setHorizontalHeaderLabels([
            "Tarih", "Kan Şekeri"
        ])
        self.measurements_table.horizontalHeader().setStretchLastSection(True)
        
        measurements_layout.addWidget(self.measurements_table)
        measurements_tab.setLayout(measurements_layout)
        tabs.addTab(measurements_tab, "📊 Ölçümler")

        # Öneriler Tab'ı
        recommendations_tab = QWidget()
        recommendations_layout = QVBoxLayout()
        
        # Öneri Formu
        form_group = QGroupBox("Yeni Öneri")
        form_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                color: #4a90e2;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        form_layout = QFormLayout()
        
        self.recommendation_patient.setMinimumHeight(35)
        
        self.recommendation_type = QComboBox()
        self.recommendation_type.addItems([
            "💊 İlaç", "🥗 Beslenme", "🏃‍♂️ Egzersiz", 
            "📋 Kontrol", "📝 Diğer"
        ])
        self.recommendation_type.setMinimumHeight(35)
        self.recommendation_type.currentTextChanged.connect(self.update_recommendation_content)
        
        # Alt tür seçimi için ComboBox
        self.subtype_combo = QComboBox()
        self.subtype_combo.setMinimumHeight(35)
        self.subtype_combo.currentTextChanged.connect(self.update_subtype_content)
        
        self.recommendation_content = QTextEdit()
        self.recommendation_content.setMinimumHeight(100)
        
        send_btn = QPushButton("📤 Öneri Gönder")
        send_btn.setMinimumHeight(40)
        send_btn.clicked.connect(self.save_recommendation)
        
        form_layout.addRow("Hasta:", self.recommendation_patient)
        form_layout.addRow("Öneri Tipi:", self.recommendation_type)
        form_layout.addRow("Alt Tür:", self.subtype_combo)
        form_layout.addRow("İçerik:", self.recommendation_content)
        form_layout.addRow(send_btn)
        
        form_group.setLayout(form_layout)
        recommendations_layout.addWidget(form_group)
        
        # Öneri Tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Tarih", "Hasta", "Tür", "İçerik"
        ])
        self.load_recommendations()
        
        recommendations_layout.addWidget(self.table)
        recommendations_tab.setLayout(recommendations_layout)
        tabs.addTab(recommendations_tab, "💡 Öneriler")

        # Belirtiler Tab'ı
        self.symptom_tab = SymptomManagement(self.doctor_id)
        tabs.addTab(self.symptom_tab, "🔍 Belirtiler")

        # Hasta Analizi Tab'ı
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout()
        
        # Hasta Seçimi
        analysis_header = QHBoxLayout()
        self.analysis_patient_combo.setMinimumHeight(35)
        self.analysis_patient_combo.currentIndexChanged.connect(self.load_patient_analysis)
        
        analysis_header.addWidget(QLabel("Hasta:"))
        analysis_header.addWidget(self.analysis_patient_combo)
        
        analysis_layout.addLayout(analysis_header)
        
        # Analiz Tablosu
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(4)
        self.analysis_table.setHorizontalHeaderLabels([
            "Özellik", "Değer", "Normal Aralık", "Durum"
        ])
        self.analysis_table.horizontalHeader().setStretchLastSection(True)
        
        analysis_layout.addWidget(self.analysis_table)
        analysis_tab.setLayout(analysis_layout)
        tabs.addTab(analysis_tab, "📈 Hasta Analizi")

        # Kan Şekeri Grafiği Tab'ı
        blood_sugar_graph_tab = BloodSugarGraph(self.doctor_id)
        tabs.addTab(blood_sugar_graph_tab, "📈 Kan Şekeri Grafiği")

        layout.addWidget(tabs)
        self.setLayout(layout)
        
        # Hastaları yükle
        self.load_patients_for_combo()
        self.load_patients()

    def load_patients(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 
                    u.tc_identity_number,
                    u.email,
                    p.diabetes_type,
                    p.diagnosis_date,
                    p.patient_id
                FROM patients p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.doctor_id = %s AND p.is_active = true
                ORDER BY u.tc_identity_number
            """, (self.doctor_id,))

            patients = cursor.fetchall()

            # Hasta listesi tablosunu güncelle
            self.patients_table.setRowCount(len(patients))
            self.patient_combo.clear()
            
            for row, patient in enumerate(patients):
                # T.C. Kimlik No
                tc_item = QTableWidgetItem(patient[0])
                tc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tc_item.setData(Qt.ItemDataRole.UserRole, patient[4])  # patient_id'yi sakla
                self.patients_table.setItem(row, 0, tc_item)
                
                # İsim (TC ve Email)
                name_item = QTableWidgetItem(f"{patient[0]} - {patient[1]}")
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.patients_table.setItem(row, 1, name_item)
                
                # Diyabet Tipi
                type_item = QTableWidgetItem(patient[2])
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.patients_table.setItem(row, 2, type_item)
                
                # Teşhis Tarihi
                date_item = QTableWidgetItem(patient[3].strftime("%d.%m.%Y"))
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.patients_table.setItem(row, 3, date_item)
                
                # Son Ölçüm
                cursor.execute("""
                    SELECT measurement_date, blood_sugar_level
                    FROM measurements
                    WHERE patient_id = %s
                    ORDER BY measurement_date DESC
                    LIMIT 1
                """, (patient[4],))
                
                last_measurement = cursor.fetchone()
                if last_measurement:
                    measurement_text = f"{last_measurement[0].strftime('%d.%m.%Y %H:%M')}\n{last_measurement[1]} mg/dL"
                else:
                    measurement_text = "Ölçüm yok"
                
                measurement_item = QTableWidgetItem(measurement_text)
                measurement_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.patients_table.setItem(row, 4, measurement_item)
                
                # İşlemler
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                details_btn = QPushButton("Detaylar")
                details_btn.clicked.connect(lambda checked, pid=patient[4]: self.show_patient_details(pid))
                actions_layout.addWidget(details_btn)
                
                actions_widget.setLayout(actions_layout)
                self.patients_table.setCellWidget(row, 5, actions_widget)
                
                # ComboBox'a hasta ekle
                self.patient_combo.addItem(f"{patient[0]} - {patient[1]}", patient[4])
            
            # Sütun genişliklerini ayarla
            self.patients_table.resizeColumnsToContents()
            self.patients_table.horizontalHeader().setStretchLastSection(True)
            
            # Hasta yönetimi tablosunu da güncelle
            self.patient_info_table.setRowCount(len(patients))
            for row, patient in enumerate(patients):
                # T.C. Kimlik No
                tc_item = QTableWidgetItem(patient[0])
                tc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tc_item.setData(Qt.ItemDataRole.UserRole, patient[4])  # patient_id'yi sakla
                self.patient_info_table.setItem(row, 0, tc_item)
                
                # E-posta
                email_item = QTableWidgetItem(patient[1])
                email_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.patient_info_table.setItem(row, 1, email_item)
                
                # Diyabet Tipi
                type_item = QTableWidgetItem(patient[2])
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.patient_info_table.setItem(row, 2, type_item)
                
                # Teşhis Tarihi
                date_item = QTableWidgetItem(patient[3].strftime("%d.%m.%Y"))
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.patient_info_table.setItem(row, 3, date_item)
                
                # Belirtiler
                cursor.execute("""
                    SELECT COUNT(DISTINCT s.symptom_id)
                    FROM patient_symptoms ps
                    JOIN symptoms s ON ps.symptom_id = s.symptom_id
                    WHERE ps.patient_id = %s
                """, (patient[4],))
                
                symptom_count = cursor.fetchone()[0]
                symptom_item = QTableWidgetItem(f"{symptom_count} belirti")
                symptom_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.patient_info_table.setItem(row, 4, symptom_item)
                
                # İşlemler
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                details_btn = QPushButton("Detaylar")
                details_btn.clicked.connect(lambda checked, pid=patient[4]: self.show_patient_details(pid))
                actions_layout.addWidget(details_btn)
                
                delete_btn = QPushButton("Sil")
                delete_btn.setStyleSheet("background-color: #dc3545; color: white;")
                delete_btn.clicked.connect(lambda checked, pid=patient[4], tc=patient[0]: self.delete_patient(pid, tc))
                actions_layout.addWidget(delete_btn)
                
                actions_widget.setLayout(actions_layout)
                self.patient_info_table.setCellWidget(row, 5, actions_widget)
            
            # Sütun genişliklerini ayarla
            self.patient_info_table.resizeColumnsToContents()
            self.patient_info_table.horizontalHeader().setStretchLastSection(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hastalar yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def load_patient_tracking(self):
        try:
            if self.tracking_patient_combo.currentData() is None:
                return
                
            patient_id = self.tracking_patient_combo.currentData()
            
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Hasta bilgilerini al
            cursor.execute("""
                SELECT u.tc_identity_number, u.email, p.diabetes_type
                FROM patients p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.patient_id = %s
            """, (patient_id,))
            
            patient_info = cursor.fetchone()
            if not patient_info:
                return
                
            # Hasta başlığını güncelle
            patient_title = f"Hasta Takibi - {patient_info[0]} ({patient_info[1]}) - {patient_info[2]}"
            self.tracking_table.setWindowTitle(patient_title)
            
            # Son 30 günün takip verilerini al
            cursor.execute("""
                SELECT 
                    tracking_date,
                    COALESCE(exercise_status, 'Yapılmadı') as exercise_status,
                    COALESCE(diet_status, 'Uygulanmadı') as diet_status,
                    notes
                FROM daily_tracking
                WHERE patient_id = %s
                AND tracking_date >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY tracking_date DESC
            """, (patient_id,))
            
            records = cursor.fetchall()
            
            # Tabloyu güncelle
            self.tracking_table.setRowCount(len(records))
            for row, record in enumerate(records):
                # Tarih
                date_item = QTableWidgetItem(record[0].strftime("%d.%m.%Y"))
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tracking_table.setItem(row, 0, date_item)
                
                # Egzersiz Durumu
                exercise_item = QTableWidgetItem(record[1])
                exercise_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if record[1] == "Yapıldı":
                    exercise_item.setBackground(QColor("#28a745"))
                    exercise_item.setForeground(QColor("white"))
                else:
                    exercise_item.setBackground(QColor("#dc3545"))
                    exercise_item.setForeground(QColor("white"))
                self.tracking_table.setItem(row, 1, exercise_item)
                
                # Diyet Durumu
                diet_item = QTableWidgetItem(record[2])
                diet_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if record[2] == "Uygulandı":
                    diet_item.setBackground(QColor("#28a745"))
                    diet_item.setForeground(QColor("white"))
                else:
                    diet_item.setBackground(QColor("#dc3545"))
                    diet_item.setForeground(QColor("white"))
                self.tracking_table.setItem(row, 2, diet_item)
                
                # Notlar
                notes_item = QTableWidgetItem(record[3] if record[3] else "")
                notes_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.tracking_table.setItem(row, 3, notes_item)
            
            # İstatistikleri hesapla ve grafikleri güncelle
            exercise_done = sum(1 for r in records if r[1] == "Yapıldı")
            exercise_total = len(records)
            exercise_percentage = (exercise_done / exercise_total * 100) if exercise_total > 0 else 0
            
            diet_done = sum(1 for r in records if r[2] == "Uygulandı")
            diet_total = len(records)
            diet_percentage = (diet_done / diet_total * 100) if diet_total > 0 else 0
            
            # Egzersiz grafiğini güncelle
            self.exercise_chart.removeAllSeries()
            exercise_series = QPieSeries()
            exercise_series.append("Yapıldı", exercise_percentage)
            exercise_series.append("Yapılmadı", 100 - exercise_percentage)
            
            # Renkleri ayarla
            exercise_series.slices()[0].setColor(QColor("#28a745"))
            exercise_series.slices()[1].setColor(QColor("#dc3545"))
            
            self.exercise_chart.addSeries(exercise_series)
            self.exercise_chart.setTitle(f"{patient_info[0]} - Egzersiz Uygulama Oranı: %{exercise_percentage:.1f}")
            
            # Diyet grafiğini güncelle
            self.diet_chart.removeAllSeries()
            diet_series = QPieSeries()
            diet_series.append("Uygulandı", diet_percentage)
            diet_series.append("Uygulanmadı", 100 - diet_percentage)
            
            # Renkleri ayarla
            diet_series.slices()[0].setColor(QColor("#28a745"))
            diet_series.slices()[1].setColor(QColor("#dc3545"))
            
            self.diet_chart.addSeries(diet_series)
            self.diet_chart.setTitle(f"{patient_info[0]} - Diyet Uygulama Oranı: %{diet_percentage:.1f}")
            
            # Sütun genişliklerini ayarla
            self.tracking_table.resizeColumnsToContents()
            self.tracking_table.horizontalHeader().setStretchLastSection(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hasta takip verileri yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def load_patient_analysis(self):
        if not self.analysis_patient_combo.currentText():
            return
            
        patient_id = self.analysis_patient_combo.currentData()
        
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Son ölçümleri al
            cursor.execute("""
                SELECT blood_sugar_level, blood_pressure_systolic, blood_pressure_diastolic, weight
                FROM measurements
                WHERE patient_id = %s
                ORDER BY measurement_date DESC
                LIMIT 1
            """, (patient_id,))
            
            latest_measurement = cursor.fetchone()
            
            # Belirtileri al
            cursor.execute("""
                SELECT COUNT(DISTINCT s.symptom_id)
                FROM patient_symptoms ps
                JOIN symptoms s ON ps.symptom_id = s.symptom_id
                WHERE ps.patient_id = %s
            """, (patient_id,))
            
            symptom_count = cursor.fetchone()[0]
            
            # Önerileri al
            cursor.execute("""
                SELECT COUNT(*)
                FROM doctor_recommendations
                WHERE patient_id = %s
            """, (patient_id,))
            
            recommendation_count = cursor.fetchone()[0]
            
            # Analiz tablosunu doldur
            self.analysis_table.setRowCount(4)
            
            # Kan Şekeri Analizi
            if latest_measurement and latest_measurement[0] is not None:
                blood_sugar = latest_measurement[0]
                blood_sugar_status = "Normal" if 70 <= blood_sugar <= 180 else "Yüksek" if blood_sugar > 180 else "Düşük"
                self.add_analysis_row(0, "Kan Şekeri", f"{blood_sugar} mg/dL", "70-180 mg/dL", blood_sugar_status)
            else:
                self.add_analysis_row(0, "Kan Şekeri", "Ölçüm yok", "70-180 mg/dL", "Bilgi yok")
            
            # Tansiyon Analizi
            if latest_measurement and latest_measurement[1] is not None and latest_measurement[2] is not None:
                systolic = latest_measurement[1]
                diastolic = latest_measurement[2]
                pressure_status = "Normal" if 90 <= systolic <= 140 and 60 <= diastolic <= 90 else "Yüksek" if systolic > 140 or diastolic > 90 else "Düşük"
                self.add_analysis_row(1, "Tansiyon", f"{systolic}/{diastolic} mmHg", "90-140/60-90 mmHg", pressure_status)
            else:
                self.add_analysis_row(1, "Tansiyon", "Ölçüm yok", "90-140/60-90 mmHg", "Bilgi yok")
            
            # Belirti Analizi
            self.add_analysis_row(2, "Aktif Belirti Sayısı", str(symptom_count), "0-3", 
                                "Normal" if symptom_count <= 3 else "Yüksek")
            
            # Öneri Analizi
            self.add_analysis_row(3, "Toplam Öneri Sayısı", str(recommendation_count), "0-10", 
                                "Normal" if recommendation_count <= 10 else "Yüksek")
            
            # Sütun genişliklerini ayarla
            self.analysis_table.resizeColumnsToContents()
            self.analysis_table.horizontalHeader().setStretchLastSection(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hasta analizi yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def add_analysis_row(self, row, feature, value, normal_range, status):
        # Özellik
        feature_item = QTableWidgetItem(feature)
        feature_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.analysis_table.setItem(row, 0, feature_item)
        
        # Değer
        value_item = QTableWidgetItem(value)
        value_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.analysis_table.setItem(row, 1, value_item)
        
        # Normal Aralık
        range_item = QTableWidgetItem(normal_range)
        range_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.analysis_table.setItem(row, 2, range_item)
        
        # Durum
        status_item = QTableWidgetItem(status)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Duruma göre renklendirme
        if status == "Normal":
            status_item.setBackground(QColor("#28a745"))  # Yeşil
            status_item.setForeground(QColor("white"))
        elif status == "Yüksek":
            status_item.setBackground(QColor("#dc3545"))  # Kırmızı
            status_item.setForeground(QColor("white"))
        elif status == "Düşük":
            status_item.setBackground(QColor("#ffc107"))  # Sarı
            status_item.setForeground(QColor("black"))
        elif status == "Bilgi yok":
            status_item.setBackground(QColor("#6c757d"))  # Gri
            status_item.setForeground(QColor("white"))
            
        self.analysis_table.setItem(row, 3, status_item)

    def show_add_patient_dialog(self):
        dialog = AddPatientDialog(self.doctor_id, self)
        if dialog.exec():
            self.load_patients()

    def show_add_measurement_dialog(self, patient_id=None):
        try:
            if patient_id is None:
                if not self.patient_combo.currentData():
                    QMessageBox.warning(self, "Uyarı", "Lütfen önce bir hasta seçin!")
                    return
                patient_id = self.patient_combo.currentData()
                
            dialog = BloodSugarMeasurementDialog(patient_id, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_measurements()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ölçüm eklenirken bir hata oluştu: {str(e)}")

    def show_add_recommendation_dialog(self, patient_id):
        try:
            if not patient_id:
                QMessageBox.warning(self, "Uyarı", "Lütfen önce bir hasta seçin!")
                return
                
            # Öneri formunu göster
            self.recommendation_patient.setCurrentText(self.patient_combo.currentText())
            # Öneri formunu aktif tab yap
            self.parent().findChild(QTabWidget).setCurrentIndex(4)  # Öneriler tab'ının indeksi
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Öneri eklenirken bir hata oluştu: {str(e)}")

    def show_patient_history(self, patient_id):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()

            # Ölçüm geçmişi
            cursor.execute("""
                SELECT m.measurement_date, m.blood_sugar_level, 
                       m.blood_pressure_systolic, m.blood_pressure_diastolic,
                       m.weight
                FROM measurements m
                WHERE m.patient_id = %s
                ORDER BY m.measurement_date DESC
            """, (patient_id,))
            measurements = cursor.fetchall()

            # Öneri geçmişi
            cursor.execute("""
                SELECT r.recommendation_type, r.content, r.created_at
                FROM doctor_recommendations r
                WHERE r.patient_id = %s
                ORDER BY r.created_at DESC
            """, (patient_id,))
            recommendations = cursor.fetchall()

            # Geçmiş penceresi
            history_dialog = QDialog(self)
            history_dialog.setWindowTitle("Hasta Geçmişi")
            history_dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout()
            
            # Ölçümler tablosu
            measurements_table = QTableWidget()
            measurements_table.setColumnCount(5)
            measurements_table.setHorizontalHeaderLabels([
                "Tarih", "Kan Şekeri", "Sistolik", "Diyastolik", "Kilo"
            ])
            measurements_table.setRowCount(len(measurements))
            
            for row, measurement in enumerate(measurements):
                measurements_table.setItem(row, 0, QTableWidgetItem(str(measurement[0])))
                measurements_table.setItem(row, 1, QTableWidgetItem(str(measurement[1])))
                measurements_table.setItem(row, 2, QTableWidgetItem(str(measurement[2])))
                measurements_table.setItem(row, 3, QTableWidgetItem(str(measurement[3])))
                measurements_table.setItem(row, 4, QTableWidgetItem(str(measurement[4])))
            
            layout.addWidget(QLabel("Ölçüm Geçmişi"))
            layout.addWidget(measurements_table)
            
            # Öneriler tablosu
            recommendations_table = QTableWidget()
            recommendations_table.setColumnCount(3)
            recommendations_table.setHorizontalHeaderLabels([
                "Öneri Tipi", "İçerik", "Tarih"
            ])
            recommendations_table.setRowCount(len(recommendations))
            
            for row, recommendation in enumerate(recommendations):
                recommendations_table.setItem(row, 0, QTableWidgetItem(recommendation[0]))
                recommendations_table.setItem(row, 1, QTableWidgetItem(recommendation[1]))
                recommendations_table.setItem(row, 2, QTableWidgetItem(str(recommendation[2])))
            
            layout.addWidget(QLabel("Öneri Geçmişi"))
            layout.addWidget(recommendations_table)
            
            history_dialog.setLayout(layout)
            history_dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veritabanı hatası: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def save_recommendation(self):
        if not self.recommendation_patient.currentText():
            QMessageBox.warning(self, "Uyarı", "Lütfen bir hasta seçin!")
            return
            
        patient_id = self.recommendation_patient.currentData()
        recommendation_type = self.recommendation_type.currentText()
        subtype = self.subtype_combo.currentText() if self.subtype_combo.isVisible() else ""
        content = self.recommendation_content.toPlainText()
        
        if not content.strip():
            QMessageBox.warning(self, "Uyarı", "Lütfen öneri içeriğini girin!")
            return
        
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Öneri türü ve alt türü birleştir
            full_type = f"{recommendation_type} - {subtype}" if subtype else recommendation_type
            
            cursor.execute("""
                INSERT INTO doctor_recommendations (doctor_id, patient_id, recommendation_type, content)
                VALUES (%s, %s, %s, %s)
            """, (self.doctor_id, patient_id, full_type, content))
            
            conn.commit()
            QMessageBox.information(self, "Başarılı", "Öneri başarıyla kaydedildi!")
            
            # Formu temizle
            self.recommendation_content.clear()
            
            # Önerileri yeniden yükle
            self.load_recommendations()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Öneri kaydedilirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def delete_patient(self, patient_id, tc_number):
        """Hastayı silme işlemi"""
        reply = QMessageBox.question(
            self,
            "Hasta Silme Onayı",
            f"TC: {tc_number} numaralı hastayı silmek istediğinizden emin misiniz?\n\n"
            "Bu işlem geri alınamaz ve hastanın tüm verileri silinecektir.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = get_db_connection()
                if conn is None:
                    return
                    
                cursor = conn.cursor()
                
                # Önce hastanın user_id'sini al
                cursor.execute("""
                    SELECT user_id FROM patients WHERE patient_id = %s
                """, (patient_id,))
                user_id = cursor.fetchone()[0]
                
                # İlişkili kayıtları sil
                cursor.execute("""
                    DELETE FROM patient_symptoms WHERE patient_id = %s
                """, (patient_id,))
                cursor.execute("""
                    DELETE FROM measurements WHERE patient_id = %s
                """, (patient_id,))
                cursor.execute("""
                    DELETE FROM doctor_recommendations WHERE patient_id = %s
                """, (patient_id,))
                cursor.execute("""
                    DELETE FROM patients WHERE patient_id = %s
                """, (patient_id,))
                cursor.execute("""
                    DELETE FROM users WHERE user_id = %s
                """, (user_id,))
                
                conn.commit()
                QMessageBox.information(self, "Başarılı", "Hasta başarıyla silindi!")
                
                # Tabloyu güncelle
                self.load_patients()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Hasta silinirken bir hata oluştu: {str(e)}")
            finally:
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()

    def logout(self):
        """Doktor çıkış yapma işlemi"""
        reply = QMessageBox.question(
            self,
            "Çıkış Onayı",
            "Çıkış yapmak istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Ana pencereye dön
            if hasattr(self, 'parent') and self.parent():
                # Mevcut pencereyi gizle
                self.hide()
                # Giriş menüsünü göster
                self.parent().show_login_menu()

    def update_recommendation_content(self, recommendation_type):
        """Öneri türüne göre alt türleri güncelle"""
        self.subtype_combo.clear()
        
        if recommendation_type == "🥗 Beslenme":
            self.subtype_combo.addItems([
                "Az Şekerli Diyet",
                "Şekersiz Diyet",
                "Dengeli Beslenme"
            ])
            self.subtype_combo.setVisible(True)
            
        elif recommendation_type == "🏃‍♂️ Egzersiz":
            self.subtype_combo.addItems([
                "Yürüyüş",
                "Bisiklet",
                "Klinik Egzersiz"
            ])
            self.subtype_combo.setVisible(True)
            
        else:
            self.subtype_combo.setVisible(False)
            self.recommendation_content.clear()

    def update_subtype_content(self, subtype):
        """Seçilen alt türe göre içerik şablonunu güncelle"""
        if not subtype:
            return
            
        if self.recommendation_type.currentText() == "🥗 Beslenme":
            if subtype == "Az Şekerli Diyet":
                content = """Az Şekerli Diyet Önerileri:
- Şekerli gıdalar sınırlanmalıdır
- Kompleks karbonhidratlara öncelik verilmelidir
- Lifli gıdalar ve düşük glisemik indeksli besinler tercih edilmelidir

Lütfen hastanız için özel önerilerinizi ekleyin:"""
                
            elif subtype == "Şekersiz Diyet":
                content = """Şekersiz Diyet Önerileri:
- Rafine şeker ve şeker katkılı tüm ürünler tamamen dışlanmalıdır
- Doğal tatlandırıcılar kullanılabilir
- Meyve tüketimi kontrollü olmalıdır

Lütfen hastanız için özel önerilerinizi ekleyin:"""
                
            else:  # Dengeli Beslenme
                content = """Dengeli Beslenme Önerileri:
- Tüm besin gruplarından yeterli miktarda alınmalıdır
- Porsiyon kontrolü önemlidir
- Mevsimsel taze ürünler tercih edilmelidir
- Su tüketimi günlük en az 2-2.5 litre olmalıdır

Lütfen hastanız için özel önerilerinizi ekleyin:"""
                
        elif self.recommendation_type.currentText() == "🏃‍♂️ Egzersiz":
            if subtype == "Yürüyüş":
                content = """Yürüyüş Programı:
- Hafif tempolu, günlük yapılabilecek bir egzersizdir
- Başlangıç için ideal bir seçenektir
- Günde 30 dakika önerilir
- Sabah veya akşam saatlerinde yapılabilir

Lütfen hastanız için özel önerilerinizi ekleyin:"""
                
            elif subtype == "Bisiklet":
                content = """Bisiklet Programı:
- Alt vücut kaslarını çalıştırır
- Dış mekanda veya sabit bisikletle uygulanabilir
- Haftada 3-4 gün, 20-30 dakika önerilir
- Başlangıçta düşük tempo ile başlanmalıdır

Lütfen hastanız için özel önerilerinizi ekleyin:"""
                
            else:  # Klinik Egzersiz
                content = """Klinik Egzersiz Programı:
- Doktor tarafından verilen belirli hareketleri içerir
- Stresi azaltmaya yardımcı olur
- Hareket kabiliyetini artırır
- Düzenli olarak yapılmalıdır
- Her hareket 10-15 tekrar ile başlanmalıdır

Lütfen hastanız için özel önerilerinizi ekleyin:"""
                
        else:
            content = ""
            
        self.recommendation_content.setPlainText(content)

    def load_patients_for_combo(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()

            cursor.execute("""
                SELECT p.patient_id, u.tc_identity_number, u.email
                FROM patients p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.doctor_id = %s
                ORDER BY u.tc_identity_number
            """, (self.doctor_id,))
            
            patients = cursor.fetchall()
            
            # Tüm ComboBox'ları temizle
            self.patient_combo.clear()
            self.recommendation_patient.clear()
            self.analysis_patient_combo.clear()
            self.tracking_patient_combo.clear()  # Yeni eklenen ComboBox
            
            # Hastaları tüm ComboBox'lara ekle
            for patient in patients:
                display_text = f"{patient[1]} - {patient[2]}"
                self.patient_combo.addItem(display_text, patient[0])
                self.recommendation_patient.addItem(display_text, patient[0])
                self.analysis_patient_combo.addItem(display_text, patient[0])
                self.tracking_patient_combo.addItem(display_text, patient[0])  # Yeni eklenen ComboBox

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hastalar yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def load_doctor_info(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.tc_identity_number, u.email, d.specialization, d.license_number
                FROM doctors d
                JOIN users u ON d.user_id = u.user_id
                WHERE d.doctor_id = %s
            """, (self.doctor_id,))
            
            doctor = cursor.fetchone()
            
            if doctor:
                doctor_info = f"👨‍⚕️ Dr. {doctor[0]} | 📧 {doctor[1]} | 🏥 {doctor[2]} | 📋 Lisans No: {doctor[3]}"
                self.doctor_info_label.setText(doctor_info)
                self.doctor_info_label.setStyleSheet("""
                    font-size: 16px;
                    font-weight: bold;
                    color: #4a90e2;
                    padding: 15px;
                    background-color: #ffffff;
                    border-radius: 8px;
                    border: 2px solid #4a90e2;
                    margin: 10px;
                """)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Doktor bilgileri yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def load_recommendations(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()

            cursor.execute("""
                SELECT r.created_at, u.tc_identity_number, r.recommendation_type, r.content
                FROM doctor_recommendations r
                JOIN patients p ON r.patient_id = p.patient_id
                JOIN users u ON p.user_id = u.user_id
                WHERE r.doctor_id = %s
                ORDER BY r.created_at DESC
            """, (self.doctor_id,))
            
            recommendations = cursor.fetchall()
            
            self.table.setRowCount(len(recommendations))
            for row, recommendation in enumerate(recommendations):
                for col, value in enumerate(recommendation):
                    item = QTableWidgetItem(str(value))
                    self.table.setItem(row, col, item)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Öneriler yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def load_measurements(self):
        try:
            if not self.patient_combo.currentText():
                self.measurements_table.setRowCount(0)
                return
                
            patient_id = self.patient_combo.currentData()
            
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Son 7 günün ölçümlerini al
            cursor.execute("""
                SELECT 
                    DATE(m.measurement_date) as measurement_day,
                    EXTRACT(HOUR FROM m.measurement_date) as measurement_hour,
                    m.blood_sugar_level
                FROM measurements m
                WHERE m.patient_id = %s 
                AND m.measurement_date >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY measurement_day DESC, measurement_hour ASC
            """, (patient_id,))
            
            measurements = cursor.fetchall()
            
            # Son 7 günü oluştur
            today = datetime.now().date()
            days = [(today - timedelta(days=i)) for i in range(7)]
            
            # Ölçüm saatleri
            measurement_hours = [7, 12, 15, 18, 22]  # Sabah, Öğle, İkindi, Akşam, Gece
            
            # Tabloyu hazırla (eski: +2) -> şimdi +3 (Mesajlar için)
            self.measurements_table.setColumnCount(len(measurement_hours) + 3)  # +3 for date, average, mesaj
            self.measurements_table.setRowCount(len(days))
            
            # Başlıkları ayarla
            headers = ["Tarih"]
            for hour in measurement_hours:
                if hour == 7:
                    headers.append("Sabah (07:00)")
                elif hour == 12:
                    headers.append("Öğle (12:00)")
                elif hour == 15:
                    headers.append("İkindi (15:00)")
                elif hour == 18:
                    headers.append("Akşam (18:00)")
                elif hour == 22:
                    headers.append("Gece (22:00)")
            headers.append("Günlük Ortalama")
            headers.append("Mesajlar")
            self.measurements_table.setHorizontalHeaderLabels(headers)
            
            # Ölçümleri düzenle
            measurements_dict = {}
            for day, hour, value in measurements:
                if day not in measurements_dict:
                    measurements_dict[day] = {}
                measurements_dict[day][hour] = value
            
            # Tabloyu doldur
            for row, day in enumerate(days):
                # Tarih
                date_item = QTableWidgetItem(day.strftime("%d.%m.%Y"))
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.measurements_table.setItem(row, 0, date_item)
                
                # Günlük değerleri toplamak için
                daily_values = []
                
                # Her saat için ölçüm değerini kontrol et
                for col, hour in enumerate(measurement_hours, start=1):
                    if day in measurements_dict and hour in measurements_dict[day]:
                        blood_sugar = measurements_dict[day][hour]
                        if blood_sugar is not None:
                            # İnsülin dozu hesaplama
                            insulin_dose = self.calculate_insulin_dose(blood_sugar, hour)
                            sugar_item = QTableWidgetItem(f"{blood_sugar} mg/dL\n{insulin_dose}")
                            sugar_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            daily_values.append(blood_sugar)
                            
                            # Kan şekeri seviyesine göre renklendirme
                            if blood_sugar < 70:
                                sugar_item.setBackground(QColor("#dc3545"))  # Kırmızı - Düşük
                                sugar_item.setForeground(QColor("white"))
                            elif 70 <= blood_sugar <= 99:
                                sugar_item.setBackground(QColor("#28a745"))  # Yeşil - Normal
                                sugar_item.setForeground(QColor("white"))
                            elif 100 <= blood_sugar <= 125:
                                sugar_item.setBackground(QColor("#ffc107"))  # Sarı - Orta
                                sugar_item.setForeground(QColor("black"))
                            else:
                                sugar_item.setBackground(QColor("#dc3545"))  # Kırmızı - Yüksek
                                sugar_item.setForeground(QColor("white"))
                        else:
                            sugar_item = QTableWidgetItem("Ölçüm yok")
                            sugar_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                            sugar_item.setBackground(QColor("#6c757d"))  # Gri
                            sugar_item.setForeground(QColor("white"))
                    else:
                        sugar_item = QTableWidgetItem("⚠️ Ölçüm yapılmamış")
                        sugar_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        sugar_item.setBackground(QColor("#ffc107"))  # Sarı - Uyarı
                        sugar_item.setForeground(QColor("black"))
                    
                    self.measurements_table.setItem(row, col, sugar_item)
                
                # Günlük ortalama hesapla ve göster
                if daily_values:
                    daily_avg = sum(daily_values) / len(daily_values)
                    avg_item = QTableWidgetItem(f"{daily_avg:.1f} mg/dL")
                    avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # Ortalama değere göre renklendirme
                    if daily_avg < 70:
                        avg_item.setBackground(QColor("#dc3545"))  # Kırmızı - Düşük
                        avg_item.setForeground(QColor("white"))
                    elif 70 <= daily_avg <= 99:
                        avg_item.setBackground(QColor("#28a745"))  # Yeşil - Normal
                        avg_item.setForeground(QColor("white"))
                    elif 100 <= daily_avg <= 125:
                        avg_item.setBackground(QColor("#ffc107"))  # Sarı - Orta
                        avg_item.setForeground(QColor("black"))
                    else:
                        avg_item.setBackground(QColor("#dc3545"))  # Kırmızı - Yüksek
                        avg_item.setForeground(QColor("white"))
                else:
                    avg_item = QTableWidgetItem("Ölçüm yok")
                    avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    avg_item.setBackground(QColor("#6c757d"))  # Gri
                    avg_item.setForeground(QColor("white"))
                
                self.measurements_table.setItem(row, len(measurement_hours) + 1, avg_item)
                
                # --- MESAJLAR SÜTUNU ---
                # O günün tüm ölçümlerini topla
                gun_olcumleri = [measurements_dict[day][h] for h in measurement_hours if day in measurements_dict and h in measurements_dict[day] and measurements_dict[day][h] is not None]
                uyari_tipi, mesaj = analyze_blood_sugar_for_day(gun_olcumleri)
                mesaj_item = QTableWidgetItem(mesaj)
                mesaj_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.measurements_table.setItem(row, len(measurement_hours) + 2, mesaj_item)
            
            # Sütun genişliklerini ayarla
            self.measurements_table.resizeColumnsToContents()
            self.measurements_table.horizontalHeader().setStretchLastSection(True)
            
            # Minimum sütun genişliklerini ayarla
            for i in range(self.measurements_table.columnCount()):
                self.measurements_table.setColumnWidth(i, 120)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ölçümler yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def calculate_insulin_dose(self, blood_sugar, hour):
        """Kan şekeri değerine göre insülin dozu hesaplar"""
        # Kan şekeri aralıkları ve doz önerileri
        if blood_sugar < 70:  # Hipoglisemi
            return "⚠️ Hipoglisemi! İnsülin: Yok"
        elif 70 <= blood_sugar <= 110:  # Normal
            return "İnsülin: Yok"
        elif 111 <= blood_sugar <= 150:  # Orta Yüksek
            return "İnsülin: 1 ml"
        elif 151 <= blood_sugar <= 200:  # Yüksek
            return "İnsülin: 2 ml"
        else:  # Çok Yüksek (>200)
            return "İnsülin: 3 ml"

    def load_profile_image(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Doktorun profil fotoğrafını veritabanından al
            cursor.execute("""
                SELECT u.profile_image
                FROM users u
                JOIN doctors d ON u.user_id = d.user_id
                WHERE d.doctor_id = %s
            """, (self.doctor_id,))
            
            result = cursor.fetchone()
            
            if result and result[0]:
                # Binary veriyi QPixmap'e dönüştür
                image_data = result[0]
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                
                # Profil fotoğrafını yuvarlak yap
                rounded_pixmap = QPixmap(pixmap.size())
                rounded_pixmap.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(rounded_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                path = QPainterPath()
                path.addEllipse(0, 0, pixmap.width(), pixmap.height())
                painter.setClipPath(path)
                
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                
                # Profil fotoğrafını göster
                self.profile_image_label.setPixmap(rounded_pixmap.scaled(
                    100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                ))
            else:
                # Varsayılan profil fotoğrafını göster
                self.profile_image_label.setPixmap(QPixmap("default_profile.png").scaled(
                    100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                ))
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Profil fotoğrafı yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def change_profile_image(self):
        try:
            # Dosya seçme dialogunu aç
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Profil Fotoğrafı Seç",
                "",
                "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp)"
            )
            
            if file_name:
                # Seçilen dosyayı oku
                with open(file_name, 'rb') as file:
                    image_data = file.read()
                
                # Veritabanına kaydet
                conn = get_db_connection()
                if conn is None:
                    return
                    
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users
                    SET profile_image = %s
                    FROM doctors
                    WHERE users.user_id = doctors.user_id
                    AND doctors.doctor_id = %s
                """, (psycopg2.Binary(image_data), self.doctor_id))
                
                conn.commit()
                
                # Profil fotoğrafını güncelle
                self.load_profile_image()
                
                QMessageBox.information(self, "Başarılı", "Profil fotoğrafı başarıyla güncellendi!")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Profil fotoğrafı güncellenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def filter_patients(self):
        """Hasta listesini arama kriterine göre filtreler"""
        search_text = self.search_input.text().lower()
        
        for row in range(self.patients_table.rowCount()):
            show_row = False
            
            # T.C. Kimlik No ve İsim sütunlarını kontrol et
            for col in range(2):  # İlk iki sütun (T.C. No ve İsim)
                item = self.patients_table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            
            # Satırı göster/gizle
            self.patients_table.setRowHidden(row, not show_row)

    def show_patient_details(self, patient_id=None):
        """Hasta detaylarını gösterir"""
        if patient_id is None:
            # Tablodan seçilen satırı al
            current_row = self.patients_table.currentRow()
            if current_row < 0:
                return
            patient_id = self.patients_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Hasta bilgilerini al
            cursor.execute("""
                SELECT 
                    u.tc_identity_number,
                    u.email,
                    p.diabetes_type,
                    p.diagnosis_date,
                    p.patient_id
                FROM patients p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.patient_id = %s
            """, (patient_id,))
            
            patient = cursor.fetchone()
            
            if patient:
                # Detay penceresi
                dialog = QDialog(self)
                dialog.setWindowTitle("Hasta Detayları")
                dialog.setMinimumSize(600, 400)
                
                layout = QVBoxLayout()
                
                # Hasta bilgileri
                info_group = QGroupBox("Hasta Bilgileri")
                info_layout = QFormLayout()
                
                info_layout.addRow("T.C. Kimlik No:", QLabel(patient[0]))
                info_layout.addRow("E-posta:", QLabel(patient[1]))
                info_layout.addRow("Diyabet Tipi:", QLabel(patient[2]))
                info_layout.addRow("Teşhis Tarihi:", QLabel(patient[3].strftime("%d.%m.%Y")))
                
                info_group.setLayout(info_layout)
                layout.addWidget(info_group)
                
                # Son ölçümler
                cursor.execute("""
                    SELECT measurement_date, blood_sugar_level, blood_pressure_systolic, 
                           blood_pressure_diastolic, weight
                    FROM measurements
                    WHERE patient_id = %s
                    ORDER BY measurement_date DESC
                    LIMIT 5
                """, (patient_id,))
                
                measurements = cursor.fetchall()
                
                if measurements:
                    measurements_group = QGroupBox("Son Ölçümler")
                    measurements_layout = QVBoxLayout()
                    
                    measurements_table = QTableWidget()
                    measurements_table.setColumnCount(5)
                    measurements_table.setHorizontalHeaderLabels([
                        "Tarih", "Kan Şekeri", "Sistolik", "Diyastolik", "Kilo"
                    ])
                    
                    measurements_table.setRowCount(len(measurements))
                    for row, measurement in enumerate(measurements):
                        measurements_table.setItem(row, 0, QTableWidgetItem(measurement[0].strftime("%d.%m.%Y %H:%M")))
                        measurements_table.setItem(row, 1, QTableWidgetItem(f"{measurement[1]} mg/dL"))
                        measurements_table.setItem(row, 2, QTableWidgetItem(f"{measurement[2]} mmHg"))
                        measurements_table.setItem(row, 3, QTableWidgetItem(f"{measurement[3]} mmHg"))
                        measurements_table.setItem(row, 4, QTableWidgetItem(f"{measurement[4]} kg"))
                    
                    measurements_layout.addWidget(measurements_table)
                    measurements_group.setLayout(measurements_layout)
                    layout.addWidget(measurements_group)
                
                # İşlem butonları
                buttons_layout = QHBoxLayout()
                
                # Ölçüm ekle butonu
                add_measurement_btn = QPushButton("➕ Yeni Ölçüm Ekle")
                add_measurement_btn.clicked.connect(lambda: self.show_add_measurement_dialog(patient_id))
                buttons_layout.addWidget(add_measurement_btn)
                
                # Öneri ekle butonu
                add_recommendation_btn = QPushButton("💡 Yeni Öneri Ekle")
                add_recommendation_btn.clicked.connect(lambda: self.show_add_recommendation_dialog(patient_id))
                buttons_layout.addWidget(add_recommendation_btn)
                
                # Geçmiş butonu
                history_btn = QPushButton("📋 Geçmiş")
                history_btn.clicked.connect(lambda: self.show_patient_history(patient_id))
                buttons_layout.addWidget(history_btn)
                
                layout.addLayout(buttons_layout)
                
                dialog.setLayout(layout)
                dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hasta detayları yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

class BloodSugarGraph(QWidget):
    def __init__(self, doctor_id):
        super().__init__()
        self.doctor_id = doctor_id
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Hasta seçimi
        patient_layout = QHBoxLayout()
        patient_label = QLabel("Hasta:")
        self.patient_combo = QComboBox()
        self.load_patients()
        patient_layout.addWidget(patient_label)
        patient_layout.addWidget(self.patient_combo)
        
        # Tarih seçimi
        date_layout = QHBoxLayout()
        date_label = QLabel("Tarih:")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        
        # Grafik güncelleme butonu
        update_btn = QPushButton("Grafiği Güncelle")
        update_btn.clicked.connect(self.update_graph)
        
        # Grafik widget'ı
        self.chart = QChart()
        self.chart.setTitle("Günlük Kan Şekeri Takibi")
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        # X ekseni (saat)
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Saat")
        self.axis_x.setRange(0, 24)
        self.axis_x.setTickCount(13)
        self.axis_x.setLabelFormat("%d")
        
        # Y ekseni (kan şekeri)
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Kan Şekeri (mg/dL)")
        self.axis_y.setRange(0, 400)
        self.axis_y.setTickCount(9)
        
        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)
        
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Layout'a widget'ları ekle
        layout.addLayout(patient_layout)
        layout.addLayout(date_layout)
        layout.addWidget(update_btn)
        layout.addWidget(self.chart_view)
        
        self.setLayout(layout)
        
        # İlk grafiği oluştur
        self.update_graph()

    def load_patients(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.patient_id, u.tc_identity_number, u.email
                FROM patients p
                JOIN users u ON p.user_id = u.user_id
                WHERE p.doctor_id = %s AND p.is_active = true
                ORDER BY u.tc_identity_number
            """, (self.doctor_id,))
            
            patients = cursor.fetchall()
            
            self.patient_combo.clear()
            for patient_id, tc, email in patients:
                display_text = f"{tc} - {email}"
                self.patient_combo.addItem(display_text, patient_id)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hastalar yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def update_graph(self):
        try:
            patient_id = self.patient_combo.currentData()
            selected_date = self.date_edit.date().toPyDate()
            
            if not patient_id:
                return
                
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Seçilen tarihteki kan şekeri ölçümlerini al
            cursor.execute("""
                SELECT measurement_date, blood_sugar_level
                FROM measurements
                WHERE patient_id = %s 
                AND DATE(measurement_date) = %s
                ORDER BY measurement_date
            """, (patient_id, selected_date))
            
            measurements = cursor.fetchall()
            
            # Mevcut serileri temizle
            self.chart.removeAllSeries()
            
            if measurements:
                # Yeni seri oluştur
                series = QLineSeries()
                series.setName("Kan Şekeri")
                
                # Verileri seriye ekle
                for time, blood_sugar in measurements:
                    hour = time.hour + time.minute / 60
                    series.append(hour, blood_sugar)
                
                # Seriyi grafiğe ekle
                self.chart.addSeries(series)
                series.attachAxis(self.axis_x)
                series.attachAxis(self.axis_y)
                
                # Grafik başlığını güncelle
                patient_name = self.patient_combo.currentText()
                self.chart.setTitle(f"{patient_name} - {selected_date.strftime('%d.%m.%Y')} Kan Şekeri Takibi")
            else:
                self.chart.setTitle("Seçilen tarihte ölçüm bulunamadı")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Grafik güncellenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
  
def analyze_blood_sugar_for_day(measurements):
    """
    measurements: List of kan şekeri değerleri (mg/dL) bir gün için
    """
    if not measurements or len(measurements) == 0:
        return ("Ölçüm Eksik Uyarısı", "Hasta gün boyunca kan şekeri ölçümü yapmamıştır. Acil takip önerilir.")
    elif len(measurements) < 3:
        return ("Ölçüm Yetersiz Uyarısı", "Hastanın günlük kan şekeri ölçüm sayısı yetersiz (<3). Durum izlenmelidir.")
    for value in measurements:
        if value < 70:
            return ("Acil Uyarı", "Hastanın kan şekeri seviyesi 70 mg/dL'nin altına düştü. Hipoglisemi riski! Hızlı müdahale gerekebilir.")
        elif value > 200:
            return ("Acil Müdahale Uyarısı", "Hastanın kan şekeri 200 mg/dL'nin üzerinde. Hiperglisemi durumu. Acil müdahale gerekebilir.")
        elif 151 <= value <= 200:
            return ("İzleme Uyarısı", "Hastanın kan şekeri 151-200 mg/dL arasında. Diyabet kontrolü gereklidir.")
        elif 111 <= value <= 150:
            return ("Takip Uyarısı", "Hastanın kan şekeri 111-150 mg/dL arasında. Durum izlenmeli.")
    if all(70 <= v <= 110 for v in measurements):
        return ("Uyarı Yok", "Kan şekeri seviyesi normal aralıkta. Hiçbir işlem gerekmez.")
    return ("Takip Uyarısı", "Hastanın kan şekeri değerleri izlenmelidir.")
  