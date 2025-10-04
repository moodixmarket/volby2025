from lxml import etree
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XMLParser:
    """Parser pro zpracování XML dat z volby.cz"""
    
    def __init__(self):
        self.namespaces = {
            'ns': 'http://www.volby.cz/ps/'
        }
    
    def parse_main_results(self, xml_content: str) -> Dict:
        """
        Parsování hlavních výsledků voleb
        """
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            results = {
                'timestamp': datetime.now(),
                'regions': [],
                'parties': [],
                'progress': {}
            }
            
            # Celkové informace o průběhu sčítání - sečteme ze všech krajů
            total_districts = 0
            counted_districts = 0
            total_voters = 0
            total_votes = 0
            valid_votes = 0
            
            # Nejdřív projdeme všechny kraje pro celkovou statistiku
            for kraj in root.findall('.//ns:KRAJ', self.namespaces):
                ucast = kraj.find('ns:UCAST', self.namespaces)
                if ucast is not None:
                    total_districts += int(ucast.get('OKRSKY_CELKEM', 0))
                    counted_districts += int(ucast.get('OKRSKY_ZPRAC', 0))
                    total_voters += int(ucast.get('ZAPSANI_VOLICI', 0))
                    total_votes += int(ucast.get('VYDANE_OBALKY', 0))
                    valid_votes += int(ucast.get('PLATNE_HLASY', 0))
            
            if total_districts > 0:
                results['progress'] = {
                    'total_districts': total_districts,
                    'counted_districts': counted_districts,
                    'percentage_counted': round(counted_districts / total_districts * 100, 2) if total_districts > 0 else 0,
                    'total_voters': total_voters,
                    'total_votes': total_votes,
                    'valid_votes': valid_votes,
                    'turnout': round(total_votes / total_voters * 100, 2) if total_voters > 0 else 0
                }
            
            # Výsledky jednotlivých stran - sečteme ze všech krajů
            party_totals = {}
            
            for kraj in root.findall('.//ns:KRAJ', self.namespaces):
                for strana in kraj.findall('ns:STRANA', self.namespaces):
                    party_code = strana.get('KSTRANA')
                    party_name = strana.get('NAZ_STR')
                    hodnoty = strana.find('ns:HODNOTY_STRANA', self.namespaces)
                    
                    if hodnoty is not None:
                        votes = int(hodnoty.get('HLASY', 0))
                        
                        if party_code not in party_totals:
                            party_totals[party_code] = {
                                'code': party_code,
                                'name': party_name,
                                'votes': 0
                            }
                        party_totals[party_code]['votes'] += votes
            
            # Vypočítáme procenta a přidáme do výsledků
            for party in party_totals.values():
                percentage = round(party['votes'] / valid_votes * 100, 2) if valid_votes > 0 else 0
                party_data = {
                    'code': party['code'],
                    'name': party['name'],
                    'number': int(party['code']),  # Použijeme kód jako číslo
                    'votes': party['votes'],
                    'percentage': percentage,
                    'mandates': 0  # TODO: počítat mandáty podle D'Hondtovy metody
                }
                results['parties'].append(party_data)
            
            # Výsledky po krajích
            for kraj in root.findall('.//KRAJ', self.namespaces):
                region_data = {
                    'code': kraj.get('CIS_KRAJ'),
                    'name': kraj.get('NAZ_KRAJ'),
                    'type': 'kraj',
                    'parties': []
                }
                
                for strana in kraj.findall('.//STRANA', self.namespaces):
                    party_result = {
                        'code': strana.get('KSTRANA'),
                        'votes': int(strana.get('HLASY', 0)),
                        'percentage': float(strana.get('PROC_HLASU', '0').replace(',', '.'))
                    }
                    region_data['parties'].append(party_result)
                
                results['regions'].append(region_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Chyba při parsování hlavních výsledků: {e}")
            return {}
    
    def parse_okres_results(self, xml_content: str, okres_code: str) -> Dict:
        """
        Parsování výsledků za okres
        """
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            results = {
                'timestamp': datetime.now(),
                'okres_code': okres_code,
                'okres_name': '',
                'progress': {},
                'parties': [],
                'obce': []
            }
            
            # Informace o okresu
            okres_elem = root.find('.//OKRES', self.namespaces)
            if okres_elem is not None:
                results['okres_name'] = okres_elem.get('NAZ_OKRES', '')
                
                # Průběh sčítání v okresu
                ucast_elem = okres_elem.find('.//UCAST', self.namespaces)
                if ucast_elem is not None:
                    results['progress'] = {
                        'total_districts': int(ucast_elem.get('OKRSKY_CELKEM', 0)),
                        'counted_districts': int(ucast_elem.get('OKRSKY_ZPRAC', 0)),
                        'percentage_counted': float(ucast_elem.get('OKRSKY_ZPRAC_PROC', 0)),
                        'turnout': float(ucast_elem.get('UCAST_PROC', 0))
                    }
                
                # Výsledky stran v okresu
                for strana in okres_elem.findall('.//STRANA', self.namespaces):
                    party_data = {
                        'code': strana.get('KSTRANA'),
                        'votes': int(strana.get('HLASY', 0)),
                        'percentage': float(strana.get('PROC_HLASU', '0').replace(',', '.'))
                    }
                    results['parties'].append(party_data)
            
            # Výsledky po obcích
            for obec in root.findall('.//OBEC', self.namespaces):
                obec_data = {
                    'code': obec.get('CIS_OBEC'),
                    'name': obec.get('NAZ_OBEC'),
                    'counted': obec.get('ZPRACOVANO') == '1',
                    'parties': []
                }
                
                for strana in obec.findall('.//STRANA', self.namespaces):
                    party_result = {
                        'code': strana.get('KSTRANA'),
                        'votes': int(strana.get('HLASY', 0))
                    }
                    obec_data['parties'].append(party_result)
                
                results['obce'].append(obec_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Chyba při parsování výsledků okresu {okres_code}: {e}")
            return {}
    
    def parse_candidates_results(self, xml_content: str) -> List[Dict]:
        """
        Parsování přednostních hlasů kandidátů
        """
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            candidates = []
            
            for kandidat in root.findall('.//KANDIDAT', self.namespaces):
                candidate_data = {
                    'party_code': kandidat.get('KSTRANA'),
                    'region_code': kandidat.get('CKRAJ'),
                    'name': kandidat.get('JMENO'),
                    'surname': kandidat.get('PRIJMENI'),
                    'title_before': kandidat.get('TITULPRED', ''),
                    'title_after': kandidat.get('TITULZA', ''),
                    'position': int(kandidat.get('PORCISLO', 0)),
                    'preferential_votes': int(kandidat.get('PREF_HLASY', 0)),
                    'preferential_percentage': float(kandidat.get('PROC_PREF_HLASU', '0').replace(',', '.')),
                    'elected': kandidat.get('ZVOLEN') == '1'
                }
                candidates.append(candidate_data)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Chyba při parsování kandidátů: {e}")
            return []
    
    def parse_batch_results(self, xml_content: str, batch_type: str) -> Dict:
        """
        Parsování dávkových souborů (okrsky, obce, okresy)
        """
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            results = {
                'timestamp': datetime.now(),
                'batch_type': batch_type,
                'items': []
            }
            
            # Různé typy dávek mají různou strukturu
            if batch_type == 'okrsky':
                for okrsek in root.findall('.//OKRSEK', self.namespaces):
                    item_data = {
                        'code': okrsek.get('CIS_OKRSEK'),
                        'obec_code': okrsek.get('CIS_OBEC'),
                        'processed': okrsek.get('ZPRACOVANO') == '1',
                        'parties': []
                    }
                    
                    for strana in okrsek.findall('.//STRANA', self.namespaces):
                        party_result = {
                            'code': strana.get('KSTRANA'),
                            'votes': int(strana.get('HLASY', 0))
                        }
                        item_data['parties'].append(party_result)
                    
                    results['items'].append(item_data)
                    
            elif batch_type == 'obce':
                for obec in root.findall('.//OBEC', self.namespaces):
                    item_data = {
                        'code': obec.get('CIS_OBEC'),
                        'name': obec.get('NAZ_OBEC'),
                        'okres_code': obec.get('CIS_OKRES'),
                        'processed': obec.get('ZPRACOVANO') == '1',
                        'turnout': float(obec.get('UCAST_PROC', '0').replace(',', '.')),
                        'parties': []
                    }
                    
                    for strana in obec.findall('.//STRANA', self.namespaces):
                        party_result = {
                            'code': strana.get('KSTRANA'),
                            'votes': int(strana.get('HLASY', 0)),
                            'percentage': float(strana.get('PROC_HLASU', '0').replace(',', '.'))
                        }
                        item_data['parties'].append(party_result)
                    
                    results['items'].append(item_data)
                    
            elif batch_type == 'okresy':
                for okres in root.findall('.//OKRES', self.namespaces):
                    item_data = {
                        'code': okres.get('CIS_OKRES'),
                        'name': okres.get('NAZ_OKRES'),
                        'kraj_code': okres.get('CIS_KRAJ'),
                        'counted_districts': int(okres.get('OKRSKY_ZPRAC', 0)),
                        'total_districts': int(okres.get('OKRSKY_CELKEM', 0)),
                        'turnout': float(okres.get('UCAST_PROC', '0').replace(',', '.')),
                        'parties': []
                    }
                    
                    for strana in okres.findall('.//STRANA', self.namespaces):
                        party_result = {
                            'code': strana.get('KSTRANA'),
                            'votes': int(strana.get('HLASY', 0)),
                            'percentage': float(strana.get('PROC_HLASU', '0').replace(',', '.'))
                        }
                        item_data['parties'].append(party_result)
                    
                    results['items'].append(item_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Chyba při parsování dávky typu {batch_type}: {e}")
            return {}
    
    def parse_zahranici_results(self, xml_content: str) -> Dict:
        """
        Parsování výsledků ze zahraničí
        """
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            results = {
                'timestamp': datetime.now(),
                'countries': [],
                'total_votes': 0,
                'parties': []
            }
            
            # Celkové výsledky ze zahraničí
            zahranici_elem = root.find('.//ZAHRANICI', self.namespaces)
            if zahranici_elem is not None:
                results['total_votes'] = int(zahranici_elem.get('PLATNE_HLASY', 0))
                
                # Výsledky stran
                for strana in zahranici_elem.findall('.//STRANA', self.namespaces):
                    party_data = {
                        'code': strana.get('KSTRANA'),
                        'votes': int(strana.get('HLASY', 0)),
                        'percentage': float(strana.get('PROC_HLASU', '0').replace(',', '.'))
                    }
                    results['parties'].append(party_data)
            
            # Výsledky po státech
            for stat in root.findall('.//STAT', self.namespaces):
                country_data = {
                    'code': stat.get('CIS_STAT'),
                    'name': stat.get('NAZ_STAT'),
                    'votes': int(stat.get('PLATNE_HLASY', 0)),
                    'parties': []
                }
                
                for strana in stat.findall('.//STRANA', self.namespaces):
                    party_result = {
                        'code': strana.get('KSTRANA'),
                        'votes': int(strana.get('HLASY', 0))
                    }
                    country_data['parties'].append(party_result)
                
                results['countries'].append(country_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Chyba při parsování výsledků ze zahraničí: {e}")
            return {}