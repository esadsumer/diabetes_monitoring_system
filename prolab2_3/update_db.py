import psycopg2
from psycopg2 import sql

# Veritabanı bağlantı bilgileri
DB_CONFIG = {
    'dbname': 'diabetes_monitoring_system',
    'user': 'postgres',
    'password': 'your_password',
    'host': 'localhost',
    'port': '5432'
}

def update_database():
    try:
        # Veritabanına bağlan
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # users tablosuna profile_image sütunu ekle
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS profile_image BYTEA;
        """)

        # Değişiklikleri kaydet
        conn.commit()
        print("Veritabanı başarıyla güncellendi!")

    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_database() 