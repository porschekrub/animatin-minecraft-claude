package com.lifelikemotion.client.fp;

import com.lifelikemotion.config.LMConfig;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.item.*;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.TickEvent;
import org.joml.Vector3f;

/**
 * Little bits of magic around what you hold (first person, and around other players in third): diamond gear sparkles
 * cyan, netherite drifts embers, gold glints, enchanted things shed enchanting glyphs, a trident trails sea light, a
 * torch or lantern gives off the odd spark. Rare and small, so it never gets in the way.
 */
public final class ItemAura {
    private ItemAura() {}

    static final DustParticleOptions CYAN = new DustParticleOptions(new Vector3f(0.6f, 1f, 1f), 0.22f);
    static final DustParticleOptions GOLD = new DustParticleOptions(new Vector3f(1f, 0.88f, 0.35f), 0.2f);
    static final DustParticleOptions EMBER = new DustParticleOptions(new Vector3f(1f, 0.55f, 0.12f), 0.25f);

    public static void onClientTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        if (p == null || mc.isPaused() || !LMConfig.FP_AURAS.get() || p.isInvisible()) return;
        for (boolean main : new boolean[]{true, false}) {
            ItemStack s = main ? p.getMainHandItem() : p.getOffhandItem();
            if (s.isEmpty()) continue;
            ParticleOptions type = null;
            float chance = 0;
            String id = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(s.getItem()).getPath();
            if (id.startsWith("diamond_")) { type = CYAN; chance = 0.12f; }
            else if (id.startsWith("netherite_")) { type = EMBER; chance = 0.12f; }
            else if (id.startsWith("golden_") || s.is(Items.TOTEM_OF_UNDYING)) { type = GOLD; chance = 0.08f; }
            else if (s.getItem() instanceof TridentItem) { type = ParticleTypes.GLOW; chance = 0.06f; }
            else if (s.is(Items.TORCH) || s.is(Items.LANTERN)) { type = ParticleTypes.SMALL_FLAME; chance = 0.06f; }
            else if (s.is(Items.SOUL_TORCH) || s.is(Items.SOUL_LANTERN)) { type = ParticleTypes.SOUL_FIRE_FLAME; chance = 0.06f; }
            if (s.isEnchanted() && p.getRandom().nextFloat() < 0.15f) spawn(mc, p, main, ParticleTypes.ENCHANT, true);
            if (type != null && p.getRandom().nextFloat() < chance) spawn(mc, p, main, type, false);
        }
    }

    /** a point at the held item: in first person in front of the camera, to the hand's side; else at the hand */
    static void spawn(Minecraft mc, LocalPlayer p, boolean main, ParticleOptions type, boolean drift) {
        var r = p.getRandom();
        boolean right = main == (p.getMainArm() == HumanoidArm.RIGHT);
        float side = right ? 1 : -1;
        Vec3 look = p.getViewVector(1);
        Vec3 up = p.getUpVector(1);
        Vec3 rightV = look.cross(up).normalize();
        boolean fp = mc.options.getCameraType() == CameraType.FIRST_PERSON;
        Vec3 at = fp
                ? p.getEyePosition(1).add(look.scale(1.0)).add(rightV.scale(0.42 * side)).add(up.scale(-0.2))
                : p.position().add(0, 0.8, 0).add(rightV.scale(0.4 * side)).add(look.scale(0.3));
        at = at.add((r.nextDouble() - 0.5) * 0.25, (r.nextDouble() - 0.5) * 0.3, (r.nextDouble() - 0.5) * 0.25);
        Vec3 v = p.getDeltaMovement();
        double vy = drift ? 0.0 : 0.012 + r.nextDouble() * 0.01;
        p.level().addParticle(type, at.x, at.y, at.z, v.x + (r.nextDouble() - 0.5) * 0.01, vy, v.z + (r.nextDouble() - 0.5) * 0.01);
    }
}
