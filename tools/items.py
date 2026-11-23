"""RPG item helpers: data components, stacks, Create results, ingredients.

1.21.1 JSON component format: custom_name and lore entries are JSON-text *strings*.
Every RPG item is identified by custom_data {create_rpg: "<id>"}.
"""
import json

NS = "create_rpg"


def text(s: str, color: str | None = None) -> str:
    obj = {"text": s, "italic": False}
    if color:
        obj["color"] = color
    return json.dumps(obj, ensure_ascii=False)


def rpg_components(id: str, name: str, lore: list[str], glint: bool, extra: dict | None = None,
                   color: str | None = None) -> dict:
    comps = {
        "minecraft:custom_data": {NS: id},
        "minecraft:custom_name": text(name, color),
        "minecraft:lore": [text(line, "gray") for line in lore],
    }
    if glint:
        comps["minecraft:enchantment_glint_override"] = True
    if extra:
        comps.update(extra)
    return comps


def _material(mat_id: str):
    from tools.content import MATERIALS
    return MATERIALS[mat_id]


def material_components(mat_id: str) -> dict:
    m = _material(mat_id)
    return rpg_components(m.id, m.name, m.lore, m.glint, color=m.color)


def material_stack(mat_id: str, count: int = 1) -> dict:
    return {"id": _material(mat_id).base, "count": count, "components": material_components(mat_id)}


def material_result(mat_id: str, count: int = 1, chance: float | None = None) -> dict:
    r = {"id": _material(mat_id).base, "components": material_components(mat_id)}
    if count != 1:
        r["count"] = count
    if chance is not None:
        r["chance"] = chance
    return r


def rpg_ingredient(rpg_id: str, base: str) -> dict:
    return {"type": "neoforge:components", "items": base,
            "components": {"minecraft:custom_data": {NS: rpg_id}}, "strict": False}


def material_ingredient(mat_id: str) -> dict:
    return rpg_ingredient(mat_id, _material(mat_id).base)


def _snbt(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return f"'{v}'" if v.startswith("{") else json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ",".join(_snbt(x) for x in v) + "]"
    return "{" + ",".join(f"{k}:{_snbt(x)}" for k, x in v.items()) + "}"


def give_stack_command(base: str, comps: dict, count: int) -> str:
    """`give @s base[components] count` in 1.21.1 item-argument syntax."""
    return f"give @s {base}[{','.join(f'{k}={_snbt(v)}' for k, v in comps.items())}] {count}"


def give_command(mat_id: str, count: int) -> str:
    return give_stack_command(_material(mat_id).base, material_components(mat_id), count)
