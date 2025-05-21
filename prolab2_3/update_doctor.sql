-- Önce mevcut kayıtları temizle
DELETE FROM doctors WHERE license_number = 'DR123456';
DELETE FROM users WHERE tc_identity_number = '12345678901';

-- Yeni şifre hash'i ile doktor ekle
INSERT INTO users (tc_identity_number, password_hash, email, birth_date, gender)
VALUES (
    '12345678901',  -- TC Kimlik No
    '$2b$12$mFmLMDYTFXAb1lDXU1tjU.w45rZI1VXbQqHc8rLy9J1upvcHfqW6e',  -- Yeni 'password123' şifresinin hash'i
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

CREATE DATABASE diabetes_monitoring_system; 