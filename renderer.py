"""Pillow로 배경 및 UI를 합성한다. LCD 전송은 display.py 담당."""
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from config import W, H, PALETTES, STAGE_HEIGHT, FINAL_HEIGHT, STAGE_NAMES
from cloud import draw_cloud
from player import draw_player
from enemy import bird_sprite

@lru_cache(maxsize=3)
def stage_background(stage):
    image = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(image)
    a, b = PALETTES[stage]
    for y in range(H):
        color = tuple(int(a[i] + (b[i] - a[i]) * y / (H - 1)) for i in range(3))
        d.line((0, y, W-1, y), fill=color)
    return image


def init_renderer(game):
    game.image = Image.new("RGB", (W, H))
    game.draw = ImageDraw.Draw(game.image)
    game.font = ImageFont.load_default()
    try:
        game.banner_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
        game.small_font = ImageFont.truetype("DejaVuSans.ttf", 13)
    except OSError:
        game.banner_font = game.small_font = game.font


def center_text(game, text, y, font=None, fill="white"):
    font = font or game.font
    box = game.draw.textbbox((0, 0), text, font=font)
    x = (W - (box[2] - box[0])) // 2 - box[0]
    game.draw.text((x, y), text, fill=fill, font=font)


def render(game):
    d = game.draw
    game.image.paste(stage_background(game.stage))
    for i in range(10):
        sx = (i * 73 + 25) % W
        sy = int((i * 57 - game.camera_y * 0.25) % H)
        d.ellipse((sx, sy, sx+2, sy+2), fill="white")

    if game.state == "TITLE":
        draw_cloud(game, 120, 170, 90)
        draw_player(game, 120, 150)
        d.text((88, 64), "SKY POP", fill="white", stroke_width=1,
               stroke_fill=(40, 95, 165), font=game.font)
        d.text((51, 111), "PRESS ANY BUTTON", fill=(35, 75, 145), font=game.font)
        d.text((53, 211), "MOVE: LEFT / RIGHT", fill=(35, 75, 145), font=game.font)
    elif game.state in ("PLAY", "BANNER"):
        for cloud in game.clouds:
            if cloud["kind"] == "storm" and game.stage == 1:
                continue
            sy = cloud["y"] - game.camera_y
            if -25 < sy < H + 25:
                draw_cloud(game, cloud["x"], sy, cloud["w"], cloud["kind"])
        for bird in game.birds:
            sprite = bird_sprite()
            if bird["vx"] < 0:
                sprite = sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            game.image.paste(sprite, (int(bird["x"])-18, int(bird["y"]-game.camera_y)-10), sprite)
        if not game.hit_timer or int(game.hit_timer * 12) % 2 == 0:
            draw_player(game, game.px, game.py - game.camera_y)
        d.rectangle((0, 0, W, 31), fill=(30, 51, 91))
        d.text((7, 4), f"STAGE {game.stage}", fill="white", font=game.font)
        d.text((96, 4), f"H: {min(game.highest, FINAL_HEIGHT)}/{game.stage * STAGE_HEIGHT}", fill="white", font=game.font)
        progress = max(0.0, min(1.0, (game.highest - (game.stage - 1) * STAGE_HEIGHT) / STAGE_HEIGHT))
        d.rectangle((8, 23, W-9, 26), fill="#536582")
        if progress > 0:
            d.rectangle((8, 23, 8 + int((W-17)*progress), 26), fill="#FFE16B")
        if game.state == "BANNER":
            stage, action = game.banners[0]
            d.rounded_rectangle((10, 79, W-11, 160), radius=8, fill="#263654", outline="#DFE9FF", width=2)
            center_text(game, f"STAGE {stage} {action}", 92, game.banner_font)
            center_text(game, STAGE_NAMES[stage] if action == "START" else f"HEIGHT {stage * STAGE_HEIGHT} REACHED", 130, game.small_font, "#FFE16B")
    elif game.state == "CLEAR":
        center_text(game, "GAME CLEAR!", 61, game.banner_font, "#FFE16B")
        center_text(game, "ALL 3 STAGES COMPLETE", 106, game.small_font)
        center_text(game, f"HEIGHT: {FINAL_HEIGHT}", 132, game.small_font)
        center_text(game, "PRESS CENTER TO RETRY", 183)
    else:
        draw_cloud(game, 120, 170, 90)
        d.text((82, 75), "GAME OVER!", fill="white", stroke_width=1,
               stroke_fill=(180, 45, 75), font=game.font)
        center_text(game, f"STAGE {game.stage}  HEIGHT: {game.highest}", 110, game.font, "white")
        d.text((47, 145), "PRESS CENTER TO RETRY", fill=(35, 75, 145), font=game.font)
