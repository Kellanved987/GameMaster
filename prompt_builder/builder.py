# prompt_builder/builder.py

from memory.retrieve import retrieve_relevant_chunks
from memory.relevance_filter import filter_relevant_chunks
from db.schema import NPC, Quest, WorldFlag, Session, Turn, ConversationContext, JournalEntry
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc

RECENT_TURN_LIMIT = 3
JOURNAL_ENTRY_LIMIT = 5

def build_prompt(db: DBSession, session_id: int, player_input: str) -> str:
    # --- Context Gathering ---
    # 1. Raw Memory (Vector Store)
    raw_chunks = retrieve_relevant_chunks(player_input, session_id)
    memory_chunks = filter_relevant_chunks(player_input, raw_chunks)
    memory_section = "\n".join(c["text"] for c in memory_chunks)

    # 2. Recent Dialogue (Raw Transcript)
    recent_turns = db.query(Turn).filter_by(session_id=session_id)\
        .order_by(desc(Turn.turn_number)).limit(RECENT_TURN_LIMIT).all()
    recent_turns.reverse()
    dialogue_section = "\n".join(
        f"Player: {t.player_input}\nGM: {t.gm_response}" for t in recent_turns
    )

    # 3. Narrative Memory (Journal Entries)
    journal_entries = db.query(JournalEntry).filter_by(session_id=session_id)\
        .order_by(desc(JournalEntry.turn_number)).limit(JOURNAL_ENTRY_LIMIT).all()
    journal_entries.reverse()
    journal_section = "\n".join(
        f"- {entry.entry_text}" for entry in journal_entries
    )

    # 4. Structured State (NPCs, Quests, etc.)
    npcs = db.query(NPC).filter_by(session_id=session_id).all()
    quests = db.query(Quest).filter_by(session_id=session_id).all()
    flags = db.query(WorldFlag).filter_by(session_id=session_id).all()
    config = db.query(Session).get(session_id)
    
    # --- NEW: Active Quest Weaving Logic ---
    active_quests = [q for q in quests if q.status == 'active']
    quest_focus_section = ""
    if active_quests:
        # For simplicity, we'll focus on the first active quest.
        # This could be expanded to handle multiple active quests.
        main_quest = active_quests[0]
        quest_focus_section = f"""
[Active Quest Focus]
You are a master storyteller. Your primary goal is to advance the quest: '{main_quest.name}'.
The current status is '{main_quest.status}'. The known milestones are: {main_quest.milestones}.
Your narration MUST subtly guide the player towards this quest. Mention details in the world that are relevant to this goal.
If the player seems lost or is acting randomly, use environmental storytelling or NPC dialogue to remind them of their purpose without breaking character.
"""

    # --- Assemble the Final Prompt ---
    prompt_sections = [
        "[Player Input]\n" + player_input.strip(),
        # Add the new quest focus right at the top to guide the AI's response
        quest_focus_section.strip(),
        "\n[Campaign Journal (Recent Events)]\n" + journal_section.strip(),
        "\n[Recent Dialogue Transcript]\n" + dialogue_section.strip(),
        "\n[Relevant Memories]\n" + memory_section.strip(),
        # ... (rest of the sections are the same) ...
        "\n[NPCs]\n" + "\n".join(f"{n.name} ({n.role}) - {n.status}" for n in npcs),
        "\n[Quests]\n" + "\n".join(f"{q.name}: {q.status}" for q in quests),
        "\n[World Flags]\n" + "\n".join(f"{f.key} = {f.value}" for f in flags),
        "\n[Session Config]\n" + f"Genre: {config.genre}\nTone: {config.tone}\nRealism: {config.realism}\nPower Fantasy: {config.power_fantasy}"
    ]

    # Filter out any empty sections before joining
    return "\n\n".join(section for section in prompt_sections if section.strip() and ":" in section or "]" in section)