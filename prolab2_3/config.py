import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Veritabanı bağlantı ayarları
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'diabetes_monitoring_system'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'your_password'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

# Uygulama ayarları
APP_CONFIG = {
    'title': 'Diyabet Takip Sistemi',
    'version': '1.0.0',
    'min_width': 800,
    'min_height': 600
}

# Güvenlik ayarları
SECURITY_CONFIG = {
    'password_salt_rounds': 12,
    'session_timeout': 3600  # saniye cinsinden
} 