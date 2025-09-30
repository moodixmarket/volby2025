#!/usr/bin/env python3
"""
Skript pro spuštění sběru dat z volby.cz
"""

import sys
import logging
from pathlib import Path

# Přidání cesty k modulu
sys.path.append(str(Path(__file__).parent))

from backend.data_collector import DataCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Hlavní funkce pro spuštění kolektoru"""
    print("=" * 60)
    print("Volby PS ČR 2025 - Data Collector")
    print("=" * 60)
    print("\nSpouštím sběr dat z volby.cz...")
    print("Pro ukončení stiskněte Ctrl+C\n")
    
    try:
        collector = DataCollector()
        collector.run_forever()
    except KeyboardInterrupt:
        print("\n\nSběr dat byl ukončen uživatelem.")
    except Exception as e:
        print(f"\nChyba: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()