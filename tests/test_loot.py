import json

from conftest import load, modifiers, table_path, tags_required_by_loot, all_granted_tags, _rpg_ids_in


def test_global_modifier_list_matches_files(pack_root):
    glm = load(pack_root / "data/neoforge/loot_modifiers/global_loot_modifiers.json")
    assert glm["replace"] is False
    files = {f"create_rpg:{p.stem}" for p in (pack_root / "data/create_rpg/loot_modifiers").glob("*.json")}
    assert set(glm["entries"]) == files and len(files) == 12


def test_modifier_tables_exist(pack_root):
    for m in modifiers(pack_root):
        assert m["type"] == "neoforge:add_table"
        assert table_path(pack_root, m["table"]).exists()


def test_loot_gate_tags_are_granted_by_skills(pack_root):
    assert tags_required_by_loot(pack_root) <= all_granted_tags(pack_root)
    assert tags_required_by_loot(pack_root) == {"rpg_hunt_1", "rpg_hunt_2", "rpg_hunt_3",
                                                "rpg_mine_1", "rpg_mine_2", "rpg_mine_3",
                                                "rpg_luck_1", "rpg_luck_2", "rpg_luck_3"}


def test_no_vanilla_loot_table_overrides(pack_root):
    assert not (pack_root / "data/minecraft/loot_table").exists()


def test_every_material_source_is_dropped(pack_root):
    dropped = set()
    for m in modifiers(pack_root):
        if "luck" not in m["table"]:
            dropped.update(_rpg_ids_in(load(table_path(pack_root, m["table"]))))
    assert dropped == {f"essence_{n}" for n in range(1, 5)} | {f"fragment_{n}" for n in range(1, 5)}


def test_mob_drops_require_player_kill(pack_root):
    for p in (pack_root / "data/create_rpg/loot_modifiers").glob("essence_*.json"):
        conds = json.dumps(load(p)["conditions"])
        assert "minecraft:killed_by_player" in conds, p.name


def test_ore_drops_skip_silk_touch(pack_root):
    for p in (pack_root / "data/create_rpg/loot_modifiers").glob("fragment_*.json"):
        assert "silk_touch" in json.dumps(load(p)["conditions"]), p.name


def test_entity_type_tags(pack_root):
    d = pack_root / "data/create_rpg/tags/entity_type"
    assert "minecraft:zombie" in load(d / "overworld_monsters.json")["values"]
    assert "minecraft:blaze" in load(d / "nether_monsters.json")["values"]
    assert "minecraft:enderman" in load(d / "end_monsters.json")["values"]


def _luck(pack_root, n):
    return load(pack_root / f"data/create_rpg/loot_modifiers/luck_{n}.json")


def test_luck_levels_are_exclusive(pack_root):
    for n in (1, 2, 3):
        conds = json.dumps(_luck(pack_root, n)["conditions"])
        assert f'rpg_luck_{n}' in conds
        assert (f'rpg_luck_{n + 1}' in conds) == (n < 3)
        assert "silk_touch" in conds


def test_luck_tables_give_vanilla_drop(pack_root):
    t = load(pack_root / "data/create_rpg/loot_table/drops/luck_3.json")
    pools = [p for p in t["pools"] if p["entries"][0]["name"] == "minecraft:diamond"]
    assert len(pools) == 2  # diamond_ore + deepslate_diamond_ore
    assert all({"condition": "minecraft:random_chance", "chance": 0.15} in p["conditions"] for p in pools)
