# utils/simulation.py

from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from gemini_interface.gemini_client import call_gemini_with_tools
# Import all necessary schema objects
from db.schema import NPC, Turn, ConversationContext

# We'll simulate the top 5 most relevant NPCs to keep the simulation focused
NPC_SIMULATION_LIMIT = 5

def run_simulation_pass(db: DBSession, session_id: int):
    """
    Runs a per-NPC simulation pass. Each key NPC gets a "turn" to act based on
    their individual motivation and the recent actions of the player.
    """
    print("\n--- Running Per-NPC Simulation Pass ---")

    # Get the context of recent events
    recent_turns = db.query(Turn).filter_by(session_id=session_id)\
        .order_by(desc(Turn.turn_number)).limit(5).all()
    context_text = "\n".join(
        f"Turn {t.turn_number}: Player - {t.player_input.strip()} / GM - {t.gm_response.strip()}"
        for t in reversed(recent_turns)
    )

    # --- REFINED NPC SELECTION ---
    # Find NPCs the player has recently interacted with by joining with ConversationContext
    key_npcs = (
        db.query(NPC)
        .join(ConversationContext, NPC.id == ConversationContext.npc_id)
        .filter(NPC.session_id == session_id)
        .order_by(desc(ConversationContext.last_updated))
        .limit(NPC_SIMULATION_LIMIT)
        .all()
    )

    # If no interactions have occurred yet, fall back to the most recently created NPCs
    if not key_npcs:
        print("No recently interacted-with NPCs found. Falling back to most recently created NPCs.")
        key_npcs = db.query(NPC).filter_by(session_id=session_id)\
            .order_by(desc(NPC.id)).limit(NPC_SIMULATION_LIMIT).all()

    if not key_npcs:
        print("No key NPCs found to simulate.")
        print("--- Simulation Pass Complete ---")
        return

    print(f"Simulating agency for {len(key_npcs)} key NPC(s)...")

    # Loop through each key NPC and give them a "turn"
    for npc in key_npcs:
        print(f"\n  > Simulating for: {npc.name} (Motivation: {npc.motivation})")

        prompt = f"""
You are simulating the off-screen actions for a single NPC in an RPG.

NPC Profile:
- Name: {npc.name}
- Role: {npc.role}
- Current Status: {npc.status}
- Core Motivation: "{npc.motivation}"

Recent Game Events (from the player's perspective):
{context_text}

Considering this NPC's core motivation and the recent events, what have they been doing in the background?
Have the player's actions caused them to act? Have they made progress on a personal goal?
- If they took a significant action, use a tool to update the world state (e.g., update their own status, a quest, or a world flag).
- If their core motivation might have shifted due to dramatic events, use the `update_npc_motivation` tool.
- If they have not done anything noteworthy, simply respond with "No significant actions taken at this time."
"""
        # This call will use the AI to decide if this specific NPC should do anything
        npc_action_response = call_gemini_with_tools(db, session_id, prompt)
        print(f"    Result for {npc.name}: {npc_action_response}")

    print("\n--- Simulation Pass Complete ---")