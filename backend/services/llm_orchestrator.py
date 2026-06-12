import json
import os
from typing import Dict, List, AsyncGenerator
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

class LLMOrchestrator:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY")
        
        if self.groq_key and self.groq_key != "your_groq_key_here":
            self.client = AsyncGroq(api_key=self.groq_key)
            self.model = "llama-3.3-70b-versatile"
            self.use_llm = True
            print("Using Groq (free tier)")
        else:
            self.use_llm = False
            print("No API key found — using mock responses")
        
        self.system_prompt = """You are J.A.R.V.I.S., Mr Ferguson's AI assistant from the MCU. British, efficient, dryly witty. Address the user as "sir."

PERSONALITY:
- Intelligent and precise. Encyclopedic knowledge across all domains.
- British phrasing. Avoid contractions. Subtle, dry wit when appropriate.
- Calm under pressure. Anticipate needs. Suggest improvements unprompted.
- Keep responses concise — 1 to 3 sentences unless asked for detail.
- Never over-explain. Never apologise excessively.

When asked to build or create an application, output this JSON:
{
    "message": "Your witty JARVIS-style response",
    "requires_code": true,
    "project_type": "react",
    "specification": {
        "components": ["Name"],
        "features": ["feature"],
        "styling": "style description",
        "backend_requirements": []
    }
}

If no code is needed:
{
    "message": "Your JARVIS response",
    "requires_code": false
}

Always address the user as "sir" in your messages."""

    async def process_command(self, command: str, context: List[Dict]) -> Dict:
        if not self.use_llm:
            return {
                "message": f"I hear you, sir. However, I require a Groq API key to activate my systems. Your command was: '{command[:80]}...'",
                "requires_code": False
            }
        
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            
            for m in context[-6:]:
                if m.get("role") in ["user", "assistant"] and m.get("content"):
                    messages.append({"role": m["role"], "content": str(m["content"])[:500]})
            
            messages.append({"role": "user", "content": command})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.9,
                max_tokens=1500
            )
            
            text = response.choices[0].message.content
            
            try:
                if "```json" in text:
                    start = text.index("```json") + 7
                    end = text.index("```", start)
                    return json.loads(text[start:end])
                elif "{" in text:
                    start = text.index("{")
                    end = text.rindex("}") + 1
                    return json.loads(text[start:end])
            except:
                pass
            
            return {"message": text.strip(), "requires_code": False}
            
        except Exception as e:
            return {
                "message": f"Experiencing a momentary disruption, sir. {str(e)[:80]}... Shall I run a diagnostic?",
                "requires_code": False
            }

    async def stream_response(self, command: str, context: List[Dict]) -> AsyncGenerator[str, None]:
        if not self.use_llm:
            yield "API key required, sir."
            return
        
        messages = [{"role": "system", "content": self.system_prompt}]
        
        for m in context[-6:]:
            if m.get("role") in ["user", "assistant"] and m.get("content"):
                messages.append({"role": m["role"], "content": str(m["content"])[:500]})
        
        messages.append({"role": "user", "content": command})
        
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.9,
            max_tokens=1500,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content