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
from gemini_interface.gemini_client import call_gemini_with_tools
from sqlalchemy import desc

SIMULATION_TURN_THRESHOLD = 5

def run_game_loop(db: DBSession, session_id: int):
    session = db.query(SessionModel).get(session_id)
    if not session:
        print("Error: Session not found.")
        return

    print(f"\n🎮 Loaded session: {session.genre} - {session.tone}")
    print("Type your action. Type 'exit' to quit.\n")

    turn_counter = db.query(Turn).filter_by(session_id=session_id).count()
    sim_counter = 0

    while True:
        player_input = input("> ").strip()
        if player_input.lower() in {"exit", "quit"}:
            print("Session paused.")
            break

        # --- NEW: Dynamic Prompt Sizing ---
        is_low_stakes = len(player_input.split()) < 5 # True if input is less than 5 words

        if is_low_stakes:
            # For simple actions, use a minimal prompt and a cheaper model
            print("\n--- Low-Stakes Turn Detected ---")
            narration = call_chat_model(
                messages=[
                    {"role": "system", "content": "You are a game master. Briefly narrate the outcome of the player's simple action."},
                    {"role": "user", "content": f"Player action: {player_input}"}
                ],
                model="gpt35" # Use your cheaper/faster Azure model
            )
            run_sim = False # No need for a simulation on a simple turn
            full_prompt = f"Low-stakes action: {player_input}" # For logging purposes
        else:
            # For complex actions, use the full, detailed prompt builder and AI pipeline
            print("\n--- High-Stakes Turn Detected ---")
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
                narration = raw_response.strip()
                run_sim = False

        # --- This section now runs for both high and low stakes turns ---
        print(f"\n🧠 GM:\n{narration}")

        # --- DATABASE LOGGING ---
        turn_counter += 1
        sim_counter += 1
        turn_entry = Turn(
            session_id=session_id,
            turn_number=turn_counter,
            player_input=player_input,
            gm_response=narration,
            prompt_snapshot=full_prompt, # Log either the full or the low-stakes prompt
            timestamp=datetime.utcnow()
        )
        db.add(turn_entry)
        db.commit()

        # --- MEMORY & CONTEXT ---
        chunk_and_store(f"Player: {player_input}\nGM: {narration}", session_id)
        update_conversation_context(db, session_id, player_input, narration)

        # We only run the advanced mechanic checks on high-stakes turns
        if not is_low_stakes:
            # --- IMMEDIATE WORLD REACTION (Gemini) ---
            print("\n--- Checking for Immediate World Reactions ---")
            reaction_prompt = f"""
            The player just took an action and the GM narrated the result.
            Player Input: "{player_input}"
            GM Response: "{narration}"

            Based *only* on this immediate turn, should any world state change? If so, use a tool.
            """
            call_gemini_with_tools(db, session_id, reaction_prompt)
            print("--- World Reaction Check Complete ---")

        # --- PERIODIC SIMULATION & PROGRESSION (runs on counter) ---
        if run_sim or sim_counter >= SIMULATION_TURN_THRESHOLD:
            run_simulation_pass(db, session_id)
            evaluate_player_growth(db, session_id)
            sim_counter = 0