# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Real-time monitoring application for Czech Parliament elections 2025. The system collects election data from volby.cz, stores it in SQLite database, and provides a web dashboard with real-time updates via WebSocket.

## Tech Stack

- **Backend**: Python, Flask, Flask-SocketIO, SQLAlchemy
- **Frontend**: HTML5, JavaScript, Chart.js
- **Database**: SQLite (file-based, stored in `database/` directory)
- **Real-time**: WebSocket via Socket.IO with eventlet async mode
- **Deployment**: Docker, Docker Compose

## Development Commands

### Start Application

**Docker (recommended for deployment):**
```bash
docker-compose up -d              # Start in detached mode
docker-compose logs -f            # View real-time logs
docker-compose down               # Stop application
docker-compose up -d --build      # Rebuild after code changes
```

**Local Development:**
```bash
./start_all.sh                    # Creates venv, installs deps, starts both services
python start_collector.py         # Start data collector only
python start_webapp.py            # Start web app only
```

### Testing & Data Generation

```bash
# Generate realistic test data for development
python test_data_generator.py

# Run diagnostics
python diagnose.py

# Quick server test
python test_server.py
```

### Database

- Database file: `database/volby.db`
- Auto-created on first run via SQLAlchemy
- No migrations system - schema changes require manual handling or database recreation

### Logs

- Web app: `logs/webapp.log`
- Data collector: `logs/collector.log`
- Both services log to console and files

## Architecture

### Three-Tier Structure

1. **Data Collection Layer** (`backend/data_collector.py`)
   - Polls volby.cz XML endpoints every 1-5 seconds
   - Stores raw XML in `RawData` table
   - Runs independently from web app
   - URLs configured in `config.py` (main, kraje, okresy, zahranici, kandidati)

2. **Data Processing Layer** (`backend/aggregator.py`, `backend/xml_parser.py`)
   - Parses XML from multiple sources
   - Aggregates results by region/party
   - Stores in normalized tables (Party, Region, Result, VoteProgress, Candidate, AggregatedResult)
   - Handles Czech character encoding (UTF-8)

3. **Web Application Layer** (`webapp/`)
   - Flask app serves dashboard at `http://localhost:8080`
   - REST API endpoints in `api_routes.py`
   - WebSocket real-time updates in `websocket.py`
   - Frontend in `frontend/` directory (templates, static)

### Database Models (`backend/db_models.py`)

- **RawData**: Stores raw XML downloads with timestamp
- **Party**: Political parties with codes and names
- **Region**: Hierarchical regions (stat, kraj, okres, obec)
- **Result**: Time-series election results per party/region
- **VoteProgress**: Counting progress tracking
- **AggregatedResult**: Minute-level aggregated data
- **Candidate**: Individual candidates with preferential votes

### Key Architectural Notes

- Data collector and web app run as separate processes
- Both processes share the same SQLite database
- WebSocket broadcasts updates to connected clients every 10 seconds
- Database uses connection pooling (POOL_SIZE=20, MAX_OVERFLOW=40)
- All XML data must be handled with UTF-8 encoding

## Configuration (`config.py`)

Important settings:
- `FLASK_PORT`: 8080 (avoiding macOS AirPlay port 5000 conflict)
- `DATABASE_PATH`: `database/volby.db`
- `DOWNLOAD_INTERVAL`: 5 seconds between data collection
- `AGGREGATION_INTERVAL`: 60 seconds for minute-level aggregation
- `AUTO_REFRESH_INTERVAL`: 10 seconds for frontend updates

Environment variables (Docker):
- `FLASK_HOST`, `FLASK_PORT`, `COLLECTION_INTERVAL`

## API Endpoints

All endpoints in `webapp/api_routes.py`:

- `GET /api/current_results?region=<code>` - Current results
- `GET /api/time_series?region=<code>&hours=<n>` - Historical data
- `GET /api/progress?region=<code>` - Counting progress
- `GET /api/predictions?region=<code>` - Predictions
- `GET /api/comparison?regions=<codes>` - Multi-region comparison
- `GET /api/candidates?region=<code>&party=<code>` - Candidate list
- `GET /api/export/<format>?region=<code>` - Export (csv/json)

## Common Development Patterns

### Adding New XML Sources

1. Add URL to `config.URLS`
2. Update `data_collector.py` to fetch new source
3. Extend `xml_parser.py` to parse new XML structure
4. Update database models if needed

### Database Changes

- Modify models in `db_models.py`
- Consider: SQLite doesn't support all ALTER TABLE operations
- For major changes: backup data, drop DB, recreate with new schema

### Frontend Updates

- HTML: `frontend/templates/index.html`
- CSS: `frontend/static/css/style.css`
- JS: `frontend/static/js/app.js`
- Changes require browser refresh (no hot reload)

## Docker Notes

- Container auto-restarts unless manually stopped
- Database and logs persisted via volumes
- Health check on port 8080 every 30s
- Start period: 40s before health checks begin

## Character Encoding

Critical: All XML data sources use UTF-8. Always:
- Set `response.encoding = 'utf-8'` when fetching XML
- Use UTF-8 for database text fields
- Ensure proper Czech character handling (ě, š, č, ř, ž, ý, á, í, é, ú, ů, ň, ť, ď)

## Entry Points

- `start_collector.py`: Launches data collector
- `start_webapp.py`: Launches Flask + SocketIO app
- `start_all.sh`: Launches both with venv management
- `docker-entrypoint.sh`: Docker container startup
