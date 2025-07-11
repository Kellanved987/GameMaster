# game_loop.py

import json
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from datetime import datetime

# Adjusted imports to be more modular
from prompt_builder.builder import build_prompt
from gemini_interface.gemini_client import call_gemini_with_tools
from db.schema import Turn
from memory.ingest import chunk_and_store
from utils.dialogue_tracker import update_conversation_context
from utils.simulation import run_simulation_pass
from utils.progression import evaluate_player_growth
from gpt_interface.gpt_client import call_chat_model # Retaining for low-stakes turns

SIMULATION_TURN_THRESHOLD = 5

def run_game_turn(db: DBSession, session_id: int, player_input: str):
    """
    Runs a single turn of the game, processes player input, and returns the GM response.
    """
    # Get the current turn number
    turn_counter = db.query(Turn).filter_by(session_id=session_id).count() + 1
    
    # --- Dynamic Prompt Sizing Logic (from original game_loop) ---
    is_low_stakes = len(player_input.split()) < 5

    if is_low_stakes:
        print("\n--- Low-Stakes Turn Detected ---")
        narration = call_chat_model(
            messages=[
                {"role": "system", "content": "You are a game master. Briefly narrate the outcome of the player's simple action."},
                {"role": "user", "content": f"Player action: {player_input}"}
            ],
            model="gpt35"
        )
        full_prompt = f"Low-stakes action: {player_input}" # For logging
    else:
        print("\n--- High-Stakes Turn Detected ---")
        full_prompt = build_prompt(db, session_id, player_input)
        
        # In a web UI, we expect just the narration back. 
        # The decision to run a simulation can be handled separately.
        # We can simplify this call to use the gemini_client which is our main one.
        narration = call_gemini_with_tools(db, session_id, messages=[{"role": "user", "content": full_prompt}])

    # --- DATABASE LOGGING ---
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

    # --- MEMORY & CONTEXT ---
    chunk_and_store(f"Player: {player_input}\nGM: {narration}", session_id)
    update_conversation_context(db, session_id, player_input, narration)
    
    # --- IMMEDIATE WORLD REACTION ---
    if not is_low_stakes:
        print("\n--- Checking for Immediate World Reactions ---")
        reaction_prompt = f"""
        The player just took an action and the GM narrated the result.
        Player Input: "{player_input}"
        GM Response: "{narration}"
        Based *only* on this immediate turn, should any world state change? If so, use a tool.
        """
        call_gemini_with_tools(db, session_id, messages=[{"role": "user", "content": reaction_prompt}])
        print("--- World Reaction Check Complete ---")

    # --- PERIODIC SIMULATION & PROGRESSION ---
    if turn_counter % SIMULATION_TURN_THRESHOLD == 0:
        run_simulation_pass(db, session_id)
        evaluate_player_growth(db, session_id)
        
    return narration