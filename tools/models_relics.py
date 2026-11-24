#!/usr/bin/env python3
"""Batch 10 of Lifelike Motion's 3D items: smithing templates and pottery sherds (built with tools/models.py's
parts and painter; run tools/models.py to write them). Both are held up facing you.

A template is an ancient stone tablet with chipped edges, its trim's emblem cut into the face and inlaid with
glowing crystal. A sherd is a broken piece of a decorated pot: thick fired clay with a jagged outline and its
picture painted in the clay's own colours. Both are built from rows one pixel tall, so the outline can be chipped
anywhere, and their faces are painted from where each texel sits."""
import colorsys
import io
import random
import re
import zipfile
import zlib

import numpy as np
from PIL import Image

from models import Mat, Model, upright, JAR
from models_discs import ramp, face_paint

HELD = dict(scale=0.42, lift=6.5)
CRYSTAL = ["0a4a50", "127478", "1c9ea0", "36c4c4", "7ae4e0", "c8fff8"]   # the glowing inlay
TERRACOTTA = ["3a1c14", "4e281e", "643428", "7a4232", "92523e", "aa684e", "c4845e"]


def jar_image(path):
    with zipfile.ZipFile(JAR) as z:
        return np.array(Image.open(io.BytesIO(z.read(path))).convert("RGBA")).astype(float)


def lum(px):
    return px[..., 0] * 0.3 + px[..., 1] * 0.59 + px[..., 2] * 0.11


def rows_slab(m, mat, x0, x1, y0, y1, z0, z1, inset, paint, back=None, edge=1.0):
    """a flat slab standing up, built from rows one pixel tall; inset(row) -> (left, right) chips its outline;
    paint(x, y, k) colours its front from where each texel sits (back(x, y, k) its back)"""
    for n, y in enumerate(np.arange(y0, y1, 1.0)):
        l, r = inset(n)
        a, b = x0 + l, x1 - r
        if b - a < 0.5:
            continue

        def f(rr, ang, k, x, yy, n=n):
            return paint(x, yy, k)
        dec = face_paint(8, 8, a, b, y, y + 1, f, edge)
        if back:
            front = dec

            def dec(k, ii, jj, w, h, face, front=front, a=a, b=b, y=y):
                if face == "north":
                    x = b - (ii + 0.5) / w * (b - a)
                    return back(x, y + 1 - (jj + 0.5) / h, k)
                return front(k, ii, jj, w, h, face)
        m.box((a, y, z0), (b, y + 1, z1), mat, decal=dec, ao=False)


def profile(rnd, n, lo, hi, points=4):
    """an edge that wanders in and out: random insets at a few points down it, joined by straight lines and
    rounded to half pixels (broken, not sawn)"""
    ks = np.linspace(0, n - 1, points)
    vs = [rnd.uniform(lo, hi) for _ in ks]
    return [round(float(np.interp(i, ks, vs)) * 2) / 2 for i in range(n)]


def chips(seed, n, corner=1.0, rough=1.0):
    """a worn tablet's outline: rounded corners and gently uneven sides"""
    rnd = random.Random(seed)
    left, right = profile(rnd, n, 0, rough, 5), profile(rnd, n, 0, rough, 5)
    for i in (0, n - 1):
        left[i] += corner
        right[i] += corner
    return lambda i: (left[i], right[i])


# ---------------------------------------------------------------- smithing templates
def template(name):
    px = jar_image(f"assets/minecraft/textures/item/{name}.png")
    alpha = px[..., 3] > 0
    hsv = np.array([[colorsys.rgb_to_hsv(*(c / 255 for c in p[:3])) for p in row] for row in px])
    cyan = alpha & (hsv[..., 0] > 0.42) & (hsv[..., 0] < 0.56)
    emblem = cyan & (hsv[..., 1] > 0.3)                                  # the emblem: its cyan pixels
    if emblem.sum() > 0.4 * alpha.sum():                                 # (a cyan tablet: only the vivid ones)
        emblem = cyan & (hsv[..., 1] > 0.56)
    ys, xs = np.nonzero(alpha)
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    W, H = bx1 - bx0, by1 - by0
    stone_px = px[alpha & ~emblem][:, :3]
    med = np.median(stone_px, axis=0)
    pal = ramp("%02x%02x%02x" % tuple(int(c) for c in med), 7)
    x0, y0 = 8 - W / 2, 1.0
    x1, y1 = x0 + W, y0 + H
    groove = np.zeros_like(emblem)                       # the cut round the emblem
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        groove |= np.roll(np.roll(emblem, dy, 0), dx, 1)
    groove &= ~emblem
    rnd = np.random.default_rng(zlib.crc32(name.encode()))
    speck = rnd.random((16, 16))

    def at(x, y):
        """the template picture's pixel under a point"""
        i = np.clip((np.floor(x - x0) + bx0).astype(int), 0, 15)
        j = np.clip((np.floor(y1 - y) + by0).astype(int), 0, 15)
        return i, j

    def front(x, y, k):
        i, j = at(x, y)
        k = 3.0 + 1.2 * (y - y0) / H - 0.6                                   # lighter toward the top
        k = k + np.where(speck[j, i] < 0.12, 0.9, 0) - np.where(speck[j, i] > 0.9, 0.8, 0)
        k = np.where(groove[j, i] | emblem[j, i], 1.0, k)                    # the cut lines are in shadow
        return k

    def back(x, y, k):
        i, j = at(x, y)
        return 2.4 + 0.8 * (y - y0) / H + np.where(speck[j, i] < 0.15, 0.8, 0)
    m = Model(name)
    stone = Mat(pal, base=3, bevel=0, grad=0)
    rows_slab(m, stone, x0, x1, y0, y1, 7.0, 9.2, chips(name, int(H)), front, back, edge=2.0)
    # the inlay: glowing crystal set into the emblem, shaded like the picture's own emblem
    lit = lum(px)

    def inlay(k, ii, jj, w, h, face):
        e = emblem[by0 + jj, bx0 + ii]
        light = lit[by0 + jj, bx0 + ii]
        k = np.where(e, 2.0 + 3.0 * (light - 90) / 150, 0)
        return k, e.astype(float)
    m.box((x0, y0, 9.2), (x1, y1, 9.3), Mat(CRYSTAL, base=3, bevel=0, grad=0, glow=True, shade=False),
          faces=("south",), decal=inlay, ao=False)
    m.write(upright(**HELD), particle=f"minecraft:item/{name}", unlit=True)


# ---------------------------------------------------------------- pottery sherds
def sherd(name):
    pattern = name.replace("_pottery_sherd", "_pottery_pattern")
    px = jar_image(f"assets/minecraft/textures/entity/decorated_pot/{pattern}.png")
    L = lum(px)
    alpha = px[..., 3] > 0
    ys, xs = np.nonzero(alpha)
    bx0, bx1 = xs.min(), xs.max() + 1
    W = bx1 - bx0
    lo, hi = np.percentile(L[alpha], 5), np.percentile(L[alpha], 95)
    x0, x1 = 8 - W / 2, 8 + W / 2
    y0, y1 = 2.0, 14.0                                   # the pot side's picture, rows 2..13

    def at(x, y):
        i = np.clip((np.floor(x - x0) + bx0).astype(int), 0, 15)
        j = np.clip((np.floor(y1 - y) + 2).astype(int), 0, 15)
        return i, j

    def front(x, y, k):
        i, j = at(x, y)
        return 0.6 + 5.4 * (L[j, i] - lo) / max(hi - lo, 1)               # the picture, in fired-clay colours

    def back(x, y, k):
        return np.full_like(x, 2.2)                      # the inside of the pot: plain clay
    rnd = random.Random(name)
    n = int(y1 - y0)
    # a broken outline: each side wanders in and out, and a corner is broken off top and bottom at a slant
    left, right = profile(rnd, n, 0, 2.5), profile(rnd, n, 0, 2.5)
    top, bottom = (left, right) if rnd.random() < 0.5 else (right, left)
    for i, cut in enumerate((4.5, 3.0, 1.5)):
        top[i] += cut
        bottom[n - 1 - i] += cut - 1.0
    m = Model(name)
    clay = Mat(TERRACOTTA, base=3, bevel=0, grad=0)
    rows_slab(m, clay, x0, x1, y0, y1, 7.2, 8.8, lambda i: (left[i], right[i]), front, back, edge=1.6)
    m.write(upright(**HELD), particle=f"minecraft:item/{name}")


def _names(pattern):
    with zipfile.ZipFile(JAR) as z:
        return sorted(n.split("/")[-1][:-5] for n in z.namelist()
                      if re.match(rf"assets/minecraft/models/item/.*{pattern}\.json$", n))


RELICS = {n: (lambda n=n: template(n)) for n in _names("smithing_template")}
RELICS.update({n: (lambda n=n: sherd(n)) for n in _names("pottery_sherd")})
