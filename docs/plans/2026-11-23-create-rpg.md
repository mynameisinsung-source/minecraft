# Create RPG 데이터팩 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aternos(1.21.1 NeoForge, Create 6, Pufferfish's Skills)에서 동작하는 데이터팩 `create_rpg.zip`을 만든다. 사냥·광질·대장장이 스킬트리와, Create 공정으로 만드는 장비 5단계가 들어간다.

**Architecture:** 데이터팩 JSON은 손으로 쓰지 않는다. Python 생성기(`tools/`)가 한 곳의 데이터 정의(`tools/content.py`)에서 모든 파일을 `build/create_rpg/`에 만들고 zip으로 묶는다. pytest로 생성된 데이터팩의 구조, 상호 참조, 진행 가능성(모든 재료를 얻을 수 있는지)을 검증한다. 게임 안에서의 동작은 `INSTALL.md` 체크리스트로 사용자가 확인한다.

**Tech Stack:** Python 3.11+ (표준 라이브러리 + pytest), Minecraft 1.21.1 데이터팩 형식(pack_format 48), Create 6.0.3+ 레시피 JSON, Pufferfish's Skills config v3, NeoForge 전역 루트 수정자.

**Spec:** `docs/design.md`

## Global Constraints
- Minecraft 1.21.1, `pack.mcmeta`의 `pack_format`는 **48**, 네임스페이스는 `create_rpg`
- **틱 함수 금지:** `data/minecraft/tags/function/tick.json`을 만들지 않는다. 함수는 도전 과제 보상과 스킬 보상에서만 실행된다.
- 바닐라 드롭 테이블을 덮어쓰지 않는다. 드롭은 `neoforge:add_table` 전역 루트 수정자로만 추가한다.
- 능력치 ID는 1.21.1 형식(`generic.max_health`, `player.block_break_speed`처럼 접두사 포함)을 쓴다. Pufferfish's Attributes에 의존하지 않는다.
- 게임에 보이는 문구(아이템 이름, 설명, 스킬 이름)는 **한국어**로 쓴다. 이름은 `{"text":..., "italic":false}` 형식이다.
- RPG 아이템은 모두 `minecraft:custom_data` 안의 `{create_rpg:"<id>"}`로 구분한다. 레시피 재료는 `neoforge:components` 재료 타입에 `strict: false`, `components: {"minecraft:custom_data": {"create_rpg":"<id>"}}`를 쓴다.
- Create 레시피 결과물에 능력치나 이름을 붙일 때는 `{"id":..., "components":{...}}` 형식을 쓴다(6.0.3+).
- 형식 참고 자료: Create 레시피 예시는 `git clone --depth 1 --filter=blob:none --sparse -b mc1.21.1/dev https://github.com/Creators-of-Create/Create.git`의 `src/generated/resources/data/create/recipe`, Pufferfish 문서는 `git clone --depth 1 https://github.com/pufmat/modsdocs.git`의 `skills/src/creators`

## Review Focus
1. **진행이 막히는 재료:** 어떤 단계 레시피가 얻을 방법이 없는 RPG 아이템을 요구하면 그 단계에서 플레이가 멈춘다. → Task 3의 `test_every_consumed_item_is_obtainable`
2. **태그 이름 불일치:** 스킬 보상 태그(`rpg_hunt_1`)와 드롭 조건의 태그 이름이 다르면 상위 재료가 영영 안 나온다. → Task 4의 `test_loot_gate_tags_are_granted_by_skills`
3. **스킬트리 고립 노드:** 연결에서 빠진 노드는 찍을 수 없다. → Task 2의 `test_every_skill_reachable_from_root`
4. **도전 과제 → 함수 참조 오류:** 존재하지 않는 함수를 가리키면 대장장이 경험치가 조용히 사라진다. → Task 5의 `test_advancement_rewards_point_to_existing_functions`
5. **zip 구조 오류:** `pack.mcmeta`가 zip 최상위에 없으면 Aternos가 데이터팩을 인식하지 못한다. → Task 6의 `test_zip_has_pack_mcmeta_at_root`

---

## 파일 구조
```
create-rpg/
  docs/design.md, docs/plans/…
  tools/
    content.py      # 모든 수치·이름·레시피 정의 (데이터만, 로직 없음)
    items.py        # RPG 아이템 스택/재료 JSON 헬퍼
    gen_skills.py   # 스킬트리 3개 → puffish_skills 파일
    gen_recipes.py  # Create 레시피
    gen_loot.py     # 드롭 테이블 + 전역 루트 수정자
    gen_smithing.py # 장비 첫 획득 도전 과제 + 함수
    build.py        # 전체 생성 + zip (python -m tools.build)
  tests/
    conftest.py     # build를 한 번 실행하고 경로 fixture 제공
    test_pack.py, test_skills.py, test_recipes.py, test_loot.py, test_smithing.py
  build/            # 생성물 (git 제외)
  INSTALL.md
```

---

### Task 1: 프로젝트 뼈대, 아이템 헬퍼, pack.mcmeta

**Files:**
- Create: `tools/__init__.py`, `tools/items.py`, `tools/content.py`(이 Task에서는 `NAMESPACE`, `PACK_FORMAT`, `MATERIALS`만), `tools/build.py`, `tests/conftest.py`, `tests/test_pack.py`, `.gitignore`(`build/`, `__pycache__/`)

**Interfaces:**
- Produces:
  - `content.NAMESPACE = "create_rpg"`, `content.PACK_FORMAT = 48`
  - `content.MATERIALS: dict[str, Material]`. `Material`은 dataclass `(id: str, base: str, name: str, lore: list[str], glint: bool)`. 다음 ID를 정의한다.
    - `essence_1`~`essence_4` (몬스터 정수 I~IV, base `minecraft:prismarine_crystals`)
    - `fragment_1`~`fragment_4` (광맥 조각 I~IV, base `minecraft:disc_fragment_5`)
    - `powder_1`~`powder_4` (강화 가루 I~IV, base `minecraft:glowstone_dust`)
    - `alloy_1`~`alloy_4` (강화 합금 I~IV, base `minecraft:netherite_scrap`)
    - `plate_1`~`plate_4` (강화 합금 판 I~IV, base `create:iron_sheet`)
    - `legend_core` (전설 핵, base `minecraft:heart_of_the_sea`)
  - `items.rpg_components(id: str, name: str, lore: list[str], glint: bool, extra: dict | None = None) -> dict`: 데이터 컴포넌트 dict(`minecraft:custom_data`, `minecraft:item_name` 대신 `minecraft:custom_name`, `minecraft:lore`, `minecraft:enchantment_glint_override`, 그리고 `extra` 병합)
  - `items.material_stack(mat_id: str, count: int = 1) -> dict`: 루트 테이블이나 `give`에 쓰는 `{"id","count","components"}`
  - `items.material_result(mat_id: str, count: int = 1, chance: float | None = None) -> dict`: Create 결과물 형식
  - `items.rpg_ingredient(rpg_id: str, base: str) -> dict`: `neoforge:components` 재료
  - `build.build(out_dir: Path) -> Path`: 데이터팩 폴더를 만들고 zip 경로(`out_dir/create_rpg.zip`)를 반환. 각 `gen_*` 모듈의 `generate(root: Path) -> None`을 차례로 호출한다(이 Task에서는 `pack.mcmeta`만 생성).
  - `tests/conftest.py`: 세션 fixture `pack_root -> Path`(`build/create_rpg`)와 `pack_zip -> Path`, 헬퍼 `load(path) -> dict`

- [ ] **Step 1: 실패하는 테스트 작성** (`tests/test_pack.py`)
```python
def test_pack_mcmeta(pack_root):
    meta = load(pack_root / "pack.mcmeta")
    assert meta["pack"]["pack_format"] == 48
    assert "Create RPG" in meta["pack"]["description"]

def test_no_tick_function(pack_root):
    assert not (pack_root / "data/minecraft/tags/function/tick.json").exists()

def test_material_ingredient_is_strict_on_custom_data():
    ing = rpg_ingredient("essence_1", "minecraft:prismarine_crystals")
    assert ing == {"type": "neoforge:components", "items": "minecraft:prismarine_crystals",
                   "components": {"minecraft:custom_data": {"create_rpg": "essence_1"}}, "strict": False}

def test_all_material_names_are_korean_and_unique():
    names = [m.name for m in MATERIALS.values()]
    assert len(names) == len(set(names)) == 21
    assert all(any("가" <= ch <= "힣" for ch in n) for n in names)
```
- [ ] **Step 2:** `python -m pytest tests/test_pack.py -v` 실행 → import 오류로 FAIL
- [ ] **Step 3:** 위 Interfaces대로 `items.py`, `content.py`, `build.py`, `conftest.py` 구현
- [ ] **Step 4:** `python -m pytest tests/test_pack.py -v` 실행 → 4 passed
- [ ] **Step 5:** `git init`(최초 1회) 후 커밋 `feat: scaffold datapack generator`

---

### Task 2: 스킬트리 3개 (사냥 / 광질 / 대장장이)

**Files:**
- Modify: `tools/content.py`(스킬 정의 추가)
- Create: `tools/gen_skills.py`, `tests/test_skills.py`

**Interfaces:**
- Consumes: `content.NAMESPACE`
- Produces:
  - 카테고리 ID `hunting`, `mining`, `smithing`. 파일 위치 `data/create_rpg/puffish_skills/config.json`(`{"version":3,"categories":["hunting","mining","smithing"]}`), `data/create_rpg/puffish_skills/categories/<cat>/{category,definitions,skills,connections,experience}.json`
  - 게이트 태그: `rpg_hunt_1..3`, `rpg_mine_1..3`, `rpg_smith_1..3` (Task 4, 7에서 사용)
  - `content.SKILL_TREES: dict[str, Tree]`. `Tree`는 `(title, icon_item, nodes: list[Node], xp_values: list[int], sources: list[dict])`이고, `Node`는 `(id, title, description, icon_item, rewards: list[dict], parent: str | None, x, y, cost=1, frame="task")`
  - `gen_skills.generate(root: Path) -> None`

**트리 형태 (모든 트리 공통):** 노드 13개, 레벨 상한 20.
- 루트 1개 → 가지 3개(각 가지 3단계 능력치 노드)
- 게이트 노드 3개: 가지 끝(가지당 3개)과 연결. `frame:"goal"`, `required_spent_points` 3 / 7 / 11. 보상은 `puffish_skills:tag` 하나와 설명 문구("○○ II 해금: …").
- 연결은 `connections.json`의 `{"normal":{"bidirectional":[[a,b],…]}}` 형식
- 경험치 곡선 `xp_values`: `[20, 30, 45, 60, 80, 100, 125, 150, 180, 210, 245, 280, 320, 360, 400, 450, 500, 550, 600, 650]`. `level_limit` 20

**능력치 보상 (노드당 값, operation):**
| 트리 | 가지 A | 가지 B | 가지 C |
|---|---|---|---|
| 사냥 | `generic.attack_damage` +1 (addition) | `generic.max_health` +2 (addition) | `generic.attack_speed` +0.05 (multiply_total) |
| 광질 | `player.block_break_speed` +0.1 (multiply_total) | `generic.luck` +0.5 (addition) | `player.mining_efficiency` +2 (addition) |
| 대장장이 | `generic.armor` +1 (addition) | `generic.armor_toughness` +0.5 (addition) | `generic.knockback_resistance` +0.05 (addition) |

대장장이 게이트 노드는 태그와 함께 `puffish_skills:command`의 `command`(즉시 실행)로 보너스 재료를 지급한다. 게이트 1: `plate_1` ×4, 게이트 2: `plate_2` ×4, 게이트 3: `plate_3` ×4. `give @s <items.material_stack을 give 문법으로 변환>`

**경험치 획득처 (`sources`):**
- 사냥: `puffish_skills:kill_entity`, `experience: "dropped_xp + max_health / 10"`, `anti_farming {limit_per_chunk: 20, reset_after_seconds: 300}`. 위더 +300, 엔더 드래곤 +800은 조건부 항목으로 추가
- 광질: `puffish_skills:mine_block`. 블록 태그 조건 `#c:ores` 8, `#minecraft:base_stone_overworld` 0.2, `minecraft:ancient_debris` 40
- 대장장이: `puffish_skills:craft_item`. 결과물이 아이템 태그 `#create_rpg:smithing_crafts`면 `count * 4`. 태그 파일은 `data/create_rpg/tags/item/smithing_crafts.json`이고 내용은 다음과 같다: `create:cogwheel, create:large_cogwheel, create:shaft, create:andesite_casing, create:brass_casing, create:copper_casing, create:mechanical_press, create:mechanical_mixer, create:deployer, create:basin, create:depot, create:belt_connector, create:millstone, create:crushing_wheel, create:mechanical_crafter, create:spout, create:fluid_tank, create:blaze_burner, create:precision_mechanism, create:electron_tube`. 장비 첫 획득 경험치는 Task 5에서 추가
- `puffish_skills:test`에 태그를 쓰는 문법(`"#c:ores"` 또는 `"tag"` 키)은 참고 문서(`calculations/operations/built-in/test-block.md`, `test-item.md`)대로 따른다.

- [ ] **Step 1: 실패하는 테스트 작성** (`tests/test_skills.py`)
```python
CATS = ["hunting", "mining", "smithing"]

def test_config_lists_three_categories(pack_root):
    cfg = load(pack_root / "data/create_rpg/puffish_skills/config.json")
    assert cfg == {"version": 3, "categories": CATS}

@pytest.mark.parametrize("cat", CATS)
def test_every_skill_uses_existing_definition(pack_root, cat):
    d = cat_dir(pack_root, cat)
    defs, skills = load(d / "definitions.json"), load(d / "skills.json")
    assert len(skills) == 13
    assert all(s["definition"] in defs for s in skills.values())

@pytest.mark.parametrize("cat", CATS)
def test_every_skill_reachable_from_root(pack_root, cat):
    # skills.json의 root에서 connections.json의 bidirectional 쌍을 BFS로 따라가면 13개 모두 방문
    assert reachable(pack_root, cat) == set(load(cat_dir(pack_root, cat) / "skills.json"))

@pytest.mark.parametrize("cat,prefix", [("hunting","rpg_hunt"),("mining","rpg_mine"),("smithing","rpg_smith")])
def test_gate_tags(pack_root, cat, prefix):
    assert granted_tags(pack_root, cat) == {f"{prefix}_{i}" for i in (1, 2, 3)}

@pytest.mark.parametrize("cat", CATS)
def test_experience_curve(pack_root, cat):
    exp = load(cat_dir(pack_root, cat) / "experience.json")
    assert exp["level_limit"] == 20
    assert exp["experience_per_level"]["data"]["values"][0] == 20
    assert exp["sources"]
```
(`cat_dir`, `reachable`, `granted_tags`는 `tests/conftest.py`에 헬퍼로 추가)
- [ ] **Step 2:** `python -m pytest tests/test_skills.py -v` → FAIL
- [ ] **Step 3:** `content.SKILL_TREES`와 `gen_skills.generate` 구현, `build.build`에 연결
- [ ] **Step 4:** `python -m pytest -v` → 전부 PASS
- [ ] **Step 5:** 커밋 `feat: hunting/mining/smithing skill trees`

---

### Task 3: 장비 5단계와 Create 레시피

**Files:**
- Modify: `tools/content.py`(장비·레시피 정의)
- Create: `tools/gen_recipes.py`, `tests/test_recipes.py`, `tests/data/create_items.txt`(Create 1.21.1 아이템 ID 목록. Create 저장소 `src/generated/resources/assets/create/models/item/*.json` 파일 이름에서 추출해 저장)

**Interfaces:**
- Consumes: `items.*`, `content.MATERIALS`
- Produces:
  - `content.GEAR_SLOTS = ["sword","pickaxe","helmet","chestplate","leggings","boots"]`
  - `content.TIERS: list[Tier]`. `Tier`는 `(n: int, key: str, name: str, base_material: str, stats: dict[slot, list[attr_mod]])`
    | n | key | 이름 접두 | 바닐라 바탕 |
    |---|---|---|---|
    | 1 | apprentice | 구리 견습 | iron |
    | 2 | journeyman | 황동 숙련 | iron |
    | 3 | artisan | 강철 장인 | diamond |
    | 4 | arcane | 비전 명장 | diamond |
    | 5 | legend | 전설 | netherite |
  - 장비 RPG ID는 `gear_<key>_<slot>`(예: `gear_artisan_sword`). 이 ID는 Task 5에서 쓴다.
  - 장비 능력치는 바닐라 바탕 아이템 능력치에 **더하는** 보너스다. `minecraft:attribute_modifiers`(`show_in_tooltip: true`)에 바탕 아이템 기본값까지 포함해 쓴다. 단계별 보너스는 검 공격력 +1/+2/+3/+5/+8, 방어구 한 벌 합계 방어력 +2/+4/+6/+9/+12와 체력 0/+2/+4/+6/+10(흉갑에 몰아서), 곡괭이 `player.block_break_speed` +10%/+20%/+30%/+45%/+60%. 세부 배분은 구현자가 정하고 `content.py`에 표로 남긴다.
  - `gen_recipes.generate(root: Path) -> None`. 파일 위치는 `data/create_rpg/recipe/<type>/<name>.json`

**레시피 (전부 Create 타입):**
| 대상 | 타입 | 입력 → 출력 |
|---|---|---|
| 강화 가루 N | `create:crushing` | 광맥 조각 N → 가루 N ×1 (+50% ×1) |
| 강화 합금 N | `create:mixing` | 가루 N ×2 + 정수 N + (철·금·다이아·네더라이트 주괴 중 N번째) → 합금 N. `heat_requirement`: N=1 없음, N=2·3 `heated`, N=4 `superheated` |
| 강화 합금 판 N | `create:pressing` | 합금 N → 판 N |
| 전설 핵 | `create:mixing` (`superheated`) | `minecraft:nether_star` + 정수 IV ×4 + 판 IV ×2 → 전설 핵 ×6 |
| 1단계 장비 | `create:deploying` | 바닐라 철 장비 + `create:copper_sheet` → `gear_apprentice_*` |
| 2단계 장비 | `create:sequenced_assembly` loops 1 | 입력 `gear_apprentice_*` / 단계: deploy 판 I → deploy 정수 I → press |
| 3단계 장비 | `create:sequenced_assembly` loops 2 | 입력 바닐라 다이아 장비 / 단계: deploy 판 II → deploy 정수 II → press |
| 4단계 장비 | `create:sequenced_assembly` loops 3 | 입력 `gear_artisan_*` / 단계: deploy 판 III → filling `minecraft:lava` 250 → deploy 광맥 조각 III → press |
| 5단계 장비 | `create:sequenced_assembly` loops 2 | 입력 바닐라 네더라이트 장비 / 단계: deploy 전설 핵 → deploy 판 IV → filling `minecraft:lava` 500 → press |

- 조립 라인의 `transitional_item`은 `create:incomplete_precision_mechanism`이다(Create 자체 레시피에서 검증된 형식). 각 단계의 첫 재료도 이 아이템이다.
- 입력이 RPG 장비(2, 4단계)일 때는 `rpg_ingredient`를 쓴다.

- [ ] **Step 1: 실패하는 테스트 작성** (`tests/test_recipes.py`)
```python
def test_thirty_gear_items_each_have_one_recipe(pack_root):
    outputs = recipe_output_rpg_ids(pack_root)          # 결과물의 custom_data.create_rpg 모음
    gear = {f"gear_{t}_{s}" for t in TIER_KEYS for s in GEAR_SLOTS}
    assert gear <= set(outputs) and all(outputs.count(g) == 1 for g in gear)

def test_every_consumed_item_is_obtainable(pack_root):
    # 레시피 재료로 쓰인 모든 rpg id는 (레시피 결과물 ∪ 루트 수정자 테이블이 주는 것 ∪ 스킬 give 보상)에 있어야 함
    assert consumed_rpg_ids(pack_root) <= obtainable_rpg_ids(pack_root)

def test_create_item_ids_exist(pack_root):
    known = set((DATA / "create_items.txt").read_text().split())
    assert {i for i in all_item_ids(pack_root) if i.startswith("create:")} <= known

def test_heat_requirements(pack_root):
    assert heat_of(pack_root, "alloy_1") is None
    assert heat_of(pack_root, "alloy_2") == heat_of(pack_root, "alloy_3") == "heated"
    assert heat_of(pack_root, "alloy_4") == heat_of(pack_root, "legend_core") == "superheated"

def test_sequenced_assembly_shape(pack_root):
    r = load(pack_root / "data/create_rpg/recipe/sequenced_assembly/gear_arcane_sword.json")
    assert r["loops"] == 3 and r["transitional_item"]["id"] == "create:incomplete_precision_mechanism"
    assert [s["type"] for s in r["sequence"]] == ["create:deploying","create:filling","create:deploying","create:pressing"]

def test_legend_gear_has_custom_name_and_attributes(pack_root):
    res = load(pack_root / "data/create_rpg/recipe/sequenced_assembly/gear_legend_sword.json")["results"][0]
    assert res["id"] == "minecraft:netherite_sword"
    assert "전설" in res["components"]["minecraft:custom_name"]
    assert res["components"]["minecraft:attribute_modifiers"]["modifiers"]
```
(`obtainable_rpg_ids`는 Task 4 전에는 루트 데이터가 없으므로 이 테스트가 실패해도 된다. Task 4 Step 4에서 통과해야 한다. 이 Task의 Step 4에서는 이 테스트를 제외하고 실행한다.)
- [ ] **Step 2:** `python -m pytest tests/test_recipes.py -v` → FAIL
- [ ] **Step 3:** `content.TIERS`, 레시피 표, `gen_recipes.generate` 구현
- [ ] **Step 4:** `python -m pytest tests/test_recipes.py -v -k "not obtainable"` → PASS
- [ ] **Step 5:** 커밋 `feat: five gear tiers via Create processing`

---

### Task 4: 몬스터·광석 드롭 (레벨 태그로 해금)

**Files:**
- Create: `tools/gen_loot.py`, `tests/test_loot.py`
- Modify: `tools/content.py`(드롭 표)

**Interfaces:**
- Consumes: `items.material_stack`, 게이트 태그(Task 2)
- Produces: `data/create_rpg/loot_table/drops/<name>.json`(아이템을 주는 테이블), `data/create_rpg/loot_modifiers/<name>.json`(`type: "neoforge:add_table"`, `conditions`, `table`), `data/neoforge/loot_modifiers/global_loot_modifiers.json`(`{"replace": false, "entries": [...]}`), 엔티티 타입 태그 `data/create_rpg/tags/entity_type/{overworld_monsters,nether_monsters,end_monsters}.json`

**드롭 표:**
| 재료 | 출처 | 조건 태그 | 확률 |
|---|---|---|---|
| 정수 I | `#create_rpg:overworld_monsters` | 없음 | 0.30 |
| 정수 II | `#create_rpg:overworld_monsters` | `rpg_hunt_1` | 0.15 |
| 정수 III | `#create_rpg:nether_monsters` | `rpg_hunt_2` | 0.25 |
| 정수 IV | `#create_rpg:end_monsters` + 엔드 차원 | `rpg_hunt_3` | 0.20 |
| 정수 IV ×8 | `minecraft:wither` | 없음 | 1.0 |
| 조각 I | 석탄·구리·철 광석(심층암 포함) | 없음 | 0.35 |
| 조각 II | 금·레드스톤·청금석 광석(심층암 포함) | `rpg_mine_1` | 0.30 |
| 조각 III | 네더 금 광석, 네더 석영 광석, 고대 잔해 | `rpg_mine_2` | 0.30 (고대 잔해 1.0) |
| 조각 IV | 다이아몬드·에메랄드 광석(심층암 포함), 고대 잔해 | `rpg_mine_3` | 0.40 (고대 잔해 1.0) |

- 몬스터: `minecraft:killed_by_player` + `minecraft:entity_properties`(entity `this`, type 태그) + 태그 조건은 entity `attacking_player`, predicate `{"nbt": "{Tags:[\"rpg_hunt_N\"]}"}`
- 광석: `neoforge:loot_table_id` 조건들을 `minecraft:any_of`로 묶음 + 태그 조건은 entity `this`(부순 플레이어) + `minecraft:match_tool`로 섬세한 손길이 아닐 때만
- 엔티티 태그 내용. overworld: zombie, husk, drowned, skeleton, stray, spider, cave_spider, creeper, witch, slime, pillager, vindicator, zombie_villager, phantom, bogged. nether: blaze, wither_skeleton, piglin_brute, ghast, magma_cube, hoglin, zombified_piglin. end: enderman, shulker, endermite

- [ ] **Step 1: 실패하는 테스트 작성** (`tests/test_loot.py`)
```python
def test_global_modifier_list_matches_files(pack_root):
    glm = load(pack_root / "data/neoforge/loot_modifiers/global_loot_modifiers.json")
    assert glm["replace"] is False
    files = {f"create_rpg:{p.stem}" for p in (pack_root / "data/create_rpg/loot_modifiers").glob("*.json")}
    assert set(glm["entries"]) == files and len(files) == 9

def test_modifier_tables_exist(pack_root):
    for m in modifiers(pack_root):
        assert m["type"] == "neoforge:add_table"
        assert table_path(pack_root, m["table"]).exists()

def test_loot_gate_tags_are_granted_by_skills(pack_root):
    assert tags_required_by_loot(pack_root) <= all_granted_tags(pack_root)
    assert tags_required_by_loot(pack_root) == {"rpg_hunt_1","rpg_hunt_2","rpg_hunt_3","rpg_mine_1","rpg_mine_2","rpg_mine_3"}

def test_no_vanilla_loot_table_overrides(pack_root):
    assert not (pack_root / "data/minecraft/loot_table").exists()
```
- [ ] **Step 2:** `python -m pytest tests/test_loot.py -v` → FAIL
- [ ] **Step 3:** `gen_loot.generate` 구현. `conftest.obtainable_rpg_ids`가 드롭 테이블과 스킬 `give` 보상을 읽도록 완성
- [ ] **Step 4:** `python -m pytest -v` → 전부 PASS (Task 3의 `test_every_consumed_item_is_obtainable` 포함)
- [ ] **Step 5:** 커밋 `feat: level-gated mob and ore drops via global loot modifiers`

---

### Task 5: 장비 첫 획득 → 대장장이 경험치

**Files:**
- Create: `tools/gen_smithing.py`, `tests/test_smithing.py`

**Interfaces:**
- Consumes: `content.TIERS`, `content.GEAR_SLOTS`, 장비 RPG ID(Task 3)
- Produces: 
  - 도전 과제 `data/create_rpg/advancement/forge/root.json`(보이는 루트, 제목 "대장간", 트리거 `minecraft:tick`) 그리고 `data/create_rpg/advancement/forge/<gear_id>.json` 30개. 트리거는 `minecraft:inventory_changed`, `items: [{"items": "<바탕 아이템>", "predicates": {"minecraft:custom_data": "{create_rpg:\"<gear_id>\"}"}}]`, `rewards.function`은 `create_rpg:forge/<gear_id>`, 제목은 장비 이름, `announce_to_chat: true`
  - 함수 `data/create_rpg/function/forge/<gear_id>.mcfunction`의 내용은 한 줄: `puffish_skills experience add @s create_rpg:smithing <tier.n * 40>`
  - 카테고리 ID는 `create_rpg:smithing`으로 가정한다. 게임 안에서 탭 자동완성으로 확인하는 항목을 INSTALL 체크리스트(Task 6)에 넣는다.

- [ ] **Step 1: 실패하는 테스트 작성**
```python
def test_thirty_forge_advancements(pack_root):
    advs = list((pack_root / "data/create_rpg/advancement/forge").glob("gear_*.json"))
    assert len(advs) == 30

def test_advancement_rewards_point_to_existing_functions(pack_root):
    for adv in (pack_root / "data/create_rpg/advancement").rglob("*.json"):
        fn = load(adv).get("rewards", {}).get("function")
        if fn:
            ns, path = fn.split(":")
            assert (pack_root / f"data/{ns}/function/{path}.mcfunction").exists()

def test_forge_xp_scales_with_tier(pack_root):
    line = (pack_root / "data/create_rpg/function/forge/gear_legend_sword.mcfunction").read_text().strip()
    assert line == "puffish_skills experience add @s create_rpg:smithing 200"

def test_criterion_matches_gear_custom_data(pack_root):
    adv = load(pack_root / "data/create_rpg/advancement/forge/gear_artisan_helmet.json")
    pred = adv["criteria"]["forged"]["conditions"]["items"][0]
    assert pred["items"] == "minecraft:diamond_helmet"
    assert "gear_artisan_helmet" in pred["predicates"]["minecraft:custom_data"]
```
- [ ] **Step 2:** `python -m pytest tests/test_smithing.py -v` → FAIL
- [ ] **Step 3:** `gen_smithing.generate` 구현
- [ ] **Step 4:** `python -m pytest -v` → 전부 PASS
- [ ] **Step 5:** 커밋 `feat: smithing xp on first forge of each gear`

---

### Task 6: zip 빌드와 Aternos 설치 안내서

**Files:**
- Modify: `tools/build.py`(zip 생성)
- Create: `INSTALL.md`, `tests/test_zip.py`

**Interfaces:**
- Consumes: `build.build`
- Produces: `build/create_rpg.zip`, `INSTALL.md`

`INSTALL.md`에 들어갈 내용 (한국어):
1. Aternos 서버를 1.21.1 NeoForge로 설정하고, 모드에서 Create(6.0.3 이상)와 Pufferfish's Skills를 설치
2. 월드를 한 번 생성하고 서버를 끈 다음, 파일 메뉴의 `world/datapacks/`에 `create_rpg.zip`을 업로드하고 다시 시작
3. 확인 체크리스트(게임 안에서 확인, 각 항목에 확인 명령어 포함):
   - `/datapack list`에 `file/create_rpg.zip`이 보이는지
   - 스킬 화면(기본 단축키 K)에 사냥, 광질, 대장장이 탭이 있는지
   - `/puffish_skills experience add @s ` 뒤에서 탭 자동완성으로 카테고리 ID가 `create_rpg:smithing` 형식인지 (아니면 알려 달라는 문구)
   - 좀비를 잡으면 가끔 "몬스터 정수 I"이 떨어지는지
   - `/give`로 철 검과 구리 판을 받아 배포기(Deployer)로 1단계 검이 만들어지는지, 그리고 처음 만들었을 때 대장간 도전 과제가 뜨는지
   - JEI가 있다면 `create_rpg` 레시피가 보이는지 (선택)
   - `/tag @s add rpg_hunt_1` 후 좀비 사냥으로 정수 II가 나오는지
4. 문제가 생겼을 때: 서버 로그에서 `create_rpg`를 검색해 오류 줄을 복사해 달라는 안내
5. 진행 가이드: 단계별로 필요한 재료와 기계를 요약한 표 (`content.py`에서 생성하지 말고 손으로 작성)

- [ ] **Step 1: 실패하는 테스트 작성**
```python
def test_zip_has_pack_mcmeta_at_root(pack_zip):
    with zipfile.ZipFile(pack_zip) as z:
        names = z.namelist()
    assert "pack.mcmeta" in names
    assert all(n == "pack.mcmeta" or n.startswith("data/") for n in names)

def test_zip_json_all_parse(pack_zip):
    with zipfile.ZipFile(pack_zip) as z:
        for n in z.namelist():
            if n.endswith(".json") or n.endswith(".mcmeta"):
                json.loads(z.read(n).decode("utf-8"))
```
- [ ] **Step 2:** `python -m pytest tests/test_zip.py -v` → FAIL
- [ ] **Step 3:** `build.py`에 zip 생성 추가(UTF-8, 슬래시 경로), `python -m tools.build` 실행 시 zip 경로 출력. `INSTALL.md` 작성
- [ ] **Step 4:** `python -m pytest -v` → 전부 PASS, `python -m tools.build` → `build/create_rpg.zip` 출력
- [ ] **Step 5:** 커밋 `feat: zip build and Aternos install guide`
