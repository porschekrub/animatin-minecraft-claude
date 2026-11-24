package com.lifelikemotion.client.fp;

import com.lifelikemotion.client.ItemKind;
import com.lifelikemotion.client.Motion;
import com.lifelikemotion.config.LMConfig;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.TieredItem;
import net.minecraft.world.item.Tiers;
import net.minecraftforge.client.event.ViewportEvent;
import net.minecraftforge.event.entity.player.AttackEntityEvent;
import org.joml.Matrix4f;
import org.joml.Vector3f;

/**
 * What makes a swing land: a trail behind the blade while it cuts, the camera kicked by each strike, and when it hits
 * something a short freeze (the swing stops for a moment on impact), a shake and a burst of sparks.
 */
public final class SwingFx {
    private SwingFx() {}

    // ------------------------------------------------------------------ the strike: when it lands, how the camera moves
    /** where in each swing it lands (0..1), and the camera's kick then (pitch, yaw, roll, in degrees a second) */
    static float impact(Clip c) {
        if (c == Clips.SLASH_A) return 0.40f;
        if (c == Clips.SLASH_B) return 0.42f;
        if (c == Clips.STAB) return 0.38f;
        if (c == Clips.CHOP) return 0.48f;
        if (c == Clips.MINE) return 0.54f;
        if (c == Clips.PUNCH) return 0.32f;
        if (c == Clips.SWAT) return 0.44f;
        if (c == Clips.DIG) return 0.46f;
        if (c == Clips.TILL) return 0.52f;
        if (c == Clips.THROW) return 0.42f;
        if (c == Clips.PLACE) return 0.34f;
        return -1;
    }

    static float[] kick(Clip c) {
        if (c == Clips.SLASH_A) return new float[]{10, -26, -30};
        if (c == Clips.SLASH_B) return new float[]{6, 26, 30};
        if (c == Clips.STAB) return new float[]{22, 0, 0};
        if (c == Clips.CHOP) return new float[]{45, 0, -6};
        if (c == Clips.MINE) return new float[]{10, 0, 0};
        if (c == Clips.PUNCH) return new float[]{16, 8, 4};
        if (c == Clips.SWAT) return new float[]{10, -12, -14};
        if (c == Clips.DIG || c == Clips.TILL) return new float[]{16, 0, 0};
        if (c == Clips.THROW) return new float[]{12, -8, -4};
        if (c == Clips.PLACE) return new float[]{10, 0, 0};
        return null;
    }

    /** a swing (by this hand, s = its side) just reached the point where it lands */
    static void landed(Clip c, float s) {
        float[] k = kick(c);
        if (k != null) Camera.kick(k[0], k[1] * s, k[2] * s);
        if (pendingTarget != null && Motion.ticks - pendingAt < 20) {
            hit(pendingTarget);
            pendingTarget = null;
        }
    }

    // ------------------------------------------------------------------ hitting something: freeze, shake, sparks
    static Entity pendingTarget;
    static long pendingAt;
    /** the freeze: from, to (in ticks, render time) */
    static float freezeFrom = -1e9f, freezeTo = -1e9f;

    public static void onAttack(AttackEntityEvent e) {
        Minecraft mc = Minecraft.getInstance();
        if (e.getEntity() != mc.player || !LMConfig.FP_ENABLED.get()) return;
        pendingTarget = e.getTarget();
        pendingAt = Motion.ticks;
    }

    static void hit(Entity target) {
        Minecraft mc = Minecraft.getInstance();
        float now = Motion.ticks + mc.getFrameTime();
        float k = (float) (double) LMConfig.FP_CAMERA.get();
        if (k > 0) {
            freezeFrom = now;
            freezeTo = now + 1.6f;                                            // 80 ms
            Camera.shake = Math.max(Camera.shake, 1);
            Camera.kick(-40, 0, 0);
        }
        var p = mc.player;
        if (p == null || target == null) return;
        var lvl = p.level();
        var r = p.getRandom();
        var at = target.getBoundingBox().getCenter();
        var look = p.getLookAngle();
        double x = at.x - look.x * target.getBbWidth() * 0.5, y = at.y + target.getBbHeight() * 0.15, z = at.z - look.z * target.getBbWidth() * 0.5;
        boolean magic = p.getMainHandItem().isEnchanted();
        for (int i = 0; i < 9; i++)
            lvl.addParticle(i % 3 == 2 && magic ? ParticleTypes.ENCHANTED_HIT : ParticleTypes.CRIT, x, y, z,
                    (r.nextDouble() - 0.5) * 0.7 - look.x * 0.2, r.nextDouble() * 0.45, (r.nextDouble() - 0.5) * 0.7 - look.z * 0.2);
    }

    /** the swing's own clock: stands still for the freeze */
    static float clock(float now, float since) {
        if (freezeFrom < since) return now;
        if (now < freezeFrom) return now;
        if (now < freezeTo) return freezeFrom;
        return now - (freezeTo - freezeFrom);
    }

    // ------------------------------------------------------------------ the trail behind a blade
    /** where in each swing the blade leaves a trail (from, to), or null */
    static float[] trailWindow(Clip c) {
        if (c == Clips.SLASH_A) return new float[]{0.28f, 0.54f};
        if (c == Clips.SLASH_B) return new float[]{0.30f, 0.56f};
        if (c == Clips.STAB) return new float[]{0.24f, 0.42f};
        if (c == Clips.CHOP) return new float[]{0.36f, 0.52f};
        if (c == Clips.SWAT) return new float[]{0.24f, 0.50f};
        return null;
    }

    static int[] trailColour(ItemStack s) {
        if (s.getItem() instanceof TieredItem t) {
            if (t.getTier() == Tiers.DIAMOND) return new int[]{130, 245, 255};
            if (t.getTier() == Tiers.NETHERITE) return new int[]{255, 150, 70};
            if (t.getTier() == Tiers.GOLD) return new int[]{255, 225, 110};
            if (t.getTier() == Tiers.WOOD || t.getTier() == Tiers.STONE) return new int[]{235, 230, 215};
        }
        if (s.is(Items.TRIDENT)) return new int[]{130, 255, 220};
        return new int[]{245, 248, 255};
    }

    /**
     * Draws the trail: the blade's path over the last part of the swing, from just above the grip to the tip, bright and
     * thick at the blade and fading out behind it. {@code base} is the hand's pose before the swing, {@code after} the
     * rest of the way to the item's model (both in absolute pose space), so earlier moments of the clip can be replayed.
     */
    static void trail(PoseStack ps, MultiBufferSource buf, Clip c, float u, float s, float k, Matrix4f base, Matrix4f after,
                      Arm.Points pts, ItemStack stack) {
        if (!LMConfig.FP_TRAILS.get()) return;
        float[] w = trailWindow(c);
        if (w == null || u < w[0]) return;
        float from = Math.max(w[0], u - 0.26f), to = Math.min(u, w[1]);
        if (to - from < 0.01f) return;
        int n = 12;
        Vector3f[] tip = new Vector3f[n + 1], mid = new Vector3f[n + 1];
        Vector3f t0 = pts.tip(), m0 = new Vector3f(pts.grip()).lerp(pts.tip(), 0.55f);
        for (int i = 0; i <= n; i++) {
            float ui = to - (to - from) * i / n;
            Matrix4f m = new Matrix4f(base).mul(clipMatrix(c.sample(ui), s, k)).mul(after);
            tip[i] = Arm.toRoot(m, t0.x, t0.y, t0.z);
            mid[i] = Arm.toRoot(m, m0.x, m0.y, m0.z);
        }
        int[] col = trailColour(stack);
        // the whole trail fades as the swing passes its end
        float fade = u <= w[1] ? 1 : Math.max(0, 1 - (u - w[1]) / 0.26f);
        ps.pushPose();
        ps.last().pose().set(Arm.ROOT);
        Matrix4f m = ps.last().pose();
        VertexConsumer vc = buf.getBuffer(RenderType.debugQuads());
        for (int i = 0; i < n; i++) {
            float a0 = (1 - i / (float) n) * 0.85f * fade, a1 = (1 - (i + 1) / (float) n) * 0.85f * fade;
            quad(vc, m, mid[i], tip[i], tip[i + 1], mid[i + 1], col, a0 * 0.25f, a0, a1, a1 * 0.25f);
        }
        ps.popPose();
    }

    static void quad(VertexConsumer vc, Matrix4f m, Vector3f a, Vector3f b, Vector3f c, Vector3f d, int[] col,
                     float aa, float ab, float ac, float ad) {
        vc.vertex(m, a.x, a.y, a.z).color(col[0], col[1], col[2], (int) (aa * 255)).endVertex();
        vc.vertex(m, b.x, b.y, b.z).color(255, 255, 255, (int) (ab * 255)).endVertex();
        vc.vertex(m, c.x, c.y, c.z).color(255, 255, 255, (int) (ac * 255)).endVertex();
        vc.vertex(m, d.x, d.y, d.z).color(col[0], col[1], col[2], (int) (ad * 255)).endVertex();
    }

    /** a clip pose as a matrix, as {@link Clip#apply} does it about the hand */
    static Matrix4f clipMatrix(float[] q, float s, float k) {
        if (q.length == 7) return Clip.armMatrix(q, s, k, FirstPersonAnimator.HX, FirstPersonAnimator.HY, FirstPersonAnimator.HZ);
        return new Matrix4f().translate(s * q[0] * k, q[1] * k, q[2] * k)
                .rotateY((float) Math.toRadians(s * q[4] * k))
                .rotateX((float) Math.toRadians(q[3] * k))
                .rotateZ((float) Math.toRadians(s * q[5] * k));
    }

    // ------------------------------------------------------------------ the camera
    /** kicks and shakes added to the camera in first person: springs that snap back */
    public static final class Camera {
        private Camera() {}

        static float pitch, yaw, roll, vp, vy, vr, shake;
        static float last = Float.NaN;

        static void kick(float p, float y, float r) {
            float k = (float) (double) LMConfig.FP_CAMERA.get();
            vp += p * k;
            vy += y * k;
            vr += r * k;
        }

        public static void onAngles(ViewportEvent.ComputeCameraAngles e) {
            Minecraft mc = Minecraft.getInstance();
            float now = Motion.ticks + (float) e.getPartialTick();
            float dt = Float.isNaN(last) ? 0.016f : Mth.clamp((now - last) * 0.05f, 0, 0.05f);
            last = now;
            if (mc.player == null || !LMConfig.FP_ENABLED.get() || mc.options.getCameraType() != CameraType.FIRST_PERSON) return;
            float k = 190, d = 15;
            vp += (-k * pitch - d * vp) * dt;
            vy += (-k * yaw - d * vy) * dt;
            vr += (-k * roll - d * vr) * dt;
            pitch += vp * dt;
            yaw += vy * dt;
            roll += vr * dt;
            float sp = 0, sy = 0;
            if (shake > 0.01f) {
                float t = (Motion.ticks + mc.getFrameTime()) * 2.1f;
                float a = shake * 1.1f * (float) (double) LMConfig.FP_CAMERA.get();
                sp = (Mth.sin(t * 3.1f) + Mth.sin(t * 5.3f + 1)) * 0.5f * a;
                sy = (Mth.sin(t * 2.7f + 2) + Mth.sin(t * 4.1f)) * 0.5f * a;
                shake *= (float) Math.exp(-dt * 11);
            }
            e.setPitch(e.getPitch() + pitch + sp);
            e.setYaw(e.getYaw() + yaw + sy);
            e.setRoll(e.getRoll() + roll);
        }
    }

    static boolean trails(ItemKind kind) {
        return kind.tool();
    }
}
