import httpx

from app.config import settings

DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"


async def synthesize_speech(text: str):
    """
    Streams audio from Deepgram Aura TTS in mulaw 8kHz — matches
    Twilio's expected format directly, no conversion needed.
    """
    params = {
        "model": "aura-asteria-en",
        "encoding": "mulaw",
        "sample_rate": "8000",
    }
    headers = {
        "Authorization": f"Token {settings.deepgram_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"text": text}

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST", DEEPGRAM_TTS_URL, params=params, headers=headers, json=payload, timeout=30
        ) as response:
            async for chunk in response.aiter_bytes(chunk_size=4096):
                if chunk:
                    yield chunk