"""Village v2: hand-laid, terrain-following custom village (no vanilla village).

construct (at plaza centre) -> plaza -> place/<id> (clear trees at plaza height, then find ground with
`positioned over motion_blocking_no_leaves`) -> build/<id> (foundation, air, template, NPC marker+summon)
-> terrain-following dirt paths -> lanterns and flowers -> spawn.
"""
import json
from pathlib import Path

from tools.build import write_json, write_text
from tools.content_village import NPCS, Npc, home_scroll_components, resolve
from tools.items import cost_snbt, give_stack_command, stack_snbt
from tools.structures import (BUILDINGS, LAYOUT, PLACED, PLAZA_HALF, Placed, build_all, door_world, footprint,
                              origin_for, rotation_for)

NS = "create_rpg"
ST = f"storage {NS}:village"
H = PLAZA_HALF
OVER = "positioned over motion_blocking_no_leaves"
DIRS = {"s": (0, 1), "n": (0, -1), "e": (1, 0), "w": (-1, 0)}
YAW = {"s": 0.0, "w": 90.0, "n": 180.0, "e": 270.0}
NPC_BY_BUILDING = {n.building: n for n in NPCS}


def _tell(msg, color="yellow"):
    return "tellraw @s " + json.dumps({"text": msg, "color": color}, ensure_ascii=False)


def offer_snbt(t) -> str:
    (bspec, bcount), (sspec, scount) = t.buy, t.sell
    parts = [f"buy:{cost_snbt(*resolve(bspec), bcount)}"]
    if t.buy_b:
        parts.append(f"buyB:{cost_snbt(*resolve(t.buy_b[0]), t.buy_b[1])}")
    parts.append(f"sell:{stack_snbt(*resolve(sspec), scount)}")
    parts += ["maxUses:999999", "rewardExp:0b", "xp:0", "priceMultiplier:0.0f", "specialPrice:0", "demand:0"]
    return "{" + ",".join(parts) + "}"


def npc_nbt(n: Npc) -> str:
    name = json.dumps({"text": n.name, "color": n.color}, ensure_ascii=False)
    offers = ",".join(offer_snbt(t) for t in n.trades)
    yaw = YAW[PLACED[n.building].facing]
    return (f"{{NoAI:1b,Invulnerable:1b,PersistenceRequired:1b,Silent:1b,CustomNameVisible:1b,"
            f"CustomName:'{name}',Tags:[\"rpg_npc\",\"rpg_npc_{n.id}\"],Rotation:[{yaw}f,0.0f],"
            f'VillagerData:{{profession:"{n.profession}",level:5,type:"minecraft:plains"}},'
            f"Offers:{{Recipes:[{offers}]}}}}")


def _clamp(v):
    return max(-H, min(H, v))


def path_tiles(p: Placed) -> list:
    """2-wide L-shaped path from just outside the door to the plaza edge, outside every footprint."""
    if not BUILDINGS[p.building].door:
        return []
    ux, uz = DIRS[p.facing]
    dx, dz = door_world(p)
    pts = [(dx + ux, dz + uz)]
    x, z = dx + 2 * ux, dz + 2 * uz
    pts.append((x, z))
    tx, tz = _clamp(x), _clamp(z)
    order = ("x", "z") if p.facing in "ns" else ("z", "x")
    for axis in order:
        while (x if axis == "x" else z) != (tx if axis == "x" else tz):
            if axis == "x":
                x += 1 if tx > x else -1
            else:
                z += 1 if tz > z else -1
            pts.append((x, z))
    tiles = []
    for i, (x, z) in enumerate(pts):
        nx, nz = (pts[i + 1] if i + 1 < len(pts) else pts[i - 1])
        horizontal = nz == z
        for t in ((x, z), (x, z + 1) if horizontal else (x + 1, z)):
            tiles.append(t)
    fps = [footprint(q) for q in LAYOUT]
    out = []
    for t in tiles:
        if t in out or (abs(t[0]) <= H and abs(t[1]) <= H):
            continue
        if any(f[0] <= t[0] <= f[1] and f[2] <= t[1] <= f[3] for f in fps):
            continue
        out.append(t)
    return out


def _free(x, z, taken):
    fps = [footprint(q) for q in LAYOUT]
    return ((x, z) not in taken and not (abs(x) <= H + 1 and abs(z) <= H + 1)
            and not any(f[0] - 1 <= x <= f[1] + 1 and f[2] - 1 <= z <= f[3] + 1 for f in fps))


def decorations(all_tiles) -> list:
    taken = set(all_tiles)
    L = []
    for p in LAYOUT:                                   # a lantern post beside each path, near the door
        if not BUILDINGS[p.building].door:
            continue
        ux, uz = DIRS[p.facing]
        dx, dz = door_world(p)
        px, pz = dx + 3 * ux + 2 * uz, dz + 3 * uz + 2 * ux
        if _free(px, pz, taken):
            taken.add((px, pz))
            L += [f"execute positioned ~{px} ~ ~{pz} {OVER} run fill ~ ~ ~ ~ ~1 ~ minecraft:oak_fence",
                  f"execute positioned ~{px} ~ ~{pz} {OVER} run setblock ~ ~ ~ minecraft:lantern[hanging=false]"]
    flowers = ["minecraft:poppy", "minecraft:dandelion", "minecraft:azure_bluet", "minecraft:oxeye_daisy",
               "minecraft:cornflower", "minecraft:allium"]
    spots = [(-13, -13), (13, 13), (-13, 13), (13, -13), (-26, -8), (26, -6), (-4, 28), (8, -30), (-28, 26),
             (28, 28), (-27, -26), (25, -30), (0, -27), (-12, 30), (36, -2), (-36, -4), (16, 10), (-14, -12)]
    for i, (x, z) in enumerate(spots):
        for ox, oz in ((0, 0), (1, 0), (0, 1)):
            fx, fz = x + ox, z + oz
            if _free(fx, fz, taken):
                taken.add((fx, fz))
                L.append(f"execute positioned ~{fx} ~ ~{fz} {OVER} run setblock ~ ~ ~ {flowers[(i + ox) % len(flowers)]} keep")
    return L


def construct() -> str:
    L = ["scoreboard players set #tpl rpg_tmp 0",
         "kill @e[type=minecraft:villager,tag=rpg_npc,distance=..60]",
         "kill @e[type=minecraft:marker,tag=rpg_spot,distance=..60]",
         f"fill ~-{H} ~ ~-{H} ~{H} ~15 ~{H} minecraft:air",
         f"fill ~-{H} ~-6 ~-{H} ~{H} ~-2 ~{H} minecraft:stone",
         f"fill ~-{H} ~-1 ~-{H} ~{H} ~-1 ~{H} minecraft:stone_bricks",
         f"fill ~-{H - 1} ~-1 ~-{H - 1} ~{H - 1} ~-1 ~{H - 1} minecraft:dirt_path",
         f"fill ~-1 ~-1 ~-{H} ~1 ~-1 ~{H} minecraft:polished_andesite",
         f"fill ~-{H} ~-1 ~-1 ~{H} ~-1 ~1 minecraft:polished_andesite",
         # fountain north of centre
         "fill ~-2 ~-1 ~-7 ~2 ~-1 ~-3 minecraft:stone_bricks",
         "fill ~-1 ~-1 ~-6 ~1 ~-1 ~-4 minecraft:water",
         "fill ~-2 ~ ~-7 ~2 ~ ~-3 minecraft:stone_brick_slab[type=bottom] outline",
         "setblock ~ ~-1 ~-5 minecraft:stone_bricks",
         "setblock ~ ~ ~-5 minecraft:stone_brick_wall",
         "setblock ~ ~1 ~-5 minecraft:lantern[hanging=false]",
         "setblock ~4 ~ ~4 minecraft:bell[attachment=floor,facing=north]"]
    for x, z in ((8, 8), (-8, 8), (8, -8), (-8, -8)):
        L += [f"fill ~{x} ~ ~{z} ~{x} ~1 ~{z} minecraft:oak_fence",
              f"setblock ~{x} ~2 ~{z} minecraft:lantern[hanging=false]"]
    L += [f"execute positioned ~{p.cx} ~ ~{p.cz} run function {NS}:village/place/{p.id}" for p in LAYOUT]
    tiles = []
    for p in LAYOUT:
        for t in path_tiles(p):
            if t not in tiles:
                tiles.append(t)
    for x, z in tiles:
        L += [f"execute positioned ~{x} ~ ~{z} {OVER} run fill ~ ~ ~ ~ ~1 ~ minecraft:air replace #minecraft:replaceable",
              f"execute positioned ~{x} ~ ~{z} {OVER} run setblock ~ ~-1 ~ minecraft:dirt_path"]
    L += decorations(tiles)
    L += ["setworldspawn ~ ~ ~",
          "gamerule spawnRadius 0",
          f"execute if score #tpl rpg_tmp matches 1 run data modify {ST} built set value 1b",
          'execute if score #tpl rpg_tmp matches 0 run tellraw @a {"text":"마을을 짓지 못했어요(청크가 로드되지 않음). 그 자리에 서서 /function create_rpg:village/build_here 를 다시 입력하세요.","color":"red"}',
          'execute if score #tpl rpg_tmp matches 1 run tellraw @a [{"text":"마을이 완성됐어요! ","color":"gold"},{"text":"남쪽 촌장 집의 오르빈에게 말을 걸어 보세요.","color":"yellow"}]',
          "playsound minecraft:block.bell.use master @a ~ ~ ~ 1 1"]
    return "\n".join(L) + "\n"


def place_fn(p: Placed) -> str:
    x1, x2, z1, z2 = footprint(p)
    a, b, c, d = x1 - p.cx - 1, x2 - p.cx + 1, z1 - p.cz - 1, z2 - p.cz + 1
    return "\n".join([
        f"fill ~{a} ~-6 ~{c} ~{b} ~24 ~{d} minecraft:air replace #minecraft:logs",
        f"fill ~{a} ~-6 ~{c} ~{b} ~24 ~{d} minecraft:air replace #minecraft:leaves",
        f"execute {OVER} run function {NS}:village/build/{p.id}"]) + "\n"


def build_fn(p: Placed) -> str:
    bld = BUILDINGS[p.building]
    x1, x2, z1, z2 = footprint(p)
    a, b, c, d = x1 - p.cx, x2 - p.cx, z1 - p.cz, z2 - p.cz
    ox, oz = origin_for(p)
    tpl = f"place template {NS}:{p.building} ~{ox - p.cx} ~-1 ~{oz - p.cz} {rotation_for(p.facing)}"
    L = [f"fill ~{a} ~-6 ~{c} ~{b} ~-2 ~{d} minecraft:cobblestone",
         f"fill ~{a} ~ ~{c} ~{b} ~{bld.sy + 1} ~{d} minecraft:air",
         f"execute store success score #tpl rpg_tmp run {tpl}" if p.id == "forge" else tpl]
    n = NPC_BY_BUILDING.get(p.id)
    if n:
        wx, wz = n.world_pos
        rx, rz = wx - p.cx, wz - p.cz
        L += [f'summon minecraft:marker ~{rx} ~ ~{rz} {{Tags:["rpg_spot","rpg_spot_{n.id}"]}}',
              f"summon minecraft:villager ~{rx} ~ ~{rz} {npc_nbt(n)}"]
    return "\n".join(L) + "\n"


def respawn_here() -> str:
    L = ["kill @e[type=minecraft:villager,tag=rpg_npc]"]
    for n in NPCS:
        at = f"execute at @e[type=minecraft:marker,tag=rpg_spot_{n.id},limit=1] run"
        L += [f"{at} kill @e[type=minecraft:witch,distance=..4]", f"{at} summon minecraft:villager ~ ~ ~ {npc_nbt(n)}"]
    return "\n".join(L) + "\n"


def generate(root: Path) -> None:
    d = root / "data" / NS
    build_all(d / "structure")
    f = d / "function"
    write_json(d / "advancement" / "village" / "first_join.json", {
        "criteria": {"join": {"trigger": "minecraft:tick"}},
        "rewards": {"function": f"{NS}:village/first_join"}})
    write_text(f / "village" / "first_join.mcfunction", "\n".join([
        f"execute if data {ST} built run return 0",
        "execute if entity @s[advancements={minecraft:story/root=true}] run "
        + _tell("이미 진행 중인 월드예요. 마을을 지을 곳에 서서 /function create_rpg:village/build_here 를 입력하세요."),
        "execute if entity @s[advancements={minecraft:story/root=true}] run return 0",
        f"function {NS}:village/build_here"]) + "\n")
    write_text(f / "village" / "build_here.mcfunction", "\n".join([
        f"execute if data {ST} built run " + _tell("이미 마을이 있어요. /function create_rpg:home 으로 돌아갈 수 있어요."),
        f"execute if data {ST} built run return 0",
        "execute unless dimension minecraft:overworld run " + _tell("마을은 오버월드에만 지을 수 있어요.", "red"),
        "execute unless dimension minecraft:overworld run return 0",
        f"execute store result {ST} x int 1 run data get entity @s Pos[0]",
        f"execute store result {ST} y int 1 run data get entity @s Pos[1]",
        f"execute store result {ST} z int 1 run data get entity @s Pos[2]",
        _tell("5초 뒤에 이 자리를 중심으로 약 70×70칸에 마을이 생겨요. 그동안 제자리에 서 있으세요."),
        f"schedule function {NS}:village/build 100t"]) + "\n")
    write_text(f / "village" / "build.mcfunction", "\n".join([
        f"execute if data {ST} built run return 0",
        f"function {NS}:village/build_at with {ST}"]) + "\n")
    write_text(f / "village" / "build_at.mcfunction",
               f"$execute in minecraft:overworld positioned $(x) $(y) $(z) run function {NS}:village/construct\n")
    write_text(f / "village" / "construct.mcfunction", construct())
    for p in LAYOUT:
        write_text(f / "village" / "place" / f"{p.id}.mcfunction", place_fn(p))
        write_text(f / "village" / "build" / f"{p.id}.mcfunction", build_fn(p))
    write_text(f / "village" / "respawn_npcs.mcfunction", "\n".join([
        f"execute unless data {ST} built run " + _tell("아직 마을이 없어요.", "red"),
        f"execute if data {ST} built run function {NS}:village/respawn_npcs_here",
        f"execute if data {ST} built run " + _tell("마을 NPC를 다시 불러왔어요. (마을 안에서 실행해야 해요)", "green")]) + "\n")
    write_text(f / "village" / "respawn_npcs_here.mcfunction", respawn_here())
    write_text(f / "home.mcfunction", "\n".join([
        f"execute unless data {ST} built run " + _tell("아직 마을이 없어요.", "red"),
        f"execute if data {ST} built run function {NS}:village/home_tp with {ST}"]) + "\n")
    write_text(f / "village" / "home_tp.mcfunction", "\n".join([
        "$execute in minecraft:overworld run tp @s $(x) $(y) $(z)",
        "playsound minecraft:entity.enderman.teleport player @s",
        _tell("마을로 돌아왔어요.", "green")]) + "\n")
    write_json(d / "advancement" / "village" / "drink_home.json", {
        "criteria": {"drink": {"trigger": "minecraft:consume_item", "conditions": {"item": {
            "items": "minecraft:potion", "predicates": {"minecraft:custom_data": '{%s:"scroll_home"}' % NS}}}}},
        "rewards": {"function": f"{NS}:village/use_home"}})
    write_text(f / "village" / "use_home.mcfunction",
               f"advancement revoke @s only {NS}:village/drink_home\nfunction {NS}:home\n")
    write_text(f / "give" / "scroll_home.mcfunction",
               give_stack_command("minecraft:potion", home_scroll_components(), 16) + "\n")
