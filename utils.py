import json
import os
from typing import Any, Dict

def load_prompt(filename: str, prompt_dir: str = "prompt_templates", context: Dict[str, Any] = None) -> str:
    #Loads a prompt template file and formats it with the provided context.
    path = os.path.join(prompt_dir, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Prompt file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    if context:
        try:
            formatted_context = {k: json.dumps(v, indent=2) if isinstance(v, (dict, list)) else v for k, v in context.items()}
            return prompt_template.format(**formatted_context)
        except KeyError as e:
            print(f"❌ KeyError: The placeholder {{{e.args[0]}}} was not found in the context dictionary for prompt '{filename}'.")
            raise

    return prompt_template

def save_json(data: dict, filepath: str):
    #Saves a Python dictionary as a JSON file.Creates directories if they do not exist.
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)