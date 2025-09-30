from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db_models import SessionLocal, Party, Region, Result, VoteProgress, AggregatedResult, Candidate
from backend.aggregator import DataAggregator

api_bp = Blueprint('api', __name__)

def get_db_session():
    """Získání databázové session"""
    return SessionLocal()

@api_bp.route('/current_results')
def get_current_results():
    """
    Získání aktuálních výsledků voleb
    """
    db = get_db_session()
    try:
        region_code = request.args.get('region', 'CZ')
        
        # Najít region
        region = db.query(Region).filter(Region.code == region_code).first()
        if not region:
            return jsonify({'error': 'Region not found'}), 404
        
        # Získat nejnovější výsledky
        latest_results = db.query(Result).filter(
            Result.region_id == region.id
        ).order_by(Result.timestamp.desc()).limit(50).all()
        
        # Seskupit podle strany a vzít nejnovější
        party_results = {}
        for result in latest_results:
            if result.party_id not in party_results:
                party_results[result.party_id] = {
                    'party_id': result.party_id,
                    'party_code': result.party.code,
                    'party_name': result.party.name,
                    'party_number': result.party.number,
                    'votes': result.votes,
                    'percentage': result.percentage,
                    'mandates': result.mandates
                }
        
        # Seřadit podle hlasů
        sorted_results = sorted(party_results.values(), key=lambda x: x['votes'], reverse=True)
        
        return jsonify({
            'region': {
                'code': region.code,
                'name': region.name,
                'type': region.type
            },
            'results': sorted_results,
            'timestamp': datetime.now().isoformat()
        })
        
    finally:
        db.close()

@api_bp.route('/progress')
def get_progress():
    """
    Získání průběhu sčítání
    """
    db = get_db_session()
    try:
        region_code = request.args.get('region', 'CZ')
        
        # Najít region
        region = db.query(Region).filter(Region.code == region_code).first()
        if not region:
            return jsonify({'error': 'Region not found'}), 404
        
        # Získat nejnovější průběh
        latest_progress = db.query(VoteProgress).filter(
            VoteProgress.region_id == region.id
        ).order_by(VoteProgress.timestamp.desc()).first()
        
        if not latest_progress:
            return jsonify({'error': 'No progress data available'}), 404
        
        return jsonify({
            'region': {
                'code': region.code,
                'name': region.name
            },
            'total_districts': latest_progress.total_districts,
            'counted_districts': latest_progress.counted_districts,
            'percentage_counted': latest_progress.percentage_counted,
            'total_voters': latest_progress.total_voters,
            'total_votes': latest_progress.total_votes,
            'valid_votes': latest_progress.valid_votes,
            'turnout': latest_progress.turnout,
            'timestamp': latest_progress.timestamp.isoformat()
        })
        
    finally:
        db.close()

@api_bp.route('/time_series')
def get_time_series():
    """
    Získání časové řady výsledků (po minutách)
    """
    db = get_db_session()
    try:
        region_code = request.args.get('region', 'CZ')
        hours = int(request.args.get('hours', 24))  # Výchozí 24 hodin
        
        # Najít region
        region = db.query(Region).filter(Region.code == region_code).first()
        if not region:
            return jsonify({'error': 'Region not found'}), 404
        
        # Časový rozsah
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Získat agregované výsledky
        aggregated = db.query(AggregatedResult).filter(
            AggregatedResult.region_id == region.id,
            AggregatedResult.minute >= start_time,
            AggregatedResult.minute <= end_time
        ).order_by(AggregatedResult.minute).all()
        
        # Seskupit podle času a strany
        time_series = {}
        prev_total_votes = 0
        sorted_minutes = sorted(set([r.minute.isoformat() for r in aggregated]))
        
        for minute_str in sorted_minutes:
            # Najít všechny záznamy pro tuto minutu
            minute_records = [r for r in aggregated if r.minute.isoformat() == minute_str]
            if not minute_records:
                continue
                
            # Spočítat celkový počet hlasů v této minutě
            total_votes_this_minute = sum(r.votes for r in minute_records)
            
            # Spočítat nově sečtené hlasy (volume) - vždy kladné
            new_votes = max(0, total_votes_this_minute - prev_total_votes) if prev_total_votes > 0 else 0
            
            time_series[minute_str] = {
                'timestamp': minute_str,
                'counted_districts': minute_records[0].counted_districts if minute_records else 0,
                'total_districts': minute_records[0].total_districts if minute_records else 0,
                'total_votes': total_votes_this_minute,
                'new_votes': new_votes,  # Počet nově sečtených hlasů v této minutě
                'parties': {}
            }
            
            # Přidat data jednotlivých stran
            for record in minute_records:
                time_series[minute_str]['parties'][record.party.code] = {
                    'name': record.party.name,
                    'votes': record.votes,
                    'percentage': record.percentage
                }
            
            prev_total_votes = total_votes_this_minute
        
        # Převést na seznam
        time_series_list = list(time_series.values())
        
        return jsonify({
            'region': {
                'code': region.code,
                'name': region.name
            },
            'time_series': time_series_list
        })
        
    finally:
        db.close()

@api_bp.route('/regions')
def get_regions():
    """
    Seznam všech regionů
    """
    db = get_db_session()
    try:
        region_type = request.args.get('type', None)
        
        query = db.query(Region)
        if region_type:
            query = query.filter(Region.type == region_type)
        
        regions = query.order_by(Region.name).all()
        
        regions_list = [
            {
                'code': r.code,
                'name': r.name,
                'type': r.type,
                'parent_code': r.parent_code
            }
            for r in regions
        ]
        
        return jsonify({'regions': regions_list})
        
    finally:
        db.close()

@api_bp.route('/parties')
def get_parties():
    """
    Seznam politických stran
    """
    db = get_db_session()
    try:
        parties = db.query(Party).order_by(Party.number).all()
        
        parties_list = [
            {
                'id': p.id,
                'code': p.code,
                'name': p.name,
                'short_name': p.short_name,
                'number': p.number
            }
            for p in parties
        ]
        
        return jsonify({'parties': parties_list})
        
    finally:
        db.close()

@api_bp.route('/candidates')
def get_candidates():
    """
    Seznam kandidátů s přednostními hlasy
    """
    db = get_db_session()
    try:
        party_code = request.args.get('party', None)
        region_code = request.args.get('region', None)
        limit = int(request.args.get('limit', 20))
        
        query = db.query(Candidate)
        
        if party_code:
            party = db.query(Party).filter(Party.code == party_code).first()
            if party:
                query = query.filter(Candidate.party_id == party.id)
        
        if region_code:
            region = db.query(Region).filter(Region.code == region_code).first()
            if region:
                query = query.filter(Candidate.region_id == region.id)
        
        # Seřadit podle přednostních hlasů
        candidates = query.order_by(desc(Candidate.preferential_votes)).limit(limit).all()
        
        candidates_list = [
            {
                'name': c.name,
                'surname': c.surname,
                'title_before': c.title_before,
                'title_after': c.title_after,
                'party_name': c.party.name,
                'region_name': c.region.name,
                'position': c.position,
                'preferential_votes': c.preferential_votes,
                'preferential_percentage': c.preferential_percentage,
                'elected': c.elected
            }
            for c in candidates
        ]
        
        return jsonify({'candidates': candidates_list})
        
    finally:
        db.close()

@api_bp.route('/predictions')
def get_predictions():
    """
    Získání predikcí konečných výsledků
    """
    db = get_db_session()
    try:
        region_code = request.args.get('region', 'CZ')
        
        aggregator = DataAggregator(db)
        predictions = aggregator.calculate_predictions(region_code)
        
        return jsonify(predictions)
        
    finally:
        db.close()

@api_bp.route('/counting_speed')
def get_counting_speed():
    """
    Získání rychlosti sčítání
    """
    db = get_db_session()
    try:
        region_code = request.args.get('region', 'CZ')
        
        # Najít region
        region = db.query(Region).filter(Region.code == region_code).first()
        if not region:
            return jsonify({'error': 'Region not found'}), 404
        
        # Získat průběh za poslední hodinu
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        progress_data = db.query(VoteProgress).filter(
            VoteProgress.region_id == region.id,
            VoteProgress.timestamp >= start_time,
            VoteProgress.timestamp <= end_time
        ).order_by(VoteProgress.timestamp).all()
        
        if len(progress_data) < 2:
            return jsonify({'error': 'Not enough data for calculation'}), 404
        
        # Vypočítat rychlost
        first = progress_data[0]
        last = progress_data[-1]
        
        time_diff = (last.timestamp - first.timestamp).total_seconds() / 3600  # v hodinách
        districts_diff = last.counted_districts - first.counted_districts
        
        speed = districts_diff / time_diff if time_diff > 0 else 0
        
        # Odhad času do konce
        remaining_districts = last.total_districts - last.counted_districts
        estimated_hours = remaining_districts / speed if speed > 0 else 0
        
        return jsonify({
            'region': {
                'code': region.code,
                'name': region.name
            },
            'districts_per_hour': round(speed, 1),
            'districts_last_hour': districts_diff,
            'remaining_districts': remaining_districts,
            'estimated_hours_to_complete': round(estimated_hours, 1),
            'current_percentage': last.percentage_counted
        })
        
    finally:
        db.close()

@api_bp.route('/comparison')
def get_region_comparison():
    """
    Porovnání výsledků mezi regiony
    """
    db = get_db_session()
    try:
        region_codes = request.args.get('regions', 'CZ').split(',')
        party_code = request.args.get('party', None)
        
        comparison_data = []
        
        for region_code in region_codes:
            region = db.query(Region).filter(Region.code == region_code).first()
            if not region:
                continue
            
            # Získat nejnovější výsledky
            query = db.query(Result).filter(Result.region_id == region.id)
            
            if party_code:
                party = db.query(Party).filter(Party.code == party_code).first()
                if party:
                    query = query.filter(Result.party_id == party.id)
            
            latest_results = query.order_by(Result.timestamp.desc()).limit(50).all()
            
            # Seskupit podle strany
            party_results = {}
            for result in latest_results:
                if result.party_id not in party_results:
                    party_results[result.party_id] = {
                        'party_code': result.party.code,
                        'party_name': result.party.name,
                        'votes': result.votes,
                        'percentage': result.percentage
                    }
            
            comparison_data.append({
                'region_code': region.code,
                'region_name': region.name,
                'results': list(party_results.values())
            })
        
        return jsonify({'comparison': comparison_data})
        
    finally:
        db.close()

@api_bp.route('/export/<format>')
def export_data(format):
    """
    Export dat ve formátu CSV nebo JSON
    """
    db = get_db_session()
    try:
        region_code = request.args.get('region', 'CZ')
        
        # Najít region
        region = db.query(Region).filter(Region.code == region_code).first()
        if not region:
            return jsonify({'error': 'Region not found'}), 404
        
        # Získat nejnovější výsledky
        results = db.query(Result).filter(
            Result.region_id == region.id
        ).order_by(Result.timestamp.desc()).limit(50).all()
        
        # Seskupit podle strany
        party_results = {}
        for result in results:
            if result.party_id not in party_results:
                party_results[result.party_id] = {
                    'party_code': result.party.code,
                    'party_name': result.party.name,
                    'votes': result.votes,
                    'percentage': result.percentage,
                    'mandates': result.mandates
                }
        
        if format == 'json':
            return jsonify({
                'region': region.name,
                'timestamp': datetime.now().isoformat(),
                'results': list(party_results.values())
            })
        
        elif format == 'csv':
            import csv
            from io import StringIO
            from flask import Response
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(['Party Code', 'Party Name', 'Votes', 'Percentage', 'Mandates'])
            
            # Data
            for party in party_results.values():
                writer.writerow([
                    party['party_code'],
                    party['party_name'],
                    party['votes'],
                    party['percentage'],
                    party['mandates']
                ])
            
            response = Response(output.getvalue(), mimetype='text/csv')
            response.headers['Content-Disposition'] = f'attachment; filename=volby_2025_{region.code}.csv'
            return response
        
        else:
            return jsonify({'error': 'Invalid format. Use json or csv'}), 400
        
    finally:
        db.close()