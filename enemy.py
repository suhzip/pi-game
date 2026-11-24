"""Stage 3 새 장애물의 그림, 생성, 이동 및 충돌."""
import random
from functools import lru_cache
from PIL import Image, ImageDraw
from config import W, H, BIRD_SPEED, BIRD_INTERVAL, BIRD_KNOCKDOWN

@lru_cache(maxsize=1)
def bird_sprite():
    sprite = Image.new("RGBA", (36, 20))
    d = ImageDraw.Draw(sprite)
    d.polygon([(0, 2), (12, 6), (18, 11), (24, 6), (35, 2),
               (30, 13), (22, 18), (13, 18), (5, 13)], fill="#70495A")
    d.polygon([(2, 3), (13, 8), (18, 12), (24, 8), (33, 3),
               (28, 12), (21, 16), (14, 16), (7, 12)], fill="#E69B6F")
    d.rectangle((16, 5, 25, 13), fill="#F8D09A")
    d.rectangle((22, 7, 23, 8), fill="#292638")
    d.polygon([(26, 8), (32, 10), (26, 12)], fill="#FFDF68")
    return sprite


def update_birds(game, dt, old_x, old_y):
    if game.stage != 3:
        return
    game.hit_timer = max(0.0, game.hit_timer - dt)
    game.bird_timer -= dt
    if game.bird_timer <= 0:
        direction = random.choice((-1, 1))
        game.birds.append({"x": -20.0 if direction == 1 else W + 20.0,
                           "y": game.camera_y + random.uniform(55, 145),
                           "vx": direction * BIRD_SPEED})
        game.bird_timer = BIRD_INTERVAL
    for bird in game.birds:
        old_bx = bird["x"]
        bird["x"] += bird["vx"] * dt
        # Swept collision in relative coordinates, including fast player falls.
        ax, ay = old_x - old_bx, old_y - bird["y"]
        bx, by = game.px - bird["x"], game.py - bird["y"]
        dx, dy = bx - ax, by - ay
        length2 = dx * dx + dy * dy
        t = max(0.0, min(1.0, -(ax * dx + ay * dy) / length2)) if length2 else 0.0
        if game.hit_timer == 0 and (ax + dx*t)**2 + (ay + dy*t)**2 < 23**2:
            game.vy = max(game.vy, BIRD_KNOCKDOWN)
            game.hit_timer = 1.0
            print("BIRD HIT!", flush=True)
    game.birds = [b for b in game.birds if -40 < b["x"] < W + 40
                  and b["y"] - game.camera_y < H + 35]
