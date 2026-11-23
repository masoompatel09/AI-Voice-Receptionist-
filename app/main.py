import logging

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Connect

from app.config import settings
from app.call_session import CallSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-receptionist")

app = FastAPI(title="AI Voice Receptionist")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/voice")
async def voice_webhook(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    logger.info(f"Incoming call {call_sid}")

    stream_url = settings.public_base_url.replace("https://", "wss://").replace(
        "http://", "ws://"
    )

    vr = VoiceResponse()
    connect = Connect()
    connect.stream(url=f"{stream_url}/media-stream")
    vr.append(connect)

    return Response(content=str(vr), media_type="application/xml")


@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    await websocket.accept()
    session = CallSession(websocket)
    logger.info("Media stream connected")

    try:
        while True:
            message = await websocket.receive_json()
            await session.handle_twilio_message(message)
    except WebSocketDisconnect:
        logger.info("Media stream disconnected")
    finally:
        await session.close()