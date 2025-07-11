# world_tools.py

from sqlalchemy.orm import Session as DBSession
from db.schema import Quest, NPC, WorldFlag, Rumor
from datetime import datetime

# In world_tools.py

def update_quest_status(db_session: DBSession, session_id: int, quest_name: str, new_status: str, reason: str):
    """
    Updates the status of a quest (e.g., 'active', 'completed', 'failed').
    """
    try:
        quest = db_session.query(Quest).filter_by(session_id=session_id, name=quest_name).first()
        if quest:
            quest.status = new_status
            db_session.commit()
            return f"Success: Quest '{quest_name}' status changed to '{new_status}' because: {reason}"
        # If the quest doesn't exist, return a clear message to the AI
        return f"Error: Quest '{quest_name}' not found. No action was taken."
    except Exception as e:
        # If any other database error occurs, catch it and inform the AI
        print(f"ERROR in update_quest_status: {e}")
        return f"Error executing update: {e}. The world state was not changed."

def update_npc_status(db_session: DBSession, session_id: int, npc_name: str, new_status: str, reason: str):
    """
    Updates the status of an NPC (e.g., 'friendly', 'hostile', 'deceased', 'busy').
    Use this to reflect changes in an NPC's state or disposition due to game events.
    """
    npc = db_session.query(NPC).filter_by(session_id=session_id, name=npc_name).first()
    if npc:
        npc.status = new_status
        db_session.commit()
        return f"Success: NPC '{npc_name}' status changed to '{new_status}' because: {reason}"
    return f"Error: NPC '{npc_name}' not found."

def create_rumor(db_session: DBSession, session_id: int, rumor_content: str, is_confirmed: bool):
    """
    Creates a new rumor in the world.
    Use this when an event happens that NPCs might start talking about.
    """
    new_rumor = Rumor(
        session_id=session_id,
        content=rumor_content,
        is_confirmed=is_confirmed
    )
    db_session.add(new_rumor)
    db_session.commit()
    return f"Success: A new rumor was started: '{rumor_content}'."

def set_world_flag(db_session: DBSession, session_id: int, key: str, value: str, reason: str):
    """
    Sets or updates a world flag to track the state of the world.
    Use this for broader changes that affect a region or the overall narrative.
    """
    flag = db_session.query(WorldFlag).filter_by(session_id=session_id, key=key).first()
    if flag:
        flag.value = value
    else:
        flag = WorldFlag(session_id=session_id, key=key, value=value)
        db_session.add(flag)
    db_session.commit()
    return f"Success: World flag '{key}' set to '{value}' because: {reason}."

# Add to world_tools.py

def update_player_character(db_session: DBSession, session_id: int, skill_updates: dict, new_inventory_items: list, new_limitations: list):
    """
    Updates the player's skills, adds items to their inventory, or adds new limitations.
    Use this to reflect player growth or changes resulting from their actions.
    Skill updates should be a dictionary like {"skill_name": new_score}.
    """
    player = db_session.query(PlayerState).filter_by(session_id=session_id).first()
    if not player:
        return "Error: Player state not found."

    if skill_updates:
        # Ensure we're not overwriting with a lower value if that's a rule
        for skill, new_val in skill_updates.items():
            player.skills[skill] = new_val

    if new_inventory_items:
        player.inventory.extend(i for i in new_inventory_items if i not in player.inventory)

    if new_limitations:
        player.limitations.extend(l for l in new_limitations if l not in player.limitations)

    db_session.commit()
    return f"Success: Player state updated. Skills: {skill_updates}, Items: {new_inventory_items}, Limitations: {new_limitations}"

# Add this function alongside your other tool functions
def create_journal_entry(db_session: DBSession, session_id: int, turn_number: int, summary_text: str):
    """
    Creates a new narrative journal entry to summarize recent events.
    Use this to record the story's progress in a high-level, narrative format.
    """
    entry = JournalEntry(
        session_id=session_id,
        turn_number=turn_number,
        entry_text=summary_text,
        timestamp=datetime.utcnow()
    )
    db_session.add(entry)
    db_session.commit()
    return f"Success: Journal entry created for turn {turn_number}."


# Add this function alongside your other tool functions
def update_npc_motivation(db_session: DBSession, session_id: int, npc_name: str, new_motivation: str, reason: str):
    """
    Updates the core motivation of an NPC.
    Use this for significant character development moments, like a hero becoming jaded or a villain having a change of heart.
    """
    npc = db_session.query(NPC).filter_by(session_id=session_id, name=npc_name).first()
    if npc:
        npc.motivation = new_motivation
        db_session.commit()
        return f"Success: NPC '{npc_name}' motivation changed to '{new_motivation}' because: {reason}"
    return f"Error: NPC '{npc_name}' not found."

# Add this function alongside your other tool functions
def finalize_character_and_world(db_session: DBSession, genre: str, tone: str, world_intro: str, player_name: str, backstory: str, attributes: dict, skills: list):
    """
    Finalizes and saves the world and character after a collaborative session zero conversation.
    This is the final step. Call this only when the player has confirmed all details are correct.
    """
    try:
        # Create the new session
        new_session = SessionModel(
            genre=genre,
            tone=tone,
            # For now, realism and power_fantasy can be default or derived
            realism=False,
            power_fantasy=False
        )
        db_session.add(new_session)
        db_session.commit() # Commit to get the new session's ID

        # Create the new player state
        # Convert skills list to a dictionary with starting values
        skills_dict = {skill: 15 for skill in skills} # Start all chosen skills at a reasonable 15

        player = PlayerState(
            session_id=new_session.id,
            name=player_name,
            race="Not specified", # These can be expanded later
            character_class="Not specified",
            backstory=backstory,
            attributes=attributes, # e.g., {"strength": 12, "dexterity": 14, ...}
            skills=skills_dict,
            inventory=["Traveler's clothes", "Backpack", "Rations (3 days)"], # Start with basic items
            limitations=[]
        )
        db_session.add(player)
        db_session.commit()

        # We return the new session_id so the game can start
        return f"Success: World and character for {player_name} have been created. The adventure can now begin! New session ID is {new_session.id}"
    except Exception as e:
        return f"Error finalizing character: {e}"

# Add these two new functions

def save_dialogue_context(db_session: DBSession, session_id: int, npc_name: str, topic: str, dialogue_summary: str):
    """
    Saves the context of a conversation with an NPC, including the topic and a key quote.
    """
    npc = db_session.query(NPC).filter_by(session_id=session_id, name=npc_name).first()
    if not npc:
        return f"Error: NPC '{npc_name}' not found. Dialogue context not saved."

    context = db_session.query(ConversationContext).filter_by(session_id=session_id, npc_id=npc.id).first()
    if context:
        context.last_topic = topic
        context.recent_dialogue = dialogue_summary
        context.last_updated = datetime.utcnow()
    else:
        context = ConversationContext(
            session_id=session_id,
            npc_id=npc.id,
            last_topic=topic,
            recent_dialogue=dialogue_summary,
            last_updated=datetime.utcnow()
        )
        db_session.add(context)
    db_session.commit()
    return f"Success: Dialogue context with {npc_name} saved."

def select_relevant_memories(memory_indices: list[int]):
    """
    Selects a list of relevant memory chunks based on their indices.
    The AI should call this function with a list of integers corresponding to the memories it deems most relevant.
    """
    # This tool is unique because it doesn't interact with the database.
    # It just returns the data for the calling script to use.
    # The actual filtering logic will happen in the calling script.
    return memory_indices


# Update the full dictionary at the bottom of the file
AVAILABLE_TOOLS = {
    "update_quest_status": update_quest_status,
    "update_npc_status": update_npc_status,
    "create_rumor": create_rumor,
    "set_world_flag": set_world_flag,
    "update_player_character": update_player_character,
    "create_journal_entry": create_journal_entry,
    "update_npc_motivation": update_npc_motivation,
    "save_dialogue_context": save_dialogue_context,
    "select_relevant_memories": select_relevant_memories, # Note: This one is handled differently
}
