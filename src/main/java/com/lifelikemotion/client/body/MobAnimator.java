package com.lifelikemotion.client.body;

import com.lifelikemotion.config.LMConfig;
import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.monster.AbstractSkeleton;
import net.minecraft.world.entity.monster.Zombie;

import java.util.Map;
import java.util.WeakHashMap;

/**
 * Livelier mobs, on top of the game's own animations: farm animals breathe, bob and sway as they walk and glance about;
 * chickens pump their heads; tamed wolves wag; creepers sway; spiders' legs twitch; villagers nod; zombies shamble with
 * lolling heads and skeletons rattle. Every mob gets its own rhythm (from its id) so a herd doesn't move in lockstep.
 */
public final class MobAnimator {
    private MobAnimator() {}

    public static boolean on() {
        return LMConfig.MOBS_ENABLED.get();
    }

    static float k() {
        return (float) (double) LMConfig.MOBS_INTENSITY.get();
    }

    /**
     * What these animations added to positions and rolls that the game itself never resets: {y after, dy, z after, dz,
     * zRot after, dzRot}. Taken back out before the next frame, unless the game has set the value again meanwhile
     * (a sheep lowering its head to graze, a wolf sitting down).
     */
    static final Map<ModelPart, float[]> OFF = new WeakHashMap<>();

    /** Takes back last frame's offsets (call before the game's own animation code). */
    public static void rest(ModelPart... parts) {
        for (ModelPart p : parts) {
            p.xScale = p.yScale = p.zScale = 1;
            float[] o = OFF.remove(p);
            if (o == null) continue;
            if (p.y == o[0]) p.y -= o[1];
            if (p.z == o[2]) p.z -= o[3];
            if (p.zRot == o[4]) p.zRot -= o[5];
        }
    }

    /** Moves a part (y, z) and rolls it, remembering it so {@link #rest} can take it back. */
    static void move(ModelPart p, float dy, float dz, float dzRot) {
        float[] o = OFF.computeIfAbsent(p, k -> new float[6]);
        p.y += dy;
        p.z += dz;
        p.zRot += dzRot;
        o[0] = p.y;
        o[1] += dy;
        o[2] = p.z;
        o[3] += dz;
        o[4] = p.zRot;
        o[5] += dzRot;
    }

    static float phase(Entity e) {
        return (e.getId() * 7919 % 1000) * 0.1f;
    }

    // ------------------------------------------------------------------ pigs, cows, sheep, bears, pandas...
    public static void quadruped(Entity e, float swing, float amount, float age, ModelPart head, ModelPart body, ModelPart... legs) {
        if (!on() || age == 0) return;
        float K = k(), ph = phase(e), a = Mth.clamp(amount, 0, 1);
        float cyc = swing * 0.6662f;
        // breathing
        float br = 1 + Mth.sin(age * 0.1f + ph) * 0.012f * K;
        body.xScale = br;
        body.zScale = br;
        // walking: a bob with each step, the body rolls, the head nods
        float bob = Math.abs(Mth.sin(cyc)) * 0.7f * a * K;
        float idle = 1 - a;
        // standing: an occasional glance and a slow head tilt
        move(head, -bob, 0, Mth.sin(age * 0.045f + ph) * 0.09f * idle * K);
        move(body, -bob, 0, Mth.sin(cyc) * 0.05f * a * K);
        for (ModelPart l : legs) move(l, -bob * 0.5f, 0, 0);
        head.xRot += Mth.sin(cyc * 2) * 0.07f * a * K;
        head.yRot += glance(age, ph) * 0.35f * idle * K;
    }

    /** A head that turns to look at something now and then and holds it (a smooth step, not a constant sway). */
    static float glance(float age, float ph) {
        float t = (age + ph * 37) / 90f;
        float n = (float) Math.floor(t), f = t - n;
        float a = hash(n), b = hash(n + 1);
        float s = f < 0.85f ? 0 : (f - 0.85f) / 0.15f;
        s = s * s * (3 - 2 * s);
        return a + (b - a) * s;
    }

    static float hash(float n) {
        float x = Mth.sin(n * 12.9898f) * 43758.547f;
        return (x - (float) Math.floor(x)) * 2 - 1;
    }

    // ------------------------------------------------------------------ chickens
    public static void chicken(Entity e, float swing, float amount, float age, ModelPart head, ModelPart beak, ModelPart wattle, ModelPart body,
                               ModelPart rightWing, ModelPart leftWing) {
        if (!on() || age == 0) return;
        float K = k(), ph = phase(e), a = Mth.clamp(amount, 0, 1);
        // the head pumps forward and back with each step
        float pump = Mth.sin(swing * 0.6662f * 2) * 1.1f * a * K;
        // standing: quick, jerky looks around
        float look = Math.round(glance(age * 2.2f, ph) * 3) / 3f * 0.6f * (1 - a) * K;
        for (ModelPart p : new ModelPart[]{head, beak, wattle}) {
            move(p, 0, -pump, 0);
            p.yRot += look;
        }
        move(body, 0, 0, Mth.sin(swing * 0.6662f) * 0.08f * a * K);
        // wings tucked, twitching now and then
        float tw = Mth.sin(age * 0.9f + ph) > 0.97f ? 0.25f * K : 0;
        rightWing.zRot += tw;
        leftWing.zRot -= tw;
    }

    // ------------------------------------------------------------------ wolves
    public static void wolf(Entity e, float swing, float amount, float age, ModelPart head, ModelPart tail, ModelPart body) {
        if (!on() || age == 0) return;
        float K = k(), ph = phase(e), a = Mth.clamp(amount, 0, 1);
        if (e instanceof TamableAnimal t && t.isTame() && !t.isInSittingPose()) tail.yRot += Mth.sin(age * 0.75f) * 0.45f * K;
        float bob = Math.abs(Mth.sin(swing * 0.6662f)) * 0.5f * a * K;
        move(head, -bob, 0, Mth.sin(age * 0.05f + ph) * 0.07f * (1 - a) * K);
        body.y -= bob; // (the wolf sets its body's place every frame)
    }

    // ------------------------------------------------------------------ creepers, spiders, villagers
    public static void creeper(Entity e, float swing, float amount, float age, ModelPart root, ModelPart head) {
        if (!on() || age == 0) return;
        float K = k(), ph = phase(e);
        move(root, 0, 0, Mth.sin(age * 0.06f + ph) * 0.025f * K);
        move(head, 0, 0, Mth.sin(age * 0.06f + ph + 1.3f) * 0.06f * K);
        head.yRot += glance(age, ph) * 0.3f * (1 - Mth.clamp(amount, 0, 1)) * K;
    }

    public static void spider(Entity e, float age, ModelPart... legs) {
        if (!on() || age == 0) return;
        float K = k(), ph = phase(e);
        for (int i = 0; i < legs.length; i++) {
            float twitch = Mth.sin(age * 0.5f + ph + i * 1.7f);
            legs[i].zRot += (twitch > 0.9f ? (twitch - 0.9f) * 1.2f : 0) * (i % 2 == 0 ? 1 : -1) * K;
        }
    }

    public static void villager(Entity e, float swing, float amount, float age, ModelPart head) {
        if (!on() || age == 0) return;
        float K = k(), ph = phase(e), a = Mth.clamp(amount, 0, 1);
        head.zRot += Mth.sin(age * 0.05f + ph) * 0.08f * (1 - a) * K;
        head.xRot += Mth.sin(swing * 0.6662f * 2) * 0.08f * a * K;
        head.yRot += glance(age, ph) * 0.4f * (1 - a) * K;
    }

    // ------------------------------------------------------------------ zombies and skeletons (humanoid mobs)
    public static void humanoid(HumanoidModel<?> m, LivingEntity e, float swing, float amount, float age) {
        if (!on() || age == 0) return;
        float K = k(), ph = phase(e), a = Mth.clamp(amount, 0, 1);
        float cyc = swing * 0.6662f;
        if (e instanceof Zombie) {
            // a shamble: the head lolls, the body lurches side to side
            m.head.zRot += (Mth.sin(age * 0.06f + ph) * 0.14f + Mth.sin(cyc) * 0.1f * a) * K;
            m.head.xRot += Mth.sin(age * 0.04f + ph) * 0.06f * K;
            m.body.yRot += Mth.cos(cyc) * 0.12f * a * K;
            m.body.zRot += Mth.sin(cyc) * 0.05f * a * K;
        } else if (e instanceof AbstractSkeleton) {
            // a rattle now and then
            float r = Mth.sin(age * 0.37f + ph) > 0.93f ? Mth.sin(age * 3.1f) * 0.08f * K : 0;
            m.head.zRot += r;
            m.head.xRot += r * 0.5f;
            m.body.yRot += Mth.cos(cyc) * 0.08f * a * K;
        } else {
            m.head.zRot += Mth.sin(age * 0.05f + ph) * 0.05f * K;
            m.body.yRot += Mth.cos(cyc) * 0.08f * a * K;
        }
        m.hat.copyFrom(m.head);
    }
}
