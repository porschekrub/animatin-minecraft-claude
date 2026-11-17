package com.lifelikemotion;

import com.lifelikemotion.config.LMConfig;
import com.mojang.logging.LogUtils;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;

/**
 * Lifelike Motion: chunky 3D items, weighty first-person animations and lively body movement.
 * Everything happens on the client; a server with the mod installed only runs its start-up check.
 */
@Mod(LifelikeMotion.MODID)
public class LifelikeMotion {
    public static final String MODID = "lifelikemotion";
    public static final Logger LOG = LogUtils.getLogger();

    public LifelikeMotion() {
        var bus = FMLJavaModLoadingContext.get().getModEventBus();
        ModLoadingContext.get().registerConfig(ModConfig.Type.CLIENT, LMConfig.SPEC);
        DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> com.lifelikemotion.client.ClientInit.init(bus));
        if (Boolean.getBoolean("lifelikemotion.smoketest"))
            net.minecraftforge.common.MinecraftForge.EVENT_BUS.addListener((net.minecraftforge.event.server.ServerStartedEvent e) -> {
                LOG.info("SMOKE TEST OK");
                e.getServer().halt(false);
            });
    }
}
