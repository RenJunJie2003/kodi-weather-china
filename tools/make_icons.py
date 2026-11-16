# -*- coding: utf-8 -*-
"""
tools/make_icons.py — 用 Pillow 生成插件自带的天气/预警图标与 artwork。

生成物全部写入 resources/media/，插件运行时零外部资源依赖。
仅开发时使用；Kodi 运行不需要 Pillow。
"""
from __future__ import unicode_literals

import math
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "resources", "media")
SIZE = 128

BLUE_SKY = (79, 195, 247, 255)
SUN = (255, 202, 40, 255)
CLOUD = (236, 240, 245, 255)
CLOUD_DARK = (176, 190, 205, 255)
RAIN = (41, 121, 255, 255)
SNOW = (255, 255, 255, 255)
GRAY = (144, 164, 186, 255)
LIGHTNING = (255, 214, 0, 255)
SAND = (214, 168, 88, 255)

LEVEL_COLORS = {
    "blue": (46, 124, 246, 255),
    "yellow": (245, 197, 24, 255),
    "orange": (238, 138, 23, 255),
    "red": (217, 48, 37, 255),
    "unknown": (154, 160, 166, 255),
}


def new_canvas(size=SIZE):
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def sun(draw, cx, cy, radius, color=SUN, rays=True):
    if rays:
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = cx + math.cos(rad) * (radius + 6)
            y1 = cy + math.sin(rad) * (radius + 6)
            x2 = cx + math.cos(rad) * (radius + 16)
            y2 = cy + math.sin(rad) * (radius + 16)
            draw.line([x1, y1, x2, y2], fill=color, width=5)
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)


def cloud(draw, cx, cy, scale=1.0, color=CLOUD, outline=CLOUD_DARK):
    r = 20 * scale
    boxes = [
        (cx - 34 * scale, cy - 6 * scale, cx + 34 * scale, cy + 20 * scale),
        (cx - 24 * scale, cy - 22 * scale, cx + 2 * scale, cy + 20 * scale),
        (cx + 2 * scale, cy - 28 * scale, cx + 30 * scale, cy + 20 * scale),
    ]
    draw.rounded_rectangle(boxes[0], radius=int(10 * scale), fill=color)
    draw.ellipse([cx - 24 * scale, cy - 22 * scale, cx + 2 * scale, cy + 20 * scale], fill=color)
    draw.ellipse([cx + 2 * scale, cy - 28 * scale, cx + 30 * scale, cy + 20 * scale], fill=color)
    draw.line([cx - 30 * scale, cy + 19 * scale, cx + 30 * scale, cy + 19 * scale],
              fill=outline, width=max(1, int(2 * scale)))


def drops(draw, count, width=6, color=RAIN, slant=8):
    gap = SIZE // (count + 1)
    for i in range(count):
        x = gap * (i + 1)
        y = 84 + (i % 2) * 6
        draw.line([x, y, x - slant, y + 20], fill=color, width=width)


def flakes(draw, count, color=SNOW, size=7):
    gap = SIZE // (count + 1)
    for i in range(count):
        x = gap * (i + 1)
        y = 88 + (i % 2) * 8
        for angle in (0, 60, 120):
            rad = math.radians(angle)
            dx, dy = math.cos(rad) * size, math.sin(rad) * size
            draw.line([x - dx, y - dy, x + dx, y + dy], fill=color, width=3)


def marks(draw, text_color=(255, 255, 255, 255)):
    """问号 / 感叹号（用几何图形，避免依赖字体文件）。"""
    draw.rounded_rectangle([52, 34, 76, 78], radius=12, fill=text_color)
    draw.ellipse([56, 88, 72, 104], fill=text_color)


def weather_icon(kind):
    image = new_canvas()
    d = ImageDraw.Draw(image)
    if kind == "sunny":
        sun(d, 64, 64, 28)
    elif kind == "partly_cloudy":
        sun(d, 42, 42, 20)
        cloud(d, 76, 76, 0.95)
    elif kind in ("cloudy", "overcast"):
        cloud(d, 64, 60, 1.15, color=CLOUD if kind == "cloudy" else (198, 208, 220, 255))
        if kind == "overcast":
            cloud(d, 50, 78, 0.7, color=(168, 182, 198, 255))
    elif kind in ("rain", "light_rain", "heavy_rain", "shower"):
        cloud(d, 64, 52, 1.0)
        n = {"light_rain": 2, "shower": 3, "rain": 3, "heavy_rain": 5}[kind]
        drops(d, n, width=6 if kind != "heavy_rain" else 8)
    elif kind == "thunderstorm":
        cloud(d, 64, 50, 1.0, color=(198, 208, 220, 255))
        d.polygon([(62, 72), (48, 104), (62, 104), (54, 124),
                   (84, 88), (68, 88), (80, 72)], fill=LIGHTNING)
    elif kind == "hail":
        cloud(d, 64, 50, 1.0)
        for x, y in ((38, 90), (62, 98), (86, 88)):
            d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=SNOW, outline=CLOUD_DARK, width=2)
    elif kind == "sleet":
        cloud(d, 64, 50, 1.0)
        drops(d, 2, width=5)
        flakes(d, 2)
    elif kind in ("snow", "light_snow", "heavy_snow"):
        cloud(d, 64, 50, 1.0)
        flakes(d, {"light_snow": 2, "snow": 3, "heavy_snow": 5}[kind])
    elif kind in ("fog", "haze", "wind"):
        for i, y in enumerate((38, 56, 74, 92)):
            x0 = 18 + (i % 2) * 12
            d.rounded_rectangle([x0, y, 110 - (i % 2) * 8, y + 8], radius=4,
                                fill=(214, 224, 234, 255) if kind == "fog" else GRAY)
        if kind == "haze":
            for x, y in ((30, 24), (58, 18), (90, 26)):
                d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=SAND)
    elif kind == "dust":
        for i, y in enumerate((42, 62, 82)):
            d.arc([12 + i * 6, y - 16, 116 - i * 6, y + 18], 0, 180, fill=SAND, width=7)
        d.ellipse([76, 34, 104, 62], fill=SAND)
    elif kind == "frost":
        flakes(d, 1, color=BLUE_SKY, size=16)
        d.rounded_rectangle([24, 96, 104, 104], radius=4, fill=(180, 225, 255, 255))
    else:
        d.ellipse([14, 14, 114, 114], fill=(96, 110, 128, 255))
        marks(d)
    return image


def alert_icon(level):
    image = new_canvas()
    d = ImageDraw.Draw(image)
    color = LEVEL_COLORS.get(level, LEVEL_COLORS["unknown"])
    d.rounded_rectangle([8, 8, 120, 120], radius=26, fill=color)
    # 三角警示牌
    d.polygon([(64, 24), (110, 102), (18, 102)], fill=(255, 255, 255, 235))
    d.polygon([(64, 38), (98, 94), (30, 94)], fill=color)
    d.rounded_rectangle([60, 54, 68, 78], radius=4, fill=(255, 255, 255, 255))
    d.ellipse([59, 84, 69, 94], fill=(255, 255, 255, 255))
    return image


def addon_icon():
    size = 256
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    d.ellipse([8, 8, 248, 248], fill=(25, 108, 186, 255))
    d.ellipse([8, 8, 248, 248], outline=(255, 255, 255, 90), width=6)
    sun(d, 88, 86, 30)
    cloud(d, 148, 158, 2.05)
    for x, y in ((76, 190), (112, 204), (150, 198)):
        d.line([x, y, x - 10, y + 20], fill=RAIN, width=9)
    return image


def fanart():
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), (12, 58, 110))
    d = ImageDraw.Draw(image)
    for y in range(height):
        t = y / float(height)
        r = int(18 + 62 * t)
        g = int(96 + 78 * t)
        b = int(170 + 40 * t)
        d.line([(0, y), (width, y)], fill=(r, g, b))
    sun(d, 1030, 170, 78, color=(255, 214, 92, 255), rays=True)
    cloud(d, 300, 250, 3.2, color=(232, 240, 248, 220),
          outline=(210, 224, 238, 220))
    cloud(d, 820, 420, 2.4, color=(214, 228, 242, 190),
          outline=(200, 216, 234, 190))
    for i in range(8):
        x = 120 + i * 140
        d.line([(x, 560), (x - 24, 610)], fill=(150, 200, 245), width=8)
    return image.convert("RGB")


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    kinds = ["sunny", "partly_cloudy", "cloudy", "overcast", "shower",
             "thunderstorm", "hail", "sleet", "rain", "light_rain",
             "heavy_rain", "snow", "light_snow", "heavy_snow", "fog",
             "haze", "dust", "frost", "wind", "unknown"]
    for kind in kinds:
        weather_icon(kind).save(os.path.join(OUT, kind + ".png"))
    for level in LEVEL_COLORS:
        alert_icon(level).save(os.path.join(OUT, "alert_%s.png" % level))
    addon_icon().save(os.path.join(ROOT, "icon.png"))
    fanart().save(os.path.join(ROOT, "fanart.jpg"), quality=88)
    print("图标生成完成：%d 个天气图标 + %d 个预警图标 + icon.png + fanart.jpg"
          % (len(kinds), len(LEVEL_COLORS)))


if __name__ == "__main__":
    main()
