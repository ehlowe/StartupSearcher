
import os
from enum import Enum
from dataclasses import dataclass


from groq import Groq
groq_client = Groq(api_key=os.getenv("groq"))
from openai import OpenAI
openai_client = OpenAI(api_key=os.getenv("openai"))

@dataclass
class AIModel:
    model_name: str
    model_provider: str

class ModelSelector:
    llama70b = AIModel("llama-3.1-70b-versatile", "groq")
    gpt4omini = AIModel("gpt-4o-mini", "openai")



def stream_response(prompt, model: AIModel):
    """Streams the response from the AI model"""
    if model.model_provider == "groq":
        response = groq_client.chat.completions.create(
            model=model.model_name,
            messages=prompt,
            temperature=0,
            stream=True,
            stop=None,
        )
        return response
    elif model.model_provider == "openai":
        response = openai_client.chat.completions.create(
            model=model.model_name,
            messages=prompt,
            temperature=0,
            stream=True
        )
        return response
    else:
        return None