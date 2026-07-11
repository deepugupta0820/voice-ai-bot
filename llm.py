import json
import os
import urllib.error
import urllib.request

from groq import Groq
from dotenv import load_dotenv

from prompt import SYSTEM_PROMPT

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_model = os.getenv(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3-super-120b-a12b:free"
)

groq_client = Groq(api_key=groq_api_key) if groq_api_key else None


def _openrouter_chat(user_question):
    url = "https://openrouter.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openrouter_api_key}",
    }
    payload = {
        "model": openrouter_model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_question,
            },
        ],
        "temperature": 0.5,
        "max_tokens": 300,
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data["choices"][0]["message"]["content"]


def get_response(user_question):
    groq_error = None

    if groq_client:
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": user_question,
                    },
                ],
                temperature=0.5,
                max_tokens=300,
            )
            return response.choices[0].message.content
        except Exception as e:
            groq_error = str(e)

    if openrouter_api_key:
        try:
            return _openrouter_chat(user_question)
        except Exception as e:
            openrouter_error = str(e)
            if groq_error:
                return f"Error: GROQ failed ({groq_error}) and OpenRouter failed ({openrouter_error})"
            return f"Error: OpenRouter failed ({openrouter_error})"

    if groq_error:
        return f"Error: GROQ failed ({groq_error}) and OPENROUTER_API_KEY is not configured."

    return "Error: No valid LLM API key configured. Set GROQ_API_KEY or OPENROUTER_API_KEY."
