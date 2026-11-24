import board
import digitalio


class Joystick:
    def __init__(self):
        self.pins = {
            "up": board.D17,
            "down": board.D22,
            "left": board.D27,
            "right": board.D23,
            "center": board.D4,
        }

        self.buttons = {}

        for name, pin in self.pins.items():
            button = digitalio.DigitalInOut(pin)
            button.direction = digitalio.Direction.INPUT
            button.pull = digitalio.Pull.UP
            self.buttons[name] = button

    def pressed(self, direction):
        return not self.buttons[direction].value

    def close(self):
        for button in self.buttons.values():
            button.deinit()


if __name__ == "__main__":
    import time

    joystick = Joystick()

    try:
        while True:
            active = [
                name for name in joystick.pins
                if joystick.pressed(name)
            ]
            print("Pressed:", active, flush=True)
            time.sleep(0.2)
    except KeyboardInterrupt:
        joystick.close()