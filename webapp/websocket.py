from flask_socketio import emit, join_room, leave_room
from datetime import datetime
import threading
import time
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from backend.db_models import SessionLocal, Result, VoteProgress, Region, Party

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealtimeUpdater:
    """
    Třída pro zasílání real-time aktualizací přes WebSocket
    """
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.active_rooms = set()
        self.update_thread = None
        self.running = False
    
    def start_updates(self):
        """Spustit automatické aktualizace"""
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop)
            self.update_thread.daemon = True
            self.update_thread.start()
            logger.info("Real-time updater started")
    
    def stop_updates(self):
        """Zastavit automatické aktualizace"""
        self.running = False
        if self.update_thread:
            self.update_thread.join()
        logger.info("Real-time updater stopped")
    
    def _update_loop(self):
        """Hlavní smyčka pro zasílání aktualizací"""
        while self.running:
            try:
                # Aktualizovat všechny aktivní místnosti
                for room in list(self.active_rooms):
                    self._send_update_to_room(room)
                
                # Čekat před další aktualizací
                time.sleep(config.AUTO_REFRESH_INTERVAL)
                
            except Exception as e:
                logger.error(f"Chyba v update loop: {e}")
                time.sleep(5)
    
    def _send_update_to_room(self, room):
        """Poslat aktualizaci do konkrétní místnosti"""
        try:
            db = SessionLocal()
            
            # Parsovat room ID (format: region_<code>)
            if room.startswith('region_'):
                region_code = room[7:]
                
                # Najít region
                region = db.query(Region).filter(Region.code == region_code).first()
                if not region:
                    return
                
                # Získat nejnovější výsledky
                latest_results = db.query(Result).filter(
                    Result.region_id == region.id
                ).order_by(Result.timestamp.desc()).limit(50).all()
                
                # Získat nejnovější průběh
                latest_progress = db.query(VoteProgress).filter(
                    VoteProgress.region_id == region.id
                ).order_by(VoteProgress.timestamp.desc()).first()
                
                # Připravit data
                party_results = {}
                for result in latest_results:
                    if result.party_id not in party_results:
                        party_results[result.party_id] = {
                            'party_code': result.party.code,
                            'party_name': result.party.name,
                            'party_number': result.party.number,
                            'votes': result.votes,
                            'percentage': result.percentage,
                            'mandates': result.mandates
                        }

                # Seřadit podle hlasů (stejně jako REST API)
                sorted_results = sorted(party_results.values(), key=lambda x: x['votes'], reverse=True)

                update_data = {
                    'type': 'results_update',
                    'region': {
                        'code': region.code,
                        'name': region.name
                    },
                    'results': sorted_results,
                    'progress': None,
                    'timestamp': datetime.now().isoformat()
                }
                
                if latest_progress:
                    update_data['progress'] = {
                        'counted_districts': latest_progress.counted_districts,
                        'total_districts': latest_progress.total_districts,
                        'percentage_counted': latest_progress.percentage_counted,
                        'total_voters': latest_progress.total_voters,
                        'total_votes': latest_progress.total_votes,
                        'valid_votes': latest_progress.valid_votes,
                        'turnout': latest_progress.turnout
                    }
                
                # Poslat aktualizaci
                self.socketio.emit('update', update_data, room=room)
                
            db.close()
            
        except Exception as e:
            logger.error(f"Chyba při odesílání aktualizace do místnosti {room}: {e}")
    
    def add_room(self, room):
        """Přidat místnost k aktualizacím"""
        self.active_rooms.add(room)
        logger.info(f"Room {room} added to active rooms")
    
    def remove_room(self, room):
        """Odebrat místnost z aktualizací"""
        self.active_rooms.discard(room)
        logger.info(f"Room {room} removed from active rooms")

# Globální instance updatru
realtime_updater = None

def setup_websocket_handlers(socketio):
    """
    Nastavení WebSocket event handlerů
    """
    global realtime_updater
    realtime_updater = RealtimeUpdater(socketio)
    realtime_updater.start_updates()
    
    @socketio.on('connect')
    def handle_connect():
        """Handler pro připojení klienta"""
        logger.info(f"Client connected")
        emit('connected', {'message': 'Successfully connected to server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handler pro odpojení klienta"""
        logger.info(f"Client disconnected")
    
    @socketio.on('subscribe')
    def handle_subscribe(data):
        """
        Handler pro přihlášení k odběru aktualizací pro region
        """
        region_code = data.get('region', 'CZ')
        room = f'region_{region_code}'
        
        join_room(room)
        realtime_updater.add_room(room)
        
        logger.info(f"Client subscribed to {room}")
        emit('subscribed', {'region': region_code, 'room': room})
        
        # Poslat okamžitou aktualizaci
        realtime_updater._send_update_to_room(room)
    
    @socketio.on('unsubscribe')
    def handle_unsubscribe(data):
        """
        Handler pro odhlášení z odběru aktualizací
        """
        region_code = data.get('region', 'CZ')
        room = f'region_{region_code}'
        
        leave_room(room)
        
        # Zkontrolovat, zda v místnosti někdo zůstal
        # (toto je zjednodušené, v produkci byste měli sledovat počet klientů)
        
        logger.info(f"Client unsubscribed from {room}")
        emit('unsubscribed', {'region': region_code, 'room': room})
    
    @socketio.on('request_update')
    def handle_request_update(data):
        """
        Handler pro manuální požadavek na aktualizaci
        """
        region_code = data.get('region', 'CZ')
        room = f'region_{region_code}'
        
        realtime_updater._send_update_to_room(room)
        
    @socketio.on('get_time_series')
    def handle_get_time_series(data):
        """
        Handler pro získání časové řady dat
        """
        try:
            region_code = data.get('region', 'CZ')
            hours = data.get('hours', 24)
            
            db = SessionLocal()
            
            # Najít region
            region = db.query(Region).filter(Region.code == region_code).first()
            if not region:
                emit('error', {'message': 'Region not found'})
                return
            
            from datetime import timedelta
            from backend.db_models import AggregatedResult
            
            # Časový rozsah
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Získat agregované výsledky
            aggregated = db.query(AggregatedResult).filter(
                AggregatedResult.region_id == region.id,
                AggregatedResult.minute >= start_time,
                AggregatedResult.minute <= end_time
            ).order_by(AggregatedResult.minute).all()
            
            # Připravit data pro graf
            time_series = {}
            for record in aggregated:
                minute_str = record.minute.strftime('%Y-%m-%d %H:%M')
                if minute_str not in time_series:
                    time_series[minute_str] = {
                        'timestamp': minute_str,
                        'parties': {}
                    }
                
                time_series[minute_str]['parties'][record.party.code] = {
                    'votes': record.votes,
                    'percentage': record.percentage
                }
            
            emit('time_series_data', {
                'region': region_code,
                'data': list(time_series.values())
            })
            
            db.close()
            
        except Exception as e:
            logger.error(f"Chyba při získávání časové řady: {e}")
            emit('error', {'message': 'Failed to get time series data'})
    
    @socketio.on('get_counting_speed')
    def handle_get_counting_speed(data):
        """
        Handler pro získání rychlosti sčítání
        """
        try:
            region_code = data.get('region', 'CZ')
            
            db = SessionLocal()
            
            # Najít region
            region = db.query(Region).filter(Region.code == region_code).first()
            if not region:
                emit('error', {'message': 'Region not found'})
                return
            
            from datetime import timedelta
            
            # Získat průběh za poslední hodinu
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            progress_data = db.query(VoteProgress).filter(
                VoteProgress.region_id == region.id,
                VoteProgress.timestamp >= start_time,
                VoteProgress.timestamp <= end_time
            ).order_by(VoteProgress.timestamp).all()
            
            if len(progress_data) < 2:
                emit('counting_speed_data', {
                    'region': region_code,
                    'districts_per_hour': 0,
                    'estimated_hours': 0
                })
                return
            
            # Vypočítat rychlost
            first = progress_data[0]
            last = progress_data[-1]
            
            time_diff = (last.timestamp - first.timestamp).total_seconds() / 3600
            districts_diff = last.counted_districts - first.counted_districts
            
            speed = districts_diff / time_diff if time_diff > 0 else 0
            
            # Odhad času do konce
            remaining = last.total_districts - last.counted_districts
            estimated_hours = remaining / speed if speed > 0 else 0
            
            emit('counting_speed_data', {
                'region': region_code,
                'districts_per_hour': round(speed, 1),
                'districts_last_hour': districts_diff,
                'remaining_districts': remaining,
                'estimated_hours': round(estimated_hours, 1),
                'current_percentage': last.percentage_counted
            })
            
            db.close()
            
        except Exception as e:
            logger.error(f"Chyba při výpočtu rychlosti sčítání: {e}")
            emit('error', {'message': 'Failed to calculate counting speed'})