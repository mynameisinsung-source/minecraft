import pytest

from tools import nbt
from tools.structures import (BUILDINGS, LAYOUT, PLAZA_HALF, build_all, door_world, footprint, local_to_world,
                              origin_for, rotation_for)


def test_nbt_roundtrip(tmp_path):
    root = nbt.Compound({"a": nbt.Int(5), "s": nbt.String("한글"), "l": nbt.List(nbt.Int, [nbt.Int(1), nbt.Int(2)]),
                         "e": nbt.List(nbt.Compound, []), "c": nbt.Compound({"f": nbt.Float(1.5)})})
    p = tmp_path / "x.nbt"
    nbt.write(p, root)
    assert nbt.read(p) == {"a": 5, "s": "한글", "l": [1, 2], "e": [], "c": {"f": 1.5}}


@pytest.fixture(scope="module")
def structs(tmp_path_factory):
    d = tmp_path_factory.mktemp("s")
    build_all(d)
    return {n: nbt.read(d / f"{n}.nbt") for n in BUILDINGS}


def test_expected_buildings():
    assert set(BUILDINGS) >= {"forge", "guild", "stall", "chief_house", "inn", "workshop",
                              "house_oak", "house_spruce", "house_birch", "farm", "well"}
    assert len(LAYOUT) == 15 and len({p.id for p in LAYOUT}) == 15


@pytest.mark.parametrize("name", list(BUILDINGS))
def test_structure_valid(structs, name):
    s = structs[name]
    assert s["DataVersion"] == 3955
    sx, sy, sz = s["size"]
    assert (sx, sy, sz) == (BUILDINGS[name].sx, BUILDINGS[name].sy, BUILDINGS[name].sz)
    for b in s["blocks"]:
        x, y, z = b["pos"]
        assert 0 <= x < sx and 0 <= y < sy and 0 <= z < sz
        assert 0 <= b["state"] < len(s["palette"])
    assert all(p["Name"].split(":")[0] in ("minecraft", "create") for p in s["palette"])


@pytest.mark.parametrize("name", [n for n, b in BUILDINGS.items() if b.door])
def test_door_opening_on_south_wall(structs, name):
    s = structs[name]
    sx, _, sz = s["size"]
    solid = {tuple(b["pos"]) for b in s["blocks"] if s["palette"][b["state"]]["Name"] != "minecraft:air"}
    mid = sx // 2
    assert (mid, 1, sz - 1) not in solid and (mid, 2, sz - 1) not in solid
    assert (0, 1, sz - 1) in solid


def test_rotation_mapping():
    assert [rotation_for(f) for f in "swne"] == ["none", "clockwise_90", "180", "counterclockwise_90"]


@pytest.mark.parametrize("p", LAYOUT, ids=lambda p: p.id)
def test_footprint_centred_on_layout_point(p):
    x1, x2, z1, z2 = footprint(p)
    assert ((x1 + x2) / 2, (z1 + z2) / 2) == (p.cx, p.cz)
    b = BUILDINGS[p.building]
    w, d = (b.sx, b.sz) if p.facing in "ns" else (b.sz, b.sx)
    assert (x2 - x1 + 1, z2 - z1 + 1) == (w, d)
    ox, oz = origin_for(p)
    assert local_to_world(p, 0, 0) == (ox, oz)


def test_layout_disjoint_with_margin():
    m = 2
    fps = {p.id: footprint(p) for p in LAYOUT}
    lim = PLAZA_HALF + m
    for pid, (x1, x2, z1, z2) in fps.items():
        assert x2 < -lim or x1 > lim or z2 < -lim or z1 > lim, pid
    ids = list(fps)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = fps[ids[i]], fps[ids[j]]
            assert a[1] + m < b[0] or b[1] + m < a[0] or a[3] + m < b[2] or b[3] + m < a[2], (ids[i], ids[j])


@pytest.mark.parametrize("p", [p for p in LAYOUT if BUILDINGS[p.building].door], ids=lambda p: p.id)
def test_doors_face_plaza(p):
    dx, dz = door_world(p)
    assert abs(dx) + abs(dz) < abs(p.cx) + abs(p.cz)
