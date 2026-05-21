import sys
import uuid
import os

# --- Compatibility Patch untuk Python 3.12+ ---
# Driver Cassandra membutuhkan modul 'asyncore' yang sudah dihapus sejak Python 3.12.
# Kita melakukan patch dinamis menggunakan library 'pyasyncore' yang sudah di-install.
try:
    import asyncore
except ImportError:
    try:
        import pyasyncore
        sys.modules['asyncore'] = pyasyncore
        print("[*] Python 3.12+ compatibility patch applied (asyncore patched using pyasyncore).")
    except ImportError:
        print("[!] Warning: pyasyncore is not installed. Cassandra connection may fail in Python 3.12+.")

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from config import ASTRA_DB_CLIENT_ID, ASTRA_DB_CLIENT_SECRET, ASTRA_DB_KEYSPACE, download_secure_connect_bundle

# --- Static Courier Mapping ---
# Digunakan untuk memberikan nama (Name) pada kurir agar dashboard Radya bisa menampilkan nama kurir yang bersahabat
# (misal: KR-001 -> Andi Wijaya) alih-alih hanya UUID rumit.
COURIER_MAP = {
    "KR-001": {"name": "Andi Wijaya", "uuid": uuid.uuid5(uuid.NAMESPACE_DNS, "KR-001")},
    "KR-002": {"name": "Sari Dewi", "uuid": uuid.uuid5(uuid.NAMESPACE_DNS, "KR-002")},
    "KR-003": {"name": "Budi Santoso", "uuid": uuid.uuid5(uuid.NAMESPACE_DNS, "KR-003")},
    "KR-004": {"name": "Rina Kusuma", "uuid": uuid.uuid5(uuid.NAMESPACE_DNS, "KR-004")},
    "KR-005": {"name": "Deni Pratama", "uuid": uuid.uuid5(uuid.NAMESPACE_DNS, "KR-005")},
}

# Mapping sebaliknya (dari UUID ke String ID & Nama) untuk mempermudah mapping data saat query dari Cassandra
UUID_TO_COURIER = {
    v["uuid"]: {"name": v["name"], "code": k} for k, v in COURIER_MAP.items()
}

def get_courier_uuid(courier_id_str: str) -> uuid.UUID:
    """
    Mengonversi string ID kurir (misal: 'KR-001') secara deterministik menjadi UUID.
    Jika input sudah berupa UUID yang valid, langsung mengembalikannya sebagai tipe UUID.
    """
    try:
        # Cek jika input sudah berwujud UUID string yang valid
        return uuid.UUID(courier_id_str)
    except ValueError:
        # Jika bukan UUID (misal 'KR-001'), buat UUID unik deterministik
        if courier_id_str in COURIER_MAP:
            return COURIER_MAP[courier_id_str]["uuid"]
        return uuid.uuid5(uuid.NAMESPACE_DNS, courier_id_str)

def get_courier_info(courier_uuid: uuid.UUID) -> dict:
    """
    Mendapatkan info kode kurir dan nama berdasarkan objek UUID.
    """
    if courier_uuid in UUID_TO_COURIER:
        return UUID_TO_COURIER[courier_uuid]
    
    # Fallback jika UUID tidak terdaftar di mapping static kita
    short_uuid = str(courier_uuid)[:8]
    return {
        "name": f"Kurir ({short_uuid})",
        "code": str(courier_uuid)
    }

# --- Inisialisasi Koneksi Cassandra / Astra DB ---
session = None
cluster = None

def get_cassandra_session():
    """
    Membuat dan mengembalikan session koneksi ke DataStax Astra DB.
    Menggunakan Secure Connect Bundle (SCB) dan PlainTextAuthProvider.
    """
    global session, cluster
    
    # Jika session sudah aktif, langsung kembalikan
    if session is not None:
        return session

    # 1. Pastikan Secure Connect Bundle sudah didownload
    bundle_path = download_secure_connect_bundle()
    if not bundle_path:
        raise RuntimeError("[-] Tidak dapat menghubungkan ke Astra DB karena Secure Connect Bundle tidak ditemukan.")

    print("[*] Menghubungkan ke Astra DB (Apache Cassandra)...")
    try:
        # 2. Konfigurasi Cloud config dengan Secure Connect Bundle
        cloud_config = {
            'secure_connect_bundle': bundle_path
        }
        
        # 3. Konfigurasi Auth Provider menggunakan Client ID dan Secret Astra DB
        auth_provider = PlainTextAuthProvider(ASTRA_DB_CLIENT_ID, ASTRA_DB_CLIENT_SECRET)
        
        # 4. Hubungkan Cluster
        cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
        session = cluster.connect()
        
        # 5. Set Keyspace aktif
        session.set_keyspace(ASTRA_DB_KEYSPACE)
        print(f"[+] Berhasil terhubung ke keyspace Astra DB: '{ASTRA_DB_KEYSPACE}'!")
        
        return session
        
    except Exception as e:
        print(f"[-] Gagal menghubungkan ke Cassandra: {e}")
        import traceback
        traceback.print_exc()
        raise e

def shutdown_session():
    """
    Menutup koneksi database dengan rapi.
    """
    global session, cluster
    if session:
        session.shutdown()
        session = None
    if cluster:
        cluster.shutdown()
        cluster = None
    print("[*] Koneksi ke Cassandra ditutup.")
