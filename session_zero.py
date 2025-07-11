# session_zero.py

import os
import google.generativeai as genai
from functools import partial
from world_tools import AVAILABLE_TOOLS
from sqlalchemy.orm import Session as DBSession

def run_conversational_session_zero(db: DBSession):
    """
    Runs a conversational, interactive session zero to build the world and character.
    """
    # Configure the Gemini client for this specific task
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    # Create partial functions for our tools
    bound_tools = {
        name: partial(func, db) for name, func in AVAILABLE_TOOLS.items()
    }
    model = genai.GenerativeModel(
        model_name='gemini-1.5-pro', # Use a powerful model for this creative task
        tools=bound_tools.values(),
        system_instruction="""
You are a friendly and creative guide for Session Zero of a new text-based RPG.
Your goal is to have a natural conversation with the player to collaboratively build the game world and their character.
Do NOT ask a list of questions. Ask one open-ended question at a time, then ask clarifying follow-up questions based on the player's response.
First, establish the world's genre, tone, and a brief description.
Second, work with the player to create their character concept, name, and backstory.
Third, help them define their character's mechanics. Suggest 3-5 starting skills based on their backstory. For attributes (strength, dexterity, intelligence, charisma, wisdom, constitution), suggest a balanced array like 14, 13, 12, 11, 10, 8 to be assigned, but allow the player to adjust them.
Finally, once the player is happy with everything, summarize all the details and call the `finalize_character_and_world` tool to officially create the character and start the game.
Be engaging, creative, and conversational.
"""
    )
    chat = model.start_chat(enable_automatic_function_calling=True)

    print("\n\n🎲 Welcome to a new kind of Session Zero... 🎲")
    print("Let's create our world and your character together. I'll be your guide.")
    print("To start, what kind of adventure are you in the mood for? Tell me about the genre, the tone, or just a vibe you're feeling.")
    print("Type 'exit' when you are finished with Session Zero.")

    while True:
        player_input = input("\n> ").strip()
        if player_input.lower() == 'exit':
            print("Session Zero cancelled.")
            return None # Return None if cancelled

        response = chat.send_message(player_input)

        # Check if a tool was called. The "finalize" tool is our exit condition.
        was_tool_called = False
        for content in chat.history:
            if content.role == 'model' and content.parts:
                for part in content.parts:
                    if part.function_call and part.function_call.name == 'finalize_character_and_world':
                        was_tool_called = True
                        break
            if was_tool_called:
                break
        
        # The final response from the model after a tool call is in response.text
        # We can print it to show the success message.
        print(f"\nGUIDE: {response.text}")

        if was_tool_called:
            # Extract the new session_id from the success message to start the game
            try:
                # A bit of parsing to get the ID from the success message
                session_id = int(response.text.split("New session ID is ")[1])
                print("\n✅ Session and character setup complete! The adventure begins...")
                return session_id
            except (IndexError, ValueError):
                print("Error: Could not retrieve session ID after finalization. Please start a new game.")
                return None