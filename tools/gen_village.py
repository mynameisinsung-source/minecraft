"""Village construction (once per world), home teleport, return scroll, NPC summons."""
import json
from pathlib import Path

from tools.build import write_json, write_text
from tools.content_village import NPCS, VILLAGE_OFFSET_Z, Npc, home_scroll_components, resolve
from tools.items import cost_snbt, stack_snbt
from tools.structures import PLACEMENTS, PLAZA_HALF, build_all

NS = "create_rpg"
ST = f"storage {NS}:village"
H = PLAZA_HALF


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


def summon_npc(n: Npc) -> str:
    x, z = n.world_pos
    name = json.dumps({"text": n.name, "color": n.color}, ensure_ascii=False)
    offers = ",".join(offer_snbt(t) for t in n.trades)
    tag = (f"{{NoAI:1b,Invulnerable:1b,PersistenceRequired:1b,Silent:1b,CustomNameVisible:1b,"
           f"CustomName:'{name}',Tags:[\"rpg_npc\",\"rpg_npc_{n.id}\"],Rotation:[{n.yaw}f,0.0f],"
           f'VillagerData:{{profession:"{n.profession}",level:5,type:"minecraft:plains"}},'
           f"Offers:{{Recipes:[{offers}]}}}}")
    return f"summon minecraft:villager ~{x + 0.5} ~ ~{z + 0.5} {tag}"


def construct() -> str:
    L = [f"fill ~-{H} ~ ~-{H} ~{H} ~15 ~{H} minecraft:air",
         f"fill ~-{H} ~-6 ~-{H} ~{H} ~-2 ~{H} minecraft:stone",
         f"fill ~-{H} ~-1 ~-{H} ~{H} ~-1 ~{H} minecraft:stone_bricks",
         f"fill ~-{H - 2} ~-1 ~-{H - 2} ~{H - 2} ~-1 ~{H - 2} minecraft:dirt_path",
         f"fill ~-1 ~-1 ~-{H - 2} ~1 ~-1 ~{H - 2} minecraft:polished_andesite",
         f"fill ~-{H - 2} ~-1 ~-1 ~{H - 2} ~-1 ~1 minecraft:polished_andesite"]
    for name, (dx, dz, rot) in PLACEMENTS.items():
        L.append(f"place template {NS}:{name} ~{dx} ~-1 ~{dz} {rot}")
    L.append("setblock ~2 ~ ~2 minecraft:bell[attachment=floor,facing=north]")
    for x, z in ((6, 6), (-6, 6), (6, -6), (-6, -6)):
        L += [f"fill ~{x} ~ ~{z} ~{x} ~1 ~{z} minecraft:oak_fence",
              f"setblock ~{x} ~2 ~{z} minecraft:lantern[hanging=false]"]
    L.append(f"kill @e[type=minecraft:villager,tag=rpg_npc,distance=..{H * 2}]")
    L += [summon_npc(n) for n in NPCS]
    L += [f"execute store success score #vil rpg_tmp run place structure minecraft:village_plains ~ ~ ~{VILLAGE_OFFSET_Z}",
          'execute if score #vil rpg_tmp matches 0 run tellraw @a {"text":"(바닐라 마을은 생성하지 못했어요. 광장과 NPC는 정상이에요.)","color":"gray"}',
          "setworldspawn ~ ~ ~",
          f"data modify {ST} built set value 1b",
          'tellraw @a [{"text":"마을이 완성됐어요! ","color":"gold"},{"text":"광장의 촌장 오르빈에게 말을 걸어 보세요.","color":"yellow"}]',
          "playsound minecraft:block.bell.use master @a ~ ~ ~ 1 1"]
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
        + _tell("이미 진행 중인 월드예요. 마을을 지을 곳(평평하고 넓은 곳)에 서서 /function create_rpg:village/build_here 를 입력하세요."),
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
        _tell("5초 뒤에 이 자리에 마을이 생겨요. 주변 27×27칸이 정리됩니다."),
        f"schedule function {NS}:village/build 100t"]) + "\n")
    write_text(f / "village" / "build.mcfunction", "\n".join([
        f"execute if data {ST} built run return 0",
        f"function {NS}:village/build_at with {ST}"]) + "\n")
    write_text(f / "village" / "build_at.mcfunction",
               f"$execute in minecraft:overworld positioned $(x) $(y) $(z) run function {NS}:village/construct\n")
    write_text(f / "village" / "construct.mcfunction", construct())
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
    from tools.items import give_stack_command
    write_text(f / "give" / "scroll_home.mcfunction",
               give_stack_command("minecraft:potion", home_scroll_components(), 16) + "\n")
