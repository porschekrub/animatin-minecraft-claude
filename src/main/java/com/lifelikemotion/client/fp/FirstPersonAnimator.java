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
import org.joml.Matrix4f;
import org.joml.Vector3f;
import org.joml.Vector4f;

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
    /**
     * Where a held item sits (the game's is 0.56, -0.52, -0.72) and how big it is drawn: a little higher, nearer the
     * middle and bigger than the game's, so what you hold is there to be seen.
     */
    public static float HX = 0.40f, HY = -0.38f, HZ = -0.72f, SIZE = 1.4f;

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
        // an empty off hand: up in a guard at the side of the screen (both fists up when both hands are empty), or not
        // drawn at all when asked (unless both hands are busy: swimming, climbing, reins... or running, both arms pump)
        float runArm = Mth.clamp((Motion.lerp(Motion.sprintO, Motion.sprint, partial) - 0.2f) / 0.6f, 0, 1)
                * (p.isUsingItem() ? 0 : 1);
        boolean offRun = kind == ItemKind.EMPTY && hand == InteractionHand.OFF_HAND && runArm > 0.01f;
        ItemKind mainKind = ItemKind.of(p.getMainHandItem());
        boolean guard = kind == ItemKind.EMPTY && hand == InteractionHand.OFF_HAND && LMConfig.FP_BOTH_HANDS.get()
                && mainKind != ItemKind.SPECIAL && !(p.isUsingItem() && p.getUsedItemHand() == InteractionHand.MAIN_HAND);
        if (kind == ItemKind.EMPTY && hand == InteractionHand.OFF_HAND && (!Activities.bothArms(partial) && !offRun && !guard || p.isInvisible())) {
            e.setCanceled(true);
            return;
        }
        PoseStack ps = e.getPoseStack();
        Arm.captureRoot(ps);
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
            float px = kind == ItemKind.EMPTY ? 0.64f : HX, py = kind == ItemKind.EMPTY ? -0.6f : HY, pz = kind == ItemKind.EMPTY ? -0.72f : HZ;
            boolean mainHand = hand == InteractionHand.MAIN_HAND;
            if (offRun && !guard && !Activities.bothArms(partial)) ps.translate(0, -0.55f * (1 - runArm * runArm * (3 - 2 * runArm)), 0);
            if (!p.isAutoSpinAttack()) {
                // physics (inertia, floating, flutter, pendulum, slosh), then what you're doing with the world
                float[] ph = ItemPhysics.pose(mainHand, partial);
                Clip.apply(ps, new float[]{ph[0] * s, ph[1], ph[2], ph[3], ph[4] * s, ph[5] * s}, s, 1, px, py, pz);
                Clip.apply(ps, Activities.pose(p, mainHand, s, kind, partial), s, 1, px, py, pz);
            }
            if (!using && !p.isAutoSpinAttack()) {
                // how it's carried (standing / walking / running), and a show-off move when standing still
                Stance.apply(ps, p, kind, s, partial, px, py, pz);
                if (mainHand) Flourish.apply(ps, s, partial, px, py, pz);
            }
            if (kind == ItemKind.SPECIAL || (using && !eating) || p.isAutoSpinAttack()) {
                ((ItemInHandRendererInvoker) mc.getEntityRenderDispatcher().getItemInHandRenderer()).lm$renderArmWithItem(
                        p, partial, e.getInterpolatedPitch(), hand, swingProgress, stack, e.getEquipProgress(), ps, e.getMultiBufferSource(), e.getPackedLight());
            } else {
                // our own swing-in when the item changes; the game's attack-cooldown dip only as a light settle
                float equip = Motion.equip(hand == InteractionHand.MAIN_HAND, partial);
                ps.translate(0, -0.1f * e.getEquipProgress() * (1 - equip), 0);
                if (kind == ItemKind.EMPTY) {
                    if (!p.isInvisible()) emptyArm(ps, e.getMultiBufferSource(), e.getPackedLight(), p, right, equip,
                            hand == InteractionHand.OFF_HAND && mainKind != ItemKind.EMPTY, partial);
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
        float amt = walk * bobK * (1 + sprint * 0.8f) * aim;
        float ly = Motion.lagYaw * aim, lp = Motion.lagPitch * aim;
        // each step: a bouncy dip (sharp at the footfall, round at the top) and a sway from side to side
        float dip = (float) Math.pow(Math.abs(Mth.cos(phase)), 0.7);
        float sway = Mth.sin(phase);
        // slides: trailing the camera, the step, the jump, the landing spring, sneaking, breathing, treading water
        ps.translate(-ly * 0.0018f + sway * 0.022f * amt,
                lp * 0.0016f - dip * 0.034f * amt - air * 0.045f * bobK + Motion.landPos * 1.3f * bobK
                        - 0.03f * sneak + Mth.sin(t * 0.075f) * 0.007f * bobK
                        + Mth.sin(t * 0.1f) * 0.012f * water,
                0.03f * sneak + sprint * 0.02f * walk);
        // turns: about the hand
        float yaw = ly * 0.4f + sway * 1.2f * amt;
        float pitch = lp * 0.35f + dip * 2.6f * amt + air * 6 * bobK - Motion.landPos * 80 * bobK
                + Mth.sin(t * 0.075f + 1) * 0.9f * bobK;
        float roll = ly * 0.3f + sway * 3.4f * amt + s * Mth.sin(t * 0.08f) * 3 * water + Mth.sin(t * 0.05f) * 0.6f * bobK;
        Clip.apply(ps, new float[]{0, 0, 0, pitch, s * yaw, s * roll}, s, 1, HX, HY, HZ);
    }

    // ------------------------------------------------------------------ an empty hand: fists up
    /** where an empty hand's fist rests (x toward its side, y up, z toward you), and the off hand's guard beside a held item */
    public static float[] FIST = {0.30f, -0.32f, -0.70f}, GUARD = {0.56f, -0.42f, -0.68f};

    static void emptyArm(PoseStack ps, MultiBufferSource buf, int light, AbstractClientPlayer p, boolean right, float equip,
                         boolean guard, float partial) {
        float s = right ? 1 : -1;
        float k = (float) (double) LMConfig.FP_SWING.get();
        float[] f = guard ? GUARD : FIST;
        equip(ps, s, equip, f[0], f[1], f[2]);
        ps.translate(s * f[0], f[1], f[2]);
        // breathing: the fists rise and fall a little, each in its own time
        float t = Motion.ticks + partial;
        ps.translate(0, Mth.sin(t * 0.09f + (right ? 0 : 1.7f)) * 0.006f, 0);
        float[] q = swing(p, hand(p, right), ItemKind.EMPTY, partial);
        if (q != null) Clip.apply(ps, q, s, k, 0, 0, 0);
        Matrix4f m = ps.last().pose();
        Vector3f fist = Arm.toRoot(m, 0, 0, 0);
        Arm.draw(ps, buf, light, p, right, fist, outer(m, s));
    }

    /** which way the back of the hand faces: as at rest, turned with the hand */
    static Vector3f outer(Matrix4f m, float s) {
        Vector3f rest = Arm.restOuter(s);
        return Arm.dirToRoot(m, rest.x, rest.y, rest.z);
    }

    /** Switching to an item: it swings up into the hand from below, turning as it comes (instead of a straight drop). */
    static void equip(PoseStack ps, float s, float equip, float px, float py, float pz) {
        if (equip <= 0.001f) return;
        // (equip runs 1 -> 0) springs up from below, overshoots a touch and settles
        float x = 1 - equip;
        float c1 = 1.9f, c3 = c1 + 1;
        float back = 1 + c3 * (float) Math.pow(x - 1, 3) + c1 * (float) Math.pow(x - 1, 2);   // ease out, with overshoot
        float e = 1 - back;
        ps.translate(s * 0.10f * e, -0.62f * e, 0.06f * e);
        Clip.apply(ps, new float[]{0, 0, 0, 34 * e, -14 * e, -24 * e}, s, 1, px, py, pz);
    }

    // ------------------------------------------------------------------ an item in the hand
    static void held(PoseStack ps, MultiBufferSource buf, int light, AbstractClientPlayer p, boolean right, ItemStack stack, ItemKind kind,
                     float sw, float equip, boolean eating, float partial) {
        float s = right ? 1 : -1;
        float k = (float) (double) LMConfig.FP_SWING.get();
        if (kind == ItemKind.PICKAXE && Motion.action != Motion.Action.MINE) k *= 0.8f;
        // the hand's place, then the switch-in
        equip(ps, s, equip, HX, HY, HZ);
        ps.translate(s * HX, HY, HZ);
        Matrix4f base = new Matrix4f(ps.last().pose());
        float[] q = eating ? null : swing(p, hand(p, right), kind, partial);
        if (q != null) Clip.apply(ps, q, s, k, 0, 0, 0);
        Matrix4f afterSwing = new Matrix4f(ps.last().pose());
        if (eating) {
            // (the item's middle, here: eating moves and turns it about that)
            ps.pushPose();
            ps.scale(SIZE, SIZE, SIZE);
            Object[] mp0 = Arm.modelPose(ps, p, stack, right);
            ps.popPose();
            Vector3f mid = Arm.points((net.minecraft.client.resources.model.BakedModel) mp0[0], stack, kind).mid();
            Vector4f c = new Vector4f(mid, 1);
            ((Matrix4f) mp0[1]).transform(c);
            new Matrix4f(ps.last().pose()).invert().transform(c);
            eat(ps, p, s, stack, kind, partial, new Vector3f(c.x, c.y, c.z));
        }
        wrist(ps, p, s, kind, partial);
        ps.scale(SIZE, SIZE, SIZE);
        // the item, and the arm whose fist closes round its grip
        Object[] mp = Arm.modelPose(ps, p, stack, right);
        Arm.Points pts = Arm.points((net.minecraft.client.resources.model.BakedModel) mp[0], stack, kind);
        Matrix4f model = (Matrix4f) mp[1];
        Minecraft.getInstance().getEntityRenderDispatcher().getItemInHandRenderer().renderItem(p, stack,
                right ? ItemDisplayContext.FIRST_PERSON_RIGHT_HAND : ItemDisplayContext.FIRST_PERSON_LEFT_HAND, !right, ps, buf, light);
        if (LMConfig.FP_ARMS_WITH_ITEMS.get() && !p.isInvisible()) {
            if (eating && twoHanded(stack)) {
                // a bowl or a bucket is held in both hands, one at each side (the free hand, if it is free)
                Vector3f a = Arm.toRoot(model, pts.lo().x, pts.lo().y, pts.lo().z), b = Arm.toRoot(model, pts.hi().x, pts.hi().y, pts.hi().z);
                boolean aMine = a.x * s > b.x * s;
                Arm.draw(ps, buf, light, p, right, aMine ? a : b, outer(afterSwing, s));
                ItemStack other = right == (p.getMainArm() == HumanoidArm.RIGHT) ? p.getOffhandItem() : p.getMainHandItem();
                if (other.isEmpty()) Arm.draw(ps, buf, light, p, !right, aMine ? b : a, Arm.restOuter(-s));
            } else {
                Vector3f g = pts.grip();
                Arm.draw(ps, buf, light, p, right, Arm.toRoot(model, g.x, g.y, g.z), outer(afterSwing, s));
            }
        }
        // the blade's trail while it cuts
        if (q != null && lastClip[hand(p, right) ? 0 : 1] != null && SwingFx.trails(kind)) {
            int h = hand(p, right) ? 0 : 1;
            Matrix4f after = new Matrix4f(afterSwing).invert().mul(model);
            SwingFx.trail(ps, buf, lastClip[h], lastU[h], s, k, base, after, pts, stack);
        }
    }

    /**
     * The wrist: what you hold has weight, so it tips behind as you turn and look up and down and wobbles with each
     * step, a lantern or torch most of all.
     */
    static void wrist(PoseStack ps, AbstractClientPlayer p, float s, ItemKind kind, float partial) {
        float sway = (float) (double) LMConfig.FP_SWAY.get();
        float loose = kind == ItemKind.LIGHT ? 1.3f : kind.tool() ? 1f : 0.8f;
        float walk = Motion.lerp(Motion.walkO, Motion.walk, partial) * (float) (double) LMConfig.FP_BOB.get();
        float phase = Mth.lerp(partial, p.walkDistO, p.walkDist) * Mth.PI;
        float roll = (-Motion.lagYaw * 1.5f + Mth.sin(phase) * 5 * walk) * loose * sway;
        float pitch = (-Motion.lagPitch * 1.1f + Math.abs(Mth.cos(phase)) * 5 * walk) * loose * sway;
        ps.mulPose(Axis.ZP.rotationDegrees(roll));
        ps.mulPose(Axis.XP.rotationDegrees(pitch));
    }

    // ------------------------------------------------------------------ swings, on our own clock
    static final long[] seenStart = {Long.MIN_VALUE, Long.MIN_VALUE};
    static final float[][] lastPose = new float[2][6], fromPose = new float[2][6];
    static final float[] fromAt = {-1000, -1000};

    /** the mining loop's length for a clip (ticks) */
    static int loopTicks(Clip c) {
        return c == Clips.CHOP ? 10 : c == Clips.DIG ? 9 : Clips.ticks(c);
    }

    /** the clip each hand is playing and how far in it is (for the trail and the strike) */
    static final Clip[] lastClip = new Clip[2];
    static final float[] lastU = new float[2];

    /**
     * This hand's swing pose now, or null when it isn't swinging. A swing plays its clip over its own time (longer
     * than the game's quick swing) and stops dead for a moment when it hits something; mining loops the clip for as long
     * as a block is being broken, finishing the stroke when you stop; a new swing in the middle of one blends out of
     * where the hand is. With both hands empty the fists punch in turn.
     */
    static float[] swing(AbstractClientPlayer p, boolean main, ItemKind kind, float partial) {
        int h = main ? 0 : 1;
        float s = main == (p.getMainArm() == HumanoidArm.RIGHT) ? 1 : -1;
        float now = Motion.ticks + partial;
        if (testSwing != null) {
            if (!main) return null;
            Clip c = testClip != null ? testClip : clipFor(kind);
            lastClip[h] = c;
            lastU[h] = testSwing;
            return c.sample(testSwing);
        }
        float[] q = null;
        Clip playing = null;
        float u = 0;
        if (main && (Motion.mining || Motion.mineStop >= Motion.mineStart)) {
            Clip c = testClip != null ? testClip : clipFor(kind);
            int n = loopTicks(c);
            float a = now - Motion.mineStart;
            long end = Motion.mining ? Long.MAX_VALUE
                    : Motion.mineStart + (long) Math.ceil((Motion.mineStop - Motion.mineStart) / (double) n) * n;
            if (now < end) {
                u = (a % n) / n;
                q = c.sample(u);
                playing = c;
            }
        }
        // whose turn: the hand that swung (with both hands empty, the fists take turns)
        boolean mine = main != Motion.swingOffHand;
        boolean fists = p.getMainHandItem().isEmpty() && p.getOffhandItem().isEmpty() && LMConfig.FP_BOTH_HANDS.get();
        if (fists && Math.floorMod(Motion.swingCount, 2) == 1 && Motion.action == Motion.Action.ATTACK) mine = !mine;
        if (q == null && mine) {
            Clip c = testClip != null ? testClip : clipFor(kind);
            float age = SwingFx.clock(now, Motion.swingStart) - Motion.swingStart;
            int n = Math.max(1, Math.round(Clips.ticks(c) / Math.max(1f, (float) (double) LMConfig.FP_SPEED.get())));
            if (age >= 0 && age < n) {
                if (seenStart[h] != Motion.swingStart) {
                    // a new swing: blend out of wherever the last one left the hand
                    seenStart[h] = Motion.swingStart;
                    System.arraycopy(lastPose[h], 0, fromPose[h], 0, 6);
                    fromAt[h] = Motion.swingStart;
                    lastU[h] = 0;
                    lastClip[h] = null;
                }
                u = age / n;
                q = c.sample(u);
                playing = c;
                float b = Mth.clamp((now - fromAt[h]) / 2.5f, 0, 1);
                b = b * b * (3 - 2 * b);
                for (int i = 0; i < 6; i++) q[i] = Mth.lerp(b, fromPose[h][i], q[i]);
            }
        }
        if (q == null) {
            java.util.Arrays.fill(lastPose[h], 0);
            lastClip[h] = null;
            return null;
        }
        // the strike lands: kick the camera (and, if it hit something, freeze and shake)
        float at = SwingFx.impact(playing);
        if (lastClip[h] == playing && at >= 0) {
            float prev = lastU[h];
            boolean crossed = prev < at && u >= at || prev > u && u >= at;   // (a mining loop wraps round)
            if (crossed) SwingFx.landed(playing, s);
        }
        lastClip[h] = playing;
        lastU[h] = u;
        System.arraycopy(q, 0, lastPose[h], 0, 6);
        return q;
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
        if (kind == ItemKind.EMPTY) return Clips.PUNCH;
        return switch (kind) {
            case SWORD -> a == Motion.Action.MINE ? Clips.MINE : switch (Math.floorMod(Motion.swingCount - 1, 3)) {
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

    /** a bowl of soup or a bucket of milk: held up in both hands */
    static boolean twoHanded(ItemStack st) {
        return soup(st) || st.getItem() instanceof net.minecraft.world.item.MilkBucketItem;
    }

    /**
     * Eating and drinking, done properly: food is brought round to the middle, up to your mouth, and bitten into, a
     * bite every four ticks as the game crunches (pushed in, the hand jolting, crumbs flying), with a last big bite;
     * a bowl of soup comes up in both hands and is tipped toward you so you see into it, and gulped from; a bottle is
     * tipped right up and drunk; a bucket of milk is lifted in both hands and tipped up. Afterwards it all drops back
     * into the hand with a little bounce.
     */
    static void eat(PoseStack ps, AbstractClientPlayer p, float s, ItemStack stack, ItemKind kind, float partial, Vector3f mid) {
        float used = p.getTicksUsingItem() + partial;
        float total = stack.getUseDuration();
        float left = p.getUseItemRemainingTicks() - partial;
        boolean bowl = soup(stack);
        boolean bucket = stack.getItem() instanceof net.minecraft.world.item.MilkBucketItem;
        boolean drink = kind == ItemKind.DRINK && !bowl && !bucket;
        // up to the mouth: quick, with a little overshoot
        float x = Mth.clamp(used / 5f, 0, 1);
        float m = 1 + 2.2f * (float) Math.pow(x - 1, 3) + 1.2f * (float) Math.pow(x - 1, 2);
        // where its middle goes (camera space: x right, y up, z toward you): just below the middle of the screen
        Vector3f mouth = bowl ? new Vector3f(0, -0.20f, -0.50f) : bucket ? new Vector3f(0, -0.13f, -0.68f)
                : drink ? new Vector3f(s * 0.03f, -0.11f, -0.56f) : new Vector3f(s * 0.02f, -0.15f, -0.54f);
        Vector4f t = new Vector4f(mouth, 1);
        Arm.ROOT.transform(t);
        new Matrix4f(ps.last().pose()).invert().transform(t);
        ps.translate((t.x - mid.x) * m, (t.y - mid.y) * m, (t.z - mid.z) * m);
        float beat = (used % 4f) / 4f;                                   // the game's crunch / gulp every four ticks
        float hit = beat < 0.3f ? beat / 0.3f : Math.max(0, 1 - (beat - 0.3f) / 0.7f);
        hit = hit * hit * (3 - 2 * hit) * m * Mth.clamp((used - 5) / 2f, 0, 1);
        // everything below turns about the item's middle
        ps.translate(mid.x, mid.y, mid.z);
        if (bowl || bucket) {
            // tipped toward you (you see into it), tipped further with each gulp
            ps.mulPose(Axis.YP.rotationDegrees(-s * 10 * m));
            ps.mulPose(Axis.XP.rotationDegrees((bucket ? 50 : 38) * m + hit * 8));
            ps.translate(0, hit * 0.012f, hit * 0.015f);
        } else if (drink) {
            // the bottle tipped right up to the lips, the bottom raised; a gulp lifts it a little more
            ps.mulPose(Axis.YP.rotationDegrees(-s * 18 * m));
            ps.mulPose(Axis.XP.rotationDegrees(62 * m + hit * 8));
            ps.mulPose(Axis.ZP.rotationDegrees(s * 12 * m));
            ps.translate(0, hit * 0.01f, 0);
        } else {
            // food: turned to face you; each bite pushes it in and up, a jolt and a little shake
            ps.mulPose(Axis.YP.rotationDegrees(-s * 28 * m));
            ps.mulPose(Axis.XP.rotationDegrees(-16 * m + hit * 14));
            ps.translate(0, hit * 0.025f, hit * 0.07f);
            ps.mulPose(Axis.ZP.rotationDegrees(Mth.sin(used * 2.3f) * 5 * hit + s * Mth.sin(used * 0.7f) * 3 * m));
            // the last big bite: pushed right in
            float last = Mth.clamp(1 - left / 4f, 0, 1);
            if (last > 0) ps.translate(0, 0.02f * last, 0.1f * last * last);
            // eaten away a little with every bite
            float size = 1 - 0.22f * Mth.clamp(used / total, 0, 1);
            ps.scale(size, size, size);
        }
        ps.translate(-mid.x, -mid.y, -mid.z);
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
        float bx = s * HX, by = HY, bz = HZ;
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
