import time
import requests
import logging
from datetime import datetime
from typing import Optional, Set
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from backend.db_models import RawData, SessionLocal, init_db
from backend.aggregator import DataAggregator

logging.basicConfig(
    level=logging.INFO,
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_DIR / 'data_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataCollector:
    """
    Třída pro kontinuální stahování volebních dat
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Volby2025-DataCollector/1.0'
        })
        self.processed_batches: Set[int] = set()
        self.last_batch_check = datetime.now()
        
    def download_xml(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Stažení XML dat z URL
        """
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"Pokus {attempt + 1}/{max_retries} selhal pro {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponenciální backoff
        
        logger.error(f"Nepodařilo se stáhnout {url} po {max_retries} pokusech")
        return None
    
    def save_raw_data(self, source_type: str, xml_content: str, 
                     source_identifier: Optional[str] = None):
        """
        Uložení surových XML dat do databáze
        """
        db = SessionLocal()
        try:
            raw_data = RawData(
                source_type=source_type,
                source_identifier=source_identifier,
                xml_content=xml_content,
                timestamp=datetime.now(),
                processed=False
            )
            db.add(raw_data)
            db.commit()
            logger.debug(f"Uložena data typu {source_type} ({source_identifier})")
        except Exception as e:
            logger.error(f"Chyba při ukládání dat: {e}")
            db.rollback()
        finally:
            db.close()
    
    def collect_main_results(self):
        """
        Stažení hlavních výsledků
        """
        url = config.URLS['main']
        xml_content = self.download_xml(url)
        if xml_content:
            self.save_raw_data('main', xml_content)
            logger.info("Staženy hlavní výsledky")
    
    def collect_krajmesta_results(self):
        """
        Stažení výsledků krajských měst
        """
        url = config.URLS['krajmesta']
        xml_content = self.download_xml(url)
        if xml_content:
            self.save_raw_data('krajmesta', xml_content)
            logger.info("Staženy výsledky krajských měst")
    
    def collect_zahranici_results(self):
        """
        Stažení výsledků ze zahraničí
        """
        url = config.URLS['zahranici']
        xml_content = self.download_xml(url)
        if xml_content:
            self.save_raw_data('zahranici', xml_content)
            logger.info("Staženy výsledky ze zahraničí")
    
    def collect_candidates_results(self):
        """
        Stažení přednostních hlasů kandidátů
        """
        url = config.URLS['kandidati']
        xml_content = self.download_xml(url)
        if xml_content:
            self.save_raw_data('kandidati', xml_content)
            logger.info("Staženy přednostní hlasy kandidátů")
    
    def collect_okres_results(self):
        """
        Stažení výsledků všech okresů
        """
        for okres_code in config.OKRES_CODES:
            url = f"{config.BASE_URL}/okresy/vysledky_okres_{okres_code}.xml"
            xml_content = self.download_xml(url)
            if xml_content:
                self.save_raw_data('okres', xml_content, okres_code)
        
        logger.info(f"Staženy výsledky {len(config.OKRES_CODES)} okresů")
    
    def collect_batch_results(self):
        """
        Stažení dávkových souborů (okrsky, obce, okresy)
        """
        batch_types = [
            ('okrsky', 'okrsky/vysledky_okrsky_'),
            ('obce', 'obce_d/vysledky_obce_'),
            ('okresy', 'okresy_d/vysledky_okresy_')
        ]
        
        for batch_type, url_pattern in batch_types:
            # Zkusit stáhnout nové dávky
            for batch_num in range(1, config.MAX_BATCH_NUMBER + 1):
                if batch_num in self.processed_batches:
                    continue
                
                batch_str = str(batch_num).zfill(5)
                url = f"{config.BASE_URL}/{url_pattern}{batch_str}.xml"
                
                xml_content = self.download_xml(url)
                if xml_content:
                    self.save_raw_data(batch_type, xml_content, batch_str)
                    self.processed_batches.add(batch_num)
                    logger.info(f"Stažena dávka {batch_type} č. {batch_num}")
                else:
                    # Pokud dávka neexistuje, přestat hledat další
                    break
    
    def process_and_aggregate(self):
        """
        Zpracování a agregace dat
        """
        db = SessionLocal()
        try:
            aggregator = DataAggregator(db)
            
            # Zpracování surových dat
            aggregator.process_raw_data()
            
            # Agregace po minutách
            aggregator.aggregate_by_minute()
            
            db.commit()
            logger.info("Data zpracována a agregována")
            
        except Exception as e:
            logger.error(f"Chyba při zpracování dat: {e}")
            db.rollback()
        finally:
            db.close()
    
    def run_forever(self):
        """
        Hlavní smyčka pro kontinuální stahování dat
        """
        logger.info("Spuštěn sběr dat")
        
        # Inicializace databáze
        init_db()
        
        iteration = 0
        
        while True:
            try:
                start_time = time.time()
                
                # Stažení všech typů dat
                self.collect_main_results()
                self.collect_krajmesta_results()
                self.collect_zahranici_results()
                self.collect_candidates_results()
                
                # Stažení okresů (méně často)
                if iteration % 10 == 0:
                    self.collect_okres_results()
                
                # Kontrola dávkových souborů (každých 60 sekund)
                current_time = datetime.now()
                if (current_time - self.last_batch_check).total_seconds() > config.BATCH_CHECK_INTERVAL:
                    self.collect_batch_results()
                    self.last_batch_check = current_time
                
                # Zpracování a agregace každých 30 sekund
                if iteration % 30 == 0:
                    self.process_and_aggregate()
                
                # Vypočítat čas do dalšího stažení
                elapsed = time.time() - start_time
                sleep_time = max(0, config.DOWNLOAD_INTERVAL - elapsed)
                
                if sleep_time > 0:
                    logger.debug(f"Čekám {sleep_time:.1f}s do dalšího stažení")
                    time.sleep(sleep_time)
                
                iteration += 1
                
                # Log stavu každých 100 iterací
                if iteration % 100 == 0:
                    logger.info(f"Dokončeno {iteration} iterací sběru dat")
                    
            except KeyboardInterrupt:
                logger.info("Sběr dat ukončen uživatelem")
                break
            except Exception as e:
                logger.error(f"Neočekávaná chyba v hlavní smyčce: {e}")
                time.sleep(5)  # Počkat před dalším pokusem

def main():
    """
    Hlavní funkce pro spuštění sběru dat
    """
    collector = DataCollector()
    collector.run_forever()

if __name__ == "__main__":
    main()