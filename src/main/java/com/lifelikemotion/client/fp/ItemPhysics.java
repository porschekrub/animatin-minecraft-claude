package com.lifelikemotion.client.fp;

import com.lifelikemotion.client.ItemKind;
import com.lifelikemotion.config.LMConfig;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.*;
import net.minecraft.world.level.block.*;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;

/**
 * A little physics for what's in your hands, stepped 20 times a second (in small sub-steps) and drawn between steps:
 * - inertia: speed up and it lags back, stop and it swings on; knockback and explosions fling it and it settles
 * - free fall: it floats up off the palm as you drop, and lands back in it with a thump (harder for heavy things)
 * - cloth (beds, banners, wool, carpets): flutters with speed, streams back when running, billows up when falling
 * - hanging things (lanterns, chains): swing like a pendulum and keep swinging after you stop
 * - liquids (full buckets, bottles): slosh, tipping further and settling slowly
 * - under water everything moves slow and heavy
 * Each hand has its own state; the result is a pose {x, y, z, pitch, yaw, roll} as in {@link Clip}, but with x, yaw and
 * roll in the world's sense (right is right for both hands): multiply them by the hand's side before applying.
 */
public final class ItemPhysics {
    private ItemPhysics() {}

    public enum Material { NORMAL, HEAVY, LIGHT, CLOTH, HANGING, LIQUID }

    public static Material of(ItemStack s) {
        Item i = s.getItem();
        if (s.isEmpty()) return Material.LIGHT;
        if (i instanceof BedItem || i instanceof BannerItem) return Material.CLOTH;
        if (i instanceof BlockItem bi) {
            Block b = bi.getBlock();
            if (b instanceof WoolCarpetBlock || b instanceof CarpetBlock || b.defaultBlockState().getSoundType() == SoundType.WOOL) return Material.CLOTH;
            if (b instanceof LanternBlock || b instanceof ChainBlock) return Material.HANGING;
            if (b instanceof AnvilBlock || b.defaultBlockState().getSoundType() == SoundType.METAL || b.defaultBlockState().getSoundType() == SoundType.STONE
                    || b.defaultBlockState().getSoundType() == SoundType.DEEPSLATE || b instanceof ChestBlock || b instanceof BarrelBlock
                    || b.defaultBlockState().getSoundType() == SoundType.WOOD && b.defaultBlockState().isCollisionShapeFullBlock(net.minecraft.world.level.EmptyBlockGetter.INSTANCE, net.minecraft.core.BlockPos.ZERO))
                return Material.HEAVY;
            return Material.NORMAL;
        }
        if (i instanceof BucketItem b && b.getFluid() != net.minecraft.world.level.material.Fluids.EMPTY || i instanceof MilkBucketItem
                || i instanceof PotionItem || i instanceof HoneyBottleItem || i instanceof ExperienceBottleItem)
            return Material.LIQUID;
        if (i instanceof AxeItem || i instanceof PickaxeItem) return Material.HEAVY;
        if (i instanceof LeadItem || i.getDefaultInstance().is(Items.STRING) || i.getDefaultInstance().is(Items.PAPER)
                || i.getDefaultInstance().is(Items.FEATHER) || i instanceof MapItem || i instanceof EmptyMapItem)
            return Material.CLOTH;
        if (s.isEdible() || i instanceof SnowballItem || i instanceof EggItem) return Material.LIGHT;
        return Material.NORMAL;
    }

    static final class State {
        // position spring (blocks) and rotation spring (degrees); "o" = last step, for drawing between steps
        float x, y, z, vx, vy, vz, pitch, roll, vp, vr;
        float ox, oy, oz, op, or;
        float flutter, flutterO, lift, liftO;
        Material mat = Material.NORMAL;
    }

    static final State MAIN = new State(), OFF = new State();
    static Vec3 lastVel = Vec3.ZERO;
    static boolean wasGround = true, wasHurt;
    static float lastVy;
    static long phaseTicks;

    public static void onClientTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (p == null || mc.isPaused()) return;
        phaseTicks++;
        MAIN.mat = of(p.getMainHandItem());
        OFF.mat = of(p.getOffhandItem());
        // how you moved this tick, in your own frame: right, up, forward (toward where you look)
        Vec3 v = p.getDeltaMovement();
        Vec3 acc = v.subtract(lastVel);
        lastVel = v;
        double yaw = Math.toRadians(p.getYRot());
        double fx = -Math.sin(yaw), fz = Math.cos(yaw);
        float aFwd = (float) (acc.x * fx + acc.z * fz), aRight = (float) (acc.x * -fz + acc.z * fx), aUp = (float) acc.y;
        float speed = (float) v.length();
        boolean ground = p.onGround() || p.isPassenger() || p.getAbilities().flying || p.onClimbable();
        boolean water = p.isInWater() || p.isUnderWater();
        boolean falling = !ground && !water && v.y < -0.35;
        float land = ground && !wasGround && !water ? Mth.clamp(-lastVy * 1.2f, 0, 1.4f) : 0;
        wasGround = ground;
        lastVy = (float) v.y;
        // knocked about (a hit, an explosion): a kick sideways from where it came
        boolean hurt = p.hurtTime > 0 && p.hurtTime == p.hurtDuration;
        float hitYaw = hurt ? p.getHurtDir() : 0;
        step(MAIN, p, 1, aFwd, aRight, aUp, speed, falling, land, water, hurt, hitYaw);
        step(OFF, p, -1, aFwd, aRight, aUp, speed, falling, land, water, hurt, hitYaw);
    }

    static void step(State s, Player p, float side, float aFwd, float aRight, float aUp, float speed, boolean falling, float land,
                     boolean water, boolean hurt, float hitYaw) {
        s.ox = s.x; s.oy = s.y; s.oz = s.z; s.op = s.pitch; s.or = s.roll;
        s.flutterO = s.flutter;
        s.liftO = s.lift;
        Material m = s.mat;
        float mass = switch (m) { case HEAVY -> 1.5f; case LIGHT -> 0.6f; case CLOTH -> 0.5f; default -> 1f; };
        // stiffness and damping per material; liquids slosh (low damping), heavy things settle slowly
        float k = switch (m) { case HEAVY -> 70; case LIGHT -> 140; case LIQUID -> 55; default -> 100; };
        float d = switch (m) { case LIQUID -> 5; case HEAVY -> 11; default -> 13; };
        if (water) {
            k *= 0.45f;
            d *= 2.4f;
        }
        // kicks this tick (velocities)
        float drive = water ? 0.4f : 1f;
        s.vx += -aRight * 6 * drive;
        s.vz += aFwd * 6 * drive;
        s.vy += -aUp * 3 * drive;
        s.vp += -aFwd * 260 * drive / mass * (m == Material.LIQUID ? 1.6f : 1);
        s.vr += aRight * 260 * drive / mass * (m == Material.LIQUID ? 1.6f : 1);
        if (land > 0) {
            // the thump: down into the hand, tipping forward; heavy things harder
            s.vy -= land * 1.4f * mass;
            s.vp += land * 120 * mass;
        }
        if (hurt) {
            float rel = Mth.wrapDegrees(hitYaw);
            float sx = Mth.sin(rel * Mth.DEG_TO_RAD), sz = Mth.cos(rel * Mth.DEG_TO_RAD);
            s.vx += sx * 0.9f;
            s.vz += sz * 0.6f;
            s.vy += 0.5f;
            s.vr += sx * 160;
            s.vp -= 90;
        }
        // free fall: floats up off the palm
        float liftTarget = falling ? (m == Material.HEAVY ? 0.05f : 0.08f) : 0;
        s.lift += (liftTarget - s.lift) * (falling ? 0.12f : 0.4f);
        // cloth: flutter by speed (and streams back)
        float flutterTarget = m == Material.CLOTH ? Mth.clamp(speed * 3.2f + (falling ? 0.8f : 0), 0, 1.4f) : 0;
        s.flutter += (flutterTarget - s.flutter) * 0.2f;
        // hanging things: a pendulum (gravity pulls the angle back, almost no damping)
        if (m == Material.HANGING) {
            k = water ? 18 : 30;
            d = water ? 6 : 1.6f;
            s.vp += -aFwd * 520 * drive;
            s.vr += aRight * 520 * drive;
        }
        // integrate in small steps
        int n = 5;
        float dt = 0.05f / n;
        for (int i = 0; i < n; i++) {
            s.vx += (-k * s.x - d * s.vx) * dt;
            s.vy += (-k * s.y - d * s.vy) * dt;
            s.vz += (-k * s.z - d * s.vz) * dt;
            s.vp += (-k * s.pitch - d * s.vp) * dt;
            s.vr += (-k * s.roll - d * s.vr) * dt;
            s.x += s.vx * dt;
            s.y += s.vy * dt;
            s.z += s.vz * dt;
            s.pitch += s.vp * dt;
            s.roll += s.vr * dt;
        }
        s.x = Mth.clamp(s.x, -0.2f, 0.2f);
        s.y = Mth.clamp(s.y, -0.2f, 0.2f);
        s.z = Mth.clamp(s.z, -0.2f, 0.2f);
        s.pitch = Mth.clamp(s.pitch, -55, 55);
        s.roll = Mth.clamp(s.roll, -55, 55);
    }

    /** This hand's physics pose now. */
    public static float[] pose(boolean mainHand, float partial) {
        if (!LMConfig.FP_PHYSICS.get()) return new float[6];
        State s = mainHand ? MAIN : OFF;
        float t = phaseTicks + partial;
        float x = Mth.lerp(partial, s.ox, s.x), y = Mth.lerp(partial, s.oy, s.y), z = Mth.lerp(partial, s.oz, s.z);
        float pitch = Mth.lerp(partial, s.op, s.pitch), roll = Mth.lerp(partial, s.or, s.roll);
        float lift = Mth.lerp(partial, s.liftO, s.lift);
        float fl = Mth.lerp(partial, s.flutterO, s.flutter);
        float yaw = 0;
        // floating: up off the palm, turning slowly
        y += lift;
        pitch += lift * 60 * Mth.sin(t * 0.25f);
        roll += lift * 40 * Mth.sin(t * 0.19f + 1);
        if (fl > 0.001f) {
            // cloth: a quick ripple on top of a slower billow, leaning back the faster you go
            pitch += (-10 * fl) + (Mth.sin(t * 1.3f) * 5 + Mth.sin(t * 2.3f + 1) * 3) * fl;
            roll += (Mth.sin(t * 1.7f + 2) * 6 + Mth.sin(t * 2.9f) * 2.5f) * fl;
            yaw += Mth.sin(t * 1.1f + 0.5f) * 4 * fl;
            y += Mth.sin(t * 1.5f) * 0.012f * fl;
        }
        return new float[]{x, y, z, pitch, yaw, roll};
    }

    public static boolean hanging(boolean mainHand) {
        return (mainHand ? MAIN : OFF).mat == Material.HANGING;
    }
}
