"""
Smart Traffic, Highway and Bridge Management System
Cloud Computing Project
Backend: Flask REST Server
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import time
import uuid

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────────────────────
# IN-MEMORY DATABASE  (Cloud: AWS DynamoDB / Firebase Firestore)
# ─────────────────────────────────────────────────────────────

db = {
    "highways"  : {},
    "bridges"   : {},
    "signals"   : {},
    "alerts"    : [],
    "incidents" : [],
    "log"       : [],
    "started"   : time.time()
}

# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def now_str():
    return datetime.now().strftime("%H:%M:%S")

def new_alert(level, node_id, msg, category="traffic"):
    alert = {
        "id"       : str(uuid.uuid4())[:6],
        "time"     : now_str(),
        "ts"       : time.time(),
        "level"    : level,
        "node_id"  : node_id,
        "message"  : msg,
        "category" : category
    }
    db["alerts"].append(alert)
    if len(db["alerts"]) > 150:
        db["alerts"] = db["alerts"][-150:]
    return alert

def log_action(node_id, action, result, operator="Control Room"):
    entry = {
        "id"       : str(uuid.uuid4())[:6],
        "time"     : now_str(),
        "ts"       : time.time(),
        "node_id"  : node_id,
        "action"   : action,
        "result"   : result,
        "operator" : operator
    }
    db["log"].append(entry)
    if len(db["log"]) > 100:
        db["log"] = db["log"][-100:]

# ─────────────────────────────────────────────────────────────
# ROUTES — SYSTEM
# ─────────────────────────────────────────────────────────────

@app.route("/")
def home():
    uptime = int(time.time() - db["started"])
    return jsonify({
        "project"  : "Smart Traffic, Highway and Bridge Management System",
        "batch"    : "A1",
        "backend"  : "Flask 3.x",
        "cloud"    : "AWS ap-south-1 (Mumbai)",
        "status"   : "running",
        "uptime_s" : uptime,
        "version"  : "1.0.0"
    })


@app.route("/dashboard")
def dashboard():
    highways = list(db["highways"].values())
    bridges  = list(db["bridges"].values())
    signals  = list(db["signals"].values())

    avg_speed = 0
    peak_cong = 0
    total_veh = 0

    if highways:
        avg_speed = round(sum(h["speed"] for h in highways) / len(highways), 1)
        peak_cong = round(max(h["congestion"] for h in highways), 1)
        total_veh = sum(h["vehicles"] for h in highways)

    bridge_warn = sum(1 for b in bridges if b.get("status") in ("warning","critical"))
    open_inc    = sum(1 for i in db["incidents"] if not i.get("resolved"))

    return jsonify({
        "highways"  : highways,
        "bridges"   : bridges,
        "signals"   : signals,
        "alerts"    : db["alerts"][-40:],
        "incidents" : db["incidents"][-15:],
        "log"       : db["log"][-20:],
        "analytics" : {
            "avg_speed_kmh"   : avg_speed,
            "peak_congestion" : peak_cong,
            "total_vehicles"  : total_veh,
            "bridge_warnings" : bridge_warn,
            "open_incidents"  : open_inc,
            "total_assets"    : len(highways) + len(bridges) + len(signals)
        },
        "server_time": now_str()
    })


# ─────────────────────────────────────────────────────────────
# ROUTES — DATA INGESTION
# ─────────────────────────────────────────────────────────────

@app.route("/ingest", methods=["POST"])
def ingest():
    data   = request.get_json()
    alerts = []

    for h in data.get("highways", []):
        cong = h["congestion"]
        if cong > 85:
            h["status"] = "critical"
            alerts.append(new_alert("critical", h["id"],
                f"CRITICAL: {h['name']} — {cong:.0f}% congested, speed {h['speed']:.0f} km/h"))
        elif cong > 60:
            h["status"] = "warning"
            alerts.append(new_alert("warning", h["id"],
                f"WARNING: {h['name']} — congestion rising to {cong:.0f}%"))
        else:
            h["status"] = "normal"
        db["highways"][h["id"]] = h

    for b in data.get("bridges", []):
        hi       = b["health"]
        load_pct = (b["load"] / b["capacity"]) * 100
        if hi < 0.70 or b["vibration"] > 9:
            b["status"] = "critical"
            alerts.append(new_alert("critical", b["id"],
                f"STRUCTURAL ALERT: {b['name']} — health {hi*100:.0f}%, vibration {b['vibration']:.1f} Hz",
                "bridge"))
        elif hi < 0.83 or load_pct > 85:
            b["status"] = "warning"
            alerts.append(new_alert("warning", b["id"],
                f"BRIDGE WARNING: {b['name']} — load at {load_pct:.0f}% capacity",
                "bridge"))
        else:
            b["status"] = "healthy"
        db["bridges"][b["id"]] = b

    for s in data.get("signals", []):
        db["signals"][s["id"]] = s

    return jsonify({
        "status"         : "ok",
        "alerts_created" : len(alerts),
        "highways"       : len(data.get("highways", [])),
        "bridges"        : len(data.get("bridges", [])),
        "signals"        : len(data.get("signals", []))
    })


# ─────────────────────────────────────────────────────────────
# ROUTES — INCIDENTS
# ─────────────────────────────────────────────────────────────

@app.route("/incident", methods=["POST"])
def report_incident():
    data = request.get_json()
    inc  = {
        "id"       : str(uuid.uuid4())[:6],
        "time"     : now_str(),
        "ts"       : time.time(),
        "node_id"  : data["node_id"],
        "type"     : data["type"],
        "severity" : data["severity"],
        "location" : data["location"],
        "reporter" : data.get("reporter", "Field Unit"),
        "resolved" : False
    }
    db["incidents"].append(inc)
    lvl = "critical" if data["severity"] == "high" else "warning"
    new_alert(lvl, data["node_id"],
        f"INCIDENT [{data['type'].upper()}] at {data['location']} — {data['severity']} severity",
        "incident")
    return jsonify({"status": "logged", "incident_id": inc["id"]})


@app.route("/incident/<inc_id>/resolve", methods=["PATCH"])
def resolve_incident(inc_id):
    for inc in db["incidents"]:
        if inc["id"] == inc_id:
            inc["resolved"]    = True
            inc["resolved_at"] = now_str()
            new_alert("info", inc["node_id"],
                f"Incident {inc_id} resolved at {inc['location']}", "incident")
            return jsonify({"status": "resolved"})
    return jsonify({"error": "not found"}), 404


# ─────────────────────────────────────────────────────────────
# ROUTES — OPERATOR ACTIONS
# ─────────────────────────────────────────────────────────────

@app.route("/action/<node_id>", methods=["POST"])
def take_action(node_id):
    data     = request.get_json()
    action   = data.get("action")
    operator = data.get("operator", "Control Room")
    result   = "Node not found"

    if node_id in db["highways"]:
        node = db["highways"][node_id]
        if action == "deploy_patrol":
            node["congestion"] = max(10, node["congestion"] - 30)
            node["speed"]      = min(80, node["speed"] + 20)
            node["status"]     = "normal"
            result = f"Patrol deployed on {node['name']} — congestion reduced to {node['congestion']:.0f}%"
        elif action == "retime_signals":
            node["congestion"] = max(12, node["congestion"] - 18)
            node["speed"]      = min(70, node["speed"] + 12)
            result = f"Signals retimed on {node['name']} — speed improved to {node['speed']:.0f} km/h"
        elif action == "close_lane":
            node["lanes"]  = max(1, node.get("lanes", 2) - 1)
            node["status"] = "lane_closed"
            result = f"Lane closed on {node['name']} — {node['lanes']} lane(s) remaining"
        elif action == "notify_maintenance":
            result = f"Maintenance team notified for {node['name']}"
            new_alert("info", node_id, result)

    elif node_id in db["bridges"]:
        node = db["bridges"][node_id]
        if action == "deploy_patrol":
            node["health"]    = min(1.0, node["health"] + 0.10)
            node["vibration"] = max(2.0, node["vibration"] - 3.0)
            node["status"]    = "healthy"
            result = f"Inspection team sent to {node['name']}"
        elif action == "divert_load":
            node["load"]   = max(20, node["load"] - 25)
            node["status"] = "warning"
            result = f"Traffic diverted from {node['name']} — load reduced"
        elif action == "notify_maintenance":
            result = f"Engineers alerted for {node['name']}"
            new_alert("info", node_id, result, "bridge")

    elif node_id in db["signals"]:
        node = db["signals"][node_id]
        if action == "retime_signals":
            node["cycle_time"] = max(30, node.get("cycle_time", 90) - 15)
            node["status"]     = "optimised"
            result = f"Signal cycle at {node['name']} reduced to {node['cycle_time']}s"

    log_action(node_id, action, result, operator)
    new_alert("info", node_id, f"ACTION: {result}", "operator")
    return jsonify({"status": "ok", "result": result})


# ─────────────────────────────────────────────────────────────
# ROUTES — ANALYTICS
# ─────────────────────────────────────────────────────────────

@app.route("/analytics")
def analytics():
    highways = list(db["highways"].values())
    bridges  = list(db["bridges"].values())
    return jsonify({
        "highway_summary": {
            "total"    : len(highways),
            "critical" : sum(1 for h in highways if h.get("status") == "critical"),
            "warning"  : sum(1 for h in highways if h.get("status") == "warning"),
            "normal"   : sum(1 for h in highways if h.get("status") == "normal"),
        },
        "bridge_summary": {
            "total"    : len(bridges),
            "critical" : sum(1 for b in bridges if b.get("status") == "critical"),
            "warning"  : sum(1 for b in bridges if b.get("status") == "warning"),
            "healthy"  : sum(1 for b in bridges if b.get("status") == "healthy"),
        },
        "incidents": {
            "total"    : len(db["incidents"]),
            "open"     : sum(1 for i in db["incidents"] if not i.get("resolved")),
            "resolved" : sum(1 for i in db["incidents"] if i.get("resolved")),
        },
        "alerts_today" : len(db["alerts"]),
        "actions_taken": len(db["log"])
    })


# ─────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  Smart Traffic, Highway & Bridge Management System")
    print("  Flask Server  |  A1 Batch  |  Port 5000")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000, debug=True)