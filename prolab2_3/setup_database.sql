-- Önce mevcut tabloları sil
DROP TABLE IF EXISTS doctor_recommendations;
DROP TABLE IF EXISTS measurements;
DROP TABLE IF EXISTS symptom_logs;
DROP TABLE IF EXISTS diet_logs;
DROP TABLE IF EXISTS exercise_logs;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS users;

-- Tabloları oluştur
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    tc_identity_number VARCHAR(11) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    birth_date DATE NOT NULL,
    gender CHAR(1) NOT NULL,
    profile_picture BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

-- İndeksleri oluştur
CREATE INDEX idx_users_tc_identity ON users(tc_identity_number);
CREATE INDEX idx_patients_doctor ON patients(doctor_id);
CREATE INDEX idx_measurements_patient ON measurements(patient_id);
CREATE INDEX idx_exercise_logs_patient ON exercise_logs(patient_id);
CREATE INDEX idx_diet_logs_patient ON diet_logs(patient_id);
CREATE INDEX idx_symptom_logs_patient ON symptom_logs(patient_id);
CREATE INDEX idx_recommendations_patient ON doctor_recommendations(patient_id);

-- Örnek doktor ekle
INSERT INTO users (tc_identity_number, password_hash, email, birth_date, gender)
VALUES (
    '12345678901',  -- TC Kimlik No
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKy7PqV5Z5QYz6G',  -- 'password123' şifresinin hash'i
    'doctor@example.com',
    '1980-01-01',
    'M'
);

INSERT INTO doctors (user_id, specialization, license_number)
VALUES (
    (SELECT user_id FROM users WHERE tc_identity_number = '12345678901'),
    'Endokrinoloji',
    'DR123456'
); 