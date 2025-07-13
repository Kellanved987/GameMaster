# utils/simulation.py

from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
# --- FIX: Import the GPT client ---
from gpt_interface.gpt_client import call_chat_model
# --- FIX: We also need the Gemini client for its tool-calling ability ---
from gemini_interface.gemini_client import call_gemini_with_tools
from db.schema import NPC, Turn, ConversationContext

NPC_SIMULATION_LIMIT = 5

def run_simulation_pass(db: DBSession, session_id: int):
    """
    Runs a per-NPC simulation pass. Each key NPC gets a "turn" to act based on
    their individual motivation and the recent actions of the player.
    """
    # ... (code to get context and key_npcs remains the same) ...
    # ...

    for npc in key_npcs:
        print(f"\n  > Simulating for: {npc.name} (Motivation: {npc.motivation})")

        # --- FIX: This prompt is now structured for GPT-4o's reasoning ---
        prompt = f"""
You are simulating the off-screen actions for a single NPC in an RPG.

**NPC Profile:**
- Name: {npc.name}
- Role: {npc.role}
- Status: {npc.status}
- Motivation: "{npc.motivation}"

**Recent Game Events:**
{context_text}

Based on the NPC's motivation and the recent events, what is a single, significant action they have taken in the background? Describe it in one sentence. For example: "The guard captain has doubled the patrols near the old warehouse." If they have not done anything noteworthy, just say "No significant action."
"""
        print("\n--- Simulating NPC Actions (GPT-4o) ---")
        npc_action_description = call_chat_model([{"role": "user", "content": prompt}], model="gpt4o")

        # --- FIX: We use the description from GPT-4o to drive the tool call with Gemini ---
        if "no significant action" not in npc_action_description.lower():
            tool_prompt = f"""
            An NPC has taken a background action. Based on the description below, call the most appropriate tool to update the game state.

            Action Description: "{npc_action_description}"
            
            Available Tools: `update_npc_status`, `update_quest_status`, `create_rumor`, `set_world_flag`.
            """
            npc_action_response = call_gemini_with_tools(db, session_id, tool_prompt, model_name='gemini-2.5-flash', return_after_tools=True)
            print(f"    Result for {npc.name}: {npc_action_response}")
        else:
            print(f"    Result for {npc.name}: No significant actions taken.")

    print("\n--- Simulation Pass Complete ---")