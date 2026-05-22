const http = require("http");
const url  = require("url");

const PORT = 8787;

// data kurir (disimpan di memori, bergerak tiap request)
const couriers = [
  { courier_id: "KR-001", name: "Andi Wijaya",  latitude: -6.2000, longitude: 106.8167, status: "DELIVERING" },
  { courier_id: "KR-002", name: "Sari Dewi",    latitude: -6.2150, longitude: 106.8300, status: "IDLE" },
  { courier_id: "KR-003", name: "Budi Santoso", latitude: -6.1900, longitude: 106.8000, status: "DELIVERING" },
  { courier_id: "KR-004", name: "Rina Kusuma",  latitude: -6.2250, longitude: 106.7900, status: "DONE" },
  { courier_id: "KR-005", name: "Deni Pratama", latitude: -6.2080, longitude: 106.8450, status: "IDLE" },
];

// simulasi pergerakan kurir tiap kali di-fetch
function moveCouriers() {
  couriers.forEach(k => {
    if (k.status !== "DONE") {
      k.latitude  += (Math.random() - 0.5) * 0.002;
      k.longitude += (Math.random() - 0.5) * 0.002;
    }
  });
}

// generate riwayat rute dummy untuk satu kurir
function generateHistory(courierId, start, end) {
  const courier = couriers.find(k => k.courier_id === courierId);
  const points  = [];
  const startMs = start ? new Date(start).getTime() : Date.now() - 3600_000;
  const endMs   = end   ? new Date(end).getTime()   : Date.now();
  const steps   = 20;
  const stepMs  = (endMs - startMs) / steps;

  let lat = (courier?.latitude  ?? -6.200)  + (Math.random() - 0.5) * 0.01;
  let lng = (courier?.longitude ?? 106.816) + (Math.random() - 0.5) * 0.01;

  for (let i = 0; i <= steps; i++) {
    lat += (Math.random() - 0.5) * 0.003;
    lng += (Math.random() - 0.4) * 0.003;
    points.push({
      courier_id: courierId,
      latitude:   parseFloat(lat.toFixed(6)),
      longitude:  parseFloat(lng.toFixed(6)),
      timestamp:  new Date(startMs + i * stepMs).toISOString(),
      status:     i < 4 ? "IDLE" : i < 16 ? "DELIVERING" : "DONE",
    });
  }
  return points;
}

// http server
const server = http.createServer((req, res) => {
  // CORS header, agar browser tidak blokir request dari Live Server
  res.setHeader("Access-Control-Allow-Origin",  "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Content-Type", "application/json");

  // Preflight OPTIONS (browser kirim ini sebelum POST)
  if (req.method === "OPTIONS") { res.writeHead(204); res.end(); return; }

  const parsed   = url.parse(req.url, true);
  const pathname = parsed.pathname;
  const query    = parsed.query;

  console.log(`[${new Date().toLocaleTimeString()}] ${req.method} ${pathname}`);

  // GET /couriers/locations 
  if (req.method === "GET" && pathname === "/couriers/locations") {
    moveCouriers();
    res.writeHead(200);
    res.end(JSON.stringify(couriers));
    return;
  }

  // GET /couriers/:id/history
  const histMatch = pathname.match(/^\/couriers\/([^/]+)\/history$/);
  if (req.method === "GET" && histMatch) {
    const courierId = histMatch[1];
    const history   = generateHistory(courierId, query.start, query.end);
    res.writeHead(200);
    res.end(JSON.stringify(history));
    return;
  }

  // POST /couriers/location
  if (req.method === "POST" && pathname === "/couriers/location") {
    let body = "";
    req.on("data", chunk => body += chunk);
    req.on("end", () => {
      try {
        const data    = JSON.parse(body);
        const courier = couriers.find(k => k.courier_id === data.courier_id);
        if (courier) {
          courier.latitude  = data.latitude;
          courier.longitude = data.longitude;
          if (data.status) courier.status = data.status;
          console.log(`  → Updated ${data.courier_id}: ${data.latitude}, ${data.longitude}`);
        }
        res.writeHead(200);
        res.end(JSON.stringify({ ok: true }));
      } catch {
        res.writeHead(400);
        res.end(JSON.stringify({ error: "Invalid JSON" }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end(JSON.stringify({ error: "Endpoint tidak ditemukan" }));
});

server.listen(PORT, () => {
  console.log("╔══════════════════════════════════════╗");
  console.log("║   TrackIN Mock Server — RUNNING      ║");
  console.log(`║   http://127.0.0.1:${PORT}              ║`);
  console.log("╠══════════════════════════════════════╣");
  console.log("║  GET  /couriers/locations            ║");
  console.log("║  GET  /couriers/:id/history          ║");
  console.log("║  POST /couriers/location             ║");
  console.log("╚══════════════════════════════════════╝");
});