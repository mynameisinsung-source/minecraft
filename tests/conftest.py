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
