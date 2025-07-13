# world_tools.py

from sqlalchemy.orm import Session as DBSession
from db.schema import Quest, NPC, WorldFlag, Rumor, PlayerState, JournalEntry, ConversationContext, Session as SessionModel
from datetime import datetime
from google.generativeai.types import FunctionDeclaration, Tool

# =====================================================================================
# FUNCTION DEFINITIONS
# =====================================================================================

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
        return f"Error: Quest '{quest_name}' not found. No action was taken."
    except Exception as e:
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

def update_player_character(db_session: DBSession, session_id: int, skill_updates: dict = None, new_inventory_items: list = None, new_limitations: list = None):
    """
    Updates the player's skills, adds items to their inventory, or adds new limitations.
    Use this to reflect player growth or changes resulting from their actions.
    Skill updates should be a dictionary like {"skill_name": new_score}.
    """
    player = db_session.query(PlayerState).filter_by(session_id=session_id).first()
    if not player:
        return "Error: Player state not found."

    if skill_updates:
        current_skills = player.skills or {}
        current_skills.update(skill_updates)
        player.skills = current_skills

    if new_inventory_items:
        current_inventory = player.inventory or []
        current_inventory.extend(i for i in new_inventory_items if i not in current_inventory)
        player.inventory = current_inventory

    if new_limitations:
        current_limitations = player.limitations or []
        current_limitations.extend(l for l in new_limitations if l not in current_limitations)
        player.limitations = current_limitations

    db_session.commit()
    return f"Success: Player state updated. Skills: {skill_updates}, Items: {new_inventory_items}, Limitations: {new_limitations}"

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

def update_npc_power_level(db_session: DBSession, session_id: int, npc_name: str, new_power_level: int, reason: str):
    """
    Updates the power level of an NPC on a scale of 1-100.
    Use this when an NPC becomes significantly stronger or weaker.
    """
    npc = db_session.query(NPC).filter_by(session_id=session_id, name=npc_name).first()
    if npc:
        npc.power_level = new_power_level
        db_session.commit()
        return f"Success: NPC '{npc_name}' power level changed to '{new_power_level}' because: {reason}"
    return f"Error: NPC '{npc_name}' not found."

def update_npc_combat_style(db_session: DBSession, session_id: int, npc_name: str, new_combat_style: str, reason: str):
    """
    Updates the combat style of an NPC (e.g., 'Brute', 'Skirmisher', 'Mage').
    Use this when an NPC's combat behavior is revealed or changes.
    """
    npc = db_session.query(NPC).filter_by(session_id=session_id, name=npc_name).first()
    if npc:
        npc.combat_style = new_combat_style
        db_session.commit()
        return f"Success: NPC '{npc_name}' combat style changed to '{new_combat_style}' because: {reason}"
    return f"Error: NPC '{npc_name}' not found."

def finalize_character_and_world(db_session: DBSession, genre: str, tone: str, world_intro: str, player_name: str, backstory: str, attributes: dict, skills: dict):
    """
    Finalizes and saves the world and character after a collaborative session zero conversation.
    This is the final step. Call this only when the player has confirmed all details are correct.
    """
    try:
        new_session = SessionModel(genre=genre, tone=tone, world_intro=world_intro, realism=False, power_fantasy=False)
        db_session.add(new_session)
        db_session.commit()

        final_attributes = dict(attributes)
        final_skills = dict(skills)

        player = PlayerState(
            session_id=new_session.id,
            name=player_name,
            race="Not specified",
            character_class="Not specified",
            backstory=backstory,
            attributes=final_attributes,
            skills=final_skills,
            inventory=["Traveler's clothes", "Backpack", "Rations (3 days)"],
            limitations=[]
        )
        db_session.add(player)
        db_session.commit()
        return f"Success: World and character for {player_name} have been created. The adventure can now begin! New session ID is {new_session.id}"
    except Exception as e:
        db_session.rollback()
        print(f"ERROR in finalize_character_and_world: {e}")
        return f"Error finalizing character: {e}"

def save_dialogue_context(db_session: DBSession, session_id: int, npc_name: str, topic: str, dialogue_summary: str):
    """
    Saves the context of a conversation with an NPC, including the topic and a key quote.
    """
    npc = db_session.query(NPC).filter_by(session_id=session_id, name=npc_name).first()
    if not npc:
        npc = NPC(session_id=session_id, name=npc_name, role="Unknown", motivation="Unknown", status="active", power_level=15, combat_style="Unknown")
        db_session.add(npc)
        db_session.commit()

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
    return memory_indices

# =====================================================================================
# TOOL DEFINITIONS & HANDLERS
# =====================================================================================
WORLD_TOOLS_LIST = [
    Tool(function_declarations=[FunctionDeclaration(
        name='update_quest_status',
        description=update_quest_status.__doc__,
        parameters={'type':'object','properties':{
            'quest_name':{'type':'string'},'new_status':{'type':'string'},'reason':{'type':'string'}
        },'required':['quest_name','new_status','reason']}
    )]),
    Tool(function_declarations=[FunctionDeclaration(
        name='update_npc_status',
        description=update_npc_status.__doc__,
        parameters={'type':'object','properties':{
            'npc_name':{'type':'string'},'new_status':{'type':'string'},'reason':{'type':'string'}
        },'required':['npc_name','new_status','reason']}
    )]),
    Tool(function_declarations=[FunctionDeclaration(
        name='create_rumor',
        description=create_rumor.__doc__,
        parameters={'type':'object','properties':{
            'rumor_content':{'type':'string'},'is_confirmed':{'type':'boolean'}
        },'required':['rumor_content','is_confirmed']}
    )]),
    Tool(function_declarations=[FunctionDeclaration(
        name='set_world_flag',
        description=set_world_flag.__doc__,
        parameters={'type':'object','properties':{
            'key':{'type':'string'},'value':{'type':'string'},'reason':{'type':'string'}
        },'required':['key','value','reason']}
    )]),
    Tool(function_declarations=[FunctionDeclaration(
        name='update_player_character',
        description=update_player_character.__doc__,
        parameters={'type':'object','properties':{
            'skill_updates':{'type':'object'},'new_inventory_items':{'type':'array','items':{'type':'string'}},'new_limitations':{'type':'array','items':{'type':'string'}}
        }}
    )]),
    Tool(function_declarations=[FunctionDeclaration(
        name='create_journal_entry',
        description=create_journal_entry.__doc__,
        parameters={'type':'object','properties':{
            'turn_number':{'type':'integer'},'summary_text':{'type':'string'}
        },'required':['turn_number','summary_text']}
    )]),
    Tool(function_declarations=[FunctionDeclaration(
        name='update_npc_motivation',
        description=update_npc_motivation.__doc__,
        parameters={'type':'object','properties':{
            'npc_name':{'type':'string'},'new_motivation':{'type':'string'},'reason':{'type':'string'}
        },'required':['npc_name','new_motivation','reason']}
    )]),
    Tool(function_declarations=[FunctionDeclaration(
        name='update_npc_power_level',
        description=update_npc_power_level.__doc__,
        parameters={'type':'object','properties':{
            'npc_name':{'type':'string'},'new_power_level':{'type':'integer'},'reason':{'type':'string'}
        },'required':['npc_name','new_power_level','reason']}
    )]),
    Tool(function_declarations=[FunctionDeclaration(
        name='update_npc_combat_style',
        description=update_npc_combat_style.__doc__,
        parameters={'type':'object','properties':{
            'npc_name':{'type':'string'},'new_combat_style':{'type':'string'},'reason':{'type':'string'}
        },'required':['npc_name','new_combat_style','reason']}
    )]),
    Tool(function_declarations=[FunctionDeclaration(
        name='finalize_character_and_world',
        description=finalize_character_and_world.__doc__,
        parameters={'type':'object','properties':{
            'genre':{'type':'string'},'tone':{'type':'string'},'world_intro':{'type':'string'},'player_name':{'type':'string'},
            'backstory':{'type':'string'},'attributes':{'type':'object'},'skills':{'type':'object'}
        },'required':['genre','tone','world_intro','player_name','backstory','attributes','skills']}
    )]),
    Tool(function_declarations=[FunctionDeclaration(
        name='save_dialogue_context',
        description=save_dialogue_context.__doc__,
        parameters={'type':'object','properties':{
            'npc_name':{'type':'string'},'topic':{'type':'string'},'dialogue_summary':{'type':'string'}
        },'required':['npc_name','topic','dialogue_summary']}
    )]),
    Tool(function_declarations=[FunctionDeclaration(
        name='select_relevant_memories',
        description=select_relevant_memories.__doc__,
        parameters={'type':'object','properties':{
            'memory_indices':{'type':'array','items':{'type':'integer'}}
        },'required':['memory_indices']}
    )])
]

FUNCTION_HANDLERS = {
    "update_quest_status": update_quest_status,
    "update_npc_status": update_npc_status,
    "create_rumor": create_rumor,
    "set_world_flag": set_world_flag,
    "update_player_character": update_player_character,
    "create_journal_entry": create_journal_entry,
    "update_npc_motivation": update_npc_motivation,
    "update_npc_power_level": update_npc_power_level,
    "update_npc_combat_style": update_npc_combat_style,
    "finalize_character_and_world": finalize_character_and_world,
    "save_dialogue_context": save_dialogue_context,
    "select_relevant_memories": select_relevant_memories,
}
