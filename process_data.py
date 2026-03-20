"""
Red Bull X-Alps 2025 - Raw Data Processor
Parses BigQuery CSV exports into optimized JSON for ArcGIS 3D visualization.
Uses time-bucket approach to handle out-of-order timestamps efficiently.
Outputs: data/race_data.json
"""
import csv
import json
import os
from collections import defaultdict

csv.field_size_limit(10 * 1024 * 1024)

DATA_DIR = r"E:\3. Data\Red Bull\RBX25-RAW-DB-Exports\RBX25-RAW-DB-Exports"
OUTPUT_DIR = r"E:\3. Data\Red Bull\app\data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2025 race window
TS_MIN = 1749513600   # 2025-06-10 00:00 UTC
TS_MAX = 1751155200   # 2025-06-28 24:00 UTC
MAX_ATHLETE_ID = 37

TRACK_BUCKET = 90     # seconds per track bucket (was 60)
THERMAL_BUCKET = 90   # seconds per thermal bucket (was 60)
WIND_BUCKET = 300     # seconds per wind bucket
THERMAL_VS_MIN = 1.0  # m/s climb threshold

ACT_MAP = {'S': 0, 'F': 1, 'H': 2}

def pf(v):
    try: return float(v) if v.strip() else None
    except: return None

def pi(v):
    try: return int(v) if v.strip() else None
    except: return None

# Bucket storage: aid -> {bucket_key: [lon,lat,alt,ts,act,gs,vs]}
track_buckets = defaultdict(dict)
# Global buckets for thermals/wind: bucket_key -> point
thermal_buckets = {}
wind_buckets = {}

csv_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith('.csv'))
total_points = 0
skipped = 0

for csv_file in csv_files:
    filepath = os.path.join(DATA_DIR, csv_file)
    print(f"Processing {csv_file}...", flush=True)

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)

        for row in reader:
            if len(row) < 4:
                continue
            data = row[3]
            parts = data.split('|')

            header = parts[0].split(';')
            aid = header[0].strip()
            sensor = header[1].strip() if len(header) > 1 else ''

            try:
                if int(aid) > MAX_ATHLETE_ID:
                    continue
            except ValueError:
                continue

            for point_str in parts[1:]:
                fields = point_str.split(';')
                if len(fields) < 4:
                    continue

                ts = pf(fields[0])
                lat = pf(fields[1])
                lon = pf(fields[2])
                alt = pf(fields[3])

                if not (ts and lat and lon):
                    continue
                ts_int = int(ts)
                if ts_int < TS_MIN or ts_int > TS_MAX:
                    skipped += 1
                    continue

                total_points += 1
                vs = pf(fields[9]) if len(fields) > 9 else None
                gs = pf(fields[7]) if len(fields) > 7 else None
                act_raw = fields[12].strip() if len(fields) > 12 and fields[12].strip() else None
                ws = pf(fields[10]) if len(fields) > 10 else None
                wd = pi(fields[11]) if len(fields) > 11 else None
                act_code = ACT_MAP.get(act_raw, -1)

                # --- Track bucket (prefer Naviter sensor if conflict) ---
                bk = ts_int // TRACK_BUCKET
                existing = track_buckets[aid].get(bk)
                # Prefer Naviter (N) > Satellite (S) > others; also prefer richer data
                sensor_priority = {'N': 3, 'S': 2, 'F': 1, 'O': 0, 'B': 0}
                new_priority = sensor_priority.get(sensor, 0)
                if existing is None or new_priority > existing[5]:
                    track_buckets[aid][bk] = [
                        round(lon, 4), round(lat, 4), int(alt),
                        ts_int, act_code,
                        new_priority  # temp: sensor priority for dedup
                    ]

                # --- Thermal bucket (Naviter only, strong climb) ---
                if sensor == 'N' and vs is not None and vs > THERMAL_VS_MIN:
                    tbk = (aid, ts_int // THERMAL_BUCKET)
                    if tbk not in thermal_buckets or vs > thermal_buckets[tbk][3]:
                        thermal_buckets[tbk] = [
                            round(lon, 4), round(lat, 4), int(alt),
                            round(vs, 1), ts_int, int(aid)
                        ]

                # --- Wind bucket (Naviter only) ---
                if sensor == 'N' and ws is not None and ws > 0 and wd is not None:
                    wbk = (aid, ts_int // WIND_BUCKET)
                    if wbk not in wind_buckets:
                        wind_buckets[wbk] = [
                            round(lon, 4), round(lat, 4), int(alt),
                            round(ws, 1), wd, ts_int, int(aid)
                        ]

print(f"\nProcessed {total_points:,} points (skipped {skipped:,} out-of-range)")

# Convert buckets to sorted lists, strip sensor priority from tracks
tracks = {}
for aid in sorted(track_buckets.keys(), key=lambda x: int(x)):
    sorted_pts = sorted(track_buckets[aid].values(), key=lambda x: x[3])
    # Remove the sensor_priority field (index 7)
    # Strip sensor_priority (index 5), keep [lon, lat, alt, ts, act]
    tracks[aid] = [[p[0], p[1], p[2], p[3], p[4]] for p in sorted_pts]

thermals = sorted(thermal_buckets.values(), key=lambda x: x[4])
wind_pts = sorted(wind_buckets.values(), key=lambda x: x[5])

# Stats
all_ts = []
total_track = 0
print(f"\nTrack points per athlete:")
for aid in sorted(tracks.keys(), key=lambda x: int(x)):
    n = len(tracks[aid])
    total_track += n
    if tracks[aid]:
        all_ts.extend([tracks[aid][0][3], tracks[aid][-1][3]])
    print(f"  Athlete {aid}: {n:,} pts")

min_ts = min(all_ts) if all_ts else 0
max_ts = max(all_ts) if all_ts else 0

print(f"\nTotal track: {total_track:,}")
print(f"Thermals: {len(thermals):,}")
print(f"Wind: {len(wind_pts):,}")

from datetime import datetime, timezone
print(f"Range: {datetime.fromtimestamp(min_ts, tz=timezone.utc)} to {datetime.fromtimestamp(max_ts, tz=timezone.utc)}")

# Colors (neon palette for dark background)
COLORS = [
    [255, 59, 48],    [255, 149, 0],   [255, 204, 0],   [52, 199, 89],
    [0, 199, 190],    [48, 176, 199],  [50, 173, 230],  [0, 122, 255],
    [88, 86, 214],    [175, 82, 222],  [255, 45, 85],   [162, 132, 94],
    [0, 255, 163],    [255, 55, 95],   [100, 210, 255], [255, 214, 10],
    [76, 217, 100],   [90, 200, 250],  [255, 150, 50],  [180, 100, 255],
    [255, 105, 180],  [0, 250, 154],   [255, 165, 0],   [138, 43, 226],
    [0, 206, 209],    [255, 99, 71],   [144, 238, 144], [255, 182, 193],
    [64, 224, 208],   [218, 165, 32],  [147, 112, 219], [255, 127, 80],
    [102, 205, 170],  [240, 128, 128], [100, 149, 237], [255, 215, 0],
    [72, 209, 204],   [244, 164, 96],  [186, 85, 211],  [127, 255, 212],
]

output = {
    "tracks": {},
    "thermals": thermals,
    "wind": wind_pts,
    "meta": {
        "min_ts": min_ts, "max_ts": max_ts,
        "track_fields": ["lon", "lat", "alt", "ts", "activity"],
        "thermal_fields": ["lon", "lat", "alt", "vs", "ts", "aid"],
        "wind_fields": ["lon", "lat", "alt", "ws", "wd", "ts", "aid"],
        "activity_codes": {"0": "Stationary", "1": "Flying", "2": "Hiking", "-1": "Unknown"},
    }
}

for i, aid in enumerate(sorted(tracks.keys(), key=lambda x: int(x))):
    output["tracks"][aid] = {
        "points": tracks[aid],
        "color": COLORS[i % len(COLORS)]
    }

out_path = os.path.join(OUTPUT_DIR, 'race_data.json')
with open(out_path, 'w') as f:
    json.dump(output, f)

print(f"\nSaved: {out_path}")
print(f"Size: {os.path.getsize(out_path) / 1024 / 1024:.1f} MB")
