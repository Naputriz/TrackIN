# Data Model — TrackIN (Apache Cassandra)

## Paradigma: Wide-Column Store

TrackIN menggunakan Apache Cassandra sebagai database utama. Desain skema mengikuti prinsip **query-first design** — struktur tabel dibentuk berdasarkan pola query yang dibutuhkan, bukan relasi antar entitas.

---

## Tabel 1: `courier_locations`

> Menyimpan riwayat lokasi GPS setiap kurir secara real-time.

```
courier_locations
├── courier_id      UUID        [PARTITION KEY]
├── recorded_at     TIMESTAMP   [CLUSTERING KEY, DESC]
├── latitude        DOUBLE
├── longitude       DOUBLE
├── speed_kmh       FLOAT
└── status          TEXT        (IDLE / DELIVERING / DONE)
```

### Diagram Partisi

```
Partition: courier_id = "uuid-kurir-A"
┌─────────────────────────────────────────────────────────┐
│  recorded_at (DESC)  │ latitude  │ longitude │ status    │
├──────────────────────┼───────────┼───────────┼───────────┤
│  2024-06-01 12:05:00 │ -6.2088   │ 106.8456  │ DELIVERING│
│  2024-06-01 12:04:55 │ -6.2085   │ 106.8450  │ DELIVERING│
│  2024-06-01 12:04:50 │ -6.2080   │ 106.8445  │ IDLE      │
└─────────────────────────────────────────────────────────┘

Partition: courier_id = "uuid-kurir-B"
┌─────────────────────────────────────────────────────────┐
│  recorded_at (DESC)  │ latitude  │ longitude │ status    │
├──────────────────────┼───────────┼───────────┼───────────┤
│  2024-06-01 12:05:02 │ -6.1751   │ 106.8272  │ DELIVERING│
│  ...                 │ ...       │ ...       │ ...       │
└─────────────────────────────────────────────────────────┘
```

### Query yang Dioptimalkan

```cql
-- Ambil lokasi terbaru kurir X
SELECT * FROM courier_locations
WHERE courier_id = ?
LIMIT 1;

-- Ambil riwayat rute kurir X dalam 30 menit terakhir
SELECT * FROM courier_locations
WHERE courier_id = ?
  AND recorded_at >= ? AND recorded_at <= ?;
```

> Kedua query hanya menyentuh **satu partisi** → sangat cepat, tidak ada full table scan.

---

## Tabel 2: `deliveries`

> Menyimpan data pengiriman yang ditangani setiap kurir.

```
deliveries
├── delivery_id     UUID        [PARTITION KEY]
├── courier_id      UUID
├── customer_name   TEXT
├── destination     TEXT
├── created_at      TIMESTAMP
└── status          TEXT        (PENDING / IN_TRANSIT / DELIVERED)
```

### Diagram Partisi

```
Partition: delivery_id = "uuid-delivery-001"
┌──────────────┬───────────────┬──────────────────────┬──────────────┐
│ courier_id   │ customer_name │ destination          │ status       │
├──────────────┼───────────────┼──────────────────────┼──────────────┤
│ uuid-kurir-A │ Budi Santoso  │ Jl. Sudirman No. 5   │ IN_TRANSIT   │
└──────────────┴───────────────┴──────────────────────┴──────────────┘
```

### Query yang Dioptimalkan

```cql
-- Ambil detail pengiriman berdasarkan ID
SELECT * FROM deliveries
WHERE delivery_id = ?;
```

---

## Alur Data Sistem

```
[Simulasi GPS Script]
        │
        │  POST /location  (setiap ~3 detik)
        ▼
[FastAPI Backend]
        │
        │  INSERT INTO courier_locations
        ▼
[Apache Cassandra]
        │
        │  SELECT (polling tiap beberapa detik)
        ▼
[Dashboard Leaflet.js]
   (peta real-time)
```

---

## Mengapa Skema Ini Efisien?

| Prinsip | Implementasi di TrackIN |
|---|---|
| **Query-first design** | Tabel dirancang sesuai pola query, bukan relasi |
| **Partition per kurir** | Semua lokasi 1 kurir dalam 1 partisi -> query cepat |
| **Clustering key DESC** | Data terbaru selalu di posisi pertama -> `LIMIT 1` sangat efisien |
| **Tanpa JOIN** | Semua query diselesaikan dari 1 partisi, tanpa relasi antar tabel |
| **Horizontal scalability** | Tambah node Cassandra = tambah kapasitas, tanpa ubah skema |

---

## Perbandingan: SQL vs Cassandra untuk Use Case Ini

| Aspek | SQL (PostgreSQL, dll.) | Apache Cassandra |
|---|---|---|
| Write throughput | Terbatas, mudah bottleneck | Sangat tinggi, dirancang untuk ini |
| Query lokasi terbaru | Perlu `ORDER BY` + index | Otomatis dari clustering key DESC |
| Replikasi multi-region | Kompleks, butuh setup tambahan | Built-in |
| Skalabilitas | Vertical (upgrade server) | Horizontal (tambah node) |
| JOIN antar tabel | Didukung penuh | Tidak ada — desain skema menggantikannya |
