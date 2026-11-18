package com.lifelikemotion.client.fp;

import com.lifelikemotion.client.ItemKind;
import com.lifelikemotion.client.Motion;
import com.lifelikemotion.config.LMConfig;
import com.lifelikemotion.mixin.ItemInHandRendererInvoker;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.player.PlayerRenderer;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.client.event.RenderHandEvent;

/**
 * First-person hands with weight: your arm holds what you carry, swings are big and readable (sword slashes that
 * alternate forehand / backhand, overhead axe chops, quick pickaxe strikes, shovel scoops, punches that jab), and the
 * whole rig lags behind when you turn, bobs when you walk, pumps when you sprint, trails your jumps and dips when you
 * land. Items the game draws its own special way (bows, maps, shields...) keep their own motion but still sway.
 */
public final class FirstPersonAnimator {
    private FirstPersonAnimator() {}

    static float lastFrameKey = Float.NaN;
    /** client test: holds a swing at this point so a screenshot catches it */
    public static Float testSwing;
    /** where the arm sits relative to the item (x toward the arm's side, y up, z toward the camera) */
    public static float[] TOOL_GRIP = {0, 0, 0}, SMALL_GRIP = {0, -0.08f, -0.15f};

    public static void onRenderHand(RenderHandEvent e) {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (p == null || !LMConfig.FP_ENABLED.get()) return;
        float partial = e.getPartialTick();
        float key = Motion.ticks * 2f + partial;
        if (key != lastFrameKey) {
            lastFrameKey = key;
            Motion.frame(p, partial, (float) (double) LMConfig.FP_SWAY.get());
        }
        InteractionHand hand = e.getHand();
        boolean right = (hand == InteractionHand.MAIN_HAND) == (p.getMainArm() == HumanoidArm.RIGHT);
        float s = right ? 1 : -1;
        ItemStack stack = e.getItemStack();
        ItemKind kind = ItemKind.of(stack);
        // an emote: your arms do it
        var emote = com.lifelikemotion.client.emote.Emotes.of(p);
        if (emote != null && !p.isInvisible()) {
            e.setCanceled(true);
            PoseStack eps = e.getPoseStack();
            eps.pushPose();
            try {
                rig(eps, p, s, ItemKind.EMPTY, false, partial);
                if (com.lifelikemotion.client.emote.EmotePoses.arm(eps, emote, right, hand == InteractionHand.MAIN_HAND, partial))
                    vanillaArm(eps, e.getMultiBufferSource(), e.getPackedLight(), p, right);
            } finally {
                eps.popPose();
            }
            return;
        }
        // an empty off hand is not drawn (as in the game), unless both hands are busy (swimming, climbing, reins...)
        if (kind == ItemKind.EMPTY && hand == InteractionHand.OFF_HAND && (!Activities.bothArms(partial) || p.isInvisible())) {
            e.setCanceled(true);
            return;
        }
        PoseStack ps = e.getPoseStack();
        float swingProgress = testSwing != null && hand == InteractionHand.MAIN_HAND ? testSwing : e.getSwingProgress();
        // faster than the game's own swing if asked (never slower: the swing would be cut short)
        float speed = (float) (double) LMConfig.FP_SPEED.get();
        if (speed > 1 && swingProgress > 0) swingProgress = Math.min(1, swingProgress * speed);
        boolean using = p.isUsingItem() && p.getUseItemRemainingTicks() > 0 && p.getUsedItemHand() == hand;
        boolean eating = using && (kind == ItemKind.FOOD || kind == ItemKind.DRINK);
        e.setCanceled(true);
        ps.pushPose();
        try {
            rig(ps, p, s, kind, using, partial);
            float px = kind == ItemKind.EMPTY ? 0.64f : 0.56f, py = kind == ItemKind.EMPTY ? -0.6f : -0.52f;
            boolean mainHand = hand == InteractionHand.MAIN_HAND;
            if (!p.isAutoSpinAttack()) {
                // physics (inertia, floating, flutter, pendulum, slosh), then what you're doing with the world
                float[] ph = ItemPhysics.pose(mainHand, partial);
                Clip.apply(ps, new float[]{ph[0] * s, ph[1], ph[2], ph[3], ph[4] * s, ph[5] * s}, s, 1, px, py, -0.72f);
                Clip.apply(ps, Activities.pose(p, mainHand, s, kind, partial), s, 1, px, py, -0.72f);
            }
            if (!using && !p.isAutoSpinAttack()) {
                // how it's carried (standing / walking / running), and a show-off move when standing still
                Stance.apply(ps, p, kind, s, partial, px, py, -0.72f);
                if (mainHand) Flourish.apply(ps, s, partial, px, py, -0.72f);
            }
            if (kind == ItemKind.SPECIAL || (using && !eating) || p.isAutoSpinAttack()) {
                ((ItemInHandRendererInvoker) mc.getEntityRenderDispatcher().getItemInHandRenderer()).lm$renderArmWithItem(
                        p, partial, e.getInterpolatedPitch(), hand, swingProgress, stack, e.getEquipProgress(), ps, e.getMultiBufferSource(), e.getPackedLight());
            } else {
                // our own swing-in when the item changes; the game's attack-cooldown dip only as a light settle
                float equip = Motion.equip(hand == InteractionHand.MAIN_HAND, partial);
                ps.translate(0, -0.1f * e.getEquipProgress() * (1 - equip), 0);
                if (kind == ItemKind.EMPTY) {
                    if (!p.isInvisible()) emptyArm(ps, e.getMultiBufferSource(), e.getPackedLight(), p, right, swingProgress, equip);
                } else held(ps, e.getMultiBufferSource(), e.getPackedLight(), p, right, stack, kind, swingProgress, equip, eating, partial);
            }
        } finally {
            ps.popPose();
        }
    }

    /** client test: plays this clip instead of the one the item would choose */
    public static Clip testClip;

    // ------------------------------------------------------------------ the whole rig: sway, bob, run, jump, land
    /** Moves everything in this hand by how you move: all of it pivots about the hand, so nothing swings off screen. */
    static void rig(PoseStack ps, LocalPlayer p, float s, ItemKind kind, boolean using, float partial) {
        float bobK = (float) (double) LMConfig.FP_BOB.get();
        float t = Motion.ticks + partial;
        float sprint = Motion.lerp(Motion.sprintO, Motion.sprint, partial);
        float walk = Motion.lerp(Motion.walkO, Motion.walk, partial);
        float air = Motion.lerp(Motion.airO, Motion.air, partial);
        float sneak = Motion.lerp(Motion.sneakO, Motion.sneak, partial);
        float water = Motion.lerp(Motion.waterO, Motion.water, partial);
        float aim = using ? 0.35f : 1; // aiming a bow or eating: steadier
        float phase = Mth.lerp(partial, p.walkDistO, p.walkDist) * Mth.PI;
        float amt = walk * bobK * (1 + sprint * 0.5f) * aim;
        float ly = Motion.lagYaw * aim, lp = Motion.lagPitch * aim;
        // slides: trailing the camera, a soft figure of eight when walking, the jump, the landing spring, sneaking
        ps.translate(-ly * 0.0016f + Mth.sin(phase) * 0.010f * amt,
                lp * 0.0014f - Math.abs(Mth.cos(phase)) * 0.016f * amt - air * 0.03f * bobK + Motion.landPos * bobK
                        - 0.02f * sneak + Mth.sin(t * 0.075f) * 0.004f * bobK
                        + Mth.sin(t * 0.1f) * 0.012f * water,
                0.02f * sneak);
        // turns: about the hand
        float yaw = ly * 0.35f;
        float pitch = lp * 0.3f + Math.abs(Mth.cos(phase)) * 1.2f * amt + air * 4 * bobK - Motion.landPos * 60 * bobK
                + Mth.sin(t * 0.075f + 1) * 0.5f * bobK;
        float roll = ly * 0.25f + Mth.sin(phase) * 1.6f * amt + s * Mth.sin(t * 0.08f) * 3 * water;
        Clip.apply(ps, new float[]{0, 0, 0, pitch, s * yaw, s * roll}, s, 1, 0.56f, -0.52f, -0.72f);
    }

    // ------------------------------------------------------------------ an empty hand: jab punches
    static void emptyArm(PoseStack ps, MultiBufferSource buf, int light, AbstractClientPlayer p, boolean right, float sw, float equip) {
        float s = right ? 1 : -1;
        float k = (float) (double) LMConfig.FP_SWING.get();
        equip(ps, s, equip, 0.64f, -0.6f, -0.72f);
        if (sw > 0) {
            Clip own = actionClip(Motion.action);
            Clip c = testClip != null ? testClip : own != null ? own : Motion.action == Motion.Action.USE ? Clips.PLACE : Clips.PUNCH;
            Clip.apply(ps, c.sample(sw), s, k, 0.64f, -0.6f, -0.72f);
        }
        vanillaArm(ps, buf, light, p, right);
    }

    /** Switching to an item: it swings up into the hand from below, turning as it comes (instead of a straight drop). */
    static void equip(PoseStack ps, float s, float equip, float px, float py, float pz) {
        if (equip <= 0.001f) return;
        float e = equip * equip * (3 - 2 * equip);
        ps.translate(s * 0.08f * e, -0.6f * equip, 0.05f * e);
        Clip.apply(ps, new float[]{0, 0, 0, 30 * e, -12 * e, -20 * e}, s, 1, px, py, pz);
    }

    // ------------------------------------------------------------------ an item in the hand
    static void held(PoseStack ps, MultiBufferSource buf, int light, AbstractClientPlayer p, boolean right, ItemStack stack, ItemKind kind,
                     float sw, float equip, boolean eating, float partial) {
        float s = right ? 1 : -1;
        float k = (float) (double) LMConfig.FP_SWING.get();
        if (eating) eat(ps, p, s, stack, kind, partial);
        // the hand's place (the game's own), then the switch-in
        equip(ps, s, equip, 0.56f, -0.52f, -0.72f);
        ps.translate(s * 0.56f, -0.52f, -0.72f);
        if (!eating && sw > 0) {
            Clip c = testClip != null ? testClip : clipFor(kind);
            Clip.apply(ps, c.sample(sw), s, kind == ItemKind.PICKAXE && Motion.action != Motion.Action.MINE ? k * 0.8f : k, 0, 0, 0);
        }
        if (eating && (kind == ItemKind.DRINK || soup(stack))) {
            // a drink is tipped up to the lips; a bucket of milk much further; soup is lifted and slurped
            float m = toMouth(p, stack, partial);
            boolean bucket = stack.getItem() instanceof net.minecraft.world.item.MilkBucketItem;
            float tip = bucket ? -50 : soup(stack) ? -20 : -28;
            ps.translate(0, (bucket ? 0.12f : 0.06f) * m, 0);
            ps.mulPose(Axis.XP.rotationDegrees(tip * m));
            if (soup(stack)) ps.translate(0, Mth.sin((Motion.ticks + partial) * 0.6f) * 0.012f * m, 0);
        }
        if (kind == ItemKind.LIGHT && !ItemPhysics.hanging(hand(p, right)) || kind == ItemKind.LIGHT && !LMConfig.FP_PHYSICS.get()) {
            // a lantern / torch swings on the hand as you turn
            ps.mulPose(Axis.ZP.rotationDegrees(Motion.lagYaw * 0.9f));
            ps.mulPose(Axis.XP.rotationDegrees(Motion.lagPitch * 0.7f));
        }
        if (LMConfig.FP_ARMS_WITH_ITEMS.get() && !p.isInvisible()) {
            ps.pushPose();
            float[] g = kind.tool() || kind == ItemKind.BLOCK ? TOOL_GRIP : SMALL_GRIP;
            ps.translate(s * g[0], g[1], g[2]);
            ps.translate(s * -0.56f, 0.52f, 0.72f);
            holdingArm(ps, buf, light, p, right);
            ps.popPose();
        }
        Minecraft.getInstance().getEntityRenderDispatcher().getItemInHandRenderer().renderItem(p, stack,
                right ? ItemDisplayContext.FIRST_PERSON_RIGHT_HAND : ItemDisplayContext.FIRST_PERSON_LEFT_HAND, !right, ps, buf, light);
    }

    /** The swings that belong to an action rather than to what is held (pouring, opening a door...), or null. */
    static Clip actionClip(Motion.Action a) {
        return switch (a) {
            case POUR -> Clips.POUR;
            case SCOOP -> Clips.SCOOP;
            case STRIKE -> Clips.STRIKE;
            case SNIP -> Clips.SNIP;
            case SPRINKLE -> Clips.SPRINKLE;
            case TILL -> Clips.TILL;
            case STRIP -> Clips.STRIP;
            case FLATTEN -> Clips.FLATTEN;
            case CAST -> Clips.CAST;
            case REEL -> Clips.REEL;
            case OPEN -> Clips.OPEN;
            case PRESS -> Clips.PRESS;
            case PULL -> Clips.PULL;
            default -> null;
        };
    }

    /** Which swing, by what is held and what it is for. Swords run a three-hit combo. */
    static Clip clipFor(ItemKind kind) {
        Motion.Action a = Motion.action;
        Clip own = actionClip(a);
        if (own != null) return own;
        if (a == Motion.Action.USE) return kind == ItemKind.THROWABLE ? Clips.THROW : Clips.PLACE;
        return switch (kind) {
            case SWORD -> a == Motion.Action.MINE ? Clips.MINE : switch (Math.floorMod(Motion.swingCount, 3)) {
                case 0 -> Clips.SLASH_A;
                case 1 -> Clips.SLASH_B;
                default -> Clips.STAB;
            };
            case AXE -> Clips.CHOP;
            case PICKAXE -> a == Motion.Action.MINE ? Clips.MINE : Clips.CHOP;
            case SHOVEL -> Clips.DIG;
            case HOE -> Clips.TILL;
            case THROWABLE -> Clips.THROW;
            case ROD -> Clips.CHOP;
            default -> Clips.SWAT;
        };
    }

    /** bringing food or a drink to the mouth, chewing / sipping */
    static void eat(PoseStack ps, AbstractClientPlayer p, float s, ItemStack stack, ItemKind kind, float partial) {
        float f = p.getUseItemRemainingTicks() - partial + 1;
        float f1 = f / stack.getUseDuration();
        float f3 = 1 - (float) Math.pow(f1, 27);
        if (f1 < 0.8f) {
            boolean drink = kind == ItemKind.DRINK || soup(stack);
            float bob = drink ? Mth.sin(f * 0.5f) * 0.02f
                    : nibble(stack) ? Math.abs(Mth.cos(f / 2f * Mth.PI)) * 0.05f
                    : Math.abs(Mth.cos(f / 4f * Mth.PI) * 0.08f);
            ps.translate(0, bob, nibble(stack) ? -Math.abs(Mth.cos(f / 2f * Mth.PI)) * 0.03f : 0);
            if (!drink) ps.mulPose(Axis.ZP.rotationDegrees(Mth.sin(f * (nibble(stack) ? 1.6f : 0.8f)) * 4));
        }
        ps.translate(f3 * 0.6f * s, f3 * -0.5f, 0);
        ps.mulPose(Axis.YP.rotationDegrees(s * f3 * 90));
        ps.mulPose(Axis.XP.rotationDegrees(f3 * 10));
        ps.mulPose(Axis.ZP.rotationDegrees(s * f3 * 30));
    }

    static boolean hand(AbstractClientPlayer p, boolean right) {
        return right == (p.getMainArm() == HumanoidArm.RIGHT);
    }

    /** bowls of soup and stew are drunk from, not chewed */
    static boolean soup(ItemStack s) {
        return s.getItem() instanceof net.minecraft.world.item.BowlFoodItem || s.getItem() instanceof net.minecraft.world.item.SuspiciousStewItem;
    }

    /** small crunchy things are nibbled quickly */
    static boolean nibble(ItemStack s) {
        return s.is(net.minecraft.world.item.Items.CARROT) || s.is(net.minecraft.world.item.Items.GOLDEN_CARROT) || s.is(net.minecraft.world.item.Items.BEETROOT)
                || s.is(net.minecraft.world.item.Items.DRIED_KELP) || s.is(net.minecraft.world.item.Items.COOKIE) || s.is(net.minecraft.world.item.Items.SWEET_BERRIES)
                || s.is(net.minecraft.world.item.Items.GLOW_BERRIES) || s.is(net.minecraft.world.item.Items.MELON_SLICE) || s.is(net.minecraft.world.item.Items.POTATO);
    }

    /** how far food or a drink has come up to the mouth (0..1) */
    static float toMouth(AbstractClientPlayer p, ItemStack stack, float partial) {
        float f = p.getUseItemRemainingTicks() - partial + 1;
        return 1 - (float) Math.pow(f / stack.getUseDuration(), 27);
    }

    // ------------------------------------------------------------------ drawing the arm
    /** Rotate about the hand (not the camera). */
    static void around(PoseStack ps, float s, Runnable rot) {
        float bx = s * 0.56f, by = -0.52f, bz = -0.72f;
        ps.translate(bx, by, bz);
        rot.run();
        ps.translate(-bx, -by, -bz);
    }

    /** Rotate about the shoulder of the empty arm. */
    static void pivotArm(PoseStack ps, float s, Runnable rot) {
        float bx = s * 0.64f, by = -0.6f, bz = -0.72f;
        ps.translate(bx, by, bz);
        rot.run();
        ps.translate(-bx, -by, -bz);
    }

    /** The first-person arm turned about the shoulder so its hand grips the item. */
    static void holdingArm(PoseStack ps, MultiBufferSource buf, int light, AbstractClientPlayer p, boolean right) {
        float s = right ? 1 : -1;
        float sx = s * 0.4853f, sy = -0.8315f, sz = -0.5254f;
        ps.translate(s * -0.006f, 0.003f, 0.334f);
        ps.translate(sx, sy, sz);
        ps.mulPose(Axis.YP.rotationDegrees(s * 13.66f));
        ps.mulPose(Axis.XP.rotationDegrees(18.43f));
        ps.mulPose(Axis.ZP.rotationDegrees(s * -5.42f));
        ps.translate(-sx, -sy, -sz);
        vanillaArm(ps, buf, light, p, right);
    }

    /** The game's own first-person arm (no swing, fully raised). */
    static void vanillaArm(PoseStack ps, MultiBufferSource buf, int light, AbstractClientPlayer p, boolean right) {
        float s = right ? 1 : -1;
        ps.pushPose();
        ps.translate(s * 0.64000005f, -0.6f, -0.71999997f);
        ps.mulPose(Axis.YP.rotationDegrees(s * 45));
        ps.translate(s * -1.0f, 3.6f, 3.5f);
        ps.mulPose(Axis.ZP.rotationDegrees(s * 120));
        ps.mulPose(Axis.XP.rotationDegrees(200));
        ps.mulPose(Axis.YP.rotationDegrees(s * -135));
        ps.translate(s * 5.6f, 0, 0);
        PlayerRenderer r = (PlayerRenderer) Minecraft.getInstance().getEntityRenderDispatcher().getRenderer(p);
        if (right) r.renderRightHand(ps, buf, light, p);
        else r.renderLeftHand(ps, buf, light, p);
        ps.popPose();
    }

    static float ease(float x) {
        x = Mth.clamp(x, 0, 1);
        return x * x * (3 - 2 * x);
    }

    static float easeOut(float x) {
        x = Mth.clamp(x, 0, 1);
        return 1 - (1 - x) * (1 - x) * (1 - x);
    }
}
