# In main.py, update the "New Game" option

# ... (imports and other functions are the same) ...

# Import the new function
from session_zero import run_conversational_session_zero

def main():
    db = SessionLocal()

    while True:
        print("\n=== AI RPG GM ===")
        print("1. New Game")
        print("2. Load Game")
        print("3. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            # Call the new conversational session zero
            new_session_id = run_conversational_session_zero(db)
            if new_session_id:
                # If it returns a session ID, jump right into the game!
                run_game_loop(db, new_session_id)
        elif choice == "2":
            # ... (load game logic is the same) ...
        # ... (rest of the file is the same) ...

if __name__ == "__main__":
    main()