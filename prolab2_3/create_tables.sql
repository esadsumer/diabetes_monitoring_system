-- Önce mevcut tabloları sil
DROP TABLE IF EXISTS doctor_recommendations;
DROP TABLE IF EXISTS measurements;
DROP TABLE IF EXISTS symptom_logs;
DROP TABLE IF EXISTS diet_logs;
DROP TABLE IF EXISTS exercise_logs;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS diet_types;
DROP TABLE IF EXISTS exercise_types;
DROP TABLE IF EXISTS symptoms;
DROP TABLE IF EXISTS blood_sugar_levels;
DROP TABLE IF EXISTS daily_tracking;

-- Tabloları oluştur
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    tc_identity_number VARCHAR(11) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    birth_date DATE NOT NULL,
    gender CHAR(1) NOT NULL
);

CREATE TABLE doctors (
    doctor_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    specialization VARCHAR(100),
    license_number VARCHAR(20) UNIQUE NOT NULL
);

CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    doctor_id INTEGER REFERENCES doctors(doctor_id),
    diagnosis_date DATE NOT NULL,
    diabetes_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE diet_types (
    diet_type_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE exercise_types (
    exercise_type_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE symptoms (
    symptom_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE blood_sugar_levels (
    level_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    min_value DECIMAL(5,2),
    max_value DECIMAL(5,2),
    description TEXT NOT NULL
);

CREATE TABLE measurements (
    measurement_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id),
    blood_sugar_level DECIMAL(5,2),
    blood_pressure_systolic INTEGER,
    blood_pressure_diastolic INTEGER,
    weight DECIMAL(5,2),
    measurement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE doctor_recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    doctor_id INTEGER REFERENCES doctors(doctor_id),
    patient_id INTEGER REFERENCES patients(patient_id),
    recommendation_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT false
);

CREATE TABLE daily_tracking (
    tracking_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id),
    tracking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exercise_status VARCHAR(20) NOT NULL,
    diet_status VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Örnek verileri ekle
INSERT INTO users (tc_identity_number, password_hash, email, birth_date, gender)
VALUES (
    '12345678901',
    '$2b$12$mFmLMDYTFXAb1lDXU1tjU.w45rZI1VXbQqHc8rLy9J1upvcHfqW6e',
    'doctor@example.com',
    '1980-01-01',
    'M'
) ON CONFLICT (tc_identity_number) DO NOTHING;

INSERT INTO doctors (user_id, specialization, license_number)
VALUES (
    (SELECT user_id FROM users WHERE tc_identity_number = '12345678901'),
    'Endokrinoloji',
    'DR123456'
) ON CONFLICT (license_number) DO NOTHING;

INSERT INTO users (tc_identity_number, password_hash, email, birth_date, gender)
VALUES (
    '98765432109',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBAQK3J9J5QK8y',
    'patient@example.com',
    '1990-01-01',
    'F'
) ON CONFLICT (tc_identity_number) DO NOTHING;

INSERT INTO patients (user_id, doctor_id, diagnosis_date, diabetes_type)
VALUES (
    (SELECT user_id FROM users WHERE tc_identity_number = '98765432109'),
    (SELECT doctor_id FROM doctors WHERE license_number = 'DR123456'),
    '2024-01-01',
    'Tip 2'
) ON CONFLICT DO NOTHING;

-- Diyet türleri
INSERT INTO diet_types (name, description) VALUES
('Az Şekerli Diyet', 'Şekerli gıdalar sınırlanır, kompleks karbonhidratlara öncelik verilir. Lifli gıdalar ve düşük glisemik indeksli besinler tercih edilir.'),
('Şekersiz Diyet', 'Rafine şeker ve şeker katkılı tüm ürünler tamamen dışlanır. Hiperglisemi riski taşıyan bireylerde önerilir.'),
('Dengeli Beslenme', 'Diyabetli bireylerin yaşam tarzına uygun, dengeli ve sürdürülebilir bir diyet yaklaşımıdır. Tüm besin gruplarından yeterli miktarda alınır; porsiyon kontrolü, mevsimsel taze ürünler ve su tüketimi temel unsurlardır.');

-- Egzersiz türleri
INSERT INTO exercise_types (name, description) VALUES
('Yürüyüş', 'Hafif tempolu, günlük yapılabilecek bir egzersizdir.'),
('Bisiklet', 'Alt vücut kaslarını çalıştırır ve dış mekanda veya sabit bisikletle uygulanabilir.'),
('Klinik Egzersiz', 'Doktor tarafından verilen belirli hareketleri içeren planlı egzersizlerdir. Stresi azaltılması ve hareket kabiliyetinin artırılması amaçlanır.');

-- Belirtiler
INSERT INTO symptoms (name, description) VALUES
('Poliüri', 'Sık idrara çıkma'),
('Polifaji', 'Aşırı açlık hissi'),
('Polidipsi', 'Aşırı susama hissi'),
('Nöropati', 'El ve ayaklarda karıncalanma veya uyuşma hissi'),
('Kilo kaybı', 'Açıklanamayan kilo kaybı'),
('Yorgunluk', 'Sürekli yorgunluk hissi'),
('Yaraların yavaş iyileşmesi', 'Yaraların normalden daha yavaş iyileşmesi'),
('Bulanık görme', 'Görme keskinliğinde azalma');

-- Kan şekeri seviyeleri
INSERT INTO blood_sugar_levels (name, min_value, max_value, description) VALUES
('Düşük Seviye (Hipoglisemi)', NULL, 69.99, 'Kan şekeri seviyesi 70 mg/dL''nin altında'),
('Normal Seviye', 70, 99, 'Normal kan şekeri seviyesi'),
('Orta Seviye (Prediyabet)', 100, 125, 'Prediyabet riski taşıyan kan şekeri seviyesi'),
('Yüksek Seviye (Diyabet)', 126, NULL, 'Diyabet teşhisi için yüksek kan şekeri seviyesi');

-- Günlük takip için otomatik kayıt fonksiyonu
CREATE OR REPLACE FUNCTION check_daily_tracking()
RETURNS void AS $$
BEGIN
    -- Bugün için kayıt olmayan aktif hastaları bul
    INSERT INTO daily_tracking (patient_id, tracking_date, exercise_status, diet_status, notes)
    SELECT 
        p.patient_id,
        CURRENT_DATE,
        'Yapılmadı',
        'Yapılmadı',
        'Otomatik kayıt: Kullanıcı günlük takip bilgisi girmemiş'
    FROM patients p
    WHERE p.is_active = true
    AND NOT EXISTS (
        SELECT 1 
        FROM daily_tracking dt 
        WHERE dt.patient_id = p.patient_id 
        AND DATE(dt.tracking_date) = CURRENT_DATE
    );
END;
$$ LANGUAGE plpgsql;

-- Her gün gece yarısı çalışacak trigger
CREATE OR REPLACE FUNCTION create_daily_tracking_trigger()
RETURNS trigger AS $$
BEGIN
    PERFORM check_daily_tracking();
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Gece yarısı trigger'ı oluştur
CREATE OR REPLACE TRIGGER daily_tracking_trigger
    AFTER INSERT ON daily_tracking
    FOR EACH STATEMENT
    EXECUTE FUNCTION create_daily_tracking_trigger();

-- İlk çalıştırma için fonksiyonu çağır
SELECT check_daily_tracking(); 