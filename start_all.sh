#!/bin/bash

# Skript pro spuštění celé aplikace s virtuálním prostředím

echo "======================================"
echo "Volby PS ČR 2025 - Starting All Services"
echo "======================================"

# Získání aktuální cesty
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Kontrola Python instalace
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Python version: $(python3 --version)"

# Vytvoření virtuálního prostředí pokud neexistuje
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        echo "Try installing python3-venv: sudo apt-get install python3-venv (on Ubuntu/Debian)"
        exit 1
    fi
    echo "Virtual environment created successfully"
else
    echo "Virtual environment already exists"
fi

# Aktivace virtuálního prostředí
echo "Activating virtual environment..."
source venv/bin/activate

# Kontrola, že venv je aktivní
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

echo "Virtual environment activated: $VIRTUAL_ENV"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip -q

# Kontrola a instalace závislostí
echo "Checking Python dependencies..."
pip show flask > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
    echo "Dependencies installed successfully"
else
    # Kontrola, zda jsou všechny závislosti aktuální
    echo "Verifying all dependencies are up to date..."
    pip install -q -r requirements.txt --upgrade
fi

# Vytvoření složky pro logy, pokud neexistuje
mkdir -p logs

# Vytvoření databázové složky
mkdir -p database

# Funkce pro ukončení všech procesů při Ctrl+C
cleanup() {
    echo -e "\n\nShutting down all services..."
    kill $COLLECTOR_PID $WEBAPP_PID 2>/dev/null
    wait $COLLECTOR_PID $WEBAPP_PID 2>/dev/null
    deactivate 2>/dev/null
    echo "All services stopped."
    exit 0
}

# Nastavení handleru pro Ctrl+C
trap cleanup SIGINT SIGTERM

# Spuštění data collectoru na pozadí
echo ""
echo "Starting Data Collector..."
python start_collector.py > logs/collector.log 2>&1 &
COLLECTOR_PID=$!
echo "Data Collector started (PID: $COLLECTOR_PID)"

# Počkat 3 sekundy před spuštěním webové aplikace
sleep 3

# Spuštění webové aplikace na pozadí
echo "Starting Web Application..."
python start_webapp.py > logs/webapp.log 2>&1 &
WEBAPP_PID=$!
echo "Web Application started (PID: $WEBAPP_PID)"

# Počkat chvíli na start aplikace
sleep 2

# Kontrola, zda procesy běží
if ps -p $COLLECTOR_PID > /dev/null; then
    echo "✓ Data Collector is running"
else
    echo "✗ Data Collector failed to start - check logs/collector.log"
fi

if ps -p $WEBAPP_PID > /dev/null; then
    echo "✓ Web Application is running"
else
    echo "✗ Web Application failed to start - check logs/webapp.log"
fi

echo ""
echo "======================================"
echo "All services are running!"
echo "======================================"
echo ""
echo "Web application: http://localhost:8080"
echo ""
echo "Logs:"
echo "  - Data Collector: logs/collector.log"
echo "  - Web Application: logs/webapp.log"
echo ""
echo "To monitor logs in real-time:"
echo "  tail -f logs/collector.log"
echo "  tail -f logs/webapp.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Čekat na ukončení procesů
wait $COLLECTOR_PID $WEBAPP_PID