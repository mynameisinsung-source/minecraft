"""First forge of each gear -> one-time advancement -> smithing XP function."""
from pathlib import Path

from tools.build import write_json, write_text
from tools.content import GEAR_SLOTS, NAMESPACE, SLOT_NAME, TIERS
from tools.gen_recipes import gear_id, vanilla_item

XP_PER_TIER = 40
CATEGORY = f"{NAMESPACE}:smithing"


def generate(root: Path) -> None:
    adv = root / "data" / NAMESPACE / "advancement" / "forge"
    fn = root / "data" / NAMESPACE / "function" / "forge"
    write_json(adv / "root.json", {
        "display": {"icon": {"id": "minecraft:anvil"}, "title": "대장간",
                    "description": "Create 공정으로 RPG 장비를 단련하세요",
                    "background": "minecraft:textures/gui/advancements/backgrounds/nether.png",
                    "show_toast": False, "announce_to_chat": False},
        "criteria": {"start": {"trigger": "minecraft:tick"}}})
    for t in TIERS:
        for slot in GEAR_SLOTS:
            gid = gear_id(t, slot)
            item = vanilla_item(t.base_material, slot)
            parent = "root" if t.n == 1 else gear_id(TIERS[t.n - 2], slot)
            write_json(adv / f"{gid}.json", {
                "parent": f"{NAMESPACE}:forge/{parent}",
                "display": {"icon": {"id": item}, "title": f"{t.name} {SLOT_NAME[slot]}",
                            "description": f"처음으로 {t.name} {SLOT_NAME[slot]}을(를) 단련했다 (+{t.n * XP_PER_TIER} 대장장이 경험치)",
                            "frame": "challenge" if t.n == 5 else ("goal" if t.n >= 3 else "task"),
                            "show_toast": True, "announce_to_chat": True},
                "criteria": {"forged": {"trigger": "minecraft:inventory_changed", "conditions": {"items": [
                    {"items": item, "predicates": {"minecraft:custom_data": '{%s:"%s"}' % (NAMESPACE, gid)}}]}}},
                "rewards": {"function": f"{NAMESPACE}:forge/{gid}"}})
            write_text(fn / f"{gid}.mcfunction",
                       f"puffish_skills experience add @s {CATEGORY} {t.n * XP_PER_TIER}\n")
