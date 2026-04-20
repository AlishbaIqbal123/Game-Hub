from __future__ import annotations

import json
from pathlib import Path


class StorageManager:
    """Simple JSON-backed settings and score storage."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "state.json"
        self.state = {
            "settings": {
                "sound_enabled": True,
                "animations_enabled": True,
                "volume": 60,
            },
            "high_scores": {},
        }
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                # Deep-merge so partial JSON files don't wipe default keys
                if "settings" in data and isinstance(data["settings"], dict):
                    self.state["settings"].update(data["settings"])
                if "high_scores" in data and isinstance(data["high_scores"], dict):
                    self.state["high_scores"].update(data["high_scores"])
            except (json.JSONDecodeError, ValueError):
                # Corrupted file — keep defaults and overwrite on next save
                pass

    def save(self) -> None:
        self.path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def settings(self) -> dict:
        return self.state["settings"]

    def update_settings(self, updates: dict) -> None:
        self.state["settings"].update(updates)
        self.save()

    def high_score(self, game_key: str) -> int:
        return int(self.state["high_scores"].get(game_key, 0))

    def update_high_score(self, game_key: str, score: int) -> bool:
        score = int(score)
        if score > self.high_score(game_key):
            self.state["high_scores"][game_key] = score
            self.save()
            return True
        return False

    def has_seen_tutorial(self, game_key: str) -> bool:
        return bool(self.state.get("tutorials_seen", {}).get(game_key, False))

    def mark_tutorial_seen(self, game_key: str) -> None:
        if "tutorials_seen" not in self.state:
            self.state["tutorials_seen"] = {}
        self.state["tutorials_seen"][game_key] = True
        self.save()
