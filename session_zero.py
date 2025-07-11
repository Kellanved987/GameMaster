# session_zero.py

from sqlalchemy.orm import Session as DBSession
from gemini_interface.gemini_client import call_gemini_with_tools
from world_tools import (
    finalize_character_and_world,
    FUNCTION_HANDLERS,
    Tool,
    FunctionDeclaration,
)

# Define the minimal toolset for session zero
FINALIZE_TOOL = [
    Tool(
        function_declarations=[
            FunctionDeclaration(
                name="finalize_character_and_world",
                description=FUNCTION_HANDLERS["finalize_character_and_world"].__doc__,
                parameters={
                    "type": "object",
                    "properties": {
                        "genre": {"type": "string"},
                        "tone": {"type": "string"},
                        "world_intro": {"type": "string"},
                        "player_name": {"type": "string"},
                        "backstory": {"type": "string"},
                        "attributes": {"type": "object"},
                        "skills": {"type": "object"}, # --- CHANGED to object for skill levels
                    },
                    "required": [
                        "genre", "tone", "world_intro", "player_name",
                        "backstory", "attributes", "skills"
                    ],
                },
            )
        ]
    )
]

def run_session_zero_turn(db: DBSession, messages: list):
    """
    Processes a single turn of the Session Zero conversation using a stateful history.
    """
    # --- NEW: Updated system instruction with tiered progression rules ---
    system_instruction = {
        "role": "system",
        "content": """
You are a friendly and creative guide for Session Zero of a new text-based RPG.
Your goal is to have a natural conversation with the player to collaboratively build the game world and their character.

**Character Creation Rules:**
1.  **World First:** Establish the world's genre, tone, and a brief description.
2.  **Character Concept:** Work with the player on their character's name and backstory.
3.  **Mechanics - Skills:**
    - The game uses a 1-100 skill system with six mastery tiers (Novice, Apprentice, Adept, Expert, Master, Grandmaster).
    - Based on the character's backstory, suggest 3-5 starting skills.
    - Assign a starting value between 5 and 15 to each of these skills. Higher values should be for skills more central to their backstory.
4.  **Mechanics - Attributes:**
    - For attributes (strength, dexterity, intelligence, charisma, wisdom, constitution), suggest a balanced array like 14, 13, 12, 11, 10, 8 to be assigned, but let the player adjust them.
5.  **Finalize:** Once the player is happy, summarize everything and call the `finalize_character_and_world` tool.

Ask one open-ended question at a time. Be engaging and conversational.
"""
    }

    # Combine system instruction with the message history
    full_history = [system_instruction] + messages

    response_text = call_gemini_with_tools(
        db, None, messages=full_history, tools=FINALIZE_TOOL
    )

    return response_text