package com.lifelikemotion.client.fp;

import com.lifelikemotion.client.ItemKind;
import com.lifelikemotion.client.Motion;
import com.lifelikemotion.config.LMConfig;
import com.mojang.blaze3d.platform.InputConstants;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.item.*;
import net.minecraftforge.client.event.RegisterKeyMappingsEvent;
import net.minecraftforge.client.settings.KeyConflictContext;
import net.minecraftforge.event.TickEvent;
import org.lwjgl.glfw.GLFW;

/**
 * Plays a show-off move with what is in your main hand when you press the show-off key (Y), or (if switched on) by
 * itself after you have stood still for a moment, now and then. Moving, swinging, using or switching the
 * item ends it smoothly.
 */
public final class Flourish {
    private Flourish() {}

    public static final KeyMapping KEY = new KeyMapping("key.lifelikemotion.inspect", KeyConflictContext.IN_GAME,
            InputConstants.Type.KEYSYM.getOrCreate(GLFW.GLFW_KEY_Y), "key.categories.lifelikemotion");

    static Flourishes.Move playing;
    static long start, stopAt = -1;
    static int still, nextAt = 50, pick;
    static Item pickedFor;
    static Item playingItem;
    /** client test: shows this move frozen at this point */
    public static Flourishes.Move testMove;
    public static float testTime;
    /** where moves turn about, relative to the hand: the middle of a held item (x toward the hand's side, y up) */
    public static Float pivotX, pivotY, pivotZ;

    /** long things turn about their middle, small things about the palm, an empty hand about the wrist */
    static float[] pivotFor(ItemStack st) {
        Item i = st.getItem();
        if (i instanceof TridentItem) return new float[]{0.05f, 0.2f, 0};
        return switch (ItemKind.of(st)) {
            case SWORD, AXE, PICKAXE, SHOVEL, HOE, ROD -> new float[]{0.05f, 0.2f, 0};
            case EMPTY -> new float[]{-0.02f, 0.28f, -0.02f};
            case SPECIAL -> new float[]{0, 0.08f, 0};
            default -> new float[]{0.02f, 0.08f, 0};
        };
    }

    public static void registerKeys(RegisterKeyMappingsEvent e) {
        e.register(KEY);
    }

    /** The moves that suit an item (one is picked in turn). */
    static Flourishes.Move[] movesFor(ItemStack s) {
        Item i = s.getItem();
        // only swords and the four tools show off
        if (i instanceof SwordItem) return new Flourishes.Move[]{Flourishes.SWORD_INSPECT, Flourishes.SWORD_TOSS, Flourishes.SWORD_SALUTE};
        if (i instanceof AxeItem || i instanceof PickaxeItem || i instanceof HoeItem || i instanceof ShovelItem)
            return new Flourishes.Move[]{Flourishes.TOOL_INSPECT, Flourishes.TOOL_FLIP, Flourishes.TOOL_SPIN_REST};
        return new Flourishes.Move[0];
    }

    public static void onClientTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (p == null || mc.isPaused()) return;
        boolean manual = false;
        while (KEY.consumeClick()) manual = true;
        ItemStack main = p.getMainHandItem();
        var in = p.input;
        boolean moving = in != null && (Math.abs(in.leftImpulse) > 0.01f || Math.abs(in.forwardImpulse) > 0.01f || in.jumping)
                || Motion.walk > 0.08f || !p.onGround() && !p.isPassenger();
        boolean busy = p.swinging || p.isUsingItem() || mc.gameMode != null && mc.gameMode.isDestroying() || mc.screen != null;
        // ends: you moved, swung, used it, or it's not in your hand any more
        if (playing != null && stopAt < 0) {
            boolean over = Motion.ticks - start > ticks(playing);
            if (over) playing = null;
            else if ((moving && !manualRun) || busy || main.getItem() != playingItem) stopAt = Motion.ticks;
        }
        if (playing != null && stopAt >= 0 && Motion.ticks - stopAt > FADE) playing = null;
        // flint and steel: sparks off each strike
        // its sounds
        if (playing != null && stopAt < 0)
            for (Flourishes.Cue c : playing.cues())
                if (Motion.ticks - start == Math.round(c.at() * ticks(playing)))
                    p.level().playLocalSound(p.getX(), p.getEyeY(), p.getZ(), c.sound(), net.minecraft.sounds.SoundSource.PLAYERS,
                            c.volume(), c.pitch() * (0.95f + p.getRandom().nextFloat() * 0.1f), false);
        if (playing == Flourishes.FLINT_STRIKE && stopAt < 0)
            for (float at : Flourishes.FLINT_SPARKS)
                if (Motion.ticks - start == Math.round(at * ticks(playing))) sparks(p);
        still = moving || busy ? 0 : still + 1;
        if (still == 0) nextAt = 50;
        boolean auto = LMConfig.FP_IDLE_SHOW.get() && still >= nextAt;
        if ((manual && !busy || auto && playing == null) && LMConfig.FP_ENABLED.get()) {
            Flourishes.Move[] moves = movesFor(main);
            if (moves.length > 0) {
                // a new item starts again from its first move (the inspect)
                if (main.getItem() != pickedFor) pick = 0;
                pickedFor = main.getItem();
                playing = moves[pick++ % moves.length];
                playingItem = main.getItem();
                start = Motion.ticks;
                stopAt = -1;
                manualRun = manual;
                nextAt = still + ticks(playing) + 100 + p.getRandom().nextInt(140);
            }
        }
    }

    /** a few sparks just in front of you, a little to the hand's side */
    static void sparks(LocalPlayer p) {
        var look = p.getLookAngle();
        double yaw = Math.toRadians(p.getYRot());
        double side = p.getMainArm() == net.minecraft.world.entity.HumanoidArm.RIGHT ? 1 : -1;
        double rx = -Math.cos(yaw) * side, rz = -Math.sin(yaw) * side;
        double x = p.getX() + look.x * 0.55 + rx * 0.18, y = p.getEyeY() + look.y * 0.55 - 0.12, z = p.getZ() + look.z * 0.55 + rz * 0.18;
        var lvl = p.level();
        for (int k = 0; k < 5; k++) {
            var r = p.getRandom();
            lvl.addParticle(k < 3 ? net.minecraft.core.particles.ParticleTypes.ELECTRIC_SPARK : net.minecraft.core.particles.ParticleTypes.SMALL_FLAME,
                    x, y, z, (r.nextDouble() - 0.5) * 0.06, r.nextDouble() * 0.04, (r.nextDouble() - 0.5) * 0.06);
        }
        lvl.playLocalSound(x, y, z, net.minecraft.sounds.SoundEvents.FLINTANDSTEEL_USE, net.minecraft.sounds.SoundSource.PLAYERS, 0.35f, 1.3f, false);
    }

    static int ticks(Flourishes.Move m) {
        return Math.max(1, Math.round(m.ticks() / (float) (double) LMConfig.FP_SPEED.get()));
    }

    static boolean manualRun;
    static final int FADE = 5;

    /** Applies the move being played (if any) to the main hand, about the given pivot. */
    public static void apply(PoseStack ps, float s, float partial, float px, float py, float pz) {
        Flourishes.Move m = testMove != null ? testMove : playing;
        if (m == null) return;
        float u = testMove != null ? testTime : (Motion.ticks - start + partial) / ticks(m);
        float w = 1;
        if (testMove == null && stopAt >= 0) w = Math.max(0, 1 - (Motion.ticks - stopAt + partial) / FADE);
        w = w * w * (3 - 2 * w);
        float[] pose = m.clip().sample(u);
        // spins: the nearest way back to rest, so fading out never unwinds a whole turn
        for (int i = 3; i < 6; i++) pose[i] = net.minecraft.util.Mth.wrapDegrees(pose[i]);
        LocalPlayer p = Minecraft.getInstance().player;
        float[] pv = p == null ? new float[3] : pivotFor(p.getMainHandItem());
        if (pivotX != null) pv = new float[]{pivotX, pivotY, pivotZ};
        // (the clip's own moves stay in hand space: only the turning is about the item's middle)
        ps.translate(s * pose[0] * w, pose[1] * w, pose[2] * w);
        Clip.apply(ps, new float[]{0, 0, 0, pose[3], pose[4], pose[5]}, s, w, px + s * pv[0], py + pv[1], pz + pv[2]);
    }

    /** the move playing (or shown for a test) and how far through it it is, or null */
    static Flourishes.Move current() {
        return testMove != null ? testMove : playing;
    }

    static float time(Flourishes.Move m, float partial) {
        return testMove != null ? testTime : (Motion.ticks - start + partial) / ticks(m);
    }

    /** how much of a stopped move is left (1 while it plays) */
    static float fadeOut(float partial) {
        float w = 1;
        if (testMove == null && stopAt >= 0) w = Math.max(0, 1 - (Motion.ticks - stopAt + partial) / FADE);
        return w * w * (3 - 2 * w);
    }

    /** the item's own pose on top of the hand's (thrown in the air), or null: x, y, z, pitch, yaw, roll */
    public static float[] itemPose(float partial) {
        Flourishes.Move m = current();
        if (m == null || m.item() == null) return null;
        float[] q = m.item().sample(time(m, partial));
        float w = fadeOut(partial);
        for (int i = 0; i < 6; i++) q[i] = (i >= 3 ? net.minecraft.util.Mth.wrapDegrees(q[i]) : q[i]) * w;
        return q;
    }

    /** your other hand on the item: where along it (0 grip .. 1 far end) and how much (0..1), or null */
    public static float[] offHand(float partial) {
        Flourishes.Move m = current();
        if (m == null || m.off() == null) return null;
        float[] q = m.off().sample(time(m, partial));
        float w = net.minecraft.util.Mth.clamp(q[1], 0, 1) * fadeOut(partial);
        return w <= 0.001f ? null : new float[]{net.minecraft.util.Mth.clamp(q[0], 0, 1), w * w * (3 - 2 * w)};
    }

    /** the middle a move turns the item about (hand space) */
    public static float[] pivot(ItemStack st) {
        return pivotX != null ? new float[]{pivotX, pivotY, pivotZ} : pivotFor(st);
    }

    /** how far the move being played has come in (0 none .. 1 fully): it eases in and out over a few ticks */
    public static float weight(float partial) {
        if (testMove != null) return 1;
        if (playing == null) return 0;
        float w = Math.min(1, (Motion.ticks - start + partial) / FADE);
        if (stopAt >= 0) w = Math.min(w, Math.max(0, 1 - (Motion.ticks - stopAt + partial) / FADE));
        // and out again near its end
        float u = (Motion.ticks - start + partial) / ticks(playing);
        w = Math.min(w, Math.max(0, (1 - u) * ticks(playing) / FADE));
        w = net.minecraft.util.Mth.clamp(w, 0, 1);
        return w * w * (3 - 2 * w);
    }

    public static boolean active() {
        return playing != null || testMove != null;
    }
}
