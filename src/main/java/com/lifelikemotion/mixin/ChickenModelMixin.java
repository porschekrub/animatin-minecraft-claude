package com.lifelikemotion.mixin;

import com.lifelikemotion.client.body.MobAnimator;
import net.minecraft.client.model.ChickenModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ChickenModel.class)
public abstract class ChickenModelMixin<T extends Entity> {
    @Shadow @Final private ModelPart head;
    @Shadow @Final private ModelPart beak;
    @Shadow @Final private ModelPart redThing;
    @Shadow @Final private ModelPart body;
    @Shadow @Final private ModelPart rightWing;
    @Shadow @Final private ModelPart leftWing;

    @Inject(method = "setupAnim(Lnet/minecraft/world/entity/Entity;FFFFF)V", at = @At("HEAD"))
    private void lm$rest(T e, float swing, float amount, float age, float yaw, float pitch, CallbackInfo ci) {
        MobAnimator.rest(head, beak, redThing, body);
    }

    @Inject(method = "setupAnim(Lnet/minecraft/world/entity/Entity;FFFFF)V", at = @At("TAIL"))
    private void lm$animate(T e, float swing, float amount, float age, float yaw, float pitch, CallbackInfo ci) {
        MobAnimator.chicken(e, swing, amount, age, head, beak, redThing, body, rightWing, leftWing);
    }
}
