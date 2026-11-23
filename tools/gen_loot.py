"""Level-gated drops via NeoForge global loot modifiers (no vanilla table overrides)."""
from pathlib import Path

from tools.build import write_json
from tools.content import DROPS, END_MONSTERS, NAMESPACE, NETHER_MONSTERS, OVERWORLD_MONSTERS, MATERIALS
from tools.items import material_components

DEBRIS = {"condition": "minecraft:block_state_property", "block": "minecraft:ancient_debris"}
NO_SILK = {"condition": "minecraft:inverted", "term": {
    "condition": "minecraft:match_tool",
    "predicate": {"predicates": {"minecraft:enchantments": [
        {"enchantments": "minecraft:silk_touch", "levels": {"min": 1}}]}}}}


def _entry(mat, count):
    fns = [{"function": "minecraft:set_components", "components": material_components(mat)}]
    if count != 1:
        fns.append({"function": "minecraft:set_count", "count": count})
    return {"type": "minecraft:item", "name": MATERIALS[mat].base, "functions": fns}


def _pool(mat, count, conditions):
    return {"rolls": 1, "entries": [_entry(mat, count)], "conditions": conditions}


def _table(mat, count, chance, source):
    chance_c = {"condition": "minecraft:random_chance", "chance": chance}
    if source[0] == "ores" and "minecraft:blocks/ancient_debris" in source[1]:
        pools = [_pool(mat, count, [{"condition": "minecraft:inverted", "term": DEBRIS}, chance_c]),
                 _pool(mat, count, [DEBRIS])]
    else:
        pools = [_pool(mat, count, [chance_c] if chance < 1 else [])]
    return {"type": "minecraft:generic", "pools": pools}


def _has_tag(entity, tag):
    return {"condition": "minecraft:entity_properties", "entity": entity,
            "predicate": {"nbt": '{Tags:["%s"]}' % tag}}


def _conditions(gate, source):
    kind = source[0]
    if kind in ("mobs", "entity"):
        type_pred = f"#{NAMESPACE}:{source[1]}" if kind == "mobs" else source[1]
        c = [{"condition": "minecraft:killed_by_player"},
             {"condition": "minecraft:entity_properties", "entity": "this", "predicate": {"type": type_pred}}]
        if kind == "mobs" and source[2]:
            c.append({"condition": "minecraft:location_check", "predicate": {"dimension": source[2]}})
        if gate:
            c.append(_has_tag("attacking_player", gate))
        return c
    c = [{"condition": "minecraft:any_of", "terms": [
        {"condition": "neoforge:loot_table_id", "loot_table_id": t} for t in source[1]]}, NO_SILK]
    if gate:
        c.append(_has_tag("this", gate))
    return c


def generate(root: Path) -> None:
    data = root / "data"
    for name, values in (("overworld_monsters", OVERWORLD_MONSTERS), ("nether_monsters", NETHER_MONSTERS),
                         ("end_monsters", END_MONSTERS)):
        write_json(data / NAMESPACE / "tags" / "entity_type" / f"{name}.json",
                   {"replace": False, "values": [f"minecraft:{v}" for v in values]})
    entries = []
    for name, mat, count, chance, gate, source in DROPS:
        write_json(data / NAMESPACE / "loot_table" / "drops" / f"{name}.json", _table(mat, count, chance, source))
        write_json(data / NAMESPACE / "loot_modifiers" / f"{name}.json", {
            "type": "neoforge:add_table", "conditions": _conditions(gate, source),
            "table": f"{NAMESPACE}:drops/{name}"})
        entries.append(f"{NAMESPACE}:{name}")
    write_json(data / "neoforge" / "loot_modifiers" / "global_loot_modifiers.json",
               {"replace": False, "entries": entries})
