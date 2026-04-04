import json
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_path = Path.home() / ".remarkable_tool_config.json"

    def load(self) -> dict:
        if self.config_path.exists():
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        return {"token": "", "email": ""}

    def save(self, config: dict):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(config), encoding="utf-8")