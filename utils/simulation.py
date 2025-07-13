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

        # --- FIX: Made the prompt instructions even more explicit to prevent errors ---
        prompt = f"""
You are simulating the off-screen actions for a single NPC in an RPG.

**NPC Profile:**
- Name: {npc.name}
- Role: {npc.role}
- Current Status: {npc.status}
- Core Motivation: "{npc.motivation}"

**Recent Game Events:**
{context_text}

**Your Task:**
Based on the NPC's profile and recent events, decide if they have taken any significant action in the background.

1.  **Analyze:** Has the player's actions or the unfolding story caused this NPC to act on their motivation?
2.  **Act:** If the NPC has done something significant, call ONE of the following tools with a clear `reason`:
    * `update_npc_status(npc_name, new_status, reason)`
    * `update_quest_status(quest_name, new_status, reason)`
    * `create_rumor(rumor_content, is_confirmed)`
    * `set_world_flag(key, value, reason)`
    * `update_npc_motivation(npc_name, new_motivation, reason)`
3.  **Idle:** If the NPC has not done anything noteworthy, you MUST respond with the exact phrase: "No significant actions taken."

Do not invent new tools. Only use the tools provided.
"""
        # This call will use the AI to decide if this specific NPC should do anything
        npc_action_response = call_gemini_with_tools(db, session_id, prompt, model_name='gemini-1.5-flash-latest')
        print(f"    Result for {npc.name}: {npc_action_response}")

    print("\n--- Simulation Pass Complete ---")