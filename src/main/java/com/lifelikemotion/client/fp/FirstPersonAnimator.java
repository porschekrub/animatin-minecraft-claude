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
        // an empty off hand is not drawn (as in the game)
        if (kind == ItemKind.EMPTY && hand == InteractionHand.OFF_HAND) {
            e.setCanceled(true);
            return;
        }
        PoseStack ps = e.getPoseStack();
        float swingProgress = testSwing != null && hand == InteractionHand.MAIN_HAND ? testSwing : e.getSwingProgress();
        boolean using = p.isUsingItem() && p.getUseItemRemainingTicks() > 0 && p.getUsedItemHand() == hand;
        boolean eating = using && (kind == ItemKind.FOOD || kind == ItemKind.DRINK);
        e.setCanceled(true);
        ps.pushPose();
        try {
            rig(ps, p, s, kind, using, partial);
            if (kind == ItemKind.SPECIAL || (using && !eating) || p.isAutoSpinAttack()) {
                ((ItemInHandRendererInvoker) mc.getEntityRenderDispatcher().getItemInHandRenderer()).lm$renderArmWithItem(
                        p, partial, e.getInterpolatedPitch(), hand, swingProgress, stack, e.getEquipProgress(), ps, e.getMultiBufferSource(), e.getPackedLight());
            } else if (kind == ItemKind.EMPTY) {
                if (!p.isInvisible()) emptyArm(ps, e.getMultiBufferSource(), e.getPackedLight(), p, right, swingProgress, e.getEquipProgress());
            } else {
                held(ps, e.getMultiBufferSource(), e.getPackedLight(), p, right, stack, kind, swingProgress, e.getEquipProgress(), eating, partial);
            }
        } finally {
            ps.popPose();
        }
    }

    // ------------------------------------------------------------------ the whole rig: sway, bob, run, jump, land
    static void rig(PoseStack ps, LocalPlayer p, float s, ItemKind kind, boolean using, float partial) {
        float bobK = (float) (double) LMConfig.FP_BOB.get();
        float t = Motion.ticks + partial;
        float sprint = Motion.lerp(Motion.sprintO, Motion.sprint, partial);
        float walk = Motion.lerp(Motion.walkO, Motion.walk, partial);
        float air = Motion.lerp(Motion.airO, Motion.air, partial);
        float land = Motion.lerp(Motion.landO, Motion.land, partial);
        float sneak = Motion.lerp(Motion.sneakO, Motion.sneak, partial);
        float water = Motion.lerp(Motion.waterO, Motion.water, partial);
        float aim = using ? 0.35f : 1; // aiming a bow or eating: steadier
        // looking around: the hands trail the camera (rotate about the eye, then a little slide)
        ps.mulPose(Axis.YP.rotationDegrees(Motion.lagYaw * 0.55f * aim));
        ps.mulPose(Axis.XP.rotationDegrees(Motion.lagPitch * 0.45f * aim));
        ps.translate(-Motion.lagYaw * 0.0025f * aim, Motion.lagPitch * 0.002f * aim, 0);
        // walking: a figure of eight; sprinting: bigger, and tools are held lower and pump with each step
        float phase = Mth.lerp(partial, p.walkDistO, p.walkDist) * Mth.PI;
        float amt = walk * bobK * (1 + sprint * 0.7f) * aim;
        ps.translate(Mth.sin(phase) * 0.022f * amt, -Math.abs(Mth.cos(phase)) * 0.032f * amt, 0);
        if (sprint > 0.01f && !using) {
            float k = sprint * bobK;
            ps.translate(s * 0.03f * k, -0.035f * k, 0.02f * k);
            around(ps, s, () -> {
                ps.mulPose(Axis.XP.rotationDegrees((kind.tool() ? 12 : 7) * k + Mth.sin(phase) * 6 * k));
                ps.mulPose(Axis.ZP.rotationDegrees(s * 8 * k));
            });
        }
        // in the air the hands trail the jump; landing dips them
        ps.translate(0, -air * 0.075f * bobK, 0);
        ps.translate(0, -land * 0.11f * bobK, land * 0.03f * bobK);
        if (land > 0.01f) around(ps, s, () -> ps.mulPose(Axis.XP.rotationDegrees(land * 9 * bobK)));
        // sneaking: low and close; in water: floaty
        ps.translate(0, -0.04f * sneak, 0.03f * sneak);
        if (water > 0.01f) {
            ps.translate(Mth.sin(t * 0.07f) * 0.015f * water, Mth.sin(t * 0.1f) * 0.02f * water, 0);
            around(ps, s, () -> ps.mulPose(Axis.ZP.rotationDegrees(s * Mth.sin(t * 0.08f) * 3 * water)));
        }
        // breathing
        ps.translate(0, Mth.sin(t * 0.075f) * 0.006f * bobK, 0);
    }

    // ------------------------------------------------------------------ an empty hand: jab punches
    static void emptyArm(PoseStack ps, MultiBufferSource buf, int light, AbstractClientPlayer p, boolean right, float sw, float equip) {
        float s = right ? 1 : -1;
        float k = (float) (double) LMConfig.FP_SWING.get();
        ps.translate(0, equip * -0.6f, 0);
        if (sw > 0) {
            if (Motion.action == Motion.Action.USE) {
                float b = Mth.sin(sw * Mth.PI);
                ps.translate(-s * 0.05f * b * k, 0.04f * b * k, -0.18f * b * k);
            } else {
                // straight out fast, back slower
                float jab = sw < 0.3f ? Mth.sin(sw / 0.3f * Mth.HALF_PI) : 1 - ease((sw - 0.3f) / 0.7f);
                ps.translate(-s * 0.16f * jab * k, 0.08f * jab * k, -0.42f * jab * k);
                pivotArm(ps, s, () -> {
                    ps.mulPose(Axis.YP.rotationDegrees(s * 14 * jab * k));
                    ps.mulPose(Axis.XP.rotationDegrees(-12 * jab * k));
                });
            }
        }
        vanillaArm(ps, buf, light, p, right);
    }

    // ------------------------------------------------------------------ an item in the hand
    static void held(PoseStack ps, MultiBufferSource buf, int light, AbstractClientPlayer p, boolean right, ItemStack stack, ItemKind kind,
                     float sw, float equip, boolean eating, float partial) {
        float s = right ? 1 : -1;
        float k = (float) (double) LMConfig.FP_SWING.get();
        if (eating) eat(ps, p, s, stack, kind, partial);
        // the hand's place (the game's own)
        ps.translate(s * 0.56f, -0.52f + equip * -0.6f, -0.72f);
        if (!eating && sw > 0) swing(ps, s, kind, sw, k);
        if (eating && kind == ItemKind.DRINK) {
            // a drink is tipped up to the lips
            float m = toMouth(p, stack, partial);
            ps.translate(0, 0.06f * m, 0);
            ps.mulPose(Axis.XP.rotationDegrees(-28 * m));
        }
        if (kind == ItemKind.LIGHT) {
            // a lantern / torch swings on the hand as you turn
            ps.mulPose(Axis.ZP.rotationDegrees(Motion.lagYaw * 1.1f));
            ps.mulPose(Axis.XP.rotationDegrees(Motion.lagPitch * 0.9f));
        }
        if (LMConfig.FP_ARMS_WITH_ITEMS.get() && !p.isInvisible()) {
            ps.pushPose();
            // tools are gripped at the end of the handle; small things (torches, food, bottles) from underneath
            float[] g = kind.tool() || kind == ItemKind.BLOCK ? TOOL_GRIP : SMALL_GRIP;
            ps.translate(s * g[0], g[1], g[2]);
            ps.translate(s * -0.56f, 0.52f, 0.72f);
            holdingArm(ps, buf, light, p, right);
            ps.popPose();
        }
        Minecraft.getInstance().getEntityRenderDispatcher().getItemInHandRenderer().renderItem(p, stack,
                right ? ItemDisplayContext.FIRST_PERSON_RIGHT_HAND : ItemDisplayContext.FIRST_PERSON_LEFT_HAND, !right, ps, buf, light);
    }

    /**
     * One swing, by what is held and what it is for. The motion is a wind-up (the first ~20%), a fast strike and a
     * slower recovery: "theta" goes 0 → -1 (wound up) → +1 (follow-through) → 0.
     */
    static void swing(PoseStack ps, float s, ItemKind kind, float sw, float k) {
        Motion.Action a = Motion.action;
        if (a == Motion.Action.USE) {
            // putting something down / using it: a push forward
            float b = Mth.sin(sw * Mth.PI) * k;
            ps.translate(-s * 0.04f * b, 0.03f * b, -0.2f * b);
            ps.mulPose(Axis.XP.rotationDegrees(14 * b));
            return;
        }
        float wind = sw < 0.2f ? 0.2f : 0.18f;
        float theta = sw < wind ? -ease(sw / wind)
                : sw < 0.5f ? -1 + 2 * easeOut((sw - wind) / (0.5f - wind))
                : 1 - ease((sw - 0.5f) / 0.5f);
        float up = Math.max(-theta, 0) * k, dn = Math.max(theta, 0) * k;
        switch (kind) {
            case SWORD -> {
                if (a == Motion.Action.MINE) {
                    chop(ps, up * 0.5f, dn * 0.6f);
                    return;
                }
                // a slash across the screen; every other one comes back the other way
                boolean back = (Motion.swingCount & 1) == 0;
                if (!back) {
                    // raised up on the sword side, then cut across the middle of the screen, the blade laid flat
                    ps.translate(s * 0.06f * up - s * 0.3f * dn, 0.14f * up - 0.02f * dn, 0.05f * up - 0.12f * dn);
                    ps.mulPose(Axis.YP.rotationDegrees(s * (15 * up - 35 * dn)));
                    ps.mulPose(Axis.ZP.rotationDegrees(s * (25 * up + 40 * dn)));
                    ps.mulPose(Axis.XP.rotationDegrees(-30 * up + 5 * dn));
                } else {
                    // backhand: wound up low across the body, then swept back out and up to the right
                    ps.translate(-s * 0.3f * up + s * 0.02f * dn, -0.03f * up + 0.07f * dn, -0.08f * up - 0.08f * dn);
                    ps.mulPose(Axis.YP.rotationDegrees(s * (-40 * up + 10 * dn)));
                    ps.mulPose(Axis.ZP.rotationDegrees(s * (35 * up - 25 * dn)));
                    ps.mulPose(Axis.XP.rotationDegrees(10 * up - 15 * dn));
                }
            }
            case AXE -> chop(ps, up, dn);
            case PICKAXE, HOE -> {
                if (a == Motion.Action.MINE) {
                    // short, quick strikes into the block
                    ps.translate(0, 0.08f * up - 0.04f * dn, -0.12f * dn);
                    ps.mulPose(Axis.XP.rotationDegrees(-30 * up + 32 * dn));
                    ps.mulPose(Axis.ZP.rotationDegrees(s * 6 * dn));
                } else chop(ps, up, dn);
            }
            case SHOVEL -> {
                // a scoop: pulled back, then thrust forward and tipped up
                ps.translate(-s * 0.05f * dn, -0.06f * up + 0.06f * dn, 0.08f * up - 0.28f * dn);
                ps.mulPose(Axis.XP.rotationDegrees(15 * up - 25 * dn));
            }
            case THROWABLE -> {
                ps.translate(0, 0.12f * up + 0.05f * dn, 0.12f * up - 0.3f * dn);
                ps.mulPose(Axis.XP.rotationDegrees(-40 * up + 30 * dn));
            }
            default -> {
                // a block, food, a torch: a firm bump forward
                ps.translate(-s * 0.08f * dn, 0.06f * up - 0.05f * dn, 0.04f * up - 0.24f * dn);
                ps.mulPose(Axis.XP.rotationDegrees(-15 * up + 22 * dn));
                ps.mulPose(Axis.YP.rotationDegrees(s * 12 * dn));
            }
        }
    }

    /** raised high, then brought down hard */
    static void chop(PoseStack ps, float up, float dn) {
        ps.translate(0, 0.14f * up - 0.05f * dn, -0.02f * up - 0.14f * dn);
        ps.mulPose(Axis.XP.rotationDegrees(-35 * up + 35 * dn));
    }

    /** bringing food or a drink to the mouth, chewing / sipping */
    static void eat(PoseStack ps, AbstractClientPlayer p, float s, ItemStack stack, ItemKind kind, float partial) {
        float f = p.getUseItemRemainingTicks() - partial + 1;
        float f1 = f / stack.getUseDuration();
        float f3 = 1 - (float) Math.pow(f1, 27);
        if (f1 < 0.8f) {
            float bob = kind == ItemKind.DRINK ? Mth.sin(f * 0.5f) * 0.03f : Math.abs(Mth.cos(f / 4f * Mth.PI) * 0.1f);
            ps.translate(0, bob, 0);
        }
        ps.translate(f3 * 0.6f * s, f3 * -0.5f, 0);
        ps.mulPose(Axis.YP.rotationDegrees(s * f3 * 90));
        ps.mulPose(Axis.XP.rotationDegrees(f3 * 10));
        ps.mulPose(Axis.ZP.rotationDegrees(s * f3 * 30));
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
