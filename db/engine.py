# db/engine.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///game_master.db"

_engine = create_engine(DATABASE_URL, echo=False, future=True)

def get_engine():
    return _engine

def get_session():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return SessionLocal()
