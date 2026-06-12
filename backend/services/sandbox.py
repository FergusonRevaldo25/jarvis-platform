import tempfile
import os
from pathlib import Path
from typing import Dict

class SandboxService:
    def __init__(self):
        self.active_projects = {}

    async def create_preview(self, code_data: Dict) -> str:
        project_id = os.urandom(4).hex()
        project_dir = Path(f"temp/preview_{project_id}")
        project_dir.mkdir(parents=True, exist_ok=True)

        for filepath, content in code_data.get("files", {}).items():
            full_path = project_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)

        self.active_projects[project_id] = str(project_dir)
        return f"http://localhost:3000/preview/{project_id}"

    async def deploy(self, code_data: Dict, config: Dict = None) -> str:
        return await self.create_preview(code_data)