from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from webapp.api_routes import api_bp
from webapp.websocket import setup_websocket_handlers
from backend.db_models import init_db

# Inicializace Flask aplikace
app = Flask(__name__, 
            static_folder='../frontend/static',
            template_folder='../frontend/templates')

app.config['SECRET_KEY'] = config.SECRET_KEY
CORS(app, origins=config.SOCKETIO_CORS_ALLOWED_ORIGINS)

# Inicializace SocketIO
socketio = SocketIO(app, 
                    cors_allowed_origins=config.SOCKETIO_CORS_ALLOWED_ORIGINS,
                    async_mode=config.SOCKETIO_ASYNC_MODE)

# Registrace API blueprint
app.register_blueprint(api_bp, url_prefix='/api')

# Nastavení WebSocket handlerů
setup_websocket_handlers(socketio)

@app.route('/')
def index():
    """Hlavní stránka s dashboardem"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Application is running'})

@app.errorhandler(404)
def not_found(error):
    """Handler pro 404 chyby"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler pro 500 chyby"""
    return jsonify({'error': 'Internal server error'}), 500

def run_app():
    """Spuštění aplikace"""
    import socket
    
    # Inicializace databáze
    init_db()
    
    # Najít volný port, pokud je výchozí obsazený
    port = config.FLASK_PORT
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Kontrola, zda je port volný
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result == 0:
        print(f"Port {port} is already in use, trying to find a free port...")
        # Zkusit najít volný port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        print(f"Using port {port}")
    
    print(f"\n{'='*60}")
    print(f"Starting Flask application on http://localhost:{port}")
    print(f"{'='*60}\n")
    
    # Spuštění Flask aplikace s SocketIO
    try:
        # Použít 127.0.0.1 místo 0.0.0.0 pro localhost
        socketio.run(app, 
                     host='127.0.0.1',  # Změněno na localhost
                     port=port, 
                     debug=config.FLASK_DEBUG,
                     use_reloader=False,
                     log_output=True)
    except Exception as e:
        print(f"Error starting application: {e}")
        import sys
        sys.exit(1)

if __name__ == '__main__':
    run_app()