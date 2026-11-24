import random
import time
from functools import lru_cache

import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789
from joystick import Joystick

# Sky Pop: Raspberry Pi + Adafruit 1.3-inch TFT Bonnet (240 x 240)
W = H = 240
MOVE_SPEED = 260.0
JUMP_POWER = -470.0
RISE_GRAVITY = 900.0
FALL_GRAVITY = 1750.0
MAX_FALL_SPEED = 760.0
CLOUD_GAP = 62.0
CLOUD_SPEED = 22.0
PLAYER_RADIUS = 10
LANDING_OFFSET = 9
STORM_CHANCE = 0.35
STAGE_HEIGHT = 500
FINAL_HEIGHT = 1500
START_PLATFORM_Y = 214.0
BANNER_SECONDS = 1.3
BIRD_SPEED = 95.0
BIRD_INTERVAL = 2.4
BIRD_KNOCKDOWN = 300.0
STAGE_NAMES = {1: "SUNNY SKY", 2: "CLOUD TRAP", 3: "DANGER ZONE"}
PALETTES = {1: ((95, 175, 245), (145, 222, 250)),
            2: ((96, 113, 162), (164, 183, 215)),
            3: ((40, 45, 88), (93, 103, 158))}


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


@lru_cache(maxsize=3)
def stage_background(stage):
    image = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(image)
    a, b = PALETTES[stage]
    for y in range(H):
        color = tuple(int(a[i] + (b[i] - a[i]) * y / (H - 1)) for i in range(3))
        d.line((0, y, W-1, y), fill=color)
    return image


class SkyPop:
    def __init__(self):
        self.dc = digitalio.DigitalInOut(board.D25)
        self.rst = digitalio.DigitalInOut(board.D24)
        self.bl = digitalio.DigitalInOut(board.D26)
        self.bl.switch_to_output(value=True)
        self.lcd = st7789.ST7789(
            board.SPI(), dc=self.dc, cs=None, rst=self.rst,
            width=W, height=H, rotation=180,
            baudrate=8000000, x_offset=0, y_offset=80,
        )
        self.joy = Joystick()
        self.image = Image.new("RGB", (W, H))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()
        try:
            self.banner_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
            self.small_font = ImageFont.truetype("DejaVuSans.ttf", 13)
        except OSError:
            self.banner_font = self.small_font = self.font
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

    def add_cloud_row(self, x, y):
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
            self.clouds.append(make_cloud(safe_x, y, bounds=safe_bounds))
            self.clouds.append(make_cloud(random.uniform(*storm_bounds), y,
                                          kind="storm", bounds=storm_bounds))
        else:
            safe_x = x
            self.clouds.append(make_cloud(safe_x, y))
        self.next_x = safe_x

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
            self.add_cloud_row(x, y)
        self.stage = 1
        self.birds = []
        self.bird_timer = 0.0
        self.hit_timer = 0.0
        self.show_banners([(1, "START")])

    def show_banners(self, messages):
        self.banners = list(messages)
        self.banner_left = BANNER_SECONDS
        self.state = "BANNER"
        print(f"STAGE {self.banners[0][0]} {self.banners[0][1]}", flush=True)

    def update_banner(self, elapsed):
        self.banner_left -= elapsed
        if self.banner_left > 0:
            return
        self.banners.pop(0)
        if self.banners:
            self.banner_left = BANNER_SECONDS
            if self.banners[0][1] == "START":
                self.stage = self.banners[0][0]
            print(f"STAGE {self.banners[0][0]} {self.banners[0][1]}", flush=True)
        else:
            self.state = "CLEAR" if self.stage == 3 and self.highest >= FINAL_HEIGHT else "PLAY"

    def check_stage(self):
        if self.highest < self.stage * STAGE_HEIGHT:
            return
        if self.stage == 3:
            self.show_banners([(3, "FINISH")])
        else:
            self.show_banners([(self.stage, "FINISH"), (self.stage + 1, "START")])

    def update_birds(self, dt, old_x, old_y):
        if self.stage != 3:
            return
        self.hit_timer = max(0.0, self.hit_timer - dt)
        self.bird_timer -= dt
        if self.bird_timer <= 0:
            direction = random.choice((-1, 1))
            self.birds.append({"x": -20.0 if direction == 1 else W + 20.0,
                               "y": self.camera_y + random.uniform(55, 145),
                               "vx": direction * BIRD_SPEED})
            self.bird_timer = BIRD_INTERVAL
        for bird in self.birds:
            old_bx = bird["x"]
            bird["x"] += bird["vx"] * dt
            # Swept collision in relative coordinates, including fast player falls.
            ax, ay = old_x - old_bx, old_y - bird["y"]
            bx, by = self.px - bird["x"], self.py - bird["y"]
            dx, dy = bx - ax, by - ay
            length2 = dx * dx + dy * dy
            t = max(0.0, min(1.0, -(ax * dx + ay * dy) / length2)) if length2 else 0.0
            if self.hit_timer == 0 and (ax + dx*t)**2 + (ay + dy*t)**2 < 23**2:
                self.vy = max(self.vy, BIRD_KNOCKDOWN)
                self.hit_timer = 1.0
                print("BIRD HIT!", flush=True)
        self.birds = [b for b in self.birds if -40 < b["x"] < W + 40
                      and b["y"] - self.camera_y < H + 35]

    def update(self, dt):
        old_x, old_y = self.px, self.py
        if self.joy.pressed("left"):
            self.px -= MOVE_SPEED * dt
        if self.joy.pressed("right"):
            self.px += MOVE_SPEED * dt
        self.px = max(PLAYER_RADIUS, min(W - PLAYER_RADIUS, self.px))

        old_feet = self.py + LANDING_OFFSET
        gravity = RISE_GRAVITY if self.vy < 0 else FALL_GRAVITY
        self.vy = min(self.vy + gravity * dt, MAX_FALL_SPEED)
        self.py += self.vy * dt
        new_feet = self.py + LANDING_OFFSET

        for cloud in self.clouds:
            cloud["x"] += cloud["vx"] * dt
            lo, hi = cloud["bounds"]
            if cloud["x"] < lo:
                cloud["x"] = float(lo)
                cloud["vx"] = abs(cloud["vx"])
            elif cloud["x"] > hi:
                cloud["x"] = float(hi)
                cloud["vx"] = -abs(cloud["vx"])

        if self.vy > 0:
            # Check upper platforms first; storm clouds have no landing surface.
            for cloud in sorted(self.clouds, key=lambda c: c["y"]):
                if cloud["kind"] == "storm":
                    continue
                if (old_feet <= cloud["y"] <= new_feet
                        and abs(self.px - cloud["x"]) < cloud["w"] / 2 + 6):
                    self.py = cloud["y"] - LANDING_OFFSET
                    self.vy = JUMP_POWER
                    print("POP!", flush=True)
                    break

        self.update_birds(dt, old_x, old_y)
        if self.py - self.camera_y < 88:
            self.camera_y = self.py - 88
        self.highest = max(self.highest, int(START_PLATFORM_Y - (self.py + LANDING_OFFSET)))

        if self.clouds:
            top_y = min(c["y"] for c in self.clouds)
            while top_y > self.camera_y - 80:
                top_y -= CLOUD_GAP
                x = max(44.0, min(196.0, self.next_x + random.randint(-38, 38)))
                self.add_cloud_row(x, top_y)
        self.clouds = [c for c in self.clouds if c["y"] - self.camera_y < H + 55]
        if self.py - self.camera_y > H + 15:
            self.state = "GAMEOVER"
        else:
            self.check_stage()

    def draw_cloud(self, x, y, width=64, kind="normal"):
        sprite = cloud_sprite(kind, width)
        self.image.paste(sprite, (int(x) - width // 2,
                                  int(y) - sprite.height // 2), sprite)

    def draw_player(self, x, y):
        x, y = int(x), int(y)
        d = self.draw
        d.ellipse((x-11, y-15, x-5, y-3), fill=(255, 184, 214))
        d.ellipse((x+5, y-15, x+11, y-3), fill=(255, 184, 214))
        d.ellipse((x-11, y-10, x+11, y+9), fill=(255, 214, 233))
        d.ellipse((x-5, y-2, x-3, y), fill=(30, 30, 45))
        d.ellipse((x+3, y-2, x+5, y), fill=(30, 30, 45))
        d.ellipse((x-8, y+2, x-4, y+5), fill=(255, 138, 173))
        d.ellipse((x+4, y+2, x+8, y+5), fill=(255, 138, 173))

    def center_text(self, text, y, font=None, fill="white"):
        font = font or self.font
        box = self.draw.textbbox((0, 0), text, font=font)
        x = (W - (box[2] - box[0])) // 2 - box[0]
        self.draw.text((x, y), text, fill=fill, font=font)

    def render(self):
        d = self.draw
        self.image.paste(stage_background(self.stage))
        for i in range(10):
            sx = (i * 73 + 25) % W
            sy = int((i * 57 - self.camera_y * 0.25) % H)
            d.ellipse((sx, sy, sx+2, sy+2), fill="white")

        if self.state == "TITLE":
            self.draw_cloud(120, 170, 90)
            self.draw_player(120, 150)
            d.text((88, 64), "SKY POP", fill="white", stroke_width=1,
                   stroke_fill=(40, 95, 165), font=self.font)
            d.text((51, 111), "PRESS ANY BUTTON", fill=(35, 75, 145), font=self.font)
            d.text((53, 211), "MOVE: LEFT / RIGHT", fill=(35, 75, 145), font=self.font)
        elif self.state in ("PLAY", "BANNER"):
            for cloud in self.clouds:
                if cloud["kind"] == "storm" and self.stage == 1:
                    continue
                sy = cloud["y"] - self.camera_y
                if -25 < sy < H + 25:
                    self.draw_cloud(cloud["x"], sy, cloud["w"], cloud["kind"])
            for bird in self.birds:
                sprite = bird_sprite()
                if bird["vx"] < 0:
                    sprite = sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                self.image.paste(sprite, (int(bird["x"])-18, int(bird["y"]-self.camera_y)-10), sprite)
            if not self.hit_timer or int(self.hit_timer * 12) % 2 == 0:
                self.draw_player(self.px, self.py - self.camera_y)
            d.rectangle((0, 0, W, 31), fill=(30, 51, 91))
            d.text((7, 4), f"STAGE {self.stage}", fill="white", font=self.font)
            d.text((96, 4), f"H: {min(self.highest, FINAL_HEIGHT)}/{self.stage * STAGE_HEIGHT}", fill="white", font=self.font)
            progress = max(0.0, min(1.0, (self.highest - (self.stage - 1) * STAGE_HEIGHT) / STAGE_HEIGHT))
            d.rectangle((8, 23, W-9, 26), fill="#536582")
            if progress > 0:
                d.rectangle((8, 23, 8 + int((W-17)*progress), 26), fill="#FFE16B")
            if self.state == "BANNER":
                stage, action = self.banners[0]
                d.rounded_rectangle((10, 79, W-11, 160), radius=8, fill="#263654", outline="#DFE9FF", width=2)
                self.center_text(f"STAGE {stage} {action}", 92, self.banner_font)
                self.center_text(STAGE_NAMES[stage] if action == "START" else f"HEIGHT {stage * STAGE_HEIGHT} REACHED", 130, self.small_font, "#FFE16B")
        elif self.state == "CLEAR":
            self.center_text("GAME CLEAR!", 61, self.banner_font, "#FFE16B")
            self.center_text("ALL 3 STAGES COMPLETE", 106, self.small_font)
            self.center_text(f"HEIGHT: {FINAL_HEIGHT}", 132, self.small_font)
            self.center_text("PRESS CENTER TO RETRY", 183)
        else:
            self.draw_cloud(120, 170, 90)
            d.text((82, 75), "GAME OVER!", fill="white", stroke_width=1,
                   stroke_fill=(180, 45, 75), font=self.font)
            self.center_text(f"STAGE {self.stage}  HEIGHT: {self.highest}", 110, self.font, "white")
            d.text((47, 145), "PRESS CENTER TO RETRY", fill=(35, 75, 145), font=self.font)
        self.lcd.image(self.image)

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
                    self.update_banner(elapsed)
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
            self.bl.value = False
            self.bl.deinit()
            self.dc.deinit()
            self.rst.deinit()


if __name__ == "__main__":
    SkyPop().run()
