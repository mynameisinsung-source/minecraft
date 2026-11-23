"""Skill trees -> data/create_rpg/puffish_skills/..."""
from pathlib import Path

from tools.build import write_json
from tools.content import NAMESPACE, SKILL_TREES, SMITHING_CRAFTS, Node


def _definition(n: Node) -> dict:
    d = {"title": n.title, "description": n.description,
         "icon": {"type": "item", "data": {"item": n.icon_item}},
         "frame": {"type": "advancement", "data": {"frame": n.frame}},
         "rewards": n.rewards}
    if n.cost != 1:
        d["cost"] = n.cost
    if n.required_spent_points is not None:
        d["required_spent_points"] = n.required_spent_points
    return d


def generate(root: Path) -> None:
    base = root / "data" / NAMESPACE / "puffish_skills"
    write_json(base / "config.json", {"version": 3, "categories": list(SKILL_TREES)})
    for cat, tree in SKILL_TREES.items():
        d = base / "categories" / cat
        write_json(d / "category.json", {
            "title": tree.title, "icon": {"type": "item", "data": {"item": tree.icon_item}},
            "background": tree.background, "unlocked_by_default": True, "starting_points": 0})
        write_json(d / "definitions.json", {n.id: _definition(n) for n in tree.nodes})
        write_json(d / "skills.json", {n.id: {"x": n.x, "y": n.y, "definition": n.id, "root": n.parent is None}
                                       for n in tree.nodes})
        pairs = [[p, n.id] for n in tree.nodes for p in ((n.parent,) + n.extra_parents) if p]
        write_json(d / "connections.json", {"normal": {"bidirectional": pairs}})
        write_json(d / "experience.json", {
            "level_limit": len(tree.xp_values),
            "experience_per_level": {"type": "values", "data": {"values": tree.xp_values}},
            "sources": tree.sources})
    write_json(root / "data" / NAMESPACE / "tags" / "item" / "smithing_crafts.json",
               {"replace": False, "values": SMITHING_CRAFTS})
