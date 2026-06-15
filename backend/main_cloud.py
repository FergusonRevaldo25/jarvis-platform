from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import base64
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS

load_dotenv()

app = FastAPI(title="Jarvis Cloud API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are J.A.R.V.I.S., Tony Stark's AI. British, witty, concise. Address user as "sir." Keep responses 1-3 sentences. Dry wit."""

conversation_history = []

@app.post("/api/voice-command")
async def voice_command(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return JSONResponse({
            "transcript": "Cloud mode active",
            "response": {
                "message": "Voice transcription unavailable on cloud instance, sir. Use the text chat endpoint at /api/chat.",
                "requires_code": False
            },
            "audio_response": None
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(request: dict):
    global conversation_history
    try:
        text = request.get("text", "")
        if not text:
            return {"message": "I didn't catch that, sir."}
        
        conversation_history.append({"role": "user", "content": text})
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *conversation_history[-10:]
        ]
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.9,
            max_tokens=500
        )
        
        reply = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": reply})
        
        audio_b64 = None
        try:
            tts = gTTS(text=reply, lang='en', tld='co.uk', slow=False)
            tts_path = f"/tmp/tts_{os.urandom(4).hex()}.mp3"
            tts.save(tts_path)
            with open(tts_path, 'rb') as f:
                audio_b64 = base64.b64encode(f.read()).decode('utf-8')
            os.remove(tts_path)
        except:
            pass
        
        return {
            "message": reply,
            "audio_response": audio_b64
        }
    except Exception as e:
        return {"message": f"Disruption, sir. {str(e)[:80]}"}

@app.get("/api/health")
async def health():
    return {"status": "operational", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    return {"name": "J.A.R.V.I.S. Cloud API", "endpoints": ["/api/chat", "/api/voice-command", "/api/health"]}

if __name__ == "__main__":
    uvicorn.run("main_cloud:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))