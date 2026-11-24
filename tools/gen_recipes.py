"""Create recipes: material chain + 30 gear items."""
from pathlib import Path

from tools.build import write_json
from tools.content import (ALLOY_HEAT, ARMOR_SLOT, BASE_INGOT, GEAR_SLOTS, NAMESPACE, SLOT_NAME, TIERS,
                           TRANSITIONAL, VANILLA, Tier)
from tools.items import material_ingredient, material_result, rpg_components, rpg_ingredient

ARMOR_IDX = {"helmet": 0, "chestplate": 1, "leggings": 2, "boots": 3}


def gear_id(t: Tier, slot: str) -> str:
    return f"gear_{t.key}_{slot}"


def vanilla_item(material: str, slot: str) -> str:
    return f"minecraft:{material}_{slot}"


def _mod(attr, mid, amount, op, slot):
    return {"type": f"minecraft:{attr}", "id": mid, "amount": amount, "operation": op, "slot": slot}


def gear_modifiers(t: Tier, slot: str) -> list:
    v = VANILLA[t.base_material]
    b = f"{NAMESPACE}:bonus_{slot}"
    if slot in ("sword", "pickaxe"):
        dmg, speed = v[slot]
        mods = [_mod("generic.attack_damage", "minecraft:base_attack_damage", dmg, "add_value", "mainhand"),
                _mod("generic.attack_speed", "minecraft:base_attack_speed", speed, "add_value", "mainhand")]
        if slot == "sword":
            mods.append(_mod("generic.attack_damage", f"{b}_damage", t.sword_bonus, "add_value", "mainhand"))
        else:
            mods.append(_mod("player.block_break_speed", f"{b}_speed", t.mining_bonus, "add_multiplied_base", "mainhand"))
        return mods
    eq, i = ARMOR_SLOT[slot], ARMOR_IDX[slot]
    vid = f"minecraft:armor.{slot}"
    mods = [_mod("generic.armor", vid, v["armor"][i], "add_value", eq)]
    if v["toughness"]:
        mods.append(_mod("generic.armor_toughness", vid, v["toughness"], "add_value", eq))
    if v["kb"]:
        mods.append(_mod("generic.knockback_resistance", vid, v["kb"], "add_value", eq))
    if t.armor_bonus[i]:
        mods.append(_mod("generic.armor", f"{b}_armor", t.armor_bonus[i], "add_value", eq))
    if slot == "chestplate" and t.health_bonus:
        mods.append(_mod("generic.max_health", f"{b}_health", t.health_bonus, "add_value", eq))
    return mods


def gear_result(t: Tier, slot: str) -> dict:
    extra = {"minecraft:attribute_modifiers": {"modifiers": gear_modifiers(t, slot), "show_in_tooltip": True},
             "minecraft:rarity": t.rarity}
    lore = [f"{t.n}단계 대장간 장비", "Create 공정으로 단련되었다"]
    return {"id": vanilla_item(t.base_material, slot),
            "components": rpg_components(gear_id(t, slot), f"{t.name} {SLOT_NAME[slot]}", lore,
                                         glint=t.n >= 4, extra=extra, color=t.color)}


def _tr():
    return {"item": TRANSITIONAL}


def deploy(ing):
    return {"type": "create:deploying", "ingredients": [_tr(), ing], "results": [{"id": TRANSITIONAL}]}


def press():
    return {"type": "create:pressing", "ingredients": [_tr()], "results": [{"id": TRANSITIONAL}]}


def fill(mb):
    return {"type": "create:filling", "ingredients": [_tr(), {"type": "neoforge:single", "amount": mb, "fluid": "minecraft:lava"}],
            "results": [{"id": TRANSITIONAL}]}


def _sequence(t: Tier):
    m = material_ingredient
    return {
        2: (1, [deploy(m("plate_1")), deploy(m("essence_1")), press()]),
        3: (2, [deploy(m("plate_2")), deploy(m("essence_2")), press()]),
        4: (3, [deploy(m("plate_3")), fill(250), deploy(m("fragment_3")), press()]),
        5: (1, [deploy(m("legend_core")), deploy(m("plate_4")), fill(500), press()]),
    }[t.n]


def _input(t: Tier, slot: str) -> dict:
    if t.n in (2, 4, 5):  # upgrades of the previous tier's RPG item
        prev = TIERS[t.n - 2]
        return rpg_ingredient(gear_id(prev, slot), vanilla_item(prev.base_material, slot))
    return {"item": vanilla_item(t.base_material, slot)}


def generate(root: Path) -> None:
    r = root / "data" / NAMESPACE / "recipe"
    for n in range(1, 5):
        write_json(r / "crushing" / f"powder_{n}.json", {
            "type": "create:crushing", "ingredients": [material_ingredient(f"fragment_{n}")], "processing_time": 200,
            "results": [material_result(f"powder_{n}"), material_result(f"powder_{n}", chance=0.5)]})
        mix = {"type": "create:mixing",
               "ingredients": [material_ingredient(f"powder_{n}")] * 2 + [material_ingredient(f"essence_{n}"), {"item": BASE_INGOT[n]}],
               "results": [material_result(f"alloy_{n}")]}
        if ALLOY_HEAT[n]:
            mix["heat_requirement"] = ALLOY_HEAT[n]
        write_json(r / "mixing" / f"alloy_{n}.json", mix)
        write_json(r / "pressing" / f"plate_{n}.json", {
            "type": "create:pressing", "ingredients": [material_ingredient(f"alloy_{n}")],
            "results": [material_result(f"plate_{n}")]})
    # Create's own brass is heated-only (blaze burner needs a Nether blaze), but Deployers need brass
    # from tier 1. Slower unheated route: 1 brass instead of 2, plus redstone so it never shadows Create's.
    write_json(r / "mixing" / "brass_ingot_unheated.json", {
        "type": "create:mixing",
        "ingredients": [{"tag": "c:ingots/copper"}, {"tag": "c:ingots/zinc"}, {"item": "minecraft:redstone"}],
        "results": [{"id": "create:brass_ingot"}]})
    write_json(r / "mixing" / "legend_core.json", {
        "type": "create:mixing", "heat_requirement": "superheated",
        "ingredients": [{"item": "minecraft:nether_star"}] + [material_ingredient("essence_4")] * 4 + [material_ingredient("plate_4")] * 2,
        "results": [material_result("legend_core", count=6)]})
    for t in TIERS:
        for slot in GEAR_SLOTS:
            if t.n == 1:
                write_json(r / "deploying" / f"{gear_id(t, slot)}.json", {
                    "type": "create:deploying", "ingredients": [_input(t, slot), {"item": "create:copper_sheet"}],
                    "results": [gear_result(t, slot)]})
                continue
            loops, seq = _sequence(t)
            write_json(r / "sequenced_assembly" / f"{gear_id(t, slot)}.json", {
                "type": "create:sequenced_assembly", "ingredient": _input(t, slot), "loops": loops,
                "results": [gear_result(t, slot)], "sequence": seq, "transitional_item": {"id": TRANSITIONAL}})
