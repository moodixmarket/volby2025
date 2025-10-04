#!/bin/bash
set -e

echo "Starting volby2025 application..."
echo "Host: ${FLASK_HOST:-0.0.0.0}"
echo "Port: ${FLASK_PORT:-8080}"

# Vytvoření potřebných adresářů
mkdir -p database logs

# Spuštění aplikace
exec python -c "
from webapp.app import app
import os

host = os.getenv('FLASK_HOST', '0.0.0.0')
port = int(os.getenv('FLASK_PORT', 8080))

print(f'Starting Flask on {host}:{port}')
app.run(host=host, port=port, debug=False)
"