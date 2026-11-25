"""Sky Pop 실행 및 전체 게임 흐름 관리."""
import time
from config import H, JUMP_POWER, START_PLATFORM_Y, LANDING_OFFSET, MAX_LIVES, HIT_INVINCIBILITY, FINAL_HEIGHT, GOAL_CLOUD_WIDTH
from joystick import Joystick
from display import init_display, show_frame, close_display
from player import update_player, take_damage
from cloud import CLOUD_WIDTH, make_cloud, cloud_sprite, init_clouds, move_clouds, handle_landing, scroll_clouds
from enemy import update_birds
from stage import show_banners, update_banner, check_stage, update_rescue
from renderer import init_renderer, render


class SkyPop:
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
        self.top_cloud_y = START_PLATFORM_Y
        self.cloud_row_index = 0
        self.last_storm_row = None
        self.stage = 1
        self.banners = []
        self.banner_left = 0.0
        self.birds = []
        self.bird_timer = 0.0
        self.lives = MAX_LIVES
        self.hit_timer = 0.0
        self.fall_damage_taken = False
        self.fox_rescued = False
        self.rescue_left = 0.0
        for kind, width in (("normal", CLOUD_WIDTH), ("storm", CLOUD_WIDTH), ("normal", 90), ("normal", GOAL_CLOUD_WIDTH)):
            cloud_sprite(kind, width)

    def reset(self):
        self.state = "PLAY"
        self.px = 120.0
        self.py = 195.0
        self.vy = JUMP_POWER
        self.camera_y = 0.0
        self.highest = 0
        self.stage = 1
        self.fox_rescued = False
        self.rescue_left = 0.0
        init_clouds(self)
        self.birds = []
        self.bird_timer = 0.0
        self.lives = MAX_LIVES
        self.hit_timer = 0.0
        self.fall_damage_taken = False
        show_banners(self, [(1, "START")])

    def respawn(self):
        safe_clouds = [c for c in self.clouds if c["kind"] == "normal" and 45 <= c["y"] - self.camera_y <= H - 30]
        if safe_clouds:
            cloud = max(safe_clouds, key=lambda c: c["y"])
        else:
            # 구조 구름에 자동 부활하여 클리어되는 상황을 방지한다.
            goal_y = START_PLATFORM_Y - FINAL_HEIGHT
            cloud = make_cloud(120, max(self.camera_y + 190, goal_y + 62), moving=False)
            self.clouds.append(cloud)
        self.px = cloud["x"]
        self.py = cloud["y"] - LANDING_OFFSET
        self.vy = JUMP_POWER
        self.hit_timer = HIT_INVINCIBILITY
        self.fall_damage_taken = False
        self.state = "PLAY"
        print(f"RESPAWN! LIVES: {self.lives}", flush=True)

    def update(self, dt):
        self.hit_timer = max(0.0, self.hit_timer - dt)
        old_x, old_y, old_feet, new_feet = update_player(self, dt)
        move_clouds(self, dt)
        handle_landing(self, old_feet, new_feet)
        if self.fox_rescued:
            self.birds.clear()
            self.hit_timer = 0.0
            check_stage(self)
            return
        if self.state == "GAMEOVER":
            return
        update_birds(self, dt, old_x, old_y)
        if self.state == "GAMEOVER":
            return
        if self.py - self.camera_y < 88:
            self.camera_y = self.py - 88
        self.highest = max(self.highest, int(START_PLATFORM_Y - (self.py + LANDING_OFFSET)))
        scroll_clouds(self)
        if self.py - self.camera_y > H + 15:
            if not self.fall_damage_taken:
                self.hit_timer = 0.0
                take_damage(self, "FALL")
            if self.lives <= 0:
                self.state = "GAMEOVER"
            else:
                self.respawn()
            return
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
                any_pressed = any(self.joy.pressed(k) for k in ("up", "down", "left", "right", "center"))
                center = self.joy.pressed("center")
                if self.state == "TITLE" and any_pressed and not previous_any:
                    self.reset()
                elif self.state == "PLAY":
                    self.update(dt)
                elif self.state == "RESCUE":
                    update_rescue(self, elapsed)
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
