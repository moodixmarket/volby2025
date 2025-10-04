import os
from pathlib import Path

# Cesty
BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / 'database' / 'volby.db'
LOG_DIR = BASE_DIR / 'logs'

# Vytvoření složky pro logy
LOG_DIR.mkdir(exist_ok=True)

# URL pro stahování dat
BASE_URL = "https://www.volby.cz/opendata/ps2025/PS2025reg"  
OPENDATA_URL = "https://www.volby.cz/opendata/ps2025"

# Hlavní soubory - tyto existují
URLS = {
    'main': "https://www.volby.cz/appdata/ps2025/odata/vysledky.xml",  # Toto funguje podle uživatele
    'kraje': f"{BASE_URL}/vysledky_kraje.xml",
    'okresy': f"{BASE_URL}/vysledky_okres.xml",
    'zahranici': f"{OPENDATA_URL}/PS2025zah/vysledky_zah.xml",
    'kandidati': f"{OPENDATA_URL}/PS2025/vysledky_kandid.xml",
}

# Pro jednotlivé okresy použijeme jiný formát
# Format: vysledky_okres_XXXX.xml kde XXXX je kód okresu
OKRES_CODES = [
    '1100', '2101', '2102', '2103', '2104', '2105', '2106', '2107', '2108', '2109',
    '210A', '210B', '3101', '3102', '3103', '3104', '3105', '3106', '3107',
    '3201', '3202', '3203', '3204', '3205', '3206', '3207', '3208', '3209', '320A', '320B',
    '4101', '4102', '4103', '4104', '4105', '4106', '4107', '4201', '4202', '4203',
    '4204', '4205', '4206', '4207', '5101', '5102', '5103', '5104', '5201', '5202',
    '5203', '5301', '5302', '5303', '5304', '6101', '6102', '6103', '6104', '6105',
    '6106', '6107', '6201', '6202', '6203', '6204', '6205', '6206', '6207', '6301',
    '6302', '6303', '6304', '6305', '6401', '6402', '6403', '6404', '6405', '6406',
    '7101', '7102', '7103', '7104', '7105', '7201', '7202', '7203', '8101', '8102',
    '8103', '8104', '8105', '8106', '8107'
]

# Nastavení stahování
DOWNLOAD_INTERVAL = 5  # sekund mezi stahováním - zvýšeno pro menší zátěž serveru
MAX_BATCH_NUMBER = 9999  # maximální číslo dávky
BATCH_CHECK_INTERVAL = 60  # sekund mezi kontrolami nových dávek

# Nastavení databáze
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
POOL_SIZE = 20
MAX_OVERFLOW = 40

# Nastavení webové aplikace
FLASK_HOST = '0.0.0.0'
FLASK_PORT = int(os.getenv('FLASK_PORT', 8080))  # Změněno na port 8080
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY', 'volby-2025-secret-key-change-in-production')

# WebSocket nastavení
SOCKETIO_ASYNC_MODE = 'eventlet'
SOCKETIO_CORS_ALLOWED_ORIGINS = "*"

# Agregace dat
AGGREGATION_INTERVAL = 60  # sekund - agregace po minutách
AUTO_REFRESH_INTERVAL = 10  # sekund - automatická aktualizace frontendu

# Logování
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'