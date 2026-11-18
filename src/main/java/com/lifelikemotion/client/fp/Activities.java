package com.lifelikemotion.client.fp;

import com.lifelikemotion.client.ItemKind;
import com.lifelikemotion.client.Motion;
import com.lifelikemotion.config.LMConfig;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.animal.horse.AbstractHorse;
import net.minecraft.world.entity.vehicle.Boat;
import net.minecraftforge.event.TickEvent;

/**
 * What your hands do with the world, in first person:
 * - swimming: a breaststroke (both arms when your hands are empty)
 * - ladders and vines: hand over hand
 * - riding: holding the reins, bobbing with the horse's gait; in a boat, rowing
 * - on fire: patting at yourself
 * - waking up: a big stretch; dropping something (Q): a little toss
 * - blocking a hit with a shield: the shield knocked back
 * - drawing a bow a long time: the arm starts to tremble
 * Continuous ones fade in and out; each gives a pose {x, y, z, pitch, yaw, roll} (see {@link Clip}).
 */
public final class Activities {
    private Activities() {}

    public static float swim, swimO, climb, climbO, reins, reinsO, row, rowO, fire, fireO;
    public static double climbY;
    static boolean wasSleeping, dropWasDown;
    /** one-shot moves: [0] main hand, [1] off hand */
    static final Clip[] SHOT = new Clip[2];
    static final long[] SHOT_START = new long[2];
    static final int[] SHOT_TICKS = new int[2];
    public static float shieldKick, shieldKickO;
    /** client test: hold these on */
    public static String testActivity;

    public static void onClientTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (p == null || mc.isPaused()) return;
        swimO = swim; climbO = climb; reinsO = reins; rowO = row; fireO = fire; shieldKickO = shieldKick;
        boolean world = LMConfig.FP_WORLD_ACTIONS.get();
        var in = p.input;
        boolean pushing = in != null && (Math.abs(in.forwardImpulse) > 0.01f || Math.abs(in.leftImpulse) > 0.01f || in.jumping);
        boolean swimming = world && (p.isSwimming() || p.isInWater() && !p.onGround() && pushing && !p.isPassenger());
        boolean climbing = world && p.onClimbable() && !p.onGround() && Math.abs(p.getY() - p.yo) > 0.01;
        boolean horse = world && p.getVehicle() instanceof AbstractHorse;
        boolean boat = world && p.getVehicle() instanceof Boat && pushing;
        boolean burning = LMConfig.FP_REACTIONS.get() && p.isOnFire() && !p.fireImmune();
        String test = testActivity;
        if (test != null) {
            swimming = test.equals("swim");
            climbing = test.equals("climb");
            horse = test.equals("reins");
            boat = test.equals("row");
            burning = test.equals("fire");
        }
        swim += ((swimming ? 1 : 0) - swim) * 0.2f;
        climb += ((climbing ? 1 : 0) - climb) * 0.3f;
        reins += ((horse ? 1 : 0) - reins) * 0.2f;
        row += ((boat ? 1 : 0) - row) * 0.2f;
        fire += ((burning ? 1 : 0) - fire) * 0.3f;
        if (climbing) climbY = p.getY();
        shieldKick *= 0.7f;
        // woke up: stretch
        boolean sleeping = p.isSleeping();
        if (wasSleeping && !sleeping && world) {
            play(0, STRETCH, 40);
            play(1, STRETCH, 40);
        }
        wasSleeping = sleeping;
        // dropped something
        boolean drop = mc.options.keyDrop.isDown();
        if (drop && !dropWasDown && world && !p.getMainHandItem().isEmpty() && mc.screen == null) play(0, Clips.TOSS, 10);
        dropWasDown = drop;
    }

    public static void play(int hand, Clip c, int ticks) {
        SHOT[hand] = c;
        SHOT_START[hand] = Motion.ticks;
        SHOT_TICKS[hand] = Math.max(1, Math.round(ticks / (float) (double) LMConfig.FP_SPEED.get()));
    }

    /** the shield took a hit (from the game's "blocked" event) */
    public static void shieldHit() {
        shieldKick = 1;
    }

    public static final Clip STRETCH = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.30f, 0.06f, 0.40f, -0.06f, -40, -10, -20,
            0.55f, 0.08f, 0.44f, -0.06f, -44, -12, -24,
            0.75f, 0.04f, 0.20f, -0.03f, -20, -6, -10,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** Both arms are drawn (even an empty off hand) while doing something two-handed. */
    public static boolean bothArms(float partial) {
        float k = Math.max(Math.max(Motion.lerp(swimO, swim, partial), Motion.lerp(climbO, climb, partial)),
                Math.max(Motion.lerp(reinsO, reins, partial), Motion.lerp(rowO, row, partial)));
        return k > 0.05f || SHOT[1] != null && Motion.ticks - SHOT_START[1] < SHOT_TICKS[1];
    }

    /** This hand's pose from what you are doing now (adds up the ones fading in and out). */
    public static float[] pose(LocalPlayer p, boolean main, float s, ItemKind kind, float partial) {
        float[] out = new float[6];
        float t = Motion.ticks + partial;
        float sp = (float) (double) LMConfig.FP_SPEED.get();
        boolean empty = kind == ItemKind.EMPTY;
        float hold = empty ? 1 : 0.45f; // a hand holding something does a smaller version
        // swimming: reach forward together, sweep out and back, draw in
        float k = Motion.lerp(swimO, swim, partial);
        if (k > 0.001f) {
            float c = (t * 0.11f * sp) % 1f;
            float[] q = SWIM.sample(c);
            add(out, q, k * hold);
        }
        // climbing: hand over hand, by how far you've climbed
        k = Motion.lerp(climbO, climb, partial);
        if (k > 0.001f) {
            float c = (float) ((climbY * 1.6 + (main ? 0 : 0.5)) % 1.0);
            if (c < 0) c += 1;
            add(out, CLIMB.sample(c), k * (empty ? 1 : 0.6f));
        }
        // reins: both hands low and forward, bobbing with the horse
        k = Motion.lerp(reinsO, reins, partial);
        if (k > 0.001f) {
            float gait = p.getVehicle() != null ? (float) p.getVehicle().getDeltaMovement().horizontalDistance() * 4 : 0;
            float bob = Mth.sin(t * 0.5f * sp) * 0.02f * Math.min(gait, 1);
            add(out, new float[]{-0.12f, -0.08f + bob, -0.12f, 20, 18, 0}, k * hold);
        }
        // rowing: round and round
        k = Motion.lerp(rowO, row, partial);
        if (k > 0.001f) {
            float a = t * 0.3f * sp;
            add(out, new float[]{-0.06f, -0.04f + Mth.sin(a) * 0.05f, -0.08f + Mth.cos(a) * 0.1f, 10 + Mth.cos(a) * 14, 10, 0}, k * hold);
        }
        // on fire: the main hand pats at you, quickly
        k = Motion.lerp(fireO, fire, partial);
        if (k > 0.001f && main) {
            float a = (t * 0.32f * sp) % 1f;
            float pat = a < 0.4f ? Mth.sin(a / 0.4f * Mth.PI) : 0;
            add(out, new float[]{-0.26f, 0.16f - pat * 0.12f, 0.06f, -20 + pat * 35, 34, 14}, k * (empty ? 1 : 0.5f));
        }
        // a one-shot (stretch, toss)
        int h = main ? 0 : 1;
        if (SHOT[h] != null) {
            float u = (Motion.ticks - SHOT_START[h] + partial) / SHOT_TICKS[h];
            if (u >= 1) SHOT[h] = null;
            else add(out, SHOT[h].sample(u), 1);
        }
        // the shield knocked back by a blocked hit
        if (p.isBlocking()) {
            float kk = Motion.lerp(shieldKickO, shieldKick, partial);
            add(out, new float[]{0, 0.02f, 0.10f, -14, 0, 4}, kk);
        }
        // a bow held drawn for long: the arm trembles
        if (p.isUsingItem() && (p.getUseItem().getItem() instanceof net.minecraft.world.item.BowItem) && p.getUsedItemHand() == (main ? net.minecraft.world.InteractionHand.MAIN_HAND : net.minecraft.world.InteractionHand.OFF_HAND)) {
            float held = p.getTicksUsingItem() + partial;
            float tr = Mth.clamp((held - 30) / 60f, 0, 1) * (LMConfig.FP_REACTIONS.get() ? 1 : 0);
            if (tr > 0) add(out, new float[]{Mth.sin(t * 2.7f) * 0.004f * tr, Mth.sin(t * 3.3f) * 0.005f * tr, 0, Mth.sin(t * 3.1f) * 1.2f * tr, 0, Mth.sin(t * 2.3f) * 1.0f * tr}, 1);
        }
        return out;
    }

    static void add(float[] out, float[] q, float k) {
        for (int i = 0; i < 6; i++) out[i] += q[i] * k;
    }

    static final Clip SWIM = Clip.of(
            0.00f, -0.08f, 0.02f, 0.02f, -10, 20, 0,
            0.25f, -0.10f, 0.08f, -0.24f, -16, 26, 0,
            0.50f, 0.10f, 0.04f, -0.16f, 0, -14, -10,
            0.75f, 0.04f, -0.06f, 0.06f, 12, 0, 0,
            1.00f, -0.08f, 0.02f, 0.02f, -10, 20, 0);
    static final Clip CLIMB = Clip.of(
            0.00f, -0.06f, -0.06f, -0.04f, 0, 12, 0,
            0.45f, -0.08f, 0.26f, -0.12f, -30, 14, 0,
            0.55f, -0.08f, 0.24f, -0.12f, -26, 14, 0,
            1.00f, -0.06f, -0.06f, -0.04f, 0, 12, 0);
}
