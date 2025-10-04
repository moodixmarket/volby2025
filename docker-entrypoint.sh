#!/bin/bash
set -e

echo "Starting volby2025 application..."
echo "Host: ${FLASK_HOST:-0.0.0.0}"
echo "Port: ${FLASK_PORT:-8080}"

# Vytvoření potřebných adresářů
mkdir -p database logs

# Inicializace databáze
echo "Initializing database..."
python -c "from backend.db_models import init_db; init_db(); print('Database initialized')"

# Funkce pro ukončení všech procesů při Ctrl+C
cleanup() {
    echo -e "\n\nShutting down all services..."
    kill $COLLECTOR_PID $WEBAPP_PID 2>/dev/null
    wait $COLLECTOR_PID $WEBAPP_PID 2>/dev/null
    echo "All services stopped."
    exit 0
}

# Nastavení handleru pro SIGTERM a SIGINT
trap cleanup SIGTERM SIGINT

# Spuštění data collectoru na pozadí
echo "Starting Data Collector..."
python start_collector.py > logs/collector.log 2>&1 &
COLLECTOR_PID=$!
echo "Data Collector started (PID: $COLLECTOR_PID)"

# Počkat 3 sekundy před spuštěním webové aplikace
sleep 3

# Spuštění webové aplikace na pozadí
echo "Starting Web Application..."
python -c "
from webapp.app import app, socketio
import config

print(f'Starting Flask+SocketIO on {config.FLASK_HOST}:{config.FLASK_PORT}')
socketio.run(app, host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False, use_reloader=False, log_output=True)
" > logs/webapp.log 2>&1 &
WEBAPP_PID=$!
echo "Web Application started (PID: $WEBAPP_PID)"

# Počkat chvíli na start aplikace
sleep 2

echo ""
echo "======================================"
echo "All services are running!"
echo "======================================"
echo ""
echo "Web application: http://localhost:${FLASK_PORT:-8080}"
echo ""
echo "Logs:"
echo "  - Data Collector: logs/collector.log"
echo "  - Web Application: logs/webapp.log"
echo ""

# Čekat na ukončení procesů
wait $COLLECTOR_PID $WEBAPP_PID