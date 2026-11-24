from conftest import load
from tools.content import MATERIALS
from tools.items import rpg_ingredient


def test_pack_mcmeta(pack_root):
    meta = load(pack_root / "pack.mcmeta")
    assert meta["pack"]["pack_format"] == 48
    assert "Create RPG" in meta["pack"]["description"]


def test_no_tick_function(pack_root):
    assert not (pack_root / "data/minecraft/tags/function/tick.json").exists()


def test_material_ingredient_is_strict_on_custom_data():
    ing = rpg_ingredient("essence_1", "minecraft:prismarine_crystals")
    assert ing == {"type": "neoforge:components", "items": "minecraft:prismarine_crystals",
                   "components": {"minecraft:custom_data": {"create_rpg": "essence_1"}}, "strict": False}


def test_all_material_names_are_korean_and_unique():
    names = [m.name for m in MATERIALS.values()]
    assert len(names) == len(set(names)) == 21
    assert all(any("가" <= ch <= "힣" for ch in n) for n in names)
