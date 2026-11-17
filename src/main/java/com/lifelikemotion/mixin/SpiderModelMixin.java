package com.lifelikemotion.mixin;

import com.lifelikemotion.client.body.MobAnimator;
import net.minecraft.client.model.SpiderModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(SpiderModel.class)
public abstract class SpiderModelMixin<T extends Entity> {
    @Shadow @Final private ModelPart rightHindLeg;
    @Shadow @Final private ModelPart leftHindLeg;
    @Shadow @Final private ModelPart rightMiddleHindLeg;
    @Shadow @Final private ModelPart leftMiddleHindLeg;
    @Shadow @Final private ModelPart rightMiddleFrontLeg;
    @Shadow @Final private ModelPart leftMiddleFrontLeg;
    @Shadow @Final private ModelPart rightFrontLeg;
    @Shadow @Final private ModelPart leftFrontLeg;

    @Inject(method = "setupAnim(Lnet/minecraft/world/entity/Entity;FFFFF)V", at = @At("TAIL"))
    private void lm$animate(T e, float swing, float amount, float age, float yaw, float pitch, CallbackInfo ci) {
        MobAnimator.spider(e, age, rightHindLeg, leftHindLeg, rightMiddleHindLeg, leftMiddleHindLeg, rightMiddleFrontLeg, leftMiddleFrontLeg,
                rightFrontLeg, leftFrontLeg);
    }
}
