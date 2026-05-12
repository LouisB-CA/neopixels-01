
# NeoPixels on RPi4
* 2026-04-27
```text
i have a neopixel connected to my rpi5 gpio.  the neopixel is blinking away, as expected.  i also have a neopixel connected to my rpi4 and i want to use it as an indicator in a python script.  i think maybe i need a different library or different something for the rpi4. i can't just copy the rpi5 code, can i
```

* Claude Responded

You're right to be cautious — the RPi 4 and RPi 5 use different GPIO hardware, which affects NeoPixel control significantly.
You're right to be cautious — the RPi 4 and RPi 5 use different GPIO hardware, which affects NeoPixel control significantly.

The Core Difference
RPi 5 uses a new RP1 I/O controller chip, and the rpi-ws281x / adafruit-circuitpython-neopixel libraries work well with it via PWM or a specific pin.

RPi 4 has the older Broadcom GPIO, but NeoPixels are actually easier and more reliable on RPi 4 using PWM or SPI — the library support is more mature.

What You Need on RPi 4
The standard stack that works great on RPi 4:

bash
pip install rpi_ws281x adafruit-circuitpython-neopixel
And you'll likely need to run your script as root (or via sudo), since the PWM/DMA access requires it.

Working Example for RPi 4
python
import board
import neopixel
import time

# Common PWM-capable pins on RPi 4: board.D18 (GPIO 18) is the most reliable
NUM_PIXELS = 1  # or however many you have
PIN = board.D18

pixels = neopixel.NeoPixel(PIN, NUM_PIXELS, brightness=0.5, auto_write=False)

# Green indicator = good
def set_indicator(color):
    pixels.fill(color)
    pixels.show()

set_indicator((0, 255, 0))   # green
time.sleep(1)
set_indicator((255, 0, 0))   # red
time.sleep(1)
set_indicator((0, 0, 0))     # off
Key Differences to Watch For
Thing	RPi 5	RPi 4
Recommended pin	Varies (RP1 chip)	GPIO 18 (PWM0) is most reliable
Run as root?	Sometimes	Yes, usually required
Library	same neopixel + board	same neopixel + board
SPI alternative	Less common	Works well (GPIO 10)
If GPIO 18 / PWM Gives You Trouble
Try SPI mode instead — it's often more stable and doesn't need root on RPi 4:

bash
# Enable SPI in raspi-config first
sudo raspi-config  # → Interface Options → SPI → Enable
python
PIN = board.MOSI  # GPIO 10
So the library is the same, but you likely need to:

Use GPIO 18 (or MOSI/GPIO 10 for SPI)
Run with sudo
Make sure rpi_ws281x is installed (it's the C backend the Python lib uses)


