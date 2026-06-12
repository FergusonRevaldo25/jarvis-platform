import os
import tempfile
from gtts import gTTS
from dotenv import load_dotenv

load_dotenv()

class TTSService:
    def __init__(self):
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        self.jarvis_voice_id = "wDsJlOXPqcvIUKdLXjDs"

    async def synthesize(self, text: str):
        if not text or len(text.strip()) == 0:
            return b""
        
        # Try ElevenLabs with JARVIS voice
        if self.elevenlabs_key and self.elevenlabs_key not in ["your_elevenlabs_key_here", ""]:
            try:
                from elevenlabs.client import ElevenLabs
                client = ElevenLabs(api_key=self.elevenlabs_key)
                audio = client.text_to_speech.convert(
                    text=text,
                    voice_id=self.jarvis_voice_id,
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128"
                )
                print(f"ElevenLabs JARVIS voice: {len(audio)} bytes")
                return audio
            except Exception as e:
                print(f"ElevenLabs failed, falling back to gTTS: {e}")

        # Fallback to gTTS
        try:
            output_path = f"temp/tts_{os.urandom(4).hex()}.mp3"
            os.makedirs("temp", exist_ok=True)
            
            tts = gTTS(text=text, lang='en', tld='co.uk', slow=False)
            tts.save(output_path)
            
            with open(output_path, 'rb') as f:
                audio_bytes = f.read()
            
            os.remove(output_path)
            print(f"gTTS: {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as e:
            print(f"gTTS error: {e}")
            return b""