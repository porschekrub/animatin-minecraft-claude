package com.lifelikemotion.client.fp;

import com.lifelikemotion.client.ItemKind;
import com.lifelikemotion.client.Motion;
import com.lifelikemotion.config.LMConfig;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;

/**
 * How each kind of item is carried: one pose standing still (with breathing), one walking (swaying with each step) and
 * one running (tools over the shoulder, a sword low and ready, a torch held out in front, fists pumping...).
 * Blended by how fast you move. A pose is {x, y, z, pitch, yaw, roll} as in {@link Clip}; the step wobble is the same
 * six values, scaled by the step (side to side) and added on top.
 */
public final class Stance {
    private Stance() {}

    /** client test: this pose instead of the blend */
    public static float[] testPose;

    record Carry(float[] idle, float[] walk, float[] walkStep, float[] run, float[] runStep) {}

    static float[] p(float... v) {
        return v;
    }

    static final Carry BLADE = new Carry(
            p(0.01f, -0.02f, 0.01f, 4, -3, -4),
            p(0, -0.03f, 0.01f, 10, 12, 18), p(0.006f, 0.008f, 0, 3, 1.5f, 2),
            p(0.02f, -0.02f, 0.04f, -20, 10, 40), p(0.01f, 0.015f, 0.008f, 6, 2, 4));
    static final Carry SHOULDER = new Carry(
            p(0, -0.02f, 0.01f, 3, 0, -4),
            p(-0.03f, 0.0f, 0.0f, -12, 8, -8), p(0.006f, 0.008f, 0, 3, 1, 2),
            p(-0.04f, 0.14f, 0.02f, -70, 0, -25), p(0.008f, 0.018f, 0.006f, -4, 1, 2));
    static final Carry BLOCK = new Carry(
            p(0, -0.02f, 0.01f, 3, 2, 0),
            p(0, -0.02f, 0.0f, 4, 6, 0), p(0.006f, 0.014f, 0, 3, 2, 2),
            p(-0.04f, -0.01f, 0.03f, 6, 22, 2), p(0.01f, 0.02f, 0.006f, 6, 3, 3));
    static final Carry FOOD = new Carry(
            p(-0.01f, 0.01f, 0.02f, -4, 10, 0),
            p(-0.01f, -0.01f, 0.02f, 2, 12, 0), p(0.006f, 0.012f, 0, 3, 2, 3),
            p(-0.05f, -0.01f, 0.04f, 4, 24, 4), p(0.01f, 0.02f, 0.006f, 7, 3, 3));
    static final Carry LIGHT = new Carry(
            p(-0.02f, 0.03f, -0.03f, -5, 5, 0),
            p(-0.11f, 0.11f, -0.05f, -12, 14, 0), p(0.006f, 0.012f, 0, 2, 1, 3),
            p(-0.17f, 0.17f, -0.08f, -16, 18, 0), p(0.01f, 0.022f, 0.006f, 4, 2, 5));
    static final Carry EMPTY = new Carry(
            p(0, -0.03f, 0.02f, 4, 0, 0),
            p(0, -0.02f, 0.02f, 4, 0, 0), p(0.004f, 0.01f, 0.03f, 6, 0, 0),
            p(-0.02f, 0.04f, 0.0f, -12, 8, 0), p(0.01f, 0.03f, 0.09f, 18, 4, 0));
    static final Carry SPECIAL = new Carry(
            p(0, -0.02f, 0.01f, 3, 0, 0),
            p(0, -0.02f, 0.01f, 4, 4, 0), p(0.006f, 0.01f, 0, 3, 1, 2),
            p(-0.04f, 0.0f, 0.02f, 6, 16, 4), p(0.01f, 0.02f, 0.006f, 6, 2, 3));

    static Carry of(ItemKind k) {
        return switch (k) {
            case SWORD -> BLADE;
            case AXE, PICKAXE, SHOVEL, HOE, ROD -> SHOULDER;
            case BLOCK, OTHER -> BLOCK;
            case FOOD, DRINK, THROWABLE -> FOOD;
            case LIGHT -> LIGHT;
            case EMPTY -> EMPTY;
            case SPECIAL -> SPECIAL;
        };
    }

    /** The carry pose for this hand right now (blend of standing / walking / running), about the given pivot. */
    public static void apply(PoseStack ps, LocalPlayer p, ItemKind kind, float s, float partial, float px, float py, float pz) {
        float k = (float) (double) LMConfig.FP_BOB.get();
        if (k <= 0) return;
        Carry c = of(kind);
        float walk = Motion.lerp(Motion.walkO, Motion.walk, partial);
        float sprint = Motion.lerp(Motion.sprintO, Motion.sprint, partial);
        float busy = Motion.lerp(Motion.busyO, Motion.busy, partial);
        float t = Motion.ticks + partial;
        float phase = Mth.lerp(partial, p.walkDistO, p.walkDist) * Mth.PI;
        float wRun = sprint, wWalk = Math.min(walk * 1.4f, 1) * (1 - sprint), wIdle = Math.max(0, 1 - wRun - wWalk);
        // while swinging or using something the carry poses give way, so the swing starts from the hand
        float moveK = 1 - busy * 0.9f;
        // (x s: both hands sway the same way, and pump in turn)
        float step = Mth.sin(phase) * s, lift = Math.abs(Mth.cos(phase));
        float breath = Mth.sin(t * 0.08f);
        float[] out = new float[6];
        for (int i = 0; i < 6; i++) {
            float idle = c.idle()[i] * (1 + breath * 0.25f);
            float walkV = c.walk()[i] + c.walkStep()[i] * (i == 1 ? -lift : step);
            float runV = c.run()[i] + c.runStep()[i] * (i == 1 ? -lift : step);
            out[i] = (idle * wIdle + walkV * wWalk + runV * wRun) * moveK * k;
        }
        Clip.apply(ps, testPose != null ? testPose : out, s, 1, px, py, pz);
    }
}
