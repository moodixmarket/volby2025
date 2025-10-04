from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import config

Base = declarative_base()

class RawData(Base):
    """Tabulka pro ukládání surových XML dat"""
    __tablename__ = 'raw_data'
    
    id = Column(Integer, primary_key=True)
    source_type = Column(String(50), nullable=False)  # main, okres, krajmesta, zahranici, kandidati, okrsky, obce
    source_identifier = Column(String(50))  # kód okresu, číslo dávky atd.
    xml_content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    processed = Column(Boolean, default=False)
    
    __table_args__ = (
        Index('idx_raw_data_timestamp', 'timestamp'),
        Index('idx_raw_data_source', 'source_type', 'source_identifier'),
    )

class Party(Base):
    """Tabulka politických stran"""
    __tablename__ = 'parties'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    short_name = Column(String(50))
    number = Column(Integer)  # číslo strany na hlasovacím lístku
    
    results = relationship('Result', back_populates='party')

class Region(Base):
    """Tabulka regionů (kraje, okresy, obce)"""
    __tablename__ = 'regions'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(20), nullable=False)  # kraj, okres, obec, stat
    parent_code = Column(String(20))  # kód nadřazeného regionu
    
    results = relationship('Result', back_populates='region')
    progress = relationship('VoteProgress', back_populates='region')

class Result(Base):
    """Agregované výsledky voleb"""
    __tablename__ = 'results'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    region_id = Column(Integer, ForeignKey('regions.id'), nullable=False)
    party_id = Column(Integer, ForeignKey('parties.id'), nullable=False)
    votes = Column(Integer, default=0)
    percentage = Column(Float, default=0.0)
    mandates = Column(Integer, default=0)  # počet mandátů
    
    region = relationship('Region', back_populates='results')
    party = relationship('Party', back_populates='results')
    
    __table_args__ = (
        Index('idx_results_timestamp', 'timestamp'),
        Index('idx_results_region_party', 'region_id', 'party_id'),
    )

class VoteProgress(Base):
    """Vývoj sčítání v čase"""
    __tablename__ = 'vote_progress'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    region_id = Column(Integer, ForeignKey('regions.id'), nullable=False)
    total_districts = Column(Integer, default=0)  # celkový počet okrsků
    counted_districts = Column(Integer, default=0)  # sečtené okrsky
    percentage_counted = Column(Float, default=0.0)  # procento sečtených okrsků
    total_voters = Column(Integer, default=0)  # počet voličů v seznamu
    total_votes = Column(Integer, default=0)  # celkový počet odevzdaných hlasů
    valid_votes = Column(Integer, default=0)  # platné hlasy
    turnout = Column(Float, default=0.0)  # volební účast v procentech
    
    region = relationship('Region', back_populates='progress')
    
    __table_args__ = (
        Index('idx_progress_timestamp', 'timestamp'),
        Index('idx_progress_region', 'region_id'),
    )

class AggregatedResult(Base):
    """Agregované výsledky po minutách"""
    __tablename__ = 'aggregated_results'
    
    id = Column(Integer, primary_key=True)
    minute = Column(DateTime, nullable=False)  # zaokrouhleno na minutu
    region_id = Column(Integer, ForeignKey('regions.id'), nullable=False)
    party_id = Column(Integer, ForeignKey('parties.id'), nullable=False)
    votes = Column(Integer, default=0)
    percentage = Column(Float, default=0.0)
    counted_districts = Column(Integer, default=0)
    total_districts = Column(Integer, default=0)
    
    region = relationship('Region')
    party = relationship('Party')
    
    __table_args__ = (
        Index('idx_aggregated_minute', 'minute'),
        Index('idx_aggregated_region_party', 'region_id', 'party_id', 'minute', unique=True),
    )

class Candidate(Base):
    """Kandidáti s přednostními hlasy"""
    __tablename__ = 'candidates'
    
    id = Column(Integer, primary_key=True)
    party_id = Column(Integer, ForeignKey('parties.id'), nullable=False)
    region_id = Column(Integer, ForeignKey('regions.id'), nullable=False)
    name = Column(String(200), nullable=False)
    surname = Column(String(200), nullable=False)
    title_before = Column(String(50))
    title_after = Column(String(50))
    position = Column(Integer)  # pořadí na kandidátce
    preferential_votes = Column(Integer, default=0)
    preferential_percentage = Column(Float, default=0.0)
    elected = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.now)
    
    party = relationship('Party')
    region = relationship('Region')
    
    __table_args__ = (
        Index('idx_candidates_party', 'party_id'),
        Index('idx_candidates_region', 'region_id'),
    )

# Vytvoření engine a session s UTF-8 podporou
engine = create_engine(
    config.DATABASE_URL, 
    pool_size=config.POOL_SIZE, 
    max_overflow=config.MAX_OVERFLOW,
    connect_args={
        'check_same_thread': False,
        'timeout': 20
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Inicializace databáze"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Získání databázové session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()