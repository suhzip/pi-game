"""Stage 3 새 장애물 생성, 이동, 충돌 및 이미지 관리."""

import random

from pathlib import Path
from functools import lru_cache
from PIL import Image, ImageOps

from config import (
    W,
    H,
    BIRD_WIDTH,
    BIRD_HEIGHT,
    BIRD_SPEED,
    BIRD_INTERVAL,
    BIRD_KNOCKDOWN
)

from player import take_damage


# =========================
# 새 이미지 경로
# =========================
ASSET_DIR = Path(__file__).resolve().parent / "assets"

BIRD_IMAGE = ASSET_DIR / "bird.png"


# =========================
# 새 PNG 이미지 불러오기
# =========================
@lru_cache(maxsize=1)
def bird_sprite():

    with Image.open(BIRD_IMAGE) as image:

        sprite = image.convert("RGBA")

        # 원본 비율을 유지하면서 크기 조절
        sprite = ImageOps.contain(
            sprite,
            (BIRD_WIDTH, BIRD_HEIGHT),
            Image.Resampling.NEAREST
        )

    # 기존 렌더링 크기에 맞는 투명 이미지
    canvas = Image.new(
        "RGBA",
        (BIRD_WIDTH, BIRD_HEIGHT),
        (0, 0, 0, 0)
    )

    # 새 이미지를 가운데 배치
    canvas.paste(
        sprite,
        (
            (BIRD_WIDTH - sprite.width) // 2,
            (BIRD_HEIGHT - sprite.height) // 2
        )
    )

    return canvas


# =========================
# 새 장애물 갱신
# =========================
def update_birds(game, dt, old_x, old_y):

    # Stage 3에서만 새 등장
    if game.stage != 3:
        return

    game.bird_timer -= dt

    # 일정 시간마다 새 생성
    if game.bird_timer <= 0:

        direction = random.choice((-1, 1))

        game.birds.append({
            "x": -20.0 if direction == 1 else W + 20.0,
            "y": game.camera_y + random.uniform(55, 145),
            "vx": direction * BIRD_SPEED
        })

        game.bird_timer = BIRD_INTERVAL

    for bird in game.birds:

        old_bx = bird["x"]

        # 새 이동
        bird["x"] += bird["vx"] * dt

        # 이동 경로를 고려한 충돌 판정
        ax = old_x - old_bx
        ay = old_y - bird["y"]

        bx = game.px - bird["x"]
        by = game.py - bird["y"]

        dx = bx - ax
        dy = by - ay

        length2 = dx * dx + dy * dy

        t = (
            max(
                0.0,
                min(
                    1.0,
                    -(ax * dx + ay * dy) / length2
                )
            )
            if length2 else 0.0
        )

        # 캐릭터와 새 사이의 충돌 여부
        if (
            game.hit_timer == 0
            and (ax + dx * t)**2
            + (ay + dy * t)**2 < 23**2
        ):

            # 목숨 1개 감소
            if take_damage(game, "BIRD"):

                # 강제 낙하
                game.vy = max(
                    game.vy,
                    BIRD_KNOCKDOWN
                )

                if game.state == "GAMEOVER":
                    return

    # 화면 밖으로 이동한 새 제거
    game.birds = [
        b for b in game.birds
        if -40 < b["x"] < W + 40
        and b["y"] - game.camera_y < H + 35
    ]