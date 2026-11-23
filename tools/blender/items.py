#!/usr/bin/env python3
"""Blender-made item models for Lifelike Motion: smooth real meshes (faceted crystal blades, round fruit, glass bottles)
painted with SMOOTH per-vertex colour, not pixel textures. Blender bakes each model's painted colour (gradients, worn
lighter edges) times soft ambient occlusion straight into the mesh's vertices; Forge's OBJ loader reads them back ("vc"),
and the game blends them smoothly across each face, so there are no texels to see at any distance.

Runs with Blender's Python module:  python3 tools/blender/items.py <pack dir> [names...] [--preview out.png]

Blender works in Z-up with 1 unit = 1 block; models are built standing up around the block's middle and exported to
Minecraft's Y-up space. Each model's item display turns it onto the usual diagonal.
"""
import json
import math
import os
import sys

import bpy  # noqa: must come before bmesh
import bmesh
import numpy as np
from mathutils import Matrix, Vector

PACK = None  # the resource pack folder the models go into (set by configure)
PREVIEW = None
ONLY = set()


def configure(argv):
    """command line: <pack dir> [names...] [--preview out.png]"""
    global PACK, PREVIEW, ONLY
    args = [a for a in argv[1:] if not a.startswith("--")]
    if "--preview" in argv:
        PREVIEW = argv[argv.index("--preview") + 1]
        args = [a for a in args if a != PREVIEW]
    PACK = args[0]
    ONLY = set(args[1:])


NS = "lifelikemotion"
C = 0.5  # the block's middle (x and y); models stand on z
WHITE = f"{NS}:item/obj/white"


# ---------------------------------------------------------------- scene helpers
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color=(1, 1, 1), ramp=None, axis="Z", noise=0.0, noise_scale=8.0, stretch=(1, 1, 1), edge=0.35,
        edge_radius=0.012, alpha=1.0, glow=False, tint=-1, attr=None):
    """a painted material. ramp = [(position, colour), ...] along an object axis; noise darkens in soft patches
    (stretch < 1 on an axis draws it out into streaks along that axis); edge lightens worn edges and ridges"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    if attr:
        # colours painted onto the mesh itself (one per corner)
        ca = nt.nodes.new("ShaderNodeVertexColor")
        ca.layer_name = attr
        last = ca.outputs["Color"]
    elif ramp:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        cr = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        nt.links.new(sep.outputs[axis], cr.inputs[0])
        els = cr.color_ramp.elements
        while len(els) < len(ramp):
            els.new(0.5)
        for el, (pos, col) in zip(els, sorted(ramp)):
            el.position = pos
            el.color = (*col, 1)
        last = cr.outputs["Color"]
    else:
        rgb = nt.nodes.new("ShaderNodeRGB")
        rgb.outputs[0].default_value = (*color, 1)
        last = rgb.outputs[0]
    if noise:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = stretch
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = noise_scale
        nz.inputs["Detail"].default_value = 3.0
        nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        cr = nt.nodes.new("ShaderNodeValToRGB")
        cr.color_ramp.elements[0].color = (1 - noise, 1 - noise, 1 - noise, 1)
        cr.color_ramp.elements[1].color = (1, 1, 1, 1)
        cr.color_ramp.elements[0].position = 0.35
        cr.color_ramp.elements[1].position = 0.65
        nt.links.new(nz.outputs["Fac"], cr.inputs[0])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(last, mix.inputs[6])
        nt.links.new(cr.outputs["Color"], mix.inputs[7])
        last = mix.outputs[2]
    if edge:
        # lighter worn edges: where a rounded (bevel) normal turns away from the true one
        bev = nt.nodes.new("ShaderNodeBevel")
        bev.samples = 8
        bev.inputs["Radius"].default_value = edge_radius
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        dot = nt.nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        nt.links.new(bev.outputs[0], dot.inputs[0])
        nt.links.new(geo.outputs["Normal"], dot.inputs[1])
        cr = nt.nodes.new("ShaderNodeValToRGB")
        cr.color_ramp.elements[0].position = 0.80
        cr.color_ramp.elements[1].position = 0.985
        cr.color_ramp.elements[0].color = (edge, edge, edge, 1)
        cr.color_ramp.elements[1].color = (0, 0, 0, 1)
        nt.links.new(dot.outputs["Value"], cr.inputs[0])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "SCREEN"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(last, mix.inputs[6])
        nt.links.new(cr.outputs["Color"], mix.inputs[7])
        last = mix.outputs[2]
    nt.links.new(last, bsdf.inputs["Base Color"])
    m["alpha"] = alpha
    m["glow"] = glow
    m["tint"] = tint
    return m


def obj_from_bm(name, bm, material, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    for p in ob.data.polygons:
        p.use_smooth = smooth
    return ob


def add(op, material, smooth=True, **kw):
    op(**kw)
    ob = bpy.context.active_object
    ob.data.materials.append(material)
    for p in ob.data.polygons:
        p.use_smooth = smooth
    return ob


def modifier(ob, kind, **kw):
    md = ob.modifiers.new(kind.lower(), kind)
    for k, v in kw.items():
        setattr(md, k, v)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=md.name)
    return ob


def loft(name, rings, material, smooth=True, cap_top=True, cap_bottom=True):
    """a solid from cross-section rings [(z, [(x, y), ...]), ...] (every ring the same point count)"""
    bm = bmesh.new()
    layers = [[bm.verts.new((x, y, z)) for (x, y) in pts] for z, pts in rings]
    _skin(bm, layers, cap_top, cap_bottom)
    return obj_from_bm(name, bm, material, smooth)


def _skin(bm, layers, cap_top=True, cap_bottom=True):
    n = len(layers[0])
    for a, b in zip(layers, layers[1:]):
        for i in range(n):
            j = (i + 1) % n
            uniq = []
            for v in (a[i], a[j], b[j], b[i]):
                if all((v.co - u.co).length > 1e-6 for u in uniq):
                    uniq.append(v)
            if len(uniq) >= 3:
                try:
                    bm.faces.new(uniq)
                except ValueError:
                    pass
    for layer, cap, rev in ((layers[0], cap_bottom, True), (layers[-1], cap_top, False)):
        if cap and len({tuple(round(c, 6) for c in v.co) for v in layer}) > 2:
            # a fan around a middle point keeps the cap's faces small (smooth colour) and convex
            mid = bm.verts.new(sum((v.co for v in layer), Vector()) / len(layer))
            for i in range(n):
                f = [layer[i], layer[(i + 1) % n], mid]
                try:
                    bm.faces.new(list(reversed(f)) if rev else f)
                except ValueError:
                    pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def lathe(name, profile, material, steps=24, smooth=True, cx=C, cy=C, lobes=None):
    """a round solid from a side profile [(radius, z), ...] bottom to top; lobes = f(angle, z) -> radius scale"""
    rings = []
    for (r, z) in profile:
        pts = []
        for i in range(steps):
            a = 2 * math.pi * i / steps
            rr = r * (lobes(a, z) if lobes else 1.0)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        rings.append((z, pts))
    return loft(name, rings, material, smooth)


def dense(profile, step=0.02):
    """more rings along a side profile: small faces sort cleanly behind and in front of see-through glass"""
    out = [profile[0]]
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        n = max(1, int(math.hypot(r1 - r0, z1 - z0) / step))
        out += [(r0 + (r1 - r0) * k / n, z0 + (z1 - z0) * k / n) for k in range(1, n + 1)]
    return out


def sweep(name, path, section, material, smooth=True):
    """a bar along a path in the x/z plane: path = [(x, z, half depth, half height), ...];
    section = unit outline [(u, v), ...] (u across the depth, y; v across the height, at right angles to the path)"""
    bm = bmesh.new()
    layers = []
    for k, (x, z, d, h) in enumerate(path):
        a = path[max(k - 1, 0)]
        b = path[min(k + 1, len(path) - 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, tz) or 1.0
        nx, nz = -tz / ln, tx / ln
        layers.append([bm.verts.new((x + v * h * nx, C + u * d, z + v * h * nz)) for (u, v) in section])
    _skin(bm, layers)
    return obj_from_bm(name, bm, material, smooth)


def octagon(round_=0.72):
    return [(1, 0), (round_, round_), (0, 1), (-round_, round_), (-1, 0), (-round_, -round_), (0, -1), (round_, -round_)]


def circle(n=12):
    return [(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)]


def turn(ob, rx=0.0, ry=0.0, rz=0.0, pivot=(C, C, 0.0)):
    """rotate a part's mesh about a point (radians)"""
    pv = Vector(pivot)
    m = Matrix.Translation(pv) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y") @ Matrix.Rotation(rx, 4, "X") @ Matrix.Translation(-pv)
    ob.data.transform(ob.matrix_world.inverted() @ m @ ob.matrix_world)
    return ob


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
        # bake object transforms into the mesh, so every part shares one origin
        bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name
    return ob


# ---------------------------------------------------------------- baking into vertices and export
def _bake_corners(ob, kind, **kw):
    """bake into a new per-corner colour attribute; returns an (corners, 4) array of linear values"""
    me = ob.data
    attr = me.color_attributes.new(f"bake_{kind}_{len(me.color_attributes)}", "FLOAT_COLOR", "CORNER")
    me.color_attributes.active_color = attr
    bpy.ops.object.bake(type=kind, target="VERTEX_COLORS", **kw)
    buf = np.zeros(len(me.loops) * 4, dtype=np.float32)
    attr.data.foreach_get("color", buf)
    return buf.reshape(-1, 4)


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def bake_and_export(ob, name, display, translucent=False, particle=None, soft=0.0):
    """bake the painted colour times soft ambient occlusion (and alpha, for glass) into every corner of the mesh,
    then write the OBJ (with Forge's "vc" vertex colours), its material file and the item model"""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 64
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    me = ob.data
    ao = _bake_corners(ob, "AO")[:, :1]
    if "paint" in me.color_attributes:
        # exact colours painted per corner (Minecraft's own pixels): only the light worn edges are baked, as a mask
        base = np.zeros(len(me.loops) * 4, dtype=np.float32)
        me.color_attributes["paint"].data.foreach_get("color", base)
        base = base.reshape(-1, 4)[:, :3]
        for m in me.materials:
            nt = m.node_tree
            for node in [nd for nd in nt.nodes if nd.bl_idname == "ShaderNodeVertexColor"]:
                black = nt.nodes.new("ShaderNodeRGB")
                black.outputs[0].default_value = (0, 0, 0, 1)
                for l in list(node.outputs["Color"].links):
                    nt.links.new(black.outputs[0], l.to_socket)
        mask = _bake_corners(ob, "DIFFUSE", pass_filter={"COLOR"})[:, :3]
        # worn edges brighten in their own colour (a dark red rim stays red, it doesn't wash out to pink)
        rgb = srgb(base * (0.5 + 0.5 * ao) * (1 + 2.2 * mask))
    else:
        col = _bake_corners(ob, "DIFFUSE", pass_filter={"COLOR"})[:, :3]
        rgb = srgb(col * (0.42 + 0.58 * ao))
    alpha = np.ones((len(rgb), 1))
    if any(m.get("alpha", 1.0) < 1.0 for m in ob.data.materials):
        for m in ob.data.materials:
            nt = m.node_tree
            bsdf = nt.nodes["Principled BSDF"]
            for l in list(bsdf.inputs["Base Color"].links):
                nt.links.remove(l)
            a_ = m.get("alpha", 1.0)
            bsdf.inputs["Base Color"].default_value = (a_, a_, a_, 1)
        alpha = _bake_corners(ob, "DIFFUSE", pass_filter={"COLOR"})[:, :1]
    rgba = np.concatenate([rgb, np.clip(alpha, 0, 1)], axis=1)
    # kept for the preview render
    fin = me.color_attributes.new("final", "FLOAT_COLOR", "CORNER")
    shown = rgba[:, :3].copy()
    tinted = np.zeros(len(me.loops), dtype=bool)
    for p in me.polygons:
        if int(me.materials[p.material_index].get("tint", -1)) >= 0:
            tinted[list(p.loop_indices)] = True
    shown[tinted] *= np.array([0.97, 0.14, 0.27])  # a sample potion colour (healing)
    lin = np.where(shown <= 0.04045, shown / 12.92, np.power((shown + 0.055) / 1.055, 2.4))
    fin.data.foreach_set("color", np.concatenate([lin, rgba[:, 3:]], axis=1).astype(np.float32).ravel())
    write_obj(ob, name, rgba, soft)
    out_model = os.path.join(PACK, "assets", NS, "models", "item3d")
    model = {"loader": "forge:obj", "model": f"{NS}:models/item/obj/{name}.obj", "flip_v": True,
             "automatic_culling": False, "shade_quads": True, "emissive_ambient": True,
             "textures": {"particle": particle or f"minecraft:item/{name}"}, "display": display}
    if translucent:
        model["render_type"] = "minecraft:translucent"
    with open(os.path.join(out_model, name + ".json"), "w") as f:
        json.dump(model, f, separators=(",", ":"))


def write_obj(ob, name, rgba, soft=0.0):
    """our own OBJ writer: Minecraft's Y-up axes, corner normals, and a "vc" colour per corner (Forge's extension)"""
    me = ob.data
    # quads and triangles only (the game draws quads); bigger faces become triangles
    bm = bmesh.new()
    bm.from_mesh(me)
    big = [f for f in bm.faces if len(f.verts) > 4]
    if big:
        raise RuntimeError(f"{name}: {len(big)} faces with more than 4 corners")
    bm.free()
    normals = np.zeros(len(me.loops) * 3, dtype=np.float32)
    me.corner_normals.foreach_get("vector", normals)
    normals = normals.reshape(-1, 3)
    if soft:
        # rounded-looking edges: each corner's normal leans toward the other faces meeting at its point, so light rolls
        # softly over every rim instead of breaking sharply (shared flat faces stay flat)
        seen = {}
        for p in me.polygons:
            key = tuple(round(c, 3) for c in p.normal)
            for vi in p.vertices:
                seen.setdefault(vi, {})[key] = np.array(p.normal)
        for p in me.polygons:
            fn = np.array(p.normal)
            for li in p.loop_indices:
                others = [n for n in seen[me.loops[li].vertex_index].values() if np.dot(n, fn) < 0.99]
                if others:
                    v = fn + soft * np.sum(others, axis=0)
                    normals[li] = v / (np.linalg.norm(v) or 1.0)
    out = os.path.join(PACK, "assets", NS, "models", "item", "obj")
    os.makedirs(out, exist_ok=True)
    lines = [f"# Lifelike Motion: {name} (made in Blender by tools/blender/items.py)", f"mtllib {name}.mtl", f"o {name}"]
    for v in me.vertices:
        x, y, z = v.co
        lines.append(f"v {x:.5f} {z:.5f} {1 - y:.5f}")  # Blender Z-up -> Minecraft Y-up (+Y in Blender faces north)
    lines.append("vt 0.5 0.5")
    vn, vc = {}, {}
    nl, cl = [], []
    keyed = []
    for li, loop in enumerate(me.loops):
        n = normals[li]
        kn = (round(float(n[0]), 3), round(float(n[2]), 3), round(float(-n[1]), 3))
        if kn not in vn:
            vn[kn] = len(vn) + 1
            nl.append("vn %.3f %.3f %.3f" % kn)
        kc = tuple(round(float(c), 3) for c in rgba[li])
        if kc not in vc:
            vc[kc] = len(vc) + 1
            cl.append("vc %.3f %.3f %.3f %.3f" % kc)
        keyed.append((vn[kn], vc[kc]))
    lines += nl + cl
    mats = [(m.name.replace(" ", "_"), int(m.get("tint", -1)), bool(m.get("glow", False))) for m in me.materials]
    by_mat = {}
    for p in me.polygons:
        by_mat.setdefault(p.material_index, []).append(p)
    for mi, polys in sorted(by_mat.items()):
        lines.append(f"usemtl {mats[mi][0]}")
        for p in polys:
            corners = [f"{me.loops[li].vertex_index + 1}/1/{keyed[li][0]}/{keyed[li][1]}" for li in p.loop_indices]
            lines.append("f " + " ".join(corners))
    with open(os.path.join(out, name + ".obj"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(out, name + ".mtl"), "w") as f:
        for (mname, tint, glow) in mats:
            f.write(f"newmtl {mname}\nKd 1 1 1\nforge_TintIndex {tint}\n")
            if glow:
                f.write("Ka 1 1 1\n")
            f.write(f"map_Kd {WHITE}\n\n")


def white_texture():
    from PIL import Image
    p = os.path.join(PACK, "assets", NS, "textures", "item", "obj")
    os.makedirs(p, exist_ok=True)
    Image.new("RGBA", (16, 16), (255, 255, 255, 255)).save(os.path.join(p, "white.png"))


# ---------------------------------------------------------------- how items sit in the hand
def hand_display(turn=45, scale=0.68, tp=0.85, lift=0.0):
    return {
        "thirdperson_righthand": {"rotation": [0, -90, 55 + turn], "translation": [0, 4.0 + lift, 0.5], "scale": [tp] * 3},
        "thirdperson_lefthand": {"rotation": [0, 90, -55 - turn], "translation": [0, 4.0 + lift, 0.5], "scale": [tp] * 3},
        "firstperson_righthand": {"rotation": [0, -90, 25 + turn], "translation": [1.13, 3.2 + lift, 1.13], "scale": [scale] * 3},
        "firstperson_lefthand": {"rotation": [0, 90, -25 - turn], "translation": [1.13, 3.2 + lift, 1.13], "scale": [scale] * 3},
        "ground": {"rotation": [0, 0, turn], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "fixed": {"rotation": [0, 180, turn], "scale": [1, 1, 1]},
        "head": {"rotation": [0, 180, turn], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    }


def food_display(scale=1.0):
    s = 0.46 * scale
    return {
        "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.5 * scale] * 3},
        "thirdperson_lefthand": {"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.5 * scale] * 3},
        "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 7.0, 1.13], "scale": [s] * 3},
        "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 7.0, 1.13], "scale": [s] * 3},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
        "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    }


# ---------------------------------------------------------------- the items
def blade_section(w, t, ridge=1.25):
    """a crystal blade's cross-section: sharp edges, bevels, flat faces and a raised middle ridge"""
    return [(C + w, C), (C + 0.62 * w, C + t), (C + 0.22 * w, C + t * 1.08), (C, C + t * ridge),
            (C - 0.22 * w, C + t * 1.08), (C - 0.62 * w, C + t), (C - w, C), (C - 0.62 * w, C - t),
            (C - 0.22 * w, C - t * 1.08), (C, C - t * ridge), (C + 0.22 * w, C - t * 1.08), (C + 0.62 * w, C - t)]


def sword(name, blade_ramp, guard_ramp, grip_c, gem_c):
    blade = mat("blade", ramp=blade_ramp, edge=0.42, edge_radius=0.01)
    guard = mat("guard", ramp=guard_ramp, edge=0.45, edge_radius=0.012)
    grip = mat("grip", grip_c, noise=0.3, noise_scale=30, edge=0.25)
    gem = mat("gem", gem_c, edge=0.6, edge_radius=0.008)
    parts = []
    # blade: a gentle leaf shape, then a sharp point
    z0, z1, ztip = 0.30, 1.04, 1.22
    rings = []
    for i in range(17):
        s = i / 16
        z = z0 + (z1 - z0) * s
        w = 0.085 + 0.012 * math.sin(s * math.pi * 0.9) - 0.01 * s
        rings.append((z, blade_section(w, 0.024)))
    for s in (0.25, 0.5, 0.75, 0.92, 1.0):
        z = z1 + (ztip - z1) * s
        k = (1 - s) ** 1.15
        rings.append((z, blade_section(max(0.087 * k, 1e-4), max(0.024 * k, 1e-4))))
    parts.append(loft("blade", rings, blade, smooth=False))
    # crossguard: a chunky middle and wings that sweep up toward the blade, ending in points
    path = []
    for i in range(25):
        t = i / 24 * 2 - 1
        a = abs(t)
        x = C + t * 0.25
        z = 0.275 + 0.07 * a ** 2.2
        d = 0.05 * (1 - 0.55 * a ** 1.5) + 0.004
        h = 0.036 * (1 - 0.7 * a ** 2) + 0.004 if a < 0.97 else 0.004
        if a < 0.2:
            d, h = d * 1.12, h * 1.25
        path.append((x, z, d, h))
    g = sweep("guard", path, octagon(0.7), guard)
    modifier(g, "SUBSURF", levels=1)
    parts.append(g)
    # a gem set in the guard, on both faces
    for side in (-1, 1):
        prof = [(0.0, 0.0), (0.03, 0.012), (0.022, 0.022), (0.0, 0.026)]
        gm = lathe("gem", prof, gem, steps=8, smooth=False)
        turn(gm, rx=-side * math.pi / 2, pivot=(C, C, 0.0))
        gm.data.transform(Matrix.Translation((0, side * 0.045, 0.285)))
        parts.append(gm)
    # wrapped grip
    prof = [(0.0, 0.085)]
    for i in range(13):
        z = 0.09 + i * 0.0145
        prof += [(0.027, z), (0.031, z + 0.007)]
    prof += [(0.027, 0.28), (0.0, 0.28)]
    parts.append(lathe("grip", prof, grip, steps=14))
    # a crystal pommel
    prof = [(0.0, 0.0), (0.03, 0.02), (0.045, 0.05), (0.03, 0.085), (0.0, 0.095)]
    parts.append(lathe("pommel", prof, guard, steps=8, smooth=False))
    ob = join(parts, name)
    return ob, hand_display(20, lift=6.0)


def pickaxe(name, head_ramp):
    wood = mat("wood", ramp=[(0.0, (0.2, 0.1, 0.045)), (1.0, (0.36, 0.2, 0.09))], noise=0.35, noise_scale=6,
               stretch=(14, 14, 1.2), edge=0.15)
    head = mat("head", ramp=head_ramp, edge=0.45, edge_radius=0.014)
    wrap = mat("wrap", (0.14, 0.07, 0.035), noise=0.25, noise_scale=40, edge=0.2)
    iron = mat("iron", ramp=[(0.0, (0.25, 0.26, 0.28)), (1.0, (0.45, 0.46, 0.5))], edge=0.5)
    parts = []
    prof = [(0.0, 0.02)] + [(0.031 - 0.006 * (z / 0.95), z) for z in [0.03 + 0.06 * k for k in range(16)]] + [(0.0, 0.96)]
    parts.append(lathe("handle", prof, wood, steps=12))
    prof = [(0.0, 0.0), (0.036, 0.0), (0.04, 0.02), (0.036, 0.05), (0.0, 0.05)]
    parts.append(lathe("cap", prof, iron, steps=12))
    prof = [(0.0, 0.07)]
    for i in range(12):
        z = 0.075 + i * 0.017
        prof += [(0.033, z), (0.037, z + 0.008)]
    prof += [(0.033, 0.285), (0.0, 0.285)]
    parts.append(lathe("wrap", prof, wrap, steps=12))
    # the socket that holds the head on the handle
    sock = add(bpy.ops.mesh.primitive_cube_add, iron, size=1.0, location=(C, C, 0.865))
    sock.scale = (0.1, 0.085, 0.15)
    bpy.ops.object.transform_apply(scale=True)
    modifier(sock, "BEVEL", width=0.018, segments=3)
    parts.append(sock)
    # the head: thick in the middle, two arms curving down to sharp points
    path = []
    for i in range(29):
        t = i / 28 * 2 - 1
        a = abs(t)
        x = C + t * 0.42
        z = 0.89 - 0.2 * a ** 1.9
        h = 0.062 * (1 - a ** 1.7) + 0.003
        d = 0.05 * (1 - a ** 2.2) + 0.004
        path.append((x, z, d, h))
    hd = sweep("head", path, octagon(0.78), head)
    modifier(hd, "SUBSURF", levels=1)
    parts.append(hd)
    # rivets on both faces of the socket
    for side in (-1, 1):
        r = add(bpy.ops.mesh.primitive_uv_sphere_add, iron, segments=10, ring_count=6, radius=0.016,
                location=(C, C + side * 0.043, 0.82))
        parts.append(r)
    ob = join(parts, name)
    return ob, hand_display(45)


def apple(name):
    skin = mat("skin", ramp=[(0.12, (0.25, 0.01, 0.015)), (0.3, (0.55, 0.02, 0.03)), (0.48, (0.75, 0.06, 0.04)),
                             (0.6, (0.85, 0.3, 0.05)), (0.66, (0.65, 0.55, 0.12))],
               noise=0.22, noise_scale=3.5, stretch=(9, 9, 1.4), edge=0.0)
    stem = mat("stem", ramp=[(0.6, (0.12, 0.07, 0.03)), (0.8, (0.3, 0.2, 0.08))], edge=0.2)
    leaf = mat("leaf", ramp=[(-0.2, (0.08, 0.25, 0.04)), (0.25, (0.3, 0.62, 0.12))], axis="X", edge=0.35)
    # body: rounder and wider at the shoulders, softly lobed at the bottom, dimpled top and bottom
    prof = []
    n = 22
    for i in range(n + 1):
        a = -math.pi / 2 + math.pi * i / n
        r = 0.27 * math.cos(a) * (1 + 0.1 * math.sin(a)) ** 1.0
        z = 0.38 + 0.235 * math.sin(a)
        z -= 0.055 * math.exp(-((math.pi / 2 - a) / 0.38) ** 2)  # the stem's dimple
        z += 0.03 * math.exp(-((math.pi / 2 + a) / 0.4) ** 2)  # the flower end
        prof.append((max(r, 0.0), z))
    prof[0] = (0.0, prof[1][1] + 0.004)
    prof[-1] = (0.0, prof[-2][1] - 0.006)
    body = lathe("body", prof, skin, steps=36, lobes=lambda a, z: 1 + 0.03 * math.cos(5 * a) * max(0.0, 0.5 - z) * 3)
    parts = [body]
    # a curved stem
    rings = []
    for k in range(7):
        s = k / 6
        cx = C + 0.04 * s ** 2
        z = 0.56 + 0.17 * s
        r = 0.016 - 0.004 * s
        rings.append((z, [(cx + r * math.cos(2 * math.pi * i / 8), C + r * math.sin(2 * math.pi * i / 8)) for i in range(8)]))
    parts.append(loft("stem", rings, stem))
    # a leaf with a fold down its middle, curling at the tip
    bm = bmesh.new()
    rows = []
    L = 0.26
    for k in range(11):
        s = k / 10
        half = 0.07 * math.sin(math.pi * s) ** 0.8
        x = s * L
        lift = 0.06 * s ** 2
        row = [bm.verts.new((x, -half, lift + 0.4 * half * 0.35)), bm.verts.new((x, 0, lift)), bm.verts.new((x, half, lift + 0.4 * half * 0.35))]
        rows.append(row)
    for a_, b_ in zip(rows, rows[1:]):
        for j in range(2):
            vs = [a_[j], a_[j + 1], b_[j + 1], b_[j]]
            uniq = []
            for v in vs:
                if all((v.co - u.co).length > 1e-6 for u in uniq):
                    uniq.append(v)
            if len(uniq) >= 3:
                bm.faces.new(uniq)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    lf = obj_from_bm("leaf", bm, leaf)
    modifier(lf, "SOLIDIFY", thickness=0.012, offset=0)
    # tilted up so it reads from the side as well as from above
    lf.data.transform(Matrix.Translation((C + 0.03, C, 0.68)) @ Matrix.Rotation(0.3, 4, "Y") @ Matrix.Rotation(0.6, 4, "Z") @ Matrix.Rotation(-0.8, 4, "X"))
    parts.append(lf)
    ob = join(parts, name)
    return ob, food_display()


def potion(name):
    glass = mat("glass", ramp=[(0.1, (0.75, 0.88, 0.95)), (0.7, (0.92, 0.97, 1.0))], alpha=0.38, edge=0.0)
    liquid = mat("liquid", ramp=[(0.1, (0.55, 0.55, 0.55)), (0.34, (1.0, 1.0, 1.0))], tint=0, edge=0.0)
    cork = mat("cork", ramp=[(0.7, (0.42, 0.27, 0.13)), (0.84, (0.7, 0.52, 0.3))], noise=0.3, noise_scale=40, edge=0.3)
    twine = mat("twine", (0.62, 0.5, 0.32), noise=0.2, noise_scale=60, edge=0.2)
    # what's inside first, the glass last
    parts = []
    inner = [(0.0, 0.09), (0.11, 0.09), (0.165, 0.115), (0.2, 0.17), (0.21, 0.25), (0.2, 0.33), (0.185, 0.365), (0.0, 0.37)]
    parts.append(lathe("liquid", dense(inner, 0.025), liquid, steps=32))
    prof = [(0.0, 0.66), (0.058, 0.66), (0.062, 0.77), (0.07, 0.8), (0.066, 0.83), (0.0, 0.835)]
    parts.append(lathe("cork", prof, cork, steps=16))
    t = add(bpy.ops.mesh.primitive_torus_add, twine, major_radius=0.078, minor_radius=0.011, major_segments=24,
            minor_segments=8, location=(C, C, 0.6))
    parts.append(t)
    outer = [(0.0, 0.07), (0.13, 0.07), (0.2, 0.095), (0.24, 0.16), (0.25, 0.25), (0.235, 0.35), (0.19, 0.43),
             (0.11, 0.49), (0.072, 0.53), (0.068, 0.6), (0.07, 0.69), (0.09, 0.7), (0.092, 0.73), (0.075, 0.74),
             (0.0, 0.74)]
    parts.append(lathe("glass", dense(outer, 0.025), glass, steps=32))
    ob = join(parts, name)
    return ob, food_display(1.0)


ITEMS = {
    "diamond_sword": lambda: sword(
        "diamond_sword",
        blade_ramp=[(0.3, (0.008, 0.13, 0.17)), (0.62, (0.03, 0.38, 0.44)), (1.15, (0.16, 0.75, 0.75))],
        guard_ramp=[(0.2, (0.02, 0.16, 0.2)), (0.36, (0.05, 0.38, 0.42))],
        grip_c=(0.13, 0.065, 0.03), gem_c=(0.35, 0.95, 1.0)),
    "iron_pickaxe": lambda: pickaxe("iron_pickaxe", [(0.7, (0.13, 0.14, 0.16)), (0.95, (0.4, 0.42, 0.46))]),
    "apple": lambda: apple("apple"),
    "potion": lambda: potion("potion"),
}
TRANSLUCENT = {"potion"}


# ---------------------------------------------------------------- a quick look outside the game
def render_preview(ob, out):
    """the baked colours under soft studio light, roughly how the game will light them"""
    sc = bpy.context.scene
    pm = bpy.data.materials.new("preview")
    pm.use_nodes = True
    nt = pm.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    ca = nt.nodes.new("ShaderNodeVertexColor")
    ca.layer_name = "final"
    nt.links.new(ca.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(ca.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Specular IOR Level"].default_value = 0.0  # matte, like the game's own lighting
    ob.data.materials.clear()
    ob.data.materials.append(pm)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 96
    sc.cycles.use_denoising = False  # the denoiser smears painted pixels
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = sc.render.resolution_y = 420
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.16, 0.2, 0.28, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    sc.world = w
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    ctr = sum(bb, Vector()) / 8
    size = max((max(v[i] for v in bb) - min(v[i] for v in bb)) for i in range(3))
    cam.location = ctr + Vector((size * 0.9, -size * 1.5, size * 0.45))
    cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
    key = bpy.data.objects.new("key", bpy.data.lights.new("key", "SUN"))
    key.data.energy = 2.2
    key.rotation_euler = (0.8, 0.2, -0.6)
    sc.collection.objects.link(key)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    configure(sys.argv)
    white_texture()
    pics = []
    for name, make in ITEMS.items():
        if ONLY and name not in ONLY:
            continue
        reset()
        ob, display = make()
        bake_and_export(ob, name, display, name in TRANSLUCENT)
        print("made", name, len(ob.data.polygons), "faces")
        if PREVIEW:
            p = f"/tmp/claude-0/blender_{name}.png"
            render_preview(ob, p)
            pics.append(p)
    if PREVIEW and pics:
        from PIL import Image
        ims = [Image.open(p).convert("RGB") for p in pics]
        sheet = Image.new("RGB", (420 * len(ims), 420))
        for i, im in enumerate(ims):
            sheet.paste(im, (420 * i, 0))
        sheet.save(PREVIEW)
