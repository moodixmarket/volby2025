#!/usr/bin/env python3
"""
Skript pro spuštění webové aplikace
"""

import sys
import logging
from pathlib import Path

# Přidání cesty k modulu
sys.path.append(str(Path(__file__).parent))

from webapp.app import run_app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Hlavní funkce pro spuštění webové aplikace"""
    print("=" * 60)
    print("Volby PS ČR 2025 - Web Application")
    print("=" * 60)
    print("\nSpouštím webovou aplikaci...")
    print(f"Aplikace bude dostupná na: http://localhost:8080")
    print("(nebo na jiném volném portu, pokud je 8080 obsazený)")
    print("Pro ukončení stiskněte Ctrl+C\n")
    
    try:
        run_app()
    except KeyboardInterrupt:
        print("\n\nAplikace byla ukončena uživatelem.")
    except Exception as e:
        print(f"\nChyba: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()