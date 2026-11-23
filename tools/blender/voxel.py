#!/usr/bin/env python3
"""Minecraft's own item pictures built out into 3D: every pixel of the vanilla sprite becomes a little column, thicker
toward the middle of each shape (so a blade gets a ridge and an apple gets round), brighter pixels standing slightly
proud of darker ones (so the sprite's own shading becomes real relief). Blender then bakes soft shadows where columns
step down and lighter worn edges along every rim into the mesh's vertex colours: the item keeps its exact Minecraft
look, now solid and lit.

Runs with Blender's Python module:  python3 tools/blender/voxel.py <pack dir> [names...] [--preview out.png]
"""
import io
import math
import os
import sys
import zipfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import items as K  # noqa: E402  (loads Blender)
import bpy  # noqa: E402
import bmesh  # noqa: E402

JAR = os.environ.get("MC_JAR", "/tmp/mcjar/client.jar")
_jar = zipfile.ZipFile(JAR)


def sprite(name):
    """a vanilla item picture as an RGBA array (first frame of animated ones)"""
    im = Image.open(io.BytesIO(_jar.read(f"assets/minecraft/textures/item/{name}.png"))).convert("RGBA")
    return np.array(im.crop((0, 0, im.width, im.width)), dtype=np.float64) / 255.0


def linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# ---------------------------------------------------------------- vanilla's own ways of holding items
def held(handheld, fp_scale=0.52, fp_lift=4.6, fp_back=-1.2, fp_side=1.6):
    """vanilla's own ways of holding items, but held a little smaller and higher in first person so the whole 3D
    shape shows (our hands animate it from there)"""
    def fp(sx):
        return {"rotation": [0, -90 * sx, 25 * sx], "translation": [fp_side, fp_lift, fp_back], "scale": [fp_scale] * 3}
    tp = ({"rotation": [0, -90, 55], "translation": [0, 4.0, 0.5], "scale": [0.85] * 3},
          {"rotation": [0, 90, -55], "translation": [0, 4.0, 0.5], "scale": [0.85] * 3}) if handheld else \
         ({"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.55] * 3},
          {"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.55] * 3})
    return {
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
        "thirdperson_righthand": tp[0], "thirdperson_lefthand": tp[1],
        "firstperson_righthand": fp(1), "firstperson_lefthand": fp(-1),
        "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
    }


# ---------------------------------------------------------------- shaping
def depth_map(solid, lum, base=1.0, grow=0.6, cap=4, relief=0.0, relief_cap=0.12):
    """half-thickness of every pixel column, in pixels: rounder toward the middle of each shape, with the sprite's
    light pixels raised and its dark ones sunk"""
    n = solid.shape[0]
    # steps to the nearest empty pixel (or the picture's border)
    d = np.where(solid, 99, 0)
    changed = True
    while changed:
        changed = False
        for y in range(n):
            for x in range(n):
                if not solid[y, x]:
                    continue
                best = 1 + min(d[y + dy, x + dx] if 0 <= y + dy < n and 0 <= x + dx < n else 0
                               for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if best < d[y, x]:
                    d[y, x] = best
                    changed = True
    # a thin rim, a thicker body, and the very middle of big shapes a little thicker still: a few clean steps
    t = np.select([d <= 1, d == 2], [base, base + 0.8], base + 1.2)
    h = t / 2
    # relief from the sprite's own shading, against each pixel's neighbourhood
    rel = np.zeros_like(h)
    for y in range(n):
        for x in range(n):
            if not solid[y, x]:
                continue
            ys, xs = slice(max(y - 1, 0), y + 2), slice(max(x - 1, 0), x + 2)
            m = solid[ys, xs]
            mean = lum[ys, xs][m].mean()
            rel[y, x] = np.clip((lum[y, x] - mean) * relief, -relief_cap, relief_cap)
    return np.where(solid, np.maximum(h + rel, 0.3), 0.0)


def no_outline(col, solid):
    """a flat picture's dark outline means nothing on a round solid (the real shading draws the edges): paint each
    outline pixel with the nearest inner colour; thin parts with no inside (a stem) keep their own"""
    n = solid.shape[0]
    d = depth_steps(solid)
    inner = [(y, x) for y in range(n) for x in range(n) if d[y, x] >= 2]
    out = col.copy()
    for y in range(n):
        for x in range(n):
            if solid[y, x] and d[y, x] == 1 and inner:
                dist, (iy, ix) = min((math.hypot(y - iy, x - ix), (iy, ix)) for iy, ix in inner)
                if dist <= 2.3:
                    out[y, x] = col[iy, ix]
    # across the body (wide rows), odd-coloured pixels (the stem dipping into an apple) take the body's colour:
    # on a round solid they'd run right round it as a band
    import colorsys
    hue = lambda c: colorsys.rgb_to_hsv(*c[:3])[0] * 360
    for y in range(n):
        xs = [x for x in range(n) if solid[y, x]]
        if len(xs) < 5:
            continue
        hs = [hue(out[y, x]) for x in xs]
        buckets = {}
        for hv in hs:
            buckets[round(hv / 20)] = buckets.get(round(hv / 20), 0) + 1
        main = max(buckets, key=buckets.get) * 20
        good = [x for x, hv in zip(xs, hs) if min(abs(hv - main), 360 - abs(hv - main)) <= 14]
        for x, hv in zip(xs, hs):
            if min(abs(hv - main), 360 - abs(hv - main)) > 14 and good:
                out[y, x] = out[y, min(good, key=lambda g: abs(g - x))]
    return out


def build(name, layers, shape=None, recolour=None, wrap=False):
    """layers: [(sprite array, tint index or -1), ...] bottom to top, as in the vanilla model. shape gives each pixel
    column its half thickness; recolour may repaint the picture first; wrap paints round items by wrapping the picture
    around them (front = the picture, back = its mirror) instead of running each pixel's colour straight through"""
    n = layers[0][0].shape[0]
    col = np.zeros((n, n, 4))
    owner = np.full((n, n), -1)
    for li, (arr, _) in enumerate(layers):
        m = arr[..., 3] > 0.5
        col[m] = arr[m]
        owner[m] = li
    solid = owner >= 0
    if recolour:
        col = recolour(col, solid)
    lum = col[..., 0] * 0.299 + col[..., 1] * 0.587 + col[..., 2] * 0.114
    h = (shape or (lambda so, co, lu: depth_map(so, lu)))(solid, col, lum)
    h = np.where(solid, np.maximum(np.round(h * 2) / 2, 0.5), 0.0)  # whole half-pixel steps: a crisp, blocky look
    s = 1.0 / n  # one pixel, in blocks (Minecraft's 1/16 for a 16-pixel sprite)
    rows = {}
    for y in range(n):
        xs = np.nonzero(solid[y])[0]
        if len(xs):
            rows[y] = (xs, (xs.min() + xs.max() + 1) / 2, (xs.max() + 1 - xs.min()) / 2)

    def paint_at(y, x, xc, w):
        """the colour (and layer) at a point of the surface: xc across the picture, w in depth (- = front), in pixels"""
        if not wrap:
            return col[y, x], int(owner[y, x])
        xs, cx, r = rows[y]
        th = math.atan2(xc - cx, -w)
        if abs(th) > math.pi / 2:
            th = math.copysign(math.pi - abs(th), th)
        u = cx + th / (math.pi / 2) * r
        ix = int(xs[np.argmin(np.abs(xs + 0.5 - u))])
        return col[y, ix], int(owner[y, ix])

    mats = []
    for li, (_, tint) in enumerate(layers):
        mats.append(K.mat(f"layer{li}", attr="paint", edge=0.16, edge_radius=0.22 * s, tint=tint))
    bm = bmesh.new()
    paint = bm.loops.layers.float_color.new("paint")
    C = K.C

    def quad(pts, normal, y, x, xc, w):
        rgba, li = paint_at(y, x, xc, w)
        rgb = tuple(linear(rgba[:3]))
        vs = [bm.verts.new(p) for p in pts]
        f = bm.faces.new(vs)
        f.normal_update()
        if f.normal.dot(normal) < 0:
            f.normal_flip()
        f.material_index = li
        f.smooth = False
        for loop in f.loops:
            loop[paint] = (*rgb, 1.0)

    def strip(ax, az, bx, bz, w0, w1, normal, y, x, xc):
        """a side face from depth w0 to w1 (pixels), cut into pixel-deep pieces when the picture wraps round"""
        k = max(1, math.ceil((w1 - w0) - 1e-6)) if wrap else 1
        for i in range(k):
            a_, b_ = w0 + (w1 - w0) * i / k, w0 + (w1 - w0) * (i + 1) / k
            quad([(ax, C + a_ * s, az), (bx, C + a_ * s, bz), (bx, C + b_ * s, bz), (ax, C + b_ * s, az)],
                 normal, y, x, xc, (a_ + b_) / 2)

    for y in range(n):
        for x in range(n):
            if not solid[y, x]:
                continue
            x0, x1 = x * s, (x + 1) * s
            z0, z1 = (n - y - 1) * s, (n - y) * s
            hp = h[y, x]
            # front (toward -Y in Blender: the side vanilla shows) and back
            quad([(x0, C - hp * s, z0), (x1, C - hp * s, z0), (x1, C - hp * s, z1), (x0, C - hp * s, z1)], (0, -1, 0),
                 y, x, x + 0.5, -hp)
            quad([(x0, C + hp * s, z0), (x0, C + hp * s, z1), (x1, C + hp * s, z1), (x1, C + hp * s, z0)], (0, 1, 0),
                 y, x, x + 0.5, hp)
            # sides: full depth next to empty pixels, steps down to lower neighbours
            for dx, dz, pts, xc in ((1, 0, ((x1, z0), (x1, z1)), x + 1), (-1, 0, ((x0, z0), (x0, z1)), x),
                                    (0, -1, ((x0, z1), (x1, z1)), x + 0.5), (0, 1, ((x0, z0), (x1, z0)), x + 0.5)):
                # dz is the row step in the picture: -1 = the row above (higher up)
                ny, nx = y + dz, x + dx
                hq = h[ny, nx] if 0 <= ny < n and 0 <= nx < n and solid[ny, nx] else 0.0
                if hq >= hp - 1e-9:
                    continue
                (ax, az), (bx, bz) = pts
                normal = (dx, 0, -dz)
                if hq <= 0:
                    strip(ax, az, bx, bz, -hp, hp, normal, y, x, xc)
                else:
                    strip(ax, az, bx, bz, -hp, -hq, normal, y, x, xc)
                    strip(ax, az, bx, bz, hq, hp, normal, y, x, xc)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    ob = K.obj_from_bm(name, bm, mats[0], smooth=False)
    for m in mats[1:]:
        ob.data.materials.append(m)
    return ob


# ---------------------------------------------------------------- real shapes
STICK = {(73, 54, 21), (104, 78, 30), (137, 103, 39), (40, 30, 11)}  # the wooden handle's colours in every tool


def is_stick(col):
    return np.array([[tuple(int(round(c * 255)) for c in px[:3]) in STICK for px in row] for row in col])


def revolve(solid, col, lum):
    """round things (an apple, a bottle): every row of the picture spun round its own middle, so the front shows the
    picture and the item is a real round solid"""
    n = solid.shape[0]
    h = np.zeros((n, n))
    for y in range(n):
        xs = np.nonzero(solid[y])[0]
        if len(xs) == 0:
            continue
        x0, x1 = xs.min(), xs.max() + 1
        cx, r = (x0 + x1) / 2, (x1 - x0) / 2
        for x in xs:
            h[y, x] = math.sqrt(max(r * r - (x + 0.5 - cx) ** 2, 0.0) + 0.15)
    return h


def inflate(round_=1.0):
    """soft blobby things (bread, a potato, meat): puffed up like a cushion, thickest in the middle"""
    def f(solid, col, lum):
        d = np.zeros(solid.shape)
        n = solid.shape[0]
        edge = [(y, x) for y in range(n) for x in range(n) if not solid[y, x]]
        for y in range(n):
            for x in range(n):
                if solid[y, x]:
                    d[y, x] = min([math.hypot(y - ey, x - ex) for ey, ex in edge] + [x + 0.5, y + 0.5, n - x - 0.5, n - y - 0.5])
        r = d.max() or 1
        return round_ * r * np.sqrt(np.clip(1 - (1 - d / r) ** 2, 0, 1)) + 0.3
    return f


def sword(solid, col, lum):
    """every vanilla sword shares one picture: a thin blade with a raised middle ridge, a thick guard across it, a
    solid grip and a chunky pommel"""
    n = solid.shape[0]
    stick = is_stick(col)
    d = depth_steps(solid)
    h = np.zeros((n, n))
    for y in range(n):
        for x in range(n):
            if not solid[y, x]:
                continue
            u = x - y  # along the blade, toward the tip
            if stick[y, x]:
                h[y, x] = 1.0
            elif u >= -1:
                h[y, x] = 0.5 if d[y, x] <= 1 else 1.0
            elif u >= -7:
                h[y, x] = 1.5
            else:
                h[y, x] = 1.5
    return h


def tool(solid, col, lum):
    """pickaxes, axes, shovels, hoes: a solid head and a round wooden handle"""
    stick = is_stick(col)
    d = depth_steps(solid)
    return np.where(stick, 1.0, np.where(d <= 1, 1.0, 1.5))


def depth_steps(solid):
    n = solid.shape[0]
    d = np.where(solid, 99, 0)
    changed = True
    while changed:
        changed = False
        for y in range(n):
            for x in range(n):
                if solid[y, x]:
                    best = 1 + min(d[y + dy, x + dx] if 0 <= y + dy < n and 0 <= x + dx < n else 0
                                   for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                    if best < d[y, x]:
                        d[y, x] = best
                        changed = True
    return d


# ---------------------------------------------------------------- the items
TOOLS = ("_sword", "_pickaxe", "_axe", "_shovel", "_hoe")
ROUND = {"apple", "golden_apple", "enchanted_golden_apple", "potion", "splash_potion", "lingering_potion"}


def make(name):
    """the layers of an item's vanilla model, its real shape, and whether it's held like a tool"""
    if name in ("potion", "splash_potion", "lingering_potion"):
        layers = [(sprite("potion_overlay"), 0), (sprite(name), -1)]
    else:
        layers = [(sprite(name), -1)]
    shape = sword if name.endswith("_sword") else tool if name.endswith(TOOLS) else revolve if name in ROUND else inflate()
    rnd = name in ROUND
    ob = build(name, layers, shape, no_outline if rnd and "potion" not in name else None, wrap=rnd)
    # round things are as deep as they are wide: held a bit smaller
    return ob, (held(True) if name.endswith(TOOLS) else held(False, fp_scale=0.4, fp_lift=5.4) if rnd else held(False))


TEST = ["diamond_sword", "iron_pickaxe", "apple", "potion"]
TRANSLUCENT = set()


if __name__ == "__main__":
    K.configure(sys.argv)
    K.white_texture()
    pics = []
    for name in (sorted(K.ONLY) if K.ONLY else TEST):
        K.reset()
        ob, display = make(name)
        K.bake_and_export(ob, name, display, name in TRANSLUCENT, soft=0.6)
        print("made", name, len(ob.data.polygons), "faces")
        if K.PREVIEW:
            p = f"/tmp/claude-0/voxel_{name}.png"
            K.render_preview(ob, p)
            pics.append(p)
    if K.PREVIEW and pics:
        ims = [Image.open(p).convert("RGB") for p in pics]
        sheet = Image.new("RGB", (420 * len(ims), 420))
        for i, im in enumerate(ims):
            sheet.paste(im, (420 * i, 0))
        sheet.save(K.PREVIEW)
