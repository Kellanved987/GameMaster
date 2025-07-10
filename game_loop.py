# game_loop.py

import json
from prompt_builder.builder import build_prompt
from gpt_interface.gpt_client import call_chat_model
from db.schema import Session as SessionModel, Turn
from sqlalchemy.orm import Session as DBSession
from datetime import datetime
from memory.ingest import chunk_and_store
from utils.simulation import run_simulation_pass
from utils.dialogue_tracker import update_conversation_context
from utils.progression import evaluate_player_growth

SIMULATION_TURN_THRESHOLD = 5  # Run simulation at least every 5 turns

def run_game_loop(db: DBSession, session_id: int):
    session = db.query(SessionModel).get(session_id)
    if not session:
        print("Error: Session not found.")
        return

    print(f"\n🎮 Loaded session: {session.genre} - {session.tone}")
    print("Type your action. Type 'exit' to quit.\n")

    turn_counter = db.query(Turn).filter_by(session_id=session_id).count()
    sim_counter = 0  # Tracks turns since last simulation

    while True:
        player_input = input("> ").strip()
        if player_input.lower() in {"exit", "quit"}:
            print("Session paused.")
            break

        full_prompt = build_prompt(db, session_id, player_input)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are the player's AI game master. Respond in a cinematic, immersive tone "
                    "based on the current context. Respond using this JSON format:\n\n"
                    "{\n"
                    "  \"narration\": \"...your story text...\",\n"
                    "  \"run_simulation\": true or false\n"
                    "}"
                )
            },
            {"role": "user", "content": full_prompt}
        ]

        raw_response = call_chat_model(messages, model="gpt4o")

        try:
            parsed = json.loads(raw_response)
            narration = parsed.get("narration", "").strip()
            run_sim = parsed.get("run_simulation", False)
        except json.JSONDecodeError:
            # Fail-safe: treat whole response as narration
            narration = raw_response.strip()
            run_sim = False

        print(f"\n🧠 GM:\n{narration}")

        # Log turn to DB
        turn_counter += 1
        sim_counter += 1

        turn_entry = Turn(
            session_id=session_id,
            turn_number=turn_counter,
            player_input=player_input,
            gm_response=narration,
            prompt_snapshot=full_prompt,
            timestamp=datetime.utcnow()
        )
        db.add(turn_entry)
        db.commit()

        # Store both player input and GM output in memory
        chunk_and_store(f"Player: {player_input}\nGM: {narration}", session_id)
        update_conversation_context(db, session_id, player_input, narration)
        # Trigger simulation only if flagged or timer threshold reached
        if run_sim or sim_counter >= SIMULATION_TURN_THRESHOLD:
            run_simulation_pass(db, session_id)
            evaluate_player_growth(db, session_id)  # ✅ Now runs on same tick
            sim_counter = 0
