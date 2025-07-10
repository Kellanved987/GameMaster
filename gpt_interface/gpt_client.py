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

def call_chat_model(messages, model="gpt4o", temperature=0.7, max_tokens=1000):
    deployment = DEPLOYMENTS[model]
    response = client.chat.completions.create(
        model=deployment,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()
