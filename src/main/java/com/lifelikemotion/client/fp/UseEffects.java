package com.lifelikemotion.client.fp;

import com.lifelikemotion.client.Motion;
import com.lifelikemotion.config.LMConfig;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/** Little touches where a used thing meets the world: sparks off flint, soil off a hoe, chips off a stripped log... */
public final class UseEffects {
    private UseEffects() {}

    public static void onSwing(LocalPlayer p, Motion.Action a, Vec3 at) {
        if (at == null || !LMConfig.FP_USE_ANIMS.get()) return;
        var lvl = p.level();
        BlockPos pos = BlockPos.containing(at.x - (at.x - p.getX()) * 0.001, at.y - 0.001, at.z - (at.z - p.getZ()) * 0.001);
        var state = lvl.getBlockState(pos);
        switch (a) {
            case STRIKE -> {
                burst(p, at, ParticleTypes.ELECTRIC_SPARK, 6, 0.08);
                burst(p, at, ParticleTypes.SMALL_FLAME, 2, 0.03);
            }
            case TILL -> burst(p, at.add(0, 0.05, 0), new BlockParticleOption(ParticleTypes.BLOCK, Blocks.DIRT.defaultBlockState()), 10, 0.12);
            case STRIP, FLATTEN -> {
                if (!state.isAir()) burst(p, at, new BlockParticleOption(ParticleTypes.BLOCK, state), 8, 0.1);
            }
            case SPRINKLE -> burst(p, at.add(0, 0.1, 0), ParticleTypes.WHITE_ASH, 12, 0.05);
            case SCOOP -> {
                if (!lvl.getFluidState(pos).isEmpty()) burst(p, at, ParticleTypes.SPLASH, 10, 0.1);
            }
            case POUR -> burst(p, at.add(0, 0.2, 0), ParticleTypes.SPLASH, 6, 0.06);
            default -> {}
        }
    }

    static void burst(LocalPlayer p, Vec3 at, ParticleOptions type, int n, double spread) {
        var r = p.getRandom();
        for (int i = 0; i < n; i++)
            p.level().addParticle(type, at.x + (r.nextDouble() - 0.5) * 0.3, at.y + r.nextDouble() * 0.1, at.z + (r.nextDouble() - 0.5) * 0.3,
                    (r.nextDouble() - 0.5) * spread, r.nextDouble() * spread, (r.nextDouble() - 0.5) * spread);
    }

    /** a soft sound for the hand's own moves (used by one-shots) */
    static void sound(LocalPlayer p, net.minecraft.sounds.SoundEvent s, float vol, float pitch) {
        Minecraft.getInstance().level.playLocalSound(p.getX(), p.getEyeY(), p.getZ(), s, SoundSource.PLAYERS, vol, pitch, false);
    }

    static final net.minecraft.sounds.SoundEvent WHOOSH = SoundEvents.PLAYER_ATTACK_NODAMAGE;
}
