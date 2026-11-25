"""스테이지 전환 및 여우 구조 성공 처리."""
from config import STAGE_TARGETS, BANNER_SECONDS, RESCUE_SECONDS, START_PLATFORM_Y, FINAL_HEIGHT, LANDING_OFFSET


def show_banners(game, messages):
    game.banners = list(messages)
    game.banner_left = BANNER_SECONDS
    game.state = "BANNER"
    print(f"STAGE {game.banners[0][0]} {game.banners[0][1]}", flush=True)


def update_banner(game, elapsed):
    game.banner_left -= elapsed
    if game.banner_left > 0:
        return
    game.banners.pop(0)
    if game.banners:
        game.banner_left = BANNER_SECONDS
        if game.banners[0][1] == "START":
            game.stage = game.banners[0][0]
        print(f"STAGE {game.banners[0][0]} {game.banners[0][1]}", flush=True)
    else:
        game.state = "CLEAR" if game.fox_rescued else "PLAY"


def check_stage(game):
    # Stage 3에서는 높이가 아니라 실제 구조 구름 착지로 성공한다.
    if game.stage == 3:
        if game.fox_rescued:
            game.state = "RESCUE"
            game.rescue_left = RESCUE_SECONDS
            game.camera_y = START_PLATFORM_Y - FINAL_HEIGHT - 150
            game.px = 97.0
            game.py = START_PLATFORM_Y - FINAL_HEIGHT - LANDING_OFFSET
            print("RESCUE SUCCESS!", flush=True)
        return
    if game.highest >= STAGE_TARGETS[game.stage]:
        show_banners(game, [(game.stage, "FINISH"), (game.stage + 1, "START")])


def update_rescue(game, elapsed):
    game.rescue_left -= elapsed
    if game.rescue_left <= 0:
        show_banners(game, [(3, "FINISH")])
