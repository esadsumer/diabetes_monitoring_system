from datetime import datetime, time
import psycopg2
from PyQt6.QtWidgets import QMessageBox

class InsulinRecommendationSystem:
    def __init__(self, patient_id):
        self.patient_id = patient_id
        self.measurement_times = {
            'morning': time(7, 0),    # 07:00
            'noon': time(12, 0),      # 12:00
            'afternoon': time(15, 0),  # 15:00
            'evening': time(18, 0),    # 18:00
            'night': time(22, 0)       # 22:00
        }

    def get_todays_measurements(self):
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
            """, (self.patient_id, today))
            
            return cursor.fetchall()

        except Exception as e:
            QMessageBox.critical(None, "Hata", f"Ölçümler yüklenirken hata oluştu: {str(e)}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def get_measurements_for_period(self, current_time):
        measurements = self.get_todays_measurements()
        if not measurements:
            return None

        current_hour = current_time.hour
        relevant_measurements = []

        # Sabah ölçümü (07:00)
        if current_hour == 7:
            for measurement in measurements:
                if measurement[1].hour == 7:
                    relevant_measurements.append(measurement[0])
            return relevant_measurements[0] if relevant_measurements else None

        # Öğlen ölçümü (12:00)
        elif current_hour == 12:
            for measurement in measurements:
                if measurement[1].hour in [7, 12]:
                    relevant_measurements.append(measurement[0])
            return sum(relevant_measurements) / len(relevant_measurements) if relevant_measurements else None

        # İkindi ölçümü (15:00)
        elif current_hour == 15:
            for measurement in measurements:
                if measurement[1].hour in [7, 12, 15]:
                    relevant_measurements.append(measurement[0])
            return sum(relevant_measurements) / len(relevant_measurements) if relevant_measurements else None

        # Akşam ölçümü (18:00)
        elif current_hour == 18:
            for measurement in measurements:
                if measurement[1].hour in [7, 12, 15, 18]:
                    relevant_measurements.append(measurement[0])
            return sum(relevant_measurements) / len(relevant_measurements) if relevant_measurements else None

        # Gece ölçümü (22:00)
        elif current_hour == 22:
            for measurement in measurements:
                if measurement[1].hour in [7, 12, 15, 18, 22]:
                    relevant_measurements.append(measurement[0])
            return sum(relevant_measurements) / len(relevant_measurements) if relevant_measurements else None

        return None

    def get_insulin_recommendation(self, current_time):
        average_blood_sugar = self.get_measurements_for_period(current_time)
        
        if average_blood_sugar is None:
            return {
                'dose': None,
                'message': "İnsülin önerisi için yeterli ölçüm bulunmamaktadır.",
                'color': "#6c757d"  # Gri
            }

        # İnsülin dozu önerisi
        if average_blood_sugar < 70:
            return {
                'dose': 0,
                'message': "Hipoglisemi riski! İnsülin dozu verilmemeli.",
                'color': "#dc3545"  # Kırmızı
            }
        elif 70 <= average_blood_sugar <= 99:
            return {
                'dose': 0,
                'message': "Normal seviye. İnsülin dozu verilmemeli.",
                'color': "#28a745"  # Yeşil
            }
        elif 100 <= average_blood_sugar <= 125:
            return {
                'dose': 1,
                'message': "Prediyabet seviyesi. 1 ml insülin dozu önerilir.",
                'color': "#ffc107"  # Sarı
            }
        else:  # >= 126
            return {
                'dose': 2,
                'message': "Diyabet seviyesi. 2 ml insülin dozu önerilir.",
                'color': "#dc3545"  # Kırmızı
            } 