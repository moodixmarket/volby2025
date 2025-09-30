#!/usr/bin/env python3
"""
Rychlý test pro okamžité naplnění databáze testovacími daty
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_data_generator import TestDataGenerator
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def main():
    print("=" * 60)
    print("Quick Test Data Generation")
    print("=" * 60)
    print()
    print("This will:")
    print("1. Clear the database")
    print("2. Generate test data for ~50% counted districts")
    print("3. Create realistic election results")
    print()
    
    input("Press Enter to continue...")
    
    generator = TestDataGenerator()
    
    # Nastavit aby bylo již 50% sečteno
    generator.counted_districts = generator.total_districts // 2
    
    # Spustit generování
    generator.run("init")
    
    print()
    print("✓ Test data generated successfully!")
    print()
    print("Database now contains:")
    print(f"  • {len(generator.parties)} political parties")
    print(f"  • {len(generator.regions)} regions")
    print(f"  • {generator.counted_districts}/{generator.total_districts} districts counted")
    print(f"  • Historical data for the last 2 hours")
    print()
    print("Open http://localhost:8080 to see the results!")
    print()
    print("To generate more updates, run: python test_data_generator.py")

if __name__ == "__main__":
    main()