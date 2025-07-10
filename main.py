# main.py

import os
import sys
from dotenv import load_dotenv

from session_zero import run_session_zero
from game_loop import run_game_loop
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.schema import Session as SessionModel

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "game_master.db")
engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine)

def list_sessions(db):
    sessions = db.query(SessionModel).all()
    if not sessions:
        print("No saved sessions found.")
        return []
    print("\nSaved Sessions:")
    for i, s in enumerate(sessions):
        print(f"{i+1}. {s.genre} - {s.tone} (Realism={s.realism})")
    return sessions

def main():
    db = SessionLocal()

    while True:
        print("\n=== AI RPG GM ===")
        print("1. New Game")
        print("2. Load Game")
        print("3. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            run_session_zero(db)
        elif choice == "2":
            sessions = list_sessions(db)
            if not sessions:
                continue
            sel = input("Select session #: ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(sessions):
                run_game_loop(db, sessions[int(sel)-1].id)
        elif choice == "3":
            print("Goodbye!")
            sys.exit()
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
