package com.lifelikemotion.mixin;

import com.lifelikemotion.client.body.MobAnimator;
import net.minecraft.client.model.WolfModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.world.entity.animal.Wolf;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(WolfModel.class)
public abstract class WolfModelMixin<T extends Wolf> {
    @Shadow @Final private ModelPart head;
    @Shadow @Final private ModelPart tail;
    @Shadow @Final private ModelPart body;

    @Inject(method = "setupAnim(Lnet/minecraft/world/entity/animal/Wolf;FFFFF)V", at = @At("HEAD"))
    private void lm$rest(T e, float swing, float amount, float age, float yaw, float pitch, CallbackInfo ci) {
        // (the wolf's own prepareMobModel moves body and tail for sitting: only the head is ours to reset)
        MobAnimator.rest(head);
    }

    @Inject(method = "setupAnim(Lnet/minecraft/world/entity/animal/Wolf;FFFFF)V", at = @At("TAIL"))
    private void lm$animate(T e, float swing, float amount, float age, float yaw, float pitch, CallbackInfo ci) {
        MobAnimator.wolf(e, swing, amount, age, head, tail, body);
    }
}
