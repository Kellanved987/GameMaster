# gemini_interface/gemini_client.py

import os
import google.generativeai as genai
from dotenv import load_dotenv
from world_tools import WORLD_TOOLS_LIST, FUNCTION_HANDLERS

# Load environment variables from .env file
load_dotenv()

# Configure the client once at the module level
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_model(model_name='gemini-2.5-pro', tools=WORLD_TOOLS_LIST, system_instruction=None):
    """Initializes and returns a Gemini model with a specific toolset and system instruction."""
    return genai.GenerativeModel(
        model_name=model_name,
        tools=tools,
        system_instruction=system_instruction
    )

def call_gemini_with_tools(db_session, session_id, messages, model_name='gemini-2.5-pro', tools=WORLD_TOOLS_LIST):
    """
    Calls the Gemini model with a set of tools and a message history, then manually
    executes any function calls the model requests in a loop.
    """
    # 1. SETUP
    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    elif not isinstance(messages, list):
        raise ValueError(f"messages must be a list or string, got {type(messages)}")
    
    system_instruction = None
    if messages and isinstance(messages[0], dict) and messages[0].get('role') == 'system':
        system_instruction = messages[0]['content']
        history = messages[1:]
    else:
        history = messages

    gemini_history = []
    for msg in history:
        role = 'model' if msg['role'] == 'assistant' else 'user'
        gemini_history.append({'role': role, 'parts': [{'text': msg['content']}]})

    model = get_model(model_name=model_name, tools=tools, system_instruction=system_instruction)
    chat = model.start_chat(history=gemini_history[:-1] if gemini_history else [])
    
    if not gemini_history:
        return "No message to process."
        
    response = chat.send_message(gemini_history[-1]['parts'][0]['text'])

    max_iterations = 10
    iteration_count = 0
    
    while iteration_count < max_iterations:
        tool_calls = []
        if (response.candidates and 
            len(response.candidates) > 0 and 
            response.candidates[0].content and
            response.candidates[0].content.parts):
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    tool_calls.append(part.function_call)

        if not tool_calls:
            break

        iteration_count += 1
        api_responses = []

        for tool_call in tool_calls:
            func_name = tool_call.name
            print(f"Model wants to call tool: {func_name} with args: {dict(tool_call.args)}")

            if func_name in FUNCTION_HANDLERS:
                func_to_call = FUNCTION_HANDLERS[func_name]
                args = dict(tool_call.args)

                if func_name not in ['select_relevant_memories']:
                    args['db_session'] = db_session
                    if func_name not in ['finalize_character_and_world']:
                        args['session_id'] = session_id
                
                result = func_to_call(**args)
                
                # --- THIS IS THE FIX ---
                # Added 'select_relevant_memories' to the list of tools that should
                # immediately return their result instead of continuing the loop.
                if func_name in ['finalize_character_and_world', 'select_relevant_memories']:
                    return result
                
                api_responses.append({
                    "function_response": {
                        "name": func_name,
                        "response": {"result": result},
                    }
                })
            else:
                api_responses.append({
                    "function_response": {
                        "name": func_name,
                        "response": {"error": "Tool not found."},
                    }
                })
        
        if api_responses:
            response = chat.send_message(api_responses)
        else:
            break
            
    if iteration_count >= max_iterations:
        error_message = f"ERROR: Loop stopper triggered after {max_iterations} iterations. The last attempted tool call was likely part of a loop. Please check the console logs for details."
        print(error_message)
        return error_message

    try:
        return response.text
    except ValueError as e:
        print(f"Error getting response text: {e}")
        text_parts = []
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
        return ''.join(text_parts) if text_parts else "I encountered an issue processing your request. Please try again."