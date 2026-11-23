import base64
import logging

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)

from app.config import settings
from app.llm import get_llm_response
from app.tts import synthesize_speech

logger = logging.getLogger("voice-receptionist")


class CallSession:
    def __init__(self, websocket):
        self.websocket = websocket
        self.stream_sid = None
        self.dg_connection = None
        self.conversation_history = []

    async def start_deepgram(self):
        config = DeepgramClientOptions(options={"keepalive": "true"})
        deepgram = DeepgramClient(settings.deepgram_api_key, config)
        self.dg_connection = deepgram.listen.asynclive.v("1")

        async def on_transcript(self_inner, result, **kwargs):
            transcript = result.channel.alternatives[0].transcript
            if not transcript:
                return

            if result.is_final:
                logger.info(f"Caller said: {transcript}")
                self.conversation_history.append({"role": "user", "content": transcript})

                reply = await get_llm_response(self.conversation_history)
                logger.info(f"AI reply: {reply}")
                self.conversation_history.append({"role": "assistant", "content": reply})

                await self.speak(reply)

        self.dg_connection.on(LiveTranscriptionEvents.Transcript, on_transcript)

        options = LiveOptions(
            model="nova-2",
            language="en-US",
            encoding="mulaw",
            sample_rate=8000,
            channels=1,
            interim_results=True,
        )
        await self.dg_connection.start(options)
        logger.info("Deepgram connection started")

    async def speak(self, text: str):
        """Convert text to speech and stream it back to the caller over Twilio."""
        async for audio_chunk in synthesize_speech(text):
            payload = base64.b64encode(audio_chunk).decode("utf-8")
            message = {
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {"payload": payload},
            }
            await self.websocket.send_json(message)

    async def handle_twilio_message(self, message: dict):
        event = message.get("event")

        if event == "start":
            self.stream_sid = message["start"]["streamSid"]
            logger.info(f"Call started: {self.stream_sid}")
            await self.start_deepgram()

        elif event == "media":
            payload = message["media"]["payload"]
            audio_bytes = base64.b64decode(payload)
            if self.dg_connection:
                await self.dg_connection.send(audio_bytes)

        elif event == "stop":
            logger.info("Call ended")

    async def close(self):
        if self.dg_connection:
            await self.dg_connection.finish()
        logger.info("Session closed")