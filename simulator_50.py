import time
import requests
import random
import concurrent.futures

# API URL untuk mengirim lokasi kurir ke backend FastAPI kita
API_URL = "http://localhost:8000/couriers/location"

# Base Routes
BASE_ROUTES = [
    # Rute 1
    [(-6.3606, 106.8315), (-6.3615, 106.8300), (-6.3625, 106.8285), (-6.3635, 106.8275), (-6.3642, 106.8268), (-6.3630, 106.8255), (-6.3618, 106.8248), (-6.3600, 106.8252)],
    # Rute 2
    [(-6.3688, 106.8228), (-6.3675, 106.8232), (-6.3658, 106.8240), (-6.3645, 106.8250), (-6.3630, 106.8258), (-6.3615, 106.8268), (-6.3600, 106.8278), (-6.3590, 106.8288)],
    # Rute 3
    [(-6.3642, 106.8322), (-6.3630, 106.8310), (-6.3618, 106.8298), (-6.3605, 106.8285), (-6.3590, 106.8272), (-6.3580, 106.8260), (-6.3570, 106.8255), (-6.3582, 106.8248)],
    # Rute 4
    [(-6.3540, 106.8290), (-6.3560, 106.8280), (-6.3580, 106.8272), (-6.3600, 106.8265), (-6.3615, 106.8275), (-6.3625, 106.8290), (-6.3640, 106.8305), (-6.3655, 106.8310)],
    # Rute 5
    [(-6.3620, 106.8280), (-6.3625, 106.8270), (-6.3630, 106.8260), (-6.3635, 106.8255), (-6.3642, 106.8262), (-6.3648, 106.8272), (-6.3640, 106.8282), (-6.3630, 106.8290)]
]

# Generate 50 couriers by adding some variance to the base routes
COURIERS = []
for i in range(1, 51):
    base_route = random.choice(BASE_ROUTES)
    
    # Create slightly modified route for this specific courier
    # so they don't exactly overlap with others
    modified_route = []
    route_offset_lat = random.uniform(-0.002, 0.002)
    route_offset_lon = random.uniform(-0.002, 0.002)
    
    for lat, lon in base_route:
        modified_route.append((lat + route_offset_lat, lon + route_offset_lon))
        
    COURIERS.append({
        "id": f"KR-{i:03d}",
        "name": f"Kurir {i}",
        "route": modified_route
    })

def send_update(courier, current_index, num_points):
    lat, lon = courier["route"][current_index]
    
    # Berikan noise dinamis setiap perpindahan
    lat += random.uniform(-0.00005, 0.00005)
    lon += random.uniform(-0.00005, 0.00005)
    
    status = "DELIVERING"
    if current_index == 0:
        status = "IDLE"
    elif current_index == num_points - 1:
        status = "DONE"

    payload = {
        "courier_id": courier["id"],
        "latitude": lat,
        "longitude": lon,
        "speed_kmh": round(random.uniform(15.0, 45.0), 1),
        "status": status
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        if response.status_code == 200:
            return f"[+] {courier['id']} terkirim."
        else:
            return f"[-] Gagal {courier['id']}: HTTP {response.status_code}"
    except Exception as e:
        return f"[!] Error {courier['id']}: {e}"

def simulate_gps():
    print("==================================================")
    print("      TrackIN - 50 Drivers Load Test Simulator    ")
    print("==================================================")
    
    step = 0
    num_points = len(BASE_ROUTES[0])

    # Menggunakan ThreadPool untuk menembak API secara concurrent
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        while True:
            current_index = step % num_points
            print(f"\n[Step {step + 1}] Mengirimkan posisi 50 kurir secara bersamaan...")
            
            start_time = time.time()
            
            # Submit semua task
            futures = [executor.submit(send_update, courier, current_index, num_points) for courier in COURIERS]
            
            # Tunggu semua selesai (opsional bisa print hasilnya)
            success_count = 0
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if "[+]" in result:
                    success_count += 1
            
            duration = time.time() - start_time
            print(f"Selesai mengirim ke backend. Berhasil {success_count}/50 dalam {duration:.2f} detik.")
            
            step += 1
            time.sleep(5)

if __name__ == "__main__":
    try:
        simulate_gps()
    except KeyboardInterrupt:
        print("\n[!] Simulasi 50 driver dihentikan.")
