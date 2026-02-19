import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from autoexpert.config import settings

class SkillLibrary:
    def __init__(self, directory: Path = settings.SKILL_LIBRARY_DIR):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.skills: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self):
        for file in self.directory.glob("*.json"):
            try:
                with open(file, "r") as f:
                    skill_data = json.load(f)
                    self.skills[skill_data["name"]] = skill_data
            except Exception as e:
                print(f"Error loading skill {file}: {e}")

    def save_skill(self, name: str, code: str, description: str, win_rate: float, metadata: Optional[Dict[str, Any]] = None):
        skill_data = {
            "name": name,
            "code": code,
            "description": description,
            "win_rate": win_rate,
            "metadata": metadata or {}
        }
        self.skills[name] = skill_data
        file_path = self.directory / f"{name.replace(' ', '_').lower()}.json"
        with open(file_path, "w") as f:
            json.dump(skill_data, f, indent=4)

    def get_best_skill(self) -> Optional[Dict[str, Any]]:
        if not self.skills:
            return None
        return max(self.skills.values(), key=lambda x: x["win_rate"])

    def get_all_skills_summary(self) -> str:
        if not self.skills:
            return "No skills learned yet."
        summary = []
        for name, data in self.skills.items():
            summary.append(f"- {name}: {data['description']} (Win Rate: {data['win_rate']:.2%})")
        return "\n".join(summary)
