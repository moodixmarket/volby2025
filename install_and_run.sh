#!/bin/bash

# Kompletní instalační a spouštěcí skript

echo "======================================"
echo "Volby PS ČR 2025 - Complete Setup & Run"
echo "======================================"

# Získání aktuální cesty
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Barvy pro výpis
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $(python3 --version)${NC}"

# Port 5000 je obsazený systémovým procesem (AirPlay na macOS)
echo -e "\n${YELLOW}Step 2: Port 5000 is used by system (AirPlay), we'll use port 8080${NC}"

# Vytvoření virtuálního prostředí
echo -e "\n${YELLOW}Step 3: Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to create virtual environment${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Aktivace virtuálního prostředí
echo -e "\n${YELLOW}Step 4: Activating virtual environment...${NC}"
source venv/bin/activate

if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Error: Failed to activate virtual environment${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo -e "\n${YELLOW}Step 5: Upgrading pip...${NC}"
pip install --upgrade pip --quiet
echo -e "${GREEN}✓ Pip upgraded${NC}"

# Instalace všech závislostí
echo -e "\n${YELLOW}Step 6: Installing all dependencies...${NC}"
echo "This may take a minute..."

pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✓ All dependencies installed${NC}"

# Ověření instalace
echo -e "\n${YELLOW}Step 7: Verifying installation...${NC}"
python -c "
import sys
try:
    import flask
    import flask_cors
    import flask_socketio
    import sqlalchemy
    import requests
    import lxml
    print('✓ All modules imported successfully')
    sys.exit(0)
except ImportError as e:
    print(f'✗ Import failed: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo -e "${RED}Some modules failed to import${NC}"
    exit 1
fi

# Vytvoření složek
echo -e "\n${YELLOW}Step 8: Creating directories...${NC}"
mkdir -p logs database
echo -e "${GREEN}✓ Directories created${NC}"

# Funkce pro ukončení
cleanup() {
    echo -e "\n\n${YELLOW}Shutting down all services...${NC}"
    kill $COLLECTOR_PID $WEBAPP_PID 2>/dev/null
    wait $COLLECTOR_PID $WEBAPP_PID 2>/dev/null
    deactivate 2>/dev/null
    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Spuštění služeb
echo -e "\n${YELLOW}Step 9: Starting services...${NC}"
echo ""

# Data collector
echo "Starting Data Collector..."
python start_collector.py > logs/collector.log 2>&1 &
COLLECTOR_PID=$!
echo -e "${GREEN}✓ Data Collector started (PID: $COLLECTOR_PID)${NC}"

sleep 3

# Web aplikace
echo "Starting Web Application..."
python start_webapp.py > logs/webapp.log 2>&1 &
WEBAPP_PID=$!
echo -e "${GREEN}✓ Web Application started (PID: $WEBAPP_PID)${NC}"

sleep 3

# Kontrola běhu
echo -e "\n${YELLOW}Step 10: Checking services...${NC}"

if ps -p $COLLECTOR_PID > /dev/null; then
    echo -e "${GREEN}✓ Data Collector is running${NC}"
else
    echo -e "${RED}✗ Data Collector failed to start${NC}"
    echo "Check logs/collector.log for errors"
fi

if ps -p $WEBAPP_PID > /dev/null; then
    echo -e "${GREEN}✓ Web Application is running${NC}"
    
    # Test HTTP spojení
    sleep 2
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080 | grep -q "200\|302"; then
        echo -e "${GREEN}✓ Web server is responding${NC}"
    else
        echo -e "${YELLOW}⚠ Web server may still be starting up${NC}"
    fi
else
    echo -e "${RED}✗ Web Application failed to start${NC}"
    echo "Check logs/webapp.log for errors"
fi

echo ""
echo "======================================"
echo -e "${GREEN}Setup complete! Services running!${NC}"
echo "======================================"
echo ""
echo -e "${GREEN}➜ Open your browser at: http://localhost:8080${NC}"
echo ""
echo "Logs:"
echo "  • logs/collector.log - Data collection logs"
echo "  • logs/webapp.log - Web application logs"
echo ""
echo "Monitor logs: tail -f logs/*.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Otevřít prohlížeč na macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    sleep 2
    open http://localhost:8080 2>/dev/null
fi

# Čekat na ukončení
wait $COLLECTOR_PID $WEBAPP_PID