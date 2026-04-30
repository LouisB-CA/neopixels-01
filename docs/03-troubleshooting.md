
# Troubleshooting

## Common Problems

### Activating the venv
* You have to source the script
```bash
   source ./.venv/bin/activate
```

### Wiring
* This python does not use the same wiring as Rust programs.
* Be sure you are on GPIO 18
* Neopixels work fine on 3.3V or 5V
* Note that Data In is the short outside pin.

### Running as root
* You must use sudo and therefore you must specify the path to venv python
```bash
   sudo ./.venv/bin/python blinky.py
```

### Can't find the library
* If you get this message, see the "Running as root" section
```text

Traceback (most recent call last):
  File "/home/pi/prgms/Python/neopixel-01/blinky.py", line 9, in <module>
    from rpi_ws281x import PixelStrip, Color
ModuleNotFoundError: No module named 'rpi_ws281x'
```

