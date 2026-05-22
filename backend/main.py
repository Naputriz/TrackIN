from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from database import get_cassandra_session, get_courier_uuid, get_courier_info, COURIER_MAP

# Inisialisasi Aplikasi FastAPI
app = FastAPI(
    title="TrackIN - Real-Time Courier Tracking API",
    description="REST API backend untuk sistem pelacakan kurir real-time menggunakan FastAPI dan Apache Cassandra (Astra DB).",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LocationPostRequest(BaseModel):
    courier_id: str = Field(..., description="ID Kurir, bisa berbentuk string (misal: 'KR-001') atau UUID valid.")
    latitude: float = Field(..., description="Koordinat Lintang GPS.")
    longitude: float = Field(..., description="Koordinat Bujur GPS.")
    speed_kmh: Optional[float] = Field(0.0, description="Kecepatan kurir dalam km/jam.")
    status: str = Field(..., description="Status kurir: 'IDLE', 'DELIVERING', atau 'DONE'.")

class LocationResponse(BaseModel):
    courier_id: str
    name: str
    latitude: float
    longitude: float
    status: str

class HistoryResponse(BaseModel):
    courier_id: str
    latitude: float
    longitude: float
    timestamp: str  # Digunakan oleh frontend Radya
    recorded_at: str  # Fallback standard ISO format
    status: str

MOCK_COURIERS = [
    { "courier_id": "KR-001", "name": "Andi Wijaya",  "latitude": -6.2000, "longitude": 106.8167, "status": "DELIVERING" },
    { "courier_id": "KR-002", "name": "Sari Dewi",    "latitude": -6.2150, "longitude": 106.8300, "status": "IDLE" },
    { "courier_id": "KR-003", "name": "Budi Santoso", "latitude": -6.1900, "longitude": 106.8000, "status": "DELIVERING" },
    { "courier_id": "KR-004", "name": "Rina Kusuma",  "latitude": -6.2250, "longitude": 106.7900, "status": "DONE" },
    { "courier_id": "KR-005", "name": "Deni Pratama", "latitude": -6.2080, "longitude": 106.8450, "status": "IDLE" },
]


@app.get("/")
def read_root():
    """
    Endpoint index untuk memeriksa apakah status server FastAPI sedang online dan sehat.
    """
    return {
        "status": "online",
        "message": "Welcome to TrackIN Real-Time Courier Tracking API!",
        "database": "Connected to DataStax Astra DB"
    }

@app.post("/couriers/location", summary="Kirim Data GPS Kurir")
def update_location(payload: LocationPostRequest):
    """
    Menerima data koordinat GPS terbaru dari script simulator kurir,
    mengonversi ID kurir ke UUID, lalu menyimpannya ke tabel `courier_locations` di Cassandra.
    """
    try:
        session = get_cassandra_session()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database offline: {str(e)}")

    courier_uuid = get_courier_uuid(payload.courier_id)
    recorded_at = datetime.utcnow()

    query = """
        INSERT INTO courier_locations (courier_id, recorded_at, latitude, longitude, speed_kmh, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    try:
        # Eksekusi Query
        session.execute(
            query, 
            (courier_uuid, recorded_at, payload.latitude, payload.longitude, payload.speed_kmh, payload.status)
        )
        print(f"[+] [GPS Received] {payload.courier_id} ({payload.latitude}, {payload.longitude}) | Status: {payload.status}")
        return {"status": "success", "message": "Location saved to Cassandra successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to insert into Cassandra: {str(e)}")

@app.get("/couriers/locations", response_model=List[LocationResponse], summary="Ambil Lokasi Terbaru Semua Kurir")
def get_latest_locations():
    """
    Mengambil data lokasi paling terbaru untuk semua kurir terdaftar di Cassandra
    menggunakan query efisien bertarget partisi: `SELECT * FROM courier_locations WHERE courier_id = ? LIMIT 1`.
    Jika database kosong, mengembalikan data dummy (mock) sebagai fallback.
    """
    try:
        session = get_cassandra_session()
    except Exception:
        # Jika database offline, gunakan mock data agar demo dashboard tidak blank/crash
        print("[!] Database connection failed. Serving mock data instead...")
        return MOCK_COURIERS

    latest_locations = []
    
    for courier_code, info in COURIER_MAP.items():
        courier_uuid = info["uuid"]
        
        query = "SELECT * FROM courier_locations WHERE courier_id = %s LIMIT 1"
        try:
            row = session.execute(query, (courier_uuid,)).one()
            
            if row:
                latest_locations.append({
                    "courier_id": courier_code,  # Kembalikan string ID (misal: 'KR-001') ke frontend
                    "name": info["name"],
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "status": row.status
                })
        except Exception as e:
            print(f"[!] Error fetching latest location for {courier_code}: {e}")

    if not latest_locations:
        print("[*] No data in database yet. Serving mock data...")
        return MOCK_COURIERS

    return latest_locations

@app.get("/couriers/{courier_id}/history", response_model=List[HistoryResponse], summary="Ambil Riwayat Rute Kurir")
def get_courier_history(
    courier_id: str, 
    start: Optional[str] = Query(None, description="Format ISO Waktu Mulai (misal: 2026-05-21T08:00)"), 
    end: Optional[str] = Query(None, description="Format ISO Waktu Selesai (misal: 2026-05-21T09:00)")
):
    """
    Mengambil daftar koordinat historis perjalanan kurir tertentu dalam rentang waktu terfilter.
    Query memanfaatkan properti Clustering Key pada 'recorded_at' untuk melakukan filter perbandingan (>= dan <=).
    """
    try:
        session = get_cassandra_session()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database offline: {str(e)}")

    courier_uuid = get_courier_uuid(courier_id)
    info = get_courier_info(courier_uuid)
    
    try:
        if start:
            # parsing start datetime
            start_dt = datetime.fromisoformat(start.replace("Z", ""))
        else:
            # Default start: 24 jam yang lalu
            start_dt = datetime.utcnow() - timedelta(hours=24)
            
        if end:
            # parsing end datetime
            end_dt = datetime.fromisoformat(end.replace("Z", ""))
        else:
            # Default end: saat ini
            end_dt = datetime.utcnow()
    except ValueError:
        raise HTTPException(status_code=400, detail="Format datetime start atau end tidak valid. Gunakan format ISO (YYYY-MM-DDTHH:MM)")

    query = """
        SELECT * FROM courier_locations 
        WHERE courier_id = %s AND recorded_at >= %s AND recorded_at <= %s
    """
    
    try:
        rows = session.execute(query, (courier_uuid, start_dt, end_dt))
        history_list = []
        for row in rows:
            iso_time = row.recorded_at.isoformat()
            history_list.append({
                "courier_id": info["code"],
                "latitude": row.latitude,
                "longitude": row.longitude,
                "timestamp": iso_time,  # Dipakai oleh history.html
                "recorded_at": iso_time,
                "status": row.status
            })
        
        history_list.reverse()
        
        return history_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query database: {str(e)}")
