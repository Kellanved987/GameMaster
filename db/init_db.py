# db/init_db.py

import os
import sys
from pathlib import Path

# Ensure root directory is in path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from db.schema import Base
from sqlalchemy import create_engine

DB_PATH = os.getenv("DB_PATH", "game_master.db")

def init_database():
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Base.metadata.create_all(engine)
    print(f"Database initialized at: {DB_PATH}")

if __name__ == "__main__":
    init_database()
