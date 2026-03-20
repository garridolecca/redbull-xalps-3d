# Red Bull X-Alps 2025 - 3D Race Replay & Thermal Analysis

Interactive 3D visualization of the **Red Bull X-Alps 2025** paragliding/hiking race across the European Alps, built with ArcGIS Maps SDK for JavaScript and Calcite Design System.

![ArcGIS](https://img.shields.io/badge/ArcGIS-SceneView%203D-0079C1?style=flat-square)
![Calcite](https://img.shields.io/badge/Calcite-Design%20System-333?style=flat-square)
![Data](https://img.shields.io/badge/GPS%20Points-37.5M-orange?style=flat-square)
![Athletes](https://img.shields.io/badge/Athletes-35-DB0A40?style=flat-square)
![Race](https://img.shields.io/badge/Race%20Days-17-34C759?style=flat-square)

**[Live Demo](https://garridolecca.github.io/redbull-xalps-3d/)** | **[Presentation (PPTX)](RedBull_XAlps_2025_Dashboard.pptx)**

---

## About the Race

The **Red Bull X-Alps** is an adventure race across the European Alps where athletes travel from Salzburg, Austria to Monaco by **paragliding or hiking** - no motorized transport allowed. Athletes carry their own paraglider (~30 kg) and must pass through mandatory turnpoints. First to reach the finish line wins. The 2025 edition featured 35 athletes from 20+ countries racing over 17 days.

---

## Overview

This dashboard replays the entire race in 3D, combining animated athlete tracking with real-time thermal and wind analysis. The visualization processes **37.5 million GPS fixes** from 35 athletes into an interactive experience.

### Key Features

| Feature | Description |
|---|---|
| **3D Race Replay** | Animated athlete markers moving along GPS tracks above Alpine terrain with smooth interpolation |
| **Live Race Positions** | Dynamic ranking based on westward progress (longitude). Position numbers update in real-time as athletes overtake each other |
| **Activity Shape Markers** | Triangle = Flying, Circle = Hiking/Resting. Shapes change dynamically during playback |
| **Athlete Names & Details** | Full roster with 35 named athletes, flags, countries, live groundspeed, altitude, and activity status |
| **Wind Rose Chart** | Canvas-drawn polar diagram with 16 directions, 4 speed bins, live stats (avg/max/dominant). Updates during playback |
| **Thermal Statistics** | Active count, average and max climb rate. Only counts airborne climb events (Flying + VS > 1.0 m/s) |
| **Altitude Profile** | Sparkline elevation chart for solo'd athlete with moving time marker |
| **Solo Mode** | Filter all data to a single athlete: tracks, thermals, wind, altitude profile |
| **Dynamic Sun Lighting** | Sun position updates with playback time for realistic day/night transitions |
| **Permanent Analysis Sidebar** | Always-visible left panel with layers, thermal stats, wind rose, and altitude profile |
| **Full Documentation Guide** | Scrollable guide page (via ? button) with data pipeline, methodology, caveats, and controls |

---

## Data Pipeline

```
Naviter GPS  -->  Google Pub/Sub  -->  BigQuery  -->  Python ETL  -->  JSON   -->  ArcGIS SceneView
  Devices          (real-time)       (raw store)     (parse &         (18MB)      (3D rendering)
  (18 fields/fix)                    (14 CSVs)       downsample)                  Calcite Design
```

### Source Data
- **37.5M GPS fixes** from 35 athletes over 17 race days (June 10-27, 2025)
- **4 sensor types**: Naviter (primary), Flarm/Fanet, OGN, Satellite
- **18 fields per fix**: lat, lon, GPS altitude, baro altitude, AGL, speed, groundspeed, heading, vertical speed, windspeed, wind direction, activity mode (F/H/S), airspace, rest status, nightpass status, GPS quality

### Processing
- Pipe/semicolon-delimited PubSub messages parsed from BigQuery CSV exports
- Deduplicated via **90-second time buckets** with sensor priority ranking (Naviter > Satellite > Flarm > OGN)
- Coordinates rounded to 4 decimal places (~11m accuracy), altitude to integers
- Thermal events: Vertical Speed > 1.0 m/s **AND** UserActivity = Flying (Naviter only)
- Wind observations sampled every 5 minutes per athlete (Naviter only)

### Output
| Layer | Points | Description |
|---|---|---|
| Tracks | 293,914 | Athlete routes with altitude, activity mode, and groundspeed |
| Thermals | 46,207 | Airborne-only climb events with vertical speed |
| Wind | 61,946 | Wind speed and direction observations |

---

## Analysis Methodology

> Full details available in the app's guide page (? button)

| Indicator | How It's Derived | Caveats |
|---|---|---|
| **Climb Events ("Thermals")** | GPS fixes where Vertical Speed > 1.0 m/s AND UserActivity = Flying, Naviter sensor only | No clustering into distinct events. 1.0 m/s threshold is arbitrary. Could include ridge/wave lift |
| **Wind Rose** | Raw Windspeed + Wind Direction from Naviter Omni instrument, 5-min samples, +/-1.5hr window | Onboard measurements, not weather station data |
| **Thermal Stats** | Count, mean, max of qualifying vertical speed values within +/-1hr window | "Active" = GPS fix count, not distinct thermal count |
| **Altitude Profile** | Raw GPS Altitude (ellipsoid height) plotted over full track timeline | No terrain correction, no smoothing |
| **Race Position** | Athletes ranked by longitude (lowest = furthest west toward Monaco) | Approximate - doesn't follow actual race route |
| **Activity Mode** | Directly from UserActivity field: F=Flying, H=Hiking, S=Stationary | Only from Naviter sensor, not all sensor types |

---

## Layout

```
+------------------------------------------------------------------+
|  RED BULL X-ALPS 2025            SOLO #1 Maurer   [chart][ppl][?]|
+-------------+----------------------------------------------------+
|             |                                                    |
|  ANALYSIS   |                    3D MAP                          |
|  ---------  |                                                    |
|  Layers     |          [Triangle markers = Flying]               |
|  Thermals   |          [Circle markers = Hiking/Rest]            |
|  Wind Rose  |          [Glowing track lines]                     |
|  Alt Profile|                                                    |
|             +----------------------------------------------------+
|             | Day 5  Jun 16, 2025   [>] ========== 1x 4x  17:22  |
|             | Thermals: 42    Wind: 156    Active: 28             |
+-------------+----------------------------------------------------+
```

- **Left sidebar**: Permanent analysis panel (layers, thermal stats, wind rose, altitude profile)
- **Map**: Full 3D SceneView with satellite imagery + world elevation
- **Right panel**: Floating athlete list (toggle via people icon) with live positions, groundspeed, activity
- **Footer**: Time controls with play/pause, slider, speed buttons, stats
- **Mobile**: Left sidebar collapses, panels become full-width overlays

---

## Controls

| Control | Action |
|---|---|
| Play / Pause | Start or stop the race animation (also: `Space` bar) |
| Time Slider | Drag to scrub through the 17-day race |
| Speed (0.5x-12x) | How fast time advances (1x = 1 simulated hour per real second) |
| `Arrow Left/Right` | Jump backward / forward 1 hour |
| SOLO (pin icon) | In Athletes panel, filter all data to one athlete |
| Show All | Exit solo mode, restore all athletes |
| Double-click name | Fly 3D camera to that athlete's position |
| Chart / People icons | Toggle Analysis and Athletes panels |
| `?` button | Open full documentation guide |

---

## Setup

### Prerequisites
- An [ArcGIS API Key](https://developers.arcgis.com/) (free tier works)
- Python 3.x (for data processing only)

### Running Locally
```bash
git clone https://github.com/garridolecca/redbull-xalps-3d.git
cd redbull-xalps-3d
# Set ARCGIS_API_KEY in index.html
python -m http.server 8080
# Open http://localhost:8080
```

### Reprocessing Data
```bash
python process_data.py
# Reads CSVs from DATA_DIR, outputs data/race_data.json
```

---

## Tech Stack

| Component | Technology |
|---|---|
| **3D Map** | ArcGIS Maps SDK for JavaScript 4.31 (SceneView) |
| **UI Framework** | Calcite Design System 2.13.2 (dark mode) |
| **Charts** | HTML5 Canvas (wind rose, altitude profile) |
| **Markers** | Inline SVG via IconSymbol3DLayer (triangle/circle shapes) |
| **Track Lines** | LineSymbol3D with dual-layer glow effect |
| **Data Processing** | Python (csv, json, defaultdict) |
| **Data Source** | Google BigQuery via Pub/Sub (Naviter GPS telemetry) |
| **Hosting** | GitHub Pages (auto-deploy on push) |

---

## Architecture

```
index.html
├── Login Dialog (Calcite, client-side auth)
├── Welcome Dialog (brief intro)
├── Guide Page (full documentation, ? button)
├── Calcite Shell
│   ├── Header (nav bar, solo chip, panel toggles)
│   ├── Left Sidebar (permanent analysis panel)
│   │   ├── Layer Switches (tracks, markers)
│   │   ├── Thermal Stats (active/avg/max, live)
│   │   ├── Wind Rose (canvas, 16-dir polar chart, live)
│   │   └── Altitude Profile (canvas sparkline, solo mode)
│   ├── Main Area
│   │   ├── SceneView (satellite + world elevation)
│   │   │   ├── TrackLayer (3D polylines, dual-glow)
│   │   │   └── MarkerLayer (SVG icons, triangle/circle)
│   │   └── Time Footer (play, slider, speed, stats)
│   └── Athletes Panel (floating overlay, calcite-list)
└── Loading Overlay (streaming progress bar)

process_data.py
├── CSV Parser (10MB field limit, pipe/semicolon)
├── Time-Bucket Deduplicator (90s, sensor priority)
├── Thermal Extractor (VS > 1.0 + Flying only)
├── Wind Sampler (300s buckets, Naviter-only)
└── JSON Serializer (race_data.json, 18MB)
```

---

## Performance Optimizations

- **No map graphics for thermals/wind** - data shown via charts only (eliminated removeAll/addMany cycles)
- **Animation fast path** - only marker positions + time display per frame during playback
- **Binary search** for time-windowed data queries
- **Symbol cache** keyed by position + color + activity (avoids SVG regeneration)
- **requestIdleCallback** for non-critical sidebar updates
- **90-second time buckets** reduce data volume 3x
- **Streaming fetch** with download progress bar
- **Auto-skip** empty time gaps during playback

---

## License

This project is for demonstration and educational purposes. Race data is property of Red Bull Media House / Red Bull X-Alps.
