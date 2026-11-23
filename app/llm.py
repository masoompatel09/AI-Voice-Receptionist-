from groq import AsyncGroq

from app.config import settings

client = AsyncGroq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """You are a friendly AI receptionist for a small business.
You help callers book appointments and answer frequently asked questions.
Keep your responses short and conversational, like a real phone call.
Do not use markdown or bullet points — you're speaking, not writing."""


async def get_llm_response(conversation_history: list[dict]) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=150,
    )
    return response.choices[0].message.content