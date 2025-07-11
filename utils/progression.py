# utils/progression.py (Upgraded)

import json
from sqlalchemy.orm import Session as DBSession
from db.schema import PlayerState, Turn
from gemini_interface.gemini_client import call_gemini_with_tools # Import our Gemini client
from sqlalchemy import desc

def evaluate_player_growth(db: DBSession, session_id: int, recent_turns: int = 5):
    """
    Evaluates the player's recent actions and calls the update_player_character tool
    to apply any deserved progression.
    """
    player = db.query(PlayerState).filter_by(session_id=session_id).first()
    if not player:
        print("⚠️ No player state found.")
        return

    turns = (
        db.query(Turn)
        .filter_by(session_id=session_id)
        .order_by(desc(Turn.turn_number))
        .limit(recent_turns)
        .all()
    )
    turn_summary = "\n\n".join(
        f"Player: {t.player_input}\nGM: {t.gm_response}" for t in turns
    )

    prompt = f"""
You are managing player progression in a long-term RPG campaign.
Based on the player's recent actions, decide if they have earned any skill increases, new items, or new limitations.
Only increase skill levels if justified. Typical growth is +1 to +5.
Use the 'update_player_character' tool to apply these changes.

Player info:
Name: {player.name}
Class: {player.character_class}
Current skills: {json.dumps(player.skills)}
Current inventory: {json.dumps(player.inventory)}

Recent turns:
{turn_summary}

Analyze the player's performance and use the tool if progression is warranted.
"""

    print("\n--- Evaluating Player Progression ---")
    final_response = call_gemini_with_tools(db, session_id, prompt)
    print(f"Progression result: {final_response}")
    print("--- Progression Evaluation Complete ---")