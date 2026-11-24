import json

from conftest import DATA, load, recipes, _rpg_ids_in, recipe_output_rpg_ids, consumed_rpg_ids, obtainable_rpg_ids, all_item_ids, heat_of
from tools.content import GEAR_SLOTS, TIERS

TIER_KEYS = [t.key for t in TIERS]
SA = "data/create_rpg/recipe/sequenced_assembly/"


def test_thirty_gear_items_each_have_one_recipe(pack_root):
    outputs = recipe_output_rpg_ids(pack_root)
    gear = {f"gear_{t}_{s}" for t in TIER_KEYS for s in GEAR_SLOTS}
    assert len(gear) == 30
    assert gear <= set(outputs) and all(outputs.count(g) == 1 for g in gear)


def test_every_consumed_item_is_obtainable(pack_root):
    assert consumed_rpg_ids(pack_root) <= obtainable_rpg_ids(pack_root)


def test_create_item_ids_exist(pack_root):
    known = set((DATA / "create_items.txt").read_text().split())
    assert {i for i in all_item_ids(pack_root) if i.startswith("create:")} <= known


def test_heat_requirements(pack_root):
    assert heat_of(pack_root, "alloy_1") is None and heat_of(pack_root, "alloy_2") is None
    assert heat_of(pack_root, "alloy_3") == "heated"
    assert heat_of(pack_root, "alloy_4") == heat_of(pack_root, "legend_core") == "superheated"


def test_sequenced_assembly_shape(pack_root):
    r = load(pack_root / (SA + "gear_arcane_sword.json"))
    assert r["loops"] == 3 and r["transitional_item"]["id"] == "create:incomplete_precision_mechanism"
    assert [s["type"] for s in r["sequence"]] == ["create:deploying", "create:filling", "create:deploying", "create:pressing"]


def test_legend_gear_has_custom_name_and_attributes(pack_root):
    res = load(pack_root / (SA + "gear_legend_sword.json"))["results"][0]
    assert res["id"] == "minecraft:netherite_sword"
    assert "전설" in res["components"]["minecraft:custom_name"]
    assert res["components"]["minecraft:attribute_modifiers"]["modifiers"]


def _mods(pack_root, rel):
    r = load(pack_root / rel)
    return r["results"][0]["components"]["minecraft:attribute_modifiers"]["modifiers"]


def test_sword_damage_keeps_vanilla_base_plus_bonus(pack_root):
    # netherite sword vanilla +7, legend bonus +8
    dmg = sum(m["amount"] for m in _mods(pack_root, SA + "gear_legend_sword.json")
              if m["type"] == "minecraft:generic.attack_damage")
    assert dmg == 15
    speed = [m for m in _mods(pack_root, SA + "gear_legend_sword.json") if m["type"] == "minecraft:generic.attack_speed"]
    assert speed and speed[0]["amount"] == -2.4


def test_armor_set_bonus_totals(pack_root):
    expected = {"apprentice": 2, "journeyman": 4, "artisan": 6, "arcane": 9, "legend": 12}
    base = {"iron": 15, "diamond": 20, "netherite": 20}
    for t in TIERS:
        total = 0
        for slot in ["helmet", "chestplate", "leggings", "boots"]:
            path = next(pack_root.glob(f"data/create_rpg/recipe/*/gear_{t.key}_{slot}.json"))
            total += sum(m["amount"] for m in _mods(pack_root, path.relative_to(pack_root))
                         if m["type"] == "minecraft:generic.armor")
        assert total == base[t.base_material] + expected[t.key], t.key


def test_modifier_ids_unique_per_item(pack_root):
    for p in pack_root.glob("data/create_rpg/recipe/*/gear_*.json"):
        ids = [(m["type"], m["id"]) for m in _mods(pack_root, p.relative_to(pack_root))]
        assert len(ids) == len(set(ids)), p.name


def test_material_bases_cannot_shortcut_progression():
    from tools.content import MATERIALS
    progression = {"minecraft:netherite_scrap", "minecraft:netherite_ingot", "minecraft:diamond",
                   "minecraft:iron_ingot", "minecraft:gold_ingot", "minecraft:nether_star", "minecraft:ancient_debris"}
    assert not {m.base for m in MATERIALS.values()} & progression


def test_legend_tier_upgrades_arcane_gear_in_one_loop(pack_root):
    r = load(pack_root / (SA + "gear_legend_chestplate.json"))
    assert r["loops"] == 1
    assert r["ingredient"]["components"]["minecraft:custom_data"]["create_rpg"] == "gear_arcane_chestplate"


def test_alloy_4_uses_netherite_scrap(pack_root):
    r = load(pack_root / "data/create_rpg/recipe/mixing/alloy_4.json")
    assert {"item": "minecraft:netherite_scrap"} in r["ingredients"]


def test_unheated_brass_so_deployers_need_no_nether(pack_root):
    # Create's brass is heated-only (blaze burner = Nether); the Deployer needs brass from tier 1
    r = load(pack_root / "data/create_rpg/recipe/mixing/brass_ingot_unheated.json")
    assert "heat_requirement" not in r
    items = [i.get("tag") or i.get("item") for i in r["ingredients"]]
    assert "c:ingots/copper" in items and "c:ingots/zinc" in items and len(items) == 3
    assert r["results"] == [{"id": "create:brass_ingot"}]


def test_early_and_mid_recipes_need_no_heat(pack_root):
    early = ["alloy_1", "alloy_2", "plate_1", "plate_2", "powder_1", "powder_2"]
    for _, r in recipes(pack_root):
        ids = [i for res in r.get("results", []) for i in _rpg_ids_in(res)]
        if any(i in early or i.startswith(("gear_apprentice", "gear_journeyman", "gear_artisan"))
               or i in ("scroll_low", "scroll_mid") for i in ids):
            assert "heat_requirement" not in r, ids
