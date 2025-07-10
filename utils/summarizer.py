# utils/summarizer.py

from gpt_interface.gpt_client import call_chat_model

def summarize_turn(player_input: str, gm_response: str) -> str:
    """
    Summarizes a full turn into 1–2 sentences for memory compression.
    """
    system_prompt = (
        "You are a narrative summarizer for a text-based RPG. "
        "Given the player’s input and the GM’s response, summarize the entire turn "
        "as one or two concise story events."
    )

    user_prompt = f"""Player input:
{player_input.strip()}

GM response:
{gm_response.strip()}

Summary:"""

    response = call_chat_model(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model="gpt35",
        temperature=0.3,
        max_tokens=100
    )

    return response.strip()
