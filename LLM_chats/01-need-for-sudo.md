
## Background
There are diffences between the RPi4 and RPi5 GPIO hardware.  
The differences affect they way neopixels can be drive. 
On the RPi5, a plain user with the correct group membership can directly access the GPIO.
The rpi_ws281x library uses DMA, which writes to /dev/mem, to drive the neopixel on the RPi4.
The plain user needs sudoer privileges to access /dev/mem.
There is a fix or workaround, however.


# Claude Sonnet 4.6 suggestions 

This is a classic rpi_ws281x problem. The library needs `/dev/mem` because it uses DMA (Direct Memory Access) to achieve the precise timing neopixels require — and `/dev/mem` is root-only by default for good security reasons.

Here are your options, from best to worst:

---

## Option 1: Use `/dev/gpiomem` + PWM workaround (cleanest, but limited)

The `rpi_ws281x` library *can* use `/dev/gpiomem` instead of `/dev/mem` **if** you use the PCM or SPI backend instead of PWM. SPI is the easiest path:

**Wire your neopixel data line to GPIO 10 (SPI MOSI, pin 19)**, then in your Python code:

```python
import board
import neopixel

# Use SPI pin instead of a PWM pin
pixels = neopixel.NeoPixel(board.MOSI, NUM_PIXELS, ...)
```

Or with the lower-level rpi_ws281x directly:

```python
from rpi_ws281x import PixelStrip, ws
strip = PixelStrip(NUM_PIXELS, 10, channel=0,  # GPIO 10 = SPI
                   strip_type=ws.WS2811_STRIP_GRB)
```

Then add `pi` to the `spi` group (you likely already are) and ensure `/dev/spidev0.0` is accessible. **No root needed.**

---

## Option 2: `sudo` via a targeted sudoers rule (pragmatic)

Don't give `/dev/mem` open permissions — instead, allow `pi` to run *just this script* passwordlessly:

```bash
sudo visudo -f /etc/sudoers.d/neopixel
```

Add:

```
pi ALL=(ALL) NOPASSWD: /home/pi/yourdir/.venv/bin/python /home/pi/yourdir/neopixel.py
```

Then run it as:

```bash
sudo /home/pi/yourdir/.venv/bin/python /home/pi/yourdir/neopixel.py
```

Narrow, auditable, no broad privilege escalation.

---

## Option 3: `chmod`/`chgrp` on `/dev/mem` — **don't do this**

You'll see suggestions like:

```bash
sudo chmod o+rw /dev/mem   # ← dangerous, don't
```

This resets on every reboot anyway and opens a significant security hole. `/dev/mem` exposes raw physical memory — any process could read/write kernel memory, other processes' memory, hardware registers, etc.

---

## Option 4: `setcap` on the Python binary

Grant the specific Linux capability needed:

```bash
sudo setcap cap_sys_rawio+eip /home/pi/yourdir/.venv/bin/python3
```

`CAP_SYS_RAWIO` is what grants `/dev/mem` access. Then plain `python neopixel.py` works without sudo.

**Caveat:** This capability is granted to *that Python binary*, so any script run with that venv's Python gets it. Also, `setcap` strips `LD_LIBRARY_PATH` and some environment vars for security, which can occasionally cause import issues.

---

## Recommendation

| Situation | Best option |
|---|---|
| Can rewire to GPIO 10 | **Option 1** (SPI backend) — truly rootless |
| Must use PWM pin, security matters | **Option 2** (sudoers rule) |
| Must use PWM pin, convenience matters | **Option 4** (setcap) |
| Tempted by chmod | **Don't** |

The SPI backend (Option 1) is the "right" long-term fix — it sidesteps the `/dev/mem` requirement entirely by using the SPI peripheral's hardware timing instead of DMA through physical memory.

## The approach is the same, but the Pi4 has a gotcha

On both boards, the SPI backend avoids `/dev/mem` entirely. SPI only requires you to be in the `gpio` group to control LEDs without root — which you already are. So the concept transfers directly.

**The Pi4-specific gotcha:** On an RPi 4 you must set a fixed CPU frequency to prevent idle CPU scaling from changing the SPI clock frequency and breaking the WS281x timings.

Add these lines to `/boot/firmware/config.txt` (it's `/boot/config.txt` on older Raspberry Pi OS, but on Bookworm/Pi4 it's the firmware path):

```ini
core_freq=500
core_freq_min=500
```

Then reboot. Without this, you'll get glitchy or incorrect colors intermittently as the CPU scales its clock up and down.

---

## The other difference: library used

On the **Pi5**, `rpi_ws281x` doesn't work at all via its normal path — the underlying rpi_ws281x library needs substantial changes for Pi 5 — so on Pi5 you're forced to use `adafruit-circuitpython-neopixel-spi` (`neopixel_spi`) as a workaround.

On the **Pi4**, the original `rpi_ws281x` library works fine with SPI — you don't need to switch to the Adafruit CircuitPython library unless you prefer it. You just need to tell it to use GPIO 10 (SPI MOSI) and the SPI backend:

```python
from rpi_ws281x import PixelStrip, ws

strip = PixelStrip(
    NUM_PIXELS,
    10,                      # GPIO 10 = SPI0 MOSI
    strip_type=ws.WS2811_STRIP_GRB
)
strip.begin()
```

Or if you're using the Adafruit `neopixel_spi` layer (which works on Pi4 too):

```python
import board
import neopixel_spi as neopixel

spi = board.SPI()
pixels = neopixel.NeoPixel_SPI(spi, NUM_PIXELS, pixel_order=neopixel.GRB, auto_write=False)
```

---

## Checklist for Pi4 SPI neopixels as plain user

1. `sudo raspi-config` → Interface Options → SPI → Enable
2. Add `core_freq=500` and `core_freq_min=500` to `/boot/firmware/config.txt`
3. Reboot
4. Wire neopixel data to **GPIO 10** (physical pin 19)
5. Confirm `pi` is in the `spi` group: `groups pi`
6. Run without sudo ✓

