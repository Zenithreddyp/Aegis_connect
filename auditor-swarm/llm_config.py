import requests
import json

OLLAMA_URL =  "http://localhost:11434/api/generate"

def query_ollama(model: str, prompt: str, system_prompt: str = "", require_json: bool = True) -> dict:
    """
    Sends a prompt to the local Ollama instance and returns the response.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }
    

    if require_json:
        payload["format"] = "json"

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        # response.raise_for_status()  # Check for HTTP errors
        
        result_text = response.json().get("response", "")
        print("----OUTPUTTTTTTT----")
        print(result_text)
        if require_json:
            return json.loads(result_text)
        return {"text": result_text}
        
    except Exception as e:
        print(f"[LLM CONFIG ERROR]: {e}")
        return {"error": str(e)}