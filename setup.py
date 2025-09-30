#!/usr/bin/env python3
"""
Setup skript pro první instalaci a konfiguraci projektu
"""

import os
import sys
import subprocess
import platform

def print_header():
    """Vytiskne hlavičku"""
    print("=" * 60)
    print("Volby PS ČR 2025 - Setup & Installation")
    print("=" * 60)
    print()

def check_python_version():
    """Kontrola verze Pythonu"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"Error: Python 3.8 or higher is required (you have {version.major}.{version.minor})")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")

def create_venv():
    """Vytvoření virtuálního prostředí"""
    print("\nCreating virtual environment...")
    
    if os.path.exists("venv"):
        print("Virtual environment already exists")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✓ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError:
        print("Error: Failed to create virtual environment")
        print("Try installing python3-venv:")
        if platform.system() == "Linux":
            print("  sudo apt-get install python3-venv  # Ubuntu/Debian")
            print("  sudo yum install python3-venv      # CentOS/RHEL")
        return False

def get_pip_command():
    """Získá správný příkaz pro pip v závislosti na OS"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "pip.exe")
    else:
        return os.path.join("venv", "bin", "pip")

def get_python_command():
    """Získá správný příkaz pro python v závislosti na OS"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "python.exe")
    else:
        return os.path.join("venv", "bin", "python")

def install_dependencies():
    """Instalace závislostí"""
    print("\nInstalling dependencies...")
    
    pip_cmd = get_pip_command()
    
    if not os.path.exists(pip_cmd):
        print("Error: Virtual environment pip not found")
        return False
    
    try:
        # Upgrade pip
        print("Upgrading pip...")
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True, capture_output=True)
        print("✓ Pip upgraded")
        
        # Instalace requirements
        print("Installing packages from requirements.txt...")
        result = subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print("✓ All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def create_directories():
    """Vytvoření potřebných adresářů"""
    print("\nCreating necessary directories...")
    
    directories = ["logs", "database"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Created {directory}/")
        else:
            print(f"  {directory}/ already exists")

def test_imports():
    """Test importu základních modulů"""
    print("\nTesting imports...")
    
    python_cmd = get_python_command()
    
    test_code = """
import sys
sys.path.append('.')
try:
    import flask
    import sqlalchemy
    import lxml
    import pandas
    from backend import db_models
    from webapp import app
    print("OK")
except ImportError as e:
    print(f"FAIL: {e}")
    sys.exit(1)
"""
    
    try:
        result = subprocess.run([python_cmd, "-c", test_code], capture_output=True, text=True)
        if result.stdout.strip() == "OK":
            print("✓ All imports working correctly")
            return True
        else:
            print(f"Error testing imports: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error running import test: {e}")
        return False

def main():
    """Hlavní funkce"""
    print_header()
    
    # Kontroly a instalace
    check_python_version()
    
    if not create_venv():
        print("\n❌ Setup failed: Could not create virtual environment")
        sys.exit(1)
    
    if not install_dependencies():
        print("\n❌ Setup failed: Could not install dependencies")
        sys.exit(1)
    
    create_directories()
    
    if not test_imports():
        print("\n⚠ Warning: Some imports failed, but setup completed")
    
    # Finální instrukce
    print("\n" + "=" * 60)
    print("✅ Setup completed successfully!")
    print("=" * 60)
    print("\nTo start the application:")
    print()
    
    if platform.system() == "Windows":
        print("  Run: start_all.bat")
        print("  Or manually:")
        print("    venv\\Scripts\\activate")
        print("    python start_collector.py  # In one terminal")
        print("    python start_webapp.py     # In another terminal")
    else:
        print("  Run: ./start_all.sh")
        print("  Or manually:")
        print("    source venv/bin/activate")
        print("    python start_collector.py  # In one terminal")
        print("    python start_webapp.py     # In another terminal")
    
    print()
    print("Web application will be available at: http://localhost:8080")
    print()

if __name__ == "__main__":
    main()