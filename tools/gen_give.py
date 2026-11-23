"""Test helpers: /function create_rpg:give/<id> gives 16 materials/scrolls or 1 gear piece.
Needed because the full give commands exceed the 256-character chat limit."""
from pathlib import Path

from tools.build import write_text
from tools.content import GEAR_SLOTS, MATERIALS, NAMESPACE, SCROLLS, TIERS
from tools.gen_enhance import scroll_components
from tools.gen_recipes import gear_id, gear_result
from tools.items import give_command, give_stack_command


def generate(root: Path) -> None:
    d = root / "data" / NAMESPACE / "function" / "give"
    for m in MATERIALS:
        write_text(d / f"{m}.mcfunction", give_command(m, 16) + "\n")
    for g, s in SCROLLS.items():
        write_text(d / f"scroll_{g}.mcfunction", give_stack_command("minecraft:potion", scroll_components(s), 16) + "\n")
    for t in TIERS:
        for slot in GEAR_SLOTS:
            r = gear_result(t, slot)
            write_text(d / f"{gear_id(t, slot)}.mcfunction", give_stack_command(r["id"], r["components"], 1) + "\n")
