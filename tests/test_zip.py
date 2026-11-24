import json
import zipfile


def test_zip_has_pack_mcmeta_at_root(pack_zip):
    with zipfile.ZipFile(pack_zip) as z:
        names = z.namelist()
    assert "pack.mcmeta" in names
    assert all(n == "pack.mcmeta" or n.startswith("data/") for n in names)


def test_zip_json_all_parse(pack_zip):
    with zipfile.ZipFile(pack_zip) as z:
        checked = 0
        for n in z.namelist():
            if n.endswith(".json") or n.endswith(".mcmeta"):
                json.loads(z.read(n).decode("utf-8"))
                checked += 1
    assert checked > 100
