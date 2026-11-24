"""Village data: NPCs, trades, starter kit, quests. Data only."""
from dataclasses import dataclass, field

from tools.structures import PLACED, local_to_world



# ---- item specs: ("v", id) vanilla | ("mat", id) RPG material | ("scroll", grade) | ("home",)
def resolve(spec):
    from tools.content import MATERIALS, SCROLLS
    from tools.gen_enhance import scroll_components
    from tools.items import material_components
    kind = spec[0]
    if kind == "v":
        return spec[1], None
    if kind == "mat":
        return MATERIALS[spec[1]].base, material_components(spec[1])
    if kind == "scroll":
        return "minecraft:potion", scroll_components(SCROLLS[spec[1]])
    if kind == "home":
        return "minecraft:potion", home_scroll_components()
    raise ValueError(spec)


def home_scroll_components():
    from tools.items import rpg_components
    return rpg_components("scroll_home", "귀환 주문서", ["마시면 마을 광장으로 돌아갑니다"], glint=True, extra={
        "minecraft:potion_contents": {"potion": "minecraft:mundane", "custom_color": 0x50E070},
        "minecraft:max_stack_size": 16}, color="green")


EM = ("v", "minecraft:emerald")


@dataclass(frozen=True)
class Trade:
    buy: tuple          # (spec, count)
    sell: tuple         # (spec, count)
    buy_b: tuple | None = None


@dataclass(frozen=True)
class Npc:
    id: str
    name: str
    color: str
    profession: str
    building: str         # LAYOUT id
    local_pos: tuple      # (lx, lz) inside that building
    yaw: float
    trades: list = field(default_factory=list)

    @property
    def world_pos(self):
        return local_to_world(PLACED[self.building], *self.local_pos)


NPCS = [
    Npc("chief", "촌장 오르빈", "gold", "minecraft:librarian", "chief_house", (4, 4), 0.0),
    Npc("smith", "대장장이 브론", "red", "minecraft:weaponsmith", "forge", (4, 4), 0.0, [
        Trade((EM, 6), (("mat", "plate_1"), 2)),
        Trade((EM, 10), (("mat", "plate_2"), 2)),
        Trade((EM, 4), (("scroll", "low"), 1)),
        Trade((EM, 8), (("scroll", "mid"), 1)),
        Trade((EM, 2), (("v", "create:copper_sheet"), 8)),
    ]),
    Npc("guild", "의뢰소장 한나", "aqua", "minecraft:cartographer", "guild", (4, 4), 0.0, [
        Trade((("mat", "essence_1"), 8), (EM, 2)),
        Trade((("mat", "essence_2"), 8), (EM, 4)),
        Trade((("mat", "essence_3"), 6), (EM, 6)),
        Trade((("mat", "essence_4"), 4), (EM, 10)),
        Trade((("v", "minecraft:rotten_flesh"), 32), (EM, 1)),
        Trade((("v", "minecraft:bone"), 24), (EM, 1)),
    ]),
    Npc("merchant", "상인 미로", "green", "minecraft:farmer", "stall_1", (2, 2), 0.0, [
        Trade((EM, 1), (("v", "minecraft:bread"), 8)),
        Trade((EM, 1), (("v", "minecraft:torch"), 16)),
        Trade((EM, 2), (("v", "create:zinc_ingot"), 4)),
        Trade((EM, 2), (("v", "create:andesite_alloy"), 8)),
        Trade((EM, 1), (("home",), 2)),
        Trade((EM, 1), (("v", "minecraft:paper"), 12)),
    ]),
]


# ---------------------------------------------------------------- starter kit (chief, once)
STARTER_KIT = [
    (("v", "minecraft:stone_sword"), 1), (("v", "minecraft:stone_pickaxe"), 1), (("v", "minecraft:stone_axe"), 1),
    (("v", "minecraft:stone_shovel"), 1), (("v", "minecraft:bread"), 16), (("v", "minecraft:torch"), 32),
    (("v", "minecraft:white_bed"), 1), (("home",), 3), (("v", "create:andesite_alloy"), 16),
    (("v", "create:cogwheel"), 8), (("v", "create:shaft"), 16), (("scroll", "low"), 2), (EM, 5),
]


# ---------------------------------------------------------------- quests
@dataclass(frozen=True)
class Quest:
    id: str
    phase: str
    title: str
    kind: str            # kill | pickup | craft | forge
    target: str          # entity id / item id / gear rpg id
    count: int
    goal: str            # "좀비 10마리 처치"
    hint: str            # chief's "what now?" advice
    rewards: list        # [(spec, count)]
    icon: str

    @property
    def objective(self):
        return self.id

    @property
    def criterion(self):
        stat = {"kill": "killed", "pickup": "picked_up", "craft": "crafted"}[self.kind]
        return f"minecraft.{stat}:{self.target.replace(':', '.')}"


def _s(g, n=1):
    return (("scroll", g), n)


def _m(mid, n):
    return (("mat", mid), n)


QUESTS = [
    Quest("q01", "전반", "첫 사냥", "kill", "minecraft:zombie", 10, "좀비 10마리 처치",
          "밤이 되면 좀비가 나온다네. 10마리만 잡아 오게. 사냥 레벨도 오르고 몬스터 정수도 얻을 걸세.",
          [(EM, 4), _s("low")], "minecraft:rotten_flesh"),
    Quest("q02", "전반", "광부의 첫걸음", "pickup", "minecraft:raw_iron", 20, "철 원석 20개 줍기",
          "철광석을 캐 보게. 광질 레벨이 오르고, 가끔 광맥 조각도 나온다네.",
          [(EM, 4), _m("fragment_1", 4)], "minecraft:raw_iron"),
    Quest("q03", "전반", "톱니바퀴 장인", "craft", "create:cogwheel", 16, "톱니바퀴 16개 제작",
          "Create 기계의 기본은 톱니바퀴지. 제작대에서 16개를 만들어 보게. 대장장이 경험치도 오른다네.",
          [(EM, 5), (("v", "create:andesite_alloy"), 16)], "create:cogwheel"),
    Quest("q04", "전반", "첫 장비", "forge", "gear_apprentice_sword", 1, "구리 견습 검 만들기",
          "배포기(Deployer)에 구리 판을 들리고 철 검을 밑에 두면 구리 견습 검이 된다네. 황동이 필요하면 구리+아연+레드스톤을 혼합기에 넣게.",
          [(EM, 6), _s("low", 2)], "minecraft:iron_sword"),
    Quest("q05", "중반", "뼈를 모아라", "kill", "minecraft:skeleton", 25, "스켈레톤 25마리 처치",
          "스켈레톤 25마리를 잡아 오게. 사냥꾼 II를 찍었다면 몬스터 정수 II도 모일 걸세.",
          [(EM, 6), _m("essence_2", 3)], "minecraft:bone"),
    Quest("q06", "중반", "동굴 정리", "kill", "minecraft:cave_spider", 15, "동굴 거미 15마리 처치",
          "폐광에 동굴 거미가 득실거린다네. 15마리를 처치해 주게. 해독용 우유를 챙기게.",
          [(EM, 6), _m("plate_2", 2)], "minecraft:spider_eye"),
    Quest("q07", "중반", "빛나는 돌", "pickup", "minecraft:diamond", 5, "다이아몬드 5개 줍기",
          "깊은 곳으로 내려가 다이아몬드 5개를 모아 오게. 강철 장인 장비에 다이아 장비가 필요하다네.",
          [(EM, 8), _s("mid")], "minecraft:diamond"),
    Quest("q08", "중반", "숙련의 증표", "forge", "gear_journeyman_chestplate", 1, "황동 숙련 흉갑 만들기",
          "순차 조립 라인을 만들 차례일세. 구리 견습 흉갑에 판 I과 정수 I을 배포하고 압착하면 된다네.",
          [(EM, 8), _s("mid", 2)], "minecraft:iron_chestplate"),
    Quest("q09", "후반", "불꽃 사냥", "kill", "minecraft:blaze", 10, "블레이즈 10마리 처치",
          "이제 네더로 갈 때일세. 네더 요새의 블레이즈 10마리를 잡게. 블레이즈 버너를 만들려면 블레이즈도 한 마리 데려와야 하지.",
          [(EM, 10), _m("essence_3", 3)], "minecraft:blaze_rod"),
    Quest("q10", "후반", "검은 뼈", "kill", "minecraft:wither_skeleton", 10, "위더 스켈레톤 10마리 처치",
          "위더 스켈레톤 10마리를 처치하게. 해골을 모아 두면 위더를 부를 수 있다네.",
          [(EM, 10), _m("plate_3", 2)], "minecraft:wither_skeleton_skull"),
    Quest("q11", "후반", "고대의 잔해", "pickup", "minecraft:ancient_debris", 4, "고대 잔해 4개 줍기",
          "네더 깊은 곳의 고대 잔해 4개를 캐 오게. 광부 III을 찍었다면 광맥 조각 III도 확실히 나온다네.",
          [(EM, 12), _s("high", 2)], "minecraft:ancient_debris"),
    Quest("q12", "후반", "위더 토벌", "kill", "minecraft:wither", 1, "위더 처치",
          "위더를 쓰러뜨리면 네더의 별과 정수 IV가 나온다네. 전설 핵의 재료지. 단단히 준비하게.",
          [(EM, 16), _m("plate_4", 2)], "minecraft:nether_star"),
    Quest("q13", "후반", "공허의 사냥꾼", "kill", "minecraft:enderman", 20, "엔더맨 20마리 처치",
          "엔더맨 20마리를 잡게. 엔드에서 사냥꾼 IV가 있으면 정수 IV가 나온다네.",
          [(EM, 16), _s("top")], "minecraft:ender_pearl"),
    Quest("q14", "후반", "전설의 대장장이", "forge", "gear_legend_sword", 1, "전설 검 만들기",
          "비전 명장 검에 전설 핵과 판 IV를 배포하고 용암을 부어 압착하면 전설 검이 된다네.",
          [(EM, 20), _s("top", 2)], "minecraft:netherite_sword"),
    Quest("q15", "최종", "용 사냥", "kill", "minecraft:ender_dragon", 1, "엔더 드래곤 처치",
          "마지막일세. 엔더 드래곤을 쓰러뜨리고 돌아오게. 마을 모두가 자네를 기다리겠네.",
          [(EM, 32)], "minecraft:dragon_head"),
]
