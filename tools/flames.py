#!/usr/bin/env python3
"""Lifelike Motion's own flames: an animated flame texture painted here (not the game's fire). Each frame is a
teardrop flame that sways and flickers: a white-hot core low in the middle, warming through gold and orange to red
tongues at the tips, with a soft glowing edge. The game blends between frames (interpolate), so it moves smoothly.

    flame_texture(pack, name, palette)  ->  writes textures/item/fire/<name>.png and its .mcmeta"""
import json
import math
import os

import numpy as np
from PIL import Image

N = 32        # pixels per frame side
FRAMES = 12

FIRE = [(255, 255, 236), (255, 244, 170), (255, 214, 92), (255, 168, 46), (246, 112, 30), (214, 62, 22),
        (150, 30, 16)]
SOUL = [(236, 255, 255), (178, 252, 255), (104, 232, 246), (52, 196, 222), (30, 150, 196), (22, 96, 160),
        (16, 52, 110)]


def _noise(x, y, t, seed):
    """smooth looping value noise"""
    v = 0.0
    for k, (fx, fy, ft, a) in enumerate(((1.3, 2.1, 1, 0.5), (2.7, 3.9, 2, 0.3), (5.1, 6.3, 3, 0.2))):
        v += a * math.sin(fx * x + fy * y + 2 * math.pi * ft * t + seed * (k + 1) * 1.7) * \
             math.cos(fy * 0.7 * x - fx * 0.5 * y + 2 * math.pi * ft * t * 0.5 + seed)
    return v


def frame(t, palette, seed=0.0):
    """one frame (t in 0..1 around the loop) as an RGBA array"""
    img = np.zeros((N, N, 4), dtype=np.uint8)
    for py in range(N):
        v = 1 - (py + 0.5) / N                       # 0 at the bottom, 1 at the top
        for px in range(N):
            u = (px + 0.5) / N * 2 - 1               # -1 .. 1 across
            sway = 0.16 * v * v * math.sin(2 * math.pi * t + v * 3.2 + seed) + 0.05 * v * _noise(0, v * 3, t, seed)
            width = 0.62 * (1 - v) ** 0.55 * math.sin(math.pi * min(1.0, v * 0.92 + 0.12)) ** 0.6
            # tongues licking up near the top
            width += 0.10 * v * max(0.0, _noise(u * 3, v * 4, t, seed + 1))
            d = abs(u - sway) / max(width, 1e-3)    # 0 in the middle, 1 at the flame's edge
            if d >= 1.0 or v > 0.97:
                continue
            heat = (1 - d) ** 1.4 * 0.62 + (1 - v) ** 1.5 * 0.42 + 0.1 * _noise(u * 4, v * 5, t, seed + 2)
            heat = min(max(heat, 0.0), 1.0)
            k = (1 - heat) * (len(palette) - 1)
            i0 = int(k)
            f = k - i0
            c0, c1 = np.array(palette[i0]), np.array(palette[min(i0 + 1, len(palette) - 1)])
            col = c0 * (1 - f) + c1 * f
            alpha = 255 if d < 0.8 else int(255 * (1 - (d - 0.8) / 0.2) * 0.9 + 25)   # a soft glowing edge
            if v > 0.8:
                alpha = int(alpha * (1 - (v - 0.8) / 0.17))
            img[py, px] = (*[int(c) for c in col], max(0, min(255, alpha)))
    return img


def flame_texture(pack, name, palette, seed=0.0):
    out = os.path.join(pack, "assets", "lifelikemotion", "textures", "item", "fire")
    os.makedirs(out, exist_ok=True)
    strip = np.concatenate([frame(i / FRAMES, palette, seed) for i in range(FRAMES)], axis=0)
    Image.fromarray(strip, "RGBA").save(os.path.join(out, name + ".png"))
    with open(os.path.join(out, name + ".png.mcmeta"), "w") as fh:
        json.dump({"animation": {"frametime": 2, "interpolate": True}}, fh)
    return f"lifelikemotion:item/fire/{name}"
