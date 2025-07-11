# launcher.py

import streamlit as st
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc

from db.engine import get_engine
from db.schema import Session as SessionModel, Turn, PlayerState # Import PlayerState
from session_zero import run_session_zero_turn
from game_loop import run_game_turn 
from gemini_interface.gemini_client import call_gemini_with_tools # Import the gemini client
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

# --- UI View Functions ---

def show_home_screen():
    with SessionFactory() as db:
        sessions = db.query(SessionModel).order_by(SessionModel.id).all()
        session_map = {f"{s.id} - {s.genre} ({s.tone})": s.id for s in sessions}
        st.subheader("Start or Continue a Game")
        
        options = ["— New Game —"] + list(session_map.keys())
        selected = st.selectbox("Choose a session:", options)

        if st.button("Continue"):
            if selected == "— New Game —":
                st.session_state.screen = "session_zero"
                st.session_state.messages = [{"role": "assistant", "content": "Welcome to Session Zero! Let's create our world together. To start, what kind of adventure are you in the mood for?"}]
            else:
                session_id = session_map[selected]
                st.session_state.session_id = session_id
                st.session_state.screen = "game"
                st.session_state.messages = []

                # --- NEW: Logic to handle first-time load ---
                turn_count = db.query(Turn).filter_by(session_id=session_id).count()

                if turn_count == 0:
                    # This is the first time loading this game. Generate an intro.
                    with st.spinner("The stage is being set..."):
                        session = db.query(SessionModel).get(session_id)
                        player = db.query(PlayerState).filter_by(session_id=session_id).first()

                        intro_prompt = f"""
                        You are a master storyteller and Game Master.
                        Your task is to write a compelling, cinematic opening scene for a new RPG campaign.
                        This is the very first thing the player will see.

                        Campaign Details:
                        - Genre: {session.genre}
                        - Tone: {session.tone}

                        Player Character Backstory:
                        "{player.backstory}"

                        Based on these details, write an engaging opening narration of 2-3 paragraphs.
                        Set the scene, establish the mood, and end with a prompt that draws the player into the world, asking them "What do you do?".
                        Do not give the player any choices, just describe their current situation.
                        """
                        
                        opening_scene = call_gemini_with_tools(db, session_id, messages=[{"role": "user", "content": intro_prompt}])
                        st.session_state.messages.append({"role": "assistant", "content": opening_scene})
                else:
                    # This is a returning game. Load the history as normal.
                    turns = db.query(Turn).filter_by(session_id=session_id).order_by(Turn.turn_number).all()
                    for turn in turns:
                        st.session_state.messages.append({"role": "user", "content": turn.player_input})
                        st.session_state.messages.append({"role": "assistant", "content": turn.gm_response})
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

        if "Success: World and character" in response:
            st.success("Your new adventure is ready! Go back to the main menu to load it.")
            if st.button("Back to Main Menu"):
                st.session_state.screen = "home"
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
if st.session_state.screen == "home":
    show_home_screen()
elif st.session_state.screen == "session_zero":
    show_session_zero_ui()
elif st.session_state.screen == "game":
    show_game_screen()