# Changelog

Tüm önemli değişiklikler bu dosyada belgelenecektir.

Format [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standardını takip eder.
Versiyon numaralandırması [Semantic Versioning](https://semver.org/spec/v2.0.0.html) kullanır.

## [Unreleased]

### Planlanan Özellikler
- [ ] Docker container desteği
- [ ] PostgreSQL desteği
- [ ] Redis cache entegrasyonu
- [ ] RESTful API endpoint'leri
- [ ] React/Vue.js frontend
- [ ] Multi-language support (English)
- [ ] Mobile app (React Native)
- [ ] Email bildirimleri
- [ ] Slack entegrasyonu

## [1.0.0] - 2025-01-01

### 🎉 İlk Stabil Sürüm

#### Eklenen Özellikler

##### Kariyer Takip Motoru
- **Scopus API Entegrasyonu**: Elsevier Scopus API ile yayın verisi çekme
- **Google Scholar Bot**: Selenium ile profil tarama
- **YÖK Bot**: YÖK Akademik veritabanı scraper'ı
- **IEEE Xplore Bot**: IEEE yayınlarını tarama
- **Akıllı Karşılaştırma**: Fuzzy matching ile yayın eşleştirme
- **Detaylı Raporlama**: Scopus vs YÖK analiz raporu
- **Yayıncı Gruplama**: IEEE, Springer, Elsevier vb. kategorize etme

##### Feed Motoru
- **ArXiv Scraper**: Kategori bazlı makale tarama
- **Semantic Scholar API**: Anahtar kelime bazlı arama
- **Vector Engine**: ChromaDB ile semantic matching
- **PDF Processor**: Tam metin çıkarma ve analiz
- **AI Summarizer**: Gemini 1.5 ile özet oluşturma
- **Text-to-Speech**: gTTS ile sesli özet
- **30 Dakika Soru-Cevap**: Makaleler hakkında AI sohbet

##### Bildirim Sistemleri
- **Telegram Bot**: 
  - Otomatik makale gönderimi
  - İnteraktif sohbet
  - Ses mesajı desteği
  - Reply-based Q&A
- **WhatsApp Cloud API**:
  - Webhook entegrasyonu
  - Template mesajları
  - Audio mesaj gönderimi
  - Pending paper sistemi

##### Web Platformu
- **Kullanıcı Yönetimi**: Kayıt, login, profil
- **Dashboard**: Kariyer istatistikleri ve geçmiş
- **Mendeley Entegrasyonu**: OAuth ile otomatik kütüphane
- **Karşılaştırma Sayfası**: Detaylı yayın analizi
- **Admin Panel**: Bölüm raporları
- **Stil Tercihleri**: Samimi/Akademik/Teknik
- **Detay Seviyeleri**: Kısa/Orta/Detaylı

#### Teknik İyileştirmeler
- SQLite WAL mode ile performans artışı
- Efficient caching sistemi (30 dakika TTL)
- Rate limiting (Scopus API için)
- Undetected ChromeDriver ile bot koruması bypass
- Multi-threading support
- Error handling ve logging

#### Veritabanı
- Kullanıcı tablosu (admin desteği)
- Profil tablosu (multi-platform ID'ler)
- Makale geçmişi (full text + message ID)
- Proje tablosu
- Pending papers (WhatsApp için)

#### Dokümantasyon
- ✅ Kapsamlı README.md
- ✅ CONTRIBUTING.md
- ✅ LICENSE (MIT)
- ✅ .env.example
- ✅ CHANGELOG.md
- ✅ Detaylı kod yorumları

### Düzeltilen Hatalar
- YÖK ID çözümleme problemi
- Scopus pagination hataları
- Telegram reply tracking
- WhatsApp webhook doğrulama
- PDF download timeout'ları
- Duplicate publication detection

### Bilinen Sorunlar
- Bazı üniversiteler için YÖK scraping yavaş
- IEEE Xplore recaptcha ile bloklanabiliyor
- WhatsApp Business API approval süreci uzun
- Büyük PDF'ler için memory kullanımı yüksek

## [0.9.0] - 2024-12-20

### Beta Sürümü
- Temel özellikler tamamlandı
- Kapsamlı test edildi
- Kullanıcı feedbackları toplandı

## [0.5.0] - 2024-12-01

### Alpha Sürümü
- Proof of concept
- Temel Scopus ve ArXiv entegrasyonu
- Flask web app prototipi

## [0.1.0] - 2024-11-01

### İlk Commit
- Proje başlatıldı
- Temel veritabanı şeması
- ArXiv scraper prototipi

---

## Versiyon Notları

### Semantic Versioning

Format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (uyumsuz API değişiklikleri)
- **MINOR**: Yeni özellikler (geriye uyumlu)
- **PATCH**: Bug fix (geriye uyumlu)

### Kategoriler

- **Eklenen**: Yeni özellikler
- **Değiştirilen**: Mevcut özelliklerde değişiklikler
- **Kullanımdan Kaldırılan**: Yakında kaldırılacak özellikler
- **Kaldırılan**: Kaldırılan özellikler
- **Düzeltilen**: Bug fix'ler
- **Güvenlik**: Güvenlik yamalar
