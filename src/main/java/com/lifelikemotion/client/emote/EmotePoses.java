package com.lifelikemotion.client.emote;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;

/** How each emote looks: the body in third person, and your arms in first person. */
public final class EmotePoses {
    private EmotePoses() {}

    /** Third person: poses the model (called after everything else, so the emote wins). */
    public static void body(HumanoidModel<?> m, Player p, Emotes.Playing e, float partial) {
        float t = Emotes.time(e, partial);
        // ease in over the first few ticks, out over the last few
        float in = Mth.clamp(t / 5f, 0, 1);
        if (e.emote().duration > 0) in = Math.min(in, Mth.clamp((e.emote().duration - t) / 5f, 0, 1));
        in = in * in * (3 - 2 * in);
        boolean rightMain = p.getMainArm() == HumanoidArm.RIGHT;
        ModelPart main = rightMain ? m.rightArm : m.leftArm;
        float s = rightMain ? 1 : -1;
        switch (e.emote()) {
            case WAVE -> set(main, -0.25f, 0, s * (2.55f + Mth.sin(t * 0.7f) * 0.38f), in);
            case CLAP -> {
                // hands swing in to meet in front of the chest
                float inward = 0.6f - 0.38f * Math.abs(Mth.sin(t * 0.55f));
                set(m.rightArm, -1.25f, -inward, 0, in);
                set(m.leftArm, -1.25f, inward, 0, in);
            }
            case CHEER -> {
                float b = Math.abs(Mth.sin(t * 0.45f));
                set(m.rightArm, -2.85f + Mth.sin(t * 0.45f) * 0.2f, 0, 0.35f, in);
                set(m.leftArm, -2.85f - Mth.sin(t * 0.45f) * 0.2f, 0, -0.35f, in);
                lift(m, -1.6f * b * in);
            }
            case POINT -> set(main, m.head.xRot - Mth.HALF_PI, m.head.yRot, 0, in);
            case BOW -> {
                float b = Mth.sin(Mth.clamp(t / (e.emote().duration * 0.6f), 0, 1) * Mth.PI) * in;
                float lean = 0.65f * b;
                m.body.xRot += lean;
                m.head.xRot += 0.35f * b;
                m.rightLeg.z += 12 * Mth.sin(lean);
                m.leftLeg.z += 12 * Mth.sin(lean);
                m.head.z -= 3.5f * b;
                m.rightArm.z -= 3.5f * b;
                m.leftArm.z -= 3.5f * b;
                set(main, -0.85f, -s * 0.65f, 0, b);
                ModelPart other = rightMain ? m.leftArm : m.rightArm;
                set(other, 0.25f, 0, -s * 0.1f, b);
            }
            case FACEPALM -> {
                set(main, -2.15f, -s * 0.5f, 0, in);
                m.head.xRot += 0.35f * in;
                m.head.yRot += Mth.sin(t * 0.35f) * 0.18f * in;
            }
            case DANCE -> {
                float c = t * 0.5f;
                set(m.rightArm, Mth.sin(c) * 0.6f, 0, 0.6f + Mth.sin(c) * 0.9f, in);
                set(m.leftArm, -Mth.sin(c) * 0.6f, 0, -0.6f + Mth.sin(c) * 0.9f, in);
                set(m.rightLeg, Mth.sin(c) * 0.45f, 0, 0.05f, in);
                set(m.leftLeg, -Mth.sin(c) * 0.45f, 0, -0.05f, in);
                m.body.yRot += Mth.sin(c * 0.5f) * 0.35f * in;
                m.head.zRot += Mth.sin(c) * 0.15f * in;
                lift(m, -Math.abs(Mth.sin(c)) * 1.2f * in);
            }
            case SIT -> {
                // down on the ground, legs out, hands on the knees
                set(m.rightLeg, -1.45f, 0.12f, 0, in);
                set(m.leftLeg, -1.45f, -0.12f, 0, in);
                set(m.rightArm, -0.75f, 0.1f, 0, in);
                set(m.leftArm, -0.75f, -0.1f, 0, in);
                float d = 10.5f * in;
                m.head.y += d;
                m.body.y += d;
                m.rightArm.y += d;
                m.leftArm.y += d;
                m.rightLeg.y += d;
                m.leftLeg.y += d;
            }
        }
    }

    static void set(ModelPart p, float x, float y, float z, float k) {
        p.xRot = Mth.lerp(k, p.xRot, x);
        p.yRot = Mth.lerp(k, p.yRot, y);
        p.zRot = Mth.lerp(k, p.zRot, z);
    }

    static void lift(HumanoidModel<?> m, float dy) {
        m.head.y += dy;
        m.body.y += dy;
        m.rightArm.y += dy;
        m.leftArm.y += dy;
        m.rightLeg.y += dy;
        m.leftLeg.y += dy;
    }

    /**
     * First person: moves an empty arm's pose stack (before the arm is drawn) for the emote. Returns false when this
     * arm isn't part of the emote (it is then hidden).
     */
    public static boolean arm(PoseStack ps, Emotes.Playing e, boolean right, boolean mainArm, float partial) {
        float t = Emotes.time(e, partial);
        float k = Mth.clamp(t / 5f, 0, 1);
        if (e.emote().duration > 0) k = Math.min(k, Mth.clamp((e.emote().duration - t) / 5f, 0, 1));
        final float in = k * k * (3 - 2 * k);
        float s = right ? 1 : -1;
        switch (e.emote()) {
            case WAVE -> {
                if (!mainArm) return false;
                ps.translate(s * 0.05f * in, 0.42f * in, -0.05f * in);
                shoulder(ps, s, () -> ps.mulPose(Axis.ZP.rotationDegrees(s * (-20 + Mth.sin(t * 0.7f) * 22) * in)));
                return true;
            }
            case CLAP -> {
                float c = Math.abs(Mth.sin(t * 0.55f));
                ps.translate(-s * (0.2f + 0.18f * c) * in, 0.1f * in, -0.1f * in);
                shoulder(ps, s, () -> ps.mulPose(Axis.YP.rotationDegrees(s * (25 + 20 * c) * in)));
                return true;
            }
            case CHEER -> {
                ps.translate(s * 0.12f * in, (0.75f + Mth.sin(t * 0.45f) * 0.06f * s) * in, -0.15f * in);
                shoulder(ps, s, () -> ps.mulPose(Axis.XP.rotationDegrees(-35 * in)));
                return true;
            }
            case POINT -> {
                if (!mainArm) return false;
                ps.translate(-s * 0.2f * in, 0.12f * in, -0.15f * in);
                shoulder(ps, s, () -> ps.mulPose(Axis.YP.rotationDegrees(s * 22 * in)));
                return true;
            }
            case FACEPALM -> {
                if (!mainArm) return false;
                ps.translate(-s * 0.45f * in, 0.38f * in, 0.12f * in);
                shoulder(ps, s, () -> {
                    ps.mulPose(Axis.YP.rotationDegrees(s * 35 * in));
                    ps.mulPose(Axis.XP.rotationDegrees(-20 * in));
                });
                return true;
            }
            case DANCE -> {
                ps.translate(0, (0.2f + Mth.sin(t * 0.5f + (right ? 0 : Mth.PI)) * 0.15f) * in, 0);
                return true;
            }
            default -> {
                return false;
            }
        }
    }

    static void shoulder(PoseStack ps, float s, Runnable rot) {
        float bx = s * 0.64f, by = -0.6f, bz = -0.72f;
        ps.translate(bx, by, bz);
        rot.run();
        ps.translate(-bx, -by, -bz);
    }
}
