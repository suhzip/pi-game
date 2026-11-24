"""캐릭터 이동, 물리 계산, 캐릭터 그리기."""
from config import W, MOVE_SPEED, PLAYER_RADIUS, LANDING_OFFSET, RISE_GRAVITY, FALL_GRAVITY, MAX_FALL_SPEED

def update_player(game, dt):
    old_x, old_y = game.px, game.py
    if game.joy.pressed("left"):
        game.px -= MOVE_SPEED * dt
    if game.joy.pressed("right"):
        game.px += MOVE_SPEED * dt
    game.px = max(PLAYER_RADIUS, min(W - PLAYER_RADIUS, game.px))

    old_feet = game.py + LANDING_OFFSET
    gravity = RISE_GRAVITY if game.vy < 0 else FALL_GRAVITY
    game.vy = min(game.vy + gravity * dt, MAX_FALL_SPEED)
    game.py += game.vy * dt
    new_feet = game.py + LANDING_OFFSET
    return old_x, old_y, old_feet, new_feet


def draw_player(game, x, y):
    x, y = int(x), int(y)
    d = game.draw
    d.ellipse((x-11, y-15, x-5, y-3), fill=(255, 184, 214))
    d.ellipse((x+5, y-15, x+11, y-3), fill=(255, 184, 214))
    d.ellipse((x-11, y-10, x+11, y+9), fill=(255, 214, 233))
    d.ellipse((x-5, y-2, x-3, y), fill=(30, 30, 45))
    d.ellipse((x+3, y-2, x+5, y), fill=(30, 30, 45))
    d.ellipse((x-8, y+2, x-4, y+5), fill=(255, 138, 173))
    d.ellipse((x+4, y+2, x+8, y+5), fill=(255, 138, 173))
