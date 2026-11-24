import json
import re

from tools import nbt
from tools.content_village import NPCS
from tools.structures import BUILDINGS, LAYOUT, PLACED, PLAZA_HALF, footprint, origin_for, rotation_for
from tools.gen_village import path_tiles

F = "data/create_rpg/function/"


def text(pack_root, name):
    return (pack_root / f"{F}{name}.mcfunction").read_text(encoding="utf-8")


def all_village_lines(pack_root):
    out = []
    for p in sorted((pack_root / f"{F}village").rglob("*.mcfunction")):
        out += p.read_text(encoding="utf-8").splitlines()
    return out


def in_fp(x, z, fp):
    return fp[0] <= x <= fp[1] and fp[2] <= z <= fp[3]


def test_every_layout_building_placed_on_terrain(pack_root):
    con = text(pack_root, "village/construct")
    for p in LAYOUT:
        assert (pack_root / f"data/create_rpg/structure/{p.building}.nbt").exists()
        assert f"execute positioned ~{p.cx} ~ ~{p.cz} run function create_rpg:village/place/{p.id}" in con
        ox, oz = origin_for(p)
        assert (f"place template create_rpg:{p.building} ~{ox - p.cx} ~-1 ~{oz - p.cz} {rotation_for(p.facing)}"
                in text(pack_root, f"village/build/{p.id}"))


def test_place_functions_clear_trees_first(pack_root):
    for p in LAYOUT:
        lines = text(pack_root, f"village/place/{p.id}").splitlines()
        logs = next(i for i, l in enumerate(lines) if "replace #minecraft:logs" in l)
        leaves = next(i for i, l in enumerate(lines) if "replace #minecraft:leaves" in l)
        go = next(i for i, l in enumerate(lines)
                  if f"positioned over motion_blocking_no_leaves run function create_rpg:village/build/{p.id}" in l)
        assert logs < go and leaves < go


def test_no_vanilla_village(pack_root):
    assert not any("place structure" in l for l in all_village_lines(pack_root))


def test_build_guarded_once(pack_root):
    for fn in ("village/build", "village/build_here"):
        first = [l for l in text(pack_root, fn).splitlines() if "built" in l]
        assert first and "execute if data storage create_rpg:village built" in first[0]
    con = text(pack_root, "village/construct")
    assert "scoreboard players set #tpl rpg_tmp 0" in con.splitlines()[0:3]
    assert "execute if score #tpl rpg_tmp matches 1 run data modify storage create_rpg:village built set value 1b" in con
    assert "execute store success score #tpl rpg_tmp run place template create_rpg:forge" in text(pack_root, "village/build/forge")


def test_auto_build_only_for_new_players(pack_root):
    lines = text(pack_root, "village/first_join").splitlines()
    gate = next(i for i, l in enumerate(lines) if "minecraft:story/root=true" in l and "return" in l)
    call = next(i for i, l in enumerate(lines) if l.startswith("function create_rpg:village/build_here"))
    assert gate < call


def test_first_join_advancement(pack_root):
    adv = json.loads((pack_root / "data/create_rpg/advancement/village/first_join.json").read_text())
    assert adv["criteria"]["join"]["trigger"] == "minecraft:tick"
    assert adv["rewards"]["function"] == "create_rpg:village/first_join"


def test_fill_volumes_within_limit(pack_root):
    for l in all_village_lines(pack_root):
        if l.startswith("fill "):
            n = [int(v or 0) for v in re.findall(r"~(-?\d*)", l)]
            assert len(n) == 6, l
            vol = (abs(n[3] - n[0]) + 1) * (abs(n[4] - n[1]) + 1) * (abs(n[5] - n[2]) + 1)
            assert vol <= 32768, l


def test_paths_avoid_footprints(pack_root):
    fps = [footprint(p) for p in LAYOUT]
    con = text(pack_root, "village/construct")
    union = set()
    for p in LAYOUT:
        tiles = path_tiles(p)
        if BUILDINGS[p.building].door:
            assert tiles, p.id
        for x, z in tiles:
            assert not any(in_fp(x, z, fp) for fp in fps), (p.id, x, z)
            assert not (abs(x) <= PLAZA_HALF and abs(z) <= PLAZA_HALF), (p.id, x, z)
        union.update(tiles)
    assert con.count("run setblock ~ ~-1 ~ minecraft:dirt_path") == len(union) > 0


def test_npcs_stand_in_air_inside_their_building(pack_root):
    for npc in NPCS:
        p = PLACED[npc.building]
        wx, wz = npc.world_pos
        x1, x2, z1, z2 = footprint(p)
        assert x1 < wx < x2 and z1 < wz < z2, npc.id
        s = nbt.read(pack_root / f"data/create_rpg/structure/{p.building}.nbt")
        solid = {tuple(b["pos"]) for b in s["blocks"] if s["palette"][b["state"]]["Name"] != "minecraft:air"}
        lx, lz = npc.local_pos
        assert (lx, 1, lz) not in solid and (lx, 2, lz) not in solid, npc.id


def _summons(pack_root):
    return [l for l in all_village_lines(pack_root) if l.startswith("summon minecraft:villager")]


def test_four_npcs_summoned_with_tags_and_noai(pack_root):
    summons = _summons(pack_root)
    assert len(summons) == 4
    for npc in NPCS:
        line = next(l for l in summons if f'"rpg_npc_{npc.id}"' in l)
        for k in ("NoAI:1b", "Invulnerable:1b", "PersistenceRequired:1b", "Silent:1b", "CustomNameVisible:1b", "level:5"):
            assert k in line, (npc.id, k)
        assert f'summon minecraft:marker' in text(pack_root, f"village/build/{npc.building}")


def test_npc_summon_offsets_are_whole_blocks(pack_root):
    for l in _summons(pack_root):
        x, y, z = l.split()[2:5]
        assert "." not in x and "." not in z, l


def test_trades_buy_rpg_items_by_custom_data(pack_root):
    guild = next(l for l in _summons(pack_root) if '"rpg_npc_guild"' in l)
    assert 'buy:{id:"minecraft:prismarine_crystals",count:8,components:{"minecraft:custom_data":{create_rpg:"essence_1"}}}' in guild
    assert "maxUses:999999" in guild
    smith = next(l for l in _summons(pack_root) if '"rpg_npc_smith"' in l)
    assert 'create_rpg:"scroll_low"' in smith


def test_respawn_uses_markers(pack_root):
    body = text(pack_root, "village/respawn_npcs_here")
    assert "kill @e[type=minecraft:villager,tag=rpg_npc]" in body
    for npc in NPCS:
        assert f"execute at @e[type=minecraft:marker,tag=rpg_spot_{npc.id},limit=1] run summon minecraft:villager" in body
        assert f"execute at @e[type=minecraft:marker,tag=rpg_spot_{npc.id},limit=1] run kill @e[type=minecraft:witch,distance=..4]" in body
    assert "function create_rpg:village/respawn_npcs_here" in text(pack_root, "village/respawn_npcs")


def test_spawn_and_messages(pack_root):
    con = text(pack_root, "village/construct")
    assert "gamerule spawnRadius 0" in con and "setworldspawn ~ ~ ~" in con
    assert "70" in text(pack_root, "village/build_here")


def test_home_macro_and_return_scroll(pack_root):
    assert "$execute in minecraft:overworld run tp @s $(x) $(y) $(z)" in text(pack_root, "village/home_tp")
    assert "function create_rpg:village/home_tp with storage create_rpg:village" in text(pack_root, "home")
    adv = json.loads((pack_root / "data/create_rpg/advancement/village/drink_home.json").read_text())
    assert adv["criteria"]["drink"]["trigger"] == "minecraft:consume_item"
    use = text(pack_root, "village/use_home").splitlines()
    assert use[0] == "advancement revoke @s only create_rpg:village/drink_home"
    assert "function create_rpg:home" in use


def test_fountain_water_visible(pack_root):
    con = text(pack_root, "village/construct").splitlines()
    assert not any(" outline" in l for l in con)
    slab = next(i for i, l in enumerate(con) if "stone_brick_slab" in l)
    assert "fill ~-1 ~ ~-6 ~1 ~ ~-4 minecraft:air" in con[slab + 1:slab + 3]


def test_tree_clearing_covers_deep_sites(pack_root):
    for p in LAYOUT:
        body = text(pack_root, f"village/place/{p.id}")
        assert "~-48" in body and "~48" in body
        assert "replace minecraft:mangrove_roots" in body and "replace minecraft:mushroom_stem" in body


def test_door_landing_carved(pack_root):
    from tools.gen_village import landing_tiles
    fps = {q.id: footprint(q) for q in LAYOUT}
    for p in LAYOUT:
        if not BUILDINGS[p.building].door:
            continue
        tiles = landing_tiles(p)
        assert len(tiles) == 4, p.id
        for x, z in tiles:
            assert not any(in_fp(x, z, fp) for fp in fps.values()), (p.id, x, z)
        body = text(pack_root, f"village/build/{p.id}")
        assert "minecraft:dirt_path" in body and body.count("minecraft:air") >= 2


def test_paths_clear_trees_at_plaza_height(pack_root):
    con = text(pack_root, "village/construct")
    for p in LAYOUT:
        for x, z in path_tiles(p)[:3]:
            assert f"fill ~{x} ~-48 ~{z} ~{x} ~48 ~{z} minecraft:air replace #minecraft:logs" in con


def test_farm_crops_planted_after_light_update(pack_root):
    s = nbt.read(pack_root / "data/create_rpg/structure/farm.nbt")
    names = {p["Name"] for p in s["palette"]}
    assert not names & {"minecraft:wheat", "minecraft:carrots", "minecraft:potatoes"}
    assert 'summon minecraft:marker' in text(pack_root, "village/build/farm") and "rpg_farm" in text(pack_root, "village/build/farm")
    assert "schedule function create_rpg:village/plant_crops 10t" in text(pack_root, "village/construct")
    assert "execute at @e[type=minecraft:marker,tag=rpg_farm,limit=1] run function create_rpg:village/plant_crops_here" in text(pack_root, "village/plant_crops")
    here = text(pack_root, "village/plant_crops_here")
    for c in ("wheat[age=7]", "carrots[age=7]", "potatoes[age=7]"):
        assert c in here
