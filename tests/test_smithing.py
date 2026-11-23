from conftest import load


def test_thirty_forge_advancements(pack_root):
    advs = list((pack_root / "data/create_rpg/advancement/forge").glob("gear_*.json"))
    assert len(advs) == 30


def test_advancement_rewards_point_to_existing_functions(pack_root):
    seen = 0
    for adv in (pack_root / "data/create_rpg/advancement").rglob("*.json"):
        fn = load(adv).get("rewards", {}).get("function")
        if fn:
            seen += 1
            ns, path = fn.split(":")
            assert (pack_root / f"data/{ns}/function/{path}.mcfunction").exists()
    assert seen >= 34  # 30 forge + 4 enhancement scrolls + village/NPC/quest advancements


def test_forge_xp_scales_with_tier(pack_root):
    line = (pack_root / "data/create_rpg/function/forge/gear_legend_sword.mcfunction").read_text().strip()
    assert line == "puffish_skills experience add @s create_rpg:smithing 200"


def test_criterion_matches_gear_custom_data(pack_root):
    adv = load(pack_root / "data/create_rpg/advancement/forge/gear_artisan_helmet.json")
    pred = adv["criteria"]["forged"]["conditions"]["items"][0]
    assert pred["items"] == "minecraft:diamond_helmet"
    assert "gear_artisan_helmet" in pred["predicates"]["minecraft:custom_data"]


def test_forge_advancements_have_parent_root(pack_root):
    root = load(pack_root / "data/create_rpg/advancement/forge/root.json")
    assert "대장간" in root["display"]["title"]
    adv = load(pack_root / "data/create_rpg/advancement/forge/gear_apprentice_sword.json")
    assert adv["parent"] == "create_rpg:forge/root"
