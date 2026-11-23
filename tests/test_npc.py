import json
import re

from tools.content_village import NPCS, QUESTS, STARTER_KIT

F = "data/create_rpg/function/"


def text(pack_root, name):
    return (pack_root / f"{F}{name}.mcfunction").read_text(encoding="utf-8")


def test_talk_advancements_revoke_and_exist(pack_root):
    for n in NPCS:
        adv = json.loads((pack_root / f"data/create_rpg/advancement/npc/talk_{n.id}.json").read_text())
        c = adv["criteria"]["talk"]
        assert c["trigger"] == "minecraft:player_interacted_with_entity"
        assert f"rpg_npc_{n.id}" in json.dumps(c["conditions"])
        assert adv["rewards"]["function"] == f"create_rpg:npc/{n.id}/talk"
        assert text(pack_root, f"npc/{n.id}/talk").splitlines()[0] == f"advancement revoke @s only create_rpg:npc/talk_{n.id}"


def test_starter_kit_once(pack_root):
    lines = text(pack_root, "npc/chief/talk").splitlines()
    menu = next(i for i, l in enumerate(lines) if "if entity @s[tag=rpg_started] run function create_rpg:npc/chief/menu" in l)
    intro = next(i for i, l in enumerate(lines) if "unless entity @s[tag=rpg_started] run function create_rpg:npc/chief/intro" in l)
    assert menu < intro
    body = text(pack_root, "npc/chief/intro")
    assert "tag @s add rpg_started" in body
    assert body.count("give @s ") == len(STARTER_KIT)
    assert "advancement grant @s only create_rpg:quest/root" in body
    assert "scoreboard players set @s q01 0" in body


def test_help_topics_clickable(pack_root):
    menu = text(pack_root, "npc/chief/menu")
    targets = re.findall(r'"value": "/function (create_rpg:[\w/]+)"', menu)
    assert len(targets) == 8
    for t in targets:
        assert (pack_root / f"{F}{t.split(':')[1]}.mcfunction").exists(), t


def test_whats_next_covers_all_quests(pack_root):
    nxt = text(pack_root, "npc/chief/help/next")
    for q in QUESTS:
        assert f"advancements={{create_rpg:quest/{q.id}=false}}" in nxt
        hint = text(pack_root, f"npc/chief/hint/{q.id}")
        assert "scoreboard players set #done rpg_tmp 1" in hint


def test_guild_shows_current_quest_progress(pack_root):
    for q in QUESTS:
        cur = text(pack_root, f"npc/guild/current/{q.id}")
        if q.kind != "forge":
            assert f'"objective": "{q.id}"' in cur and str(q.count) in cur
