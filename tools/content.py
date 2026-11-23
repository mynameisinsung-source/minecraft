"""All names, numbers and recipes of the datapack. Data only."""
from dataclasses import dataclass, field

NAMESPACE = "create_rpg"
PACK_FORMAT = 48
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV"}
TIER_COLOR = {1: "white", 2: "yellow", 3: "aqua", 4: "light_purple"}


@dataclass(frozen=True)
class Material:
    id: str
    base: str
    name: str
    lore: list = field(default_factory=list)
    glint: bool = False
    color: str | None = None


def _series(prefix, base, name, lore):
    return {f"{prefix}_{n}": Material(f"{prefix}_{n}", base, f"{name} {ROMAN[n]}", [lore.format(n=n)],
                                      glint=n >= 3, color=TIER_COLOR[n])
            for n in range(1, 5)}


MATERIALS: dict[str, Material] = {
    **_series("essence", "minecraft:prismarine_crystals", "몬스터 정수", "{n}단계 몬스터에게서 얻은 정수"),
    **_series("fragment", "minecraft:disc_fragment_5", "광맥 조각", "{n}단계 광맥에서 캐낸 조각"),
    **_series("powder", "minecraft:glowstone_dust", "강화 가루", "광맥 조각 {n}단계를 분쇄한 가루"),
    **_series("alloy", "minecraft:netherite_scrap", "강화 합금", "{n}단계 장비의 재료가 되는 합금"),
    **_series("plate", "create:iron_sheet", "강화 합금 판", "{n}단계 합금을 눌러 만든 판"),
    "legend_core": Material("legend_core", "minecraft:heart_of_the_sea", "전설 핵",
                            ["위더의 별에서 뽑아낸 힘", "전설 장비의 심장"], glint=True, color="gold"),
}
