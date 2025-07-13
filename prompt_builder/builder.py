# prompt_builder/builder.py

import json
from memory.retrieve import retrieve_relevant_chunks
from memory.relevance_filter import filter_relevant_chunks
from db.schema import NPC, Quest, WorldFlag, Session, Turn, ConversationContext, JournalEntry, PlayerState # Import PlayerState
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc

RECENT_TURN_LIMIT = 3
JOURNAL_ENTRY_LIMIT = 5

def build_prompt(db: DBSession, session_id: int, player_input: str) -> str:
    # --- Context Gathering ---
    raw_chunks = retrieve_relevant_chunks(player_input, session_id)
    memory_chunks = filter_relevant_chunks(player_input, raw_chunks)
    memory_section = "\n".join(c["text"] for c in memory_chunks)

    recent_turns = db.query(Turn).filter_by(session_id=session_id)\
        .order_by(desc(Turn.turn_number)).limit(RECENT_TURN_LIMIT).all()
    recent_turns.reverse()
    dialogue_section = "\n".join(
        f"Player: {t.player_input}\nGM: {t.gm_response}" for t in recent_turns
    )

    journal_entries = db.query(JournalEntry).filter_by(session_id=session_id)\
        .order_by(desc(JournalEntry.turn_number)).limit(JOURNAL_ENTRY_LIMIT).all()
    journal_entries.reverse()
    journal_section = "\n".join(
        f"- {entry.entry_text}" for entry in journal_entries
    )

    player = db.query(PlayerState).filter_by(session_id=session_id).first()
    npcs = db.query(NPC).filter_by(session_id=session_id).all()
    quests = db.query(Quest).filter_by(session_id=session_id).all()
    flags = db.query(WorldFlag).filter_by(session_id=session_id).all()
    config = db.query(Session).get(session_id)
    
    player_sheet_section = ""
    if player:
        player_sheet_section = f"""
[Player Character Sheet]
- Name: {player.name}
- Class: {player.character_class}
- Attributes: {json.dumps(player.attributes)}
- Skills: {json.dumps(player.skills)}
- Inventory: {json.dumps(player.inventory)}
- Limitations: {json.dumps(player.limitations)}
"""
    
    active_quests = [q for q in quests if q.status == 'active']
    quest_focus_section = ""
    if active_quests:
        main_quest = active_quests[0]
        quest_focus_section = f"""
[Active Quest Focus]
Your primary goal is to advance the quest: '{main_quest.name}'.
The current status is '{main_quest.status}'. The known milestones are: {main_quest.milestones}.
Your narration MUST subtly guide the player towards this quest.
"""

    # --- THIS IS THE FIX ---
    # We now provide context for both the NPC Power and Player Skill scales.
    game_world_key = """
[Game World Key]
- NPC Power Level Scale: 1 (Child) to 100 (God-like Entity).
- Player Skill Scale: 1-19 (Novice), 20-39 (Apprentice), 40-59 (Adept), 60-79 (Expert), 80-99 (Master), 100 (Grandmaster).
"""

    # --- Assemble the Final Prompt ---
    prompt_sections = [
        "[Player Input]\n" + player_input.strip(),
        quest_focus_section.strip(),
        player_sheet_section.strip(),
        game_world_key.strip(), # <-- Add the new, combined world key
        "\n[Campaign Journal (Recent Events)]\n" + journal_section.strip(),
        "\n[Recent Dialogue Transcript]\n" + dialogue_section.strip(),
        "\n[Relevant Memories]\n" + memory_section.strip(),
        "\n[NPCs]\n" + "\n".join(f"{n.name} ({n.role}) - Status: {n.status} (Power: {n.power_level}, Style: {n.combat_style})" for n in npcs),
        "\n[Quests]\n" + "\n".join(f"{q.name}: {q.status}" for q in quests),
        "\n[World Flags]\n" + "\n".join(f"{f.key} = {f.value}" for f in flags),
        "\n[Session Config]\n" + f"Genre: {config.genre}\nTone: {config.tone}\nRealism: {config.realism}\nPower Fantasy: {config.power_fantasy}"
    ]

    return "\n\n".join(section for section in prompt_sections if section.strip() and ":" in section or "]" in section)