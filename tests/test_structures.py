import pytest

from tools import nbt
from tools.structures import BUILDINGS, PLACEMENTS, PLAZA_HALF, footprint, build_all

NAMES = ["forge", "guild", "stall"]


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
    return {n: nbt.read(d / f"{n}.nbt") for n in NAMES}


@pytest.mark.parametrize("name", NAMES)
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


@pytest.mark.parametrize("name", NAMES)
def test_door_opening_on_south_wall(structs, name):
    s = structs[name]
    sx, _, sz = s["size"]
    solid = {tuple(b["pos"]) for b in s["blocks"] if s["palette"][b["state"]]["Name"] != "minecraft:air"}
    mid = sx // 2
    assert (mid, 1, sz - 1) not in solid and (mid, 2, sz - 1) not in solid
    assert (0, 1, sz - 1) in solid  # wall corner exists


def test_footprints_inside_plaza_and_disjoint():
    fps = {n: footprint(n) for n in NAMES}
    for n, (x1, x2, z1, z2) in fps.items():
        assert -PLAZA_HALF <= x1 <= x2 <= PLAZA_HALF and -PLAZA_HALF <= z1 <= z2 <= PLAZA_HALF, n
    names = list(fps)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = fps[names[i]], fps[names[j]]
            assert a[1] < b[0] or b[1] < a[0] or a[3] < b[2] or b[3] < a[2], (names[i], names[j])


def test_doors_face_plaza_center():
    # door = local (mid, sz-1) mapped to world; must be the footprint edge nearest the center
    from tools.structures import local_to_world
    for n in NAMES:
        b = BUILDINGS[n]
        wx, wz = local_to_world(n, b.sx // 2, b.sz - 1)
        x1, x2, z1, z2 = footprint(n)
        cx, cz = (x1 + x2) / 2, (z1 + z2) / 2
        assert abs(wx) + abs(wz) < abs(cx) + abs(cz), n
