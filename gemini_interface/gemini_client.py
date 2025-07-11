# gemini_interface/gemini_client.py

import os
import google.generativeai as genai
from world_tools import AVAILABLE_TOOLS

# Configure the client once
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def call_gemini_with_tools(db_session, session_id, prompt: str):
    """
    Calls the Gemini model with a set of tools, then manually executes any function
    calls the model requests by injecting the necessary database context.
    """
    # We pass the raw, unwrapped functions to the model.
    # The library can now correctly inspect their signatures and docstrings.
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=list(AVAILABLE_TOOLS.values())
    )

    chat = model.start_chat()
    # Send the initial prompt to the model
    response = chat.send_message(prompt)

    # Check if the model's first response contains a function call
    try:
        tool_calls = response.candidates[0].content.parts[0].function_calls
    except (ValueError, AttributeError, IndexError):
        # No tool call was made, just return the text response from the first turn
        return response.text

    # If we are here, the model wants to call one or more tools.
    # We now manually execute them.
    for tool_call in tool_calls:
        func_name = tool_call.name
        print(f"Model wants to call tool: {func_name} with args: {dict(tool_call.args)}")
        
        if func_name in AVAILABLE_TOOLS:
            func_to_call = AVAILABLE_TOOLS[func_name]
            args = dict(tool_call.args)

            # --- This is the key change ---
            # We inject the database context here, during execution, not declaration.
            # A simple heuristic: if it's not the memory filter, it probably needs the db.
            if func_name not in ['select_relevant_memories']:
                args['db_session'] = db_session
                if session_id is not None:
                   args['session_id'] = session_id
            
            # Execute the function with the combined arguments
            result = func_to_call(**args)
            
            # Send the result of our function call back to the model
            response = chat.send_message(
                genai.Part(function_response=genai.protos.FunctionResponse(name=func_name, response={'result': result})),
            )
        else:
            # If the model hallucinates a function that doesn't exist
            response = chat.send_message(
                genai.Part(function_response=genai.protos.FunctionResponse(name=func_name, response={'error': 'Tool not found.'})),
            )

    # The final response from the model after processing the tool results
    return response.text