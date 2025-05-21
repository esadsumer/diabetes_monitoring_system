import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import bcrypt
import time

# Veritabanı bağlantı bilgileri
DB_NAME = 'diabetes_monitoring_system'
DB_USER = 'postgres'
DB_PASSWORD = 'your_password'   
DB_HOST = 'localhost'
DB_PORT = '5432'

def terminate_connections():
    try:
        # postgres veritabanına bağlan
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Mevcut bağlantıları sonlandır
        cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{DB_NAME}'
            AND pid <> pg_backend_pid();
        """)
        
        cursor.close()
        conn.close()
        print("Mevcut bağlantılar sonlandırıldı.")
    except Exception as e:
        print(f"Bağlantıları sonlandırırken hata: {str(e)}")

def create_database():
    try:
        # Önce mevcut bağlantıları sonlandır
        terminate_connections()
        time.sleep(1)  # Bağlantıların kapanması için bekle
        
        # postgres veritabanına bağlan
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Eğer veritabanı varsa sil
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        print(f"{DB_NAME} veritabanı silindi (eğer varsa)")
        
        time.sleep(1)  # Veritabanının silinmesi için bekle
        
        # Yeni veritabanı oluştur
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"{DB_NAME} veritabanı oluşturuldu")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Veritabanı oluştururken hata: {str(e)}")
        return False

def create_tables():
    try:
        # Yeni veritabanına bağlan
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        
        # Tabloları oluştur
        cursor.execute("""
            DROP TABLE IF EXISTS doctor_recommendations CASCADE;
            DROP TABLE IF EXISTS measurements CASCADE;
            DROP TABLE IF EXISTS symptom_logs CASCADE;
            DROP TABLE IF EXISTS diet_logs CASCADE;
            DROP TABLE IF EXISTS exercise_logs CASCADE;
            DROP TABLE IF EXISTS daily_tracking CASCADE;
            DROP TABLE IF EXISTS patients CASCADE;
            DROP TABLE IF EXISTS doctors CASCADE;
            DROP TABLE IF EXISTS users CASCADE;

            CREATE TABLE users (
                user_id SERIAL PRIMARY KEY,
                tc_identity_number VARCHAR(11) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                birth_date DATE NOT NULL,
                gender CHAR(1) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE doctors (
                doctor_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                specialization VARCHAR(100),
                license_number VARCHAR(50) UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT true
            );

            CREATE TABLE patients (
                patient_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                doctor_id INTEGER REFERENCES doctors(doctor_id),
                diagnosis_date DATE,
                diabetes_type VARCHAR(50),
                is_active BOOLEAN DEFAULT true
            );

            CREATE TABLE measurements (
                measurement_id SERIAL PRIMARY KEY,
                patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
                blood_sugar_level DECIMAL(5,2),
                blood_pressure_systolic INTEGER,
                blood_pressure_diastolic INTEGER,
                weight DECIMAL(5,2),
                measurement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE doctor_recommendations (
                recommendation_id SERIAL PRIMARY KEY,
                doctor_id INTEGER REFERENCES doctors(doctor_id) ON DELETE CASCADE,
                patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
                recommendation_type VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT false
            );

            CREATE TABLE daily_tracking (
                tracking_id SERIAL PRIMARY KEY,
                patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
                tracking_date DATE NOT NULL,
                exercise_status VARCHAR(20) NOT NULL,
                diet_status VARCHAR(20) NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE exercise_logs (
                log_id SERIAL PRIMARY KEY,
                patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
                exercise_type VARCHAR(100) NOT NULL,
                duration_minutes INTEGER NOT NULL,
                intensity VARCHAR(50),
                notes TEXT,
                log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE diet_logs (
                log_id SERIAL PRIMARY KEY,
                patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
                meal_type VARCHAR(50) NOT NULL,
                food_items TEXT NOT NULL,
                calories INTEGER,
                carbohydrates INTEGER,
                notes TEXT,
                log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE symptom_logs (
                log_id SERIAL PRIMARY KEY,
                patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
                symptom_type VARCHAR(100) NOT NULL,
                severity INTEGER CHECK (severity BETWEEN 1 AND 10),
                notes TEXT,
                log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Tablolar oluşturuldu")
        
        # Örnek doktor ekle
        password = 'password123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
            INSERT INTO users (tc_identity_number, password_hash, email, birth_date, gender)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id
        """, ('12345678901', password_hash, 'doctor@example.com', '1980-01-01', 'M'))
        
        user_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO doctors (user_id, specialization, license_number)
            VALUES (%s, %s, %s)
        """, (user_id, 'Endokrinoloji', 'DR123456'))
        
        print("Örnek doktor hesabı oluşturuldu")
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Tabloları oluştururken hata: {str(e)}")
        return False

if __name__ == "__main__":
    print("Veritabanı kurulum işlemi başlıyor...")
    if create_database():
        time.sleep(2)  # Veritabanının oluşturulması için bekle
        if create_tables():
            print("\nKurulum başarıyla tamamlandı!")
            print("\nDoktor giriş bilgileri:")
            print("TC Kimlik No: 12345678901")
            print("Şifre: password123")
        else:
            print("Tablolar oluşturulurken hata oluştu!")
    else:
        print("Veritabanı oluşturulurken hata oluştu!") 