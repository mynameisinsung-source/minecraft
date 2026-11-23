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
