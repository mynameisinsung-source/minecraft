import pytest
from conftest import load, cat_dir, reachable, granted_tags

CATS = ["hunting", "mining", "smithing"]


def test_config_lists_three_categories(pack_root):
    cfg = load(pack_root / "data/create_rpg/puffish_skills/config.json")
    assert cfg == {"version": 3, "categories": CATS}


@pytest.mark.parametrize("cat", CATS)
def test_every_skill_uses_existing_definition(pack_root, cat):
    d = cat_dir(pack_root, cat)
    defs, skills = load(d / "definitions.json"), load(d / "skills.json")
    assert len(skills) == 13
    assert all(s["definition"] in defs for s in skills.values())


@pytest.mark.parametrize("cat", CATS)
def test_every_skill_reachable_from_root(pack_root, cat):
    assert reachable(pack_root, cat) == set(load(cat_dir(pack_root, cat) / "skills.json"))


@pytest.mark.parametrize("cat,prefix", [("hunting", "rpg_hunt"), ("mining", "rpg_mine"), ("smithing", "rpg_smith")])
def test_gate_tags(pack_root, cat, prefix):
    assert granted_tags(pack_root, cat) == {f"{prefix}_{i}" for i in (1, 2, 3)}


@pytest.mark.parametrize("cat", CATS)
def test_experience_curve(pack_root, cat):
    exp = load(cat_dir(pack_root, cat) / "experience.json")
    assert exp["level_limit"] == 20
    assert exp["experience_per_level"]["data"]["values"][0] == 20
    assert exp["sources"]


@pytest.mark.parametrize("cat", CATS)
def test_gates_require_increasing_spent_points(pack_root, cat):
    defs = load(cat_dir(pack_root, cat) / "definitions.json")
    gates = sorted(d["required_spent_points"] for d in defs.values() if "required_spent_points" in d)
    assert gates == [3, 7, 11]


def test_smithing_crafts_tag_lists_create_parts(pack_root):
    tag = load(pack_root / "data/create_rpg/tags/item/smithing_crafts.json")
    assert "create:cogwheel" in tag["values"] and len(tag["values"]) == 20
