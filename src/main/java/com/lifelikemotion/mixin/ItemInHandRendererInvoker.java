package com.lifelikemotion.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.ItemInHandRenderer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

/** Lets the first-person animator draw the game's own hand for special items (bows, maps, shields...) inside its sway. */
@Mixin(ItemInHandRenderer.class)
public interface ItemInHandRendererInvoker {
    @Invoker("renderArmWithItem")
    void lm$renderArmWithItem(AbstractClientPlayer player, float partial, float pitch, InteractionHand hand, float swing, ItemStack stack,
                              float equip, PoseStack poseStack, MultiBufferSource buffers, int light);
}
