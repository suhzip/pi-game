"""캐릭터 이동, 물리 계산, 피격 처리 및 이미지 렌더링."""

from pathlib import Path
from functools import lru_cache
from PIL import Image

from config import (
    W,
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    MOVE_SPEED,
    PLAYER_RADIUS,
    LANDING_OFFSET,
    RISE_GRAVITY,
    FALL_GRAVITY,
    MAX_FALL_SPEED,
    HIT_INVINCIBILITY
)


# =========================
# 캐릭터 이미지 경로
# =========================
ASSET_DIR = Path(__file__).resolve().parent / "assets"

PLAYER_IMAGE = ASSET_DIR / "player.png"


# =========================
# 캐릭터 이미지 불러오기
# =========================
@lru_cache(maxsize=1)
def player_sprite():

    with Image.open(PLAYER_IMAGE) as image:

        sprite = image.convert("RGBA")

        sprite = sprite.resize(
            (PLAYER_WIDTH, PLAYER_HEIGHT),
            Image.Resampling.NEAREST
        )

    return sprite


# =========================
# 목숨 차감 및 피격 처리
# =========================
def take_damage(game, source):

    # 무적 상태에서는 피해를 받지 않음
    if game.hit_timer > 0 or game.lives <= 0:
        return False

    # 목숨 1개 감소
    game.lives -= 1

    # 피격 후 무적 시간
    game.hit_timer = HIT_INVINCIBILITY

    # 추락 시 목숨 중복 차감 방지
    game.fall_damage_taken = True

    print(
        f"{source} HIT! LIVES: {game.lives}",
        flush=True
    )

    # 목숨이 0개일 때 게임 종료
    if game.lives <= 0:
        game.state = "GAMEOVER"

    return True


# =========================
# 캐릭터 이동 및 물리 계산
# =========================
def update_player(game, dt):

    old_x, old_y = game.px, game.py

    # 왼쪽 이동
    if game.joy.pressed("left"):
        game.px -= MOVE_SPEED * dt

    # 오른쪽 이동
    if game.joy.pressed("right"):
        game.px += MOVE_SPEED * dt

    # 화면 밖 이동 방지
    game.px = max(
        PLAYER_RADIUS,
        min(W - PLAYER_RADIUS, game.px)
    )

    # 이동 전 발 위치
    old_feet = game.py + LANDING_OFFSET

    # 상승 및 하강 중력 적용
    gravity = (
        RISE_GRAVITY
        if game.vy < 0
        else FALL_GRAVITY
    )

    # 수직 속도 계산
    game.vy = min(
        game.vy + gravity * dt,
        MAX_FALL_SPEED
    )

    # 캐릭터 위치 갱신
    game.py += game.vy * dt

    # 이동 후 발 위치
    new_feet = game.py + LANDING_OFFSET

    return old_x, old_y, old_feet, new_feet


# =========================
# 캐릭터 이미지 화면 출력
# =========================
def draw_player(game, x, y):

    # 캐릭터 이미지 불러오기
    sprite = player_sprite()

    # 캐릭터 중심 기준 가로 위치
    draw_x = int(x) - sprite.width // 2

    # 기존 착지 기준에 맞춰 세로 위치 계산
    draw_y = (
        int(y)
        + LANDING_OFFSET
        - sprite.height
        + 1
    )

    # 투명 배경을 유지하면서 이미지 합성
    game.image.paste(
        sprite,
        (draw_x, draw_y),
        sprite
    )