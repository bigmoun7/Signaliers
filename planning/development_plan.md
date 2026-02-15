# Rencana Pengembangan: Signaliers (Dashboard Saham & Kripto Real-time)

## 1. Gambaran Proyek
Aplikasi dashboard web yang menghimpun data saham dan kripto secara real-time, melakukan analisis teknikal, dan menampilkan sinyal beli/tunggu berdasarkan indikator tertentu.

## 2. Tech Stack
- **Backend:** Python (FastAPI) - Performa tinggi, mendukung async.
- **Frontend:** React.js + Tailwind CSS - UI modern dan responsif.
- **Sumber Data:** 
    - Saham: Alpha Vantage / Yahoo Finance (yfinance).
    - Kripto: Binance API / CoinGecko.
- **Database/Caching:** Redis (Utama untuk caching agar tidak terkena rate limit), PostgreSQL (Opsional untuk menyimpan data historis).
- **Library Analisis:** TA-Lib atau Pandas TA.

## 3. Arsitektur & Alur Data
1. **Data Fetcher:** Tugas terjadwal (Celery atau loop async sederhana) mengambil data dari API.
2. **Caching:** Data mentah disimpan di Redis dengan waktu kadaluarsa untuk mematuhi rate limit API.
3. **Analysis Engine:** Memproses data cache untuk menghitung indikator (RSI, SMA, MACD, Bollinger Bands).
4. **Signal Generator:** Mengevaluasi indikator terhadap aturan (Golden Cross, RSI < 30, dll.) untuk menghasilkan sinyal.
5. **API Layer:** FastAPI menyajikan sinyal yang telah diproses ke frontend React.
6. **Frontend:** Menampilkan dashboard dengan tabel sinyal dan grafik.

## 4. Fitur Utama & Logika Implementasi

### A. Data Aggregation
- Mengambil data OHLCV (Open, High, Low, Close, Volume).
- Timeframe: 1h (1 jam), 4h (4 jam), 1d (1 hari).
- **Strategi Rate Limit:** 
    - Gunakan Redis untuk menyimpan timestamp pengambilan terakhir.
    - Hanya ambil data baru jika cache sudah kadaluarsa atau kosong.

### B. Technical Analysis Engine
- **Golden Cross:** 
    - Hitung SMA 50 dan SMA 200.
    - Sinyal: `SMA 50 > SMA 200` (Bullish).
- **RSI Oversold:**
    - Hitung RSI (periode 14).
    - Sinyal: `RSI < 30` (Potensi Beli).
- **MACD Divergence:**
    - Hitung garis MACD dan garis Signal.
    - Sinyal: `MACD > Signal` (Crossover Bullish).
- **Bollinger Bands:**
    - Hitung pita Atas, Tengah, Bawah.
    - Sinyal: `Harga <= Pita Bawah` DAN `Volume > Rata-rata Volume` (Potensi Pembalikan Arah).

### C. Signal Dashboard (UI)
- Kolom Tabel: Simbol, Harga, Perubahan 24j, RSI, Status MACD, Status SMA, Sinyal (BELI/TUNGGU).
- Indikator Visual (Hijau untuk Beli, Merah/Abu-abu untuk Tunggu).

## 5. Tahapan Pengembangan

### Fase 1: Setup Backend & Pengambilan Data
1. Inisialisasi struktur proyek FastAPI.
2. Setup koneksi Redis.
3. Implementasi `DataFetcher` untuk Yahoo Finance dan Binance.
4. Implementasi mekanisme Caching.

### Fase 2: Inti Analisis Teknikal
1. Install `pandas` dan `pandas_ta` / `ta-lib`.
2. Buat class `AnalysisEngine`.
3. Implementasi fungsi perhitungan indikator (RSI, SMA, MACD, BB).
4. Implementasi Logika Sinyal.

### Fase 3: Pengembangan API
1. Buat endpoint:
    - `GET /api/market/status` (Cek kesehatan sistem)
    - `GET /api/signals?type=stock`
    - `GET /api/signals?type=crypto`
2. Hubungkan API ke Analysis Engine.

### Fase 4: Pengembangan Frontend
1. Inisialisasi proyek React dengan Vite.
2. Install Tailwind CSS.
3. Buat komponen `Dashboard`.
4. Ambil data dari API backend dan tampilkan dalam tabel.

### Fase 5: Pengujian & Optimasi
1. Logika Backtesting (jalankan algoritma pada data historis).
2. Optimasi panggilan API dan caching.
3. Tambahkan placeholder "Sentimen Berita" (fitur masa depan).

## 6. Struktur Folder
```
signaliers/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # Titik masuk FastAPI
│   │   ├── api/               # Rute API
│   │   ├── core/              # Konfigurasi, Database
│   │   ├── services/          # Logika Bisnis
│   │   │   ├── fetcher.py     # Pengambilan Data
│   │   │   ├── analysis.py    # Logika Analisis Teknikal
│   │   │   └── signals.py     # Pembuatan Sinyal
│   │   └── models/            # Model Pydantic
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── services/
│   ├── package.json
│   └── tailwind.config.js
└── planning/
    └── development_plan.md
```
