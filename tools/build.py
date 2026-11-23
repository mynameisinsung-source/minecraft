"""Generate the datapack into <out>/create_rpg and zip it. Run: python -m tools.build"""
import json
import shutil
import sys
from pathlib import Path

from tools import content


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


def _pack_mcmeta(root: Path) -> None:
    write_json(root / "pack.mcmeta", {"pack": {
        "pack_format": content.PACK_FORMAT,
        "description": "Create RPG — 사냥·광질·대장장이 성장 + Create 대장간"}})


GENERATORS = [_pack_mcmeta]


def build(out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    root = out_dir / content.NAMESPACE
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for gen in GENERATORS:
        gen(root)
    return out_dir / f"{content.NAMESPACE}.zip"


if __name__ == "__main__":
    print(build(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "build"))
