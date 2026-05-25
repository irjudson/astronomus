# Astronomus

> Intelligent observing session planner for astrophotography with Seestar S50 integration

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)

---

## What is Astronomus?

Astronomus is a comprehensive observing session planning tool that helps astrophotographers maximize their imaging time by intelligently scheduling deep sky objects throughout the night. The application accounts for astronomical phenomena, weather conditions, and equipment limitations to create optimal observation plans.

**Perfect for:**
- 🔭 Seestar S50 telescope users
- 🌌 Astrophotography enthusiasts
- 📊 Data-driven session planning
- 🌐 Any location worldwide

<video src="https://github.com/user-attachments/assets/c7d2a73b-c59c-4d33-b3f8-50da1b46fa11" autoplay loop muted playsinline width="100%"></video>

---

## Key Features

### ✅ Implemented

**Smart Scheduling**
- Greedy algorithm with urgency-based lookahead optimizes target selection
- Field rotation calculation for alt-az mounts
- Per-azimuth local horizon profile with linear interpolation
- Satellite avoidance: blocked-interval scheduling using Celestrak visual TLEs
- Planet/moon wishlist items scheduled as real time-blocks (Meeus magnitudes, ring tilt)
- Comet targets in plan via MPC ephemeris; "visible comets tonight" card in Tonight view
- Automated daily plan generation at noon with Celery Beat

**Unmanned Capture Automation**
- Auto-execute at dusk — Celery Beat computes astronomical twilight, queues plan at exact time
- Scope connectivity retries — TCP-pings S50 every 5 min, up to 6 attempts
- Weather watchdog — aborts session if rain, excess wind, or high humidity detected
- Session webhooks — scope unreachable, session started, completed/aborted notifications
- Automation settings tab — all thresholds configurable in UI

**Comprehensive Catalog**
- **12,400+ objects** from OpenNGC, Caldwell (109), Arp Atlas (50), Sharpless HII (50)
- User-defined custom targets with CRUD API, image thumbnails, and "My Targets" tab
- Advanced filtering by type, magnitude, constellation
- Score-based sorting, visible-tonight filter, nearby-objects proximity search

**Weather Integration**
- 7Timer astronomical seeing and transparency forecasts
- Local Ambient Weather WS-2902 station (temp, humidity, wind, dew point)
- Open-Meteo **7-day daily forecast** with color-coded astronomy score strip
- Composite weather scoring integrated into target selection

**Seestar S50 Integration**
- Direct WiFi plan upload via `set_plan` API — **"Send to Scope"** button in Plan view
- MJPEG live preview stream (`/api/telescope/preview/stream`)
- Telescope-driven horizon scan (brightness-ratio sky/terrain detection)
- Full telescope control: goto, capture, focus, gain, dew heater, polar alignment
- Optimized for 50mm f/5 optics (1.27° × 0.71° FOV)

**Live Session Tracking**
- Live now-marker advances in real time during active session
- NowPlayingPanel: current/next target, frame progress bar, auto-advance on completion
- "Done →" button to skip to next target; extend target duration inline

**GPU Processing**
- CUDA-accelerated FITS stacking with CuPy
- Sigma-clipped mean stacking for outlier rejection
- Auto-stretch matching Seestar native output
- NVIDIA MPS for efficient GPU sharing

**Vue 3 SPA**
- Tonight / Sky / Plan / Observe / Archive navigation
- Interactive timeline drag-editing with real-time conflict detection
- Wishlist, saved plans, gap-filling optimizer
- Toast notifications, settings modal with Horizon and Automation tabs

### 📋 Next Up

**Post-Capture Processing UI**
- Archive tab backend is functional; file ingest, job queue UI, and batch export in progress

**Unmanned Capture Reliability**
- Manual "run now" trigger, dry-run validation, webhook delivery visibility

[See full roadmap →](docs/planning/ROADMAP.md)

---

## Quick Start

### Docker (Recommended)

```bash
# Start all services
docker compose up -d

# Access the application
open http://localhost:9247
```

**That's it!** The default configuration works out of the box for testing.

[Full quick start guide →](QUICK_START.md)

### Native Development

```bash
# Setup
git clone https://github.com/irjudson/astronomus.git
cd astronomus/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 9247 --reload
```

[Development guide →](docs/development/DEVELOPMENT.md)

---

## Seestar S50 Authentication Setup

To use Seestar S50 telescope control features, you need the RSA private key for authentication with firmware 6.45+.

### Automatic Key Extraction

Run the extraction script:

```bash
cd backend
./scripts/extract_seestar_key.sh
```

The script will:
1. Look for the Seestar APK in `/tmp/`
2. Extract the embedded RSA private key
3. Save it to `backend/secrets/seestar_private_key.pem`

### Manual Key Provision

If you already have the key, create the file manually:

```bash
mkdir -p backend/secrets
# Paste your PEM key into:
nano backend/secrets/seestar_private_key.pem
chmod 600 backend/secrets/seestar_private_key.pem
```

### Getting Help

If you need assistance obtaining the key:
- Open an issue: [GitHub Issues](https://github.com/irjudson/astronomus/issues)
- Contact the maintainer for instructions

**Note:** The key is extracted from the official Seestar app and is required for the authentication protocol used by firmware 6.45+. This is the same key used by the official app.

---

## Documentation

### For Users

- **[Quick Start](QUICK_START.md)** - Get started in 5 minutes
- **[User Guide](docs/user-guides/USAGE.md)** - How to use the planner
- **[API Documentation](docs/user-guides/API_USAGE.md)** - API endpoints and examples
- **[Seestar Integration](docs/seestar/SEESTAR_INTEGRATION.md)** - Using with Seestar S50
- **[Daily Planning](docs/planning/DAILY_PLANNING.md)** - Automatic plan generation

### For Developers

- **[Architecture](docs/architecture/ARCHITECTURE.md)** - System design and components
- **[Development Setup](docs/development/DEVELOPMENT.md)** - Native installation guide
- **[Testing Guide](docs/development/TESTING_GUIDE.md)** - Running and writing tests
- **[Processing Design](docs/architecture/PROCESSING_DESIGN.md)** - Image processing pipeline

### For Operators

- **[Docker Deployment](docs/development/DOCKER_SETUP.md)** - Production deployment
- **[Configuration Reference](docs/CONFIGURATION.md)** - All environment variables
- **[GPU Configuration](docs/planning/GPU_MPS_CONFIG.md)** - NVIDIA MPS setup

[Complete documentation index →](docs/INDEX.md)

---

## Architecture

Everything runs in a **single Docker container** (`astronomus`, port 9247). PostgreSQL, Redis, Celery workers, and the FastAPI web server are all co-located processes within that container.

```
┌──────────────────────────────────────────────────────────────┐
│  Docker container: astronomus  (port 9247)                   │
│                                                              │
│  Vue 3 SPA ──HTTP──▶ FastAPI / Uvicorn                      │
│                        Planner · Catalog · Weather ·         │
│                        Telescope · Processing · Export       │
│                               │                              │
│          ┌────────────────────┼───────────────────┐          │
│          ▼                    ▼                   ▼           │
│    PostgreSQL 14          Redis 7            Celery           │
│    (data store)       (task broker)    Worker + Beat         │
│                                        daily plan gen,       │
│                                        dusk auto-execute,    │
│                                        weather watchdog      │
└─────────────────────────────┬────────────────────────────────┘
                              │
       ┌──────────────────────┼─────────────────────┐
       ▼                      ▼                      ▼
 Seestar S50             wx-service            Internet APIs
 TCP :4700            (shared-infra net)    Open-Meteo · 7Timer
 WiFi / LAN           Ambient WS-2902       Celestrak TLEs
                       local weather         SkyView images
```

[Detailed architecture →](docs/architecture/ARCHITECTURE.md)

---

## Tech Stack

**Backend**
- Python 3.11+
- FastAPI for REST API
- SQLAlchemy for ORM
- Alembic for migrations
- Celery for background tasks

**Database**
- PostgreSQL for data persistence
- Redis for message broker

**Processing**
- CuPy for GPU acceleration (CUDA 12.8+)
- NumPy for CPU fallback
- Astropy for FITS file handling
- Skyfield for astronomical calculations

**Frontend**
- Vue 3 + Vite + Pinia + Vue Router
- Tailwind CSS for styling

**Deployment**
- Docker and Docker Compose
- NVIDIA Container Toolkit for GPU
- Celery Beat for scheduling

---

## Default Configuration

**Location:** Three Forks, Montana
- Latitude: 45.9183°N
- Longitude: 111.5433°W
- Elevation: 1234m (4049 ft)
- Timezone: America/Denver

**Planning:**
- Min altitude: 30°
- Max altitude: 70° (to avoid high field rotation)
- Setup time: 30 minutes
- Planning mode: Balanced

**Telescope:** Seestar S50
- Aperture: 50mm
- Focal length: 50mm (f/5)
- FOV: 1.27° × 0.71°
- Max exposure: 10 seconds

[Configuration guide →](docs/CONFIGURATION.md)

---

## Key Algorithms

### Field Rotation Calculation
For alt-az mounts, field rotation rate (degrees/minute):

```
rate = 15 × cos(latitude) / cos(altitude) × |sin(azimuth)|
```

The scheduler:
- Prefers 45-65° altitude range (optimal)
- Avoids zenith during meridian passage
- Scores targets based on rotation rate

### Target Scoring
Composite score (0-1) based on weighted components:

| Component | Weight | Factors |
|-----------|--------|---------|
| Visibility | 40% | Altitude, duration, field rotation |
| Weather | 30% | Cloud cover, humidity, wind, seeing |
| Object Quality | 30% | Brightness, size match to FOV |

### Urgency-Based Scheduling
Targets setting within the lookahead window (30 minutes) receive priority bonus to avoid missing time-sensitive objects.

---

## API Endpoints

**Planning:**
- `POST /api/plan` - Generate observing plan
- `GET /api/plans` - List saved plans
- `GET /api/catalog/search` - Search catalog (paginated, scored)
- `GET /api/targets` - List DSO targets
- `GET /api/targets/{catalog_id}` - Get target details
- `GET /api/catalog/stats` - Catalog statistics
- `GET /api/solar-system/objects` - All solar system bodies with current altitude

**Telescope:**
- `POST /api/telescope/connect` - Connect to Seestar S50
- `GET /api/telescope/status` - Device state
- `POST /api/telescope/execute` - Start plan execution
- `POST /api/telescope/abort` - Abort session
- `GET /api/telescope/preview/stream` - MJPEG live preview stream

**Weather:**
- `GET /api/astronomy/weather/astronomy` - Astronomical seeing + transparency (7Timer)
- `GET /api/astronomy/weather/local` - Current local station reading (Ambient WS-2902)
- `GET /api/astronomy/weather/multiday` - 7-day daily forecast (Open-Meteo)

**Processing:**
- `POST /api/processing/auto` - Auto-process FITS file
- `POST /api/processing/stack-and-stretch` - Stack and stretch FITS
- `GET /api/processing/jobs/{job_id}` - Job status
- `GET /api/processing/browse` - Browse FITS file tree

**System:**
- `GET /api/health` - Health check
- `GET /api/docs` - OpenAPI documentation (Swagger UI)

[Complete API documentation →](http://localhost:9247/api/docs)

---

## Requirements

**Minimum:**
- Python 3.11+
- Docker 20.10+ and Docker Compose 2.0+ (Docker installation)
- OR PostgreSQL 14+ and Redis 6+ (Native installation)

**Optional:**
- NVIDIA GPU with CUDA 12.8+ for GPU-accelerated processing
- OpenWeatherMap API key (free tier) for weather forecasts

**OS Support:**
- Linux (tested on Ubuntu 22.04+)
- macOS (tested on 12.0+)
- Windows via WSL2

---

## Testing

```bash
# Start services
docker-compose up -d

# Run test suite
docker exec astronomus pytest

# Run with coverage
docker exec astronomus pytest --cov=app

# Run specific test
docker exec astronomus pytest tests/test_planner_service.py
```

**Test Coverage:** 726 tests passing (unit + integration), 49 skipped (hardware)

[Testing guide →](docs/development/TESTING_GUIDE.md)

---

## Contributing

Contributions are welcome! Areas of interest:

**Features:**
- Mosaic planning (multi-panel FOV, overlap calculator)
- Advanced image processing algorithms
- Mobile PWA / offline favorites
- Interactive sky map overlay

**Improvements:**
- Enhanced scheduling algorithms
- Additional export formats
- UI/UX enhancements
- Performance optimizations

**Documentation:**
- Additional examples and tutorials
- Translation to other languages
- Video guides

**Process:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow [development guidelines](docs/development/DEVELOPMENT.md)
4. Run tests and ensure they pass (`pytest`)
5. Submit a pull request

[Development guide →](docs/development/DEVELOPMENT.md)

---

## License

MIT License - See [LICENSE](LICENSE) for details

**Free for:**
- Personal use
- Commercial use
- Modification
- Distribution

**Requirements:**
- Include copyright notice
- Include license text

---

## Acknowledgments

**Software:**
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Skyfield](https://rhodesmill.org/skyfield/) - Astronomical calculations
- [Astropy](https://www.astropy.org/) - Astronomy tools for Python
- [CuPy](https://cupy.dev/) - GPU-accelerated computing

**Data Sources:**
- [OpenNGC](https://github.com/mattiaverga/OpenNGC) - Open NGC/IC catalog (CC-BY-SA-4.0)
- [OpenWeatherMap](https://openweathermap.org/) - Weather forecasts
- [7Timer](http://www.7timer.info/) - Astronomical seeing forecasts

**Community:**
- [Seestar S50 Users](https://www.reddit.com/r/seestar/) - Telescope community
- [smart-underworld/seestar_alp](https://github.com/smart-underworld/seestar_alp) - Seestar automation tools

---

## Support

**Documentation:** [docs/INDEX.md](docs/INDEX.md)

**Issues:** [GitHub Issues](https://github.com/irjudson/astronomus/issues)

**Discussions:** [GitHub Discussions](https://github.com/irjudson/astronomus/discussions) (for questions)

---

**Made for stargazers, by stargazers** 🔭✨
