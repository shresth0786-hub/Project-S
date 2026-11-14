"""
Content Generation Module — modular, separate from core pipeline
- Video-to-summary (via LLM)
- Summary-to-storyboard
- Text-to-image via external API (OpenAI DALL·E) with mock fallback
- TTS narration placeholder
"""
from typing import Optional
from app.services.llm import get_llm_provider

def generate_storyboard(summary: str) -> list:
    provider = get_llm_provider()
    prompt = f"Convert summary into 4-scene storyboard with timestamps and image prompts.\nSummary: {summary}\nReturn JSON list with scene, timestamp, prompt."
    out = provider.generate(prompt, system="You are storyboard generator.")
    # Mock parse: split sentences
    scenes = []
    for i, s in enumerate(summary.split(".")[:4]):
        if s.strip():
            scenes.append({"scene": i+1, "timestamp": i*15, "prompt": s.strip()[:100], "description": s.strip()})
    return scenes

def text_to_image(prompt: str) -> str:
    # Interface for external model API
    try:
        from app.core.config import settings
        if settings.OPENAI_API_KEY:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            resp = client.images.generate(model="dall-e-3", prompt=prompt, n=1, size="1024x1024")
            return resp.data[0].url or "https://via.placeholder.com/1024x1024?text=VisionX+Generated"
    except Exception as e:
        print(f"T2I fallback: {e}")
    return f"mock://generated-image?prompt={prompt[:40]}"

def text_to_speech(text: str, out_path: str) -> str:
    # Placeholder for TTS (e.g., OpenAI TTS / Coqui)
    # Write mock mp3
    try:
        with open(out_path, "wb") as f:
            f.write(b"ID3")  # minimal
        return out_path
    except Exception as e:
        print(f"TTS fallback: {e}")
        return ""
