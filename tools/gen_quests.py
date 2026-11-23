"""Village quests: advancement tab "마을 의뢰", stat-objective counted, chained, rewards via function."""
import json
from pathlib import Path

from tools.build import write_json, write_text
from tools.content_village import QUESTS, resolve
from tools.items import give_stack_command

NS = "create_rpg"


def _reward_name(spec, n):
    kind = spec[0]
    if kind == "mat":
        from tools.content import MATERIALS
        return f"{MATERIALS[spec[1]].name} ×{n}"
    if kind == "scroll":
        from tools.content import SCROLLS
        return f"{SCROLLS[spec[1]].name} ×{n}"
    if kind == "home":
        return f"귀환 주문서 ×{n}"
    names = {"minecraft:emerald": "에메랄드", "create:andesite_alloy": "안산암 합금"}
    return f"{names.get(spec[1], spec[1])} ×{n}"


def _player_conditions(q, prev):
    conds = [{"condition": "minecraft:entity_properties", "entity": "this", "predicate": {
        "type_specific": {"type": "minecraft:player", "advancements": {f"{NS}:quest/{prev}": True}}}}]
    if q.kind == "forge":
        conds.append({"condition": "minecraft:entity_properties", "entity": "this", "predicate": {
            "type_specific": {"type": "minecraft:player", "advancements": {f"{NS}:forge/{q.target}": True}}}})
    else:
        conds.append({"condition": "minecraft:entity_scores", "entity": "this", "scores": {q.objective: {"min": q.count}}})
    return conds


def generate(root: Path) -> None:
    d = root / "data" / NS
    a, f = d / "advancement" / "quest", d / "function"
    write_json(a / "root.json", {
        "display": {"icon": {"id": "minecraft:bell"}, "title": "마을 의뢰",
                    "description": "광장의 촌장 오르빈에게 말을 걸어 시작하세요",
                    "background": "minecraft:textures/gui/advancements/backgrounds/adventure.png",
                    "show_toast": False, "announce_to_chat": False},
        "criteria": {"start": {"trigger": "minecraft:impossible"}}})
    prev = "root"
    for i, q in enumerate(QUESTS):
        rewards = ", ".join(_reward_name(s, n) for s, n in q.rewards)
        frame = "challenge" if q.phase == "최종" else ("goal" if q.kind == "forge" else "task")
        write_json(a / f"{q.id}.json", {
            "parent": f"{NS}:quest/{prev}",
            "display": {"icon": {"id": q.icon}, "title": f"[{q.phase}] {q.title}",
                        "description": f"{q.goal}\n보상: {rewards}", "frame": frame,
                        "show_toast": True, "announce_to_chat": False},
            "criteria": {"done": {
                "trigger": "minecraft:player_killed_entity" if q.kind == "kill" else "minecraft:inventory_changed",
                "conditions": {"player": _player_conditions(q, prev)}}},
            "rewards": {"function": f"{NS}:quest/reward/{q.id}"}})
        body = [give_stack_command(*resolve(s), n) for s, n in q.rewards]
        body.append("tellraw @s " + json.dumps([
            {"text": "✔ 의뢰 완료: ", "color": "gold"}, {"text": q.title, "color": "yellow"},
            {"text": f"  (보상: {rewards})", "color": "gray"}], ensure_ascii=False))
        body.append("playsound minecraft:ui.toast.challenge_complete player @s")
        if i + 1 < len(QUESTS):
            nxt = QUESTS[i + 1]
            if nxt.kind != "forge":
                body.append(f"scoreboard players set @s {nxt.objective} 0")
            body.append("tellraw @s " + json.dumps([
                {"text": "다음 의뢰: ", "color": "aqua"}, {"text": f"「{nxt.title}」 {nxt.goal}", "color": "white"}],
                ensure_ascii=False))
        write_text(f / "quest" / "reward" / f"{q.id}.mcfunction", "\n".join(body) + "\n")
        prev = q.id
    load = f / "load.mcfunction"
    lines = [f"scoreboard objectives add {q.objective} {q.criterion}" for q in QUESTS if q.kind != "forge"]
    load.write_text(load.read_text(encoding="utf-8") + "\n".join(lines) + "\n", encoding="utf-8")
