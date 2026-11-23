import re

from tools import nbt
from tools.content_village import NPCS
from tools.structures import PLACEMENTS, footprint

F = "data/create_rpg/function/"


def text(pack_root, name):
    return (pack_root / f"{F}{name}.mcfunction").read_text(encoding="utf-8")


def test_structures_in_pack_and_placed_with_rotation(pack_root):
    con = text(pack_root, "village/construct")
    for name, (dx, dz, rot) in PLACEMENTS.items():
        assert (pack_root / f"data/create_rpg/structure/{name}.nbt").exists()
        assert f"place template create_rpg:{name} ~{dx} ~-1 ~{dz} {rot}" in con


def test_build_guarded_once(pack_root):
    for fn in ("village/build", "village/build_here"):
        first = [l for l in text(pack_root, fn).splitlines() if "built" in l]
        assert first and "execute if data storage create_rpg:village built" in first[0]
    assert "data modify storage create_rpg:village built set value 1b" in text(pack_root, "village/construct")


def test_auto_build_only_for_new_players(pack_root):
    lines = text(pack_root, "village/first_join").splitlines()
    gate = next(i for i, l in enumerate(lines) if "minecraft:story/root=true" in l and "return" in l)
    call = next(i for i, l in enumerate(lines) if l.startswith("function create_rpg:village/build_here"))
    assert gate < call


def test_first_join_advancement(pack_root):
    import json
    adv = json.loads((pack_root / "data/create_rpg/advancement/village/first_join.json").read_text())
    assert adv["criteria"]["join"]["trigger"] == "minecraft:tick"
    assert adv["rewards"]["function"] == "create_rpg:village/first_join"


def test_fill_volumes_within_limit(pack_root):
    for l in text(pack_root, "village/construct").splitlines():
        if l.startswith("fill "):
            n = [int(v or 0) for v in re.findall(r"~(-?\d*)", l)]
            assert len(n) == 6
            vol = (abs(n[3] - n[0]) + 1) * (abs(n[4] - n[1]) + 1) * (abs(n[5] - n[2]) + 1)
            assert vol <= 32768, l


def test_npcs_stand_in_air_inside_their_building(pack_root):
    for npc in NPCS:
        wx, wz = npc.world_pos
        if npc.building is None:
            assert all(not (x1 <= wx <= x2 and z1 <= wz <= z2) for x1, x2, z1, z2 in map(footprint, PLACEMENTS))
            continue
        x1, x2, z1, z2 = footprint(npc.building)
        assert x1 < wx < x2 and z1 < wz < z2, npc.id
        s = nbt.read(pack_root / f"data/create_rpg/structure/{npc.building}.nbt")
        solid = {tuple(b["pos"]) for b in s["blocks"] if s["palette"][b["state"]]["Name"] != "minecraft:air"}
        lx, lz = npc.local_pos
        assert (lx, 1, lz) not in solid and (lx, 2, lz) not in solid, npc.id


def test_four_npcs_summoned_with_tags_and_noai(pack_root):
    con = text(pack_root, "village/construct")
    summons = [l for l in con.splitlines() if l.startswith("summon minecraft:villager")]
    assert len(summons) == 4
    for npc in NPCS:
        line = next(l for l in summons if f'"rpg_npc_{npc.id}"' in l)
        for k in ("NoAI:1b", "Invulnerable:1b", "PersistenceRequired:1b", "Silent:1b", "CustomNameVisible:1b", "level:5"):
            assert k in line, (npc.id, k)


def test_trades_buy_rpg_items_by_custom_data(pack_root):
    con = text(pack_root, "village/construct")
    guild = next(l for l in con.splitlines() if '"rpg_npc_guild"' in l)
    assert 'buy:{id:"minecraft:prismarine_crystals",count:8,components:{"minecraft:custom_data":{create_rpg:"essence_1"}}}' in guild
    assert "maxUses:999999" in guild
    smith = next(l for l in con.splitlines() if '"rpg_npc_smith"' in l)
    assert 'create_rpg:"scroll_low"' in smith


def test_village_structure_placed_and_spawn_set(pack_root):
    con = text(pack_root, "village/construct")
    assert "place structure minecraft:village_plains ~ ~ ~56" in con
    assert "setworldspawn ~ ~ ~" in con


def test_home_macro_and_return_scroll(pack_root):
    assert "$execute in minecraft:overworld run tp @s $(x) $(y) $(z)" in text(pack_root, "village/home_tp")
    assert "function create_rpg:village/home_tp with storage create_rpg:village" in text(pack_root, "home")
    import json
    adv = json.loads((pack_root / "data/create_rpg/advancement/village/drink_home.json").read_text())
    assert adv["criteria"]["drink"]["trigger"] == "minecraft:consume_item"
    use = text(pack_root, "village/use_home").splitlines()
    assert use[0] == "advancement revoke @s only create_rpg:village/drink_home"
    assert "function create_rpg:home" in use
