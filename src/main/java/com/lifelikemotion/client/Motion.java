package com.lifelikemotion.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.HitResult;
import net.minecraftforge.client.event.InputEvent;
import net.minecraftforge.event.TickEvent;

/**
 * What the local player is doing, smoothed, for the first-person animations: running, in the air, landing, sneaking,
 * swimming, and what the current swing is (a slash, a mining strike, a punch or putting something down).
 * Values with an "O" twin are per tick and are interpolated by the partial tick.
 */
public final class Motion {
    private Motion() {}

    public enum Action { ATTACK, MINE, USE }

    public static float sprint, sprintO, air, airO, land, landO, sneak, sneakO, water, waterO, walk, walkO;
    /** counts swings: odd and even slashes go opposite ways */
    public static int swingCount;
    public static Action action = Action.ATTACK;
    static Action pending = Action.ATTACK;
    static boolean wasGround = true;
    static double lastVy;
    public static long ticks;
    /** ticks since the item in each hand changed (for the swing-in), capped */
    static final int EQUIP_TICKS = 7;
    static int equipMain = EQUIP_TICKS, equipMainO = EQUIP_TICKS, equipOff = EQUIP_TICKS, equipOffO = EQUIP_TICKS;
    static net.minecraft.world.item.ItemStack lastMain = net.minecraft.world.item.ItemStack.EMPTY, lastOff = net.minecraft.world.item.ItemStack.EMPTY;

    /** 1 just after switching to a new item, 0 once it is in the hand */
    public static float equip(boolean mainHand, float partial) {
        float t = mainHand ? lerp(equipMainO, equipMain, partial) : lerp(equipOffO, equipOff, partial);
        float x = Mth.clamp(t / EQUIP_TICKS, 0, 1);
        return 1 - (1 - (1 - x) * (1 - x) * (1 - x));
    }

    static void onClientTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (p == null || mc.isPaused()) return;
        ticks++;
        sprintO = sprint; airO = air; landO = land; sneakO = sneak; waterO = water; walkO = walk;
        boolean ground = p.onGround() || p.getAbilities().flying || p.isPassenger() || p.onClimbable();
        boolean inWater = p.isInWater() || p.isSwimming();
        float vy = (float) p.getDeltaMovement().y;
        sprint += ((p.isSprinting() && !inWater ? 1 : 0) - sprint) * 0.2f;
        sneak += ((p.isCrouching() ? 1 : 0) - sneak) * 0.25f;
        water += ((inWater ? 1 : 0) - water) * 0.12f;
        float speed = (float) Math.min(1, p.getDeltaMovement().horizontalDistance() * 4);
        walk += ((ground ? speed : 0) - walk) * 0.25f;
        // + rising, - falling (lags a little, so the hands trail behind the jump)
        air += ((ground || inWater ? 0 : Mth.clamp(vy * 2.5f, -1, 1)) - air) * 0.3f;
        if (ground && !wasGround && !inWater) {
            land = Math.max(land, Mth.clamp((float) -lastVy * 1.4f, 0.12f, 1));
            landKick -= Mth.clamp((float) -lastVy * 1.1f, 0.15f, 1.2f);
        } else land *= 0.75f;
        // taking off: a small lift
        if (!ground && wasGround && vy > 0.2f && !inWater) landKick += 0.35f;
        wasGround = ground;
        lastVy = vy;
        // switching what's in a hand: the swing-in starts over
        net.minecraft.world.item.ItemStack main = p.getMainHandItem(), off = p.getOffhandItem();
        if (!net.minecraft.world.item.ItemStack.isSameItem(main, lastMain)) equipMain = 0;
        if (!net.minecraft.world.item.ItemStack.isSameItem(off, lastOff)) equipOff = 0;
        lastMain = main.copy();
        lastOff = off.copy();
        equipMainO = equipMain;
        equipOffO = equipOff;
        equipMain = Math.min(equipMain + 1, EQUIP_TICKS);
        equipOff = Math.min(equipOff + 1, EQUIP_TICKS);
        // a new swing started this tick
        if (p.swinging && p.swingTime == 0) {
            swingCount++;
            action = mc.gameMode != null && mc.gameMode.isDestroying() ? Action.MINE : pending;
        }
        if (mc.gameMode != null && mc.gameMode.isDestroying()) action = Action.MINE;
    }

    static void onInteraction(InputEvent.InteractionKeyMappingTriggered e) {
        Minecraft mc = Minecraft.getInstance();
        if (e.isAttack()) pending = mc.hitResult != null && mc.hitResult.getType() == HitResult.Type.BLOCK ? Action.MINE : Action.ATTACK;
        else if (e.isUseItem()) pending = Action.USE;
    }

    public static float lerp(float o, float n, float partial) {
        return o + (n - o) * partial;
    }

    // ------------------------------------------------------------ per frame: hands lag behind when you look around
    public static float lagYaw, lagPitch, velYaw, velPitch;
    /** the hands' landing spring: an offset (blocks) that dips and bounces back */
    public static float landPos, landVel;
    static float landKick;
    static float lastYaw = Float.NaN, lastPitch;
    static long lastNanos;

    /** Springs the hands' lag toward how fast the camera turns; call once per frame. */
    public static void frame(LocalPlayer p, float partial, float swayK) {
        long now = System.nanoTime();
        float dt = lastNanos == 0 ? 0.016f : Math.min((now - lastNanos) / 1e9f, 0.1f);
        lastNanos = now;
        float yaw = p.getViewYRot(partial), pitch = p.getViewXRot(partial);
        if (Float.isNaN(lastYaw) || dt <= 0) {
            lastYaw = yaw;
            lastPitch = pitch;
            return;
        }
        float dYaw = Mth.wrapDegrees(yaw - lastYaw), dPitch = pitch - lastPitch;
        lastYaw = yaw;
        lastPitch = pitch;
        // degrees per second turned -> how far the hands are pulled the other way (capped)
        float tYaw = Mth.clamp(-dYaw / dt * 0.035f, -14, 14) * swayK;
        float tPitch = Mth.clamp(-dPitch / dt * 0.03f, -10, 10) * swayK;
        // a damped spring: overshoots a little and settles, so the item feels like it has weight
        // landing / jumping: a springy dip that settles
        landVel += landKick;
        landKick = 0;
        landVel += (-landPos * 160 - landVel * 13) * dt;
        landPos += landVel * dt;
        float k = 60, d = 11;
        velYaw += ((tYaw - lagYaw) * k - velYaw * d) * dt;
        velPitch += ((tPitch - lagPitch) * k - velPitch * d) * dt;
        lagYaw += velYaw * dt;
        lagPitch += velPitch * dt;
    }
}
