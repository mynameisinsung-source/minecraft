# 강화 · 행운 · 네더 시기 조정 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** design.md §9를 구현한다. 가열 공정은 4단계 재료부터 필요하게 하고, +1~+10 강화 주문서 시스템과 행운 추가 드롭을 넣는다.

**Architecture:** 기존 생성기에 `tools/gen_enhance.py`를 새로 추가한다. 주문서는 마시는 `minecraft:potion` 아이템이다. 마시면 `consume_item` 도전 과제가 발동하고, 보상 함수가 왼손 장비의 단계와 강화 수치를 `execute if items`로 판별한 뒤 `item modify`로 강화한다. 행운은 `gen_loot.py`에 전역 루트 수정자 3개를 추가해서 구현한다.

**Tech Stack:** 기존과 동일 (Python 생성기 + pytest, 1.21.1 데이터팩).

**Spec:** `docs/design.md` §9

## Global Constraints
- 기존 계획(`docs/plans/2026-11-23-create-rpg.md`)의 Global Constraints를 모두 따른다. 특히 **틱 함수 금지**. 단, `#minecraft:load`는 허용한다(로드할 때 한 번만 실행).
- 강화 수치는 장비 `custom_data`의 `rpg_enh` 키에 **문자열** `"1"`~`"10"`으로 저장한다(JSON 숫자는 NBT 타입이 모호해서 피한다).
- 강화 modifier ID는 `create_rpg:enhance`(누적값 하나로 덮어씀)와 `create_rpg:enhance_bonus`(+10 체력)다.
- 주문서 ID와 허용 범위: `scroll_low`는 1~3, `scroll_mid`는 4~5, `scroll_high`는 6~7, `scroll_top`은 8~10. 대장장이 상한: 태그 없음 3, `rpg_smith_1` 5, `rpg_smith_2` 7, `rpg_smith_3` 10.

## Review Focus
1. **장비를 왼손 대신 오른손에 든 경우:** 주문서만 날아가면 안 된다. 주문서를 돌려주고 안내해야 한다. → `test_failure_paths_refund_scroll`
2. **이미 +10인 장비:** 더 강화되거나 주문서를 잃으면 안 된다. → `test_max_level_refunds`
3. **상한보다 높은 주문서 사용:** 예를 들어 태그 없이 +3인 장비에 중급 주문서를 쓰면 거절하고 주문서를 돌려줘야 한다. → `test_cap_checks_use_smith_tags`
4. **도전 과제 해제 누락:** 해제하지 않으면 두 번째 주문서부터 아무 일도 일어나지 않는다. → `test_scroll_functions_revoke_their_advancement`
5. **행운 단계 중복 적용:** 행운 III이면 15%만 적용되어야 하고, 5%·10%·15%가 겹치면 안 된다. → `test_luck_levels_are_exclusive`

---

### Task 7: 가열 시기 조정 + 행운 추가 드롭
**Files:** Modify `tools/content.py`(ALLOY_HEAT, 광질 가지 B, LUCK_DROPS), `tools/gen_loot.py`; Test `tests/test_recipes.py`, `tests/test_loot.py`, `tests/test_skills.py`
**Interfaces:** Produces tags `rpg_luck_1..3`(광질 가지 B 노드 1~3의 보상, 능력치 대신), loot modifiers `create_rpg:luck_1..3`

- `ALLOY_HEAT = {1: None, 2: None, 3: "heated", 4: "superheated"}`
- 광질 가지 B: 이름 "행운", 노드 `n`의 보상은 `tag_reward(f"rpg_luck_{n}")`, 설명은 "광석 추가 드롭 확률 5%/10%/15%"
- `LUCK_DROPS`: (광석 블록 → 추가 아이템) 석탄→coal, 구리→raw_copper, 철→raw_iron, 금→raw_gold, 레드스톤→redstone, 청금석→lapis_lazuli, 다이아→diamond, 에메랄드→emerald(이상 심층암 포함), nether_quartz_ore→quartz, nether_gold_ore→gold_nugget. 확률은 `{1: 0.05, 2: 0.10, 3: 0.15}`
- 수정자 `luck_n`의 조건: 광석 테이블 `any_of` + 섬세한 손길 제외 + `rpg_luck_n` 있음 + (n<3이면) `rpg_luck_{n+1}` 없음. 테이블: 블록마다 풀 하나(`block_state_property` + `random_chance`)

- [ ] **Step 1: 테스트 수정·추가**
```python
# test_recipes.py
def test_heat_requirements(pack_root):
    assert heat_of(pack_root, "alloy_1") is None and heat_of(pack_root, "alloy_2") is None
    assert heat_of(pack_root, "alloy_3") == "heated"
    assert heat_of(pack_root, "alloy_4") == heat_of(pack_root, "legend_core") == "superheated"
# test_loot.py: 수정자 개수 9 → 12, tags_required 집합에 rpg_luck_1..3 추가
def test_luck_levels_are_exclusive(pack_root): ...  # luck_1은 rpg_luck_2 없음 조건, luck_2는 rpg_luck_3 없음 조건, luck_3은 제외 조건 없음
def test_luck_tables_give_vanilla_drop(pack_root): ...  # luck_3 테이블에 minecraft:diamond 항목이 있고 확률 0.15
# test_skills.py
def test_mining_luck_nodes_grant_tags(pack_root): ...  # 광질 트리 태그 = rpg_mine_1..3 ∪ rpg_luck_1..3
```
(기존 `test_gate_tags`는 해금 노드의 태그만 비교하도록 조정)
- [ ] **Step 2:** `python3 -m pytest -q` → 새 테스트 FAIL
- [ ] **Step 3:** 구현
- [ ] **Step 4:** `python3 -m pytest -q` → 전부 PASS
- [ ] **Step 5:** 커밋 `feat: nether-free mid game heat, luck extra drops`

### Task 8: 강화 주문서 시스템
**Files:** Create `tools/gen_enhance.py`, `tests/test_enhance.py`; Modify `tools/content.py`(SCROLLS, ENH_*), `tools/gen_recipes.py`(장비 custom_data에 `rpg_gear:"1"` 추가, 주문서 혼합 레시피), `tools/build.py`
**Interfaces:**
- Consumes: `TIERS`, `GEAR_SLOTS`, `gear_id`, `gear_modifiers`, `rpg_components`, 대장장이 태그
- Produces:
  - 주문서 결과물(`minecraft:potion`, `potion_contents` 물 + `custom_color`, `max_stack_size` 16)
  - 도전 과제 `create_rpg:enhance/drink_<grade>`(트리거 `consume_item`, 보상 함수 `create_rpg:enhance/use_<grade>`)
  - 함수 `create_rpg:load`(`scoreboard objectives add rpg_tmp dummy`)와 `data/minecraft/tags/function/load.json`
  - 아이템 수정자 `create_rpg:enhance/<gear_id>_<k>`(k=1..10): `set_custom_data`(`{rpg_enh:"k"}`), `set_attributes`(replace false, 누적값, k=10이면 bonus 체력 +2), `set_name`(`"<장비 이름> +k"`, 단계 색상)
- 강화량: 검 `generic.attack_damage` k, 곡괭이 `player.block_break_speed` 0.05k(add_multiplied_base), 방어구 `generic.armor` 0.5k (해당 부위 슬롯)
- 함수 `use_<grade>` 흐름: 도전 과제 해제 → 왼손 RPG 장비가 없으면 실패 → 현재 수치를 `#lvl rpg_tmp`에 넣음 → 상한을 `#cap`에 넣음 → 목표(lvl+1)가 주문서 범위 밖이거나 상한을 넘으면 실패 → 장비 ID 30개 × 목표 수치 중 맞는 수정자 적용 → 성공 소리와 메시지. 실패하면 `give`로 주문서를 돌려주고 이유를 `tellraw`로 알림. 실패 여부는 `#ok rpg_tmp`로 관리.
- 주문서 레시피: `create:mixing`, 판 N + 정수 N + `minecraft:paper` → 주문서 ×2. 열: low/mid 없음, high 가열, top 초가열

- [ ] **Step 1: 테스트 작성** (`tests/test_enhance.py`)
  - `test_four_scroll_recipes_and_heat` (주문서 4종, 결과물 count 2, 열 조건)
  - `test_scroll_functions_revoke_their_advancement`
  - `test_failure_paths_refund_scroll` (함수에 `give @s minecraft:potion[...scroll_<grade>...]`가 실패 분기에 있음)
  - `test_max_level_refunds` (scroll_top의 허용 범위 상한이 10이고, 목표 11은 수정자가 없음)
  - `test_cap_checks_use_smith_tags` (함수에 `tag=rpg_smith_1/2/3`과 상한 5/7/10이 있음)
  - `test_modifier_files_for_every_gear_and_level` (300개 존재, `+10` 파일에만 `enhance_bonus`)
  - `test_enhance_amounts` (예: `gear_legend_sword_7`의 attack_damage 7, `gear_artisan_helmet_4`의 armor 2.0 head, `gear_apprentice_pickaxe_10`의 0.5)
  - `test_gear_marked_enhanceable` (모든 장비 결과물의 custom_data에 `rpg_gear:"1"`)
  - `test_load_tag_only` (load 태그는 있고 tick 태그는 없음)
- [ ] **Step 2:** FAIL 확인
- [ ] **Step 3:** 구현
- [ ] **Step 4:** `python3 -m pytest -q` → 전부 PASS
- [ ] **Step 5:** 커밋 `feat: +1..+10 enhancement scrolls gated by smithing level`

### Task 9: 안내서 갱신
**Files:** Modify `INSTALL.md`
- 열 조건 줄, 강화 시스템 절(사용법, 주문서 표, 상한, 단계를 올리면 강화가 초기화된다는 주의), 행운 설명, 체크리스트 항목 추가(주문서 강화와 실패 시 반환 확인, `/tag @s add rpg_smith_1`로 상한 확인)
- [ ] `python3 -m pytest -q` PASS, `python3 -m tools.build`로 zip 생성 후 커밋 `docs: guide for enhancement and luck`
