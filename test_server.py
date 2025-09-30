#!/usr/bin/env python3
"""
Jednoduchý test server pro ověření, že Flask funguje
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return """
    <html>
    <head><title>Test Server</title></head>
    <body>
        <h1>Flask Test Server is Running!</h1>
        <p>If you can see this, Flask is working correctly.</p>
        <p><a href="/test">Test JSON endpoint</a></p>
    </body>
    </html>
    """

@app.route('/test')
def test():
    return jsonify({
        'status': 'ok',
        'message': 'Flask is working correctly',
        'endpoints': [
            '/',
            '/test'
        ]
    })

if __name__ == '__main__':
    import socket
    
    # Najít volný port
    port = 8080
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    
    if result == 0:
        print(f"Port {port} is in use, finding a free port...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
    
    print(f"Starting test server on http://localhost:{port}")
    print("Press Ctrl+C to stop")
    
    app.run(host='127.0.0.1', port=port, debug=True)