# gemini_interface/gemini_client.py

import os
import google.generativeai as genai
from dotenv import load_dotenv
from world_tools import WORLD_TOOLS_LIST, FUNCTION_HANDLERS

# Load environment variables from .env file
load_dotenv()

# Configure the client once at the module level
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_model(tools=WORLD_TOOLS_LIST, system_instruction=None):
    """Initializes and returns a Gemini model with a specific toolset and system instruction."""
    return genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=tools,
        system_instruction=system_instruction
    )

def call_gemini_with_tools(db_session, session_id, messages: list, tools=WORLD_TOOLS_LIST):
    """
    Calls the Gemini model with a set of tools and a message history, then manually
    executes any function calls the model requests.
    """
    system_instruction = None
    if messages and messages[0]['role'] == 'system':
        system_instruction = messages[0]['content']
        history = messages[1:]
    else:
        history = messages

    gemini_history = []
    for msg in history:
        role = 'model' if msg['role'] == 'assistant' else 'user'
        gemini_history.append({'role': role, 'parts': [{'text': msg['content']}]})

    model = get_model(tools=tools, system_instruction=system_instruction)
    
    chat = model.start_chat(history=gemini_history[:-1])
    
    response = chat.send_message(gemini_history[-1]['parts'][0]['text'])

    try:
        tool_calls = response.candidates[0].content.parts[0].function_calls
    except (ValueError, AttributeError, IndexError):
        return response.text

    for tool_call in tool_calls:
        func_name = tool_call.name
        print(f"Model wants to call tool: {func_name} with args: {dict(tool_call.args)}")
        
        if func_name in FUNCTION_HANDLERS:
            func_to_call = FUNCTION_HANDLERS[func_name]
            args = dict(tool_call.args)

            if func_name not in ['select_relevant_memories']:
                if func_name not in ['finalize_character_and_world']:
                    args['session_id'] = session_id
                args['db_session'] = db_session
            
            result = func_to_call(**args)
            
            # --- NEW: Immediately return the result for the finalize tool ---
            if func_name == 'finalize_character_and_world':
                return result

            response = chat.send_message(
                genai.Part(function_response=genai.protos.FunctionResponse(name=func_name, response={'result': result})),
            )
        else:
            response = chat.send_message(
                genai.Part(function_response=genai.protos.FunctionResponse(name=func_name, response={'error': 'Tool not found.'})),
            )

    return response.text