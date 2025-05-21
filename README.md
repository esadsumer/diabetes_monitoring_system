Diyabet Hasta Takip Sistemi
Bu proje, diyabet hastalarının sağlık verilerini etkili bir biçimde izlemek, yorumlamak ve hem hastaya hem de hekime zamanında uyarılar sağlamak amacıyla geliştirilmiştir.

Sistem Özellikleri
Kullanıcı yönetimi (Doktor ve Hasta)
T.C. kimlik numarası ile giriş
Profil fotoğrafı desteği
Egzersiz takibi
Diyet takibi
Semptom takibi
Ölçüm verileri girişi
Doktor önerileri
Veritabanı Yapısı
Sistem PostgreSQL veritabanı kullanmaktadır. Veritabanı şeması aşağıdaki tabloları içerir:

users: Temel kullanıcı bilgileri
doctors: Doktor özel bilgileri
patients: Hasta özel bilgileri
exercise_logs: Egzersiz kayıtları
diet_logs: Diyet kayıtları
symptom_logs: Semptom kayıtları
measurements: Ölçüm verileri
doctor_recommendations: Doktor önerileri
Kurulum
PostgreSQL veritabanını yükleyin
schema.sql dosyasını çalıştırarak veritabanını oluşturun:
psql -U postgres -f schema.sql
Güvenlik
Tüm şifreler veritabanında hash'lenmiş olarak saklanır
T.C. kimlik numaraları benzersiz olarak tanımlanmıştır
Kullanıcı yetkilendirmesi rol tabanlıdır
Kullanıcı Tipleri
Doktor
Sisteme önceden tanımlanmış kullanıcı adı ve şifre ile giriş
Hasta tanımlama
Hasta verilerini görüntüleme
Öneri girme
Hasta
Doktor tarafından tanımlandıktan sonra e-posta ile gönderilen bilgilerle giriş
Egzersiz takibi
Diyet takibi
Semptom takibi
Ölçüm verilerini girme
