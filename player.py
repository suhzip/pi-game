"""캐릭터 이동, 물리 계산, 피격 처리 및 그래픽."""

from config import (
    W,
    MOVE_SPEED,
    PLAYER_RADIUS,
    LANDING_OFFSET,
    RISE_GRAVITY,
    FALL_GRAVITY,
    MAX_FALL_SPEED,
    HIT_INVINCIBILITY
)


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

    # 화면 밖으로 이동하지 않도록 제한
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
# 캐릭터 그래픽
# =========================
def draw_player(game, x, y):

    x, y = int(x), int(y)

    d = game.draw

    # 왼쪽 귀
    d.ellipse(
        (x-11, y-15, x-5, y-3),
        fill=(255, 184, 214)
    )

    # 오른쪽 귀
    d.ellipse(
        (x+5, y-15, x+11, y-3),
        fill=(255, 184, 214)
    )

    # 몸통
    d.ellipse(
        (x-11, y-10, x+11, y+9),
        fill=(255, 214, 233)
    )

    # 왼쪽 눈
    d.ellipse(
        (x-5, y-2, x-3, y),
        fill=(30, 30, 45)
    )

    # 오른쪽 눈
    d.ellipse(
        (x+3, y-2, x+5, y),
        fill=(30, 30, 45)
    )

    # 왼쪽 볼
    d.ellipse(
        (x-8, y+2, x-4, y+5),
        fill=(255, 138, 173)
    )

    # 오른쪽 볼
    d.ellipse(
        (x+4, y+2, x+8, y+5),
        fill=(255, 138, 173)
    )