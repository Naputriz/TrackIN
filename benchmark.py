import sys, os, time, random, sqlite3
import psycopg2
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

JUMLAH_DATA = 500
COURIER_IDS = ["KR-001", "KR-002", "KR-003", "KR-004", "KR-005"]
STATUSES = ["DELIVERING", "IDLE", "DONE"]

def generate_data():
    return {
        "courier_id": random.choice(COURIER_IDS),
        "latitude": round(random.uniform(-6.370, -6.355), 6),
        "longitude": round(random.uniform(106.820, 106.835), 6),
        "speed_kmh": round(random.uniform(10.0, 50.0), 1),
        "status": random.choice(STATUSES),
        "recorded_at": datetime.now(timezone.utc),
    }

# postgre
def test_postgres():
    conn = psycopg2.connect(host="localhost", port=5432,
                            dbname="postgres", user="postgres", password="password")
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS courier_locations")
    cur.execute("""CREATE TABLE courier_locations (
        courier_id TEXT, recorded_at TEXT,
        latitude REAL, longitude REAL,
        speed_kmh REAL, status TEXT)""")
    conn.commit()

    rows = [generate_data() for _ in range(JUMLAH_DATA)]

    start = time.perf_counter()
    cur.executemany("INSERT INTO courier_locations VALUES (%s,%s,%s,%s,%s,%s)",
        [(r["courier_id"], r["recorded_at"].isoformat(),
          r["latitude"], r["longitude"], r["speed_kmh"], r["status"]) for r in rows])
    conn.commit()
    elapsed = time.perf_counter() - start

    cur.close()
    conn.close()
    return elapsed

# cassandra
def test_cassandra():
    from cassandra.cluster import Cluster
    from cassandra.concurrent import execute_concurrent_with_args

    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect()

    session.execute("CREATE KEYSPACE IF NOT EXISTS benchmark_ks WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}")
    session.set_keyspace('benchmark_ks')
    session.execute("""CREATE TABLE IF NOT EXISTS courier_locations (
        courier_id text, recorded_at timestamp,
        latitude double, longitude double,
        speed_kmh double, status text,
        PRIMARY KEY (courier_id, recorded_at))""")

    prepared = session.prepare("""
        INSERT INTO courier_locations
        (courier_id, recorded_at, latitude, longitude, speed_kmh, status)
        VALUES (?, ?, ?, ?, ?, ?)""")

    rows = [generate_data() for _ in range(JUMLAH_DATA)]
    params = [(r["courier_id"], r["recorded_at"], r["latitude"],
               r["longitude"], r["speed_kmh"], r["status"]) for r in rows]

    start = time.perf_counter()
    execute_concurrent_with_args(session, prepared, params, concurrency=500)
    elapsed = time.perf_counter() - start

    cluster.shutdown()
    return elapsed

print("=" * 52)
print("  TrackIN - Eksperimen: NoSQL vs SQL")
print("  Apache Cassandra vs PostgreSQL")
print("=" * 52)

print(f"\n[1/2] Menguji PostgreSQL ({JUMLAH_DATA} insert)...")
waktu_postgres = test_postgres()
print(f"      Selesai: {waktu_postgres:.2f} detik ({int(JUMLAH_DATA/waktu_postgres)} insert/detik)")

print(f"\n[2/2] Menguji Cassandra ({JUMLAH_DATA} insert)...")
waktu_cassandra = test_cassandra()
print(f"      Selesai: {waktu_cassandra:.2f} detik ({int(JUMLAH_DATA/waktu_cassandra)} insert/detik)")

print("\n" + "=" * 52)
print("  HASIL PERBANDINGAN")
print("=" * 52)
print(f"  PostgreSQL : {waktu_postgres:.2f} detik")
print(f"  Cassandra  : {waktu_cassandra:.2f} detik")
print("=" * 52)

if waktu_postgres < waktu_cassandra:
    print("  PostgreSQL lebih cepat untuk data lokal skala kecil.")
    print("  Cassandra unggul di skala besar & distributed system.")
else:
    print("  Cassandra lebih cepat!")
print("=" * 52)