from typing import List, Dict, Optional
import os
from app.core.config import settings

# Provider interface with mock fallback

class LLMProvider:
    def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"OpenAI init failed: {e}")
                self.client = None

    def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        if not self.client:
            return MockProvider().generate(prompt, system)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", 0.2),
                max_tokens=kwargs.get("max_tokens", 800),
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"LLM error: {e}, fallback to mock")
            return MockProvider().generate(prompt, system)

class MockProvider(LLMProvider):
    def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        # Deterministic mock that respects evidence grounding
        # If prompt contains "EVIDENCE:" section, we attempt to summarize it
        if "EVIDENCE:" in prompt:
            evidence_part = prompt.split("EVIDENCE:")[-1].split("QUESTION:")[0].strip()
            if not evidence_part or evidence_part == "No evidence found." or len(evidence_part) < 20:
                return "I don't have sufficient evidence to answer this question based on the video content. The retrieved context does not contain relevant information with timestamps."
            # Return grounded mock
            lines = evidence_part.strip().split("\n")[:3]
            joined = " | ".join([l[:120] for l in lines])
            return f"Based on the video evidence: {joined}. Please see the cited timestamps for verification. (mock mode - configure OPENAI_API_KEY for full LLM generation)"
        # Generic mock
        if "summary" in prompt.lower():
            return "This video contains multiple scenes with spoken narration and visual events. Key moments are highlighted in the timeline with timestamps. (mock summary)"
        return "Mock response: evidence-grounded answer would appear here when LLM is configured. Retrieved evidence is shown in citations."

def get_llm_provider() -> LLMProvider:
    if settings.OPENAI_API_KEY:
        p = OpenAIProvider()
        if p.client:
            return p
    return MockProvider()
