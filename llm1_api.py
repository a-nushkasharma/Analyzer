class LLM1Client:
    """Stub wrapper for LLM1 (e.g., OpenAI), will replace.call with real API usage."""
    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def call(self, prompt: str) -> str:
        raise NotImplementedError("Wire this to LLM provider")
