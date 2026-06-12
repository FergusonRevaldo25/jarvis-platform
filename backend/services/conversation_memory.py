import json
import os
from typing import Dict, List
from datetime import datetime

class ConversationMemory:
    def __init__(self):
        self.memory_file = "temp/conversation_memory.json"
        self.conversation_history: List[Dict] = []
        self.max_history = 30
        self._load_memory()

    def _load_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    self.conversation_history = json.load(f)
        except:
            self.conversation_history = []

    def _save_memory(self):
        try:
            os.makedirs("temp", exist_ok=True)
            with open(self.memory_file, 'w') as f:
                json.dump(self.conversation_history[-self.max_history:], f, indent=2)
        except:
            pass

    async def get_context(self) -> List[Dict]:
        return self.conversation_history[-15:]

    async def add_exchange(self, user_input: str, assistant_response: Dict):
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_response.get("message", ""),
            "timestamp": datetime.now().isoformat()
        })
        self._save_memory()

    def add_exchange_nowait(self, user_input: str, assistant_response: Dict):
        self.conversation_history.append({
            "role": "user", "content": user_input, "timestamp": datetime.now().isoformat()
        })
        self.conversation_history.append({
            "role": "assistant", "content": assistant_response.get("message", ""), "timestamp": datetime.now().isoformat()
        })
        self._save_memory()

    async def clear(self):
        self.conversation_history = []
        self._save_memory()