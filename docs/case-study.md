# Case Study: Gojek & Apache Cassandra

## Tentang Gojek

Gojek adalah super-app asal Indonesia yang didirikan pada 2010, kini beroperasi di lebih dari 5 negara Asia Tenggara. Dengan lebih dari **2 juta mitra driver aktif** dan puluhan layanan (GoRide, GoCar, GoFood, GoSend, dll.), Gojek memproses data dalam skala sangat besar secara real-time.

---

## Masalah yang Dihadapi

| Tantangan | Detail |
|---|---|
| Volume write ekstrem | Setiap driver mengirim data GPS setiap 4–5 detik → ratusan juta operasi tulis per jam |
| Latensi rendah | Sistem dispatch harus membaca lokasi terkini dalam **milidetik** |
| Operasional multi-region | Beroperasi di ratusan kota, data harus tersedia konsisten di banyak wilayah |
| Skalabilitas | Jumlah driver terus bertambah, database harus bisa scale-out tanpa ubah arsitektur |

---

## Mengapa Apache Cassandra?

### 1. Write Throughput Tinggi
Cassandra dirancang khusus untuk menangani operasi tulis dalam jumlah besar dengan latensi rendah — sesuatu yang tidak bisa dipenuhi oleh database relasional pada skala Gojek.

### 2. Replikasi Multi-Region
Cassandra mendukung replikasi multi-region secara built-in, sehingga data lokasi driver tetap tersedia meski diakses dari berbagai kota atau negara sekaligus.

### 3. Optimal untuk Time-Series Data
Data GPS bersifat time-series (koordinat berdasarkan waktu). Dengan model **wide-column** dan **clustering key berbasis timestamp**, query seperti *"ambil lokasi terbaru driver X"* bisa diselesaikan sangat cepat tanpa full table scan.

### 4. Tidak Ada Single Point of Failure
Arsitektur Cassandra yang terdistribusi membuat sistem tetap berjalan normal meski salah satu node bermasalah — kritis untuk platform yang tidak boleh down.

---

## Model Data di Gojek

```
TABLE driver_locations
  PRIMARY KEY: driver_id (Partition Key), timestamp DESC (Clustering Key)
  COLUMNS: latitude, longitude, speed, heading, status
```

| Komponen | Nilai | Penjelasan |
|---|---|---|
| Partition Key | `driver_id` | Menentukan di node mana data disimpan |
| Clustering Key | `timestamp DESC` | Data terurut dari terbaru ke terlama |
| Kolom | `latitude`, `longitude` | Koordinat GPS |
| Kolom | `speed`, `heading` | Kecepatan dan arah perjalanan |
| Kolom | `status` | `AVAILABLE` / `ON_TRIP` / `OFFLINE` |

**Pola query yang dioptimalkan:**
- *"Ambil 1 data lokasi terbaru dari driver X"*
- *"Ambil riwayat rute driver X dalam 30 menit terakhir"*

Keduanya sangat efisien karena data sudah terpartisi per driver dan terurut berdasarkan waktu.

---

## Relevansi dengan Proyek TrackIN

TrackIN merepresentasikan langsung masalah yang diselesaikan Gojek, dalam skala lebih kecil:

| Gojek | TrackIN |
|---|---|
| Mitra driver mengirim GPS tiap 4–5 detik | Virtual courier mengirim GPS tiap beberapa detik via simulasi script |
| Sistem dispatch membaca lokasi real-time | Dashboard Leaflet.js polling lokasi terbaru dari API |
| Skala jutaan driver | Skala simulasi untuk tujuan pembelajaran |
| Apache Cassandra sebagai penyimpanan utama | Apache Cassandra dengan skema yang terinspirasi langsung dari Gojek |

---

## Referensi

- "Inside GoJek Tech Stack And Infrastructure" — Appscrip Blog, May 2023. https://appscrip.com/blog/gojek-tech-stack-and-infrastructure/
- Apache Cassandra Official Documentation — https://cassandra.apache.org/_/index.html
