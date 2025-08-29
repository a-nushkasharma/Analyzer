import os
import json
import openai
from dotenv import load_dotenv
from typing import Any, Dict
from utils import load_prompt

load_dotenv()

class LLM1Client:
    def __init__(self, api_key: str = None, model: str = None, prompt_dir: str = "prompt_templates"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing OpenAI API Key")
        
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5-nano")
        self.client = openai.OpenAI(api_key=self.api_key)
        self.prompt_dir = prompt_dir

    def _get_prompt(self, phase: int, context: Dict[str, Any] = None) -> str:
        
        #Load and format the prompt using the centralized utility function.
       
        filename = f"phase{phase}.txt"
        return load_prompt(filename, self.prompt_dir, context=context)

    def analyze_contract(self, contract_code: str, phase: int = 1, context: Dict[str, Any] = None) -> list | dict:
        
        prompt_with_context = self._get_prompt(phase, context)
        full_prompt = f"{prompt_with_context}\n\nContract Code:\n{contract_code}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a helpful security auditor that only responds in a valid JSON format."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            raw_text = response.choices[0].message.content
            
            parsed_json = json.loads(raw_text)

            if isinstance(parsed_json, dict):
                # If the model returns a single object, wrap it in a list.
                return [parsed_json]
            return parsed_json

        except Exception as e:
            print(f"⚠️ Error calling OpenAI API: {e}")
            return []