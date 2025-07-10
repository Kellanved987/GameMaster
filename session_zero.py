import json
import re
from gpt_interface.gpt_client import call_chat_model
from db.schema import Session as SessionModel, PlayerState
from sqlalchemy.orm import Session as DBSession

def prompt_user(question):
    print(f"\n{question}")
    return input("> ").strip()

def extract_json_block(text):
    """Safely extract first valid JSON block from GPT response"""
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON block found.")
    return json.loads(match.group(0))

def run_session_zero(db: DBSession):
    print("\n🎲 Welcome to Session Zero...")
    print("Let’s shape the world you’ll be adventuring in.")

    genre = prompt_user("What genre do you want? (e.g., fantasy, sci-fi, horror)")
    tone = prompt_user("What should the tone be? (e.g., dark, heroic, comedic)")
    realism = prompt_user("Should the world follow grounded realism? (yes/no)").lower() in ["yes", "y"]
    pf = prompt_user("Enable power fantasy mode (you rarely fail)? (yes/no)").lower() in ["yes", "y"]

    config_text = f"Genre: {genre}\nTone: {tone}\nRealism: {realism}\nPower Fantasy: {pf}"

    # Generate world intro
    world_intro = call_chat_model(
        messages=[
            {
                "role": "system",
                "content": "You are a cinematic RPG narrator. Create a compelling introduction to a new world based on the following configuration."
            },
            {
                "role": "user",
                "content": f"Create a short world introduction:\n{config_text}"
            }
        ],
        model="gpt4o",
        temperature=0.9,
        max_tokens=400
    )

    print("\n🎬 Your world is ready:\n")
    print(world_intro)

    # Save session
    new_session = SessionModel(
        genre=genre,
        tone=tone,
        realism=realism,
        power_fantasy=pf
    )
    db.add(new_session)
    db.commit()

    # Generate player state
    player_prompt = f"""Based on the following world intro, generate a player character in JSON:

{world_intro}

Use this format:
{{
  "name": "...",
  "race": "...",
  "character_class": "...",
  "backstory": "...",
  "attributes": {{
    "strength": 10,
    "dexterity": 10,
    "intelligence": 10
  }},
  "skills": {{
    "Tracking": 50,
    "Herbalism": 40
  }},
  "inventory": ["item1", "item2"],
  "limitations": ["flaw1", "flaw2"]
}}

Narrative explanation (optional) should come AFTER the JSON block.
"""

    raw_player_state = call_chat_model(
        messages=[
            {"role": "system", "content": "Respond only in the JSON format above. Add narrative afterward if needed."},
            {"role": "user", "content": player_prompt}
        ],
        model="gpt4o",
        temperature=0.7,
        max_tokens=800
    )

    try:
        parsed = extract_json_block(raw_player_state)
        player = PlayerState(
            session_id=new_session.id,
            name=parsed["name"],
            race=parsed["race"],
            character_class=parsed["character_class"],
            backstory=parsed["backstory"],
            attributes=parsed["attributes"],
            skills=parsed["skills"],
            inventory=parsed["inventory"],
            limitations=parsed["limitations"]
        )
        db.add(player)
        db.commit()
        print(f"\n✅ Player created: {player.name}, the {player.race} {player.character_class}")
    except Exception as e:
        print("❌ Failed to parse player state:", e)
        print("Raw output:\n", raw_player_state)

    print("\n✅ Session and character setup complete. You may now begin your journey.")
