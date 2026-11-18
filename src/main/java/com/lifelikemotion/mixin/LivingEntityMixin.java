package com.lifelikemotion.mixin;

import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.LivingEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Hears the game's "your shield blocked a hit" event, so the first-person shield can be knocked back. */
@Mixin(LivingEntity.class)
public abstract class LivingEntityMixin {
    @Inject(method = "handleEntityEvent", at = @At("HEAD"))
    private void lm$shieldBlock(byte id, CallbackInfo ci) {
        if (id == 29 && (Object) this == Minecraft.getInstance().player) com.lifelikemotion.client.fp.Activities.shieldHit();
    }
}
