# kellanved987/gamemaster/GameMaster-a3a27eca3400b56292c31c1c7bf611a13a230a19/launcher.py

import streamlit as st
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
import traceback
import time

from db.engine import get_engine
from db.schema import Session as SessionModel, Turn, PlayerState, NPC, Quest, WorldFlag, Rumor, Location, ConversationContext, JournalEntry
from session_zero import run_session_zero_turn
from game_loop import run_game_turn
from gemini_interface.gemini_client import call_gemini_with_tools
from dotenv import load_dotenv

load_dotenv()

# --- Configuration and Setup ---
SessionFactory = sessionmaker(bind=get_engine())
st.set_page_config(page_title="AI RPG GM", layout="centered")
st.title("🎮 AI RPG Game Master")

# --- Initialize Session State ---
if "screen" not in st.session_state:
    st.session_state.screen = "home"
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.confirm_delete = False
    st.session_state.confirm_restart = False

# --- Deletion and Restart Logic ---
def delete_campaign(db, session_id_to_delete):
    try:
        db.query(ConversationContext).filter(ConversationContext.session_id == session_id_to_delete).delete()
        db.query(JournalEntry).filter(JournalEntry.session_id == session_id_to_delete).delete()
        db.query(Location).filter(Location.session_id == session_id_to_delete).delete()
        db.query(NPC).filter(NPC.session_id == session_id_to_delete).delete()
        db.query(PlayerState).filter(PlayerState.session_id == session_id_to_delete).delete()
        db.query(Quest).filter(Quest.session_id == session_id_to_delete).delete()
        db.query(Rumor).filter(Rumor.session_id == session_id_to_delete).delete()
        db.query(Turn).filter(Turn.session_id == session_id_to_delete).delete()
        db.query(WorldFlag).filter(WorldFlag.session_id == session_id_to_delete).delete()
        session_to_delete = db.query(SessionModel).get(session_id_to_delete)
        if session_to_delete:
            db.delete(session_to_delete)
        db.commit()
        st.success(f"Campaign {session_id_to_delete} has been permanently deleted.")
        st.session_state.confirm_delete = False
    except Exception as e:
        db.rollback()
        st.error(f"An error occurred while deleting the campaign: {e}")

def restart_campaign(db, session_id_to_restart):
    try:
        print(f"--- RESTARTING CAMPAIGN {session_id_to_restart} ---")
        db.query(ConversationContext).filter(ConversationContext.session_id == session_id_to_restart).delete()
        db.query(JournalEntry).filter(JournalEntry.session_id == session_id_to_restart).delete()
        db.query(Location).filter(Location.session_id == session_id_to_restart).delete()
        db.query(NPC).filter(NPC.session_id == session_id_to_restart).delete()
        db.query(Quest).filter(Quest.session_id == session_id_to_restart).delete()
        db.query(Rumor).filter(Rumor.session_id == session_id_to_restart).delete()
        db.query(Turn).filter(Turn.session_id == session_id_to_restart).delete()
        db.query(WorldFlag).filter(WorldFlag.session_id == session_id_to_restart).delete()
        db.commit()
        st.success(f"Campaign {session_id_to_restart} has been restarted.")
        st.session_state.confirm_restart = False
        print(f"--- CAMPAIGN {session_id_to_restart} RESTART COMPLETE ---")
    except Exception as e:
        db.rollback()
        st.error(f"An error occurred while restarting the campaign: {e}")
        print(f"--- ERROR DURING RESTART OF CAMPAIGN {session_id_to_restart} ---")
        print(traceback.format_exc())

# --- UI View Functions ---

def show_home_screen():
    with SessionFactory() as db:
        sessions = db.query(SessionModel).order_by(SessionModel.id).all()
        session_map = {f"{s.id} - {s.genre} ({s.tone})": s.id for s in sessions}
        st.subheader("Start or Continue a Game")
        
        options = ["— New Game —"] + list(session_map.keys())
        selected_key = st.selectbox("Choose a session:", options)

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            if st.button("Continue Game", use_container_width=True):
                if selected_key == "— New Game —":
                    st.session_state.screen = "session_zero"
                    st.session_state.messages = [{"role": "assistant", "content": "Welcome to Session Zero! Let's create our world together. To start, what kind of adventure are you in the mood for?"}]
                else:
                    session_id = session_map[selected_key]
                    st.session_state.session_id = session_id
                    st.session_state.screen = "game"
                    st.session_state.messages = []
                    turn_count = db.query(Turn).filter_by(session_id=session_id).count()
                    if turn_count == 0:
                        with st.spinner("The stage is being set..."):
                            session = db.query(SessionModel).get(session_id)
                            player = db.query(PlayerState).filter_by(session_id=session_id).first()
                            intro_prompt = "You are a master storyteller..."
                            opening_scene = call_gemini_with_tools(db, session_id, messages=[{"role": "user", "content": intro_prompt}])
                            st.session_state.messages.append({"role": "assistant", "content": opening_scene})
                    else:
                        turns = db.query(Turn).filter_by(session_id=session_id).order_by(Turn.turn_number).all()
                        for turn in turns:
                            st.session_state.messages.append({"role": "user", "content": turn.player_input})
                            st.session_state.messages.append({"role": "assistant", "content": turn.gm_response})
                st.rerun()

        with col2:
            if selected_key != "— New Game —":
                if st.button("Restart", use_container_width=True):
                    st.session_state.confirm_restart = True
                    st.session_state.session_to_restart = session_map[selected_key]
                    st.rerun()

        with col3:
            if selected_key != "— New Game —":
                if st.button("Delete", use_container_width=True, type="secondary"):
                    st.session_state.confirm_delete = True
                    st.session_state.session_to_delete = session_map[selected_key]
                    st.rerun()

        if st.session_state.get('confirm_delete', False):
            st.warning(f"Are you sure you want to permanently delete campaign {st.session_state.session_to_delete}?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes, Delete It", use_container_width=True, type="primary"):
                    with SessionFactory() as db_for_delete:
                        delete_campaign(db_for_delete, st.session_state.session_to_delete)
                    st.rerun()
            with c2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.confirm_delete = False
                    st.rerun()
        
        if st.session_state.get('confirm_restart', False):
            st.warning(f"Are you sure you want to restart campaign {st.session_state.session_to_restart}?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes, Restart It", use_container_width=True, type="primary"):
                    with SessionFactory() as db_for_restart:
                        restart_campaign(db_for_restart, st.session_state.session_to_restart)
                    st.rerun()
            with c2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.confirm_restart = False
                    st.rerun()

def show_session_zero_ui():
    st.subheader("🎲 New Game: Session Zero")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What do you say?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("GM is thinking..."):
                with SessionFactory() as db:
                    response = run_session_zero_turn(db, st.session_state.messages)
                    st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

        if "Success: World and character created for session" in response:
            st.success("Your new adventure is ready! Loading game...")
            try:
                # --- THIS IS THE FIX ---
                # Parse the session ID from the response string.
                new_session_id = int(response.split("session ")[1].split(".")[0])
                
                # Set session state to switch to the game screen.
                st.session_state.session_id = new_session_id
                st.session_state.screen = "game"
                st.session_state.messages = [] 
                
                # A short delay to allow the user to read the message.
                time.sleep(2)
                st.rerun()

            except (IndexError, ValueError) as e:
                # Fallback if parsing fails, restoring the original button.
                st.error("Error starting game automatically. Please return to the main menu to load your game.")
                st.session_state.screen = "home"
                if st.button("Back to Main Menu"):
                    st.rerun()

def show_game_screen():
    st.subheader("⚔️ Adventure in Progress")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What do you do?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("GM is thinking..."):
                with SessionFactory() as db:
                    response = run_game_turn(db, st.session_state.session_id, prompt)
                    st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

# --- Main App Router ---
try:
    if st.session_state.screen == "home":
        show_home_screen()
    elif st.session_state.screen == "session_zero":
        show_session_zero_ui()
    elif st.session_state.screen == "game":
        show_game_screen()
except Exception as e:
    print("--- AN ERROR OCCURRED ---")
    print(traceback.format_exc())
    print("-------------------------")
    st.error("An unexpected error occurred! Check the console for details.")
    st.exception(e)