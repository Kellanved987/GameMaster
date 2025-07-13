# db/schema.py

from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean,
    Text, DateTime, ForeignKey
)
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, JSON

from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# --- Core Tables ---

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    genre = Column(String)
    tone = Column(String)
    world_intro = Column(Text) # <-- This is the fix
    realism = Column(Boolean)
    power_fantasy = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    sim_counter = Column(Integer, default=0)
    player_state = relationship("PlayerState", back_populates="session", uselist=False)

class NPC(Base):
    __tablename__ = "npcs"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    name = Column(String)
    role = Column(String)
    faction = Column(String)
    motivation = Column(Text)
    status = Column(String)
    personality_traits = Column(Text)
    relationships = Column(SQLiteJSON)
    emotional_state = Column(String)
    last_interaction = Column(DateTime)


class Quest(Base):
    __tablename__ = "quests"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    name = Column(String)
    milestones = Column(SQLiteJSON)
    consequences = Column(SQLiteJSON)
    status = Column(String)


class WorldFlag(Base):
    __tablename__ = "world_flags"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    key = Column(String)
    value = Column(String)  # Use "true", "false", "unknown", etc.


class Rumor(Base):
    __tablename__ = "rumors"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    content = Column(Text)
    is_confirmed = Column(Boolean, default=False)


class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(Text)
    atmosphere = Column(String)
    local_events = Column(SQLiteJSON)
    connected_locations = Column(SQLiteJSON)


class ConversationContext(Base):
    __tablename__ = "conversation_contexts"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    npc_id = Column(Integer, ForeignKey("npcs.id"))
    recent_dialogue = Column(Text)
    last_topic = Column(String)
    last_updated = Column(DateTime)


class Turn(Base):
    __tablename__ = "turns"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    turn_number = Column(Integer)
    player_input = Column(Text)
    gm_response = Column(Text)
    prompt_used = Column(Text)
    summary = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    prompt_snapshot = Column(Text)  # Stores full prompt sent to GPT
    

class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    turn_number = Column(Integer) # The turn number at which this summary was created
    entry_text = Column(Text) # The narrative summary
    timestamp = Column(DateTime, default=datetime.utcnow)


class PlayerState(Base):
    __tablename__ = "player_state"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    name = Column(String)
    race = Column(String)
    character_class = Column(String)
    backstory = Column(Text)
    attributes = Column(JSON)     # {"strength": 10, "dexterity": 14, ...}
    skills = Column(JSON)         # ["lockpicking", "tracking"]
    inventory = Column(JSON)      # ["dagger", "rope"]
    limitations = Column(JSON)    # ["no magic", "hunted in Duskport"]

    session = relationship("Session", back_populates="player_state")