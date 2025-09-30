#!/bin/bash

# Diagnostika s aktivovaným venv

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Barvy
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "Diagnostics with Virtual Environment"
echo "======================================"
echo ""

# Kontrola venv
if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found!${NC}"
    echo "Run: python3 -m venv venv"
    exit 1
fi

# Aktivace venv
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Failed to activate virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Spuštění Python diagnostiky
python diagnose.py