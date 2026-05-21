# TrackIN — Real-Time Courier Tracking System
**Kelompok 8 | Mata Kuliah Basis Data (SBD) | Wide-Column Store — Apache Cassandra**

TrackIN adalah aplikasi pemantauan kurir logistik secara real-time yang terinspirasi dari arsitektur Gojek real-time driver location tracking. Sistem ini menggunakan **FastAPI** di backend, **Apache Cassandra (DataStax Astra DB)** sebagai database penyimpanan data berkabel time-series berkapasitas tinggi, **Python Script** untuk simulator GPS kurir, dan **HTML + Leaflet.js** di frontend untuk dashboard peta interaktif.

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

## Deklarasi Penggunaan AI (Academic Integrity)
Kami menyatakan bahwa dalam pengerjaan backend FastAPI dan GPS Simulator ini, kami berkonsultasi dengan asisten AI **Antigravity** untuk:
* Patch kecocokan Python 3.12+ (`pyasyncore`) untuk driver Cassandra.
* Script auto-downloader Secure Connect Bundle zip dari Astra DB DevOps API.
* Helper fungsi konversi string ID ke UUID secara deterministik menggunakan `uuid.uuid5`.
* Penanganan encoding terminal Windows (ASCII print statements) pada simulator GPS.

Kami telah memverifikasi seluruh fungsionalitas kode ini secara manual dan memastikan kelancaran aplikasinya pada demo lokal.
