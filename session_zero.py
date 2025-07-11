# session_zero.py

from sqlalchemy.orm import Session as DBSession
from gemini_interface.gemini_client import call_gemini_with_tools

def run_session_zero_turn(db: DBSession, chat_history: str, player_input: str):
    """
    Processes a single turn of the Session Zero conversation.
    """
    system_instruction = """
You are a friendly and creative guide for Session Zero of a new text-based RPG.
Your goal is to have a natural conversation with the player to collaboratively build the game world and their character.
Do NOT ask a list of questions. Ask one open-ended question at a time, then ask clarifying follow-up questions based on the player's response.
First, establish the world's genre, tone, and a brief description.
Second, work with the player to create their character concept, name, and backstory.
Third, help them define their character's mechanics. Suggest 3-5 starting skills based on their backstory. For attributes (strength, dexterity, intelligence, charisma, wisdom, constitution), suggest a balanced array like 14, 13, 12, 11, 10, 8 to be assigned, but allow the player to adjust them.
Finally, once the player is happy with everything, summarize all the details and call the `finalize_character_and_world` tool to officially create the character and start the game.
Be engaging, creative, and conversational.
"""
    # Construct the full prompt for the AI
    full_prompt = f"{system_instruction}\n\n--- Conversation History ---\n{chat_history}\n--- Your Turn ---\nPlayer: {player_input}\nGuide:"
    
    # Call the Gemini client. We pass `None` for session_id because it doesn't exist yet.
    # The client will correctly handle this and only inject it into tools that need it if it's not None.
    response_text = call_gemini_with_tools(db, None, full_prompt)
    
    return response_text