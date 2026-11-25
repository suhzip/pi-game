"""Pillow 기반 게임 화면 및 UI 렌더링."""

from pathlib import Path
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

from config import (
    W, H,
    STAGE_LENGTHS, STAGE_STARTS, STAGE_TARGETS, FINAL_HEIGHT,
    FOX_WIDTH, FOX_HEIGHT,
    STAGE_NAMES, MAX_LIVES
)
from cloud import draw_cloud
from player import draw_player
from enemy import bird_sprite

# 스테이지별 배경 이미지
ASSET_DIR = Path(__file__).resolve().parent / "assets"
BACKGROUND_IMAGES = {
    1: "bg_stage1.png",
    2: "bg_stage2.png",
    3: "bg_stage3.png"
}


@lru_cache(maxsize=3)
def stage_background(stage):
    """PNG를 한 번만 불러와 LCD 크기에 맞춰 캐싱한다."""
    path = ASSET_DIR / BACKGROUND_IMAGES[stage]
    with Image.open(path) as image:
        return image.convert("RGB").resize(
            (W, H), Image.Resampling.NEAREST
        )


def init_renderer(game):
    game.image = Image.new("RGB", (W, H))
    game.draw = ImageDraw.Draw(game.image)
    game.font = ImageFont.load_default()

    try:
        game.banner_font = ImageFont.truetype(
            "DejaVuSans-Bold.ttf", 22
        )
        game.small_font = ImageFont.truetype(
            "DejaVuSans.ttf", 13
        )
    except OSError:
        game.banner_font = game.font
        game.small_font = game.font

    # 시작 화면 전용 폰트
    game.title_font = result_font(40)
    game.title_subtitle_font = result_font(13)
    game.title_start_font = result_font(19)
    game.title_controls_font = result_font(13)

    # 결과 화면 전용 폰트
    game.result_heading_font = result_font(28)
    game.result_title_font = result_font(38)
    game.result_info_font = result_font(16)
    game.result_button_font = result_font(13)

    fox_sprite()
    fox_sprite(True)

    # 게임 시작 전 배경 3개를 미리 로딩
    for stage in BACKGROUND_IMAGES:
        stage_background(stage)


def center_text(game, text, y, font=None, fill="white"):
    font = font or game.font
    box = game.draw.textbbox((0, 0), text, font=font)
    x = (W - (box[2] - box[0])) // 2 - box[0]
    game.draw.text((x, y), text, fill=fill, font=font)


def draw_hearts(game):
    d = game.draw
    points = [
        (0, 2), (2, 2), (2, 0), (5, 0),
        (5, 2), (7, 2), (7, 0), (10, 0),
        (10, 2), (12, 2), (12, 6), (10, 6),
        (10, 8), (8, 8), (8, 10), (4, 10),
        (4, 8), (2, 8), (2, 6), (0, 6)
    ]
    for i in range(MAX_LIVES):
        x = W - 4 - MAX_LIVES * 14 + i * 14
        y = 5
        alive = i < game.lives
        color = "#FF526E" if alive else "#59657E"
        d.polygon([(x+a, y+b) for a, b in points], fill=color)
        if alive:
            d.rectangle((x+2, y+2, x+3, y+3), fill="#FFB8C8")


def result_font(size):
    """LCD 결과 화면용 굵은 글꼴."""
    for path in (
        "DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        # 구형 Pillow에서는 기본 비트맵 폰트를 사용한다.
        return ImageFont.load_default()


def result_text(game, text, top, font, fill="white"):
    """글자의 실제 보이는 영역을 기준으로 중앙에 배치."""
    box = game.draw.textbbox((0, 0), text, font=font)
    x = (W - (box[2] - box[0])) // 2 - box[0]
    game.draw.text((x, top - box[1]), text, font=font, fill=fill)


def draw_result(game, cleared):
    """중앙에 배치되는 작은 게임 종료 결과창."""
    d = game.draw
    accent = "#FFE16B" if cleared else "#FF7085"
    panel = "#17233C" if cleared else "#2B2038"

    # LCD 중앙에 190 x 170px 결과창 배치
    d.rounded_rectangle((25, 35, W-26, H-36), radius=10,
                        fill=panel, outline=accent, width=3)
    result_text(game, "GAME", 45, game.result_heading_font)
    result_text(game, "CLEAR!" if cleared else "OVER!", 72,
                game.result_title_font, accent)
    d.line((42, 108, W-43, 108), fill=accent, width=1)
    result_text(game, "FOX RESCUED!" if cleared else f"STAGE {game.stage}",
                117, game.result_info_font)
    height = FINAL_HEIGHT if cleared else game.highest
    result_text(game, f"HEIGHT: {height}", 137, game.result_info_font)
    d.rounded_rectangle((38, 160, W-39, 191), radius=5, fill=accent)
    result_text(game, "CENTER TO RETRY", 171,
                game.result_button_font, panel)
    draw_hearts(game)


@lru_cache(maxsize=1)
def title_player_sprite():
    """시작 화면에서만 토끼를 크게 표시한다."""
    with Image.open(ASSET_DIR / "player.png") as image:
        return image.convert("RGBA").resize((40, 52), Image.Resampling.NEAREST)


def title_text(game, text, top, font, fill, outline="#233D68", stroke=1):
    box = game.draw.textbbox((0, 0), text, font=font)
    x = (W - (box[2] - box[0])) // 2 - box[0]
    game.draw.text((x, top - box[1]), text, font=font, fill=fill,
                   stroke_width=stroke, stroke_fill=outline)


def draw_title(game):
    """팝업 없이 배경 전체를 활용하는 시작 화면."""
    # 로고 그림자와 큰 제목
    title_text(game, "SKY POP!", 25, game.title_font, "#233D68", stroke=2)
    title_text(game, "SKY POP!", 21, game.title_font, "#FFF2A0", stroke=2)
    title_text(game, "RESCUE THE FOX", 65, game.title_subtitle_font, "white")

    # 기존 구름과 토끼를 시작 화면의 대표 이미지로 사용
    draw_cloud(game, W // 2, 155, 100)
    sprite = title_player_sprite()
    game.image.paste(sprite, (W // 2 - sprite.width // 2, 90), sprite)

    # 별도의 창이나 버튼 박스 없이 글씨로 안내
    title_text(game, "PRESS ANY BUTTON", 184, game.title_start_font,
               "#FFE16B", stroke=2)
    title_text(game, "LEFT / RIGHT TO MOVE", 214, game.title_controls_font,
               "white", stroke=1)


@lru_cache(maxsize=2)
def fox_sprite(freed=False):
    """고해상도 원본을 LCD용 픽셀 이미지로 한 번만 변환한다."""
    with Image.open(ASSET_DIR / ("fox_free.png" if freed else "fox_bound.png")) as image:
        sprite = image.convert("RGBA")
        sprite.thumbnail((FOX_WIDTH, FOX_HEIGHT), Image.Resampling.NEAREST)
        return sprite


def draw_rescue_cloud(game, cloud, sy):
    """움직이지 않는 특별한 구조 구름, HELP 표식, 밧줄에 묶인 여우."""
    x = int(cloud["x"])
    draw_cloud(game, x, sy, cloud["w"], "goal")
    if game.fox_rescued:
        sprite = fox_sprite(True)
        bottom = int(sy) - round(cloud["w"] / 4) + 5
        game.image.paste(sprite, (x + 18 - sprite.width // 2, bottom - sprite.height), sprite)
    else:
        sprite = fox_sprite()
        bottom = int(sy) - round(cloud["w"] / 4) + 5
        game.image.paste(sprite, (x - sprite.width // 2, bottom - sprite.height), sprite)
        font = game.result_button_font
        text = "HELP!"
        box = game.draw.textbbox((0, 0), text, font=font)
        game.draw.text((x - (box[2] - box[0]) // 2 - box[0],
                        bottom - sprite.height - 5 - box[3]), text,
                       font=font, fill="#FFE16B", stroke_width=1,
                       stroke_fill="#17233C")


def render(game):
    d = game.draw

    # 고정 배경: 구름 및 캐릭터보다 먼저 출력
    game.image.paste(stage_background(game.stage), (0, 0))

    # TITLE
    if game.state == "TITLE":
        draw_title(game)

    # PLAY / BANNER
    elif game.state in ("PLAY", "BANNER", "RESCUE"):
        # 구름 출력
        for cloud in game.clouds:
            if cloud["kind"] == "storm" and game.stage == 1:
                continue
            sy = cloud["y"] - game.camera_y
            if -25 < sy < H + 25:
                if cloud["kind"] == "goal":
                    draw_rescue_cloud(game, cloud, sy)
                else:
                    draw_cloud(game, cloud["x"], sy, cloud["w"], cloud["kind"])

        # 새 장애물 출력 및 이동 방향 반전
        for bird in game.birds:
            sprite = bird_sprite()
            if bird["vx"] < 0:
                sprite = sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            game.image.paste(
                sprite,
                (int(bird["x"]) - sprite.width // 2,
                 int(bird["y"] - game.camera_y) - sprite.height // 2),
                sprite
            )

        # 피격 및 부활 후 무적 상태 깜빡임
        if not game.hit_timer or int(game.hit_timer * 12) % 2 == 0:
            draw_player(game, game.px, game.py - game.camera_y)

        # 상단 HUD
        d.rectangle((0, 0, W, 31), fill=(30, 51, 91))
        d.text((7, 4), f"STAGE {game.stage}",
               fill="white", font=game.font)
        d.text((83, 4),
               ("LAND ON GOAL!" if game.stage == 3 and game.highest >= FINAL_HEIGHT and not game.fox_rescued
                else f"H: {min(game.highest, FINAL_HEIGHT)}/{STAGE_TARGETS[game.stage]}"),
               fill="white", font=game.font)
        draw_hearts(game)

        # 스테이지 진행률
        progress = max(0.0, min(1.0,
            (game.highest - STAGE_STARTS[game.stage]) / STAGE_LENGTHS[game.stage]
        ))
        d.rectangle((8, 23, W-9, 26), fill="#536582")
        if progress > 0:
            d.rectangle((8, 23, 8 + int((W-17) * progress), 26),
                        fill="#FFE16B")

        # 구조 성공 연출: 팝업 없이 여우와 토끼가 함께 보인다.
        if game.state == "RESCUE":
            title_text(game, "FOX RESCUED!", 48, game.result_heading_font,
                       "#FFE16B", stroke=2)

        # 스테이지 시작 및 종료 안내
        if game.state == "BANNER":
            stage, action = game.banners[0]
            d.rounded_rectangle((10, 79, W-11, 160), radius=8,
                                fill="#263654", outline="#DFE9FF", width=2)
            center_text(game, f"STAGE {stage} {action}", 92, game.banner_font)
            message = (STAGE_NAMES[stage] if action == "START"
                       else "FOX RESCUED!" if stage == 3
                       else f"HEIGHT {STAGE_TARGETS[stage]} REACHED")
            center_text(game, message, 130, game.small_font, "#FFE16B")

    # CLEAR
    elif game.state == "CLEAR":
        draw_result(game, cleared=True)

    # GAMEOVER
    elif game.state == "GAMEOVER":
        draw_result(game, cleared=False)
