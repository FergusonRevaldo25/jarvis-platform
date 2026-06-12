import json
from typing import Dict, List
from pathlib import Path

class CodeGenerator:
    def __init__(self):
        self.templates_path = Path("templates")
        self.templates_path.mkdir(exist_ok=True)

    async def generate(self, specification: Dict, project_type: str = "react") -> Dict:
        files = await self._generate_react_app(specification)
        return {
            "files": files,
            "project_type": project_type,
            "entry_point": "public/index.html"
        }

    async def _generate_react_app(self, spec: Dict) -> Dict[str, str]:
        files = {}

        files["package.json"] = json.dumps({
            "name": "jarvis-generated-app",
            "version": "1.0.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build"
            }
        }, indent=2)

        files["public/index.html"] = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis App</title>
</head>
<body>
    <div id="root"></div>
</body>
</html>"""

        components = spec.get("components", ["Header", "Main", "Footer"])

        for component in components:
            name = component if isinstance(component, str) else component.get("name", "Component")
            files[f"src/components/{name}.js"] = self._generate_component(name)
            files[f"src/components/{name}.css"] = self._generate_styles(name)

        files["src/App.js"] = self._generate_app(components)
        files["src/App.css"] = self._generate_app_styles()

        files["src/index.js"] = """
import React from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
"""
        return files

    def _generate_component(self, name: str) -> str:
        return f"""import React from 'react';
import './{name}.css';

const {name} = () => {{
    return (
        <div className="{name.lower()}-container">
            <h2>{name}</h2>
            <p>This is the {name} component.</p>
        </div>
    );
}};

export default {name};
"""

    def _generate_styles(self, name: str) -> str:
        return f""".{name.lower()}-container {{
    padding: 20px;
    margin: 10px;
    border-radius: 8px;
    background: #ffffff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}
"""

    def _generate_app(self, components: List) -> str:
        comp_names = [c if isinstance(c, str) else c.get("name", "Component") for c in components]
        imports = "\n".join([f"import {n} from './components/{n}';" for n in comp_names])
        return f"""import React from 'react';
{imports}

const App = () => {{
    return (
        <div className="app">
            <header className="app-header">
                <h1>Generated Application</h1>
            </header>
            <main className="app-main">
                {'\n                '.join([f'<{n} />' for n in comp_names])}
            </main>
        </div>
    );
}};

export default App;
"""

    def _generate_app_styles(self) -> str:
        return """
.app {
    min-height: 100vh;
    background: #f0f2f5;
}
.app-header {
    background: #1a1a2e;
    color: white;
    padding: 20px;
    text-align: center;
}
.app-main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}
"""