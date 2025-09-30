#!/bin/bash

# Skript pro spuštění generátoru testovacích dat

echo "======================================"
echo "Test Data Generator for Volby 2025"
echo "======================================"
echo ""

# Získání cesty
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Kontrola venv
if [ ! -d "venv" ]; then
    echo "Virtual environment not found!"
    echo "Please run ./install_and_run.sh first"
    exit 1
fi

# Aktivace venv
source venv/bin/activate

if [ -z "$VIRTUAL_ENV" ]; then
    echo "Failed to activate virtual environment"
    exit 1
fi

echo "Virtual environment activated"
echo ""

# Menu
echo "Select option:"
echo "1. Quick test - Generate 50% counted data immediately"
echo "2. Full generator - Interactive mode with continuous updates"
echo "3. Reset - Clear all data and start fresh"
echo ""

read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "Running quick test..."
        python quick_test.py
        ;;
    2)
        echo "Running full generator..."
        python test_data_generator.py
        ;;
    3)
        echo "Resetting database..."
        python -c "
from test_data_generator import TestDataGenerator
from backend.db_models import init_db
init_db()
gen = TestDataGenerator()
gen.clear_database()
print('Database cleared!')
"
        ;;
    *)
        echo "Invalid choice"
        ;;
esac