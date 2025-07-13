# utils/dialogue_tracker.py

from sqlalchemy.orm import Session as DBSession
from gemini_interface.gemini_client import call_gemini_with_tools

def update_conversation_context(db: DBSession, session_id: int, player_input: str, gm_response: str):
    """
    Uses Gemini to extract and save the active NPC, topic, and dialogue summary.
    """
    prompt = f"""
You are an assistant helping track RPG conversations.
Given the player's input and the GM's response, extract the main NPC involved, the topic they discussed, and a short quote or summary of what the NPC said.
Then, call the `save_dialogue_context` tool with this information.

Player input:
{player_input}

GM response:
{gm_response}
"""
    # --- MODIFIED: Use the new, cheaper Flash model ---
    call_gemini_with_tools(db, session_id, messages=prompt, model_name='gemini-2.5-flash')