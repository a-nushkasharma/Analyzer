class LLM2Client:
    """Stub wrapper for LLM2 (e.g., Gemini), will replace .call with real API usage."""
    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def call(self, prompt: str) -> str:
        raise NotImplementedError("Wire this to LLM provider (Gemini)")
