from apps.config.settings import settings


class OllamaService:
    def __init__(self, base_url: str = settings.ollama_base_url, model: str = settings.ollama_model):
        self.base_url = base_url
        self.model = model

    async def generate_question(self, interview_context: str) -> str:
        raise NotImplementedError("Ollama question generation will be implemented in the AI milestone.")

    async def evaluate_answer(self, question: str, answer: str) -> dict:
        raise NotImplementedError("Ollama answer evaluation will be implemented in the AI milestone.")
