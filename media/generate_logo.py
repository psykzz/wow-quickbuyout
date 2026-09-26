"""Generates media/logo.png (512x512, 1:1) for CurseForge / Wago. Requires Pillow."""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

SIZE = 512
SS = 4  # supersampling factor
S = SIZE * SS
CENTER = S / 2


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def radial_gradient(size, inner, outer, center, radius):
    img = Image.new("RGBA", (size, size))
    px = img.load()
    cx, cy = center
    for y in range(size):
        for x in range(size):
            t = min(1.0, math.hypot(x - cx, y - cy) / radius)
            px[x, y] = lerp(inner, outer, t * t)
    return img


def build():
    # Gradients are computed at low resolution and upscaled for speed.
    lo = 256
    bg = radial_gradient(lo, (58, 36, 92, 255), (14, 10, 28, 255), (lo * 0.5, lo * 0.38), lo * 0.75)
    bg = bg.resize((S, S), Image.BICUBIC)

    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), radius=int(S * 0.18), fill=255)
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    canvas.paste(bg, (0, 0), mask)

    coin_r = S * 0.34
    coin_box = (CENTER - coin_r, CENTER - coin_r, CENTER + coin_r, CENTER + coin_r)

    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    g = S * 0.06
    ImageDraw.Draw(glow).ellipse(
        (coin_box[0] - g, coin_box[1] - g, coin_box[2] + g, coin_box[3] + g), fill=(255, 190, 60, 150)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(S * 0.05))
    canvas = Image.alpha_composite(canvas, glow)

    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    off = S * 0.02
    ImageDraw.Draw(shadow).ellipse(
        (coin_box[0] + off, coin_box[1] + off * 2, coin_box[2] + off, coin_box[3] + off * 2), fill=(0, 0, 0, 160)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(S * 0.02))
    canvas = Image.alpha_composite(canvas, shadow)

    coin_lo = radial_gradient(lo, (255, 226, 120, 255), (178, 102, 12, 255), (lo * 0.42, lo * 0.38), lo * 0.62)
    coin_face = coin_lo.resize((S, S), Image.BICUBIC)
    coin_mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(coin_mask).ellipse(coin_box, fill=255)
    coin_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    coin_layer.paste(coin_face, (0, 0), coin_mask)
    canvas = Image.alpha_composite(canvas, coin_layer)

    d = ImageDraw.Draw(canvas)
    rim = S * 0.022
    d.ellipse(coin_box, outline=(120, 70, 10, 255), width=int(rim))
    inner_r = coin_r * 0.82
    d.ellipse(
        (CENTER - inner_r, CENTER - inner_r, CENTER + inner_r, CENTER + inner_r),
        outline=(150, 90, 15, 200),
        width=int(S * 0.01),
    )

    def bolt(scale, dx=0.0, dy=0.0):
        pts = [(0.16, -0.66), (-0.40, 0.10), (-0.06, 0.10), (-0.18, 0.66), (0.40, -0.12), (0.06, -0.12)]
        return [(CENTER + (x * scale) + dx, CENTER + (y * scale) + dy) for x, y in pts]

    bolt_scale = coin_r * 1.0
    bolt_shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(bolt_shadow).polygon(bolt(bolt_scale, S * 0.012, S * 0.02), fill=(90, 45, 0, 210))
    bolt_shadow = bolt_shadow.filter(ImageFilter.GaussianBlur(S * 0.01))
    canvas = Image.alpha_composite(canvas, bolt_shadow)

    d = ImageDraw.Draw(canvas)
    d.polygon(bolt(bolt_scale), fill=(255, 252, 235, 255), outline=(120, 66, 8, 255), width=int(S * 0.008))

    highlight = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hx, hy, hw, hh = CENTER - coin_r * 0.55, CENTER - coin_r * 0.62, coin_r * 0.5, coin_r * 0.28
    ImageDraw.Draw(highlight).ellipse((hx - hw, hy - hh, hx + hw, hy + hh), fill=(255, 255, 255, 90))
    highlight = highlight.rotate(35, center=(hx, hy)).filter(ImageFilter.GaussianBlur(S * 0.03))
    highlight.putalpha(Image.composite(highlight.getchannel("A"), Image.new("L", (S, S), 0), coin_mask))
    canvas = Image.alpha_composite(canvas, highlight)

    return canvas.resize((SIZE, SIZE), Image.LANCZOS)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
    build().save(out, optimize=True)
    print(out)
