"""Building designs -> structure template NBT (1.21.1, DataVersion 3955).

Every building is designed with its door on the south wall (local +z, z = sz-1) and local y=0 as its
floor; PLACEMENTS rotates it so the door faces the plaza center. Plaza center = (0, 0) = first player pos.
"""
from dataclasses import dataclass, field
from pathlib import Path

from tools import nbt

DATA_VERSION = 3955
PLAZA_HALF = 10


@dataclass
class Building:
    name: str
    sx: int
    sy: int
    sz: int
    door: bool = True
    blocks: dict = field(default_factory=dict)

    def set(self, x, y, z, state):
        assert 0 <= x < self.sx and 0 <= y < self.sy and 0 <= z < self.sz, (self.name, x, y, z)
        self.blocks[(x, y, z)] = state

    def fill(self, x1, y1, z1, x2, y2, z2, state):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    self.set(x, y, z, state)

    def walls(self, y1, y2, state):
        for y in range(y1, y2 + 1):
            for x in range(self.sx):
                self.set(x, y, 0, state)
                self.set(x, y, self.sz - 1, state)
            for z in range(self.sz):
                self.set(0, y, z, state)
                self.set(self.sx - 1, y, z, state)

    def to_structure(self) -> nbt.Compound:
        palette, index, blocks = [], {}, []
        for (x, y, z), state in sorted(self.blocks.items()):
            if state not in index:
                index[state] = len(palette)
                name, _, props = state.partition("[")
                entry = {"Name": nbt.String(name)}
                if props:
                    entry["Properties"] = nbt.Compound({k: nbt.String(v) for k, v in
                                                        (p.split("=") for p in props.rstrip("]").split(","))})
                palette.append(nbt.Compound(entry))
            blocks.append(nbt.Compound({"pos": nbt.List(nbt.Int, [nbt.Int(x), nbt.Int(y), nbt.Int(z)]),
                                        "state": nbt.Int(index[state])}))
        return nbt.Compound({
            "DataVersion": nbt.Int(DATA_VERSION),
            "size": nbt.List(nbt.Int, [nbt.Int(self.sx), nbt.Int(self.sy), nbt.Int(self.sz)]),
            "palette": nbt.List(nbt.Compound, palette),
            "blocks": nbt.List(nbt.Compound, blocks),
            "entities": nbt.List(nbt.Compound, []),
        })


AIR = "minecraft:air"
LANTERN = "minecraft:lantern[hanging=true,waterlogged=false]"


def _forge() -> Building:
    b = Building("forge", 9, 8, 9)
    b.fill(0, 0, 0, 8, 7, 8, AIR)
    b.fill(0, 0, 0, 8, 0, 8, "minecraft:stone_bricks")
    b.walls(1, 4, "minecraft:cobblestone")
    for x, z in ((0, 0), (8, 0), (0, 8), (8, 8)):
        b.fill(x, 1, z, x, 4, z, "minecraft:oak_log[axis=y]")
    b.fill(3, 1, 8, 5, 3, 8, AIR)                         # wide forge entrance
    for x, z in ((0, 4), (8, 4)):
        b.set(x, 2, z, "minecraft:glass")
    b.fill(0, 5, 0, 8, 5, 8, "minecraft:deepslate_tiles")
    b.fill(1, 6, 1, 7, 6, 7, "minecraft:deepslate_tile_slab[type=bottom,waterlogged=false]")
    b.fill(7, 5, 1, 7, 6, 1, "minecraft:bricks")          # chimney
    b.set(7, 7, 1, "minecraft:campfire[lit=true,signal_fire=false,facing=north,waterlogged=false]")
    b.set(1, 1, 1, "minecraft:chest[facing=south,type=single,waterlogged=false]")
    b.set(3, 1, 1, "minecraft:smithing_table")
    b.set(5, 1, 1, "minecraft:blast_furnace[facing=south,lit=true]")
    b.set(6, 1, 1, "minecraft:furnace[facing=south,lit=true]")
    b.set(7, 1, 1, "minecraft:lava_cauldron")
    b.set(2, 1, 3, "minecraft:anvil[facing=east]")
    b.set(6, 1, 3, "minecraft:grindstone[face=floor,facing=north]")
    b.set(7, 1, 5, "create:andesite_casing")
    b.set(7, 2, 5, "create:andesite_casing")
    b.set(7, 1, 6, "create:andesite_casing")
    for x, z in ((4, 4), (2, 6), (6, 6)):
        b.set(x, 4, z, LANTERN)
    return b


def _guild() -> Building:
    b = Building("guild", 9, 8, 9)
    b.fill(0, 0, 0, 8, 7, 8, AIR)
    b.fill(0, 0, 0, 8, 0, 8, "minecraft:oak_planks")
    b.walls(1, 4, "minecraft:oak_planks")
    for x, z in ((0, 0), (8, 0), (0, 8), (8, 8), (4, 0), (0, 4), (8, 4)):
        b.fill(x, 1, z, x, 4, z, "minecraft:spruce_log[axis=y]")
    b.fill(4, 1, 8, 4, 2, 8, AIR)                         # door
    for x, z in ((2, 8), (6, 8), (0, 2), (0, 6), (8, 2), (8, 6)):
        b.set(x, 2, z, "minecraft:glass")
    b.fill(0, 5, 0, 8, 5, 8, "minecraft:spruce_planks")
    b.fill(1, 6, 1, 7, 6, 7, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    b.fill(1, 1, 1, 7, 2, 1, "minecraft:bookshelf")
    b.set(4, 1, 1, "minecraft:lectern[facing=south,has_book=false,powered=false]")
    b.set(4, 2, 1, AIR)
    b.set(6, 1, 1, "minecraft:cartography_table")
    b.fill(7, 2, 3, 7, 3, 5, "minecraft:spruce_trapdoor[facing=west,half=bottom,open=true,powered=false,waterlogged=false]")
    b.set(1, 1, 6, "minecraft:barrel[facing=up,open=false]")
    b.set(1, 1, 7, "minecraft:barrel[facing=up,open=false]")
    for x, z in ((4, 4), (2, 2), (6, 6)):
        b.set(x, 4, z, LANTERN)
    return b


def _stall() -> Building:
    b = Building("stall", 5, 5, 5)
    b.fill(0, 0, 0, 4, 4, 4, AIR)
    b.fill(0, 0, 0, 4, 0, 4, "minecraft:spruce_planks")
    for x, z in ((0, 0), (4, 0), (0, 4), (4, 4)):
        b.fill(x, 1, z, x, 3, z, "minecraft:oak_fence[east=false,north=false,south=false,west=false,waterlogged=false]")
    for x in range(5):
        b.fill(x, 4, 0, x, 4, 4, "minecraft:red_wool" if x % 2 == 0 else "minecraft:white_wool")
    b.set(1, 1, 3, "minecraft:barrel[facing=up,open=false]")
    b.set(2, 1, 3, "minecraft:spruce_slab[type=top,waterlogged=false]")
    b.set(3, 1, 3, "minecraft:barrel[facing=up,open=false]")
    b.set(1, 1, 0, "minecraft:hay_block[axis=y]")
    b.set(2, 1, 0, "minecraft:composter[level=0]")
    b.set(3, 1, 0, "minecraft:hay_block[axis=y]")
    b.set(2, 3, 2, LANTERN)
    return b


def _stairs(wood, facing):
    return f"minecraft:{wood}_stairs[facing={facing},half=bottom,shape=straight,waterlogged=false]"


def gable_roof(b: Building, y0: int, roof_wood: str, gable_block: str):
    """Ridge along x. Rows of stairs rise from both z edges toward the middle; gable ends filled."""
    k = 0
    while k < b.sz - 1 - k:
        y = y0 + k
        for x in range(b.sx):
            b.set(x, y, k, _stairs(roof_wood, "south"))
            b.set(x, y, b.sz - 1 - k, _stairs(roof_wood, "north"))
        for z in range(k + 1, b.sz - 1 - k):
            b.set(0, y, z, gable_block)
            b.set(b.sx - 1, y, z, gable_block)
        k += 1
    if k == b.sz - 1 - k:
        for x in range(b.sx):
            b.set(x, y0 + k, k, f"minecraft:{roof_wood}_planks")


def _chief_house() -> Building:
    b = Building("chief_house", 9, 9, 9)
    b.fill(0, 0, 0, 8, 8, 8, AIR)
    b.fill(0, 0, 0, 8, 0, 8, "minecraft:stone_bricks")
    b.walls(1, 1, "minecraft:stone_bricks")
    b.walls(2, 3, "minecraft:spruce_planks")
    for x, z in ((0, 0), (8, 0), (0, 8), (8, 8)):
        b.fill(x, 1, z, x, 3, z, "minecraft:spruce_log[axis=y]")
    b.fill(4, 1, 8, 4, 2, 8, AIR)
    for x, z in ((2, 8), (6, 8), (0, 4), (8, 4), (4, 0)):
        b.set(x, 2, z, "minecraft:glass")
    gable_roof(b, 4, "dark_oak", "minecraft:spruce_planks")
    b.set(1, 1, 1, "minecraft:red_bed[facing=north,part=head,occupied=false]")
    b.set(1, 1, 2, "minecraft:red_bed[facing=north,part=foot,occupied=false]")
    b.fill(5, 1, 1, 7, 2, 1, "minecraft:bookshelf")
    b.set(7, 1, 3, "minecraft:lectern[facing=west,has_book=false,powered=false]")
    b.set(1, 1, 6, "minecraft:chest[facing=east,type=single,waterlogged=false]")
    b.set(7, 1, 6, "minecraft:barrel[facing=up,open=false]")
    b.set(7, 2, 6, "minecraft:lantern[hanging=false,waterlogged=false]")
    b.fill(3, 1, 3, 5, 1, 5, AIR)
    for x in range(3, 6):
        for z in range(3, 6):
            b.set(x, 0, z, "minecraft:red_terracotta")
    return b


def _inn() -> Building:
    b = Building("inn", 11, 10, 9)
    b.fill(0, 0, 0, 10, 9, 8, AIR)
    b.fill(0, 0, 0, 10, 0, 8, "minecraft:oak_planks")
    b.walls(1, 4, "minecraft:oak_planks")
    for x in (0, 5, 10):
        for z in (0, 8):
            b.fill(x, 1, z, x, 4, z, "minecraft:stripped_oak_log[axis=y]")
    b.fill(5, 1, 8, 5, 2, 8, AIR)
    for x in (2, 3, 7, 8):
        b.set(x, 2, 8, "minecraft:glass")
        b.set(x, 2, 0, "minecraft:glass")
    gable_roof(b, 5, "spruce", "minecraft:oak_planks")
    for x in (1, 3, 7, 9):
        b.set(x, 1, 1, "minecraft:white_bed[facing=north,part=head,occupied=false]")
        b.set(x, 1, 2, "minecraft:white_bed[facing=north,part=foot,occupied=false]")
    for x in (2, 8):
        b.set(x, 1, 1, "minecraft:barrel[facing=up,open=false]")
        b.set(x, 2, 1, "minecraft:lantern[hanging=false,waterlogged=false]")
    for x, z in ((2, 5), (8, 5)):
        b.set(x, 1, z, "minecraft:oak_fence[east=false,north=false,south=false,west=false,waterlogged=false]")
        b.set(x, 2, z, "minecraft:oak_pressure_plate[powered=false]")
        b.set(x - 1, 1, z, _stairs("oak", "east"))
        b.set(x + 1, 1, z, _stairs("oak", "west"))
    b.set(5, 4, 4, LANTERN)
    return b


def _workshop() -> Building:
    b = Building("workshop", 11, 7, 11)
    b.fill(0, 0, 0, 10, 6, 10, AIR)
    b.fill(0, 0, 0, 10, 0, 10, "minecraft:polished_andesite")
    for x in (0, 5, 10):
        for z in (0, 5, 10):
            if (x, z) != (5, 5) and not (x == 5 and z == 10):
                b.fill(x, 1, z, x, 4, z, "minecraft:stripped_spruce_log[axis=y]")
    b.fill(0, 5, 0, 10, 5, 10, "minecraft:spruce_slab[type=bottom,waterlogged=false]")
    b.fill(1, 1, 0, 4, 1, 0, "minecraft:spruce_fence[east=true,north=false,south=false,west=true,waterlogged=false]")
    b.fill(6, 1, 0, 9, 1, 0, "minecraft:spruce_fence[east=true,north=false,south=false,west=true,waterlogged=false]")
    b.set(1, 1, 1, "minecraft:crafting_table")
    b.set(2, 1, 1, "minecraft:chest[facing=south,type=single,waterlogged=false]")
    b.set(3, 1, 1, "minecraft:chest[facing=south,type=single,waterlogged=false]")
    b.set(9, 1, 1, "create:andesite_casing")
    b.set(8, 1, 1, "create:andesite_casing")
    for x, z in ((2, 2), (8, 8), (2, 8), (8, 2)):
        b.set(x, 4, z, LANTERN)
    return b


WOOD_ROOF = {"oak": "dark_oak", "spruce": "spruce", "birch": "oak"}


def _house(wood: str) -> Building:
    b = Building(f"house_{wood}", 7, 8, 7)
    b.fill(0, 0, 0, 6, 7, 6, AIR)
    b.fill(0, 0, 0, 6, 0, 6, "minecraft:cobblestone")
    b.walls(1, 3, f"minecraft:{wood}_planks")
    for x, z in ((0, 0), (6, 0), (0, 6), (6, 6)):
        b.fill(x, 1, z, x, 3, z, f"minecraft:{wood}_log[axis=y]")
    b.fill(3, 1, 6, 3, 2, 6, AIR)
    for x, z in ((1, 6), (5, 6), (0, 3), (6, 3), (3, 0)):
        b.set(x, 2, z, "minecraft:glass")
    gable_roof(b, 4, WOOD_ROOF[wood], f"minecraft:{wood}_planks")
    b.set(1, 1, 1, "minecraft:light_blue_bed[facing=north,part=head,occupied=false]")
    b.set(1, 1, 2, "minecraft:light_blue_bed[facing=north,part=foot,occupied=false]")
    b.set(5, 1, 1, "minecraft:crafting_table")
    b.set(5, 1, 2, "minecraft:barrel[facing=up,open=false]")
    b.set(5, 2, 2, "minecraft:lantern[hanging=false,waterlogged=false]")
    b.set(1, 1, 5, "minecraft:flower_pot")
    return b


def _farm() -> Building:
    b = Building("farm", 9, 3, 9, door=False)
    b.fill(0, 0, 0, 8, 2, 8, AIR)
    b.fill(0, 0, 0, 8, 0, 8, "minecraft:farmland[moisture=7]")
    b.fill(1, 0, 4, 7, 0, 4, "minecraft:water[level=0]")
    crops = ["minecraft:wheat[age=7]", "minecraft:carrots[age=7]", "minecraft:potatoes[age=7]"]
    for z in range(1, 8):
        if z == 4:
            continue
        for x in range(1, 8):
            b.set(x, 1, z, crops[(x - 1) // 3 % 3])
    for x in range(9):
        for z in (0, 8):
            b.set(x, 0, z, "minecraft:oak_log[axis=x]")
            b.set(x, 1, z, "minecraft:oak_fence[east=true,north=false,south=false,west=true,waterlogged=false]")
    for z in range(1, 8):
        for x in (0, 8):
            b.set(x, 0, z, "minecraft:oak_log[axis=z]")
            b.set(x, 1, z, "minecraft:oak_fence[east=false,north=true,south=true,west=false,waterlogged=false]")
    b.set(4, 1, 8, "minecraft:oak_fence_gate[facing=south,in_wall=false,open=false,powered=false]")
    b.set(0, 1, 0, "minecraft:hay_block[axis=y]")
    b.set(8, 1, 8, "minecraft:composter[level=0]")
    return b


def _well() -> Building:
    b = Building("well", 5, 6, 5, door=False)
    b.fill(0, 0, 0, 4, 5, 4, AIR)
    b.fill(0, 0, 0, 4, 0, 4, "minecraft:cobblestone")
    b.fill(1, 0, 1, 3, 0, 3, "minecraft:water[level=0]")
    for x in range(5):
        for z in range(5):
            if x in (0, 4) or z in (0, 4):
                b.set(x, 1, z, "minecraft:stone_brick_wall[east=low,north=low,south=low,west=low,up=true,waterlogged=false]")
    for x, z in ((0, 0), (4, 0), (0, 4), (4, 4)):
        b.fill(x, 2, z, x, 3, z, "minecraft:oak_fence[east=false,north=false,south=false,west=false,waterlogged=false]")
    b.fill(0, 4, 0, 4, 4, 4, "minecraft:oak_slab[type=bottom,waterlogged=false]")
    b.set(2, 3, 2, LANTERN)
    return b


BUILDINGS = {b.name: b for b in (_forge(), _guild(), _stall(), _chief_house(), _inn(), _workshop(),
                                 _house("oak"), _house("spruce"), _house("birch"), _farm(), _well())}


@dataclass(frozen=True)
class Placed:
    id: str
    building: str
    cx: int
    cz: int
    facing: str          # direction the door faces: n / e / s / w


# Hand-placed, deliberately irregular; checked by tests for overlap and door direction.
LAYOUT = [
    Placed("forge", "forge", -3, -19, "s"),
    Placed("workshop", "workshop", 12, -21, "s"),
    Placed("guild", "guild", 20, -1, "w"),
    Placed("stall_1", "stall", -17, -4, "e"),
    Placed("stall_2", "stall", -17, 4, "e"),
    Placed("chief_house", "chief_house", 2, 20, "n"),
    Placed("inn", "inn", -18, 18, "e"),
    Placed("well", "well", -8, 18, "s"),
    Placed("farm", "farm", 20, 20, "s"),
    Placed("house_1", "house_oak", -20, -20, "s"),
    Placed("house_2", "house_spruce", 30, -14, "w"),
    Placed("house_3", "house_birch", 32, 6, "w"),
    Placed("house_4", "house_oak", -31, 12, "e"),
    Placed("house_5", "house_spruce", 12, 32, "n"),
    Placed("house_6", "house_birch", -14, -32, "s"),
]
PLACED = {p.id: p for p in LAYOUT}

_ROT = {"s": "none", "w": "clockwise_90", "n": "180", "e": "counterclockwise_90"}


def rotation_for(facing: str) -> str:
    return _ROT[facing]


def _rot(rotation, x, z):
    return {"none": (x, z), "clockwise_90": (-z, x), "180": (-x, -z), "counterclockwise_90": (z, -x)}[rotation]


def _extent(p: Placed):
    b = BUILDINGS[p.building]
    pts = [_rot(rotation_for(p.facing), x, z) for x in (0, b.sx - 1) for z in (0, b.sz - 1)]
    return min(q[0] for q in pts), max(q[0] for q in pts), min(q[1] for q in pts), max(q[1] for q in pts)


def origin_for(p: Placed):
    x1, x2, z1, z2 = _extent(p)
    return p.cx - (x1 + x2) // 2, p.cz - (z1 + z2) // 2


def local_to_world(p: Placed, lx, lz):
    ox, oz = origin_for(p)
    rx, rz = _rot(rotation_for(p.facing), lx, lz)
    return ox + rx, oz + rz


def footprint(p: Placed):
    ox, oz = origin_for(p)
    x1, x2, z1, z2 = _extent(p)
    return ox + x1, ox + x2, oz + z1, oz + z2


def door_world(p: Placed):
    b = BUILDINGS[p.building]
    return local_to_world(p, b.sx // 2, b.sz - 1)


def build_all(out_dir: Path) -> None:
    for name, b in BUILDINGS.items():
        nbt.write(Path(out_dir) / f"{name}.nbt", b.to_structure())
