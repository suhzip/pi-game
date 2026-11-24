"""Stage 3 새 장애물 생성, 이동 및 충돌 처리."""

import random
from functools import lru_cache
from PIL import Image, ImageDraw

from config import (
    W, H,
    BIRD_SPEED,
    BIRD_INTERVAL,
    BIRD_KNOCKDOWN
)

from player import take_damage


# 새 이미지 생성
@lru_cache(maxsize=1)
def bird_sprite():

    sprite = Image.new("RGBA", (36, 20))
    d = ImageDraw.Draw(sprite)

    # 외곽선
    d.polygon([
        (0, 2), (12, 6), (18, 11),
        (24, 6), (35, 2), (30, 13),
        (22, 18), (13, 18), (5, 13)
    ], fill="#70495A")

    # 날개
    d.polygon([
        (2, 3), (13, 8), (18, 12),
        (24, 8), (33, 3), (28, 12),
        (21, 16), (14, 16), (7, 12)
    ], fill="#E69B6F")

    # 몸통
    d.rectangle(
        (16, 5, 25, 13),
        fill="#F8D09A"
    )

    # 눈
    d.rectangle(
        (22, 7, 23, 8),
        fill="#292638"
    )

    # 부리
    d.polygon([
        (26, 8), (32, 10), (26, 12)
    ], fill="#FFDF68")

    return sprite


# 새 장애물 갱신
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
                min(1.0, -(ax * dx + ay * dy) / length2)
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