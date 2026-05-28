from apps.config.settings import settings


class SarvamAIService:
    def __init__(self, api_key: str = settings.sarvam_api_key):
        self.api_key = api_key

    async def speech_to_text(self, audio_bytes: bytes, content_type: str) -> str:
        raise NotImplementedError("Sarvam speech-to-text will be implemented in the voice milestone.")

    async def text_to_speech(self, text: str) -> bytes:
        raise NotImplementedError("Sarvam text-to-speech will be implemented in the voice milestone.")
