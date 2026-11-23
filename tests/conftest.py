import json
import sys
from collections import deque
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DATA = Path(__file__).resolve().parent / "data"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def pack_zip():
    from tools.build import build
    return build(ROOT / "build")


@pytest.fixture(scope="session")
def pack_root(pack_zip):
    return pack_zip.parent / "create_rpg"


SKILLS_DIR = "data/create_rpg/puffish_skills"


def cat_dir(pack_root, cat):
    return Path(pack_root) / SKILLS_DIR / "categories" / cat


def reachable(pack_root, cat):
    d = cat_dir(pack_root, cat)
    skills = load(d / "skills.json")
    pairs = load(d / "connections.json")["normal"]["bidirectional"]
    adj = {s: set() for s in skills}
    for a, b in pairs:
        adj[a].add(b)
        adj[b].add(a)
    seen = {s for s, v in skills.items() if v.get("root")}
    q = deque(seen)
    while q:
        for n in adj[q.popleft()]:
            if n not in seen:
                seen.add(n)
                q.append(n)
    return seen


def granted_tags(pack_root, cat):
    defs = load(cat_dir(pack_root, cat) / "definitions.json")
    return {r["data"]["tag"] for d in defs.values() for r in d.get("rewards", [])
            if r["type"] == "puffish_skills:tag"}


def all_granted_tags(pack_root):
    cats = load(Path(pack_root) / SKILLS_DIR / "config.json")["categories"]
    return set().union(*(granted_tags(pack_root, c) for c in cats))


RPG_RE = __import__("re").compile(r'create_rpg:\\?"(\w+)\\?"')


def _walk(obj):
    yield obj
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def _rpg_ids_in(obj):
    out = []
    for o in _walk(obj):
        if isinstance(o, dict) and isinstance(o.get("minecraft:custom_data"), dict):
            rid = o["minecraft:custom_data"].get("create_rpg")
            if rid:
                out.append(rid)
    return out


def recipes(pack_root):
    return [(p, load(p)) for p in sorted((Path(pack_root) / "data/create_rpg/recipe").rglob("*.json"))]


def recipe_output_rpg_ids(pack_root):
    return [rid for _, r in recipes(pack_root) for res in r.get("results", []) for rid in _rpg_ids_in(res)]


def consumed_rpg_ids(pack_root):
    out = set()
    for _, r in recipes(pack_root):
        for o in _walk(r):
            if isinstance(o, dict) and o.get("type") == "neoforge:components":
                out.add(o["components"]["minecraft:custom_data"]["create_rpg"])
    return out


def obtainable_rpg_ids(pack_root):
    root = Path(pack_root)
    out = set(recipe_output_rpg_ids(root))
    for p in (root / "data/create_rpg/loot_table").rglob("*.json"):
        out.update(_rpg_ids_in(load(p)))
    for p in (root / "data/create_rpg/puffish_skills").rglob("definitions.json"):
        out.update(RPG_RE.findall(p.read_text(encoding="utf-8")))
    return out


def all_item_ids(pack_root):
    root = Path(pack_root)
    ids = set()
    for _, r in recipes(root):
        for o in _walk(r):
            if isinstance(o, dict):
                for k in ("id", "item", "items"):
                    if isinstance(o.get(k), str) and ":" in o[k]:
                        ids.add(o[k])
    for p in (root / "data/create_rpg/tags/item").rglob("*.json"):
        ids.update(v for v in load(p)["values"] if not v.startswith("#"))
    return ids


def heat_of(pack_root, rpg_id):
    for _, r in recipes(pack_root):
        if r["type"] == "create:mixing" and rpg_id in [i for res in r["results"] for i in _rpg_ids_in(res)]:
            return r.get("heat_requirement")
    raise AssertionError(f"no mixing recipe for {rpg_id}")
