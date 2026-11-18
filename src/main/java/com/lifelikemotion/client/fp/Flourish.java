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
 * Plays a show-off move with what is in your main hand: by itself after you have stood still for a moment (then now and
 * then while you keep standing), or right away with the inspect key (I). Moving, swinging, using or switching the
 * item ends it smoothly.
 */
public final class Flourish {
    private Flourish() {}

    public static final KeyMapping KEY = new KeyMapping("key.lifelikemotion.inspect", KeyConflictContext.IN_GAME,
            InputConstants.Type.KEYSYM.getOrCreate(GLFW.GLFW_KEY_I), "key.categories.lifelikemotion");

    static Flourishes.Move playing;
    static long start, stopAt = -1;
    static int still, nextAt = 50, pick;
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
        if (i instanceof BowItem || i instanceof CrossbowItem) return new Flourishes.Move[]{Flourishes.BOW_PLUCK};
        if (i instanceof ShieldItem) return new Flourishes.Move[]{Flourishes.SHIELD_BRACE};
        if (i instanceof TridentItem) return new Flourishes.Move[]{Flourishes.TRIDENT_SPIN};
        return switch (ItemKind.of(s)) {
            case SWORD -> new Flourishes.Move[]{Flourishes.SWORD_TWIRL_WIPE, Flourishes.SWORD_FLIP};
            case AXE -> new Flourishes.Move[]{Flourishes.TOOL_TOSS, Flourishes.TOOL_SHOULDER};
            case PICKAXE, HOE -> new Flourishes.Move[]{Flourishes.TOOL_TWIRL, Flourishes.TOOL_SHOULDER, Flourishes.TOOL_TOSS};
            case SHOVEL -> new Flourishes.Move[]{Flourishes.SHOVEL_SPIN, Flourishes.TOOL_SHOULDER};
            case ROD -> new Flourishes.Move[]{Flourishes.ROD_FLICK};
            case BLOCK -> new Flourishes.Move[]{Flourishes.SMALL_TOSS, Flourishes.TURN_OVER};
            case FOOD, DRINK -> new Flourishes.Move[]{Flourishes.TURN_OVER, Flourishes.SMALL_TOSS};
            case THROWABLE -> new Flourishes.Move[]{Flourishes.JUGGLE, Flourishes.SMALL_TOSS};
            case LIGHT -> new Flourishes.Move[]{Flourishes.LIGHT_RAISE};
            case EMPTY -> new Flourishes.Move[]{Flourishes.HAND_FLEX, Flourishes.HAND_CRACK};
            case OTHER -> new Flourishes.Move[]{Flourishes.TURN_OVER, Flourishes.SMALL_TOSS};
            case SPECIAL -> new Flourishes.Move[0];
        };
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
            boolean over = Motion.ticks - start > playing.ticks();
            if (over) playing = null;
            else if ((moving && !manualRun) || busy || main.getItem() != playingItem) stopAt = Motion.ticks;
        }
        if (playing != null && stopAt >= 0 && Motion.ticks - stopAt > FADE) playing = null;
        still = moving || busy ? 0 : still + 1;
        if (still == 0) nextAt = 50;
        boolean auto = LMConfig.FP_IDLE_SHOW.get() && still >= nextAt;
        if ((manual && !busy || auto && playing == null) && LMConfig.FP_ENABLED.get()) {
            Flourishes.Move[] moves = movesFor(main);
            if (moves.length > 0) {
                playing = moves[pick++ % moves.length];
                playingItem = main.getItem();
                start = Motion.ticks;
                stopAt = -1;
                manualRun = manual;
                nextAt = still + playing.ticks() + 100 + p.getRandom().nextInt(140);
            }
        }
    }

    static boolean manualRun;
    static final int FADE = 5;

    /** Applies the move being played (if any) to the main hand, about the given pivot. */
    public static void apply(PoseStack ps, float s, float partial, float px, float py, float pz) {
        Flourishes.Move m = testMove != null ? testMove : playing;
        if (m == null) return;
        float u = testMove != null ? testTime : (Motion.ticks - start + partial) / m.ticks();
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

    public static boolean active() {
        return playing != null || testMove != null;
    }
}
