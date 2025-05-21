from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QDoubleSpinBox, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, QDateTime, QTime
from PyQt6.QtGui import QColor
import psycopg2
from datetime import datetime, time, timedelta
from insulin_recommendation import InsulinRecommendationSystem

class BloodSugarMeasurementDialog(QDialog):
    def __init__(self, patient_id, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.insulin_system = InsulinRecommendationSystem(patient_id)
        self.setWindowTitle("Kan Şekeri Ölçümü")
        self.setup_ui()
        self.check_measurement_time()
        self.load_todays_measurements()

    def load_todays_measurements(self):
        try:
            conn = psycopg2.connect(
                dbname='diabetes_monitoring_system',
                user='postgres',
                password='your_password',
                host='localhost',
                port='5432'
            )
            cursor = conn.cursor()

            # Bugünün başlangıcını al
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Bugünkü ölçümleri getir
            cursor.execute("""
                SELECT blood_sugar_level, measurement_date
                FROM measurements
                WHERE patient_id = %s AND measurement_date >= %s
                ORDER BY measurement_date
            """, (int(self.patient_id), today))
            
            results = cursor.fetchall()
            
            # None değerleri filtrele ve geçerli ölçümleri al
            self.todays_measurements = [
                (float(level), date) for level, date in results 
                if level is not None and date is not None
            ]
            
            # Ortalama hesapla ve insülin önerisi göster
            self.calculate_average_and_insulin()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ölçümler yüklenirken hata oluştu: {str(e)}")
            self.todays_measurements = []  # Hata durumunda boş liste
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def calculate_average_and_insulin(self):
        if not self.todays_measurements:
            self.average_label.setText("Bugün henüz ölçüm yapılmamış.")
            self.insulin_label.setText("İnsülin önerisi için ölçüm gerekli.")
            self.level_label.setText("Kan Şekeri Seviyesi: Ölçüm Yok")
            return

        # Seçilen ölçüm zamanına göre değerlendirilecek ölçümleri belirle
        selected_time = self.measurement_time.currentText()
        
        try:
            if "Sabah" in selected_time:
                measurements = [m[0] for m in self.todays_measurements if m[1].hour == 7]
                period = "Sabah"
            elif "Öğle" in selected_time:
                measurements = [m[0] for m in self.todays_measurements if m[1].hour in [7, 12]]
                period = "Öğlen"
            elif "İkindi" in selected_time:
                measurements = [m[0] for m in self.todays_measurements if m[1].hour in [7, 12, 15]]
                period = "İkindi"
            elif "Akşam" in selected_time:
                measurements = [m[0] for m in self.todays_measurements if m[1].hour in [7, 12, 15, 18]]
                period = "Akşam"
            elif "Gece" in selected_time:
                measurements = [m[0] for m in self.todays_measurements if m[1].hour in [7, 12, 15, 18, 22]]
                period = "Gece"
            else:
                self.average_label.setText("Lütfen bir ölçüm zamanı seçin.")
                self.insulin_label.setText("İnsülin önerisi için ölçüm zamanı seçilmeli.")
                self.level_label.setText("Kan Şekeri Seviyesi: Seçim Gerekli")
                return

            if not measurements:
                self.average_label.setText(f"{period} ölçümü için önceki ölçümler bulunamadı.")
                self.insulin_label.setText("İnsülin önerisi için önceki ölçümler gerekli.")
                self.level_label.setText(f"Kan Şekeri Seviyesi: {period} Ölçümü Yok")
                return

            # Ortalama hesapla
            average = sum(measurements) / len(measurements)
            self.average_label.setText(f"Ortalama Kan Şekeri: {average:.1f} mg/dL")

            # İnsülin dozu önerisi
            if average < 70:
                insulin_dose = "Hipoglisemi riski! İnsülin dozu verilmemeli."
                color = "#dc3545"  # Kırmızı
                level_info = "Hipoglisemi"
            elif 70 <= average <= 99:
                insulin_dose = "Normal seviye. İnsülin dozu verilmemeli."
                color = "#28a745"  # Yeşil
                level_info = "Normal"
            elif 100 <= average <= 125:
                insulin_dose = "Orta yüksek seviye. 1 ml insülin dozu önerilir."
                color = "#ffc107"  # Sarı
                level_info = "Orta Yüksek"
            else:
                insulin_dose = "Çok yüksek seviye. 3 ml insülin dozu önerilir."
                color = "#dc3545"  # Kırmızı
                level_info = "Çok Yüksek"

            self.insulin_label.setText(insulin_dose)
            self.insulin_label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    background-color: #f8f9fa;
                    font-size: 14px;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid {color};
                }}
            """)

            self.level_label.setText(f"Kan Şekeri Seviyesi: {level_info}")
            self.level_label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    background-color: #f8f9fa;
                    font-size: 14px;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid {color};
                    text-align: center;
                }}
            """)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ortalama hesaplanırken hata oluştu: {str(e)}")
            self.average_label.setText("Hesaplama hatası!")
            self.insulin_label.setText("İnsülin önerisi hesaplanamadı.")
            self.level_label.setText("Kan Şekeri Seviyesi: Hata")

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Ölçüm zamanı bilgisi
        self.time_info_label = QLabel()
        self.time_info_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.time_info_label)

        # Kan Şekeri Seviyeleri Bilgisi
        levels_info = QLabel("Kan Şekeri Seviyeleri:\n"
                           "• Düşük Seviye (Hipoglisemi): < 70 mg/dL\n"
                           "• Normal Seviye: 70 – 99 mg/dL\n"
                           "• Orta Seviye (Prediyabet): 100 – 125 mg/dL\n"
                           "• Yüksek Seviye (Diyabet): ≥ 126 mg/dL")
        levels_info.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e1e1e1;
            }
        """)
        layout.addWidget(levels_info)

        # Kan Şekeri
        sugar_layout = QHBoxLayout()
        self.blood_sugar = QDoubleSpinBox()
        self.blood_sugar.setRange(0, 1000)
        self.blood_sugar.setSuffix(" mg/dL")
        self.blood_sugar.setStyleSheet("""
            QDoubleSpinBox {
                padding: 10px;
                border: 2px solid #e1e1e1;
                border-radius: 5px;
                font-size: 14px;
                min-height: 40px;
            }
            QDoubleSpinBox:focus {
                border-color: #4a90e2;
            }
        """)
        self.blood_sugar.valueChanged.connect(self.check_blood_sugar_level)
        sugar_layout.addWidget(QLabel("Kan Şekeri:"))
        sugar_layout.addWidget(self.blood_sugar)
        layout.addLayout(sugar_layout)

        # Kan Şekeri Seviyesi Göstergesi
        self.level_label = QLabel()
        self.level_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                text-align: center;
            }
        """)
        layout.addWidget(self.level_label)

        # Ortalama Kan Şekeri Göstergesi
        self.average_label = QLabel()
        self.average_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e1e1e1;
            }
        """)
        layout.addWidget(self.average_label)

        # İnsülin Önerisi Göstergesi
        self.insulin_label = QLabel()
        self.insulin_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e1e1e1;
            }
        """)
        layout.addWidget(self.insulin_label)

        # Ölçüm zamanı seçimi
        time_layout = QHBoxLayout()
        self.measurement_time = QComboBox()
        self.measurement_time.addItems([
            "Sabah Ölçümü (07:00 - 08:00)",
            "Öğle Ölçümü (12:00 - 13:00)",
            "İkindi Ölçümü (15:00 - 16:00)",
            "Akşam Ölçümü (18:00 - 19:00)",
            "Gece Ölçümü (22:00 - 23:00)"
        ])
        self.measurement_time.currentTextChanged.connect(self.update_recommendation)
        time_layout.addWidget(QLabel("Ölçüm Zamanı:"))
        time_layout.addWidget(self.measurement_time)
        layout.addLayout(time_layout)

        # Kaydet butonu
        save_btn = QPushButton("Ölçümü Kaydet")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2d6da3;
            }
        """)
        save_btn.clicked.connect(self.save_measurement)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def update_recommendation(self):
        current_time = datetime.now().time()
        recommendation = self.insulin_system.get_insulin_recommendation(current_time)
        
        if recommendation['dose'] is None:
            self.insulin_label.setText(recommendation['message'])
            self.insulin_label.setStyleSheet(f"""
                QLabel {{
                    color: {recommendation['color']};
                    background-color: #f8f9fa;
                    font-size: 14px;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid {recommendation['color']};
                }}
            """)
            return

        self.insulin_label.setText(recommendation['message'])
        self.insulin_label.setStyleSheet(f"""
            QLabel {{
                color: {recommendation['color']};
                background-color: #f8f9fa;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid {recommendation['color']};
            }}
        """)

    def check_blood_sugar_level(self):
        value = self.blood_sugar.value()
        if value < 70:
            self.level_label.setText("⚠️ Düşük Seviye (Hipoglisemi)")
            self.level_label.setStyleSheet("""
                QLabel {
                    color: #dc3545;
                    background-color: #f8d7da;
                    font-size: 14px;
                    padding: 10px;
                    border-radius: 5px;
                    text-align: center;
                }
            """)
        elif 70 <= value <= 99:
            self.level_label.setText("✅ Normal Seviye")
            self.level_label.setStyleSheet("""
                QLabel {
                    color: #28a745;
                    background-color: #d4edda;
                    font-size: 14px;
                    padding: 10px;
                    border-radius: 5px;
                    text-align: center;
                }
            """)
        elif 100 <= value <= 125:
            self.level_label.setText("⚠️ Orta Seviye (Prediyabet)")
            self.level_label.setStyleSheet("""
                QLabel {
                    color: #ffc107;
                    background-color: #fff3cd;
                    font-size: 14px;
                    padding: 10px;
                    border-radius: 5px;
                    text-align: center;
                }
            """)
        else:
            self.level_label.setText("⚠️ Yüksek Seviye (Diyabet)")
            self.level_label.setStyleSheet("""
                QLabel {
                    color: #dc3545;
                    background-color: #f8d7da;
                    font-size: 14px;
                    padding: 10px;
                    border-radius: 5px;
                    text-align: center;
                }
            """)

    def check_measurement_time(self):
        current_time = QDateTime.currentDateTime().time()
        current_hour = current_time.hour()
        
        # Ölçüm zamanı önerisi
        if 7 <= current_hour < 8:
            self.measurement_time.setCurrentText("Sabah Ölçümü (07:00 - 08:00)")
            self.time_info_label.setText("Sabah ölçümü için uygun zaman dilimindesiniz.")
            self.time_info_label.setStyleSheet("""
                QLabel {
                    color: #28a745;
                    background-color: #d4edda;
                    font-size: 14px;
                    padding: 10px;
                    border-radius: 5px;
                }
            """)
        elif 12 <= current_hour < 13:
            self.measurement_time.setCurrentText("Öğle Ölçümü (12:00 - 13:00)")
            self.time_info_label.setText("Öğle ölçümü için uygun zaman dilimindesiniz.")
            self.time_info_label.setStyleSheet("""
                QLabel {
                    color: #28a745;
                    background-color: #d4edda;
                    font-size: 14px;
                    padding: 10px;
                    border-radius: 5px;
                }
            """)
        elif 15 <= current_hour < 16:
            self.measurement_time.setCurrentText("İkindi Ölçümü (15:00 - 16:00)")
            self.time_info_label.setText("İkindi ölçümü için uygun zaman dilimindesiniz.")
            self.time_info_label.setStyleSheet("""
                QLabel {
                    color: #28a745;
                    background-color: #d4edda;
                    font-size: 14px;
                    padding: 10px;
                    border-radius: 5px;
                }
            """)
        elif 18 <= current_hour < 19:
            self.measurement_time.setCurrentText("Akşam Ölçümü (18:00 - 19:00)")
            self.time_info_label.setText("Akşam ölçümü için uygun zaman dilimindesiniz.")
            self.time_info_label.setStyleSheet("""
                QLabel {
                    color: #28a745;
                    background-color: #d4edda;
                    font-size: 14px;
                    padding: 10px;
                    border-radius: 5px;
                }
            """)
        elif 22 <= current_hour < 23:
            self.measurement_time.setCurrentText("Gece Ölçümü (22:00 - 23:00)")
            self.time_info_label.setText("Gece ölçümü için uygun zaman dilimindesiniz.")
            self.time_info_label.setStyleSheet("""
                QLabel {
                    color: #28a745;
                    background-color: #d4edda;
                    font-size: 14px;
                    padding: 10px;
                    border-radius: 5px;
                }
            """)
        else:
            self.time_info_label.setText("⚠️ Şu anda önerilen ölçüm zamanı değil, ancak istediğiniz ölçümü seçebilirsiniz.")
            self.time_info_label.setStyleSheet("""
                QLabel {
                    color: #ffc107;
                    background-color: #fff3cd;
                    font-size: 14px;
                    padding: 10px;
                    border-radius: 5px;
                }
            """)

    def save_measurement(self):
        # Kan şekeri seviyesi kontrolü
        value = self.blood_sugar.value()
        if value < 70:
            reply = QMessageBox.warning(self, "Düşük Kan Şekeri Uyarısı",
                                      "Kan şekeri seviyeniz düşük (Hipoglisemi)! Ölçümü kaydetmek istediğinizden emin misiniz?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return
        elif value >= 126:
            reply = QMessageBox.warning(self, "Yüksek Kan Şekeri Uyarısı",
                                      "Kan şekeri seviyeniz yüksek (Diyabet)! Ölçümü kaydetmek istediğinizden emin misiniz?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        try:
            conn = psycopg2.connect(
                dbname='diabetes_monitoring_system',
                user='postgres',
                password='Esad1183*',
                host='localhost',
                port='5432'
            )
            cursor = conn.cursor()

            # Ölçümü kaydet
            cursor.execute("""
                INSERT INTO measurements (patient_id, blood_sugar_level, measurement_date)
                VALUES (%s, %s, %s)
            """, (
                int(self.patient_id),
                self.blood_sugar.value(),
                datetime.now()
            ))

            conn.commit()
            QMessageBox.information(self, "Başarılı", "Kan şekeri ölçümü başarıyla kaydedildi!")
            
            # Ölçümleri yeniden yükle ve ortalamaları güncelle
            self.update_recommendation()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veritabanı hatası: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close() 