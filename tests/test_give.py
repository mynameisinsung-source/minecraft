from tools.content import MATERIALS, SCROLLS

D = "data/create_rpg/function/give/"


def test_give_functions_for_scrolls_and_materials(pack_root):
    for g in SCROLLS:
        text = (pack_root / f"{D}scroll_{g}.mcfunction").read_text(encoding="utf-8")
        assert text.startswith("give @s minecraft:potion[") and f'scroll_{g}' in text and text.strip().endswith(" 16")
    for m in MATERIALS:
        text = (pack_root / f"{D}{m}.mcfunction").read_text(encoding="utf-8")
        assert f'create_rpg:"{m}"' in text and text.strip().endswith(" 16")


def test_give_function_for_every_gear(pack_root):
    assert len(list((pack_root / D).glob("gear_*.mcfunction"))) == 30
    text = (pack_root / f"{D}gear_legend_sword.mcfunction").read_text(encoding="utf-8")
    assert text.startswith("give @s minecraft:netherite_sword[") and "minecraft:attribute_modifiers=" in text
