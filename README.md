# Volby PS ČR 2025 - Real-time Election Monitoring System

Real-time monitoring application for Czech Parliament elections 2025. Collects, aggregates, and visualizes election data from official sources.

## Features

- **Real-time data collection** from volby.cz every second
- **SQLite database** with time-series data aggregation
- **Web dashboard** with interactive charts and real-time updates via WebSocket
- **Multiple views**: Current Results, Timeline, Total Votes, Region Comparison, Top Candidates
- **Auto-refresh** every 10 seconds
- **Export functionality** (CSV/JSON)
- **Test data generator** for development
- **Docker support** for easy deployment

## Tech Stack

- **Backend**: Python, Flask, Flask-SocketIO, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Database**: SQLite
- **Real-time**: WebSocket (Socket.IO)
- **Deployment**: Docker, Docker Compose

## Installation

### Prerequisites

- Python 3.8+ (for manual installation)
- Docker and Docker Compose (for Docker installation)
- pip (for manual installation)

### Option 1: Docker (Recommended)

The easiest way to run the application is using Docker:

```bash
# Clone the repository
git clone https://github.com/moodixmarket/volby2025.git
cd volby2025

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

The application will be available at `http://localhost:8080`

**Docker benefits:**
- No need to install Python dependencies manually
- Isolated environment
- Easy to deploy and manage
- Automatic restart on failure
- Persistent data storage

### Option 2: Quick Start (Shell Script)

```bash
# Clone the repository
git clone https://github.com/moodixmarket/volby2025.git
cd volby2025

# Run install and start script
chmod +x install_and_run.sh
./install_and_run.sh
```

### Option 3: Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the application
./start_app.sh
```

## Usage

### Using Docker

```bash
# Start the application
docker-compose up -d

# View real-time logs
docker-compose logs -f

# Stop the application
docker-compose down

# Restart the application
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build
```

### Using Shell Scripts

1. **Start the application**:
   ```bash
   ./start_app.sh
   ```

2. **Access the web interface**:
   Open browser at `http://localhost:8080`

3. **Generate test data** (for development):
   ```bash
   python test_data_generator.py
   ```

4. **Stop the application**:
   ```bash
   ./stop_app.sh
   ```

## Project Structure

```
volby2025/
├── backend/
│   ├── data_collector.py    # XML data collection from volby.cz
│   ├── xml_parser.py         # Parse election XML data
│   ├── db_models.py         # SQLAlchemy database models
│   └── aggregator.py        # Data aggregation logic
├── webapp/
│   ├── app.py               # Flask application
│   ├── api_routes.py        # REST API endpoints
│   └── websocket.py         # WebSocket real-time updates
├── frontend/
│   ├── templates/
│   │   └── index.html       # Main HTML template
│   └── static/
│       ├── css/
│       │   └── style.css    # Styles
│       └── js/
│           └── app.js       # Frontend JavaScript
├── database/                # SQLite database (auto-created)
├── logs/                    # Application logs
├── config.py               # Configuration
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── docker-entrypoint.sh    # Docker startup script
├── .dockerignore           # Docker build exclusions
├── start_app.sh           # Start script
├── stop_app.sh            # Stop script
└── test_data_generator.py # Test data generator

```

## Features in Detail

### Current Results View
- Bar chart with party results
- Table with votes, percentages, mandates, and trends
- Real-time counting progress

### Timeline View
- Line chart showing party support over time
- Volume chart showing votes per minute
- Zoom and pan controls
- Data range selector (1h, 6h, 12h, 24h, 48h, all)

### Total Votes View
- Line chart showing absolute vote counts per party
- Statistics: total counted, average new votes/min, leading party
- Mouse controls for zoom and pan

### Region Comparison
- Compare results between multiple regions
- Interactive checkboxes for region selection
- Bar chart visualization

### Top Candidates
- List of candidates with preferential votes
- Filter by party
- Shows elected status

## Configuration

### Docker Configuration

Edit `docker-compose.yml` to customize:

```yaml
environment:
  - FLASK_HOST=0.0.0.0
  - FLASK_PORT=8080
  - COLLECTION_INTERVAL=1
ports:
  - "8080:8080"  # Change external port if needed
```

### Manual Configuration

Edit `config.py` to customize:

```python
# Flask settings
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 8080

# Database
DATABASE_NAME = 'volby2025.db'
DATABASE_PATH = 'database/'

# Data collection interval
COLLECTION_INTERVAL = 1  # seconds
```

## API Endpoints

- `GET /api/current_results?region=<code>` - Current election results
- `GET /api/time_series?region=<code>&hours=<n>` - Time series data
- `GET /api/progress?region=<code>` - Counting progress
- `GET /api/predictions?region=<code>` - Result predictions
- `GET /api/comparison?regions=<codes>` - Region comparison
- `GET /api/candidates?region=<code>&party=<code>` - Candidate list
- `GET /api/export/<format>?region=<code>` - Export data (csv/json)

## Development

### Generate Test Data

```bash
# Using Docker
docker-compose exec volby2025 python test_data_generator.py

# Without Docker
python test_data_generator.py
```

This creates realistic test data simulating election counting progress.

### Monitoring

Check application logs:

```bash
# Using Docker
docker-compose logs -f

# Without Docker
tail -f logs/webapp.log
tail -f logs/data_collector.log
```

### Development with Docker

For active development with auto-reload:

```bash
# Mount current directory and enable debug mode
docker-compose -f docker-compose.dev.yml up
```

## Deployment

### Production Deployment with Docker

1. Clone the repository on your server
2. Configure environment variables in `docker-compose.yml`
3. Run with production settings:

```bash
docker-compose up -d
```

The application includes:
- Automatic restart on failure
- Health checks
- Persistent data volumes
- Resource optimization

### Docker Image Sizes

- Base image: ~150 MB
- Final image: ~200 MB
- With data: varies based on election data volume

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Notes

- Port 8080 is used by default (port 5000 conflicts with macOS AirPlay)
- Database is stored in `database/` directory (persisted in Docker volumes)
- Logs are stored in `logs/` directory (persisted in Docker volumes)
- All times are in local timezone
- Docker containers automatically restart unless stopped manually

## Troubleshooting

### Docker Issues

**Container not accessible:**
```bash
# Check if container is running
docker-compose ps

# Check logs
docker-compose logs -f

# Restart container
docker-compose restart
```

**Port already in use:**
```bash
# Change port in docker-compose.yml
ports:
  - "8081:8080"  # Use port 8081 instead
```

**Database permissions:**
```bash
# Fix permissions
sudo chown -R $USER:$USER database/ logs/
```

## License

MIT License

## Author

Jan Růžička

## Acknowledgments

- Data source: [volby.cz](https://www.volby.cz)
- Charts: [Chart.js](https://www.chartjs.org/)
- Real-time: [Socket.IO](https://socket.io/)
- Containerization: [Docker](https://www.docker.com/)