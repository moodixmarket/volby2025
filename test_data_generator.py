#!/usr/bin/env python3
"""
Generátor testovacích dat pro simulaci volebních výsledků
"""

import random
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.db_models import SessionLocal, init_db, Party, Region, Result, VoteProgress, AggregatedResult, Candidate
from sqlalchemy import func
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class TestDataGenerator:
    """Generátor realistických testovacích dat"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.parties = []
        self.regions = []
        self.total_districts = 14866  # Reálný počet okrsků v ČR
        self.counted_districts = 0
        self.total_voters = 8500000  # Přibližný počet voličů
        self.start_time = datetime.now() - timedelta(hours=2)  # Simulace začátku před 2 hodinami
        
        # Reálné strany s očekávanými výsledky
        self.party_data = [
            {"code": "ANO", "name": "ANO 2011", "short_name": "ANO", "number": 1, "expected_pct": 28.5},
            {"code": "ODS", "name": "Občanská demokratická strana", "short_name": "ODS", "number": 2, "expected_pct": 15.2},
            {"code": "STAN", "name": "Starostové a nezávislí", "short_name": "STAN", "number": 3, "expected_pct": 13.8},
            {"code": "SPD", "name": "Svoboda a přímá demokracie", "short_name": "SPD", "number": 4, "expected_pct": 11.5},
            {"code": "PIRATI", "name": "Česká pirátská strana", "short_name": "Piráti", "number": 5, "expected_pct": 9.3},
            {"code": "CSSD", "name": "Česká strana sociálně demokratická", "short_name": "ČSSD", "number": 6, "expected_pct": 4.2},
            {"code": "KDU", "name": "KDU-ČSL", "short_name": "KDU-ČSL", "number": 7, "expected_pct": 5.8},
            {"code": "TOP09", "name": "TOP 09", "short_name": "TOP 09", "number": 8, "expected_pct": 5.1},
            {"code": "KSCM", "name": "Komunistická strana Čech a Moravy", "short_name": "KSČM", "number": 9, "expected_pct": 3.8},
            {"code": "PRISERAHA", "name": "Přísaha", "short_name": "Přísaha", "number": 10, "expected_pct": 2.8}
        ]
        
        # České kraje
        self.kraj_data = [
            {"code": "CZ010", "name": "Hlavní město Praha"},
            {"code": "CZ020", "name": "Středočeský kraj"},
            {"code": "CZ031", "name": "Jihočeský kraj"},
            {"code": "CZ032", "name": "Plzeňský kraj"},
            {"code": "CZ041", "name": "Karlovarský kraj"},
            {"code": "CZ042", "name": "Ústecký kraj"},
            {"code": "CZ051", "name": "Liberecký kraj"},
            {"code": "CZ052", "name": "Královéhradecký kraj"},
            {"code": "CZ053", "name": "Pardubický kraj"},
            {"code": "CZ063", "name": "Kraj Vysočina"},
            {"code": "CZ064", "name": "Jihomoravský kraj"},
            {"code": "CZ071", "name": "Olomoucký kraj"},
            {"code": "CZ072", "name": "Zlínský kraj"},
            {"code": "CZ080", "name": "Moravskoslezský kraj"}
        ]
    
    def clear_database(self):
        """Vyčištění databáze od starých dat"""
        logger.info("Clearing old data...")
        self.db.query(AggregatedResult).delete()
        self.db.query(Result).delete()
        self.db.query(VoteProgress).delete()
        self.db.query(Candidate).delete()
        self.db.query(Party).delete()
        self.db.query(Region).delete()
        self.db.commit()
        logger.info("Database cleared")
    
    def create_parties(self):
        """Vytvoření politických stran"""
        logger.info("Creating parties...")
        for party_info in self.party_data:
            party = Party(
                code=party_info["code"],
                name=party_info["name"],
                short_name=party_info["short_name"],
                number=party_info["number"]
            )
            self.db.add(party)
            self.parties.append(party)
        self.db.commit()
        logger.info(f"Created {len(self.parties)} parties")
    
    def create_regions(self):
        """Vytvoření regionů"""
        logger.info("Creating regions...")
        
        # Celá ČR
        cr = Region(code="CZ", name="Česká republika", type="stat")
        self.db.add(cr)
        self.regions.append(cr)
        
        # Kraje
        for kraj_info in self.kraj_data:
            kraj = Region(
                code=kraj_info["code"],
                name=kraj_info["name"],
                type="kraj"
            )
            self.db.add(kraj)
            self.regions.append(kraj)
        
        # Několik okresů pro každý kraj
        okres_names = ["Sever", "Jih", "Východ", "Západ", "Centrum"]
        for kraj in self.regions[1:]:  # Skip ČR
            for i, okres_name in enumerate(okres_names[:3]):  # 3 okresy na kraj
                okres = Region(
                    code=f"{kraj.code}_O{i+1}",
                    name=f"{kraj.name} - {okres_name}",
                    type="okres",
                    parent_code=kraj.code
                )
                self.db.add(okres)
                self.regions.append(okres)
        
        self.db.commit()
        logger.info(f"Created {len(self.regions)} regions")
    
    def create_candidates(self):
        """Vytvoření kandidátů s přednostními hlasy"""
        logger.info("Creating candidates...")
        
        first_names = ["Jan", "Petr", "Pavel", "Tomáš", "Martin", "Jana", "Eva", "Hana", "Marie", "Lenka"]
        last_names = ["Novák", "Svoboda", "Novotný", "Dvořák", "Černý", "Procházka", "Krejčí", "Horák", "Němec", "Pospíšil"]
        titles = ["Ing.", "Mgr.", "JUDr.", "MUDr.", "PhDr.", "doc.", "prof.", "", "", ""]
        
        for party in self.parties[:5]:  # Top 5 stran
            for region in self.regions[1:6]:  # Několik krajů
                for position in range(1, 11):  # Top 10 kandidátů
                    candidate = Candidate(
                        party_id=party.id,
                        region_id=region.id,
                        name=random.choice(first_names),
                        surname=random.choice(last_names),
                        title_before=random.choice(titles),
                        title_after="Ph.D." if random.random() > 0.7 else "",
                        position=position,
                        preferential_votes=random.randint(100, 10000),
                        preferential_percentage=random.uniform(0.5, 15.0),
                        elected=position <= 3 and random.random() > 0.5
                    )
                    self.db.add(candidate)
        
        self.db.commit()
        logger.info("Created candidates")
    
    def generate_single_update(self, current_time: datetime):
        """Generování jedné aktualizace dat"""
        
        # Zvýšit počet sečtených okrsků
        new_districts = min(random.randint(50, 200), self.total_districts - self.counted_districts)
        self.counted_districts += new_districts
        percentage_counted = (self.counted_districts / self.total_districts) * 100
        
        # Výpočet účasti (postupně roste)
        base_turnout = 45 + (percentage_counted * 0.2)  # 45-65%
        turnout = min(base_turnout + random.uniform(-2, 2), 75)
        
        total_votes = int(self.total_voters * (turnout / 100) * (percentage_counted / 100))
        valid_votes = int(total_votes * 0.98)  # 98% platných hlasů
        
        logger.info(f"Update: {self.counted_districts}/{self.total_districts} districts ({percentage_counted:.1f}%), turnout {turnout:.1f}%")
        
        # Pro každý region
        for region in self.regions[:3]:  # ČR a první 2 kraje pro rychlost
            
            # Progress
            progress = VoteProgress(
                timestamp=current_time,
                region_id=region.id,
                total_districts=self.total_districts if region.code == "CZ" else self.total_districts // 14,
                counted_districts=self.counted_districts if region.code == "CZ" else self.counted_districts // 14,
                percentage_counted=percentage_counted,
                total_voters=self.total_voters if region.code == "CZ" else self.total_voters // 14,
                total_votes=total_votes if region.code == "CZ" else total_votes // 14,
                valid_votes=valid_votes if region.code == "CZ" else valid_votes // 14,
                turnout=turnout
            )
            self.db.add(progress)
            
            # Výsledky stran
            remaining_pct = 100.0
            party_results = []
            
            for i, party in enumerate(self.parties):
                # Postupná konvergence k očekávanému výsledku
                party_info = self.party_data[i]
                expected = party_info["expected_pct"]
                
                # Na začátku více variability, postupně se stabilizuje
                variability = 5.0 * (1 - percentage_counted / 100)
                current_pct = expected + random.uniform(-variability, variability)
                current_pct = max(0.1, min(current_pct, remaining_pct))
                
                # Regionální variace
                if region.type == "kraj":
                    regional_var = random.uniform(-2, 2)
                    current_pct += regional_var
                
                current_pct = max(0.1, current_pct)
                
                if i == len(self.parties) - 1:
                    current_pct = remaining_pct  # Poslední strana dostane zbytek
                else:
                    remaining_pct -= current_pct
                
                votes = int(valid_votes * (current_pct / 100))
                
                # Výpočet mandátů (D'Hondt, 5% klauzule)
                mandates = 0
                if current_pct >= 5.0 and region.code == "CZ":
                    mandates = int(200 * (current_pct / 100))  # Zjednodušený výpočet
                
                result = Result(
                    timestamp=current_time,
                    region_id=region.id,
                    party_id=party.id,
                    votes=votes,
                    percentage=current_pct,
                    mandates=mandates
                )
                self.db.add(result)
                party_results.append((party.name, current_pct))
            
            # Agregované výsledky po minutách
            minute = current_time.replace(second=0, microsecond=0)
            for party in self.parties:
                result = self.db.query(Result).filter(
                    Result.region_id == region.id,
                    Result.party_id == party.id,
                    Result.timestamp == current_time
                ).first()
                
                if result:
                    agg = AggregatedResult(
                        minute=minute,
                        region_id=region.id,
                        party_id=party.id,
                        votes=result.votes,
                        percentage=result.percentage,
                        counted_districts=self.counted_districts,
                        total_districts=self.total_districts
                    )
                    self.db.add(agg)
        
        self.db.commit()
    
    def generate_historical_data(self):
        """Generování historických dat za poslední 2 hodiny"""
        logger.info("Generating historical data...")
        
        current_time = self.start_time
        now = datetime.now()
        
        # Reset počítadla
        self.counted_districts = 0
        
        while current_time < now and self.counted_districts < self.total_districts:
            self.generate_single_update(current_time)
            current_time += timedelta(minutes=1)
        
        logger.info(f"Generated historical data up to {self.counted_districts} districts")
    
    def run_continuous(self, interval: int = 30):
        """Kontinuální generování nových dat"""
        logger.info(f"Starting continuous generation every {interval} seconds...")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while self.counted_districts < self.total_districts:
                current_time = datetime.now()
                self.generate_single_update(current_time)
                
                if self.counted_districts >= self.total_districts:
                    logger.info("All districts counted! Simulation complete.")
                    break
                
                logger.info(f"Next update in {interval} seconds...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("\nSimulation stopped by user")
    
    def run(self, mode: str = "both"):
        """Hlavní metoda pro spuštění generátoru"""
        
        # Inicializace databáze
        init_db()
        
        if mode in ["init", "both"]:
            # Vyčištění a inicializace
            self.clear_database()
            self.create_parties()
            self.create_regions()
            self.create_candidates()
            
            # Generování historických dat
            self.generate_historical_data()
            
            logger.info("Initial data generation complete!")
            logger.info(f"Generated data for {self.counted_districts}/{self.total_districts} districts")
        
        if mode in ["continuous", "both"]:
            # Kontinuální generování
            self.run_continuous()

def main():
    """Hlavní funkce"""
    print("=" * 60)
    print("Test Data Generator for Volby 2025")
    print("=" * 60)
    print()
    print("Select mode:")
    print("1. Generate initial historical data only")
    print("2. Run continuous updates only")
    print("3. Both (clear, init, then continuous)")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    generator = TestDataGenerator()
    
    if choice == "1":
        generator.run("init")
        print("\nHistorical data generated successfully!")
        print("You can now open http://localhost:8080 to see the data")
    elif choice == "2":
        generator.run("continuous")
    elif choice == "3":
        generator.run("both")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()