# prompt\_builder/builder.py

from memory.retrieve import retrieve\_relevant\_chunks
from memory.relevance\_filter import filter\_relevant\_chunks

from db.schema import NPC, Quest, WorldFlag, Session, Turn, ConversationContext
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc

recent\_turn\_limit = 3

def build\_prompt(db: DBSession, session\_id: int, player\_input: str) -> str:
\# Memory
raw\_chunks = retrieve\_relevant\_chunks(player\_input)
memory = filter\_relevant\_chunks(player\_input, raw\_chunks)

```
# Recent Dialogue
recent_turns = db.query(Turn).filter_by(session_id=session_id)
recent_turns = recent_turns.order_by(desc(Turn.turn_number)).limit(recent_turn_limit).all()
recent_turns.reverse()
dialogue_section = "\n".join(
    f"Player: {t.player_input}\nGM: {t.gm_response}" for t in recent_turns
)

# Structured state
npcs = db.query(NPC).filter_by(session_id=session_id).all()
quests = db.query(Quest).filter_by(session_id=session_id).all()
flags = db.query(WorldFlag).filter_by(session_id=session_id).all()
config = db.query(Session).get(session_id)

# NPC dialogue memory
contexts = db.query(ConversationContext).filter_by(session_id=session_id).all()
npc_contexts = "\n".join(
    f"{c.npc_id}: Last topic was '{c.last_topic}'. Recent: \"{c.recent_dialogue}\""
    for c in contexts if c.recent_dialogue
)

# Assemble prompt
prompt_sections = [
    "[Player Input]\n" + player_input.strip(),
    "\n[Recent Dialogue]\n" + dialogue_section.strip(),
    "\n[Relevant Memory]\n" + "\n".join(c["text"] for c in memory),
    "\n[NPC Dialogue Contexts]\n" + npc_contexts.strip(),
    "\n[NPCs]\n" + "\n".join(f"{n.name} ({n.role}) - {n.status}" for n in npcs),
    "\n[Quests]\n" + "\n".join(f"{q.name}: {q.status}" for q in quests),
    "\n[World Flags]\n" + "\n".join(f"{f.key} = {f.value}" for f in flags),
    "\n[Session Config]\n" + f"Genre: {config.genre}\nTone: {config.tone}\nRealism: {config.realism}\nPower Fantasy: {config.power_fantasy}"
]

return "\n\n".join(prompt_sections)
```
