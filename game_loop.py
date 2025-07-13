# game_loop.py

import json
import re
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from datetime import datetime

# Adjusted imports for the new architecture
from prompt_builder.builder import build_prompt
from gemini_interface.gemini_client import call_gemini_with_tools
from gpt_interface.gpt_client import call_chat_model
from db.schema import Turn
from memory.ingest import chunk_and_store
from utils.simulation import run_simulation_pass
from utils.progression import evaluate_player_growth
from world_tools import FUNCTION_HANDLERS # Import the function handlers directly

SIMULATION_TURN_THRESHOLD = 5

def run_game_turn(db: DBSession, session_id: int, player_input: str):
    """
    Runs a single turn of the game using a two-step "Logic -> Narration" pipeline.
    """
    turn_counter = db.query(Turn).filter_by(session_id=session_id).count() + 1
    
    # --- STEP 1: THE LOGIC ENGINE (Gemini 2.5 Pro) ---
    print("\n--- Running Logic Engine ---")
    logic_prompt_context = build_prompt(db, session_id, player_input)
    
    logic_prompt = f"""
You are the Logic Engine for a text-based RPG. Your job is to be a strict rules referee.
Based on the provided game state and player input, determine the outcome of the player's action.

**Your Task:**
1.  **Analyze Feasibility:** First, analyze the [Player Input] against the [Player Character Sheet]. Is the action possible?
2.  **Determine Outcome:** Decide if the action succeeds, fails, or partially succeeds.
3.  **Identify Tool Calls:** Determine if any world state changes are necessary and identify the appropriate tools to call.
4.  **Return JSON:** You MUST respond with ONLY a single, valid JSON object containing the following keys:
    - `outcome_summary`: A brief, one-sentence description of what happened. (e.g., "The player successfully picks the lock.")
    - `tool_calls`: A list of any necessary tool call objects. Each object must have a `name` and `args`.

**Game State:**
{logic_prompt_context}
"""
    
    logic_response_text = call_gemini_with_tools(db, session_id, messages=[{"role": "user", "content": logic_prompt}])
    
    try:
        match = re.search(r"\{.*\}", logic_response_text, re.DOTALL)
        if match:
            clean_json_string = match.group(0)
            logic_result = json.loads(clean_json_string)
        else:
            raise json.JSONDecodeError("No JSON object found in the response.", logic_response_text, 0)
            
    except json.JSONDecodeError:
        print(f"ERROR: Logic Engine did not return valid JSON. Response:\n{logic_response_text}")
        logic_result = {"outcome_summary": "The world seems to shift in response to your action, but the details are unclear.", "tool_calls": []}

    # --- STEP 2: THE NARRATOR (GPT-4o) ---
    print("\n--- Running Narrator ---")
    
    summary = logic_result.get('outcome_summary', 'Something unexpected happens.')
    
    # --- THIS IS THE FIX ---
    # The narrator now receives the full game context in addition to the event summary.
    narration_prompt = f"""
You are a master storyteller and cinematic AI Game Master.
Your only job is to take the following event summary and turn it into an engaging, immersive, and well-written narrative of 2-3 paragraphs.
You MUST use the provided Game State context to inform your narration. The story must be consistent with the recent dialogue, character sheets, and world state.
Do not break character or mention game mechanics.

**Event to Narrate:**
{summary}

**Full Game State Context:**
{logic_prompt_context}
"""
    narration = call_chat_model([{"role": "user", "content": narration_prompt}], model="gpt4o")

    # --- STEP 3: EXECUTE TOOL CALLS & LOGGING ---
    print("\n--- Executing World Reactions ---")
    if logic_result.get("tool_calls"):
        for tool_call in logic_result["tool_calls"]:
            func_name = tool_call.get("name")
            args = tool_call.get("args", {})
            
            if func_name in FUNCTION_HANDLERS:
                func_to_call = FUNCTION_HANDLERS[func_name]
                args['db_session'] = db
                args['session_id'] = session_id
                if func_name == 'create_journal_entry' and 'turn_number' not in args:
                    args['turn_number'] = turn_counter

                try:
                    print(f"Executing tool: {func_name} with args: {args}")
                    func_to_call(**args)
                except TypeError as e:
                    print(f"ERROR executing tool {func_name}: {e}")
            else:
                print(f"Warning: Logic Engine tried to call unknown tool '{func_name}'")
            
    print("--- World Reaction Check Complete ---")

    # --- DATABASE LOGGING ---
    turn_entry = Turn(
        session_id=session_id,
        turn_number=turn_counter,
        player_input=player_input,
        gm_response=narration,
        prompt_snapshot=logic_prompt_context,
        timestamp=datetime.utcnow()
    )
    db.add(turn_entry)
    db.commit()

    # --- MEMORY & CONTEXT ---
    chunk_and_store(f"Player: {player_input}\nGM: {narration}", session_id)
    
    # --- PERIODIC SIMULATION & PROGRESSION ---
    if turn_counter % SIMULATION_TURN_THRESHOLD == 0:
        run_simulation_pass(db, session_id)
        evaluate_player_growth(db, session_id)
        
    return narration
