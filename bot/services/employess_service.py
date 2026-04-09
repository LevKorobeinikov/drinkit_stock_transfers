from __future__ import annotations

import json
from pathlib import Path


class EmployeeService:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._save({"employees": ["Алина", "Полина", "Варя", "Соня"]})

    def list(self) -> list[str]:
        return self._load()["employees"]

    def add(self, name: str) -> None:
        name = name.strip()
        if not name:
            raise ValueError("Имя не может быть пустым")
        data = self._load()
        if name in data["employees"]:
            raise ValueError("Сотрудник уже есть в списке")
        data["employees"].append(name)
        self._save(data)

    def remove(self, name: str) -> None:
        data = self._load()
        if name not in data["employees"]:
            raise ValueError("Такого сотрудника нет в списке")
        data["employees"].remove(name)
        self._save(data)

    def _load(self) -> dict:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
