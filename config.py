import os
from pathlib import Path

# Cesty
BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / 'database' / 'volby.db'
LOG_DIR = BASE_DIR / 'logs'

# Vytvoření složky pro logy
LOG_DIR.mkdir(exist_ok=True)

# URL pro stahování dat
BASE_URL = "https://www.volby.cz/appdata/ps2025/odata"
URLS = {
    'main': f"{BASE_URL}/vysledky.xml",
    'krajmesta': f"{BASE_URL}/vysledky_krajmesta.xml",
    'zahranici': f"{BASE_URL}/vysledky_zahranici.xml",
    'kandidati': f"{BASE_URL}/vysledky_kandid.xml",
}

# Okresy - kódy okresů ČR
OKRES_CODES = [
    'CZ0100', 'CZ0201', 'CZ0202', 'CZ0203', 'CZ0204', 'CZ0205', 'CZ0206', 'CZ0207', 'CZ0208', 'CZ0209',
    'CZ020A', 'CZ020B', 'CZ020C', 'CZ0311', 'CZ0312', 'CZ0313', 'CZ0314', 'CZ0315', 'CZ0316', 'CZ0317',
    'CZ0321', 'CZ0322', 'CZ0323', 'CZ0324', 'CZ0325', 'CZ0326', 'CZ0327', 'CZ0411', 'CZ0412', 'CZ0413',
    'CZ0421', 'CZ0422', 'CZ0423', 'CZ0424', 'CZ0425', 'CZ0426', 'CZ0427', 'CZ0511', 'CZ0512', 'CZ0513',
    'CZ0514', 'CZ0521', 'CZ0522', 'CZ0523', 'CZ0524', 'CZ0525', 'CZ0531', 'CZ0532', 'CZ0533', 'CZ0534',
    'CZ0611', 'CZ0612', 'CZ0613', 'CZ0614', 'CZ0615', 'CZ0621', 'CZ0622', 'CZ0623', 'CZ0624', 'CZ0625',
    'CZ0626', 'CZ0627', 'CZ0631', 'CZ0632', 'CZ0633', 'CZ0634', 'CZ0635', 'CZ0641', 'CZ0642', 'CZ0643',
    'CZ0644', 'CZ0645', 'CZ0646', 'CZ0647', 'CZ0711', 'CZ0712', 'CZ0713', 'CZ0714', 'CZ0715', 'CZ0721',
    'CZ0722', 'CZ0723', 'CZ0724', 'CZ0801', 'CZ0802', 'CZ0803', 'CZ0804', 'CZ0805', 'CZ0806'
]

# Nastavení stahování
DOWNLOAD_INTERVAL = 1  # sekund mezi stahováním
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