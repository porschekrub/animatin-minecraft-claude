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

    /**
     * What a swing is for. USE is putting something down; the rest are using a particular thing (pouring a bucket,
     * striking flint...) or working something in the world (opening a chest or door, pressing a button, pulling a lever).
     */
    public enum Action { ATTACK, MINE, USE, OPEN, PRESS, PULL, POUR, SCOOP, STRIKE, SNIP, SPRINKLE, TILL, STRIP, FLATTEN, CAST, REEL }

    /** where the thing being used was aimed (for sparks, soil...) */
    public static net.minecraft.world.phys.Vec3 usedAt;

    /** swinging, mining or using something (smoothed, 0..1) */
    public static float busy, busyO;
    public static float sprint, sprintO, air, airO, land, landO, sneak, sneakO, water, waterO, walk, walkO;
    /** counts swings: odd and even slashes go opposite ways */
    public static int swingCount;
    /**
     * Swings run on our own clock (longer and bigger than the game's quick one): when the last one started (ticks) and
     * with which hand. Mining is a loop of its own for as long as a block is being broken.
     */
    public static long swingStart = -1000, mineStart = -1000, mineStop = -1000;
    public static boolean swingOffHand, mining;
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
        busyO = busy;
        boolean isBusy = p.swinging || p.isUsingItem() || mc.gameMode != null && mc.gameMode.isDestroying()
                || ticks - swingStart < 12;
        busy += ((isBusy ? 1 : 0) - busy) * (isBusy ? 0.6f : 0.15f);
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
        boolean destroying = mc.gameMode != null && mc.gameMode.isDestroying();
        if (p.swinging && p.swingTime == 0) {
            action = destroying ? Action.MINE : pending;
            // (while mining the game swings again and again: that is the mining loop, not new swings)
            if (!destroying) {
                swingCount++;
                swingStart = ticks;
                swingOffHand = p.swingingArm == net.minecraft.world.InteractionHand.OFF_HAND;
            }
            com.lifelikemotion.client.fp.UseEffects.onSwing(p, action, usedAt);
        }
        if (destroying) action = Action.MINE;
        if (destroying && !mining) {
            mining = true;
            mineStart = ticks;
        } else if (!destroying && mining) {
            mining = false;
            mineStop = ticks;
        }
    }

    static void onInteraction(InputEvent.InteractionKeyMappingTriggered e) {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (p == null) return;
        net.minecraft.world.item.ItemStack held = p.getItemInHand(e.getHand());
        if (e.isAttack()) {
            pending = mc.hitResult != null && mc.hitResult.getType() == HitResult.Type.BLOCK ? Action.MINE : Action.ATTACK;
            if (held.getItem() instanceof net.minecraft.world.item.ShearsItem && com.lifelikemotion.config.LMConfig.FP_USE_ANIMS.get()) pending = Action.SNIP;
        } else if (e.isUseItem()) pending = useAction(mc, p, held);
    }

    /** What right-clicking will do: work a block in the world, use the held thing in its own way, or put it down. */
    static Action useAction(Minecraft mc, LocalPlayer p, net.minecraft.world.item.ItemStack held) {
        net.minecraft.world.item.Item i = held.getItem();
        boolean onBlock = mc.hitResult instanceof net.minecraft.world.phys.BlockHitResult bh && bh.getType() == HitResult.Type.BLOCK;
        usedAt = mc.hitResult != null ? mc.hitResult.getLocation() : null;
        if (onBlock && !p.isSecondaryUseActive() && com.lifelikemotion.config.LMConfig.FP_WORLD_ACTIONS.get()) {
            var pos = ((net.minecraft.world.phys.BlockHitResult) mc.hitResult).getBlockPos();
            var state = mc.level.getBlockState(pos);
            var b = state.getBlock();
            if (b instanceof net.minecraft.world.level.block.ButtonBlock) return Action.PRESS;
            if (b instanceof net.minecraft.world.level.block.LeverBlock) return Action.PULL;
            if (b instanceof net.minecraft.world.level.block.DoorBlock || b instanceof net.minecraft.world.level.block.TrapDoorBlock
                    || b instanceof net.minecraft.world.level.block.FenceGateBlock || state.getMenuProvider(mc.level, pos) != null
                    || b instanceof net.minecraft.world.level.block.ChestBlock || b instanceof net.minecraft.world.level.block.EnderChestBlock
                    || b instanceof net.minecraft.world.level.block.ShulkerBoxBlock || b instanceof net.minecraft.world.level.block.BarrelBlock)
                return Action.OPEN;
        }
        if (!com.lifelikemotion.config.LMConfig.FP_USE_ANIMS.get()) return Action.USE;
        if (i instanceof net.minecraft.world.item.BucketItem bucket)
            return bucket.getFluid() == net.minecraft.world.level.material.Fluids.EMPTY ? Action.SCOOP : Action.POUR;
        if (i instanceof net.minecraft.world.item.FlintAndSteelItem || i instanceof net.minecraft.world.item.FireChargeItem && onBlock) return Action.STRIKE;
        if (i instanceof net.minecraft.world.item.ShearsItem) return Action.SNIP;
        if (i instanceof net.minecraft.world.item.BoneMealItem || i instanceof net.minecraft.world.item.ItemNameBlockItem
                && ((net.minecraft.world.item.ItemNameBlockItem) i).getBlock() instanceof net.minecraft.world.level.block.BushBlock)
            return Action.SPRINKLE;
        if (onBlock && i instanceof net.minecraft.world.item.HoeItem) return Action.TILL;
        if (onBlock && i instanceof net.minecraft.world.item.AxeItem) return Action.STRIP;
        if (onBlock && i instanceof net.minecraft.world.item.ShovelItem) return Action.FLATTEN;
        if (i instanceof net.minecraft.world.item.FishingRodItem) return p.fishing == null ? Action.CAST : Action.REEL;
        return Action.USE;
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
    static float lastT = Float.NaN;

    /** Springs the hands' lag toward how fast the camera turns; call once per frame. */
    public static void frame(LocalPlayer p, float partial, float swayK) {
        // (game time, so the springs keep pace with everything else, slowed or paused)
        float now = ticks + partial;
        float dt = Float.isNaN(lastT) ? 0.016f : Mth.clamp((now - lastT) * 0.05f, 0, 0.1f);
        lastT = now;
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
        float tYaw = Mth.clamp(-dYaw / dt * 0.05f, -24, 24) * swayK;
        float tPitch = Mth.clamp(-dPitch / dt * 0.045f, -18, 18) * swayK;
        // a damped spring: overshoots a little and settles, so the item feels like it has weight
        // landing / jumping: a springy dip that settles
        landVel += landKick;
        landKick = 0;
        landVel += (-landPos * 160 - landVel * 13) * dt;
        landPos += landVel * dt;
        float k = 70, d = 8.5f;
        velYaw += ((tYaw - lagYaw) * k - velYaw * d) * dt;
        velPitch += ((tPitch - lagPitch) * k - velPitch * d) * dt;
        lagYaw += velYaw * dt;
        lagPitch += velPitch * dt;
    }
}
