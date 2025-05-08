# led_control.py
import board, neopixel, random, colorsys

# ----- strip configuration (adjust these three lines) -----
PIXEL_PIN  = board.D18   # DIN wire on the first LED
NUM_PIXELS = 90          # total LEDs on the string
BRIGHTNESS = 0.5         # 0.0 – 1.0 overall brightness
# ----------------------------------------------------------

pixels = neopixel.NeoPixel(
    PIXEL_PIN,
    NUM_PIXELS,
    brightness=BRIGHTNESS,
    auto_write=False,
    pixel_order=neopixel.GRB
)

# private helper: return a random blue‑purple colour
def _random_blue_purple():
    hue = random.uniform(0.55, 0.78)           # 200°–280° in HSV
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))

# ---------- PUBLIC API ---------- #
def turn_on_light():
    """Fill the whole strip with random blue‑purple values and show it."""
    for i in range(NUM_PIXELS):
        pixels[i] = _random_blue_purple()
    pixels.show()

def turn_off_light():
    """Turn every LED off (black) and latch it to the strip."""
    pixels.fill((0, 0, 0))
    pixels.show()
    # pass
# --------------------------------- #

# # Optional quick test: run `sudo python3 led_control.py`
# if __name__ == "__main__":
#     from time import sleep
#     turn_on_light()
#     sleep(2)
#     turn_off_light()