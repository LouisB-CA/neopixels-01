#!/usr/bin/env python3
"""
NeoPixel Color Verification - verify_rgb.py
Requires RGB values as positional arguments (0-255 each).
"""

import argparse
import functools
import time
import signal
import os, sys

try:
    from rpi_ws281x import PixelStrip, Color
except ModuleNotFoundError as e:
    print(f"Error: {e}", file=sys.stderr)
    print(f"\nDid you `source ./.venv/bin/activate` into your virtual environment?\n",
          file=sys.stderr)
    sys.exit(1)


# NeoPixel configuration
LED_COUNT      = 1        # Number of LED pixels
LED_PIN        = 18       # GPIO pin connected to the pixels (must support PWM!)
LED_FREQ_HZ    = 800000   # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10       # DMA channel to use for generating signal
LED_BRIGHTNESS = 32       # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0        # PWM channel

# Global strip object for signal handler cleanup
strip = None


def parse_args():
    """Parse and validate positional RGB arguments (0-255 each) and optional --duration.
    Returns a tuple (r, g, b, duration).
    """
    parser = argparse.ArgumentParser(
        description="Light a single NeoPixel with the given RGB color.",
        usage=f"sudo ./.venv/bin/python {os.path.basename(__file__)} R G B [--duration DURATION]",
        epilog="R, G, B must each be integers in the range 0-255. DURATION must be a positive float.",
    )
    parser.add_argument("r", type=int, metavar="R", help="Red   component (0-255)")
    parser.add_argument("g", type=int, metavar="G", help="Green component (0-255)")
    parser.add_argument("b", type=int, metavar="B", help="Blue  component (0-255)")
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        metavar="DURATION",
        help="Duration in seconds to hold the color (default: 5.0)",
    )

    args = parser.parse_args()

    errors = []
    for name, val in (("R", args.r), ("G", args.g), ("B", args.b)):
        if not (0 <= val <= 255):
            errors.append(f"  {name}={val} is out of range (0-255)")
    if args.duration <= 0:
        errors.append(f"  --duration={args.duration} must be a positive value")

    if errors:
        parser.print_usage(sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    return args.r, args.g, args.b, args.duration


def signal_handler(sig, frame):
    """Handle Ctrl+C and termination signals gracefully."""
    print("\nExiting...", file=sys.stderr)
    if strip:
        strip.setPixelColor(0, Color(0, 0, 0))
        strip.show()
    sys.exit(0)


def main():
    global strip

    r, g, b, duration  = parse_args()

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and initialise NeoPixel strip
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                       LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    try:
        strip.begin()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"Usage: sudo ./.venv/bin/python {os.path.basename(__file__)} R G B",
              file=sys.stderr)
        sys.exit(1)

    try:
        # Ensure pixel is off before we start
        strip.setPixelColor(0, Color(0, 0, 0))
        strip.show()

        print("NeoPixel Color Verification")
        print("=" * 50)
        print(f"Setting color  R={r}  G={g}  B={b}")

        # Apply the requested color
        strip.setPixelColor(0, Color(g, r, b))
        strip.show()

        # Hold the color so it can be visually verified
        time.sleep(duration)

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)

    finally:
        # Always turn the pixel off on exit
        if strip:
            strip.setPixelColor(0, Color(0, 0, 0))
            strip.show()
        print("NeoPixel off")


if __name__ == '__main__':
    print = functools.partial(print, flush=True)
    main()


