import random
import time

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


def make_cloud(x, y, moving=True):
    return {
        "x": float(x), "y": float(y), "w": 64,
        "vx": random.choice((-1.0, 1.0)) * CLOUD_SPEED if moving else 0.0,
    }


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
        self.state = "TITLE"
        self.highest = 0
        self.camera_y = 0.0
        self.px = 120.0
        self.py = 195.0
        self.vy = 0.0
        self.clouds = []
        self.next_x = 120.0

    def reset(self):
        self.state = "PLAY"
        self.px = 120.0
        self.py = 195.0
        self.vy = JUMP_POWER
        self.camera_y = 0.0
        self.highest = 0
        self.next_x = 120.0
        self.clouds = [make_cloud(120, 214, moving=False)]
        x = 120.0
        for y in (152, 90, 28, -34, -96):
            x = max(44.0, min(196.0, x + random.randint(-38, 38)))
            self.clouds.append(make_cloud(x, y))
        self.next_x = x

    def update(self, dt):
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
            if cloud["x"] < 34:
                cloud["x"] = 34.0
                cloud["vx"] = abs(cloud["vx"])
            elif cloud["x"] > W - 34:
                cloud["x"] = float(W - 34)
                cloud["vx"] = -abs(cloud["vx"])

        if self.vy > 0:
            # Crossing test avoids missing landings during fast falls.
            for cloud in self.clouds:
                if (old_feet <= cloud["y"] <= new_feet
                        and abs(self.px - cloud["x"]) < cloud["w"] / 2 + 6):
                    self.py = cloud["y"] - LANDING_OFFSET
                    self.vy = JUMP_POWER
                    print("POP!", flush=True)
                    break

        if self.py - self.camera_y < 88:
            self.camera_y = self.py - 88
        self.highest = max(self.highest, int(-self.camera_y))

        if self.clouds:
            top_y = min(c["y"] for c in self.clouds)
            while top_y > self.camera_y - 80:
                top_y -= CLOUD_GAP
                self.next_x = max(44.0, min(196.0, self.next_x + random.randint(-38, 38)))
                self.clouds.append(make_cloud(self.next_x, top_y))
        self.clouds = [c for c in self.clouds if c["y"] - self.camera_y < H + 55]
        if self.py - self.camera_y > H + 15:
            self.state = "GAMEOVER"

    def draw_cloud(self, x, y, width=64):
        x, y = int(x), int(y)
        half = width // 2
        d = self.draw
        d.ellipse((x-half+4, y+2, x+half+4, y+13), fill=(135, 185, 224))
        d.ellipse((x-half, y-5, x+half, y+9), fill="white")
        d.ellipse((x-22, y-14, x+5, y+8), fill="white")
        d.ellipse((x-5, y-17, x+23, y+8), fill="white")
        d.line((x-half+9, y, x+half-9, y), fill=(185, 220, 250), width=2)
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

    def render(self):
        d = self.draw
        for y in range(H):
            d.line((0, y, W, y), fill=(95+y//12, min(175+y//5, 240), 245))
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
        elif self.state == "PLAY":
            for cloud in self.clouds:
                sy = cloud["y"] - self.camera_y
                if -25 < sy < H + 25:
                    self.draw_cloud(cloud["x"], sy, cloud["w"])
            self.draw_player(self.px, self.py - self.camera_y)
            d.rectangle((0, 0, W, 23), fill=(35, 100, 170))
            d.text((8, 7), f"HEIGHT: {self.highest}", fill="white", font=self.font)
        else:
            self.draw_cloud(120, 170, 90)
            d.text((82, 75), "GAME OVER!", fill="white", stroke_width=1,
                   stroke_fill=(180, 45, 75), font=self.font)
            d.text((76, 110), f"HEIGHT: {self.highest}", fill=(35, 75, 145), font=self.font)
            d.text((47, 145), "PRESS CENTER TO RETRY", fill=(35, 75, 145), font=self.font)
        self.lcd.image(self.image)

    def run(self):
        previous_any = False
        previous_center = False
        last = time.monotonic()
        try:
            while True:
                now = time.monotonic()
                dt = min(now - last, 0.06)
                last = now
                any_pressed = any(self.joy.pressed(k) for k in
                                  ("up", "down", "left", "right", "center"))
                center = self.joy.pressed("center")
                if self.state == "TITLE" and any_pressed and not previous_any:
                    self.reset()
                elif self.state == "PLAY":
                    self.update(dt)
                elif self.state == "GAMEOVER" and center and not previous_center:
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