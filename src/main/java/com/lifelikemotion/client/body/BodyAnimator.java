package com.lifelikemotion.client.body;

import com.lifelikemotion.client.ItemKind;
import com.lifelikemotion.config.LMConfig;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.UseAnim;

import java.util.Map;
import java.util.WeakHashMap;

/**
 * Lively third-person bodies, laid on top of the game's own poses (so armour, capes and held items follow):
 * breathing, a torso that twists and bounces with each step, leaning into a sprint, knees up when jumping and arms
 * flailing when falling, a squash on landing, paddling and kicking in water, a flutter kick when swimming, hand over
 * hand up ladders, flinching when hurt, food to the mouth, and big readable swings (alternating sword slashes,
 * overhead axe chops, punches).
 */
public final class BodyAnimator {
    private BodyAnimator() {}

    static final class State {
        float lastAge = -1, air, land, tread, climb, sprint, swim;
        boolean wasGround = true, wasSwinging;
        double lastVy;
        int swings;
    }

    static final Map<LivingEntity, State> STATES = new WeakHashMap<>();
    /** client test: holds the local player's swing at this point so a screenshot catches it */
    public static Float testAttack;

    /** Puts back the offsets this class moves (the game does not reset all of them itself). */
    public static void reset(HumanoidModel<?> m, LivingEntity e, float age) {
        if (e instanceof net.minecraft.world.entity.Mob) {
            m.head.zRot = 0;
            m.body.zRot = 0;
            return;
        }
        if (!(e instanceof Player)) return;
        // every part back to where the model was built with it: nothing this class moved can pile up frame to frame
        for (ModelPart part : new ModelPart[]{m.head, m.body, m.rightArm, m.leftArm, m.rightLeg, m.leftLeg}) {
            net.minecraft.client.model.geom.PartPose i = part.getInitialPose();
            part.x = i.x;
            part.y = i.y;
            part.z = i.z;
            part.zRot = i.zRot;
        }
    }

    public static void apply(HumanoidModel<?> m, LivingEntity e, float limbSwing, float limbAmount, float age, float headYaw, float headPitch) {
        if (e instanceof net.minecraft.world.entity.Mob) {
            MobAnimator.humanoid(m, e, limbSwing, limbAmount, age);
            return;
        }
        // age 0: the first-person arm (or a statue) - left alone
        if (age == 0 || !(e instanceof Player p)) return;
        var emote = com.lifelikemotion.client.emote.Emotes.of(p);
        if (emote != null && !p.isPassenger() && !p.isSleeping()) {
            try {
                if (LMConfig.BODY_ENABLED.get()) animate(m, p, limbSwing, limbAmount, age);
                com.lifelikemotion.client.emote.EmotePoses.body(m, p, emote, age - p.tickCount);
            } catch (Throwable t) {
                // never break player rendering
            }
            m.hat.copyFrom(m.head);
            return;
        }
        if (!LMConfig.BODY_ENABLED.get()) return;
        if (p != Minecraft.getInstance().player && !LMConfig.BODY_OTHER_PLAYERS.get()) return;
        if (p.isSleeping() || p.isFallFlying() || p.isSpectator() || p.isAutoSpinAttack()) return;
        try {
            animate(m, p, limbSwing, limbAmount, age);
        } catch (Throwable t) {
            // never break player rendering
        }
        m.hat.copyFrom(m.head);
    }

    static void animate(HumanoidModel<?> m, Player p, float swing, float amount, float age) {
        float I = (float) (double) LMConfig.BODY_INTENSITY.get();
        State st = STATES.computeIfAbsent(p, k -> new State());
        float dt = st.lastAge < 0 ? 1 : age - st.lastAge;
        if (dt < 0 || dt > 10) dt = 1;
        st.lastAge = age;
        float f = 1 - (float) Math.pow(0.7, dt); // ~0.3 per tick, frame-rate independent

        boolean water = p.isInWater();
        boolean swimming = m.swimAmount > 0 || p.isVisuallySwimming();
        boolean riding = p.isPassenger();
        boolean climbing = p.onClimbable() && !p.onGround() && !riding;
        double y = p.getY();
        double vy = y - p.yo; // per tick
        boolean ground = p.onGround() || riding || climbing || p.getAbilities().flying;
        float speed = Mth.clamp(amount, 0, 1);

        st.air += ((ground || water ? 0 : Mth.clamp((float) vy * 2.5f, -1, 1)) - st.air) * f;
        if (ground && !st.wasGround && !water && st.lastVy < -0.25) st.land = Math.max(st.land, Mth.clamp((float) -st.lastVy * 1.2f, 0.2f, 1));
        else st.land *= (float) Math.pow(0.72, dt);
        if (dt > 0.0001) {
            st.wasGround = ground;
            st.lastVy = vy;
        }
        st.tread += ((water && !swimming && !p.onGround() && !riding ? 1 : 0) - st.tread) * f;
        st.climb += ((climbing ? 1 : 0) - st.climb) * f;
        st.sprint += ((p.isSprinting() && !water ? 1 : 0) - st.sprint) * f;
        st.swim += ((swimming ? 1 : 0) - st.swim) * f;
        if (testAttack != null && p == Minecraft.getInstance().player) m.attackTime = testAttack;
        boolean swingingNow = m.attackTime > 0;
        if (swingingNow && !st.wasSwinging) st.swings++;
        st.wasSwinging = swingingNow;

        // ---- breathing
        float br = Mth.sin(age * 0.09f) * 0.035f * I;
        m.rightArm.zRot += br;
        m.leftArm.zRot -= br;
        m.head.xRot += Mth.sin(age * 0.09f + 1) * 0.015f * I;

        // ---- walking / running on the ground
        if (p.onGround() && !riding && !swimming) {
            float cyc = swing * 0.6662f;
            float twist = Mth.cos(cyc) * 0.11f * speed * I * (1 + st.sprint * 0.6f);
            m.body.yRot += twist;
            m.head.yRot -= twist * 0.5f;
            float bounce = (1 - Math.abs(Mth.cos(cyc))) * 0.55f * speed * I * (1 + st.sprint * 0.5f);
            lift(m, -bounce, true);
            m.rightArm.zRot += 0.06f * speed * I;
            m.leftArm.zRot -= 0.06f * speed * I;
            if (st.sprint > 0.01f && !m.crouching) {
                float lean = 0.3f * st.sprint * speed * I;
                m.body.xRot += lean;
                m.rightLeg.z += 12 * Mth.sin(lean);
                m.leftLeg.z += 12 * Mth.sin(lean);
                m.rightLeg.y -= 12 * (1 - Mth.cos(lean));
                m.leftLeg.y -= 12 * (1 - Mth.cos(lean));
                m.head.z -= 1.2f * st.sprint * speed;
                // arms pump harder, a little bent in
                float pump = 0.45f * st.sprint * speed * I;
                m.rightArm.xRot += Mth.cos(cyc + Mth.PI) * pump;
                m.leftArm.xRot += Mth.cos(cyc) * pump;
                m.rightArm.zRot += 0.1f * st.sprint;
                m.leftArm.zRot -= 0.1f * st.sprint;
            }
        }

        // ---- in the air: knees up going up, flailing coming down
        float a = st.air * I;
        if (a > 0) {
            m.rightLeg.xRot -= 0.6f * a;
            m.leftLeg.xRot += 0.25f * a;
            m.rightArm.xRot -= 0.35f * a;
            m.leftArm.xRot -= 0.2f * a;
            m.rightArm.zRot += 0.25f * a;
            m.leftArm.zRot -= 0.25f * a;
        } else if (a < 0) {
            float fl = -a;
            m.rightArm.zRot += 0.85f * fl;
            m.leftArm.zRot -= 0.85f * fl;
            m.rightArm.xRot += Mth.sin(age * 0.7f) * 0.35f * fl;
            m.leftArm.xRot += Mth.sin(age * 0.7f + 2) * 0.35f * fl;
            m.rightLeg.zRot += 0.18f * fl;
            m.leftLeg.zRot -= 0.18f * fl;
            m.rightLeg.xRot += Mth.sin(age * 0.5f) * 0.3f * fl;
            m.leftLeg.xRot -= Mth.sin(age * 0.5f) * 0.3f * fl;
        }

        // ---- landing: a squash
        float L = st.land * I;
        if (L > 0.01f) {
            lift(m, 1.8f * L, false);
            m.rightArm.xRot -= 0.35f * L;
            m.leftArm.xRot -= 0.35f * L;
            m.rightArm.zRot += 0.2f * L;
            m.leftArm.zRot -= 0.2f * L;
            m.rightLeg.zRot += 0.12f * L;
            m.leftLeg.zRot -= 0.12f * L;
            m.body.xRot += 0.15f * L;
        }

        // ---- treading water: paddling arms, kicking legs
        float tw = st.tread;
        if (tw > 0.01f) {
            float c = age * 0.24f;
            blend(m.rightArm, Mth.sin(c) * 0.35f, 0, 0.75f + Mth.sin(c) * 0.25f, tw);
            blend(m.leftArm, Mth.sin(c + Mth.PI) * 0.35f, 0, -0.75f - Mth.sin(c + Mth.PI) * 0.25f, tw);
            blend(m.rightLeg, Mth.sin(age * 0.33f) * 0.45f, 0, 0.08f, tw);
            blend(m.leftLeg, -Mth.sin(age * 0.33f) * 0.45f, 0, -0.08f, tw);
        }
        // ---- swimming: a flutter kick
        if (st.swim > 0.01f) {
            float k = Mth.sin(age * 0.6f) * 0.32f * st.swim * I;
            m.rightLeg.xRot += k;
            m.leftLeg.xRot -= k;
        }

        // ---- ladders: hand over hand
        float cl = st.climb;
        if (cl > 0.01f) {
            float cad = (float) (y * 3.2);
            blend(m.rightArm, -2.6f + Mth.sin(cad) * 0.45f, 0, 0.12f, cl);
            blend(m.leftArm, -2.6f + Mth.sin(cad + Mth.PI) * 0.45f, 0, -0.12f, cl);
            blend(m.rightLeg, -0.3f + Mth.sin(cad + Mth.PI) * 0.45f, 0, 0, cl);
            blend(m.leftLeg, -0.3f + Mth.sin(cad) * 0.45f, 0, 0, cl);
            m.body.xRot += 0.06f * cl;
        }

        // ---- hurt: flinch back, arms up
        if (p.hurtTime > 0 && p.hurtDuration > 0) {
            float h = p.hurtTime / (float) p.hurtDuration * I;
            m.head.xRot -= 0.25f * h;
            m.body.xRot -= 0.1f * h;
            m.rightArm.xRot -= 0.35f * h;
            m.leftArm.xRot -= 0.35f * h;
            m.rightArm.zRot += 0.3f * h;
            m.leftArm.zRot -= 0.3f * h;
        }

        // ---- eating and drinking: to the mouth
        if (p.isUsingItem()) {
            UseAnim ua = p.getUseItem().getUseAnimation();
            if (ua == UseAnim.EAT || ua == UseAnim.DRINK) {
                boolean rightHand = (p.getUsedItemHand() == net.minecraft.world.InteractionHand.MAIN_HAND) == (p.getMainArm() == HumanoidArm.RIGHT);
                ModelPart arm = rightHand ? m.rightArm : m.leftArm;
                float s = rightHand ? 1 : -1;
                if (ua == UseAnim.EAT) {
                    arm.xRot = -1.45f + Mth.sin(age * 1.6f) * 0.09f + m.head.xRot * 0.5f;
                    arm.yRot = -0.55f * s;
                } else {
                    arm.xRot = -1.95f + m.head.xRot * 0.5f;
                    arm.yRot = -0.5f * s;
                    m.head.xRot -= 0.35f;
                }
                arm.zRot = 0;
            }
        }

        // ---- swings
        if (swingingNow && !p.isUsingItem()) swing(m, p, m.attackTime, I, (st.swings & 1) == 0);
    }

    /** One swing, by what is in the hand (third person): the arm, and the body twisting into it. */
    static void swing(HumanoidModel<?> m, Player p, float t, float I, boolean backhand) {
        HumanoidArm side = p.swingingArm == net.minecraft.world.InteractionHand.MAIN_HAND ? p.getMainArm() : p.getMainArm().getOpposite();
        boolean right = side == HumanoidArm.RIGHT;
        ModelPart arm = right ? m.rightArm : m.leftArm;
        float s = right ? 1 : -1;
        ItemKind kind = ItemKind.of(p.getItemInHand(p.swingingArm));
        float wind = 0.2f;
        float theta = t < wind ? -ease(t / wind) : t < 0.5f ? -1 + 2 * easeOut((t - wind) / (0.5f - wind)) : 1 - ease((t - 0.5f) / 0.5f);
        float up = Math.max(-theta, 0) * I, dn = Math.max(theta, 0) * I;
        float twist;
        switch (kind) {
            case SWORD -> {
                if (!backhand) {
                    // high on the sword side, cut down and across
                    arm.xRot = -2.5f * up - 0.6f * dn - 0.3f * (1 - up - dn);
                    arm.yRot = s * (0.45f * up - 0.75f * dn);
                    arm.zRot = s * (0.4f * up - 0.1f * dn);
                    twist = s * (0.35f * up - 0.5f * dn);
                } else {
                    // back the other way, low to high
                    arm.xRot = -0.9f * up - 1.9f * dn - 0.3f * (1 - up - dn);
                    arm.yRot = s * (-0.8f * up + 0.55f * dn);
                    arm.zRot = s * (-0.05f * up + 0.5f * dn);
                    twist = s * (-0.45f * up + 0.4f * dn);
                }
            }
            case AXE, PICKAXE, HOE, SHOVEL -> {
                // overhead, then down hard (bending into it)
                arm.xRot = -3.0f * up - 0.5f * dn - 0.4f * (1 - up - dn);
                arm.yRot = s * -0.15f * dn;
                arm.zRot = 0;
                m.body.xRot += 0.18f * dn;
                twist = s * -0.15f * dn;
            }
            case EMPTY -> {
                // a jab: the shoulder turns into it
                float jab = t < 0.3f ? Mth.sin(t / 0.3f * Mth.HALF_PI) : 1 - ease((t - 0.3f) / 0.7f);
                arm.xRot = -1.55f * jab * I + arm.xRot * (1 - jab);
                arm.yRot = s * -0.25f * jab;
                arm.zRot = 0;
                twist = s * -0.45f * jab * I;
            }
            case BLOCK, FOOD, DRINK, LIGHT, OTHER -> {
                // reaching out to put something down
                float b = Mth.sin(t * Mth.PI) * I;
                arm.xRot = arm.xRot * (1 - b) - 1.35f * b;
                arm.yRot = s * -0.2f * b;
                arm.zRot = 0;
                m.body.xRot += 0.12f * b;
                twist = s * -0.2f * b;
            }
            default -> {
                return; // the game's own swing
            }
        }
        m.body.yRot = twist;
        // shoulders turn with the torso
        m.rightArm.z = Mth.sin(twist) * 5;
        m.rightArm.x = -Mth.cos(twist) * 5;
        m.leftArm.z = -Mth.sin(twist) * 5;
        m.leftArm.x = Mth.cos(twist) * 5;
        (right ? m.leftArm : m.rightArm).yRot += twist;
    }

    /** Moves the whole body up (negative) or down (positive), legs too when asked. */
    static void lift(HumanoidModel<?> m, float dy, boolean legs) {
        m.head.y += dy;
        m.body.y += dy;
        m.rightArm.y += dy;
        m.leftArm.y += dy;
        if (legs) {
            m.rightLeg.y += dy;
            m.leftLeg.y += dy;
        }
    }

    static void blend(ModelPart part, float x, float y, float z, float k) {
        part.xRot += (x - part.xRot) * k;
        part.yRot += (y - part.yRot) * k;
        part.zRot += (z - part.zRot) * k;
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
