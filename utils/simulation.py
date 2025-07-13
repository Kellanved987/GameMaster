# utils/simulation.py

from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from gpt_interface.gpt_client import call_chat_model
from gemini_interface.gemini_client import call_gemini_with_tools
from db.schema import NPC, Turn, ConversationContext

NPC_SIMULATION_LIMIT = 5

def run_simulation_pass(db: DBSession, session_id: int):
    """
    Runs a per-NPC simulation pass. Each key NPC gets a "turn" to act based on
    their individual motivation and the recent actions of the player.
    """
    print("\n--- Running Per-NPC Simulation Pass ---")

    recent_turns = db.query(Turn).filter_by(session_id=session_id)\
        .order_by(desc(Turn.turn_number)).limit(5).all()
    context_text = "\n".join(
        f"Turn {t.turn_number}: Player - {t.player_input.strip()} / GM - {t.gm_response.strip()}"
        for t in reversed(recent_turns)
    )

    key_npcs = (
        db.query(NPC)
        .join(ConversationContext, NPC.id == ConversationContext.npc_id)
        .filter(NPC.session_id == session_id)
        .order_by(desc(ConversationContext.last_updated))
        .limit(NPC_SIMULATION_LIMIT)
        .all()
    )

    if not key_npcs:
        print("No recently interacted-with NPCs found. Falling back to most recently created NPCs.")
        key_npcs = db.query(NPC).filter_by(session_id=session_id)\
            .order_by(desc(NPC.id)).limit(NPC_SIMULATION_LIMIT).all()

    if not key_npcs:
        print("No key NPCs found to simulate.")
        print("--- Simulation Pass Complete ---")
        return

    print(f"Simulating agency for {len(key_npcs)} key NPC(s)...")

    for npc in key_npcs:
        print(f"\n  > Simulating for: {npc.name} (Motivation: {npc.motivation})")

        prompt = f"""
You are simulating the off-screen actions for a single NPC in an RPG.

**Game World Key:**
- Power Level Scale: 1 (Child) to 100 (God-like Entity).

**NPC Profile:**
- Name: {npc.name}
- Role: {npc.role}
- Status: {npc.status}
- Motivation: "{npc.motivation}"
- Power Level: {npc.power_level}

**Recent Game Events:**
{context_text}

Based on the NPC's profile and the recent events, what is a single, significant action they have taken in the background? A higher power level NPC should be capable of more impactful actions. Describe it in one sentence. For example: "The guard captain (Power: 55) has doubled the patrols near the old warehouse." If they have not done anything noteworthy, just say "No significant action."
"""
        print("\n--- Simulating NPC Actions (GPT-4o) ---")
        npc_action_description = call_chat_model([{"role": "user", "content": prompt}], model="gpt4o")

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
