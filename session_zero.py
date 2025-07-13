# session_zero.py

from sqlalchemy.orm import Session as DBSession
from gemini_interface.gemini_client import call_gemini_with_tools
# This now correctly imports the main tool list from its proper source.
from world_tools import WORLD_TOOLS_LIST

def run_session_zero_turn(db: DBSession, messages: list):
    """
    Processes a single turn of the Session Zero conversation using a stateful history.
    """
    system_instruction = {
        "role": "system",
        "content": """
You are a friendly and creative guide for Session Zero of a new text-based RPG.
Your goal is to have a natural conversation with the player to collaboratively build the game world and their character.

**Character Creation Rules:**
1.  **World First:** Establish the world's genre, tone, and a brief description.
2.  **Character Concept:** Work with the player on their character's name and backstory.
3.  **Mechanics - Skills:**
    - The game uses a 1-100 skill system. Based on the backstory, suggest 3-5 starting skills with values between 5 and 15.
4.  **Mechanics - Attributes:**
    - For attributes (strength, dexterity, intelligence, charisma, wisdom, constitution), suggest a balanced array like 14, 13, 12, 11, 10, 8 to be assigned, but let the player adjust them.
5.  **Finalize:** Once the player is happy, summarize everything and call the `finalize_character_and_world` tool.

Ask one open-ended question at a time. Be engaging and conversational.
"""
    }

    # Combine system instruction with the message history
    full_history = [system_instruction] + messages

    # The call now correctly uses the imported WORLD_TOOLS_LIST
    response_text = call_gemini_with_tools(
        db, None, messages=full_history, tools=WORLD_TOOLS_LIST
    )

    return response_text