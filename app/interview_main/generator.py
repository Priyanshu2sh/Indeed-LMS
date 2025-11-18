import re
from .config import generator

def generate_next_question(history: str):
    try:
        response = generator(history)  # Only API call
    except Exception as e:
        return f"Error calling generator: {e}"

    # --- Normalize Mistral API output ---
    generated_text = None

    if isinstance(response, dict):
        if "choices" in response and len(response["choices"]) > 0:
            generated_text = response["choices"][0]["message"]["content"]
        else:
            generated_text = str(response)
    else:
        generated_text = str(response)

    # --- Postprocess ---
    new_part = generated_text.replace(history, "").strip()
    new_part = re.sub(r'^\**\s*Interviewer:\**\s*', "", new_part, flags=re.IGNORECASE)

    # First line only
    match = re.search(r'^(.*?)(?:\n|$)', new_part)
    return match.group(1).strip() if match else None