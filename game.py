"""Sky Pop 실행 및 전체 흐름. 각 기능은 독립 모듈에 정의한다."""
import random
import time
from config import H, JUMP_POWER, START_PLATFORM_Y, LANDING_OFFSET
from joystick import Joystick
from display import init_display, show_frame, close_display
from player import update_player
from cloud import make_cloud, cloud_sprite, add_cloud_row, move_clouds, handle_landing, scroll_clouds
from enemy import update_birds
from stage import show_banners, update_banner, check_stage
from renderer import init_renderer, render


class SkyPop:
    """게임 상태를 한 곳에 보관하고 각 기능을 순서대로 호출한다."""
    def __init__(self):
        init_display(self)
        self.joy = Joystick()
        init_renderer(self)
        self.state = "TITLE"
        self.highest = 0
        self.camera_y = 0.0
        self.px = 120.0
        self.py = 195.0
        self.vy = 0.0
        self.clouds = []
        self.next_x = 120.0
        self.stage = 1
        self.banners = []
        self.banner_left = 0.0
        self.birds = []
        self.bird_timer = 0.0
        self.hit_timer = 0.0
        # Prepare sprites before entering the game loop.
        for kind, width in (("normal", 64), ("storm", 64), ("normal", 90)):
            cloud_sprite(kind, width)

    def reset(self):
        self.state = "PLAY"
        self.px = 120.0
        self.py = 195.0
        self.vy = JUMP_POWER
        self.camera_y = 0.0
        self.highest = 0
        self.next_x = 120.0
        self.clouds = [make_cloud(120, 214, moving=False)]
        for y in (152, 90, 28, -34, -96):
            x = max(44.0, min(196.0, self.next_x + random.randint(-38, 38)))
            add_cloud_row(self, x, y)
        self.stage = 1
        self.birds = []
        self.bird_timer = 0.0
        self.hit_timer = 0.0
        show_banners(self, [(1, "START")])

    def update(self, dt):
        old_x, old_y, old_feet, new_feet = update_player(self, dt)
        move_clouds(self, dt)
        handle_landing(self, old_feet, new_feet)
        update_birds(self, dt, old_x, old_y)
        if self.py - self.camera_y < 88:
            self.camera_y = self.py - 88
        self.highest = max(self.highest, int(START_PLATFORM_Y - (self.py + LANDING_OFFSET)))
        scroll_clouds(self)
        if self.py - self.camera_y > H + 15:
            self.state = "GAMEOVER"
        else:
            check_stage(self)

    def render(self):
        render(self)
        show_frame(self)

    def run(self):
        previous_any = False
        previous_center = False
        last = time.monotonic()
        try:
            while True:
                now = time.monotonic()
                elapsed = now - last
                dt = min(elapsed, 0.06)
                last = now
                any_pressed = any(self.joy.pressed(k) for k in
                                  ("up", "down", "left", "right", "center"))
                center = self.joy.pressed("center")
                if self.state == "TITLE" and any_pressed and not previous_any:
                    self.reset()
                elif self.state == "PLAY":
                    self.update(dt)
                elif self.state == "BANNER":
                    update_banner(self, elapsed)
                elif self.state in ("GAMEOVER", "CLEAR") and center and not previous_center:
                    self.reset()
                previous_any = any_pressed
                previous_center = center
                self.render()
                time.sleep(0.005)
        except KeyboardInterrupt:
            print("Sky Pop stopped", flush=True)
        finally:
            self.joy.close()
            close_display(self)


if __name__ == "__main__":
    SkyPop().run()
