import math
from PIL import Image, ImageDraw, ImageFilter

# 1. Animated Halo Icon
def create_halo_gif(filename, size=128, frames=20):
    images = []
    for i in range(frames):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Pulsing effect
        pulse = 0.7 + 0.3 * math.sin(2 * math.pi * i / frames)
        halo_width = int(16 * pulse)
        halo_color = (120, 180, 255, int(120 * pulse))  # Light blue, semi-transparent
        # Draw outer glow
        for r in range(halo_width, 0, -2):
            alpha = int(80 * (r / halo_width))
            draw.ellipse(
                [size//2 - 40 - r, size//2 - 40 - r, size//2 + 40 + r, size//2 + 40 + r],
                outline=(180, 200, 220, alpha)
            )
        # Draw main halo
        draw.ellipse(
            [size//2 - 40, size//2 - 40, size//2 + 40, size//2 + 40],
            outline=halo_color, width=halo_width
        )
        # Optional: blur for extra softness
        img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
        images.append(img)
    images[0].save(filename, save_all=True, append_images=images[1:], duration=60, loop=0, disposal=2)

# 2. Loading Spinner
def create_spinner_gif(filename, size=64, frames=12, dots=8):
    images = []
    for i in range(frames):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        for d in range(dots):
            angle = 2 * math.pi * (d / dots) + 2 * math.pi * (i / frames)
            x = size // 2 + int(22 * math.cos(angle))
            y = size // 2 + int(22 * math.sin(angle))
            # Fade tail dots
            fade = int(255 * (0.3 + 0.7 * ((d + i) % dots) / dots))
            color = (120, 180, 255, fade) if d == 0 else (180, 190, 200, fade)
            draw.ellipse([x-6, y-6, x+6, y+6], fill=color)
        images.append(img)
    images[0].save(filename, save_all=True, append_images=images[1:], duration=60, loop=0, disposal=2)

if __name__ == "__main__":
    create_halo_gif("halo_icon.gif")
    create_spinner_gif("loading_spinner.gif")
    print("GIFs created: halo_icon.gif, loading_spinner.gif") 