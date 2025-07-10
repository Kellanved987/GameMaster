# utils/progression.py

import json
from sqlalchemy.orm import Session as DBSession
from db.schema import PlayerState, Turn
from gpt_interface.gpt_client import call_chat_model
from sqlalchemy import desc

def evaluate_player_growth(db: DBSession, session_id: int, recent_turns: int = 5):
    player = db.query(PlayerState).filter_by(session_id=session_id).first()
    if not player:
        print("⚠️ No player state found.")
        return

    turns = (
        db.query(Turn)
        .filter_by(session_id=session_id)
        .order_by(desc(Turn.turn_number))
        .limit(recent_turns)
        .all()
    )
    turns.reverse()

    turn_summary = "\n\n".join(
        f"Player: {t.player_input}\nGM: {t.gm_response}" for t in turns
    )

    system = (
        "You are managing player progression in a long-term RPG campaign. "
        "The player has structured skills from 1 to 100. Only increase skill levels if justified by player behavior. "
        "Typical growth is +1 to +5. You may also add new skills, new inventory items, or limitations. "
        "Do NOT inflate the player's power without cause. Use the provided JSON structure."
    )

    user = f"""Player info:
Name: {player.name}
Class: {player.character_class}
Current skills: {json.dumps(player.skills, indent=2)}

Recent turns:
{turn_summary}

Respond with:
{{
  "skills": {{ "skill name": updated numeric score }},
  "inventory_add": ["optional items"],
  "limitations_add": ["optional new limitations"]
}}"""

    response = call_chat_model(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        model="gpt4o",
        temperature=0.3,
        max_tokens=400
    )

    try:
        data = json.loads(response)
        updated_skills = data.get("skills", {})
        new_items = data.get("inventory_add", [])
        new_limits = data.get("limitations_add", [])

        if updated_skills:
            for skill, new_val in updated_skills.items():
                old = player.skills.get(skill, 0)
                if new_val > old:
                    player.skills[skill] = new_val

        if new_items:
            player.inventory.extend(i for i in new_items if i not in player.inventory)

        if new_limits:
            player.limitations.extend(l for l in new_limits if l not in player.limitations)

        db.commit()
        print("✅ Player progression applied.")

    except Exception as e:
        print("❌ Failed to parse progression response:", e)
        print("Raw output:", response)
