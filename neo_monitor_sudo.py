#!/usr/bin/env python3
"""
NeoPixel Voltage Monitor Sudo Version - neo_monitor_sudo.py
Reads current and voltage data from SQLite database and displays on NeoPixel
Color gradient: Blue (0V) -> Cyan -> Green -> Yellow -> Red (19V)
Color gradient: Blue (0.35A) -> Cyan -> Green -> Yellow -> Red (0.50A)
Based on code provided by Claude Sonnet 4.5 (2025-01-20)
"""

import time
import functools
import sqlite3
import signal
import os, sys
import colorsys
try :
    from rpi_ws281x import PixelStrip, Color
except ModuleNotFoundError as e:
    print(f"Error: {e}")
    print(f"\nDid you `source ./.venv/bin/activate` into your virtual environment?\n")
    sys.exit(0)


# NeoPixel configuration
LED_COUNT = 1           # Number of LED pixels
LED_PIN = 18           # GPIO pin connected to the pixels (must support PWM!)
LED_FREQ_HZ = 800000   # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10           # DMA channel to use for generating signal
LED_BRIGHTNESS = 32    # Set to 0 for darkest and 255 for brightest
LED_INVERT = False     # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0        # PWM channel

# Voltage to color mapping
MAX_VOLTAGE = 19.0     # Red at 19V
MIN_VOLTAGE = 0.0      # Blue at 0V

# Current to color mapping
MAX_CURRENT = 0.50     # Red at 0.5A
MIN_CURRENT = 0.35     # Blue at 0.35A

# Global strip object for cleanup
strip = None

def signal_handler(sig, frame):
    """Handle Ctrl+C and termination signals"""
    print("\nExiting...")
    if strip:
        strip.setPixelColor(0, Color(0, 0, 0))
        strip.show()
    sys.exit(0)

class ColorMapper :
    def __init__(self) :
        self.previous_value = 0
        self.previous_band = 6          # bands are numbered 0 to 6
        self.break_points = [ 1000, 480, 460, 420, 400, 385, 100, -100 ]
        self.rgb = [ (128, 0, 0), (128, 15, 0), (128, 35, 0), (40, 40, 40),
                        (0, 96, 96), (0, 0, 255), (0, 128, 0) ]
        self.name = [   "red",     "red-orange", "orange",   "white",
                             "cyan",     "blue",     "green" ]
        
    def current_to_color(self, val) :
        # convert current to color with hsyteresis
        val = int( 1000*val + 0.5 )         # round off to milliamps
        val = max(min(1000, val), 0)        # limit to 0-1000mA
        breaks = self.break_points[::]      # slice copy

        if val == self.previous_value :                 # constant
            r, g, b = self.rgb[self.previous_band]
            return self.name[self.previous_band], Color(g, r, b)
        
        elif val > self.previous_value :                # rising
            breaks[self.previous_band] += 2             # widen the band more at the top

        else :                                          # falling
            breaks[self.previous_band+1] -= 2           # widen the band more at the bottom
        
        for band in range(7) :
            if val > breaks[band+1] :
                r, g, b = self.rgb[band]
                self.previous_band = band
                self.previous_value = val
                return self.name[band], Color(g, r, b)
        
        return Color(0, 0, 0)

# endof class ColorMapper

def old_current_to_color(current):
    """
    Convert current to RGB color using HSV color space
    Blue (240°) at 0.35A -> Red (0°) at 0.4A
    
    Args:
        current: Current value (0.35-0.50A)
    
    Returns:
        Color object for NeoPixel (GRB format)
    """
    # Clamp current to valid range
    current = max(MIN_CURRENT, min(current, MAX_CURRENT))
    
    # Normalize to 0-1 range
    normalized = current / MAX_CURRENT
    
    # Map to hue: 240° (blue) at 0.35A to 0° (red) at 0.40A
    # HSV hue is 0-1 range where 0=red, 0.66=blue
    # We want to go from blue (0.66) to red (0.0/1.0)
    hue = 0.66 * (1.0 - normalized)  # 0.66 -> 0.0 as current increases
    
    # Full saturation and value for vibrant colors
    saturation = 1.0
    value = 1.0
    
    # Convert HSV to RGB
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    
    # Convert to 0-255 range and return as Color (note: GRB format)
    return Color(int(g * 255), int(r * 255), int(b * 255))

def voltage_to_color(voltage):
    """
    Convert voltage to RGB color using HSV color space
    Blue (240°) at 0V -> Red (0°) at 19V
    
    Args:
        voltage: Voltage value (0-19V)
    
    Returns:
        Color object for NeoPixel (GRB format)
    """
    # Clamp voltage to valid range
    voltage = max(MIN_VOLTAGE, min(voltage, MAX_VOLTAGE))
    
    # Normalize to 0-1 range
    normalized = voltage / MAX_VOLTAGE
    
    # Map to hue: 240° (blue) at 0V to 0° (red) at 19V
    # HSV hue is 0-1 range where 0=red, 0.66=blue
    # We want to go from blue (0.66) to red (0.0/1.0)
    hue = 0.66 * (1.0 - normalized)  # 0.66 -> 0.0 as voltage increases
    
    # Full saturation and value for vibrant colors
    saturation = 1.0
    value = 1.0
    
    # Convert HSV to RGB
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    
    # Convert to 0-255 range and return as Color (note: GRB format)
    return Color(int(g * 255), int(r * 255), int(b * 255))

def get_latest_database(base_path="/home/pi/prgms/Python/jumpack-01/databases"):
    """
    Find the most recent database file matching the pattern
    Returns the full path to the database
    """
    import glob
    import os
    
    pattern = os.path.join(base_path, "jumpack_*.db")
    db_files = glob.glob(pattern)
    
    if not db_files:
        raise FileNotFoundError(f"No database files found matching {pattern}")
    
    # Get the most recent file
    latest_db = max(db_files, key=os.path.getmtime)
    return latest_db

def main():
    global strip
    cmap = ColorMapper()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create NeoPixel object
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, 
                      LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    
    # Initialize the library
    try :
        strip.begin()
    except RuntimeError as e:
        print(f"Error: {e}")
        print(f"\nUsage:  sudo ./.venv/bin/python {os.path.basename(__file__)}")
        sys.exit(1)

    
    # Turn off initially
    strip.setPixelColor(0, Color(0, 0, 0))
    strip.show()
    
    print("NeoPixel Current Monitor")
    print("=" * 50)
    
    try:
        # Find and open database
        db_path = get_latest_database()
        print(f"Database: {db_path}")
        print()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query all readings ordered by timestamp
        cursor.execute("""
            SELECT timestamp, bus_voltage_v, current_a 
            FROM readings 
            ORDER BY timestamp
        """)
        
        rows = cursor.fetchall()
        print(f"Found {len(rows)} records")
        print()
        print(f"{'Timestamp':<24} {'Current (A)':<12} {'Color'}")
        print("-" * 60)
        
        # Display each record on the NeoPixel
        for timestamp, voltage, current in rows[::5] :
            # Handle None values
            if voltage is None:
                voltage = 0.0
            
            # Convert voltage to color
            color_name, color = cmap.current_to_color(current)
            
            # Update NeoPixel
            strip.setPixelColor(0, color)
            strip.show()
            
            print(f"{timestamp:.19}      {current:>11.6f}  {color_name}")
            
            # Delay between records
            time.sleep(0.25)
        
        print()
        print("Playback complete")
        
        # Close database
        conn.close()
        
        # Keep last color displayed for a moment
        time.sleep(2)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Turn off NeoPixel
        if strip:
            strip.setPixelColor(0, Color(0, 0, 0))
            strip.show()
        print("NeoPixel off")

if __name__ == '__main__':
    print = functools.partial(print, flush=True)
    main()


