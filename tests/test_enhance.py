import json

from conftest import load
from tools.content import GEAR_SLOTS, TIERS

GRADES = {"low": (1, 3), "mid": (4, 5), "high": (6, 7), "top": (8, 10)}
D = "data/create_rpg/"


def fn(pack_root, grade):
    return (pack_root / f"{D}function/enhance/use_{grade}.mcfunction").read_text(encoding="utf-8")


def mod(pack_root, name):
    return load(pack_root / f"{D}item_modifier/enhance/{name}.json")


def test_four_scroll_recipes_and_heat(pack_root):
    heat = {"low": None, "mid": None, "high": "heated", "top": "superheated"}
    for g, h in heat.items():
        r = load(pack_root / f"{D}recipe/mixing/scroll_{g}.json")
        assert r.get("heat_requirement") == h
        res = r["results"][0]
        assert res["id"] == "minecraft:potion" and res["count"] == 2
        assert res["components"]["minecraft:custom_data"]["create_rpg"] == f"scroll_{g}"
        assert {"item": "minecraft:paper"} in r["ingredients"]


def test_scroll_functions_revoke_their_advancement(pack_root):
    for g in GRADES:
        adv = load(pack_root / f"{D}advancement/enhance/drink_{g}.json")
        assert adv["criteria"]["drink"]["trigger"] == "minecraft:consume_item"
        assert adv["rewards"]["function"] == f"create_rpg:enhance/use_{g}"
        assert fn(pack_root, g).splitlines()[0] == f"advancement revoke @s only create_rpg:enhance/drink_{g}"


def test_failure_paths_refund_scroll(pack_root):
    for g in GRADES:
        text = fn(pack_root, g)
        refund = [l for l in text.splitlines() if "give @s minecraft:potion" in l]
        assert refund and all("#ok rpg_tmp matches 0" in l for l in refund)
        assert f'scroll_{g}' in refund[0]
        assert "weapon.offhand" in text
        assert "rpg_enh" not in text


def test_max_level_refunds(pack_root):
    text = fn(pack_root, "top")
    assert "item modify entity @s weapon.offhand create_rpg:enhance/gear_legend_sword_10" in text
    assert "_11" not in text
    assert not (pack_root / f"{D}item_modifier/enhance/gear_legend_sword_11.json").exists()


def test_cap_checks_use_smith_tags(pack_root):
    text = fn(pack_root, "mid")
    for tag, cap in (("rpg_smith_1", 5), ("rpg_smith_2", 7), ("rpg_smith_3", 10)):
        assert f"if entity @s[tag={tag}] run scoreboard players set #cap rpg_tmp {cap}" in text
    assert "scoreboard players set #cap rpg_tmp 3" in text


def test_modifier_files_for_every_gear_and_level(pack_root):
    files = list((pack_root / f"{D}item_modifier/enhance").glob("*.json"))
    assert len(files) == 300
    for f in files:
        has_bonus = "create_rpg:enhance_bonus" in f.read_text(encoding="utf-8")
        assert has_bonus == f.stem.endswith("_10"), f.name


def _attr(m):
    sa = next(x for x in m if x["function"] == "minecraft:set_attributes")
    assert sa["replace"] is False
    return {x["attribute"]: x for x in sa["modifiers"]}


def test_enhance_amounts(pack_root):
    assert _attr(mod(pack_root, "gear_legend_sword_7"))["minecraft:generic.attack_damage"]["amount"] == 7
    helm = _attr(mod(pack_root, "gear_artisan_helmet_4"))["minecraft:generic.armor"]
    assert helm["amount"] == 2.0 and helm["slot"] == "head"
    pick = _attr(mod(pack_root, "gear_apprentice_pickaxe_10"))
    assert pick["minecraft:player.block_break_speed"]["amount"] == 0.5
    assert pick["minecraft:generic.max_health"]["amount"] == 2


def test_name_and_level_written(pack_root):
    m = mod(pack_root, "gear_arcane_boots_6")
    name = next(x for x in m if x["function"] == "minecraft:set_name")
    assert "비전 명장 부츠 +6" in json.dumps(name, ensure_ascii=False)
    comps = next(x for x in m if x["function"] == "minecraft:set_components")
    assert comps["components"] == {"minecraft:custom_model_data": 6}
    assert not any(x["function"] == "minecraft:set_custom_data" for x in m)


def test_gear_custom_data_unchanged_so_enhanced_gear_still_upgrades(pack_root):
    # neoforge:components compares custom_data exactly; enhancement must not touch it
    for p in pack_root.glob(f"{D}recipe/*/gear_*.json"):
        assert list(load(p)["results"][0]["components"]["minecraft:custom_data"]) == ["create_rpg"], p.name


def test_function_detects_all_gear_and_levels(pack_root):
    text = fn(pack_root, "low")
    assert text.count('scoreboard players set #gear rpg_tmp 1') == 30
    assert 'weapon.offhand *[minecraft:custom_model_data=10]' in text


def test_load_tag_only(pack_root):
    assert load(pack_root / "data/minecraft/tags/function/load.json")["values"] == ["create_rpg:load"]
    assert "scoreboard objectives add rpg_tmp dummy" in (pack_root / f"{D}function/load.mcfunction").read_text()
    assert not (pack_root / "data/minecraft/tags/function/tick.json").exists()
