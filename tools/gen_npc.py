"""NPC dialogue: right-click (player_interacted_with_entity) -> chat lines, chief help menu, starter kit."""
import json
from pathlib import Path

from tools.build import write_json, write_text
from tools.content_village import NPCS, QUESTS, STARTER_KIT, resolve
from tools.items import give_stack_command

NS = "create_rpg"
NPC = {n.id: n for n in NPCS}


def say(npc_id, *parts, cond=""):
    n = NPC[npc_id]
    body = [{"text": f"[{n.name}] ", "color": n.color}]
    body += [{"text": p, "color": "white"} if isinstance(p, str) else p for p in parts]
    pre = f"execute {cond} run " if cond else ""
    return pre + "tellraw @s " + json.dumps(body, ensure_ascii=False)


def button(label, fn, color="aqua"):
    return {"text": f"[{label}] ", "color": color,
            "clickEvent": {"action": "run_command", "value": f"/function {NS}:{fn}"},
            "hoverEvent": {"action": "show_text", "contents": "클릭해서 듣기"}}


HELP = {
    "levels": ("레벨과 스킬", [
        "사냥은 몬스터를, 광질은 광석을, 대장장이는 Create 부품 제작과 장비 첫 완성으로 레벨이 오른다네.",
        "레벨이 오를 때마다 스킬 포인트 1개! K키로 스킬 화면을 열어 찍으면 되지.",
        "둥근 테두리의 해금 노드(3포인트)는 그 트리에 3·7·11포인트를 쓴 뒤 찍을 수 있고, 상위 재료가 나오기 시작한다네."]),
    "gear": ("장비 단계", [
        "장비는 5단계일세: 구리 견습 → 황동 숙련 → 강철 장인 → 비전 명장 → 전설.",
        "1단계는 배포기로 철 장비에 구리 판을 대면 되고, 2단계부터는 순차 조립 라인(벨트 위 배포기·주입기·압착기)이 필요하다네.",
        "1~3단계는 지상에서, 4~5단계 재료는 네더와 엔드에서 구하게."]),
    "enhance": ("강화", [
        "강화할 장비를 왼손(F키)에 들고 강화 주문서를 마시면 +1이 된다네. 실패는 없네.",
        "하급 +1~3, 중급 +4~5, 상급 +6~7, 최상급 +8~10. 대장장이 해금 노드를 찍을수록 상한이 +5, +7, +10으로 오르지.",
        "조심하게! 장비 단계를 올리면 새 장비가 나와서 강화가 사라진다네. 마지막에 쓸 장비에 강화하게."]),
    "materials": ("재료 만들기", [
        "광맥 조각을 분쇄 바퀴로 갈면 강화 가루가 된다네.",
        "가루 2개 + 몬스터 정수 + 주괴를 혼합기에 넣으면 강화 합금, 압착기로 누르면 강화 합금 판이지.",
        "판 + 정수 + 종이를 혼합기에 넣으면 강화 주문서 2장이 나온다네."]),
    "luck": ("행운과 드롭", [
        "몬스터는 몬스터 정수를, 광석은 광맥 조각을 떨어뜨린다네. 섬세한 손길로 캐면 조각이 안 나오니 주의하게.",
        "광질 트리의 행운 노드를 찍으면 광석을 캘 때 원래 드롭이 하나 더 나올 확률이 5·10·15%로 오른다네."]),
    "quests": ("의뢰", [
        "의뢰소의 한나에게 가면 지금 맡은 의뢰와 진행 상황을 알려 줄 걸세. 목표를 채우면 자동으로 완료되지.",
        "몬스터 정수가 남으면 한나에게 납품해서 에메랄드로 바꾸게. 에메랄드로 브론과 미로에게 물건을 살 수 있다네."]),
    "home": ("귀환", [
        "귀환 주문서를 마시면 언제든 이 광장으로 돌아온다네. 미로가 팔고 있지.",
        "명령어로는 /function create_rpg:home 이라네."]),
}


def chief_files(f: Path):
    write_text(f / "npc" / "chief" / "talk.mcfunction", "\n".join([
        f"advancement revoke @s only {NS}:npc/talk_chief",
        f"execute if entity @s[tag=rpg_started] run function {NS}:npc/chief/menu",
        f"execute unless entity @s[tag=rpg_started] run function {NS}:npc/chief/intro"]) + "\n")
    intro = [
        say("chief", "어서 오게, 여행자여! 여기는 톱니와 모루의 마을일세."),
        say("chief", "몬스터를 사냥하고 광석을 캐며 실력을 키우고, Create 기계로 장비를 단련하는 곳이지."),
        say("chief", "빈손으로 보낼 순 없지. 이걸 받게. 시작에 필요한 것들일세."),
    ]
    intro += [give_stack_command(*resolve(spec), n) for spec, n in STARTER_KIT]
    intro += [
        "tag @s add rpg_started",
        f"advancement grant @s only {NS}:quest/root",
        f"scoreboard players set @s {QUESTS[0].objective} 0",
        say("chief", "첫 의뢰가 열렸네. 동쪽 의뢰소의 ", {"text": "한나", "color": "aqua"}, "에게 가 보게. "
            "북쪽엔 대장간, 서쪽엔 상점이 있다네. 궁금한 게 있으면 언제든 내게 다시 말을 걸게."),
        "playsound minecraft:entity.player.levelup player @s",
    ]
    write_text(f / "npc" / "chief" / "intro.mcfunction", "\n".join(intro) + "\n")
    topics = list(HELP) + ["next"]
    labels = {k: v[0] for k, v in HELP.items()} | {"next": "지금 뭘 해야 하지?"}
    row1 = [button(labels[t], f"npc/chief/help/{t}") for t in topics[:4]]
    row2 = [button(labels[t], f"npc/chief/help/{t}", "gold" if t == "next" else "aqua") for t in topics[4:]]
    write_text(f / "npc" / "chief" / "menu.mcfunction", "\n".join([
        say("chief", "무엇이 궁금한가? 아래에서 골라 보게."),
        "tellraw @s " + json.dumps([{"text": " "}] + row1, ensure_ascii=False),
        "tellraw @s " + json.dumps([{"text": " "}] + row2, ensure_ascii=False)]) + "\n")
    for key, (title, lines) in HELP.items():
        write_text(f / "npc" / "chief" / "help" / f"{key}.mcfunction",
                   "\n".join([f"tellraw @s " + json.dumps({"text": f"── {title} ──", "color": "gold"}, ensure_ascii=False)]
                             + [say("chief", l) for l in lines]) + "\n")
    nxt = ["scoreboard players set #done rpg_tmp 0"]
    for q in QUESTS:
        nxt.append(f"execute if score #done rpg_tmp matches 0 if entity @s[advancements={{{NS}:quest/{q.id}=false}}] "
                   f"run function {NS}:npc/chief/hint/{q.id}")
        write_text(f / "npc" / "chief" / "hint" / f"{q.id}.mcfunction", "\n".join([
            say("chief", {"text": f"[{q.phase}] {q.title}: ", "color": "yellow"}, q.hint),
            "scoreboard players set #done rpg_tmp 1"]) + "\n")
    nxt.append(say("chief", "모든 의뢰를 끝냈군! 자네는 이 마을의 영웅일세. 이제 마음껏 강화하고 탐험하게.",
                   cond="if score #done rpg_tmp matches 0"))
    write_text(f / "npc" / "chief" / "help" / "next.mcfunction", "\n".join(nxt) + "\n")


def smith_files(f: Path):
    write_text(f / "npc" / "smith" / "talk.mcfunction", "\n".join([
        f"advancement revoke @s only {NS}:npc/talk_smith",
        say("smith", "오, 손님인가! 망치 소리가 좀 시끄럽지?"),
        say("smith", "지금 자네 솜씨로는 +3까지 강화할 수 있겠군. 대장장이 레벨을 올리면 더 높이 갈 수 있다네.",
            cond="if entity @s[tag=!rpg_smith_1]"),
        say("smith", "숙련 대장장이로군. +5까지 강화할 수 있겠어.", cond="if entity @s[tag=rpg_smith_1,tag=!rpg_smith_2]"),
        say("smith", "장인의 손이야! +7까지는 문제없지.", cond="if entity @s[tag=rpg_smith_2,tag=!rpg_smith_3]"),
        say("smith", "명장이 왔군! +10까지 마음껏 강화하게.", cond="if entity @s[tag=rpg_smith_3]"),
        say("smith", "강화할 장비를 왼손에 들고 주문서를 마시게. 판과 주문서는 에메랄드로 팔고 있다네.")]) + "\n")


def guild_files(f: Path):
    L = [f"advancement revoke @s only {NS}:npc/talk_guild",
         say("guild", "의뢰소에 온 걸 환영해요! 먼저 광장의 촌장님께 인사드리고 오세요.", cond="if entity @s[tag=!rpg_started]"),
         f"execute if entity @s[tag=!rpg_started] run return 0",
         "scoreboard players set #done rpg_tmp 0"]
    for q in QUESTS:
        L.append(f"execute if score #done rpg_tmp matches 0 if entity @s[advancements={{{NS}:quest/{q.id}=false}}] "
                 f"run function {NS}:npc/guild/current/{q.id}")
        progress = [] if q.kind == "forge" else [
            {"text": " (진행: ", "color": "gray"}, {"score": {"name": "@s", "objective": q.objective}, "color": "gray"},
            {"text": f"/{q.count})", "color": "gray"}]
        write_text(f / "npc" / "guild" / "current" / f"{q.id}.mcfunction", "\n".join([
            say("guild", "지금 맡은 의뢰는 ", {"text": f"「{q.title}」", "color": "yellow"}, f" — {q.goal}", *progress),
            "scoreboard players set #done rpg_tmp 1"]) + "\n")
    L += [say("guild", "의뢰를 전부 끝내셨네요! 정말 대단해요.", cond="if score #done rpg_tmp matches 0"),
          say("guild", "몬스터 정수가 남으면 저한테 납품하세요. 에메랄드로 바꿔 드릴게요.")]
    write_text(f / "npc" / "guild" / "talk.mcfunction", "\n".join(L) + "\n")


def merchant_files(f: Path):
    write_text(f / "npc" / "merchant" / "talk.mcfunction", "\n".join([
        f"advancement revoke @s only {NS}:npc/talk_merchant",
        say("merchant", "어서 와요! 빵, 횃불, 아연까지 다 있어요."),
        say("merchant", "멀리 나갈 땐 귀환 주문서를 꼭 챙겨요. 마시면 여기로 바로 돌아온다고요!")]) + "\n")


def generate(root: Path) -> None:
    d = root / "data" / NS
    f = d / "function"
    for n in NPCS:
        write_json(d / "advancement" / "npc" / f"talk_{n.id}.json", {
            "criteria": {"talk": {"trigger": "minecraft:player_interacted_with_entity", "conditions": {"entity": [
                {"condition": "minecraft:entity_properties", "entity": "this",
                 "predicate": {"nbt": '{Tags:["rpg_npc_%s"]}' % n.id}}]}}},
            "rewards": {"function": f"{NS}:npc/{n.id}/talk"}})
    chief_files(f)
    smith_files(f)
    guild_files(f)
    merchant_files(f)
