# 🌐 Türk Devletleri Teşkilatı (TDT) & Azerbaycan Medya Takip ve Yapay Zeka Analiz Portalı

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![LLM AI](https://img.shields.io/badge/AI-Qwen--397B-FF6F00?style=for-the-badge&logo=openai&logoColor=white)](https://llmstat.iletisim.gov.tr/)
[![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**Türkiye ve Bölgesel Medyayı 7/24 Canlı Tarayan, Yapay Zeka ile Otomatik Sınıflandıran ve Diplomatik Özetler Üreten Kurumsal Medya Takip Sistemi**

[Özellikler](#-temel-özellikler) • [Mimari](#-sistem-mimarisi) • [Kurulum](#-kurulum-ve-başlatma) • [Ekran Görüntüleri](#-kullanıcı-arayüzü) • [Katkıda Bulunma](#-katkıda-bulunma)

</div>

---

## 📖 Genel Bakış

**TDT & Azerbaycan Medya Takip Portalı**, Türk Devletleri Teşkilatı (TDT) coğrafyası ve Azerbaycan Cumhuriyeti odaklı stratejik gelişmeleri; ulusal haber ajansları, basılı/dijital gazeteler ve arama motorları üzerinden **kesintisiz 7/24** izlemek üzere geliştirilmiş yapay zeka destekli bir istihbarat ve analiz platformudur.

Sistem, yüzlerce kaynaktan saniyeler içinde binlerce haberi çekerek **2 Kademeli Hibrit Filtreleme (Regex + LLM)** ve **Jaccard Benzerlik Algoritması** ile mükerrer içerikleri eler, diplomatik bağlamı tespit eder ve stratejik panellere servis eder.

---

## 🌟 Temel Özellikler

### 1. 📡 Geniş Kapsamlı Çoklu Kaynak Taraması (20+ Kaynak & SerpApi)
* **Resmi / Ana Akım Medya:** Anadolu Ajansı (AA), TRT Haber, İhlas Haber Ajansı (İHA), DHA, NTV, Habertürk, Milliyet, Hürriyet
* **İktidar / Muhafazakar Medya:** A Haber, Yeni Şafak, Sabah, Türkiye Gazetesi, Yeni Akit
* **Muhalif / Bağımsız Medya:** Sözcü, Cumhuriyet, Halk TV, T24, BirGün
* **Finans & Sektörel Medya:** Bloomberg HT, Defensehere (Savunma Sanayii), Bölgesel & Sınır Ajansları
* **Google News & SerpApi Katmanı:** Derinlemesine arama motoru yedeklemesi ile hiçbir kritik gelişme gözden kaçmaz.

### 2. ⚡ Akıllı Tekilleştirme (Fuzzy Deduplication)
* **Jaccard Similarity (Token-Overlap):** Başlık ve haber metinleri üzerinde anlamsal kelime matrisi oluşturularak aynı haberi farklı başlıklarla geçen kaynaklar tespit edilir ve mükerrer haber kirliliği %100 önlenir.

### 3. 🎯 5 Stratejik Odak Kategorisi
Haberler otomatik olarak analiz edilir ve ilgili stratejik panellere yönlendirilir:
1. **🇦🇿 Ermenistan Hattı & Barış Süreci:** Zengezur koridoru, sınır komisyonları, Karabağ, Hankendi, Şuşa ve Paşinyan temasları.
2. **🤝 Diplomasi, İkili İlişkiler & Siyaset:** Türkiye-Azerbaycan üst düzey görüşmeleri, Aliyev-Erdoğan temasları, Dışişleri ve Büyükelçilik çalışmaları.
3. **🌐 Türk Devletleri Teşkilatı (TDT):** Orta Koridor, Kazakistan, Özbekistan, Kırgızistan, Türkmenistan, KKTC ve Hazar bölgesi projeleri.
4. **⚡ Enerji, SOCAR & Ekonomi:** SOCAR, TANAP/TAP, Şahdeniz, doğalgaz-petrol koridorları ve ticaret hacmi.
5. **🛡️ Güvenlik, Savunma Sanayii & Askeri İşbirlikleri:** Ortak tatbikatlar, ordu modernizasyonu, sınır güvenliği ve İHA/SİHA işbirlikleri.

### 4. 🤖 Yapay Zeka Destekli 2 Cümlelik Diplomatik Özetleme
* **Qwen-397B LLM Motoru:** Ham haber metinleri taranarak diplomatik, sade ve net 2 cümlelik yönetici özeti çıkarılır.
* **Paralel İşleme:** Asenkron `ThreadPoolExecutor` mimarisiyle saniyeler içinde onlarca haber özetlenir.

### 5. ⚠️ Çapraz Karşılaştırma ve Tutarsızlık Tespiti (Cross-Comparison)
* Farklı medya gruplarının (Resmi, İktidar, Muhalif) aynı olaya ilişkin verdiği çelişkili rakamlar, iddialar ve söylemler yapay zeka tarafından algılanarak uyarı rozetleriyle işaretlenir.

### 6. 🌐 Çift Dilli Kurumsal Arayüz (TR / AZ)
* Tek tıkla Türkiye Türkçesi ve Azerbaycan Türkçesi (Ana Dil) arasında kusursuz geçiş.

---

## 🏗️ Sistem Mimarisi

```
├── adapters/                  # Bağımsız Medya Scraper & RSS Adaptörleri
│   ├── base_adapter.py        # Temel HTTP/RSS motoru, metin ve tarih ayrıştırıcı
│   ├── serpapi_adapter.py     # Google News derin tarama entegrasyonu
│   ├── aa_adapter.py          # Anadolu Ajansı Adaptörü
│   ├── trt_adapter.py         # TRT Haber Adaptörü
│   ├── iha_adapter.py         # İHA Adaptörü
│   ├── sozcu_adapter.py       # Sözcü Adaptörü
│   ├── yenisafak_adapter.py   # Yeni Şafak Adaptörü
│   ├── bloomberght_adapter.py # Finans & Enerji Adaptörü
│   ├── defensehere_adapter.py # Savunma Sanayii Adaptörü
│   └── runner.py              # Eşzamanlı (Multithreaded) Adaptör Yöneticisi
├── classifier/                # Yapay Zeka & NLP Sınıflandırma Hattı
│   ├── stage1.py              # Stage 1: Yüksek Hızlı Regex & Anahtar Kelime Motoru
│   ├── stage2.py              # Stage 2: Qwen LLM Semantik Sınıflandırıcı & Özetleyici
│   └── cross_comparison.py    # Çapraz Medya Analizi ve Tutarsızlık Tespiti
├── db/                        # Veritabanı Katmanı
│   └── database.py            # SQLite şeması, CRUD operasyonları ve migration motoru
├── scheduler/                 # Arka Plan Görev Yöneticisi
│   └── scheduler.py           # Periyodik canlı tarama ve veri işleme hattı
├── web/                       # Web Sunucusu ve Görsel Arayüz
│   ├── app.py                 # Flask REST API ve Rota Yöneticisi
│   ├── templates/             # Jinja2 HTML Arayüz Şablonları
│   └── static/                # Modern Glassmorphic CSS & Vanilla JS
├── config.py                  # Merkezi Sistem Ayarları ve Kaynak Yapılandırması
├── run.py                     # Portal Ana Giriş Noktası
├── test_system.py             # Birim ve Entegrasyon Testleri
├── requirements.txt           # Python Bağımlılıkları
└── .env.example               # Örnek Konfigürasyon Şablonu
```

---

## 🚀 Kurulum ve Başlatma

### 1. Projeyi Klonlayın
```bash
git clone https://github.com/merenaydin23/tdt-medya-takip-portali.git
cd tdt-medya-takip-portali
```

### 2. Sanal Ortam Oluşturun ve Bağımlılıkları Yükleyin
```bash
# Sanal ortam oluşturma
python -m venv venv

# Sanal ortamı aktif etme (Windows)
venv\Scripts\activate
# (macOS/Linux için: source venv/bin/activate)

# Paketleri yükleme
pip install -r requirements.txt
```

### 3. Yapılandırma Dosyasını Hazırlayın
`.env.example` dosyasını `.env` olarak kopyalayın ve gerekli anahtarları tanımlayın:
```bash
cp .env.example .env
```

```env
# LLM / Yapay Zeka Servisi (İsteğe Bağlı / Özelleştirilebilir)
LLM_BASE_URL=https://llmstat.iletisim.gov.tr/v1
LLM_API_KEY=your_api_key_here
LLM_MODEL=qwen-397b
ENABLE_AI_SUMMARY=False
ENABLE_LLM_STAGE2=False

# SerpApi Anahtarı (Google News derin tarama için)
SERPAPI_KEY=your_serpapi_key_here

# Sunucu Ayarları
PORT=5000
HOST=127.0.0.1
DEBUG=True
```

### 4. Uygulamayı Başlatın
```bash
python run.py
```

Tarayıcınızda açın:
👉 **`http://127.0.0.1:5000`**

---

## 🧪 Testlerin Çalıştırılması

Sistem bileşenlerinin (adaptörler, veritabanı bütünlüğü, başlık temizleyiciler ve API uç noktaları) doğrulanması için dahili test paketini çalıştırabilirsiniz:

```bash
python test_system.py
```

---

## 🛡️ Güvenlik ve Gizlilik

* Hassas anahtarlar (LLM API Key, SerpApi Key) `.env` dosyasında tutulur ve `.gitignore` ile depoya gitmesi engellenir.
* Veritabanı yerel SQLite (`db/media_monitor.db`) dosyasında çalışır, dışarıya yetkisiz veri aktarımı yapılmaz.

---

## 📄 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakabilirsiniz.
