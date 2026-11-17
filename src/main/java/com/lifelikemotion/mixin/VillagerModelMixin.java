package com.lifelikemotion.mixin;

import com.lifelikemotion.client.body.MobAnimator;
import net.minecraft.client.model.VillagerModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(VillagerModel.class)
public abstract class VillagerModelMixin<T extends Entity> {
    @Shadow @Final private ModelPart head;

    @Inject(method = "setupAnim(Lnet/minecraft/world/entity/Entity;FFFFF)V", at = @At("HEAD"))
    private void lm$rest(T e, float swing, float amount, float age, float yaw, float pitch, CallbackInfo ci) {
        head.zRot = 0;
    }

    @Inject(method = "setupAnim(Lnet/minecraft/world/entity/Entity;FFFFF)V", at = @At("TAIL"))
    private void lm$animate(T e, float swing, float amount, float age, float yaw, float pitch, CallbackInfo ci) {
        MobAnimator.villager(e, swing, amount, age, head);
    }
}
