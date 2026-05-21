import time
import requests
import random

# API URL untuk mengirim lokasi kurir ke backend FastAPI kita
API_URL = "http://localhost:8000/couriers/location"

# --- DEFINISI RUTE SIMULASI (Universitas Indonesia, Depok) ---
# Kita membuat rute pergerakan nyata di sekitar kampus UI Depok agar demo terlihat keren dan realistis.

# Rute 1: Dari Stasiun UI -> Fasilkom -> Rektorat UI (Untuk Kurir Andi)
ROUTE_ANDI = [
    (-6.3606, 106.8315), (-6.3615, 106.8300), (-6.3625, 106.8285),
    (-6.3635, 106.8275), (-6.3642, 106.8268), (-6.3630, 106.8255),
    (-6.3618, 106.8248), (-6.3600, 106.8252)
]

# Rute 2: Dari Kukusan Teknik (Kutek) -> FT -> FEB -> Vokasi (Untuk Kurir Sari)
ROUTE_SARI = [
    (-6.3688, 106.8228), (-6.3675, 106.8232), (-6.3658, 106.8240),
    (-6.3645, 106.8250), (-6.3630, 106.8258), (-6.3615, 106.8268),
    (-6.3600, 106.8278), (-6.3590, 106.8288)
]

# Rute 3: Dari Pondok Cina (Pocin) -> FIK -> FMIPA -> Fasilkom (Untuk Kurir Budi)
ROUTE_BUDI = [
    (-6.3642, 106.8322), (-6.3630, 106.8310), (-6.3618, 106.8298),
    (-6.3605, 106.8285), (-6.3590, 106.8272), (-6.3580, 106.8260),
    (-6.3570, 106.8255), (-6.3582, 106.8248)
]

# Rute 4: Dari Asrama UI -> Balairung -> FIB -> FH (Untuk Kurir Rina)
ROUTE_RINA = [
    (-6.3540, 106.8290), (-6.3560, 106.8280), (-6.3580, 106.8272),
    (-6.3600, 106.8265), (-6.3615, 106.8275), (-6.3625, 106.8290),
    (-6.3640, 106.8305), (-6.3655, 106.8310)
]

# Rute 5: Sekitar Danau Kenanga -> Masjid UI -> Perpustakaan Pusat (Untuk Kurir Deni)
ROUTE_DENI = [
    (-6.3620, 106.8280), (-6.3625, 106.8270), (-6.3630, 106.8260),
    (-6.3635, 106.8255), (-6.3642, 106.8262), (-6.3648, 106.8272),
    (-6.3640, 106.8282), (-6.3630, 106.8290)
]

COURIERS = [
    {"id": "KR-001", "name": "Andi Wijaya",  "route": ROUTE_ANDI, "status": "DELIVERING"},
    {"id": "KR-002", "name": "Sari Dewi",    "route": ROUTE_SARI, "status": "DELIVERING"},
    {"id": "KR-003", "name": "Budi Santoso", "route": ROUTE_BUDI, "status": "DELIVERING"},
    {"id": "KR-004", "name": "Rina Kusuma",  "route": ROUTE_RINA, "status": "DELIVERING"},
    {"id": "KR-005", "name": "Deni Pratama", "route": ROUTE_DENI, "status": "DELIVERING"},
]

def simulate_gps():
    print("==================================================")
    print("      TrackIN - Real-Time GPS Courier Simulator     ")
    print("      (Mengirim koordinat UI Depok ke FastAPI DB)   ")
    print("==================================================")
    print(f"Target API Backend: {API_URL}")
    print("Menekan CTRL+C untuk menghentikan simulasi.\n")

    step = 0
    num_points = len(ROUTE_ANDI) # Semua rute didefinisikan dengan panjang 8 titik

    while True:
        # Menghitung index pergerakan saat ini (melingkar/looping rutenya)
        current_index = step % num_points
        
        print(f"\n[Step {step + 1}] Mengirimkan posisi kurir...")
        
        for courier in COURIERS:
            lat, lon = courier["route"][current_index]
            
            # Berikan sedikit noise acak kecil (micro-variation) 
            # agar visual marker kurir terlihat lebih natural dan dinamis di peta
            lat += random.uniform(-0.00005, 0.00005)
            lon += random.uniform(-0.00005, 0.00005)
            
            # Tentukan status pengiriman secara acak untuk demo variasi warna badge
            status = "DELIVERING"
            if current_index == 0:
                status = "IDLE"
            elif current_index == num_points - 1:
                status = "DONE"

            # Payload JSON sesuai dengan validasi skema Pydantic di Backend
            payload = {
                "courier_id": courier["id"],
                "latitude": lat,
                "longitude": lon,
                "speed_kmh": round(random.uniform(15.0, 45.0), 1),
                "status": status
            }

            try:
                # Kirim request POST ke backend FastAPI
                response = requests.post(API_URL, json=payload, timeout=5)
                if response.status_code == 200:
                    print(f"  [+] [GPS Kirim] {courier['name']} ({courier['id']}) -> ({lat:.5f}, {lon:.5f}) | Speed: {payload['speed_kmh']} km/h | Status: {status}")
                else:
                    print(f"  [-] [Gagal] {courier['name']} -> HTTP Status: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"  [!] [Koneksi Error] Gagal menghubungi backend untuk {courier['name']}: {e}")

        # Tunggu 5 detik sebelum mengirim update posisi berikutnya (meniru Gojek nyata!)
        step += 1
        time.sleep(5)

if __name__ == "__main__":
    try:
        simulate_gps()
    except KeyboardInterrupt:
        print("\n[!] Simulasi GPS dihentikan. Terima kasih!")
