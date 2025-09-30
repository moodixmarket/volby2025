#!/usr/bin/env python3
"""
Diagnostický skript pro ověření problémů s aplikací
"""

import socket
import subprocess
import sys
import os

def check_port(port):
    """Kontrola, zda je port volný"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def check_process_on_port(port):
    """Najde proces běžící na daném portu (Mac/Linux)"""
    try:
        result = subprocess.run(['lsof', '-i', f':{port}'], 
                              capture_output=True, text=True)
        if result.stdout:
            print(f"Process on port {port}:")
            print(result.stdout)
            return True
    except:
        pass
    return False

def kill_process_on_port(port):
    """Zabije proces na daném portu"""
    try:
        result = subprocess.run(['lsof', '-t', '-i', f':{port}'], 
                              capture_output=True, text=True)
        if result.stdout:
            pid = result.stdout.strip()
            print(f"Killing process {pid} on port {port}")
            subprocess.run(['kill', '-9', pid])
            return True
    except:
        pass
    return False

def main():
    print("=" * 60)
    print("Diagnostika Volby 2025 Application")
    print("=" * 60)
    print()
    
    # Kontrola portů
    ports_to_check = [5000, 8080, 8081, 8082]
    
    print("Checking ports...")
    for port in ports_to_check:
        if check_port(port):
            print(f"❌ Port {port} is IN USE")
            check_process_on_port(port)
        else:
            print(f"✅ Port {port} is FREE")
    
    print()
    
    # Kontrola Python modulů
    print("Checking Python modules...")
    modules = ['flask', 'flask_cors', 'flask_socketio', 'sqlalchemy', 'requests', 'lxml']
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module} is installed")
        except ImportError:
            print(f"❌ {module} is NOT installed")
    
    print()
    
    # Kontrola souborů
    print("Checking files...")
    files = [
        'webapp/app.py',
        'backend/data_collector.py',
        'config.py',
        'requirements.txt'
    ]
    
    for file in files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} NOT found")
    
    print()
    
    # Nabídka akcí
    print("Options:")
    print("1. Kill all processes on ports 5000 and 8080")
    print("2. Start test server")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ")
    
    if choice == '1':
        for port in [5000, 8080]:
            if kill_process_on_port(port):
                print(f"Killed process on port {port}")
        print("Done. You can now run start_all.sh")
    elif choice == '2':
        print("Starting test server...")
        subprocess.run([sys.executable, 'test_server.py'])

if __name__ == "__main__":
    main()