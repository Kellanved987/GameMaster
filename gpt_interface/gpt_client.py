# gpt_interface/gpt_client.py

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

DEPLOYMENTS = {
    "gpt4o": os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT4O"),
    "gpt35": os.getenv("AZURE_OPENAI_DEPLOYMENT_GPT35"),
}

def call_chat_model(messages, model="gpt4o", temperature=0.7, max_tokens=2048):
    deployment = DEPLOYMENTS[model]
    response = client.chat.completions.create(
        model=deployment,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    choice = response.choices[0]
    content = choice.message.content
    finish_reason = choice.finish_reason

    # --- THIS IS THE FIX ---
    # Start with the content, or an empty string if content is None
    final_response = content.strip() if content else ""

    # If the AI was cut off because of the token limit, add a warning.
    if finish_reason == "length":
        final_response += "\n\n*[The story was cut short as the narration became too long. You can ask for a summary or to continue.]*"

    return final_response