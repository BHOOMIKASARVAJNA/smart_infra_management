"""
Smart Traffic, Highway and Bridge Management System
IoT Sensor Simulator | Cloud Computing Project

Simulates:
  - 5 Bengaluru roads
  - 4 Bridges
  - 6 Traffic Signal Junctions
Posts to Flask server every 2 seconds.
"""

import requests
import time
import random
import copy

SERVER = "https://smart-infra-management-2.onrender.com/ingest"
INCIDENT = "https://smart-infra-management-2.onrender.com/incident"

HIGHWAYS = [
    {
        "id"        : "RD-MYSORE",
        "name"      : "Mysore Road (NH-275)",
        "zone"      : "West Bengaluru",
        "path"      : [[12.9716,77.5946],[12.9500,77.5600],[12.9200,77.5200],[12.8900,77.4800]],
        "speed"     : 58.0,
        "congestion": 48.0,
        "vehicles"  : 3200,
        "lanes"     : 6,
        "wait_min"  : 4.0,
        "type"      : "National Highway"
    },
    {
        "id"        : "RD-TUMKUR",
        "name"      : "Tumkur Road (NH-48)",
        "zone"      : "North-West Bengaluru",
        "path"      : [[13.0250,77.5350],[13.0600,77.5100],[13.0900,77.4900],[13.1200,77.4700]],
        "speed"     : 62.0,
        "congestion": 40.0,
        "vehicles"  : 2800,
        "lanes"     : 4,
        "wait_min"  : 3.5,
        "type"      : "National Highway"
    },
    {
        "id"        : "RD-KANAKAPURA",
        "name"      : "Kanakapura Road (SH-87)",
        "zone"      : "South Bengaluru",
        "path"      : [[12.9352,77.5644],[12.9100,77.5500],[12.8800,77.5300],[12.8500,77.5100]],
        "speed"     : 35.0,
        "congestion": 72.0,
        "vehicles"  : 4100,
        "lanes"     : 4,
        "wait_min"  : 8.0,
        "type"      : "State Highway"
    },
    {
        "id"        : "RD-WHITEFIELD",
        "name"      : "Whitefield Main Road",
        "zone"      : "East Bengaluru",
        "path"      : [[12.9698,77.7499],[12.9800,77.7300],[12.9900,77.7100],[13.0000,77.6900]],
        "speed"     : 28.0,
        "congestion": 78.0,
        "vehicles"  : 4800,
        "lanes"     : 4,
        "wait_min"  : 10.0,
        "type"      : "City Road"
    },
    {
        "id"        : "RD-BELLARY",
        "name"      : "Bellary Road (NH-44)",
        "zone"      : "North Bengaluru",
        "path"      : [[13.0600,77.5950],[13.0900,77.5900],[13.1300,77.5850],[13.1700,77.5800]],
        "speed"     : 70.0,
        "congestion": 32.0,
        "vehicles"  : 2100,
        "lanes"     : 6,
        "wait_min"  : 2.5,
        "type"      : "National Highway"
    },
]

BRIDGES = [
    {
        "id"          : "BR-MYSOREROAD",
        "name"        : "Mysore Road Elevated Corridor",
        "zone"        : "West",
        "lat"         : 12.9500, "lng": 77.5600,
        "health"      : 0.93,
        "vibration"   : 3.8,
        "load"        : 78.0,
        "capacity"    : 180.0,
        "temperature" : 29.0,
        "age_years"   : 8,
        "last_check"  : "2026-01-15",
        "material"    : "Pre-stressed Concrete"
    },
    {
        "id"          : "BR-NAGAWARA",
        "name"        : "Nagawara Lake Overbridge",
        "zone"        : "North",
        "lat"         : 13.0450, "lng": 77.6200,
        "health"      : 0.79,
        "vibration"   : 6.9,
        "load"        : 130.0,
        "capacity"    : 160.0,
        "temperature" : 31.5,
        "age_years"   : 22,
        "last_check"  : "2025-11-20",
        "material"    : "Reinforced Concrete"
    },
    {
        "id"          : "BR-BELLANDUR",
        "name"        : "Bellandur Lake Bridge",
        "zone"        : "South-East",
        "lat"         : 12.9246, "lng": 77.6780,
        "health"      : 0.96,
        "vibration"   : 2.5,
        "load"        : 55.0,
        "capacity"    : 140.0,
        "temperature" : 27.5,
        "age_years"   : 5,
        "last_check"  : "2026-02-28",
        "material"    : "Steel Composite"
    },
    {
        "id"          : "BR-PEENYA",
        "name"        : "Peenya Industrial Flyover",
        "zone"        : "North-West",
        "lat"         : 13.0280, "lng": 77.5200,
        "health"      : 0.85,
        "vibration"   : 5.1,
        "load"        : 105.0,
        "capacity"    : 130.0,
        "temperature" : 30.0,
        "age_years"   : 15,
        "last_check"  : "2026-01-05",
        "material"    : "Reinforced Concrete"
    },
]

SIGNALS = [
    {"id":"SIG-JAYANAGAR",   "name":"Jayanagar 4th Block Junction", "lat":12.9254,"lng":77.5830,"cycle_time":90, "queue":22,"status":"normal"  },
    {"id":"SIG-RAJAJINAGAR", "name":"Rajajinagar Circle",            "lat":12.9921,"lng":77.5530,"cycle_time":75, "queue":35,"status":"normal"  },
    {"id":"SIG-YESHWANTPUR", "name":"Yeshwantpur Circle",            "lat":13.0234,"lng":77.5512,"cycle_time":60, "queue":18,"status":"normal"  },
    {"id":"SIG-KORAMANGALA", "name":"Koramangala Water Tank Jn",     "lat":12.9354,"lng":77.6195,"cycle_time":90, "queue":44,"status":"warning" },
    {"id":"SIG-MALLESHWARAM","name":"Malleshwaram 18th Cross",        "lat":13.0050,"lng":77.5700,"cycle_time":80, "queue":15,"status":"normal"  },
    {"id":"SIG-ELECTRONIC",  "name":"Electronic City Phase 1 Gate",  "lat":12.8445,"lng":77.6600,"cycle_time":120,"queue":60,"status":"critical"},
]

INCIDENT_TYPES = ["accident", "pothole", "flooding", "breakdown", "fallen_tree"]
LOCATIONS = {
    "RD-MYSORE"     : "Mysore Road near Kengeri Metro Station",
    "RD-TUMKUR"     : "Tumkur Road near Peenya Industrial Area",
    "RD-KANAKAPURA" : "Kanakapura Road near Gottigere Junction",
    "RD-WHITEFIELD" : "Whitefield Road near ITPL Main Gate",
    "RD-BELLARY"    : "Bellary Road near Hebbal Interchange",
}

def update_highway(h, tick):
    h["speed"]      = round(max(5,  min(110, h["speed"]      + random.gauss(0, 5))), 1)
    h["congestion"] = round(max(5,  min(100, h["congestion"] + random.gauss(0, 7))), 1)
    h["vehicles"]   = random.randint(500, 6000)
    h["wait_min"]   = round(max(0.5, h["congestion"] / 10), 1)
    is_peak = (20 < (tick % 200) < 60) or (120 < (tick % 200) < 160)
    if is_peak:
        h["congestion"] = min(100, round(h["congestion"] * 1.35, 1))
        h["speed"]      = max(5,   round(h["speed"]      * 0.65, 1))
    if h["id"] == "RD-WHITEFIELD" and random.random() < 0.20:
        h["congestion"] = round(random.uniform(85, 98), 1)
        h["speed"]      = round(random.uniform(5, 18),  1)
        h["vehicles"]   = random.randint(5000, 7000)
    if h["id"] == "RD-KANAKAPURA" and random.random() < 0.12:
        h["congestion"] = round(random.uniform(78, 92), 1)
        h["speed"]      = round(random.uniform(10, 22), 1)
    return h

def update_bridge(b):
    b["health"]      = round(max(0.40, min(1.0,  b["health"]    + random.gauss(0, 0.015))), 3)
    b["vibration"]   = round(max(1.0,  min(15.0, b["vibration"] + random.gauss(0, 0.5))),  1)
    b["load"]        = round(max(15,   min(b["capacity"]*1.1, b["load"] + random.gauss(0, 9))), 1)
    b["temperature"] = round(random.uniform(25, 40), 1)
    if b["id"] == "BR-NAGAWARA" and random.random() < 0.12:
        b["health"]    = round(random.uniform(0.60, 0.72), 3)
        b["vibration"] = round(random.uniform(8.5, 13.0),  1)
        b["load"]      = round(random.uniform(140, 160),   1)
    if b["id"] == "BR-PEENYA" and random.random() < 0.08:
        b["load"]      = round(random.uniform(120, 148), 1)
        b["vibration"] = round(random.uniform(7.0, 10.5), 1)
    return b

def update_signal(s, tick):
    s["queue"] = max(0, int(s["queue"] + random.gauss(0, 6)))
    is_peak = (20 < (tick % 200) < 60) or (120 < (tick % 200) < 160)
    if is_peak:
        s["queue"] = min(150, s["queue"] + random.randint(8, 20))
    if s["queue"] > 50:
        s["status"] = "critical"
    elif s["queue"] > 25:
        s["status"] = "warning"
    else:
        s["status"] = "normal"
    return s

def maybe_incident(highways, tick):
    if random.random() < 0.04:
        road     = random.choice(highways)
        severity = random.choice(["low", "medium", "high"])
        itype    = random.choice(INCIDENT_TYPES)
        location = LOCATIONS.get(road["id"], road["name"])
        payload  = {
            "node_id"  : road["id"],
            "type"     : itype,
            "severity" : severity,
            "location" : location,
            "reporter" : f"CCTV-Cam-{random.randint(100, 999)}"
        }
        try:
            requests.post(INCIDENT, json=payload, timeout=3)
            print(f"  ⚡ INCIDENT → [{itype}] on {road['name']} | severity: {severity}")
        except:
            pass

def run():
    print("=" * 58)
    print("  Smart Traffic, Highway & Bridge Management System")
    print("  Sensor Simulator  |  Bangaluru Road Network")
    print(f"  Sending data to -> {SERVER}")
    print("=" * 58)
    tick = 0
    while True:
        tick += 1
        roads   = [update_highway(copy.deepcopy(h), tick) for h in HIGHWAYS]
        bridges = [update_bridge(copy.deepcopy(b))        for b in BRIDGES]
        signals = [update_signal(copy.deepcopy(s), tick)  for s in SIGNALS]
        payload = {"highways": roads, "bridges": bridges, "signals": signals}
        try:
            r      = requests.post(SERVER, json=payload, timeout=5)
            resp   = r.json()
            alerts = resp.get("alerts_created", 0)
            a_tag  = f"  ⚠ {alerts} alert(s)" if alerts else ""
            print(f"[Tick {tick:04d}]  OK  {len(roads)} roads · {len(bridges)} bridges · {len(signals)} signals — HTTP {r.status_code}{a_tag}")
        except requests.ConnectionError:
            print(f"[Tick {tick:04d}]  X   Server offline — run: python server.py")
        except Exception as e:
            print(f"[Tick {tick:04d}]  X   {e}")
        maybe_incident(roads, tick)
        time.sleep(2)

if __name__ == "__main__":
    run()
