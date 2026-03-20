# Red Bull X-Alps 2025 - 3D Race Replay & Thermal Analysis

Interactive 3D visualization of the **Red Bull X-Alps 2025** paragliding/hiking race across the European Alps, built with ArcGIS Maps SDK for JavaScript.

![Dashboard](https://img.shields.io/badge/ArcGIS-SceneView%203D-blue?style=flat-square)
![Data](https://img.shields.io/badge/GPS%20Points-37.5M-orange?style=flat-square)
![Athletes](https://img.shields.io/badge/Athletes-35-red?style=flat-square)
![Race](https://img.shields.io/badge/Race%20Days-17-green?style=flat-square)

---

## Overview

This dashboard replays the entire Red Bull X-Alps 2025 race in 3D, combining animated athlete tracking with thermal and wind analysis across the Alpine terrain. The visualization processes **37.5 million GPS fixes** from 35 athletes into an interactive experience.

### Key Features

- **3D Race Replay** - Animated athlete markers moving along actual GPS tracks above Alpine terrain with smooth interpolation
- **Thermal Column Visualization** - 3D cylinders at detected thermal locations, sized and colored by vertical speed (climb rate)
- **Wind Observation Layer** - Windspeed data from onboard Naviter instruments
- **Dynamic Sun Lighting** - Sun position updates with the time slider for realistic day/night transitions
- **Time Animation Controls** - Play/pause, variable speed (0.5h/s to 12h/s), scrub through 17 race days
- **Per-Athlete Controls** - Toggle visibility, fly-to-athlete camera navigation, live altitude readout

---

## Data Pipeline

```
Naviter GPS  -->  Google Pub/Sub  -->  BigQuery  -->  Python ETL  -->  JSON  -->  ArcGIS SceneView
  Devices          (real-time)       (raw store)     (parse &         (25MB)     (3D rendering)
                                                     downsample)
```

### Source Data
- **37.5M GPS fixes** from 35 athletes over 17 race days (June 10-27, 2025)
- **4 sensor types**: Naviter (primary), Flarm/Fanet, OGN, Satellite
- **18 fields per fix**: lat, lon, GPS altitude, baro altitude, AGL, speed, groundspeed, heading, vertical speed, windspeed, wind direction, activity mode, airspace, rest status, nightpass status, GPS quality, additional JSON

### Processing
- Pipe/semicolon-delimited PubSub messages parsed from BigQuery CSV exports
- Deduplicated via **60-second time buckets** with sensor priority ranking (Naviter > Satellite > Flarm > OGN)
- Thermal events extracted where vertical speed > 1.0 m/s
- Wind observations sampled every 5 minutes per athlete

### Output
| Layer | Points | Description |
|---|---|---|
| Tracks | 439,274 | Athlete routes with altitude and activity mode |
| Thermals | 79,550 | Climb events with vertical speed |
| Wind | 61,946 | Wind speed and direction observations |

---

## Controls

| Control | Action |
|---|---|
| `Space` | Play / Pause animation |
| `Arrow Left/Right` | Jump -/+ 1 hour |
| Time Slider | Scrub through entire race |
| Speed Buttons | 0.5h/s, 1h/s, 4h/s, 12h/s |
| Click Athlete | Toggle track visibility |
| Double-click Athlete | Fly camera to position |
| `?` Button | Show intro guide |
| Mouse / Touch | Orbit, pan, zoom 3D scene |

---

## Setup

### Prerequisites
- An [ArcGIS API Key](https://developers.arcgis.com/) (free tier works)
- Python 3.x (for data processing only)

### Running Locally

1. Clone this repository
2. Set your ArcGIS API key in `index.html` (`ARCGIS_API_KEY` constant)
3. Start a local server:
   ```bash
   cd redbull-xalps-3d
   python -m http.server 8080
   ```
4. Open http://localhost:8080

### Login
Use the demo credentials shown on the login screen.

### Reprocessing Data (optional)
If you have the raw BigQuery CSV exports:
```bash
python process_data.py
```
This reads CSVs from the configured `DATA_DIR` and outputs `data/race_data.json`.

---

## Tech Stack

- **Frontend**: ArcGIS Maps SDK for JavaScript 4.30 (SceneView, GraphicsLayer, 3D symbols)
- **Data Processing**: Python (csv, json, defaultdict)
- **Data Source**: Google BigQuery via Pub/Sub (Naviter GPS telemetry)
- **Rendering**: WebGL via ArcGIS SceneView with world elevation service

---

## Architecture

```
index.html
├── Login Screen (client-side auth gate)
├── Intro Modal (data pipeline + controls guide)
├── SceneView (satellite basemap + world elevation)
│   ├── TrackLayer (GraphicsLayer - 3D polylines per athlete)
│   ├── ThermalLayer (GraphicsLayer - 3D cylinders, time-filtered)
│   ├── WindLayer (GraphicsLayer - colored dots, time-filtered)
│   └── MarkerLayer (GraphicsLayer - animated position dots)
├── Time Controls (custom slider + requestAnimationFrame loop)
├── Sidebar (athlete list with live altitude)
└── Layer Toggles

process_data.py
├── CSV Parser (handles 10MB+ fields, pipe/semicolon delimited)
├── Time-Bucket Deduplicator (60s buckets, sensor priority)
├── Thermal Extractor (vs > 1.0 m/s, 60s buckets)
├── Wind Sampler (300s buckets, Naviter-only)
└── JSON Serializer (race_data.json)
```

---

## License

This project is for demonstration and educational purposes. Race data is property of Red Bull Media House / Red Bull X-Alps.
