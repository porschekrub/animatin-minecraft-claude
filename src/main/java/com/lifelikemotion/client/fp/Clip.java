package com.lifelikemotion.client.fp;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.util.Mth;

/**
 * A first-person animation: keyframes of where the item (or fist) is, in 0..1 of the swing, joined by a smooth spline
 * so it moves in curves (wind-up, fast strike, overshoot, settle) rather than straight lines between poses.
 * A pose is {x, y, z, pitch, yaw, roll}: x toward the hand's own side, y up, z toward the camera; pitch + tips the item
 * forward/down, yaw + turns it in across the screen, roll + leans it in toward the middle. All are mirrored for the
 * left hand. Times must start at 0 and end at 1 (both normally the rest pose).
 */
public final class Clip {
    final float[] times;
    final float[][] poses;

    private Clip(float[] times, float[][] poses) {
        this.times = times;
        this.poses = poses;
    }

    /** of(t0, x,y,z,pitch,yaw,roll,  t1, ...) */
    public static Clip of(float... v) {
        int n = v.length / 7;
        float[] t = new float[n];
        float[][] p = new float[n][6];
        for (int i = 0; i < n; i++) {
            t[i] = v[i * 7];
            System.arraycopy(v, i * 7 + 1, p[i], 0, 6);
        }
        return new Clip(t, p);
    }

    /** The pose at time u (0..1): a Catmull-Rom spline through the keyframes (times may be uneven). */
    public float[] sample(float u) {
        u = Mth.clamp(u, 0, 1);
        int i = 0;
        while (i < times.length - 2 && u > times[i + 1]) i++;
        int i0 = Math.max(i - 1, 0), i2 = Math.min(i + 1, times.length - 1), i3 = Math.min(i + 2, times.length - 1);
        float t1 = times[i], t2 = times[i2];
        float span = Math.max(t2 - t1, 1e-4f);
        float x = (u - t1) / span;
        float x2 = x * x, x3 = x2 * x;
        float h00 = 2 * x3 - 3 * x2 + 1, h10 = x3 - 2 * x2 + x, h01 = -2 * x3 + 3 * x2, h11 = x3 - x2;
        float[] out = new float[6];
        for (int c = 0; c < 6; c++) {
            float p0 = poses[i0][c], p1 = poses[i][c], p2 = poses[i2][c], p3 = poses[i3][c];
            // tangents scaled to this segment's length (keeps uneven spacing smooth)
            float m1 = i0 == i ? 0 : (p2 - p0) / Math.max(times[i2] - times[i0], 1e-4f) * span;
            float m2 = i3 == i2 ? 0 : (p3 - p1) / Math.max(times[i3] - times[i], 1e-4f) * span;
            out[c] = h00 * p1 + h10 * m1 + h01 * p2 + h11 * m2;
        }
        return out;
    }

    /** Applies a pose about a pivot (the hand's grip), mirrored for the left hand (s = -1), scaled by k. */
    public static void apply(PoseStack ps, float[] p, float s, float k, float px, float py, float pz) {
        ps.translate(s * p[0] * k, p[1] * k, p[2] * k);
        ps.translate(s * px, py, pz);
        ps.mulPose(Axis.YP.rotationDegrees(s * p[4] * k));
        ps.mulPose(Axis.XP.rotationDegrees(p[3] * k));
        ps.mulPose(Axis.ZP.rotationDegrees(s * p[5] * k));
        ps.translate(-s * px, -py, -pz);
    }
}
