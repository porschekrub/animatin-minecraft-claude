package com.lifelikemotion.mixin;

import com.lifelikemotion.client.body.MobAnimator;
import net.minecraft.client.model.QuadrupedModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(QuadrupedModel.class)
public abstract class QuadrupedModelMixin<T extends Entity> {
    @Shadow @Final protected ModelPart head;
    @Shadow @Final protected ModelPart body;
    @Shadow @Final protected ModelPart rightHindLeg;
    @Shadow @Final protected ModelPart leftHindLeg;
    @Shadow @Final protected ModelPart rightFrontLeg;
    @Shadow @Final protected ModelPart leftFrontLeg;

    @Inject(method = "setupAnim(Lnet/minecraft/world/entity/Entity;FFFFF)V", at = @At("HEAD"))
    private void lm$rest(T e, float swing, float amount, float age, float yaw, float pitch, CallbackInfo ci) {
        MobAnimator.rest(head, body, rightHindLeg, leftHindLeg, rightFrontLeg, leftFrontLeg);
    }

    @Inject(method = "setupAnim(Lnet/minecraft/world/entity/Entity;FFFFF)V", at = @At("TAIL"))
    private void lm$animate(T e, float swing, float amount, float age, float yaw, float pitch, CallbackInfo ci) {
        MobAnimator.quadruped(e, swing, amount, age, head, body, rightHindLeg, leftHindLeg, rightFrontLeg, leftFrontLeg);
    }
}
