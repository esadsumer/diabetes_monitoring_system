from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QFormLayout, QLineEdit, QTextEdit, QComboBox,
                            QMessageBox, QDialog, QDateEdit, QTabWidget,
                            QSpinBox, QDoubleSpinBox, QFrame, QGroupBox,
                            QFileDialog, QScrollArea)
from PyQt6.QtCore import Qt, QDate, QDateTime
from PyQt6.QtGui import QColor, QPixmap, QImage, QPainter, QPainterPath
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
import psycopg2
from datetime import datetime, timedelta
import bcrypt
from blood_sugar_dialog import BloodSugarMeasurementDialog
import base64
import io
import os

# Veritabanı bağlantı bilgileri
DB_CONFIG = {
    'dbname': 'diabetes_monitoring_system',
    'user': 'postgres',
    'password': 'your_password',
    'host': 'localhost',
    'port': '5432'
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        QMessageBox.critical(None, "Veritabanı Bağlantı Hatası", 
                           f"Veritabanına bağlanırken hata oluştu:\n{str(e)}")
        return None

class PatientPanel(QWidget):
    def __init__(self, patient_id):
        super().__init__()
        self.patient_id = patient_id
        self.diet_percentage = 0
        self.exercise_percentage = 0
        self.setup_styles()
        self.setup_ui()
        self.load_patient_info()
        self.load_measurements()
        self.load_recommendations()
        self.load_symptoms()
        self.load_daily_tracking()

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
        """)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Üst Bilgi Paneli
        info_panel = QFrame()
        info_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        """)
        info_layout = QHBoxLayout()
        
        # Profil Resmi
        self.profile_image_label = QLabel()
        self.profile_image_label.setFixedSize(120, 120)
        self.profile_image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #4a90e2;
                border-radius: 60px;
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
                min-width: 160px;
                font-size: 14px;
                padding: 10px;
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
        
        # Hasta Bilgileri
        self.patient_info_label = QLabel()
        self.patient_info_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #4a90e2;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            min-width: 400px;
        """)
        info_layout.addWidget(self.patient_info_label)
        
        # Çıkış Butonu
        logout_btn = QPushButton("🚪 Çıkış Yap")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                min-width: 160px;
                font-size: 14px;
                padding: 10px;
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
        
        # Günlük Takip Tab'ı
        daily_tracking_tab = QWidget()
        daily_tracking_layout = QVBoxLayout()
        
        # Scroll Area için container
        scroll_container = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_container.setLayout(scroll_layout)
        
        # Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4a90e2;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Günlük Takip Formu için Scroll Area
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4a90e2;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Form container
        form_container = QWidget()
        form_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
            }
        """)
        form_container_layout = QVBoxLayout()
        form_container_layout.setContentsMargins(0, 0, 0, 0)
        form_container.setLayout(form_container_layout)
        
        # Günlük Takip Formu
        form_group = QGroupBox("Günlük Takip")
        form_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
                font-size: 14px;
                min-height: 250px;
            }
            QGroupBox::title {
                color: #4a90e2;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        # Ana form layout
        form_layout = QVBoxLayout()
        
        # Yüzde göstergeleri için container
        percentage_container = QWidget()
        percentage_layout = QHBoxLayout()
        percentage_container.setLayout(percentage_layout)
        
        # Diyet ve egzersiz yüzdelerini göster
        self.diet_label = QLabel(f"🍽️ Diyet Uyumu: %{self.diet_percentage:.1f}")
        self.exercise_label = QLabel(f"🏃 Egzersiz Uyumu: %{self.exercise_percentage:.1f}")
        
        # Stil ayarları
        for label in [self.diet_label, self.exercise_label]:
            label.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    font-weight: bold;
                    color: #b71c1c;
                    padding: 20px;
                    background-color: #e3f2fd;
                    border: 3px solid #2196f3;
                    border-radius: 10px;
                    margin: 10px;
                    min-width: 350px;
                }
            """)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            percentage_layout.addWidget(label)
        
        form_layout.addWidget(percentage_container)
        
        # Form elemanları için container
        form_elements = QFormLayout()
        form_elements.setSpacing(10)
        form_elements.setContentsMargins(8, 8, 8, 8)
        
        # Egzersiz Durumu
        self.exercise_status = QComboBox()
        self.exercise_status.addItems(["Yapıldı", "Yapılmadı"])
        self.exercise_status.setMinimumHeight(35)
        self.exercise_status.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                padding: 6px;
                border: 2px solid #4a90e2;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
        """)
        form_elements.addRow("Egzersiz Durumu:", self.exercise_status)
        
        # Diyet Durumu
        self.diet_status = QComboBox()
        self.diet_status.addItems(["Uygulandı", "Uygulanmadı"])
        self.diet_status.setMinimumHeight(35)
        self.diet_status.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                padding: 6px;
                border: 2px solid #4a90e2;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
        """)
        form_elements.addRow("Diyet Durumu:", self.diet_status)
        
        # Notlar
        self.daily_notes = QTextEdit()
        self.daily_notes.setPlaceholderText("Günlük notlarınızı buraya yazabilirsiniz...")
        self.daily_notes.setMinimumHeight(100)
        self.daily_notes.setStyleSheet("""
            QTextEdit {
                font-size: 14px;
                padding: 6px;
                border: 2px solid #4a90e2;
                border-radius: 4px;
                background-color: white;
            }
        """)
        form_elements.addRow("Notlar:", self.daily_notes)
        
        form_layout.addLayout(form_elements)
        form_group.setLayout(form_layout)
        form_container_layout.addWidget(form_group)
        
        # Kaydet Butonu
        save_btn = QPushButton("💾 Günlük Takibi Kaydet")
        save_btn.setMinimumHeight(35)
        save_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 6px 12px;
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2d6da3;
            }
        """)
        save_btn.clicked.connect(self.save_daily_tracking)
        form_container_layout.addWidget(save_btn)
        
        # Form container'ı scroll area'ya ekle
        form_scroll.setWidget(form_container)
        scroll_layout.addWidget(form_scroll)
        
        # Günlük Takip Tablosu için Scroll Area
        table_scroll = QScrollArea()
        table_scroll.setWidgetResizable(True)
        table_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4a90e2;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Günlük Takip Tablosu
        self.daily_tracking_table = QTableWidget()
        self.daily_tracking_table.setColumnCount(4)
        self.daily_tracking_table.setHorizontalHeaderLabels([
            "Tarih", "Egzersiz", "Diyet", "Notlar"
        ])
        self.daily_tracking_table.horizontalHeader().setStretchLastSection(True)
        
        # Tablo boyutunu ayarla
        self.daily_tracking_table.setMinimumHeight(500)
        self.daily_tracking_table.setMinimumWidth(900)
        
        # Sütun genişliklerini ayarla
        self.daily_tracking_table.setColumnWidth(0, 200)  # Tarih
        self.daily_tracking_table.setColumnWidth(1, 150)  # Egzersiz
        self.daily_tracking_table.setColumnWidth(2, 150)  # Diyet
        self.daily_tracking_table.setColumnWidth(3, 700)  # Notlar
        
        # Tablo stilini güncelle
        self.daily_tracking_table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                gridline-color: #e1e1e1;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 15px;
                min-height: 40px;
            }
            QHeaderView::section {
                background-color: #4a90e2;
                color: white;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
        """)
        
        # Alternatif satır renklendirmesi
        self.daily_tracking_table.setAlternatingRowColors(True)
        
        # Satır yüksekliğini ayarla
        self.daily_tracking_table.verticalHeader().setDefaultSectionSize(40)
        
        table_scroll.setWidget(self.daily_tracking_table)
        scroll_layout.addWidget(table_scroll)
        
        # Ana layout'a scroll area'yı ekle
        daily_tracking_layout.addWidget(scroll_area)
        daily_tracking_tab.setLayout(daily_tracking_layout)
        tabs.addTab(daily_tracking_tab, "📅 Günlük Takip")

        # Ölçümler Tab'ı
        measurements_tab = QWidget()
        measurements_layout = QVBoxLayout()
        
        # Ölçüm Ekleme Butonu
        add_measurement_btn = QPushButton("➕ Yeni Ölçüm Ekle")
        add_measurement_btn.setMinimumHeight(40)
        add_measurement_btn.clicked.connect(self.show_add_measurement_dialog)
        measurements_layout.addWidget(add_measurement_btn)
        
        # Ölçüm Tablosu
        self.measurements_table = QTableWidget()
        self.measurements_table.setColumnCount(6)
        self.measurements_table.setHorizontalHeaderLabels([
            "Tarih", "Kan Şekeri", "Tansiyon", "Kilo", 
            "Durum", "Uyarı"
        ])
        self.measurements_table.horizontalHeader().setStretchLastSection(True)
        
        measurements_layout.addWidget(self.measurements_table)
        measurements_tab.setLayout(measurements_layout)
        tabs.addTab(measurements_tab, "📊 Ölçümlerim")

        # Öneriler Tab'ı
        recommendations_tab = QWidget()
        recommendations_layout = QVBoxLayout()
        
        # Öneri Tablosu
        self.recommendations_table = QTableWidget()
        self.recommendations_table.setColumnCount(3)
        self.recommendations_table.setHorizontalHeaderLabels([
            "Öneri Tipi", "İçerik", "Tarih"
        ])
        self.recommendations_table.horizontalHeader().setStretchLastSection(True)
        
        recommendations_layout.addWidget(self.recommendations_table)
        recommendations_tab.setLayout(recommendations_layout)
        tabs.addTab(recommendations_tab, "💡 Doktor Önerileri")

        # Belirtiler Tab'ı
        symptoms_tab = QWidget()
        symptoms_layout = QVBoxLayout()
        
        # Belirti Tablosu
        self.symptoms_table = QTableWidget()
        self.symptoms_table.setColumnCount(3)
        self.symptoms_table.setHorizontalHeaderLabels([
            "Tarih", "Belirti", "Notlar"
        ])
        self.symptoms_table.horizontalHeader().setStretchLastSection(True)
        
        symptoms_layout.addWidget(self.symptoms_table)
        symptoms_tab.setLayout(symptoms_layout)
        tabs.addTab(symptoms_tab, "🔍 Belirtilerim")

        # Kan Şekeri Grafiği Tab'ı
        blood_sugar_graph_tab = BloodSugarGraph(self.patient_id)
        tabs.addTab(blood_sugar_graph_tab, "📈 Kan Şekeri Grafiği")

        layout.addWidget(tabs)
        self.setLayout(layout)

    def load_patient_info(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.tc_identity_number, u.email, p.diabetes_type, 
                       p.diagnosis_date, d.specialization
                FROM patients p
                JOIN users u ON p.user_id = u.user_id
                JOIN doctors d ON p.doctor_id = d.doctor_id
                WHERE p.patient_id = %s
            """, (self.patient_id,))
            
            patient_info = cursor.fetchone()
            
            if patient_info:
                info_text = f"👤 Hasta: {patient_info[0]}\n"
                info_text += f"📧 E-posta: {patient_info[1]}\n"
                info_text += f"💉 Diyabet Tipi: {patient_info[2]}\n"
                info_text += f"📅 Teşhis Tarihi: {patient_info[3].strftime('%d.%m.%Y')}\n"
                info_text += f"👨‍⚕️ Doktor Uzmanlığı: {patient_info[4]}"
                
                self.patient_info_label.setText(info_text)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hasta bilgileri yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def load_measurements(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Son 7 günün ölçümlerini al
            cursor.execute("""
                SELECT 
                    DATE(m.measurement_date) as measurement_day,
                    EXTRACT(HOUR FROM m.measurement_date) as measurement_hour,
                    m.blood_sugar_level,
                    m.blood_pressure_systolic,
                    m.blood_pressure_diastolic,
                    m.weight
                FROM measurements m
                WHERE m.patient_id = %s 
                AND m.measurement_date >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY measurement_day DESC, measurement_hour ASC
            """, (self.patient_id,))
            
            measurements = cursor.fetchall()
            
            # Son 7 günü oluştur
            today = datetime.now().date()
            days = [(today - timedelta(days=i)) for i in range(7)]
            
            # Ölçüm saatleri
            measurement_hours = [7, 12, 15, 18, 22]  # Sabah, Öğle, İkindi, Akşam, Gece
            
            # Tabloyu hazırla
            self.measurements_table.setColumnCount(len(measurement_hours) + 2)  # +2 for date and average columns
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
            self.measurements_table.setHorizontalHeaderLabels(headers)
            
            # Ölçümleri düzenle
            measurements_dict = {}
            for day, hour, blood_sugar, systolic, diastolic, weight in measurements:
                if day not in measurements_dict:
                    measurements_dict[day] = {}
                measurements_dict[day][hour] = (blood_sugar, systolic, diastolic, weight)
            
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
                        blood_sugar, systolic, diastolic, weight = measurements_dict[day][hour]
                        if blood_sugar is not None:
                            # İnsülin dozu hesaplama
                            insulin_dose = self.calculate_insulin_dose(blood_sugar)
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

    def load_recommendations(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT r.recommendation_type, r.content, r.created_at
                FROM doctor_recommendations r
                WHERE r.patient_id = %s
                ORDER BY r.created_at DESC
            """, (self.patient_id,))
            
            recommendations = cursor.fetchall()
            
            self.recommendations_table.setRowCount(len(recommendations))
            for row, recommendation in enumerate(recommendations):
                # Öneri Tipi
                type_item = QTableWidgetItem(recommendation[0])
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.recommendations_table.setItem(row, 0, type_item)
                
                # İçerik
                content = recommendation[1]
                # İçeriği daha okunaklı hale getir
                content = content.replace('\n', ' | ')
                content_item = QTableWidgetItem(content)
                content_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.recommendations_table.setItem(row, 1, content_item)
                
                # Tarih
                date_item = QTableWidgetItem(recommendation[2].strftime("%d.%m.%Y %H:%M"))
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.recommendations_table.setItem(row, 2, date_item)
            
            # Sütun genişliklerini ayarla
            self.recommendations_table.resizeColumnsToContents()
            self.recommendations_table.horizontalHeader().setStretchLastSection(True)
            
            # Minimum sütun genişliklerini ayarla
            self.recommendations_table.setColumnWidth(0, 200)  # Öneri Tipi
            self.recommendations_table.setColumnWidth(1, 500)  # İçerik
            self.recommendations_table.setColumnWidth(2, 150)  # Tarih
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Öneriler yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def get_status(self, blood_sugar, systolic, diastolic):
        status = []
        
        if blood_sugar < 70:
            status.append("Düşük Kan Şekeri")
        elif blood_sugar > 180:
            status.append("Yüksek Kan Şekeri")
        else:
            status.append("Normal Kan Şekeri")
        
        if systolic > 140 or diastolic > 90:
            status.append("Yüksek Tansiyon")
        elif systolic < 90 or diastolic < 60:
            status.append("Düşük Tansiyon")
        else:
            status.append("Normal Tansiyon")
        
        return ", ".join(status)

    def get_warning(self, blood_sugar, systolic, diastolic):
        warnings = []
        
        if blood_sugar < 70:
            warnings.append("Acil müdahale gerekebilir!")
        elif blood_sugar > 180:
            warnings.append("Kan şekeri yüksek, dikkat!")
        
        if systolic > 140 or diastolic > 90:
            warnings.append("Tansiyon yüksek, kontrol gerekli!")
        elif systolic < 90 or diastolic < 60:
            warnings.append("Tansiyon düşük, dikkat!")
        
        return " | ".join(warnings) if warnings else "Normal"

    def show_add_measurement_dialog(self):
        dialog = BloodSugarMeasurementDialog(self.patient_id, self)
        if dialog.exec():
            self.load_measurements()

    def logout(self):
        """Hasta çıkış yapma işlemi"""
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

    def load_symptoms(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ps.date_added, s.name, ps.notes
                FROM patient_symptoms ps
                JOIN symptoms s ON ps.symptom_id = s.symptom_id
                WHERE ps.patient_id = %s
                ORDER BY ps.date_added DESC
            """, (self.patient_id,))
            
            symptoms = cursor.fetchall()
            
            self.symptoms_table.setRowCount(len(symptoms))
            for row, symptom in enumerate(symptoms):
                # Tarih
                date_item = QTableWidgetItem(symptom[0].strftime("%d.%m.%Y %H:%M"))
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.symptoms_table.setItem(row, 0, date_item)
                
                # Belirti
                symptom_item = QTableWidgetItem(symptom[1])
                symptom_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.symptoms_table.setItem(row, 1, symptom_item)
                
                # Notlar
                notes_item = QTableWidgetItem(symptom[2] if symptom[2] else "")
                notes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.symptoms_table.setItem(row, 2, notes_item)
            
            # Sütun genişliklerini ayarla
            self.symptoms_table.resizeColumnsToContents()
            self.symptoms_table.horizontalHeader().setStretchLastSection(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Belirtiler yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def load_daily_tracking(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Son 30 günlük diyet ve egzersiz yüzdelerini al
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN diet_status = 'Uygulandı' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as diet_percentage,
                    COUNT(CASE WHEN exercise_status = 'Yapıldı' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as exercise_percentage
                FROM daily_tracking
                WHERE patient_id = %s
                AND tracking_date >= CURRENT_DATE - INTERVAL '30 days'
            """, (self.patient_id,))
            
            result = cursor.fetchone()
            
            if result:
                self.diet_percentage = result[0] if result[0] is not None else 0
                self.exercise_percentage = result[1] if result[1] is not None else 0
                
                # Yüzde göstergelerini güncelle
                if hasattr(self, 'diet_label'):
                    self.diet_label.setText(f"🍽️ Diyet Uyumu: %{self.diet_percentage:.1f}")
                if hasattr(self, 'exercise_label'):
                    self.exercise_label.setText(f"🏃 Egzersiz Uyumu: %{self.exercise_percentage:.1f}")
            
            # Günlük takip verilerini al
            cursor.execute("""
                SELECT tracking_date, exercise_status, diet_status, notes
                FROM daily_tracking
                WHERE patient_id = %s
                ORDER BY tracking_date DESC
            """, (self.patient_id,))
            
            records = cursor.fetchall()
            
            self.daily_tracking_table.setRowCount(len(records))
            for row, record in enumerate(records):
                # Tarih
                date_item = QTableWidgetItem(record[0].strftime("%d.%m.%Y %H:%M"))
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.daily_tracking_table.setItem(row, 0, date_item)
                
                # Egzersiz Durumu
                exercise_item = QTableWidgetItem(record[1])
                exercise_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Duruma göre renklendirme
                if record[1] == "Yapıldı":
                    exercise_item.setBackground(QColor("#28a745"))
                    exercise_item.setForeground(QColor("white"))
                else:
                    exercise_item.setBackground(QColor("#dc3545"))
                    exercise_item.setForeground(QColor("white"))
                self.daily_tracking_table.setItem(row, 1, exercise_item)
                
                # Diyet Durumu
                diet_item = QTableWidgetItem(record[2])
                diet_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Duruma göre renklendirme
                if record[2] == "Uygulandı":
                    diet_item.setBackground(QColor("#28a745"))
                    diet_item.setForeground(QColor("white"))
                else:
                    diet_item.setBackground(QColor("#dc3545"))
                    diet_item.setForeground(QColor("white"))
                self.daily_tracking_table.setItem(row, 2, diet_item)
                
                # Notlar
                notes_item = QTableWidgetItem(record[3] if record[3] else "")
                notes_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.daily_tracking_table.setItem(row, 3, notes_item)
            
            # Sütun genişliklerini ayarla
            self.daily_tracking_table.resizeColumnsToContents()
            self.daily_tracking_table.horizontalHeader().setStretchLastSection(True)
            
            # Minimum sütun genişliklerini ayarla
            self.daily_tracking_table.setColumnWidth(0, 200)  # Tarih
            self.daily_tracking_table.setColumnWidth(1, 150)  # Egzersiz
            self.daily_tracking_table.setColumnWidth(2, 150)  # Diyet
            self.daily_tracking_table.setColumnWidth(3, 700)  # Notlar
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Günlük takip verileri yüklenirken hata oluştu: {str(e)}")

    def save_daily_tracking(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Önce bugün için kayıt var mı kontrol et
            cursor.execute("""
                SELECT tracking_id FROM daily_tracking
                WHERE patient_id = %s AND DATE(tracking_date) = CURRENT_DATE
            """, (self.patient_id,))
            
            existing_record = cursor.fetchone()
            
            if existing_record:
                # Mevcut kaydı güncelle
                cursor.execute("""
                    UPDATE daily_tracking
                    SET exercise_status = %s, diet_status = %s, notes = %s
                    WHERE tracking_id = %s
                """, (
                    self.exercise_status.currentText(),
                    self.diet_status.currentText(),
                    self.daily_notes.toPlainText(),
                    existing_record[0]
                ))
            else:
                # Yeni kayıt ekle
                cursor.execute("""
                    INSERT INTO daily_tracking (patient_id, tracking_date, exercise_status, diet_status, notes)
                    VALUES (%s, CURRENT_DATE, %s, %s, %s)
                """, (
                    self.patient_id,
                    self.exercise_status.currentText(),
                    self.diet_status.currentText(),
                    self.daily_notes.toPlainText()
                ))
            
            conn.commit()
            QMessageBox.information(self, "Başarılı", "Günlük takip başarıyla kaydedildi!")
            
            # Formu temizle
            self.daily_notes.clear()
            
            # Tabloyu güncelle
            self.load_daily_tracking()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Günlük takip kaydedilirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def analyze_measurements(self):
        try:
            conn = psycopg2.connect(
                dbname='diabetes_monitoring_system',
                user='postgres',
                password='Esad1183*',
                host='localhost',
                port='5432'
            )
            cursor = conn.cursor()

            # Son 7 günün ölçümlerini getir
            cursor.execute("""
                SELECT blood_sugar_level, measurement_date
                FROM measurements
                WHERE patient_id = %s
                AND measurement_date >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY measurement_date
            """, (self.patient_id,))
            
            results = cursor.fetchall()
            
            # None değerleri filtrele ve geçerli ölçümleri al
            measurements = [
                (float(level), date) for level, date in results 
                if level is not None and date is not None
            ]

            if not measurements:
                self.analysis_label.setText("Son 7 günde ölçüm bulunamadı.")
                return

            # Ortalama kan şekeri
            avg_blood_sugar = sum(m[0] for m in measurements) / len(measurements)
            
            # En yüksek ve en düşük değerler
            max_blood_sugar = max(m[0] for m in measurements)
            min_blood_sugar = min(m[0] for m in measurements)
            
            # Normal aralıkta olan ölçümlerin yüzdesi
            normal_count = sum(1 for m in measurements if 70 <= m[0] <= 110)
            normal_percentage = (normal_count / len(measurements)) * 100

            # Analiz sonuçlarını göster
            analysis_text = f"""
            <h3>Son 7 Günün Analizi</h3>
            <p>Ortalama Kan Şekeri: {avg_blood_sugar:.1f} mg/dL</p>
            <p>En Yüksek Değer: {max_blood_sugar:.1f} mg/dL</p>
            <p>En Düşük Değer: {min_blood_sugar:.1f} mg/dL</p>
            <p>Normal Aralıkta Olan Ölçümler: %{normal_percentage:.1f}</p>
            """

            # Uyarı mesajları
            warnings = []
            if avg_blood_sugar < 70:
                warnings.append("⚠️ Ortalama kan şekeri düşük (Hipoglisemi riski)")
            elif avg_blood_sugar > 110:
                warnings.append("⚠️ Ortalama kan şekeri yüksek")
            
            if max_blood_sugar > 200:
                warnings.append("⚠️ Çok yüksek kan şekeri değerleri tespit edildi")
            if min_blood_sugar < 50:
                warnings.append("⚠️ Tehlikeli düşük kan şekeri değerleri tespit edildi")
            
            if normal_percentage < 50:
                warnings.append("⚠️ Ölçümlerin yarısından azı normal aralıkta")

            if warnings:
                analysis_text += "<h4>Uyarılar:</h4><ul>"
                for warning in warnings:
                    analysis_text += f"<li>{warning}</li>"
                analysis_text += "</ul>"

            self.analysis_label.setText(analysis_text)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hasta analizi yüklenirken hata oluştu: {str(e)}")
            self.analysis_label.setText("Analiz yüklenirken bir hata oluştu.")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def load_profile_image(self):
        try:
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.profile_image
                FROM users u
                JOIN patients p ON u.user_id = p.user_id
                WHERE p.patient_id = %s
            """, (self.patient_id,))
            
            result = cursor.fetchone()
            
            if result and result[0]:
                # Veritabanından gelen binary veriyi QPixmap'e dönüştür
                image_data = result[0]
                image = QImage.fromData(image_data)
                pixmap = QPixmap.fromImage(image)
                
                # Resmi yuvarlak yap ve boyutlandır
                pixmap = pixmap.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                
                # Yuvarlak maske oluştur
                rounded_pixmap = QPixmap(96, 96)
                rounded_pixmap.fill(Qt.GlobalColor.transparent)
                
                from PyQt6.QtGui import QPainter, QPainterPath
                painter = QPainter(rounded_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, 96, 96)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                
                self.profile_image_label.setPixmap(rounded_pixmap)
            else:
                # Varsayılan profil resmi
                self.profile_image_label.setText("👤")
                self.profile_image_label.setStyleSheet("""
                    QLabel {
                        border: 2px solid #4a90e2;
                        border-radius: 50px;
                        background-color: #f8f9fa;
                        font-size: 48px;
                    }
                """)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Profil resmi yüklenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def change_profile_image(self):
        try:
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Profil Resmi Seç",
                "",
                "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.gif)"
            )
            
            if file_name:
                # Resmi oku ve boyutlandır
                image = QImage(file_name)
                if image.isNull():
                    QMessageBox.warning(self, "Hata", "Seçilen dosya bir resim değil!")
                    return
                
                # Resmi 200x200'den büyükse küçült
                if image.width() > 200 or image.height() > 200:
                    image = image.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                
                # Resmi geçici dosyaya kaydet
                temp_file = "temp_profile.png"
                image.save(temp_file, "PNG")
                
                # Geçici dosyayı binary veriye dönüştür
                with open(temp_file, "rb") as f:
                    image_data = f.read()
                
                # Geçici dosyayı sil
                os.remove(temp_file)
                
                # Veritabanına kaydet
                conn = get_db_connection()
                if conn is None:
                    return
                    
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE users
                    SET profile_image = %s
                    FROM patients
                    WHERE users.user_id = patients.user_id
                    AND patients.patient_id = %s
                """, (image_data, self.patient_id))
                
                conn.commit()
                
                # Profil resmini güncelle
                self.load_profile_image()
                
                QMessageBox.information(self, "Başarılı", "Profil resmi başarıyla güncellendi!")
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Profil resmi güncellenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close() 

    def calculate_insulin_dose(self, blood_sugar):
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

class BloodSugarGraph(QWidget):
    def __init__(self, patient_id):
        super().__init__()
        self.patient_id = patient_id
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
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
        layout.addLayout(date_layout)
        layout.addWidget(update_btn)
        layout.addWidget(self.chart_view)
        
        self.setLayout(layout)
        
        # İlk grafiği oluştur
        self.update_graph()

    def update_graph(self):
        try:
            selected_date = self.date_edit.date().toPyDate()
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Seçilen tarihteki kan şekeri ölçümlerini al
            cursor.execute("""
                SELECT measurement_date, blood_sugar_level
                FROM measurements
                WHERE patient_id = %s 
                AND DATE(measurement_date) = %s
                ORDER BY measurement_date
            """, (self.patient_id, selected_date))
            
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
                self.chart.setTitle(f"{selected_date.strftime('%d.%m.%Y')} Kan Şekeri Takibi")
            else:
                self.chart.setTitle("Seçilen tarihte ölçüm bulunamadı")
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Grafik güncellenirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

class BloodSugarMeasurementDialog(QDialog):
    def __init__(self, patient_id, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.setWindowTitle("Kan Şekeri Ölçümü")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Ölçüm formu
        form_layout = QFormLayout()
        
        # Ölçüm zamanı seçimi
        self.measurement_time = QComboBox()
        self.measurement_time.addItems([
            "Sabah (07:00)",
            "Öğle (12:00)",
            "İkindi (15:00)",
            "Akşam (18:00)",
            "Gece (22:00)"
        ])
        form_layout.addRow("Ölçüm Zamanı:", self.measurement_time)
        
        # Kan şekeri değeri
        self.blood_sugar = QSpinBox()
        self.blood_sugar.setRange(0, 500)
        self.blood_sugar.setSuffix(" mg/dL")
        form_layout.addRow("Kan Şekeri:", self.blood_sugar)
        
        # Kaydet butonu
        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.save_measurement)
        
        layout.addLayout(form_layout)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)

    def save_measurement(self):
        try:
            # Seçilen zaman dilimine göre saat belirle
            time_slot = self.measurement_time.currentText()
            hour = 7  # Varsayılan sabah
            if "Öğle" in time_slot:
                hour = 12
            elif "İkindi" in time_slot:
                hour = 15
            elif "Akşam" in time_slot:
                hour = 18
            elif "Gece" in time_slot:
                hour = 22
            
            # Bugünün tarihini al ve seçilen saati ekle
            measurement_date = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
            
            conn = get_db_connection()
            if conn is None:
                return
                
            cursor = conn.cursor()
            
            # Aynı gün ve saat için ölçüm var mı kontrol et
            cursor.execute("""
                SELECT measurement_id FROM measurements 
                WHERE patient_id = %s 
                AND DATE(measurement_date) = DATE(%s)
                AND EXTRACT(HOUR FROM measurement_date) = %s
            """, (self.patient_id, measurement_date, hour))
            
            existing_measurement = cursor.fetchone()
            
            if existing_measurement:
                # Mevcut ölçümü güncelle
                cursor.execute("""
                    UPDATE measurements 
                    SET blood_sugar_level = %s
                    WHERE measurement_id = %s
                """, (self.blood_sugar.value(), existing_measurement[0]))
            else:
                # Yeni ölçüm ekle
                cursor.execute("""
                    INSERT INTO measurements (patient_id, measurement_date, blood_sugar_level)
                    VALUES (%s, %s, %s)
                """, (self.patient_id, measurement_date, self.blood_sugar.value()))
            
            conn.commit()
            QMessageBox.information(self, "Başarılı", "Ölçüm başarıyla kaydedildi!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ölçüm kaydedilirken hata oluştu: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close() 