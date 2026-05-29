import asyncio
import json
import logging
from urllib import error, request

from apps.config.settings import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, base_url: str = settings.ollama_base_url, model: str = settings.ollama_model):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.backend = settings.llm_backend.lower().strip()
        self.llama_cpp_base_url = settings.llama_cpp_base_url.rstrip("/")
        self.gemini_api_key = settings.gemini_api_key
        self.gemini_model = settings.gemini_model
        self.gemini_base_url = settings.gemini_base_url.rstrip("/")

    def _build_prompt(self, interview_context: str, count: int) -> str:
        return (
            "You are an expert interview assistant.\n"
            "Generate high-quality mock interview questions.\n"
            "Return ONLY valid JSON in this format:\n"
            '{"questions":[{"question_text":"...","question_type":"technical|hr|behavioral","difficulty":"easy|medium|hard","category":"...","expected_answer":"..."}]}\n'
            f"Generate exactly {count} questions.\n"
            f"Context:\n{interview_context}"
        )

    def _extract_questions(self, response_text: str, provider_name: str) -> list[dict]:
        response_text = response_text.strip()
        if response_text.startswith("```"):
            response_text = response_text.removeprefix("```json").removeprefix("```").strip()
            response_text = response_text.removesuffix("```").strip()
        content = json.loads(response_text)
        questions = content.get("questions", [])
        if not isinstance(questions, list):
            raise ValueError(f"Invalid questions format from {provider_name}.")
        return questions

    def _provider_name(self) -> str:
        if self.backend == "llama_cpp":
            return "llama.cpp"
        if self.backend == "gemini":
            return "Gemini"
        return "Ollama"

    async def generate_questions(self, interview_context: str, count: int = 5) -> list[dict]:
        prompt = self._build_prompt(interview_context=interview_context, count=count)
        provider = self._provider_name()
        logger.info("LLM question generation started provider=%s count=%s", provider, count)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }

        def _call_ollama() -> list[dict]:
            endpoint = f"{self.base_url}/api/generate"
            logger.info("Calling Ollama generate endpoint=%s model=%s", endpoint, self.model)
            req = request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=90) as resp:
                raw = resp.read().decode("utf-8")
            parsed = json.loads(raw)
            response_text = parsed.get("response", "{}")
            questions = self._extract_questions(response_text=response_text, provider_name="Ollama")
            logger.info("Ollama returned questions count=%s", len(questions))
            return questions

        def _call_llama_cpp() -> list[dict]:
            endpoint = f"{self.llama_cpp_base_url}/completion"
            logger.info("Calling llama.cpp completion endpoint=%s", endpoint)
            llama_payload = {
                "prompt": prompt,
                "n_predict": 800,
                "temperature": 0.4,
                "top_p": 0.9,
                "stop": ["\n\n\n"],
            }
            req = request.Request(
                endpoint,
                data=json.dumps(llama_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
            parsed = json.loads(raw)
            response_text = parsed.get("content", "{}")
            questions = self._extract_questions(response_text=response_text, provider_name="llama.cpp")
            logger.info("llama.cpp returned questions count=%s", len(questions))
            return questions

        def _call_gemini() -> list[dict]:
            if not self.gemini_api_key:
                raise RuntimeError("GEMINI_API_KEY is required when LLM_BACKEND=gemini.")

            endpoint = f"{self.gemini_base_url}/models/{self.gemini_model}:generateContent"
            logger.info("Calling Gemini generateContent model=%s", self.gemini_model)
            gemini_payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt,
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.4,
                    "topP": 0.9,
                    "responseMimeType": "application/json",
                },
            }
            req = request.Request(
                endpoint,
                data=json.dumps(gemini_payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.gemini_api_key,
                },
                method="POST",
            )
            with request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
            parsed = json.loads(raw)
            candidates = parsed.get("candidates", [])
            if not candidates:
                raise ValueError("Gemini returned no candidates.")
            parts = candidates[0].get("content", {}).get("parts", [])
            response_text = "".join(part.get("text", "") for part in parts)
            questions = self._extract_questions(response_text=response_text, provider_name="Gemini")
            logger.info("Gemini returned questions count=%s", len(questions))
            return questions

        try:
            if self.backend == "llama_cpp":
                questions = await asyncio.to_thread(_call_llama_cpp)
                logger.info("LLM question generation finished provider=%s count=%s", provider, len(questions))
                return questions
            if self.backend == "gemini":
                questions = await asyncio.to_thread(_call_gemini)
                logger.info("LLM question generation finished provider=%s count=%s", provider, len(questions))
                return questions
            questions = await asyncio.to_thread(_call_ollama)
            logger.info("LLM question generation finished provider=%s count=%s", provider, len(questions))
            return questions
        except error.URLError as exc:
            provider = self._provider_name()
            logger.exception("Unable to reach LLM provider=%s", provider)
            raise RuntimeError(f"Unable to reach {provider} service.") from exc
        except json.JSONDecodeError as exc:
            provider = self._provider_name()
            logger.exception("Invalid JSON returned by LLM provider=%s", provider)
            raise RuntimeError(f"Invalid JSON returned by {provider}.") from exc
        except Exception as exc:
            logger.exception("LLM question generation failed provider=%s", provider)
            raise RuntimeError(str(exc)) from exc
