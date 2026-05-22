# TrackIN — Real-Time Courier Tracking System
**Kelompok 8 | Mata Kuliah Basis Data (SBD) | Wide-Column Store — Apache Cassandra**

TrackIN adalah aplikasi pemantauan kurir logistik secara real-time yang terinspirasi dari arsitektur Gojek real-time driver location tracking. Sistem ini menggunakan **FastAPI** di backend, **Apache Cassandra (DataStax Astra DB)** sebagai database penyimpanan data berkabel time-series berkapasitas tinggi, **Python Script** untuk simulator GPS kurir, dan **HTML + Leaflet.js** di frontend untuk dashboard peta interaktif.

## Tech Stack
- **Backend**: FastAPI (Python), Uvicorn
- **Database**: Apache Cassandra (DataStax Astra DB)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla), Leaflet.js
- **Simulator**: Python Script (GPS Simulation)

## Arsitektur Sistem
Sistem ini menggunakan arsitektur client-server dengan aliran data utama sebagai berikut:

| Komponen | Teknologi | Fungsi |
|-----------|------------------|---------------------------------|
| Database | Apache Cassandra | Simpan data lokasi real-time |
| Backend | FastAPI (Python) | menerima dan memproses request, lalu menyimpannya ke **Apache Cassandra (Astra DB)**. |
| Frontend | Leaflet.js | Mengambil data dari Backend secara real-time maupun riwayat historis untuk divisualisasikan pada peta interaktif. |
| Simulasi | Python Script | mensimulasikan pergerakan kurir dan mengirimkan data lokasi secara berkala ke Backend melalui REST API. |

## Diagram Arsitektur Sistem
<img width="2469" height="899" alt="trackin-system" src="https://github.com/user-attachments/assets/5316be35-c2c2-4bed-8454-547d4947fb34" />


## Struktur Folder
```text
TrackIN/
├── backend/
│   ├── config.py           # Konfigurasi kredensial dan environment (Astra DB)
│   ├── database.py         # Inisialisasi koneksi database Cassandra
│   ├── main.py             # Entry point backend dan routing API FastAPI
│   └── requirements.txt    # Daftar pusta/referensi Python backend
├── frontend/
│   ├── config.js           # Konfigurasi hostname/URL endpoint API
│   ├── history.html        # UI Dashboard riwayat perjalanan kurir
│   ├── index.html          # UI Dashboard utama live tracking (Leaflet.js)
│   └── mock-server.js      # Mock server untuk testing/offline mode
├── simulator.py            # Script generator data lokasi kurir real-time GPS
└── README.md               # Dokumentasi aplikasi
```

## Cara Menjalankan Aplikasi

Pastikan Anda memiliki Python 3.10+ terinstal di sistem operasi Anda (Windows/macOS/Linux).

### Langkah 1: Jalankan Backend FastAPI
1. Masuk ke folder backend:
   ```bash
   cd backend
   ```
2. Instal semua dependensi Python:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan server FastAPI menggunakan Uvicorn:
   ```bash
   python -m uvicorn main:app --reload
   ```
   * *Catatan Wow Factor*: Backend kami secara otomatis akan terhubung dengan **Astra DB** kelompok 8, mendownload Secure Connect Bundle `.zip` secara programmatik, dan mem-patch modul driver agar kompatibel secara 100% dengan Python 3.12+ (menggunakan `pyasyncore`).
   * API Anda sekarang aktif pada: `http://localhost:8000`
   * Anda bisa mengakses dokumentasi interaktif Swagger API di: `http://localhost:8000/docs`

### Langkah 2: Jalankan GPS Simulator Kurir
1. Buka terminal baru dan pastikan berada di folder utama `TrackIN`.
2. Jalankan script simulator:
   ```bash
   python simulator.py
   ```
   Simulator akan otomatis mensimulasikan pergerakan 5 kurir aktif di peta UI Depok dan mengirimkan request POST koordinat ke backend setiap 5 detik.

### Langkah 3: Jalankan Frontend Dashboard
1. Pastikan isi file `frontend/config.js` sudah diset ke API lokal (`API_BASE: "http://localhost:8000"`).
2. Cukup buka file `frontend/index.html` langsung di browser Anda (atau klik kanan -> *Open with Live Server* jika menggunakan VS Code).
3. Anda akan melihat peta interaktif Leaflet.js dengan marker 5 kurir aktif yang bergerak secara real-time!
4. Masuk ke halaman **Riwayat Rute** (`frontend/history.html`) untuk melihat jalur riwayat perjalanan kurir berdasarkan filter waktu tertentu.

---

## Eksperimen: NoSQL vs SQL (Benchmark Insert)

Sebagai bagian dari eksplorasi teknologi, kami melakukan benchmark perbandingan performa insert antara **Apache Cassandra** dan **PostgreSQL** menggunakan data simulasi lokasi kurir.

Pengujian dilakukan dengan menginsert data lokasi kurir secara massal menggunakan concurrent writes pada Cassandra dan `executemany` pada PostgreSQL. Hasil eksperimen menunjukkan bahwa **Cassandra unggul dalam throughput insert** dibandingkan PostgreSQL:

| Database | Waktu | Throughput |
|---|---|---|
| PostgreSQL | 0.09 detik | 5.779 insert/detik |
| Cassandra | 0.06 detik | 8.101 insert/detik |

Cassandra mampu mengungguli PostgreSQL berkat arsitektur **distributed writes** dan **concurrent execution**-nya yang dirancang khusus untuk menangani data time-series bervolume tinggi. Hal ini memperkuat keputusan kami memilih Apache Cassandra sebagai database utama TrackIN untuk menyimpan data lokasi kurir secara real-time.

---

## Deklarasi Penggunaan AI (Academic Integrity)
Kami menyatakan bahwa dalam pengerjaan backend FastAPI dan GPS Simulator ini, kami berkonsultasi dengan asisten AI **Antigravity** untuk:
* Patch kecocokan Python 3.12+ (`pyasyncore`) untuk driver Cassandra.
* Script auto-downloader Secure Connect Bundle zip dari Astra DB DevOps API.
* Helper fungsi konversi string ID ke UUID secara deterministik menggunakan `uuid.uuid5`.
* Penanganan encoding terminal Windows (ASCII print statements) pada simulator GPS.

Kami telah memverifikasi seluruh fungsionalitas kode ini secara manual dan memastikan kelancaran aplikasinya pada demo lokal.
