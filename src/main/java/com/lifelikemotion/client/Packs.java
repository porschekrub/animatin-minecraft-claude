package com.lifelikemotion.client;

import com.lifelikemotion.LifelikeMotion;
import com.lifelikemotion.config.LMConfig;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.server.packs.PackType;
import net.minecraft.server.packs.PathPackResources;
import net.minecraft.server.packs.repository.Pack;
import net.minecraft.server.packs.repository.PackSource;
import net.minecraftforge.client.event.ScreenEvent;
import net.minecraftforge.event.AddPackFindersEvent;
import net.minecraftforge.fml.ModList;

import java.nio.file.Path;

/**
 * The 3D item models come as a built-in resource pack ("Lifelike 3D Items"), so players can switch them off (or put
 * another 3D pack above them) in Options → Resource Packs. It is switched on once for you, the first time the game
 * starts with the mod; after that your choice in the menu stands.
 */
public final class Packs {
    private Packs() {}

    public static final String ITEMS_3D = "lifelikemotion:3d_items";
    static boolean checked;

    static void addFinders(AddPackFindersEvent e) {
        if (e.getPackType() != PackType.CLIENT_RESOURCES) return;
        Path path = ModList.get().getModFileById(LifelikeMotion.MODID).getFile().findResource("resourcepacks/lifelike_3d_items");
        e.addRepositorySource(add -> {
            Pack pack = Pack.readMetaAndCreate(ITEMS_3D, Component.literal("Lifelike 3D Items"), false,
                    id -> new PathPackResources(id, path, true), PackType.CLIENT_RESOURCES, Pack.Position.TOP, PackSource.BUILT_IN);
            if (pack != null) add.accept(pack);
        });
    }

    /** First start: switch the pack on (one resource reload, at the title screen). */
    static void onScreenInit(ScreenEvent.Init.Post e) {
        if (checked || !(e.getScreen() instanceof TitleScreen)) return;
        checked = true;
        if (LMConfig.ITEMS_3D_PACK_ADDED.get()) return;
        Minecraft mc = Minecraft.getInstance();
        var repo = mc.getResourcePackRepository();
        LMConfig.ITEMS_3D_PACK_ADDED.set(true);
        LMConfig.SPEC.save();
        if (!repo.isAvailable(ITEMS_3D) || repo.getSelectedIds().contains(ITEMS_3D)) return;
        repo.addPack(ITEMS_3D);
        LifelikeMotion.LOG.info("switched on the Lifelike 3D Items resource pack (first start)");
        mc.options.updateResourcePacks(repo);
    }

    /** For the client test (quick play skips the title screen). */
    static void enableNow() {
        Minecraft mc = Minecraft.getInstance();
        var repo = mc.getResourcePackRepository();
        if (repo.isAvailable(ITEMS_3D) && !repo.getSelectedIds().contains(ITEMS_3D)) {
            repo.addPack(ITEMS_3D);
            mc.options.updateResourcePacks(repo);
        }
    }
}
