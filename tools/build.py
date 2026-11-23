"""Generate the datapack into <out>/create_rpg and zip it. Run: python -m tools.build"""
import json
import shutil
import sys
import zipfile
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


def _generators():
    from tools import gen_enhance, gen_give, gen_loot, gen_recipes, gen_skills, gen_smithing
    return [_pack_mcmeta, gen_skills.generate, gen_recipes.generate, gen_loot.generate, gen_smithing.generate, gen_enhance.generate, gen_give.generate]


def build(out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    root = out_dir / content.NAMESPACE
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for gen in _generators():
        gen(root)
    zip_path = out_dir / f"{content.NAMESPACE}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(root.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(root).as_posix())
    return zip_path


if __name__ == "__main__":
    print(build(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "build"))
