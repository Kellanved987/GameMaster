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
    executes any function calls the model requests in a loop.
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
    
    # Send the last message to start the conversation
    response = chat.send_message(gemini_history[-1]['parts'][0]['text'])

    # Loop to handle a multi-turn conversation with tool calls
    while True:
        # Check if there are any function calls in any part of the response
        has_function_calls = False
        tool_calls = []
        
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    has_function_calls = True
                    tool_calls.append(part.function_call)
        
        # If no function calls are found, we can safely return the text
        if not has_function_calls:
            try:
                return response.text
            except ValueError:
                # If we still can't get text, extract it manually from parts
                text_parts = []
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                return ''.join(text_parts) if text_parts else "No text response available"

        # Process function calls
        api_responses = []
        for tool_call in tool_calls:
            func_name = tool_call.name
            print(f"Model wants to call tool: {func_name} with args: {dict(tool_call.args)}")

            if func_name in FUNCTION_HANDLERS:
                func_to_call = FUNCTION_HANDLERS[func_name]
                args = dict(tool_call.args)

                # Inject database context where needed
                if func_name not in ['select_relevant_memories']:
                    args['db_session'] = db_session
                    if func_name not in ['finalize_character_and_world']:
                        args['session_id'] = session_id
                
                # Execute the function
                result = func_to_call(**args)
                
                # If this was the finalization tool, its result is the final answer.
                if func_name == 'finalize_character_and_world':
                    return result
                
                # For other tools, collect the results to send back to the model
                api_responses.append(
                    genai.Part(function_response=genai.protos.FunctionResponse(name=func_name, response={'result': result}))
                )
            else:
                # Handle cases where the model hallucinates a tool name
                api_responses.append(
                    genai.Part(function_response=genai.protos.FunctionResponse(name=func_name, response={'error': 'Tool not found.'}))
                )
        
        # Send the collected tool responses back to the model to continue the conversation
        response = chat.send_message(api_responses)