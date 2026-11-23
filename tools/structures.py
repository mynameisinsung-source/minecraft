"""Building designs -> structure template NBT (1.21.1, DataVersion 3955).

Every building is designed with its door on the south wall (local +z, z = sz-1) and local y=0 as its
floor; PLACEMENTS rotates it so the door faces the plaza center. Plaza center = (0, 0) = first player pos.
"""
from dataclasses import dataclass, field
from pathlib import Path

from tools import nbt

DATA_VERSION = 3955
PLAZA_HALF = 13


@dataclass
class Building:
    name: str
    sx: int
    sy: int
    sz: int
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


BUILDINGS = {b.name: b for b in (_forge(), _guild(), _stall())}

# name -> (dx, dz, rotation) of the template origin relative to plaza center; y = plaza floor (-1)
PLACEMENTS = {
    "forge": (-4, -12, "none"),
    "guild": (13, -4, "clockwise_90"),
    "stall": (-11, 2, "counterclockwise_90"),
}


def local_to_world(name, lx, lz):
    dx, dz, rot = PLACEMENTS[name]
    if rot == "none":
        return dx + lx, dz + lz
    if rot == "clockwise_90":
        return dx - lz, dz + lx
    if rot == "counterclockwise_90":
        return dx + lz, dz - lx
    raise ValueError(rot)


def footprint(name):
    b = BUILDINGS[name]
    pts = [local_to_world(name, x, z) for x in (0, b.sx - 1) for z in (0, b.sz - 1)]
    xs, zs = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), max(xs), min(zs), max(zs)


def build_all(out_dir: Path) -> None:
    for name, b in BUILDINGS.items():
        nbt.write(Path(out_dir) / f"{name}.nbt", b.to_structure())
