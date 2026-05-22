import sys
import uuid
import os

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

COURIER_MAP = {
    "KR-001": {"name": "Andi Wijaya", "uuid": uuid.uuid5(uuid.NAMESPACE_DNS, "KR-001"), "code": "KR-001"},
    "KR-002": {"name": "Sari Dewi", "uuid": uuid.uuid5(uuid.NAMESPACE_DNS, "KR-002"), "code": "KR-002"},
    "KR-003": {"name": "Budi Santoso", "uuid": uuid.uuid5(uuid.NAMESPACE_DNS, "KR-003"), "code": "KR-003"},
    "KR-004": {"name": "Rina Kusuma", "uuid": uuid.uuid5(uuid.NAMESPACE_DNS, "KR-004"), "code": "KR-004"},
    "KR-005": {"name": "Deni Pratama", "uuid": uuid.uuid5(uuid.NAMESPACE_DNS, "KR-005"), "code": "KR-005"},
}

def get_courier_uuid(courier_id_str: str) -> uuid.UUID:
    """
    Mengonversi string ID kurir (misal: 'KR-001') secara deterministik menjadi UUID.
    Jika kurir belum ada di COURIER_MAP, maka akan didaftarkan secara otomatis (Dynamic Registration).
    """
    try:
        return uuid.UUID(courier_id_str)
    except ValueError:
        pass

    # registrasi Otomatis jika kurir baru pertama kali mengirim data
    if courier_id_str not in COURIER_MAP:
        new_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, courier_id_str)
        # Pisahkan angka dari string (misal KR-060) untuk memberi nama otomatis yang rapi
        name = f"Kurir {courier_id_str.replace('KR-', '')}"
        COURIER_MAP[courier_id_str] = {
            "name": name,
            "uuid": new_uuid,
            "code": courier_id_str
        }
        print(f"[*] Registered new courier dynamically: {name} ({courier_id_str})")
        
    return COURIER_MAP[courier_id_str]["uuid"]

def get_courier_info(courier_uuid: uuid.UUID) -> dict:
    """
    Mendapatkan info kode kurir dan nama berdasarkan objek UUID.
    """
    # cari di dictionary values
    for info in COURIER_MAP.values():
        if info["uuid"] == courier_uuid:
            return info
    
    # fallback jika UUID tidak terdaftar (hampir tidak mungkin karena selalu didaftarkan)
    short_uuid = str(courier_uuid)[:8]
    return {
        "name": f"Kurir ({short_uuid})",
        "code": str(courier_uuid)
    }


# Inisialisasi Koneksi Cassandra / Astra DB 
session = None
cluster = None

def get_cassandra_session():
    """
    Membuat dan mengembalikan session koneksi ke DataStax Astra DB.
    Menggunakan Secure Connect Bundle (SCB) dan PlainTextAuthProvider.
    """
    global session, cluster
    
    # jika session sudah aktif, langsung kembalikan
    if session is not None:
        return session

    bundle_path = download_secure_connect_bundle()
    if not bundle_path:
        raise RuntimeError("[-] Tidak dapat menghubungkan ke Astra DB karena Secure Connect Bundle tidak ditemukan.")

    print("[*] Menghubungkan ke Astra DB (Apache Cassandra)...")
    try:
        cloud_config = {
            'secure_connect_bundle': bundle_path
        }
        
        auth_provider = PlainTextAuthProvider(ASTRA_DB_CLIENT_ID, ASTRA_DB_CLIENT_SECRET)
        
        cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
        session = cluster.connect()
        
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
