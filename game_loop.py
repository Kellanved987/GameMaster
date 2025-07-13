# game_loop.py

import json
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from datetime import datetime

# Adjusted imports
from prompt_builder.builder import build_prompt
from gemini_interface.gemini_client import call_gemini_with_tools
# --- FIX: We no longer need the gpt_client ---
# from gpt_interface.gpt_client import call_chat_model
from db.schema import Turn
from memory.ingest import chunk_and_store
from utils.simulation import run_simulation_pass
from utils.progression import evaluate_player_growth

SIMULATION_TURN_THRESHOLD = 5

def run_game_turn(db: DBSession, session_id: int, player_input: str):
    """
    Runs a single turn of the game, processes player input, and returns the GM response.
    """
    turn_counter = db.query(Turn).filter_by(session_id=session_id).count() + 1
    
    print("\n--- Processing Turn ---")
    full_prompt = build_prompt(db, session_id, player_input)
    
    # --- FIX: Using Gemini 2.5 Pro for the main, creative narration ---
    messages = [
        {"role": "system", "content": "You are a cinematic, immersive AI game master. Narrate the outcome of the player's action based on the detailed context provided. Do not break character."},
        {"role": "user", "content": full_prompt}
    ]
    # This now uses our updated Gemini client, which will default to the Pro model
    narration = call_gemini_with_tools(db, session_id, messages=messages)

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
    
    # --- IMMEDIATE WORLD REACTION ---
    print("\n--- Checking for Immediate World Reactions ---")
    
    reaction_prompt = f"""
    You are a game state manager. Your ONLY job is to call tools based on the last turn.

    **Last Turn:**
    - Player Input: "{player_input}"
    - GM Response: "{narration}"

    **Available Tools:**
    - `save_dialogue_context(npc_name: str, topic: str, dialogue_summary: str)`
    - `update_quest_status(quest_name: str, new_status: str, reason: str)`
    - `update_npc_status(npc_name: str, new_status: str, reason: str)`
    - `create_rumor(rumor_content: str, is_confirmed: bool)`
    - `set_world_flag(key: str, value: str, reason: str)`

    Analyze the last turn and call any necessary tools. If no tools are needed, respond with "No changes."
    Do not add any other text to your response.
    """
    call_gemini_with_tools(db, session_id, messages=reaction_prompt, return_after_tools=True)
    print("--- World Reaction Check Complete ---")

    # --- PERIODIC SIMULATION & PROGRESSION ---
    if turn_counter % SIMULATION_TURN_THRESHOLD == 0:
        run_simulation_pass(db, session_id)
        evaluate_player_growth(db, session_id)
        
    return narration