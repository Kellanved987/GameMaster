# utils/progression.py

import json
from sqlalchemy.orm import Session as DBSession
from db.schema import PlayerState, Turn
# --- FIX: Import the GPT client ---
from gpt_interface.gpt_client import call_chat_model
# --- FIX: We also need the Gemini client for its tool-calling ability ---
from gemini_interface.gemini_client import call_gemini_with_tools
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

    # --- FIX: This prompt is now structured for GPT-4o's reasoning ---
    prompt = f"""
You are managing player progression in an RPG. Your job is to analyze the player's recent actions and decide if they have earned a skill increase.

**Rules:**
- Award small, incremental skill increases (+1 to +3) for successfully using a skill.
- If a skill increase pushes them into a new tier (Novice > Apprentice > Adept > Expert > Master), mention it in your reasoning.

**Player Info:**
- Name: {player.name}
- Class: {player.character_class}
- Current Skills: {json.dumps(player.skills)}

**Recent Turns:**
{turn_summary}

Based on the rules and recent turns, provide a brief, one-sentence rationale for any skill increases. For example: "Tayschrenn successfully used necromancy to raise a corpse." If no progression is warranted, just say "No progression."
"""
    print("\n--- Evaluating Player Progression (GPT-4o) ---")
    reasoning = call_chat_model([{"role": "user", "content": prompt}], model="gpt4o")

    # --- FIX: We use the reasoning from GPT-4o to drive the tool call with Gemini ---
    if "no progression" not in reasoning.lower():
        tool_prompt = f"""
        Based on the following rationale, call the `update_player_character` tool to apply the earned progression.

        Rationale: "{reasoning}"

        Current Skills: {json.dumps(player.skills)}
        """
        final_response = call_gemini_with_tools(db, session_id, [{"role": "user", "content": tool_prompt}])
        print(f"Progression result: {final_response}")
    else:
        print("Progression result: No progression earned.")
        
    print("--- Progression Evaluation Complete ---")