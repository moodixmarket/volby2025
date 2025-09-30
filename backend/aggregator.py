from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
from typing import Dict, List
from backend.db_models import (
    RawData, Party, Region, Result, VoteProgress, 
    AggregatedResult, Candidate, get_db
)
from backend.xml_parser import XMLParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataAggregator:
    """Agregátor dat pro minutové intervaly"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.parser = XMLParser()
    
    def process_raw_data(self):
        """
        Zpracování všech nezpracovaných surových dat
        """
        try:
            # Získání nezpracovaných dat
            unprocessed = self.db.query(RawData).filter(
                RawData.processed == False
            ).order_by(RawData.timestamp).all()
            
            for raw_data in unprocessed:
                self._process_single_raw_data(raw_data)
                raw_data.processed = True
                self.db.commit()
                
            logger.info(f"Zpracováno {len(unprocessed)} surových záznamů")
            
        except Exception as e:
            logger.error(f"Chyba při zpracování surových dat: {e}")
            self.db.rollback()
    
    def _process_single_raw_data(self, raw_data: RawData):
        """
        Zpracování jednoho záznamu surových dat
        """
        try:
            if raw_data.source_type == 'main':
                self._process_main_results(raw_data)
            elif raw_data.source_type == 'okres':
                self._process_okres_results(raw_data)
            elif raw_data.source_type == 'kandidati':
                self._process_candidates_results(raw_data)
            elif raw_data.source_type == 'zahranici':
                self._process_zahranici_results(raw_data)
            elif raw_data.source_type in ['okrsky', 'obce', 'okresy']:
                self._process_batch_results(raw_data)
                
        except Exception as e:
            logger.error(f"Chyba při zpracování dat typu {raw_data.source_type}: {e}")
    
    def _process_main_results(self, raw_data: RawData):
        """
        Zpracování hlavních výsledků
        """
        results = self.parser.parse_main_results(raw_data.xml_content)
        if not results:
            return
        
        # Uložení nebo aktualizace informací o stranách
        for party_data in results.get('parties', []):
            party = self.db.query(Party).filter(
                Party.code == party_data['code']
            ).first()
            
            if not party:
                party = Party(
                    code=party_data['code'],
                    name=party_data['name'],
                    number=party_data['number']
                )
                self.db.add(party)
                self.db.flush()
        
        # Získání nebo vytvoření regionu pro celou ČR
        cr_region = self.db.query(Region).filter(
            Region.code == 'CZ'
        ).first()
        
        if not cr_region:
            cr_region = Region(
                code='CZ',
                name='Česká republika',
                type='stat'
            )
            self.db.add(cr_region)
            self.db.flush()
        
        # Uložení průběhu sčítání
        if results.get('progress'):
            progress = VoteProgress(
                timestamp=raw_data.timestamp,
                region_id=cr_region.id,
                **results['progress']
            )
            self.db.add(progress)
        
        # Uložení výsledků stran
        for party_data in results.get('parties', []):
            party = self.db.query(Party).filter(
                Party.code == party_data['code']
            ).first()
            
            if party:
                result = Result(
                    timestamp=raw_data.timestamp,
                    region_id=cr_region.id,
                    party_id=party.id,
                    votes=party_data['votes'],
                    percentage=party_data['percentage'],
                    mandates=party_data.get('mandates', 0)
                )
                self.db.add(result)
        
        # Zpracování výsledků po krajích
        for region_data in results.get('regions', []):
            region = self.db.query(Region).filter(
                Region.code == region_data['code']
            ).first()
            
            if not region:
                region = Region(
                    code=region_data['code'],
                    name=region_data['name'],
                    type=region_data['type']
                )
                self.db.add(region)
                self.db.flush()
            
            # Uložení výsledků stran v kraji
            for party_result in region_data.get('parties', []):
                party = self.db.query(Party).filter(
                    Party.code == party_result['code']
                ).first()
                
                if party:
                    result = Result(
                        timestamp=raw_data.timestamp,
                        region_id=region.id,
                        party_id=party.id,
                        votes=party_result['votes'],
                        percentage=party_result['percentage']
                    )
                    self.db.add(result)
        
        self.db.flush()
    
    def _process_okres_results(self, raw_data: RawData):
        """
        Zpracování výsledků okresu
        """
        results = self.parser.parse_okres_results(
            raw_data.xml_content, 
            raw_data.source_identifier
        )
        if not results:
            return
        
        # Získání nebo vytvoření okresu
        okres = self.db.query(Region).filter(
            Region.code == results['okres_code']
        ).first()
        
        if not okres:
            okres = Region(
                code=results['okres_code'],
                name=results['okres_name'],
                type='okres'
            )
            self.db.add(okres)
            self.db.flush()
        
        # Uložení průběhu sčítání
        if results.get('progress'):
            progress = VoteProgress(
                timestamp=raw_data.timestamp,
                region_id=okres.id,
                **results['progress']
            )
            self.db.add(progress)
        
        # Uložení výsledků stran
        for party_data in results.get('parties', []):
            party = self.db.query(Party).filter(
                Party.code == party_data['code']
            ).first()
            
            if party:
                result = Result(
                    timestamp=raw_data.timestamp,
                    region_id=okres.id,
                    party_id=party.id,
                    votes=party_data['votes'],
                    percentage=party_data['percentage']
                )
                self.db.add(result)
        
        # Zpracování obcí v okresu
        for obec_data in results.get('obce', []):
            obec = self.db.query(Region).filter(
                Region.code == obec_data['code']
            ).first()
            
            if not obec:
                obec = Region(
                    code=obec_data['code'],
                    name=obec_data['name'],
                    type='obec',
                    parent_code=results['okres_code']
                )
                self.db.add(obec)
                self.db.flush()
            
            # Uložení výsledků stran v obci
            for party_result in obec_data.get('parties', []):
                party = self.db.query(Party).filter(
                    Party.code == party_result['code']
                ).first()
                
                if party:
                    result = Result(
                        timestamp=raw_data.timestamp,
                        region_id=obec.id,
                        party_id=party.id,
                        votes=party_result['votes']
                    )
                    self.db.add(result)
        
        self.db.flush()
    
    def _process_candidates_results(self, raw_data: RawData):
        """
        Zpracování přednostních hlasů kandidátů
        """
        candidates = self.parser.parse_candidates_results(raw_data.xml_content)
        
        for cand_data in candidates:
            party = self.db.query(Party).filter(
                Party.code == cand_data['party_code']
            ).first()
            
            region = self.db.query(Region).filter(
                Region.code == cand_data['region_code']
            ).first()
            
            if party and region:
                # Kontrola, zda kandidát již existuje
                candidate = self.db.query(Candidate).filter(
                    Candidate.party_id == party.id,
                    Candidate.region_id == region.id,
                    Candidate.surname == cand_data['surname'],
                    Candidate.name == cand_data['name']
                ).first()
                
                if candidate:
                    # Aktualizace existujícího kandidáta
                    candidate.preferential_votes = cand_data['preferential_votes']
                    candidate.preferential_percentage = cand_data['preferential_percentage']
                    candidate.elected = cand_data['elected']
                    candidate.timestamp = raw_data.timestamp
                else:
                    # Vytvoření nového kandidáta
                    candidate = Candidate(
                        party_id=party.id,
                        region_id=region.id,
                        name=cand_data['name'],
                        surname=cand_data['surname'],
                        title_before=cand_data['title_before'],
                        title_after=cand_data['title_after'],
                        position=cand_data['position'],
                        preferential_votes=cand_data['preferential_votes'],
                        preferential_percentage=cand_data['preferential_percentage'],
                        elected=cand_data['elected'],
                        timestamp=raw_data.timestamp
                    )
                    self.db.add(candidate)
        
        self.db.flush()
    
    def _process_zahranici_results(self, raw_data: RawData):
        """
        Zpracování výsledků ze zahraničí
        """
        results = self.parser.parse_zahranici_results(raw_data.xml_content)
        if not results:
            return
        
        # Získání nebo vytvoření regionu pro zahraničí
        zahranici = self.db.query(Region).filter(
            Region.code == 'ZAHRANICI'
        ).first()
        
        if not zahranici:
            zahranici = Region(
                code='ZAHRANICI',
                name='Zahraničí',
                type='zahranici'
            )
            self.db.add(zahranici)
            self.db.flush()
        
        # Uložení celkových výsledků ze zahraničí
        for party_data in results.get('parties', []):
            party = self.db.query(Party).filter(
                Party.code == party_data['code']
            ).first()
            
            if party:
                result = Result(
                    timestamp=raw_data.timestamp,
                    region_id=zahranici.id,
                    party_id=party.id,
                    votes=party_data['votes'],
                    percentage=party_data['percentage']
                )
                self.db.add(result)
        
        # Zpracování jednotlivých států
        for country_data in results.get('countries', []):
            country = self.db.query(Region).filter(
                Region.code == country_data['code']
            ).first()
            
            if not country:
                country = Region(
                    code=country_data['code'],
                    name=country_data['name'],
                    type='stat',
                    parent_code='ZAHRANICI'
                )
                self.db.add(country)
                self.db.flush()
            
            # Uložení výsledků stran ve státě
            for party_result in country_data.get('parties', []):
                party = self.db.query(Party).filter(
                    Party.code == party_result['code']
                ).first()
                
                if party:
                    result = Result(
                        timestamp=raw_data.timestamp,
                        region_id=country.id,
                        party_id=party.id,
                        votes=party_result['votes']
                    )
                    self.db.add(result)
        
        self.db.flush()
    
    def _process_batch_results(self, raw_data: RawData):
        """
        Zpracování dávkových výsledků
        """
        results = self.parser.parse_batch_results(
            raw_data.xml_content,
            raw_data.source_type
        )
        if not results:
            return
        
        for item_data in results.get('items', []):
            # Zpracování podle typu dávky
            if raw_data.source_type == 'obce':
                region = self.db.query(Region).filter(
                    Region.code == item_data['code']
                ).first()
                
                if not region:
                    region = Region(
                        code=item_data['code'],
                        name=item_data['name'],
                        type='obec',
                        parent_code=item_data.get('okres_code')
                    )
                    self.db.add(region)
                    self.db.flush()
                
                # Uložení výsledků stran
                for party_result in item_data.get('parties', []):
                    party = self.db.query(Party).filter(
                        Party.code == party_result['code']
                    ).first()
                    
                    if party:
                        result = Result(
                            timestamp=raw_data.timestamp,
                            region_id=region.id,
                            party_id=party.id,
                            votes=party_result['votes'],
                            percentage=party_result.get('percentage', 0)
                        )
                        self.db.add(result)
        
        self.db.flush()
    
    def aggregate_by_minute(self):
        """
        Agregace dat po minutách
        """
        try:
            # Získání posledního času agregace
            last_aggregation = self.db.query(
                func.max(AggregatedResult.minute)
            ).scalar()
            
            if last_aggregation:
                start_time = last_aggregation + timedelta(minutes=1)
            else:
                # První agregace - začít od nejstaršího záznamu
                first_record = self.db.query(
                    func.min(Result.timestamp)
                ).scalar()
                
                if not first_record:
                    return
                
                start_time = first_record.replace(second=0, microsecond=0)
            
            # Konec je aktuální čas zaokrouhlený dolů na minutu
            end_time = datetime.now().replace(second=0, microsecond=0)
            
            current_minute = start_time
            
            while current_minute <= end_time:
                next_minute = current_minute + timedelta(minutes=1)
                
                # Získání nejnovějších výsledků pro každou kombinaci region-strana v dané minutě
                results = self.db.query(
                    Result.region_id,
                    Result.party_id,
                    func.max(Result.timestamp).label('max_timestamp')
                ).filter(
                    Result.timestamp >= current_minute,
                    Result.timestamp < next_minute
                ).group_by(
                    Result.region_id,
                    Result.party_id
                ).all()
                
                for region_id, party_id, max_timestamp in results:
                    # Získání konkrétního výsledku
                    result = self.db.query(Result).filter(
                        Result.region_id == region_id,
                        Result.party_id == party_id,
                        Result.timestamp == max_timestamp
                    ).first()
                    
                    if result:
                        # Získání informací o průběhu sčítání
                        progress = self.db.query(VoteProgress).filter(
                            VoteProgress.region_id == region_id,
                            VoteProgress.timestamp >= current_minute,
                            VoteProgress.timestamp < next_minute
                        ).order_by(VoteProgress.timestamp.desc()).first()
                        
                        # Vytvoření agregovaného záznamu
                        aggregated = AggregatedResult(
                            minute=current_minute,
                            region_id=region_id,
                            party_id=party_id,
                            votes=result.votes,
                            percentage=result.percentage,
                            counted_districts=progress.counted_districts if progress else 0,
                            total_districts=progress.total_districts if progress else 0
                        )
                        self.db.add(aggregated)
                
                current_minute = next_minute
            
            self.db.commit()
            logger.info(f"Agregace dokončena do {end_time}")
            
        except Exception as e:
            logger.error(f"Chyba při agregaci dat: {e}")
            self.db.rollback()
    
    def calculate_predictions(self, region_code: str = 'CZ') -> Dict:
        """
        Výpočet predikcí konečných výsledků na základě aktuálního trendu
        """
        try:
            region = self.db.query(Region).filter(
                Region.code == region_code
            ).first()
            
            if not region:
                return {}
            
            # Získání posledního stavu
            latest_progress = self.db.query(VoteProgress).filter(
                VoteProgress.region_id == region.id
            ).order_by(VoteProgress.timestamp.desc()).first()
            
            if not latest_progress or latest_progress.percentage_counted == 0:
                return {}
            
            # Získání aktuálních výsledků
            current_results = self.db.query(Result).filter(
                Result.region_id == region.id
            ).order_by(Result.timestamp.desc()).limit(20).all()  # Počet stran
            
            predictions = {
                'current_counted_percentage': latest_progress.percentage_counted,
                'parties': []
            }
            
            # Výpočet predikcí pro každou stranu
            seen_parties = set()
            for result in current_results:
                if result.party_id not in seen_parties:
                    seen_parties.add(result.party_id)
                    
                    # Jednoduchá lineární predikce
                    predicted_votes = int(result.votes * (100 / latest_progress.percentage_counted))
                    
                    predictions['parties'].append({
                        'party_id': result.party_id,
                        'party_name': result.party.name,
                        'current_votes': result.votes,
                        'current_percentage': result.percentage,
                        'predicted_votes': predicted_votes,
                        'predicted_percentage': result.percentage  # Procenta zůstávají stejná
                    })
            
            return predictions
            
        except Exception as e:
            logger.error(f"Chyba při výpočtu predikcí: {e}")
            return {}