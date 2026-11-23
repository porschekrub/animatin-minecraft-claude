package com.lifelikemotion.mixin;

import net.minecraft.server.packs.PackResources;
import net.minecraft.server.packs.PackType;
import net.minecraft.server.packs.resources.ReloadInstance;
import net.minecraft.server.packs.resources.ReloadableResourceManager;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.util.Unit;
import net.minecraftforge.client.model.obj.ObjLoader;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.lang.reflect.Field;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;

/**
 * Our 3D item models are Blender meshes read by Forge's OBJ loader, which looks files up in the resource packs of the
 * reload BEFORE the current one; models in a pack switched on just now (ours, at the title screen) can't be found.
 * At the start of each reload, point it at the game's live resource manager, which always sees the current packs.
 */
@Mixin(ReloadableResourceManager.class)
public abstract class ReloadableResourceManagerMixin {
    @Shadow @Final private PackType type;
    private static Field lm$objManager;

    @Inject(method = "createReload", at = @At("HEAD"))
    private void lm$liveObjPacks(Executor background, Executor game, CompletableFuture<Unit> waiting, List<PackResources> packs,
                                 CallbackInfoReturnable<ReloadInstance> cir) {
        if (type != PackType.CLIENT_RESOURCES) return;
        try {
            if (lm$objManager == null) {
                lm$objManager = ObjLoader.class.getDeclaredField("manager");
                lm$objManager.setAccessible(true);
            }
            lm$objManager.set(ObjLoader.INSTANCE, (ResourceManager) (Object) this);
        } catch (ReflectiveOperationException | RuntimeException ignored) {
            // a Forge without the field: nothing to fix
        }
    }
}
