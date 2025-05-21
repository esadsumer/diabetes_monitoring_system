import psycopg2
from datetime import datetime

# Veritabanı bağlantı bilgileri
DB_CONFIG = {
    'dbname': 'diabetes_monitoring_system',
    'user': 'postgres',
    'password': 'your_password',
    'host': 'localhost',
    'port': '5432'
}

def check_recommendations():
    try:
        # Veritabanına bağlan
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Son 5 öneriyi al
        cursor.execute("""
            SELECT r.created_at, u.tc_identity_number, r.recommendation_type, r.content
            FROM doctor_recommendations r
            JOIN patients p ON r.patient_id = p.patient_id
            JOIN users u ON p.user_id = u.user_id
            ORDER BY r.created_at DESC
            LIMIT 5
        """)
        
        recommendations = cursor.fetchall()
        
        print("\nSon 5 Öneri:")
        print("-" * 80)
        for rec in recommendations:
            print(f"Tarih: {rec[0]}")
            print(f"Hasta TC: {rec[1]}")
            print(f"Öneri Türü: {rec[2]}")
            print(f"İçerik: {rec[3]}")
            print("-" * 80)
            
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_recommendations() 