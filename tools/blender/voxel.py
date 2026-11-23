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


def build(name, layers, extra=None):
    """layers: [(sprite array, tint index or -1), ...] bottom to top, as in the vanilla model. extra(h, col, solid)
    may reshape the depth for one item."""
    n = layers[0][0].shape[0]
    col = np.zeros((n, n, 4))
    owner = np.full((n, n), -1)
    for li, (arr, _) in enumerate(layers):
        m = arr[..., 3] > 0.5
        col[m] = arr[m]
        owner[m] = li
    solid = owner >= 0
    lum = col[..., 0] * 0.299 + col[..., 1] * 0.587 + col[..., 2] * 0.114
    h = depth_map(solid, lum)
    if extra:
        h = extra(h, col, solid)
    s = 1.0 / n  # one pixel, in blocks (Minecraft's 1/16 for a 16-pixel sprite)

    mats = []
    for li, (_, tint) in enumerate(layers):
        mats.append(K.mat(f"layer{li}", attr="paint", edge=0.16, edge_radius=0.22 * s, tint=tint))
    bm = bmesh.new()
    paint = bm.loops.layers.float_color.new("paint")
    C = K.C

    def quad(pts, normal, li, rgb):
        vs = [bm.verts.new(p) for p in pts]
        f = bm.faces.new(vs)
        f.normal_update()
        if f.normal.dot(normal) < 0:
            f.normal_flip()
        f.material_index = li
        f.smooth = False
        for loop in f.loops:
            loop[paint] = (*rgb, 1.0)

    for y in range(n):
        for x in range(n):
            if not solid[y, x]:
                continue
            rgb = tuple(linear(col[y, x, :3]))
            li = int(owner[y, x])
            x0, x1 = x * s, (x + 1) * s
            z0, z1 = (n - y - 1) * s, (n - y) * s
            hp = h[y, x] * s
            # front (toward -Y in Blender: the side vanilla shows) and back
            quad([(x0, C - hp, z0), (x1, C - hp, z0), (x1, C - hp, z1), (x0, C - hp, z1)], (0, -1, 0), li, rgb)
            quad([(x0, C + hp, z0), (x0, C + hp, z1), (x1, C + hp, z1), (x1, C + hp, z0)], (0, 1, 0), li, rgb)
            # sides: full height next to empty pixels, steps down to lower neighbours
            for dx, dz, pts in ((1, 0, ((x1, z0), (x1, z1))), (-1, 0, ((x0, z0), (x0, z1))),
                                (0, -1, ((x0, z1), (x1, z1))), (0, 1, ((x0, z0), (x1, z0)))):
                # dz here is the row step in the picture: -1 = the row above (higher z)
                ny, nx = y + dz, x + dx
                hq = h[ny, nx] * s if 0 <= ny < n and 0 <= nx < n and solid[ny, nx] else 0.0
                if hq >= hp - 1e-9:
                    continue
                (ax, az), (bx, bz) = pts
                normal = (dx, 0, -dz)
                if hq <= 0:
                    quad([(ax, C - hp, az), (bx, C - hp, bz), (bx, C + hp, bz), (ax, C + hp, az)], normal, li, rgb)
                else:
                    quad([(ax, C - hp, az), (bx, C - hp, bz), (bx, C - hq, bz), (ax, C - hq, az)], normal, li, rgb)
                    quad([(ax, C + hq, az), (bx, C + hq, bz), (bx, C + hp, bz), (ax, C + hp, az)], normal, li, rgb)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    ob = K.obj_from_bm(name, bm, mats[0], smooth=False)
    for m in mats[1:]:
        ob.data.materials.append(m)
    return ob


# ---------------------------------------------------------------- the items
TOOLS = ("_sword", "_pickaxe", "_axe", "_shovel", "_hoe")


def make(name):
    """the layers of an item's vanilla model, and whether it's held like a tool"""
    if name in ("potion", "splash_potion", "lingering_potion"):
        layers = [(sprite("potion_overlay"), 0), (sprite(name), -1)]
    else:
        layers = [(sprite(name), -1)]
    ob = build(name, layers)
    return ob, held(name.endswith(TOOLS))


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
