# launcher.py

import streamlit as st
from sqlalchemy.orm import sessionmaker
from db.engine import get_engine
from db.schema import Session as SessionModel
# Import the new "single turn" function
from session_zero import run_session_zero_turn
from game_loop import run_game_loop # We still need this for later

# --- Configuration and Setup ---
SessionFactory = sessionmaker(bind=get_engine())
st.set_page_config(page_title="AI RPG GM", layout="centered")
st.title("🎮 AI RPG Game Master")

# --- Initialize Session State ---
if "screen" not in st.session_state:
    st.session_state.screen = "home"
    st.session_state.session_id = None
    # This will now hold our conversation history for the UI
    st.session_state.messages = []

# --- UI View Functions ---

def show_home_screen():
    # ... (This function remains the same as the last version)
    with SessionFactory() as db:
        sessions = db.query(SessionModel).order_by(SessionModel.id).all()
        session_map = {f"{s.id} - {s.genre} ({s.tone})": s.id for s in sessions}
        st.subheader("Start or Continue a Game")
        selected = st.selectbox("Choose a session:", ["— New Game —"] + list(session_map.keys()))
        if st.button("Continue"):
            if selected == "— New Game —":
                st.session_state.screen = "session_zero"
                # Initialize Session Zero chat
                st.session_state.messages = [{"role": "assistant", "content": "Welcome to Session Zero! Let's create our world together. To start, what kind of adventure are you in the mood for?"}]
                st.rerun()
            else:
                st.warning("Loading existing games is not yet implemented.")

def show_session_zero_ui():
    st.subheader("🎲 New Game: Session Zero")
    
    # Display existing messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Get new player input from the chat box at the bottom of the screen
    if prompt := st.chat_input("What do you say?"):
        # Add player message to history and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display the AI's response
        with st.chat_message("assistant"):
            with st.spinner("GM is thinking..."):
                with SessionFactory() as db:
                    # Create the chat history string for the AI
                    history_string = "".join(f"{m['role'].capitalize()}: {m['content']}\n" for m in st.session_state.messages)
                    # Call our single-turn function
                    response = run_session_zero_turn(db, history_string, prompt)
                    st.markdown(response)
        
        # Add AI response to history
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Check if the game was created
        if "Success: World and character" in response:
            st.success("Your new adventure is ready! Go back to the main menu to load it.")
            st.session_state.screen = "home"
            # No rerun here, let the user see the success message and click a button
            if st.button("Back to Main Menu"):
                st.rerun()

# --- Main App Router ---
if st.session_state.screen == "home":
    show_home_screen()
elif st.session_state.screen == "session_zero":
    show_session_zero_ui()