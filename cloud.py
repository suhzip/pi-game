"""구름 생성, 이동, 착지, 소멸 및 이미지 관리."""
import random
from pathlib import Path
from functools import lru_cache
from PIL import Image
from config import (
    W, H, CLOUD_SPEED, CLOUD_GAP, STAGE_TARGETS, FINAL_HEIGHT, GOAL_CLOUD_WIDTH,
    START_PLATFORM_Y, STORM_CHANCE, LANDING_OFFSET, JUMP_POWER
)
from player import take_damage

ASSET_DIR = Path(__file__).resolve().parent / "assets"
CLOUD_WIDTH = 58
CLOUD_IMAGES = {"normal": "cloud_normal.png", "storm": "cloud_storm.png"}

# 스테이지별 세로 간격, 가로 이동 거리, 움직임 범위, 속도
ROW_RULES = {
    1: (CLOUD_GAP, CLOUD_GAP + 2, 58, 120, 16, CLOUD_SPEED),
    2: (CLOUD_GAP - 2, CLOUD_GAP + 2, 66, 125, 22, CLOUD_SPEED + 6),
    3: (CLOUD_GAP - 1, CLOUD_GAP + 3, 74, 130, 26, CLOUD_SPEED + 12)
}


def cloud_stage(y):
    altitude = START_PLATFORM_Y - y
    return 3 if altitude >= STAGE_TARGETS[2] else 2 if altitude >= STAGE_TARGETS[1] else 1


def make_cloud(x, y, moving=True, kind="normal", bounds=(34, W - 34)):
    speed = ROW_RULES[cloud_stage(y)][5]
    return {
        "x": float(x), "y": float(y), "w": CLOUD_WIDTH,
        "vx": random.choice((-1, 1)) * speed if moving else 0.0,
        "kind": kind, "bounds": bounds
    }


@lru_cache(maxsize=2)
def load_cloud_image(kind):
    with Image.open(ASSET_DIR / CLOUD_IMAGES[kind]) as image:
        return image.convert("RGBA")


@lru_cache(maxsize=8)
def cloud_sprite(kind, width):
    sprite = load_cloud_image(kind)
    height = max(1, round(sprite.height * width / sprite.width))
    return sprite.resize((width, height), Image.Resampling.NEAREST)


def should_add_storm(game, stage):
    if stage == 1:
        return False
    if game.last_storm_row is None:
        return True
    distance = game.cloud_row_index - game.last_storm_row
    if distance < 3:
        return False
    max_distance = 5 if stage == 2 else 4
    chance = STORM_CHANCE if stage == 2 else 0.50
    return distance >= max_distance or random.random() < chance


# 두 칸 전 구름의 중심 거리 및 이동 구역 사이 최소 간격
# (중심 거리, 이동 구역 간격)
TWO_ROW_RULES = {1: (72, 40), 2: (76, 44), 3: (80, 48)}
MIN_TRAVEL_WIDTH = 12


def safe_bounds(x, stage, storm):
    travel = ROW_RULES[stage][4]
    lo, hi = 34, W - 34
    if storm:
        lo, hi = (34, 82) if x <= W / 2 else (W - 82, W - 34)
    return max(lo, x - travel), min(hi, x + travel)


def choose_safe_x(game, stage, storm):
    """직전 층뿐 아니라 두 층 전 구름과도 다른 위치를 선택한다."""
    min_dx, max_dx = ROW_RULES[stage][2:4]
    min_two_dx, min_zone_gap = TWO_ROW_RULES[stage]
    older = game.safe_row_history[-2] if len(game.safe_row_history) >= 2 else None
    candidates = []
    for x in range(34, W - 33):
        if storm and not (x <= 82 or x >= W - 82):
            continue
        lo, hi = safe_bounds(x, stage, storm)
        if older is not None:
            old_x, old_bounds = older
            if abs(x - old_x) < min_two_dx:
                continue
            # 두 칸 전 구름의 이동 구역과 새 구름 이동 구역을 분리한다.
            if x < old_x:
                hi = min(hi, old_bounds[0] - min_zone_gap)
            else:
                lo = max(lo, old_bounds[1] + min_zone_gap)
        if not (lo <= x <= hi) or hi - lo < MIN_TRAVEL_WIDTH:
            continue
        candidates.append((x, (lo, hi)))

    # 두 칸 간격을 우선한다. 한 칸 간격은 가능할 때만 기존 범위를 유지.
    preferred = [c for c in candidates if min_dx <= abs(c[0] - game.next_x) <= max_dx]
    if not preferred:
        preferred = [c for c in candidates if 32 <= abs(c[0] - game.next_x) <= 155]
    if not preferred:
        preferred = [c for c in candidates if abs(c[0] - game.next_x) <= 165]
    pool = preferred or candidates
    # 잘못된 설정은 명확한 오류로 알린다.
    if not pool:
        raise ValueError("No valid cloud position: check TWO_ROW_RULES and ROW_RULES")
    # 후보 중 넓은 이동 범위와 직전 층과의 거리도 적당히 선호한다.
    weights = [1 + (hi - lo) / 16 + min(abs(x - game.next_x), 100) / 50
               for x, (lo, hi) in pool]
    return random.choices(pool, weights=weights, k=1)[0]


def add_cloud_row(game, x, y, storm=False, bounds=None):
    stage = cloud_stage(y)
    bounds = safe_bounds(x, stage, storm) if bounds is None else bounds
    if storm:
        storm_lane = (W - 82, W - 34) if x <= W / 2 else (34, 82)
        sx = random.randint(storm_lane[0] + 6, storm_lane[1] - 6)
        game.clouds.append(make_cloud(sx, y, kind="storm", bounds=storm_lane))
    game.clouds.append(make_cloud(x, y, bounds=bounds))
    game.next_x = x
    # 생성 기록을 저장하므로 밟아서 삭제된 구름도 다음 배치에 반영된다.
    game.safe_row_history.append((x, bounds))
    game.safe_row_history = game.safe_row_history[-2:]


def spawn_next_cloud_row(game):
    # 최종 높이에 정확히 구조 구름을 한 번만 생성한다.
    goal_y = START_PLATFORM_Y - FINAL_HEIGHT
    remaining = game.top_cloud_y - goal_y
    if remaining <= 0:
        return
    if remaining <= 75:
        goal = make_cloud(W / 2, goal_y, moving=False,
                          kind="goal", bounds=(W / 2, W / 2))
        goal["w"] = GOAL_CLOUD_WIDTH
        game.clouds.append(goal)
        game.top_cloud_y = goal_y
        game.cloud_row_index += 1
        return
    # 새로 생성될 층의 실제 스테이지에 맞는 간격만 선택
    gaps = []
    min_all_gap = int(min(rule[0] for rule in ROW_RULES.values()))
    max_all_gap = int(max(rule[1] for rule in ROW_RULES.values()))
    for gap in range(min_all_gap, max_all_gap + 1):
        stage = cloud_stage(game.top_cloud_y - gap)
        min_gap, max_gap = ROW_RULES[stage][:2]
        if min_gap <= gap <= max_gap:
            gaps.append(gap)
    if remaining <= 2 * max_all_gap:
        # 마지막 두 층은 지나치게 좁거나 넓지 않도록 나눈다.
        gaps = [gap for gap in gaps if 40 <= remaining - gap <= 75] or [int(remaining / 2)]
    y = game.top_cloud_y - random.choice(gaps)
    stage = cloud_stage(y)
    game.cloud_row_index += 1
    storm = should_add_storm(game, stage)
    x, bounds = choose_safe_x(game, stage, storm)
    add_cloud_row(game, x, y, storm, bounds)
    if storm:
        game.last_storm_row = game.cloud_row_index
    # 생성 기록은 구름이 사라져도 유지
    game.top_cloud_y = y


def init_clouds(game):
    game.clouds = [make_cloud(W / 2, START_PLATFORM_Y, moving=False, bounds=(W / 2, W / 2))]
    game.next_x = W / 2
    game.safe_row_history = [(W / 2, (W / 2, W / 2))]
    game.top_cloud_y = START_PLATFORM_Y
    game.cloud_row_index = 0
    game.last_storm_row = None
    while game.top_cloud_y > max(game.camera_y - 80, START_PLATFORM_Y - FINAL_HEIGHT):
        spawn_next_cloud_row(game)


def move_clouds(game, dt):
    for cloud in game.clouds:
        cloud["x"] += cloud["vx"] * dt
        lo, hi = cloud["bounds"]
        if cloud["x"] < lo:
            cloud["x"] = float(lo)
            cloud["vx"] = abs(cloud["vx"])
        elif cloud["x"] > hi:
            cloud["x"] = float(hi)
            cloud["vx"] = -abs(cloud["vx"])


def handle_landing(game, old_feet, new_feet):
    if game.vy <= 0:
        return
    for cloud in sorted(game.clouds, key=lambda c: c["y"]):
        if not (old_feet <= cloud["y"] <= new_feet and abs(game.px - cloud["x"]) < cloud["w"] / 2 + 6):
            continue
        if cloud["kind"] == "storm":
            if game.stage >= 2:
                take_damage(game, "STORM")
                if game.state == "GAMEOVER":
                    return
            continue
        if cloud["kind"] == "goal":
            # 높이만 넘는 것은 성공이 아니다. 실제로 마지막 구름에 착지해야 한다.
            game.py = cloud["y"] - LANDING_OFFSET
            game.vy = 0.0
            game.highest = max(game.highest, FINAL_HEIGHT)
            game.fox_rescued = True
            game.fall_damage_taken = False
            print("FOX RESCUED!", flush=True)
            return
        game.py = cloud["y"] - LANDING_OFFSET
        game.vy = JUMP_POWER
        game.fall_damage_taken = False
        game.clouds.remove(cloud)
        print("POP! CLOUD REMOVED!", flush=True)
        break


def scroll_clouds(game):
    # 마지막 생성 높이를 사용하여 삭제된 구름이 다시 생기지 않게 함
    while game.top_cloud_y > max(game.camera_y - 80, START_PLATFORM_Y - FINAL_HEIGHT):
        spawn_next_cloud_row(game)
    game.clouds = [c for c in game.clouds if c["kind"] == "goal" or c["y"] - game.camera_y < H + 55]


def draw_cloud(game, x, y, width=CLOUD_WIDTH, kind="normal"):
    sprite = cloud_sprite("normal" if kind == "goal" else kind, width)
    game.image.paste(sprite, (int(x) - width // 2, int(y) - round(width / 4)), sprite)