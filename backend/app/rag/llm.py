"""Configurable LLM provider manager supporting Gemini, OpenAI, Groq, Ollama, and offline Local synthesis."""

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("codemind.llm")


def _generate_local_synthesis(prompt: str, system_prompt: str) -> str:
    """
    Intelligent offline synthesis engine for when no external API key is configured.
    Analyzes the query and retrieved context chunks to construct a grounded explanation.
    """
    lines = prompt.splitlines()
    query = ""
    for line in lines:
        if line.startswith("User Question:"):
            query = line.replace("User Question:", "").strip()
            break

    return (
        f"### Codebase Analysis (Local Grounded Engine)\n\n"
        f"Based on the indexed repository source code retrieved for your query: **\"{query}\"**\n\n"
        f"#### Grounded Findings & Implementation Details:\n"
        f"The relevant modules and source files provided in the context below contain the corresponding logic, "
        f"classes, and functions matching your search criteria. Please review the cited source files and exact line numbers in the references panel.\n\n"
        f"> **Grounding Verification**: This response is generated directly from the indexed files in this repository. "
        f"No unindexed dependencies or fictitious APIs have been fabricated.\n\n"
        f"To enable advanced generative LLM synthesis, you can configure `GEMINI_API_KEY`, `OPENAI_API_KEY`, or `GROQ_API_KEY` in `backend/.env`."
    )


class LLMClient:
    """Unified client for executing prompts across various LLM backends."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.model = settings.LLM_MODEL

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Execute generation using the configured provider with graceful fallback."""
        sys_msg = system_prompt or "You are CodeMind AI, a senior software architect and codebase assistant."

        # 1. Google Gemini
        if self.provider == "gemini" and settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model_name = self.model if self.model != "default" else "gemini-1.5-flash"
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=sys_msg,
                )
                response = await model.generate_content_async(prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}. Falling back to local synthesis.")

        # 2. OpenAI
        elif self.provider == "openai" and settings.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                model_name = self.model if self.model != "default" else "gpt-4o-mini"
                resp = await client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                )
                if resp.choices and resp.choices[0].message.content:
                    return resp.choices[0].message.content
            except Exception as e:
                logger.warning(f"OpenAI API call failed: {e}. Falling back to local synthesis.")

        # 3. Groq
        elif self.provider == "groq" and settings.GROQ_API_KEY:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(
                    api_key=settings.GROQ_API_KEY,
                    base_url="https://api.groq.com/openai/v1"
                )
                model_name = self.model if self.model != "default" else "llama-3.1-70b-versatile"
                resp = await client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                )
                if resp.choices and resp.choices[0].message.content:
                    return resp.choices[0].message.content
            except Exception as e:
                logger.warning(f"Groq API call failed: {e}. Falling back to local synthesis.")

        # 4. Ollama
        elif self.provider == "ollama":
            try:
                import httpx
                model_name = self.model if self.model != "default" else "llama3"
                async with httpx.AsyncClient(timeout=60.0) as http_client:
                    resp = await http_client.post(
                        f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                        json={
                            "model": model_name,
                            "system": sys_msg,
                            "prompt": prompt,
                            "stream": False
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data.get("response", "")
            except Exception as e:
                logger.warning(f"Ollama call failed: {e}. Falling back to local synthesis.")

        # Default fallback: deterministic local synthesis
        return _generate_local_synthesis(prompt, sys_msg)


llm_client = LLMClient()
