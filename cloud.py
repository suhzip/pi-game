"""구름 이미지, 생성, 이동, 착지 및 스크롤 관리."""

import random

from pathlib import Path
from functools import lru_cache
from PIL import Image

from config import (
    W,
    H,
    CLOUD_SPEED,
    CLOUD_GAP,
    STAGE_HEIGHT,
    START_PLATFORM_Y,
    STORM_CHANCE,
    LANDING_OFFSET,
    JUMP_POWER
)

from player import take_damage


# =========================
# 구름 이미지 및 크기 설정
# =========================

ASSET_DIR = Path(__file__).resolve().parent / "assets"

CLOUD_WIDTH = 48

CLOUD_IMAGES = {
    "normal": "cloud_normal.png",
    "storm": "cloud_storm.png"
}


# =========================
# 구름 객체 생성
# =========================
def make_cloud(
    x, y,
    moving=True,
    kind="normal",
    bounds=(34, W - 34)
):

    return {
        "x": float(x),
        "y": float(y),
        "w": CLOUD_WIDTH,
        "vx": random.choice((-1.0, 1.0)) * CLOUD_SPEED
              if moving else 0.0,
        "kind": kind,
        "bounds": bounds
    }


# =========================
# PNG 이미지 불러오기
# =========================
@lru_cache(maxsize=2)
def load_cloud_image(kind):

    image_path = ASSET_DIR / CLOUD_IMAGES[kind]

    with Image.open(image_path) as image:

        return image.convert("RGBA")


# =========================
# 구름 이미지 크기 조절
# =========================
@lru_cache(maxsize=8)
def cloud_sprite(kind, width):

    sprite = load_cloud_image(kind)

    # 기존 이미지 비율 유지
    height = max(
        1,
        round(sprite.height * width / sprite.width)
    )

    # 픽셀아트의 선명한 모양 유지
    return sprite.resize(
        (width, height),
        Image.Resampling.NEAREST
    )


# =========================
# 새로운 구름 배치
# =========================
def add_cloud_row(game, x, y):

    altitude = START_PLATFORM_Y - y

    # 스테이지별 먹구름 등장 확률
    chance = (
        0.50
        if altitude >= 2 * STAGE_HEIGHT
        else STORM_CHANCE
    )

    first_storm_row = (
        STAGE_HEIGHT <= altitude
        < STAGE_HEIGHT + CLOUD_GAP
    )

    paired = (
        altitude >= STAGE_HEIGHT
        and (first_storm_row or random.random() < chance)
    )

    # 일반 구름과 먹구름 함께 생성
    if paired:

        left = (34, 78)
        right = (162, 206)

        safe_bounds, storm_bounds = (
            (left, right)
            if x <= W / 2
            else (right, left)
        )

        safe_x = max(
            safe_bounds[0],
            min(safe_bounds[1], x)
        )

        # 일반 구름 생성
        game.clouds.append(
            make_cloud(
                safe_x,
                y,
                bounds=safe_bounds
            )
        )

        # 먹구름 생성
        game.clouds.append(
            make_cloud(
                random.uniform(*storm_bounds),
                y,
                kind="storm",
                bounds=storm_bounds
            )
        )

    else:

        safe_x = x

        game.clouds.append(
            make_cloud(safe_x, y)
        )

    game.next_x = safe_x


# =========================
# 구름 좌우 이동
# =========================
def move_clouds(game, dt):

    for cloud in game.clouds:

        cloud["x"] += cloud["vx"] * dt

        lo, hi = cloud["bounds"]

        # 왼쪽 경계에서 방향 전환
        if cloud["x"] < lo:

            cloud["x"] = float(lo)
            cloud["vx"] = abs(cloud["vx"])

        # 오른쪽 경계에서 방향 전환
        elif cloud["x"] > hi:

            cloud["x"] = float(hi)
            cloud["vx"] = -abs(cloud["vx"])


# =========================
# 구름 착지 및 충돌 판정
# =========================
def handle_landing(game, old_feet, new_feet):

    # 캐릭터가 하강 중일 때만 검사
    if game.vy > 0:

        for cloud in sorted(
            game.clouds,
            key=lambda c: c["y"]
        ):

            # 실제 구름 크기를 기준으로 충돌 판정
            if (
                old_feet <= cloud["y"] <= new_feet
                and abs(game.px - cloud["x"])
                < cloud["w"] / 2 + 6
            ):

                # -------------------------
                # 먹구름 착지
                # -------------------------
                if cloud["kind"] == "storm":

                    if game.stage >= 2:

                        # 목숨 1개 감소
                        take_damage(game, "STORM")

                        if game.state == "GAMEOVER":
                            return

                    # 자동 점프하지 않고 낙하
                    continue

                # -------------------------
                # 일반 구름 착지
                # -------------------------
                game.py = cloud["y"] - LANDING_OFFSET

                # 자동 점프
                game.vy = JUMP_POWER

                # 중복 낙하 피해 기록 초기화
                game.fall_damage_taken = False

                print("POP!", flush=True)

                break


# =========================
# 화면 스크롤 및 구름 관리
# =========================
def scroll_clouds(game):

    if game.clouds:

        top_y = min(c["y"] for c in game.clouds)

        # 화면 위쪽에 새로운 구름 생성
        while top_y > game.camera_y - 80:

            top_y -= CLOUD_GAP

            x = max(
                44.0,
                min(
                    196.0,
                    game.next_x + random.randint(-38, 38)
                )
            )

            add_cloud_row(game, x, top_y)

    # 화면 아래로 벗어난 구름 제거
    game.clouds = [
        c for c in game.clouds
        if c["y"] - game.camera_y < H + 55
    ]


# =========================
# 구름 이미지 화면 출력
# =========================
def draw_cloud(
    game, x, y,
    width=CLOUD_WIDTH,
    kind="normal"
):

    sprite = cloud_sprite(kind, width)

    # 번개 부분을 제외한 구름 몸체 기준으로 배치
    body_half_height = round(width / 4)

    game.image.paste(
        sprite,
        (
            int(x) - width // 2,
            int(y) - body_half_height
        ),
        sprite
    )