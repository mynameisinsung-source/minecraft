import json

from tools.content_village import QUESTS

A = "data/create_rpg/advancement/quest/"
F = "data/create_rpg/function/"


def adv(pack_root, qid):
    return json.loads((pack_root / f"{A}{qid}.json").read_text(encoding="utf-8"))


def test_fifteen_quests_chained(pack_root):
    root = adv(pack_root, "root")
    assert root["criteria"]["start"]["trigger"] == "minecraft:impossible"
    prev = "root"
    for q in QUESTS:
        a = adv(pack_root, q.id)
        assert a["parent"] == f"create_rpg:quest/{prev}"
        cond = json.dumps(a["criteria"]["done"]["conditions"]["player"])
        assert f'"create_rpg:quest/{prev}": true' in cond, q.id
        trig = a["criteria"]["done"]["trigger"]
        assert trig == ("minecraft:player_killed_entity" if q.kind == "kill" else "minecraft:inventory_changed")
        if q.kind == "forge":
            assert f'"create_rpg:forge/{q.target}": true' in cond
        else:
            assert f'"{q.id}": {{"min": {q.count}}}' in cond
        prev = q.id
    assert len(QUESTS) == 15


def test_objectives_created_on_load(pack_root):
    load = (pack_root / f"{F}load.mcfunction").read_text()
    for q in QUESTS:
        if q.kind != "forge":
            assert f"scoreboard objectives add {q.id} {q.criterion}" in load
    assert "minecraft.crafted:create.cogwheel" in load


def test_reward_resets_next_objective(pack_root):
    for q, nxt in zip(QUESTS, QUESTS[1:]):
        body = (pack_root / f"{F}quest/reward/{q.id}.mcfunction").read_text(encoding="utf-8")
        assert (f"scoreboard players set @s {nxt.id} 0" in body) == (nxt.kind != "forge"), q.id


def test_quest_rewards_valid_items(pack_root):
    for q in QUESTS:
        body = (pack_root / f"{F}quest/reward/{q.id}.mcfunction").read_text(encoding="utf-8")
        assert body.count("give @s ") == len(q.rewards)
        assert adv(pack_root, q.id)["rewards"]["function"] == f"create_rpg:quest/reward/{q.id}"


def test_final_quest_title_dialogue(pack_root):
    body = (pack_root / f"{F}quest/reward/q15.mcfunction").read_text(encoding="utf-8")
    assert "용을 쓰러뜨린 자" in body and "촌장 오르빈" in body
