from __future__ import annotations

import base64
import io
from typing import Optional

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from agent.openai_client import OpenAIClient
from agent.safety import build_chat_messages, sanitize_user_text


app = FastAPI(title="AI Friends - Empathetic Multimodal Friend")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = OpenAIClient()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/chat")
async def api_chat(
    text: str = Form(""),
    image_url: Optional[str] = Form(None),
) -> JSONResponse:
    user_text = sanitize_user_text(text)
    messages = build_chat_messages(user_text, image_url)
    reply = client.chat(messages)
    return JSONResponse({"reply": reply})


@app.post("/api/voice")
async def api_voice(
    text: str = Form("")
):
    user_text = sanitize_user_text(text)
    audio_bytes = client.tts_to_audio_bytes(user_text)
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")


# 간단한 이미지 업로드를 위한 엔드포인트 (선택적): 프론트에서 Data URL로 사용 가능
@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)) -> JSONResponse:
    content = await file.read()
    data_url = "data:" + (file.content_type or "image/png") + ";base64," + base64.b64encode(content).decode("utf-8")
    return JSONResponse({"image_url": data_url})


@app.post("/api/transcribe")
async def api_transcribe(file: UploadFile = File(...)) -> JSONResponse:
    content = await file.read()
    text = client.transcribe_audio(content, filename=file.filename or "audio.webm")
    return JSONResponse({"text": text})


def create_app() -> FastAPI:
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)


