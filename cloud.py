"""구름 생성, 좌우 이동, 착지 및 스크롤 관리."""
import random
from functools import lru_cache
from PIL import Image, ImageDraw
from config import W, H, CLOUD_SPEED, CLOUD_GAP, STAGE_HEIGHT, START_PLATFORM_Y, STORM_CHANCE, LANDING_OFFSET, JUMP_POWER

def make_cloud(x, y, moving=True, kind="normal", bounds=(34, W - 34)):
    return {
        "x": float(x), "y": float(y), "w": 64,
        "vx": random.choice((-1.0, 1.0)) * CLOUD_SPEED if moving else 0.0,
        "kind": kind,
        "bounds": bounds,
    }


@lru_cache(maxsize=8)
def cloud_sprite(kind, width):
    """Generate transparent pixel-art once per type and width."""
    sprite = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(sprite)
    if kind == "storm":
        outline, body, shade, light = "#33384D", "#686E87", "#454B65", "#9199AF"
    else:
        outline, body, shade, light = "#91B6DA", "#F9FCFF", "#C5DFF5", "#FFFFFF"
    d.polygon([(0, 9), (0, 7), (3, 7), (3, 5), (7, 5), (7, 3),
               (10, 3), (10, 1), (19, 1), (19, 3), (23, 3), (23, 5),
               (27, 5), (27, 7), (30, 7), (30, 9), (31, 9), (31, 12),
               (29, 12), (29, 14), (3, 14), (3, 13), (0, 13)], fill=outline)
    d.polygon([(1, 9), (4, 9), (4, 6), (8, 6), (8, 4), (11, 4),
               (11, 2), (18, 2), (18, 4), (22, 4), (22, 6), (26, 6),
               (26, 8), (29, 8), (29, 10), (30, 10), (30, 11),
               (28, 11), (28, 13), (4, 13), (4, 12), (1, 12)], fill=body)
    d.rectangle((4, 11, 28, 12), fill=shade)
    d.rectangle((7, 13, 25, 13), fill=shade)
    d.line((11, 3, 16, 3), fill=light)
    d.line((8, 5, 11, 5), fill=light)
    # The collision plane remains at the middle of the sprite (y=8).
    if kind == "storm":
        d.polygon([(16, 5), (12, 10), (16, 10), (14, 14),
                   (21, 8), (17, 8), (19, 5)], fill="#FFE16B")
    else:
        d.line((5, 8, 26, 8), fill="#D2E8FA")
    return sprite.resize((width, max(1, width // 2)), Image.Resampling.NEAREST)


def add_cloud_row(game, x, y):
    """Generate hazards by world altitude, independent of camera position."""
    altitude = START_PLATFORM_Y - y
    chance = 0.50 if altitude >= 2 * STAGE_HEIGHT else STORM_CHANCE
    first_storm_row = STAGE_HEIGHT <= altitude < STAGE_HEIGHT + CLOUD_GAP
    paired = altitude >= STAGE_HEIGHT and (first_storm_row or random.random() < chance)
    if paired:
        # Separate movement lanes prevent an unsafe cloud from hiding a safe one.
        left, right = (34, 78), (162, 206)
        safe_bounds, storm_bounds = (left, right) if x <= W / 2 else (right, left)
        safe_x = max(safe_bounds[0], min(safe_bounds[1], x))
        game.clouds.append(make_cloud(safe_x, y, bounds=safe_bounds))
        game.clouds.append(make_cloud(random.uniform(*storm_bounds), y,
                                      kind="storm", bounds=storm_bounds))
    else:
        safe_x = x
        game.clouds.append(make_cloud(safe_x, y))
    game.next_x = safe_x


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
    if game.vy > 0:
        # Check upper platforms first; storm clouds have no landing surface.
        for cloud in sorted(game.clouds, key=lambda c: c["y"]):
            if cloud["kind"] == "storm":
                continue
            if (old_feet <= cloud["y"] <= new_feet
                    and abs(game.px - cloud["x"]) < cloud["w"] / 2 + 6):
                game.py = cloud["y"] - LANDING_OFFSET
                game.vy = JUMP_POWER
                print("POP!", flush=True)
                break


def scroll_clouds(game):
    if game.clouds:
        top_y = min(c["y"] for c in game.clouds)
        while top_y > game.camera_y - 80:
            top_y -= CLOUD_GAP
            x = max(44.0, min(196.0, game.next_x + random.randint(-38, 38)))
            add_cloud_row(game, x, top_y)
    game.clouds = [c for c in game.clouds if c["y"] - game.camera_y < H + 55]


def draw_cloud(game, x, y, width=64, kind="normal"):
    sprite = cloud_sprite(kind, width)
    game.image.paste(sprite, (int(x) - width // 2,
                              int(y) - sprite.height // 2), sprite)
