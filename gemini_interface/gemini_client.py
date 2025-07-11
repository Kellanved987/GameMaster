# gemini_interface/gemini_client.py

import os
import google.generativeai as genai
from functools import partial
from world_tools import AVAILABLE_TOOLS

# Make sure to set your GOOGLE_API_KEY in your .env file
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def call_gemini_with_tools(db_session, session_id, prompt: str):
    """
    Calls the Gemini model, providing it with tools.
    If db_session and session_id are provided, it binds them to the tools that need them.
    """
    bound_tools = {}

    # Bind tools that require a database session only if one is provided
    if db_session and session_id is not None:
        # Create partial functions for each tool that needs the database
        for name, func in AVAILABLE_TOOLS.items():
            # A simple way to check if a tool needs the db is by its name for now
            if name != 'select_relevant_memories':
                bound_tools[name] = partial(func, db_session, session_id)

    # Always include tools that do not require a database session
    if 'select_relevant_memories' in AVAILABLE_TOOLS:
        bound_tools['select_relevant_memories'] = AVAILABLE_TOOLS['select_relevant_memories']

    # If no tools are applicable (e.g., no db_session and only db tools exist), handle gracefully
    if not bound_tools:
        print("Warning: No applicable tools for this call.")
        # Fallback to a model without tools if none are bound
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text

    # Configure the model with the appropriate set of tools
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=list(bound_tools.values()) # Pass the list of function objects
    )

    # Start the chat with automatic function calling enabled
    chat = model.start_chat(enable_automatic_function_calling=True)
    response = chat.send_message(prompt)

    # Log the tool calls for debugging purposes
    final_response = response.text
    for content in chat.history:
        if content.role == 'model' and content.parts:
            for part in content.parts:
                if part.function_call:
                    fc = part.function_call
                    print(f"Tool call executed: {fc.name} with args: {dict(fc.args)}")
                # If a tool returns a result (like our relevance filter), capture it
                elif part.function_response:
                    # This is how we get the direct return value from a non-db tool
                    if part.function_response.name == 'select_relevant_memories':
                        final_response = part.function_response.response['result']


    return final_response