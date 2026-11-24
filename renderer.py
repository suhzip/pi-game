"""Pillow 기반 게임 화면 및 UI 렌더링."""

from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

from config import (
    W,
    H,
    PALETTES,
    STAGE_HEIGHT,
    FINAL_HEIGHT,
    STAGE_NAMES,
    MAX_LIVES
)

from cloud import draw_cloud
from player import draw_player
from enemy import bird_sprite


# =========================
# 스테이지별 배경 생성
# =========================
@lru_cache(maxsize=3)
def stage_background(stage):

    image = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(image)

    a, b = PALETTES[stage]

    for y in range(H):

        color = tuple(
            int(a[i] + (b[i] - a[i]) * y / (H - 1))
            for i in range(3)
        )

        d.line(
            (0, y, W-1, y),
            fill=color
        )

    return image


# =========================
# 렌더링 초기화
# =========================
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


# =========================
# 가운데 정렬 텍스트
# =========================
def center_text(game, text, y, font=None, fill="white"):

    font = font or game.font

    box = game.draw.textbbox(
        (0, 0),
        text,
        font=font
    )

    x = (W - (box[2] - box[0])) // 2 - box[0]

    game.draw.text(
        (x, y),
        text,
        fill=fill,
        font=font
    )


# =========================
# 오른쪽 상단 하트 UI
# =========================
def draw_hearts(game):

    d = game.draw

    # 최대 목숨 개수만큼 하트 생성
    for i in range(MAX_LIVES):

        # 오른쪽 상단 위치
        x = W - 4 - MAX_LIVES * 14 + i * 14

        y = 5

        # 작은 픽셀아트 하트 모양
        points = [
            (0, 2),
            (2, 2),
            (2, 0),
            (5, 0),
            (5, 2),
            (7, 2),
            (7, 0),
            (10, 0),
            (10, 2),
            (12, 2),
            (12, 6),
            (10, 6),
            (10, 8),
            (8, 8),
            (8, 10),
            (4, 10),
            (4, 8),
            (2, 8),
            (2, 6),
            (0, 6)
        ]

        # 남아 있는 목숨 확인
        alive = i < game.lives

        # 빨간색: 남은 목숨
        # 회색: 잃은 목숨
        color = (
            "#FF526E"
            if alive
            else "#59657E"
        )

        # 하트 그리기
        d.polygon(
            [(x+a, y+b) for a, b in points],
            fill=color
        )

        # 하트 하이라이트
        if alive:

            d.rectangle(
                (x+2, y+2, x+3, y+3),
                fill="#FFB8C8"
            )


# =========================
# 전체 게임 화면 렌더링
# =========================
def render(game):

    d = game.draw

    # 스테이지별 배경 출력
    game.image.paste(
        stage_background(game.stage)
    )

    # 배경 장식
    for i in range(10):

        sx = (i * 73 + 25) % W

        sy = int(
            (i * 57 - game.camera_y * 0.25) % H
        )

        d.ellipse(
            (sx, sy, sx+2, sy+2),
            fill="white"
        )


    # =========================
    # 게임 시작 화면
    # =========================
    if game.state == "TITLE":

        draw_cloud(
            game,
            120,
            170,
            90
        )

        draw_player(
            game,
            120,
            150
        )

        d.text(
            (88, 64),
            "SKY POP",
            fill="white",
            stroke_width=1,
            stroke_fill=(40, 95, 165),
            font=game.font
        )

        d.text(
            (51, 111),
            "PRESS ANY BUTTON",
            fill=(35, 75, 145),
            font=game.font
        )

        d.text(
            (53, 211),
            "MOVE: LEFT / RIGHT",
            fill=(35, 75, 145),
            font=game.font
        )


    # =========================
    # 게임 진행 화면
    # =========================
    elif game.state in ("PLAY", "BANNER"):

        # -------------------------
        # 구름 출력
        # -------------------------
        for cloud in game.clouds:

            # Stage 1에서는 먹구름 표시하지 않음
            if (
                cloud["kind"] == "storm"
                and game.stage == 1
            ):

                continue

            sy = cloud["y"] - game.camera_y

            if -25 < sy < H + 25:

                draw_cloud(
                    game,
                    cloud["x"],
                    sy,
                    cloud["w"],
                    cloud["kind"]
                )


        # -------------------------
        # 새 장애물 출력
        # -------------------------
        for bird in game.birds:

            sprite = bird_sprite()

            # 이동 방향에 따라 이미지 반전
            if bird["vx"] < 0:

                sprite = sprite.transpose(
                    Image.Transpose.FLIP_LEFT_RIGHT
                )

            game.image.paste(
                sprite,
                (
                    int(bird["x"]) - 18,
                    int(bird["y"] - game.camera_y) - 10
                ),
                sprite
            )


        # -------------------------
        # 캐릭터 출력
        # -------------------------

        # 피격 및 부활 후 무적 상태에서 깜빡임
        if (
            not game.hit_timer
            or int(game.hit_timer * 12) % 2 == 0
        ):

            draw_player(
                game,
                game.px,
                game.py - game.camera_y
            )


        # -------------------------
        # 상단 HUD
        # -------------------------
        d.rectangle(
            (0, 0, W, 31),
            fill=(30, 51, 91)
        )

        # 현재 스테이지 표시
        d.text(
            (7, 4),
            f"STAGE {game.stage}",
            fill="white",
            font=game.font
        )

        # 현재 높이 표시
        d.text(
            (83, 4),
            f"H: {min(game.highest, FINAL_HEIGHT)}/{game.stage * STAGE_HEIGHT}",
            fill="white",
            font=game.font
        )

        # 오른쪽 상단 하트 표시
        draw_hearts(game)


        # -------------------------
        # 스테이지 진행률
        # -------------------------
        progress = max(
            0.0,
            min(
                1.0,
                (
                    game.highest
                    - (game.stage - 1) * STAGE_HEIGHT
                ) / STAGE_HEIGHT
            )
        )

        # 진행률 바 배경
        d.rectangle(
            (8, 23, W-9, 26),
            fill="#536582"
        )

        # 현재 진행률
        if progress > 0:

            d.rectangle(
                (
                    8,
                    23,
                    8 + int((W-17) * progress),
                    26
                ),
                fill="#FFE16B"
            )


        # -------------------------
        # 스테이지 시작 및 종료 안내
        # -------------------------
        if game.state == "BANNER":

            stage, action = game.banners[0]

            d.rounded_rectangle(
                (10, 79, W-11, 160),
                radius=8,
                fill="#263654",
                outline="#DFE9FF",
                width=2
            )

            center_text(
                game,
                f"STAGE {stage} {action}",
                92,
                game.banner_font
            )

            message = (
                STAGE_NAMES[stage]
                if action == "START"
                else f"HEIGHT {stage * STAGE_HEIGHT} REACHED"
            )

            center_text(
                game,
                message,
                130,
                game.small_font,
                "#FFE16B"
            )


    # =========================
    # 게임 클리어 화면
    # =========================
    elif game.state == "CLEAR":

        center_text(
            game,
            "GAME CLEAR!",
            61,
            game.banner_font,
            "#FFE16B"
        )

        center_text(
            game,
            "ALL 3 STAGES COMPLETE",
            106,
            game.small_font
        )

        center_text(
            game,
            f"HEIGHT: {FINAL_HEIGHT}",
            132,
            game.small_font
        )

        center_text(
            game,
            "PRESS CENTER TO RETRY",
            183
        )

        # 클리어 시 남은 목숨 표시
        draw_hearts(game)


    # =========================
    # 게임 오버 화면
    # =========================
    else:

        draw_cloud(
            game,
            120,
            170,
            90
        )

        d.text(
            (82, 75),
            "GAME OVER!",
            fill="white",
            stroke_width=1,
            stroke_fill=(180, 45, 75),
            font=game.font
        )

        center_text(
            game,
            f"STAGE {game.stage}  HEIGHT: {game.highest}",
            110,
            game.font,
            "white"
        )

        d.text(
            (47, 145),
            "PRESS CENTER TO RETRY",
            fill=(35, 75, 145),
            font=game.font
        )

        # 모든 목숨이 소진된 상태 표시
        draw_hearts(game)