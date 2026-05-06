#!/usr/bin/env python3
"""Display DMX UI status on framebuffer screen"""
import time
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np

FB_DEVICE = "/dev/fb0"
WIDTH = 480
HEIGHT = 320

def create_ui_image():
    """Create simple UI display"""
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(18, 20, 23))
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_large = ImageFont.load_default()
        font_med = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Title
    draw.text((20, 20), "LASER DMX", fill=(107, 177, 255), font=font_large)
    
    # Status
    try:
        r = requests.get("http://localhost:8080/status", timeout=1)
        status = r.json()
        status_text = status.get('status', 'Unknown')
    except:
        status_text = "Connecting..."
    
    draw.text((20, 70), f"Status: {status_text}", fill=(242, 245, 249), font=font_small)
    
    # Instructions
    y = 120
    draw.text((20, y), "Connect from browser:", fill=(170, 179, 190), font=font_med)
    draw.text((20, y+35), "http://10.0.0.84:8080", fill=(107, 177, 255), font=font_large)
    
    draw.text((20, HEIGHT-40), "System Ready", fill=(170, 179, 190), font=font_small)
    
    return img

def rgb888_to_rgb565(img):
    """Convert RGB888 to RGB565 format"""
    arr = np.array(img)
    r = (arr[:,:,0] >> 3).astype(np.uint16)
    g = (arr[:,:,1] >> 2).astype(np.uint16)
    b = (arr[:,:,2] >> 3).astype(np.uint16)
    rgb565 = (r << 11) | (g << 5) | b
    return rgb565.astype('<u2').tobytes()

def main():
    """Display UI on framebuffer"""
    print("Starting framebuffer UI display...")
    
    try:
        with open(FB_DEVICE, 'wb') as fb:
            while True:
                img = create_ui_image()
                fb_data = rgb888_to_rgb565(img)
                fb.seek(0)
                fb.write(fb_data)
                fb.flush()
                time.sleep(5)  # Update every 5 seconds
    except KeyboardInterrupt:
        print("\nStopping framebuffer display")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
