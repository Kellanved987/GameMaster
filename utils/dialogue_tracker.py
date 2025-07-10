# utils/dialogue_tracker.py

from db.schema import ConversationContext
from gpt_interface.gpt_client import call_chat_model

def update_conversation_context(db, session_id: int, player_input: str, gm_response: str):
    """
    Uses GPT to extract the active NPC, topic, and recent dialogue from the exchange,
    and updates the ConversationContext table accordingly.
    """
    system = (
        "You are an assistant helping track RPG conversations. "
        "Given a player's input and the GM's response, extract the main NPC involved, "
        "the topic they discussed, and a short quote or summary of what the NPC said."
    )

    user = f"""Player input:
{player_input}

GM response:
{gm_response}

Return this JSON format:
{{
  "npc_name": "Name of NPC",
  "last_topic": "Topic of conversation",
  "recent_dialogue": "Short quote or paraphrase of what the NPC said"
}}"""

    response = call_chat_model(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user.strip()}
        ],
        model="gpt35",
        temperature=0.3,
        max_tokens=150
    )

    import json
    try:
        data = json.loads(response)
        npc_name = data["npc_name"].strip()
        topic = data["last_topic"].strip()
        snippet = data["recent_dialogue"].strip()

        # Find existing context
        context = db.query(ConversationContext).filter_by(
            session_id=session_id, npc_id=npc_name
        ).first()

        if context:
            context.last_topic = topic
            context.recent_dialogue = snippet
        else:
            context = ConversationContext(
                session_id=session_id,
                npc_id=npc_name,
                last_topic=topic,
                recent_dialogue=snippet
            )
            db.add(context)

        db.commit()
        return context

    except Exception as e:
        print("Dialogue context parse error:", e)
        return None
