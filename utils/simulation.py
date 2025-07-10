# utils/simulation.py

from sqlalchemy.orm import Session as DBSession
from db.schema import WorldFlag, Quest, NPC, Turn
from gpt_interface.gpt_client import call_chat_model
from sqlalchemy import desc

def run_simulation_pass(db: DBSession, session_id: int) -> dict:
    """
    Runs a simulation pass on the world state based on recent turns and flags.
    Updates relevant DB tables in-place.
    """
    # Fetch recent turns or summaries
    recent_turns = db.query(Turn).filter_by(session_id=session_id)\
        .order_by(desc(Turn.turn_number)).limit(5).all()
    context_text = "\n".join(
        f"Turn {t.turn_number}: Player - {t.player_input.strip()} / GM - {t.gm_response.strip()}"
        for t in reversed(recent_turns)
    )

    # Current world state
    flags = db.query(WorldFlag).filter_by(session_id=session_id).all()
    quests = db.query(Quest).filter_by(session_id=session_id).all()
    npcs = db.query(NPC).filter_by(session_id=session_id).all()

    system = "You are a world simulation engine for a narrative RPG. Based on player history and current world state, determine if anything changed off-screen."

    user = f"""
Recent context:
{context_text}

Current flags:
{[f"{f.key}={f.value}" for f in flags]}

Current quests:
{[f"{q.name}: {q.status}" for q in quests]}

Current NPCs:
{[f"{n.name} ({n.status})" for n in npcs]}

Which flags, NPC statuses, or quests should be updated?
Return JSON only in this format:
{{
  "flags": [{{"key": "...", "value": "..."}}],
  "quests": [{{"name": "...", "status": "..."}}],
  "npcs": [{{"name": "...", "status": "..."}}]
}}
"""

    response = call_chat_model(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user.strip()}
        ],
        model="gpt35",
        temperature=0.4,
        max_tokens=300
    )

    try:
        import json
        updates = json.loads(response)

        # Apply updates
        for f in updates.get("flags", []):
            flag = db.query(WorldFlag).filter_by(session_id=session_id, key=f["key"]).first()
            if flag: flag.value = f["value"]

        for q in updates.get("quests", []):
            quest = db.query(Quest).filter_by(session_id=session_id, name=q["name"]).first()
            if quest: quest.status = q["status"]

        for n in updates.get("npcs", []):
            npc = db.query(NPC).filter_by(session_id=session_id, name=n["name"]).first()
            if npc: npc.status = n["status"]

        db.commit()
        return updates

    except Exception as e:
        print("Simulation failed:", e)
        return {}
