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

## Tech Stack

- **Backend**: Python, Flask, Flask-SocketIO, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **Database**: SQLite
- **Real-time**: WebSocket (Socket.IO)

## Installation

### Prerequisites

- Python 3.8+
- pip

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/volby2025.git
cd volby2025

# Run install and start script
chmod +x install_and_run.sh
./install_and_run.sh
```

### Manual Installation

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
python test_data_generator.py
```

This creates realistic test data simulating election counting progress.

### Monitoring

Check application logs:
```bash
tail -f logs/webapp.log
tail -f logs/data_collector.log
```

### Stop the Application

```bash
./stop_app.sh
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Notes

- Port 8080 is used by default (port 5000 conflicts with macOS AirPlay)
- Database is stored in `database/` directory
- Logs are stored in `logs/` directory
- All times are in local timezone

## License

MIT License

## Author

Jan Růžička

## Acknowledgments

- Data source: [volby.cz](https://www.volby.cz)
- Charts: [Chart.js](https://www.chartjs.org/)
- Real-time: [Socket.IO](https://socket.io/)