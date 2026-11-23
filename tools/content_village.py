"""Village data: NPCs, trades, starter kit, quests. Data only."""
from dataclasses import dataclass, field

from tools.structures import local_to_world

VILLAGE_OFFSET_Z = 56   # vanilla village center, south of the plaza


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
    building: str | None
    local_pos: tuple      # (lx, lz) inside building, or world (x, z) when building is None
    yaw: float
    trades: list = field(default_factory=list)

    @property
    def world_pos(self):
        if self.building is None:
            return self.local_pos
        return local_to_world(self.building, *self.local_pos)


NPCS = [
    Npc("chief", "촌장 오르빈", "gold", "minecraft:librarian", None, (0, 3), 180.0),
    Npc("smith", "대장장이 브론", "red", "minecraft:weaponsmith", "forge", (4, 4), 0.0, [
        Trade((EM, 6), (("mat", "plate_1"), 2)),
        Trade((EM, 10), (("mat", "plate_2"), 2)),
        Trade((EM, 4), (("scroll", "low"), 1)),
        Trade((EM, 8), (("scroll", "mid"), 1)),
        Trade((EM, 2), (("v", "create:copper_sheet"), 8)),
    ]),
    Npc("guild", "의뢰소장 한나", "aqua", "minecraft:cartographer", "guild", (4, 4), 90.0, [
        Trade((("mat", "essence_1"), 8), (EM, 2)),
        Trade((("mat", "essence_2"), 8), (EM, 4)),
        Trade((("mat", "essence_3"), 6), (EM, 6)),
        Trade((("mat", "essence_4"), 4), (EM, 10)),
        Trade((("v", "minecraft:rotten_flesh"), 32), (EM, 1)),
        Trade((("v", "minecraft:bone"), 24), (EM, 1)),
    ]),
    Npc("merchant", "상인 미로", "green", "minecraft:farmer", "stall", (2, 2), 270.0, [
        Trade((EM, 1), (("v", "minecraft:bread"), 8)),
        Trade((EM, 1), (("v", "minecraft:torch"), 16)),
        Trade((EM, 2), (("v", "create:zinc_ingot"), 4)),
        Trade((EM, 2), (("v", "create:andesite_alloy"), 8)),
        Trade((EM, 1), (("home",), 2)),
        Trade((EM, 1), (("v", "minecraft:paper"), 12)),
    ]),
]
