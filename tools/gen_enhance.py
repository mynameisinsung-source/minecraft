"""+1..+10 enhancement: drinkable scrolls -> consume_item advancement -> function -> item modifier.

Level is stored in minecraft:custom_model_data (NOT custom_data): neoforge:components ingredients
compare custom_data exactly, so touching it would stop enhanced gear from entering tier-up recipes.
"""
import json
from pathlib import Path

from tools.build import write_json, write_text
from tools.content import (ARMOR_SLOT, ENH_BASE_CAP, ENH_CAPS, ENH_MAX, ENH_MAX_BONUS_HEALTH, ENH_PER_LEVEL,
                           GEAR_SLOTS, NAMESPACE, SCROLLS, SLOT_NAME, TIERS, Scroll)
from tools.gen_recipes import gear_id
from tools.items import give_stack_command, material_ingredient, rpg_components

OBJ = "rpg_tmp"
OFF = "weapon.offhand"


def scroll_components(s: Scroll) -> dict:
    lore = [f"+{s.lo} ~ +{s.hi} 강화용", "강화할 RPG 장비를 왼손에 들고 마시세요"]
    return rpg_components(f"scroll_{s.grade}", s.name, lore, glint=True, extra={
        "minecraft:potion_contents": {"potion": "minecraft:mundane", "custom_color": s.potion_color},
        "minecraft:max_stack_size": 16})


def _slot_eq(slot):
    return "mainhand" if slot in ("sword", "pickaxe") else ARMOR_SLOT[slot]


def enhance_modifier(tier, slot, k) -> list:
    attr, per, op = ENH_PER_LEVEL["armor" if slot in ARMOR_SLOT else slot]
    eq = _slot_eq(slot)
    mods = [{"attribute": f"minecraft:{attr}", "id": f"{NAMESPACE}:enhance", "amount": round(per * k, 4),
             "operation": op, "slot": eq}]
    if k == ENH_MAX:
        mods.append({"attribute": "minecraft:generic.max_health", "id": f"{NAMESPACE}:enhance_bonus",
                     "amount": ENH_MAX_BONUS_HEALTH, "operation": "add_value", "slot": eq})
    return [
        {"function": "minecraft:set_components", "components": {"minecraft:custom_model_data": k}},
        {"function": "minecraft:set_attributes", "replace": False, "modifiers": mods},
        {"function": "minecraft:set_name", "target": "custom_name",
         "name": {"text": f"{tier.name} {SLOT_NAME[slot]} +{k}", "italic": False, "color": tier.color}},
    ]


def _tell(cond, parts, color):
    return f"execute {cond} run tellraw @s " + json.dumps([{"text": "", "color": color}] + parts, ensure_ascii=False)


def _score(name):
    return {"score": {"name": name, "objective": OBJ}}


def use_function(s: Scroll) -> str:
    sb = f"scoreboard players"
    L = [f"advancement revoke @s only {NAMESPACE}:enhance/drink_{s.grade}",
         f"{sb} set #err {OBJ} 0", f"{sb} set #gear {OBJ} 0", f"{sb} set #lvl {OBJ} 0"]
    gears = [(t, slot) for t in TIERS for slot in GEAR_SLOTS]
    for t, slot in gears:
        L.append(f'execute if items entity @s {OFF} *[minecraft:custom_data~{{{NAMESPACE}:"{gear_id(t, slot)}"}}] '
                 f"run {sb} set #gear {OBJ} 1")
    for k in range(1, ENH_MAX + 1):
        L.append(f"execute if items entity @s {OFF} *[minecraft:custom_model_data={k}] run {sb} set #lvl {OBJ} {k}")
    L.append(f"{sb} set #cap {OBJ} {ENH_BASE_CAP}")
    for tag, cap in ENH_CAPS.items():
        L.append(f"execute if entity @s[tag={tag}] run {sb} set #cap {OBJ} {cap}")
    L += [f"{sb} operation #next {OBJ} = #lvl {OBJ}", f"{sb} add #next {OBJ} 1",
          f"execute if score #gear {OBJ} matches 0 run {sb} set #err {OBJ} 1",
          f"execute if score #err {OBJ} matches 0 if score #lvl {OBJ} matches {ENH_MAX}.. run {sb} set #err {OBJ} 4",
          f"execute if score #err {OBJ} matches 0 unless score #next {OBJ} matches {s.lo}..{s.hi} run {sb} set #err {OBJ} 2",
          f"execute if score #err {OBJ} matches 0 if score #next {OBJ} > #cap {OBJ} run {sb} set #err {OBJ} 3",
          f"execute store success score #ok {OBJ} if score #err {OBJ} matches 0"]
    for t, slot in gears:
        gid = gear_id(t, slot)
        for k in range(s.lo, s.hi + 1):
            L.append(f"execute if score #ok {OBJ} matches 1 if score #next {OBJ} matches {k} "
                     f'if items entity @s {OFF} *[minecraft:custom_data~{{{NAMESPACE}:"{gid}"}}] '
                     f"run item modify entity @s {OFF} {NAMESPACE}:enhance/{gid}_{k}")
    L += [f"execute if score #ok {OBJ} matches 1 run playsound minecraft:block.anvil.use player @s",
          _tell(f"if score #ok {OBJ} matches 1", [{"text": "강화 성공! 이제 +"}, _score("#next")], "gold"),
          _tell(f"if score #err {OBJ} matches 1", [{"text": "강화할 RPG 장비를 왼손에 들고 마셔야 해요. 주문서를 돌려드렸어요."}], "red"),
          _tell(f"if score #err {OBJ} matches 4", [{"text": "이미 최대 강화(+10)예요. 주문서를 돌려드렸어요."}], "red"),
          _tell(f"if score #err {OBJ} matches 2", [{"text": f"이 주문서는 +{s.lo} ~ +{s.hi} 강화에만 쓸 수 있어요. 지금 장비는 +"},
                                                    _score("#lvl"), {"text": "예요. 주문서를 돌려드렸어요."}], "red"),
          _tell(f"if score #err {OBJ} matches 3", [{"text": "대장장이 레벨이 부족해요. 지금 강화 상한은 +"},
                                                    _score("#cap"), {"text": "예요. 주문서를 돌려드렸어요."}], "red"),
          f"execute if score #ok {OBJ} matches 0 run " + give_stack_command("minecraft:potion", scroll_components(s), 1)]
    return "\n".join(L) + "\n"


def generate(root: Path) -> None:
    d = root / "data" / NAMESPACE
    write_json(root / "data" / "minecraft" / "tags" / "function" / "load.json", {"values": [f"{NAMESPACE}:load"]})
    write_text(d / "function" / "load.mcfunction", f"scoreboard objectives add {OBJ} dummy\n")
    for s in SCROLLS.values():
        recipe = {"type": "create:mixing",
                  "ingredients": [material_ingredient(f"plate_{s.n}"), material_ingredient(f"essence_{s.n}"),
                                  {"item": "minecraft:paper"}],
                  "results": [{"id": "minecraft:potion", "count": 2, "components": scroll_components(s)}]}
        if s.heat:
            recipe["heat_requirement"] = s.heat
        write_json(d / "recipe" / "mixing" / f"scroll_{s.grade}.json", recipe)
        write_json(d / "advancement" / "enhance" / f"drink_{s.grade}.json", {
            "criteria": {"drink": {"trigger": "minecraft:consume_item", "conditions": {"item": {
                "items": "minecraft:potion",
                "predicates": {"minecraft:custom_data": '{%s:"scroll_%s"}' % (NAMESPACE, s.grade)}}}}},
            "rewards": {"function": f"{NAMESPACE}:enhance/use_{s.grade}"}})
        write_text(d / "function" / "enhance" / f"use_{s.grade}.mcfunction", use_function(s))
    for t in TIERS:
        for slot in GEAR_SLOTS:
            for k in range(1, ENH_MAX + 1):
                write_json(d / "item_modifier" / "enhance" / f"{gear_id(t, slot)}_{k}.json", enhance_modifier(t, slot, k))
