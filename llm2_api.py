import os
import json
from dotenv import load_dotenv
from typing import Any, Dict
import google.generativeai as genai

from utils import load_prompt

load_dotenv()
class LLM2Client:
    def __init__(self, api_key: str = None, model: str = "gemini-1.5-flash", prompt_dir: str = "prompt_templates"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing Gemini API Key")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
        self.prompt_dir = prompt_dir

    def _get_prompt(self, phase: int, context: Dict[str, Any] = None) -> str:
        
        filename = f"phase{phase}.txt"
        return load_prompt(filename, self.prompt_dir, context=context)

    def analyze_contract(self, contract_code: str, phase: int = 1, context: Dict[str, Any] = None) -> list | dict:
        
        prompt_with_context = self._get_prompt(phase, context)
        full_prompt = f"{prompt_with_context}\n\nContract Code:\n{contract_code}"

        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.2,
            max_output_tokens=2048
        )

        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            raw_text = response.text
            
            try:
                # First, attempt to parse the raw text directly.
                return json.loads(raw_text)
            except json.JSONDecodeError as e:
                # If parsing fails, it's likely the "missing comma" error.
                print(f"⚠️ Initial JSON decoding failed: {e}. Attempting to fix...")
                # Fix the common "}{" error by replacing it with "},{".
                fixed_text = raw_text.replace('}{', '},{')
                return json.loads(fixed_text)

        except Exception as e:
            print(f"⚠️ An unexpected error occurred calling Gemini API: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"Raw model output that caused error:\n{response.text}")
            return []