from __future__ import annotations

import random

PRIMARY_ZONES = ["КМ/Бар", "МС/Зал"]
SECONDARY_ZONES = ["Туалет", "Бэк"]


def build_assignment(employees: list[str]) -> dict[str, list[str]]:
    if len(employees) != 2:
        raise ValueError("Нужно ровно 2 сотрудника")
    shuffled = employees[:]
    random.shuffle(shuffled)
    assignment: dict[str, list[str]] = {employee: [] for employee in shuffled}
    for employee, zone in zip(shuffled, PRIMARY_ZONES):
        assignment[employee].append(zone)
    for zone in SECONDARY_ZONES:
        candidates = [employee for employee, zones in assignment.items() if len(zones) < 2]
        if not candidates:
            raise RuntimeError("Не осталось кандидатов для дополнительной зоны")
        chosen = random.choice(candidates)
        assignment[chosen].append(zone)
    return assignment


def format_assignment(assignment: dict[str, list[str]]) -> str:
    lines = ["Распределение зон на сегодня:\n"]
    for employee, zones in assignment.items():
        lines.append(f"👤 {employee}")
        for zone in zones:
            lines.append(f"— {zone}")
        lines.append("")
    return "\n".join(lines).strip()
