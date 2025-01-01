import os
import gc
import ssl
import wifi
import time
import socketpool
import adafruit_requests
import board
import displayio
import framebufferio
import rgbmatrix
import terminalio
import neopixel
import adafruit_display_text.label


# Release any existing displays
displayio.release_displays()

# Initialize the status LED
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.3, auto_write=True)
pixel.fill((0, 0, 255))

# Initialize the RGB matrix
matrix = rgbmatrix.RGBMatrix(
    width=64, height=32, bit_depth=3,  
    rgb_pins=[
        board.MTX_R1,
        board.MTX_G1,
        board.MTX_B1,
        board.MTX_R2,
        board.MTX_G2,
        board.MTX_B2
    ],
    addr_pins=[
        board.MTX_ADDRA,
        board.MTX_ADDRB,
        board.MTX_ADDRC,
        board.MTX_ADDRD
    ],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE
)

# Create the display using the RGB matrix
display = framebufferio.FramebufferDisplay(matrix)

# Configuration
TIKTOK_USERNAME = os.getenv('TIKTOK_USERNAME')
UPDATE_INTERVAL = 30  # seconds

# Connect to WiFi
print("Connecting to WiFi...")
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))
print(f"Connected to {os.getenv('CIRCUITPY_WIFI_SSID')}")

# Initialize requests
pool = socketpool.SocketPool(wifi.radio)
context = ssl.create_default_context()
requests = adafruit_requests.Session(pool, context)

def get_follower_count(username):
    """Fetch follower count from TikTok profile page"""
    try:
        pixel.fill((255, 255, 0))  # Yellow while fetching
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        url = f'https://www.tiktok.com/@{username}'
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            content = response.text
            follower_marker = '"followerCount":'
            if follower_marker in content:
                start_index = content.find(follower_marker) + len(follower_marker)
                end_index = content.find(",", start_index)
                if end_index != -1:
                    followers = int(content[start_index:end_index].strip())
                    pixel.fill((0, 255, 0))  # Green on success
                    return followers
        pixel.fill((255, 0, 0))  # Red on error
        return None
    except Exception as e:
        print(f"Error fetching followers: {e}")
        pixel.fill((255, 0, 0))  # Red on error
        return None
    finally:
        try:
            response.close()
        except:
            pass
        gc.collect()  # Added garbage collection

def format_number(num):
    """Format large numbers in a display-friendly way"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 100000:
        return f"{num/100000:.1f}K"
    return str(num)

def update_display(followers):
    """Update the Matrix display with new follower count"""
    group = displayio.Group()
    
    # Load the background bitmap
    background = displayio.OnDiskBitmap("/frame.bmp")
    bg_sprite = displayio.TileGrid(background, pixel_shader=background.pixel_shader)
    group.append(bg_sprite)
    
    # Create the follower count label
    label2 = adafruit_display_text.label.Label(
        terminalio.FONT,
        color=0xFF9500,
        text=format_number(followers)
    )
    # Center the follower count
    label2.anchor_point = (0.5, 0.5)
    label2.anchored_position = (48, 24)
    
    group.append(label2)
    display.root_group = group

# Main loop
while True:
    try:
        count = get_follower_count(TIKTOK_USERNAME)
        if count:
            update_display(count)
            print(f"Updated display with {count} followers")
        else:
            print("Failed to get follower count")
        time.sleep(UPDATE_INTERVAL)
    except Exception as Error:
        print(Error)
        time.sleep(10)
        gc.collect()
        time.sleep(5)
        microcontroller.reset()  # Reset on critical errors
