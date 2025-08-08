import requests
import json
from datetime import datetime
from pathlib import Path

# === Inställningar ===
COORDS_FILE = "coordinates.json"
OUTPUT_FILE = "dashboard.html"
ALERTS_URL = "https://opendata.smhi.se/triangulering/alerts.json"

# === Hjälpfunktioner ===

def fetch_forecast(lat, lon):
    url = f"https://opendata.smhi.se/metfcst/pmp/json/1.0/?lat={lat}&lon={lon}"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def get_alerts():
    r = requests.get(ALERTS_URL)
    if r.status_code != 200:
        return []
    return r.json()

def extract_weather_data(forecast):
    try:
        t_series = forecast["timeSeries"]
        first = t_series[0]["parameters"]
        data = {p["name"]: p["values"][0] for p in first}
        return {
            "temperature": data.get("t"),
            "precipitation": data.get("pmean"),
            "soilMoisture": data.get("sfcsoilmoisture", "–")
        }
    except Exception:
        return {"temperature": "–", "precipitation": "–", "soilMoisture": "–"}

def match_alerts_to_locations(alerts, coordinates):
    matched = []
    for alert in alerts:
        for area in alert.get("info", [{}])[0].get("area", []):
            for coord in coordinates:
                if coord["name"].lower() in area.get("areaDesc", "").lower():
                    matched.append((coord["name"], alert["info"][0]["event"]))
    return matched

# === Huvudlogik ===

with open(COORDS_FILE, encoding="utf-8") as f:
    coordinates = json.load(f)

weather_data = []
for coord in coordinates:
    forecast = fetch_forecast(coord["lat"], coord["lon"])
    if forecast:
        data = extract_weather_data(forecast)
        weather_data.append({
            "name": coord["name"],
            "temperature": data["temperature"],
            "precipitation": data["precipitation"],
            "soilMoisture": data["soilMoisture"]
        })
    else:
        weather_data.append({
            "name": coord["name"],
            "temperature": "–",
            "precipitation": "–",
            "soilMoisture": "–"
        })

alerts_raw = get_alerts()
matched_alerts = match_alerts_to_locations(alerts_raw, coordinates)

# === Generera HTML ===

html = f"""<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <title>Västra Götalands väderdashboard</title>
    <style>
        body {{ font-family: sans-serif; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 2em; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
        th {{ background-color: #f0f0f0; }}
        .warning {{ background-color: #ffdddd; }}
    </style>
</head>
<body>
    <h1>Väderdata för Västra Götaland</h1>
    <p>Senast uppdaterad: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

    <table>
        <tr>
            <th>Plats</th>
            <th>Temperatur (°C)</th>
            <th>Nederbörd (mm)</th>
            <th>Markfuktighet</th>
        </tr>
"""

for row in weather_data:
    html += f"""<tr>
        <td>{row['name']}</td>
        <td>{row['temperature']}</td>
        <td>{row['precipitation']}</td>
        <td>{row['soilMoisture']}</td>
    </tr>
"""

html += "</table>\n"

if matched_alerts:
    html += "<h2>Aktuella varningar</h2>\n<table>\n<tr><th>Plats</th><th>Typ av varning</th></tr>\n"
    for loc, warning in matched_alerts:
        html += f"<tr class='warning'><td>{loc}</td><td>{warning}</td></tr>\n"
    html += "</table>\n"
else:
    html += "<p>Inga varningar just nu.</p>\n"

html += "</body></html>"

Path(OUTPUT_FILE).write_text(html, encoding="utf-8")
