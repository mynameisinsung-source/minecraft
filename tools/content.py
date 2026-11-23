"""All names, numbers and recipes of the datapack. Data only."""
from dataclasses import dataclass, field

NAMESPACE = "create_rpg"
PACK_FORMAT = 48
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV"}
TIER_COLOR = {1: "white", 2: "yellow", 3: "aqua", 4: "light_purple"}


@dataclass(frozen=True)
class Material:
    id: str
    base: str
    name: str
    lore: list = field(default_factory=list)
    glint: bool = False
    color: str | None = None


def _series(prefix, base, name, lore):
    return {f"{prefix}_{n}": Material(f"{prefix}_{n}", base, f"{name} {ROMAN[n]}", [lore.format(n=n)],
                                      glint=n >= 3, color=TIER_COLOR[n])
            for n in range(1, 5)}


MATERIALS: dict[str, Material] = {
    **_series("essence", "minecraft:prismarine_crystals", "몬스터 정수", "{n}단계 몬스터에게서 얻은 정수"),
    **_series("fragment", "minecraft:disc_fragment_5", "광맥 조각", "{n}단계 광맥에서 캐낸 조각"),
    **_series("powder", "minecraft:glowstone_dust", "강화 가루", "광맥 조각 {n}단계를 분쇄한 가루"),
    **_series("alloy", "minecraft:netherite_scrap", "강화 합금", "{n}단계 장비의 재료가 되는 합금"),
    **_series("plate", "create:iron_sheet", "강화 합금 판", "{n}단계 합금을 눌러 만든 판"),
    "legend_core": Material("legend_core", "minecraft:heart_of_the_sea", "전설 핵",
                            ["위더의 별에서 뽑아낸 힘", "전설 장비의 심장"], glint=True, color="gold"),
}


# ---------------------------------------------------------------- skill trees
@dataclass(frozen=True)
class Node:
    id: str
    title: str
    description: str
    icon_item: str
    rewards: list
    parent: str | None
    x: int
    y: int
    cost: int = 1
    frame: str = "task"
    required_spent_points: int | None = None
    extra_parents: tuple = ()


@dataclass(frozen=True)
class Tree:
    title: str
    icon_item: str
    background: str
    nodes: list
    xp_values: list
    sources: list


XP_VALUES = [20, 30, 45, 60, 80, 100, 125, 150, 180, 210, 245, 280, 320, 360, 400, 450, 500, 550, 600, 650]
GATE_SPENT = [3, 7, 11]
GATE_COST = 3  # 10 regular nodes + 3 gates x 3 = 19 points ≤ 20 levels


def attr(attribute: str, value: float, op: str) -> dict:
    return {"type": "puffish_skills:attribute",
            "data": {"attribute": attribute, "value": value, "operation": op}}


def tag_reward(tag: str) -> dict:
    return {"type": "puffish_skills:tag", "data": {"tag": tag}}


def command_reward(cmd: str) -> dict:
    return {"type": "puffish_skills:command", "data": {"command": cmd}}


def _fmt(v, op):
    return f"+{round(v * 100)}%" if op == "multiply_total" else f"+{v:g}"


def _tree(key, title, icon, bg, branches, gates, xp_sources, root_icon):
    """branches: 3 x (name, icon, attribute, value, op). gates: 3 x (title, desc, icon, rewards)."""
    nodes = [Node(f"{key}_root", f"{title}의 길", f"{title} 성장을 시작합니다. {branches[0][0]} {_fmt(branches[0][3], branches[0][4])}",
                  root_icon, [attr(*branches[0][2:])], None, 0, 0)]
    dirs = [(-1, -1), (0, -1), (1, -1)]
    for b, (name, bicon, attribute, value, op) in enumerate(branches):
        parent = f"{key}_root"
        for step in range(1, 4):
            nid = f"{key}_{'abc'[b]}{step}"
            nodes.append(Node(nid, f"{name} {ROMAN[step]}", f"{name} {_fmt(value, op)}", bicon,
                              [attr(attribute, value, op)], parent,
                              dirs[b][0] * 40 * step, dirs[b][1] * 34 * step))
            parent = nid
    prev = None
    for g, (gtitle, gdesc, gicon, grewards) in enumerate(gates, start=1):
        parents = (f"{key}_a3", f"{key}_b3", f"{key}_c3") if g == 1 else (prev,)
        nid = f"{key}_gate{g}"
        nodes.append(Node(nid, gtitle, gdesc, gicon, grewards, parents[0], 0, 40 + 34 * (g - 1),
                          cost=GATE_COST, frame="goal", required_spent_points=GATE_SPENT[g - 1],
                          extra_parents=parents[1:]))
        prev = nid
    return Tree(title, icon, bg, nodes, XP_VALUES, xp_sources)


def _var(*ops):
    return {"operations": list(ops)}


def _test(**data):
    return {"type": "puffish_skills:test", "data": data}


HUNTING_SOURCES = [{
    "type": "puffish_skills:kill_entity",
    "data": {
        "variables": {
            "dropped_xp": _var({"type": "get_dropped_experience"}),
            "max_health": _var({"type": "get_killed_living_entity"}, {"type": "get_max_health"}),
            "is_wither": _var({"type": "get_killed_living_entity"}, {"type": "get_type"},
                              _test(entity_type="minecraft:wither")),
            "is_dragon": _var({"type": "get_killed_living_entity"}, {"type": "get_type"},
                              _test(entity_type="minecraft:ender_dragon")),
        },
        "experience": [
            {"condition": "is_wither", "expression": "300"},
            {"condition": "is_dragon", "expression": "800"},
            {"expression": "dropped_xp + max_health / 10"},
        ],
        "anti_farming": {"limit_per_chunk": 20, "reset_after_seconds": 300},
    },
}]

MINING_SOURCES = [{
    "type": "puffish_skills:mine_block",
    "data": {
        "variables": {
            "is_debris": _var({"type": "get_mined_block_state"}, _test(block="minecraft:ancient_debris")),
            "is_ore": _var({"type": "get_mined_block_state"}, _test(block="#c:ores")),
            "is_stone": _var({"type": "get_mined_block_state"}, _test(block="#minecraft:base_stone_overworld")),
        },
        "experience": [
            {"condition": "is_debris", "expression": "40"},
            {"condition": "is_ore", "expression": "8"},
            {"condition": "is_stone", "expression": "0.2"},
        ],
    },
}]

SMITHING_CRAFTS = [
    "create:cogwheel", "create:large_cogwheel", "create:shaft", "create:andesite_casing", "create:brass_casing",
    "create:copper_casing", "create:mechanical_press", "create:mechanical_mixer", "create:deployer", "create:basin",
    "create:depot", "create:belt_connector", "create:millstone", "create:crushing_wheel", "create:mechanical_crafter",
    "create:spout", "create:fluid_tank", "create:blaze_burner", "create:precision_mechanism", "create:electron_tube",
]

SMITHING_SOURCES = [{
    "type": "puffish_skills:craft_item",
    "data": {
        "variables": {
            "is_part": _var({"type": "get_crafted_item_stack"}, _test(item="#create_rpg:smithing_crafts")),
            "count": _var({"type": "get_crafted_item_stack"}, {"type": "get_count"}),
        },
        "experience": [{"condition": "is_part", "expression": "count * 4"}],
    },
}]


def _smith_gate(n):
    from tools.items import give_command
    return [tag_reward(f"rpg_smith_{n}"), command_reward(give_command(f"plate_{n}", 4))]


BG = "minecraft:textures/gui/advancements/backgrounds/{}.png"

SKILL_TREES: dict[str, Tree] = {
    "hunting": _tree(
        "hunting", "사냥", "minecraft:iron_sword", BG.format("adventure"),
        [("공격력", "minecraft:iron_sword", "generic.attack_damage", 1, "addition"),
         ("생명력", "minecraft:golden_apple", "generic.max_health", 2, "addition"),
         ("공격 속도", "minecraft:feather", "generic.attack_speed", 0.05, "multiply_total")],
        [("사냥꾼 II", "해금: 몬스터 정수 II가 떨어지기 시작합니다.", "minecraft:prismarine_crystals", [tag_reward("rpg_hunt_1")]),
         ("사냥꾼 III", "해금: 네더 몬스터가 몬스터 정수 III을 떨어뜨립니다.", "minecraft:blaze_rod", [tag_reward("rpg_hunt_2")]),
         ("사냥꾼 IV", "해금: 엔드 몬스터가 몬스터 정수 IV를 떨어뜨립니다.", "minecraft:ender_eye", [tag_reward("rpg_hunt_3")])],
        HUNTING_SOURCES, "minecraft:bone"),
    "mining": _tree(
        "mining", "광질", "minecraft:iron_pickaxe", BG.format("stone"),
        [("채굴 속도", "minecraft:golden_pickaxe", "player.block_break_speed", 0.1, "multiply_total"),
         ("행운", "minecraft:emerald", "generic.luck", 0.5, "addition"),
         ("채굴 효율", "minecraft:iron_pickaxe", "player.mining_efficiency", 2, "addition")],
        [("광부 II", "해금: 금·레드스톤·청금석 광석에서 광맥 조각 II가 나옵니다.", "minecraft:gold_ore", [tag_reward("rpg_mine_1")]),
         ("광부 III", "해금: 네더 광석과 고대 잔해에서 광맥 조각 III이 나옵니다.", "minecraft:nether_quartz_ore", [tag_reward("rpg_mine_2")]),
         ("광부 IV", "해금: 다이아몬드·에메랄드 광석에서 광맥 조각 IV가 나옵니다.", "minecraft:diamond_ore", [tag_reward("rpg_mine_3")])],
        MINING_SOURCES, "minecraft:stone_pickaxe"),
    "smithing": _tree(
        "smithing", "대장장이", "minecraft:anvil", BG.format("nether"),
        [("방어력", "minecraft:iron_chestplate", "generic.armor", 1, "addition"),
         ("방어 강도", "minecraft:diamond_chestplate", "generic.armor_toughness", 0.5, "addition"),
         ("밀치기 저항", "minecraft:shield", "generic.knockback_resistance", 0.05, "addition")],
        [("숙련 대장장이", "보너스: 강화 합금 판 I 4개를 받습니다.", "create:iron_sheet", _smith_gate(1)),
         ("장인 대장장이", "보너스: 강화 합금 판 II 4개를 받습니다.", "create:brass_casing", _smith_gate(2)),
         ("명장 대장장이", "보너스: 강화 합금 판 III 4개를 받습니다.", "minecraft:smithing_table", _smith_gate(3))],
        SMITHING_SOURCES, "create:cogwheel"),
}
