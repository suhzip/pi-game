"""라즈베리파이 TFT LCD 하드웨어 및 SPI 전송."""
import board
import digitalio
from adafruit_rgb_display import st7789
from config import W, H

def init_display(game):
    game.dc = digitalio.DigitalInOut(board.D25)
    game.rst = digitalio.DigitalInOut(board.D24)
    game.bl = digitalio.DigitalInOut(board.D26)
    game.bl.switch_to_output(value=True)
    game.lcd = st7789.ST7789(
        board.SPI(), dc=game.dc, cs=None, rst=game.rst,
        width=W, height=H, rotation=180,
        baudrate=8000000, x_offset=0, y_offset=80,
    )


def show_frame(game):
    game.lcd.image(game.image)

def close_display(game):
    game.bl.value = False
    game.bl.deinit()
    game.dc.deinit()
    game.rst.deinit()
