from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import base64
import subprocess
import psutil
import pyautogui
import webbrowser
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Jarvis AI Builder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stt_service = None
llm_orchestrator = None
memory_service = None
tts_service = None

def get_stt():
    global stt_service
    if stt_service is None:
        from services.speech_to_text import SpeechToTextService
        stt_service = SpeechToTextService(model_size="base")
    return stt_service

def get_llm():
    global llm_orchestrator
    if llm_orchestrator is None:
        from services.llm_orchestrator import LLMOrchestrator
        llm_orchestrator = LLMOrchestrator()
    return llm_orchestrator

def get_memory():
    global memory_service
    if memory_service is None:
        from services.conversation_memory import ConversationMemory
        memory_service = ConversationMemory()
    return memory_service

def get_tts():
    global tts_service
    if tts_service is None:
        from services.tts_service import TTSService
        tts_service = TTSService()
    return tts_service

def execute_system_command(command: str) -> str:
    command_lower = command.lower()
    
    try:
        if "volume" in command_lower:
            if "up" in command_lower or "increase" in command_lower:
                for _ in range(10): pyautogui.press('volumeup')
                return "Volume increased, sir."
            elif "down" in command_lower or "decrease" in command_lower:
                for _ in range(10): pyautogui.press('volumedown')
                return "Volume decreased, sir."
            elif "mute" in command_lower:
                pyautogui.press('volumemute')
                return "Muted, sir."

        if "play" in command_lower and ("music" in command_lower or "song" in command_lower or "spotify" in command_lower or "track" in command_lower):
            song = command_lower
            for word in ["play", "music", "song", "spotify", "track", "on spotify", "by"]:
                song = song.replace(word, "")
            song = song.strip()
            if song:
                webbrowser.open(f'spotify:search:{song.replace(" ", "%20")}')
                return f"Searching Spotify for '{song}', sir."
            else:
                pyautogui.press('playpause')
                return "Playing music, sir."
        if command_lower in ["pause", "pause music", "stop music"]:
            pyautogui.press('playpause'); return "Paused, sir."
        if command_lower in ["resume", "resume music"]:
            pyautogui.press('playpause'); return "Resuming, sir."
        if command_lower in ["next", "next song", "skip"]:
            pyautogui.press('nexttrack'); return "Next track, sir."
        if command_lower in ["previous", "previous song"]:
            pyautogui.press('prevtrack'); return "Previous, sir."

        if "open" in command_lower:
            if "chrome" in command_lower or "browser" in command_lower:
                webbrowser.open('https://google.com'); return "Chrome opened, sir."
            elif "notepad" in command_lower:
                subprocess.Popen('notepad.exe'); return "Notepad, sir."
            elif "calculator" in command_lower:
                subprocess.Popen('calc.exe'); return "Calculator, sir."
            elif "explorer" in command_lower or "files" in command_lower:
                subprocess.Popen('explorer.exe'); return "File Explorer, sir."
            elif "cmd" in command_lower or "terminal" in command_lower:
                subprocess.Popen('cmd.exe'); return "Command Prompt, sir."
            elif "spotify" in command_lower:
                os.system('start spotify:'); return "Spotify, sir."
            elif "youtube" in command_lower:
                webbrowser.open('https://youtube.com'); return "YouTube, sir."
            elif "github" in command_lower:
                webbrowser.open('https://github.com'); return "GitHub, sir."
            elif "camera" in command_lower or "webcam" in command_lower:
                subprocess.Popen('start microsoft.windows.camera:', shell=True); return "Camera, sir."

        if "battery" in command_lower:
            battery = psutil.sensors_battery()
            if battery: return f"Battery at {battery.percent}%, {'plugged in' if battery.power_plugged else 'on battery'}, sir."
        if "cpu" in command_lower:
            return f"CPU at {psutil.cpu_percent()}%, sir."
        if "ram" in command_lower or "memory" in command_lower:
            mem = psutil.virtual_memory()
            return f"RAM at {mem.percent}%, {mem.available//(1024*1024)}MB free, sir."
        
        if "lock" in command_lower and ("pc" in command_lower or "computer" in command_lower):
            subprocess.run('rundll32.exe user32.dll,LockWorkStation'); return "Locked, sir."
        if "screenshot" in command_lower:
            path = os.path.join(os.path.expanduser("~"), "Desktop", f"jarvis_ss_{datetime.now().strftime('%H%M%S')}.png")
            pyautogui.screenshot(path); return "Screenshot saved, sir."
        if "minimize" in command_lower:
            pyautogui.hotkey('win', 'd'); return "Minimized, sir."
        
        return None
    except Exception as e:
        return f"Error: {str(e)[:50]}"

@app.post("/api/voice-command")
async def process_voice_command(file: UploadFile = File(...)):
    audio_path = None
    try:
        os.makedirs("temp", exist_ok=True)
        audio_path = f"temp/{file.filename}"
        content = await file.read()
        
        if len(content) < 500:
            return JSONResponse({"transcript": "", "response": {"message": "", "requires_code": False}, "audio_response": None})
        
        with open(audio_path, "wb") as f:
            f.write(content)

        transcript = await get_stt().transcribe(audio_path)
        if not transcript.strip():
            return JSONResponse({"transcript": "", "response": {"message": "", "requires_code": False}, "audio_response": None})

        print(f"User: {transcript}")

        sys_result = execute_system_command(transcript)
        if sys_result:
            response = {"message": sys_result, "requires_code": False}
            get_memory().add_exchange_nowait(transcript, response)
            audio_bytes = await get_tts().synthesize(sys_result)
            return JSONResponse({
                "transcript": transcript, "response": response,
                "audio_response": base64.b64encode(audio_bytes).decode('utf-8') if audio_bytes else None
            })

        context = await get_memory().get_context()
        response = await get_llm().process_command(command=transcript, context=context)

        if response.get("requires_code"):
            from services.code_generator import CodeGenerator
            gen = CodeGenerator()
            generated_code = await gen.generate(
                specification=response["specification"],
                project_type=response.get("project_type", "react")
            )
            response["code"] = generated_code

        await get_memory().add_exchange(transcript, response)
        audio_bytes = await get_tts().synthesize(response.get("message", ""))
        
        return JSONResponse({
            "transcript": transcript, "response": response,
            "audio_response": base64.b64encode(audio_bytes).decode('utf-8') if audio_bytes else None
        })

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if audio_path and os.path.exists(audio_path): os.remove(audio_path)

@app.get("/api/health")
async def health_check():
    return {"status": "operational", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)