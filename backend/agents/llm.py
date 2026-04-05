import os
import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")

def call_llm(prompt: str):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "llama3:instruct",
                "prompt": prompt,
                "stream": False
            }
        )

        data = response.json()

        # Debug print (VERY IMPORTANT)
        print("OLLAMA RESPONSE:", data)

        return data.get("response", "No response from model")

    except Exception as e:
        print("ERROR:", str(e))
        return f"Error: {str(e)}"
