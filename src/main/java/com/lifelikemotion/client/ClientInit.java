package com.lifelikemotion.client;

import com.lifelikemotion.LifelikeMotion;
import com.lifelikemotion.client.fp.FirstPersonAnimator;
import com.lifelikemotion.config.LMConfigScreen;
import net.minecraftforge.client.ConfigScreenHandler;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.ModLoadingContext;

/** Client side set-up: all listeners live here so a server never loads a client class. */
public final class ClientInit {
    private ClientInit() {}

    public static void init(IEventBus modBus) {
        ModLoadingContext.get().registerExtensionPoint(ConfigScreenHandler.ConfigScreenFactory.class,
                () -> new ConfigScreenHandler.ConfigScreenFactory((mc, parent) -> new LMConfigScreen(parent)));
        modBus.addListener(Packs::addFinders);
        modBus.addListener(com.lifelikemotion.client.emote.Emotes::registerKeys);
        modBus.addListener(com.lifelikemotion.client.fp.Flourish::registerKeys);
        var bus = MinecraftForge.EVENT_BUS;
        bus.addListener(Packs::onScreenInit);
        bus.addListener(Motion::onClientTick);
        bus.addListener(Motion::onInteraction);
        bus.addListener(FirstPersonAnimator::onRenderHand);
        bus.addListener(com.lifelikemotion.client.emote.Emotes::onClientTick);
        bus.addListener(com.lifelikemotion.client.fp.Flourish::onClientTick);
        bus.addListener(com.lifelikemotion.client.fp.ItemPhysics::onClientTick);
        bus.addListener(com.lifelikemotion.client.fp.Activities::onClientTick);
        if (Boolean.getBoolean("lifelikemotion.clientsmoke")) {
            LifelikeMotion.LOG.info("client test mode");
            bus.register(ClientSmoke.class);
            if (Boolean.getBoolean("lifelikemotion.promo")) bus.addListener(Promo::onOverlay);
        }
    }
}
