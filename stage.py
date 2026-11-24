"""스테이지 진행 및 START / FINISH 안내 상태."""
from config import STAGE_HEIGHT, FINAL_HEIGHT, BANNER_SECONDS

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
        game.state = "CLEAR" if game.stage == 3 and game.highest >= FINAL_HEIGHT else "PLAY"


def check_stage(game):
    if game.highest < game.stage * STAGE_HEIGHT:
        return
    if game.stage == 3:
        show_banners(game, [(3, "FINISH")])
    else:
        show_banners(game, [(game.stage, "FINISH"), (game.stage + 1, "START")])
