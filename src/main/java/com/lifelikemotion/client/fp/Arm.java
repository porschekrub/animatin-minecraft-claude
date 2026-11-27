package com.lifelikemotion.client.fp;

import com.lifelikemotion.client.ItemKind;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.PlayerModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.block.model.BakedQuad;
import net.minecraft.client.renderer.entity.player.PlayerRenderer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.resources.model.BakedModel;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.PlayerModelPart;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import org.joml.Vector4f;

import java.util.Map;
import java.util.WeakHashMap;

/**
 * Your arm in first person, the way it really holds things: drawn from your shoulder (just off screen, bottom corner)
 * to your fist, wherever the fist is. The fist closes round the held item's grip, found from the item's own model (the
 * bottom of a handle, the underside of a block or an apple), so every item is held for real and the arm follows every
 * swing, sway and toss by itself.
 * <p>
 * Points are in the hand render's camera space at the start of the hand's event ("root": x right, y up, z toward you).
 */
public final class Arm {
    private Arm() {}

    /**
     * the shoulder (x toward the arm's own side) and how big the arm is drawn. The shoulder sits low and close, so at
     * rest the arm reaches up and out to the hand the way the game's own first-person arm does.
     */
    public static float SX = 1.06f, SY = -1.0f, SZ = -0.32f, SCALE = 0.78f;

    /** the game's own first-person arm's turn (model space to the hand's camera space) */
    static Quaternionf vanilla(float s) {
        return new Quaternionf().rotateY((float) Math.toRadians(45 * s)).rotateZ((float) Math.toRadians(120 * s))
                .rotateX((float) Math.toRadians(200)).rotateY((float) Math.toRadians(-135 * s));
    }

    /** which way the back of the hand faces when the arm is at rest (camera space) */
    static Vector3f restOuter(float s) {
        return vanilla(s).transform(new Vector3f(-s, 0, 0));
    }

    static final Matrix4f ROOT = new Matrix4f(), ROOT_INV = new Matrix4f();
    static final Matrix3f ROOT_N = new Matrix3f();

    static void captureRoot(PoseStack ps) {
        ROOT.set(ps.last().pose());
        ROOT.invert(ROOT_INV);
        ROOT_N.set(ps.last().normal());
    }

    /** a point of the current pose, in root space */
    static Vector3f toRoot(Matrix4f pose, float x, float y, float z) {
        Vector4f v = new Vector4f(x, y, z, 1);
        pose.transform(v);
        ROOT_INV.transform(v);
        return new Vector3f(v.x, v.y, v.z);
    }

    /** a direction of the current pose, in root space (normalised) */
    static Vector3f dirToRoot(Matrix4f pose, float x, float y, float z) {
        Vector4f v = new Vector4f(x, y, z, 0);
        pose.transform(v);
        ROOT_INV.transform(v);
        return new Vector3f(v.x, v.y, v.z).normalize();
    }

    /**
     * Draws the arm (with its sleeve) reaching from the shoulder to the fist at {@code fist}: turned the way the game's
     * own first-person arm is, then swung round to point at the fist, and twisted about its length part of the way
     * toward {@code outer} (where the back of the hand faces as the wrist turns).
     */
    static void draw(PoseStack ps, MultiBufferSource buf, int light, AbstractClientPlayer p, boolean right, Vector3f fist, Vector3f outer) {
        float s = right ? 1 : -1;
        Vector3f shoulder = new Vector3f(s * SX, SY, SZ);
        Vector3f y = new Vector3f(fist).sub(shoulder).normalize();          // down the arm, toward the fist
        Quaternionf qv = vanilla(s);
        Quaternionf q = new Quaternionf().rotationTo(qv.transform(new Vector3f(0, 1, 0)), y).mul(qv);
        // the twist: part of the way toward where the back of the hand should face
        Vector3f now = q.transform(new Vector3f(-s, 0, 0));
        Vector3f want = new Vector3f(outer).sub(new Vector3f(y).mul(outer.dot(y)));
        now.sub(new Vector3f(y).mul(now.dot(y)));
        if (want.lengthSquared() > 1e-4f && now.lengthSquared() > 1e-4f) {
            float ang = (float) Math.atan2(new Vector3f(now).cross(want).dot(y), now.dot(want));
            q = new Quaternionf().rotationAxis(ang * 0.6f, y).mul(q);
        }
        boolean slim = "slim".equals(p.getModelName());
        float cx = (right ? -1 : 1) * (slim ? 0.5f : 1f);                   // the middle of the arm, across
        PlayerRenderer r = (PlayerRenderer) Minecraft.getInstance().getEntityRenderDispatcher().getRenderer(p);
        PlayerModel<AbstractClientPlayer> model = r.getModel();
        ModelPart arm = right ? model.rightArm : model.leftArm, sleeve = right ? model.rightSleeve : model.leftSleeve;
        PartPose a = arm.storePose(), b = sleeve.storePose();
        boolean av = arm.visible, bv = sleeve.visible;
        ps.pushPose();
        try {
            ps.last().pose().set(ROOT);
            ps.last().normal().set(ROOT_N);
            ps.translate(fist.x, fist.y, fist.z);
            ps.mulPose(q);
            // long enough to reach back past the shoulder (off screen) wherever the fist goes
            float reach = new Vector3f(fist).sub(shoulder).length() + 0.25f;
            float stretch = Math.max(1, reach / (10.5f / 16f * SCALE));
            ps.scale(SCALE, SCALE, SCALE);
            ps.scale(1, stretch, 1);
            ps.translate(-cx / 16f, -8.5f / 16f, 0);                         // (the fist is the last few pixels)
            arm.setPos(0, 0, 0);
            arm.setRotation(0, 0, 0);
            sleeve.setPos(0, 0, 0);
            sleeve.setRotation(0, 0, 0);
            arm.visible = true;
            sleeve.visible = p.isModelPartShown(right ? PlayerModelPart.RIGHT_SLEEVE : PlayerModelPart.LEFT_SLEEVE);
            var skin = p.getSkinTextureLocation();
            arm.render(ps, buf.getBuffer(RenderType.entitySolid(skin)), light, OverlayTexture.NO_OVERLAY);
            sleeve.render(ps, buf.getBuffer(RenderType.entityTranslucent(skin)), light, OverlayTexture.NO_OVERLAY);
        } finally {
            arm.loadPose(a);
            sleeve.loadPose(b);
            arm.visible = av;
            sleeve.visible = bv;
            ps.popPose();
        }
    }

    // ------------------------------------------------------------------ where an item is held
    /**
     * model-space points of an item (0..1 block): the grip, the far end (a blade's tip), the bottom, and its two sides
     * low down (where two hands hold a bowl)
     */
    record Points(Vector3f grip, Vector3f tip, Vector3f bottom, Vector3f lo, Vector3f hi, Vector3f mid) {}

    static final Map<BakedModel, Points> CACHE = new WeakHashMap<>();

    /**
     * Where a held thing is gripped: a long thing (a tool, a torch) just above the end of its handle (the far end is
     * whatever sticks out furthest from there); a lantern by its handle on top; anything else from underneath.
     */
    static Points points(BakedModel model, ItemStack stack, ItemKind kind) {
        boolean lantern = stack.getItem() instanceof BlockItem bi && bi.getBlock() instanceof net.minecraft.world.level.block.LanternBlock;
        boolean longThing = kind.tool() || kind == ItemKind.LIGHT && !lantern;
        return CACHE.computeIfAbsent(model, m -> {
            float minX = 9, minY = 9, minZ = 9, maxX = -9, maxY = -9, maxZ = -9;
            java.util.List<Vector3f> vs = new java.util.ArrayList<>();
            RandomSource rnd = RandomSource.create(42);
            for (Direction d : new Direction[]{null, Direction.UP, Direction.DOWN, Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST}) {
                for (BakedQuad bq : m.getQuads(null, d, rnd)) {
                    int[] v = bq.getVertices();
                    int stride = v.length / 4;
                    for (int i = 0; i < 4; i++) {
                        float x = Float.intBitsToFloat(v[i * stride]), y = Float.intBitsToFloat(v[i * stride + 1]), z = Float.intBitsToFloat(v[i * stride + 2]);
                        vs.add(new Vector3f(x, y, z));
                        minX = Math.min(minX, x); maxX = Math.max(maxX, x);
                        minY = Math.min(minY, y); maxY = Math.max(maxY, y);
                        minZ = Math.min(minZ, z); maxZ = Math.max(maxZ, z);
                    }
                }
            }
            if (vs.isEmpty()) return new Points(new Vector3f(0.5f, 0.3f, 0.5f), new Vector3f(0.5f, 1, 0.5f), new Vector3f(0.5f, 0, 0.5f),
                    new Vector3f(0.2f, 0.3f, 0.5f), new Vector3f(0.8f, 0.3f, 0.5f), new Vector3f(0.5f, 0.5f, 0.5f));
            Vector3f mid = new Vector3f((minX + maxX) / 2, (minY + maxY) / 2, (minZ + maxZ) / 2);
            float sideY = minY + (maxY - minY) * 0.3f;
            Vector3f lo = new Vector3f(minX + 0.03f, sideY, mid.z), hi = new Vector3f(maxX - 0.03f, sideY, mid.z);
            if (longThing) {
                // the bottom of the handle: the middle of the lowest points
                Vector3f bottom = new Vector3f();
                int n = 0;
                for (Vector3f v : vs) if (v.y <= minY + 0.02f) { bottom.add(v); n++; }
                bottom.div(Math.max(n, 1));
                Vector3f tip = bottom;
                float best = -1;
                for (Vector3f v : vs) {
                    float d = v.distanceSquared(bottom);
                    if (d > best) { best = d; tip = v; }
                }
                Vector3f grip = new Vector3f(bottom).lerp(tip, 0.16f);
                return new Points(grip, new Vector3f(tip), bottom, lo, hi, mid);
            }
            if (lantern) return new Points(new Vector3f(mid.x, maxY - 0.04f, mid.z), new Vector3f(mid.x, minY, mid.z), new Vector3f(mid.x, minY, mid.z), lo, hi, mid);
            Vector3f grip = new Vector3f(mid.x, minY + (maxY - minY) * 0.12f, mid.z);
            return new Points(grip, new Vector3f(mid.x, maxY, mid.z), new Vector3f(mid.x, minY, mid.z), lo, hi, mid);
        });
    }

    /**
     * The item's model as it will be drawn from this pose (overrides and display transform applied, as the game does),
     * and the pose its model space sits in.
     */
    static Object[] modelPose(PoseStack ps, AbstractClientPlayer p, ItemStack stack, boolean right) {
        var ir = Minecraft.getInstance().getItemRenderer();
        BakedModel model = ir.getModel(stack, p.level(), p, 0);
        PoseStack tmp = new PoseStack();
        tmp.last().pose().set(ps.last().pose());
        tmp.last().normal().set(ps.last().normal());
        BakedModel shown = net.minecraftforge.client.ForgeHooksClient.handleCameraTransforms(tmp, model,
                right ? ItemDisplayContext.FIRST_PERSON_RIGHT_HAND : ItemDisplayContext.FIRST_PERSON_LEFT_HAND, !right);
        tmp.translate(-0.5f, -0.5f, -0.5f);
        return new Object[]{shown, new Matrix4f(tmp.last().pose())};
    }
}
