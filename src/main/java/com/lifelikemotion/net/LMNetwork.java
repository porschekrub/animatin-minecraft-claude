package com.lifelikemotion.net;

import com.lifelikemotion.LifelikeMotion;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.NetworkDirection;
import net.minecraftforge.network.NetworkEvent;
import net.minecraftforge.network.NetworkRegistry;
import net.minecraftforge.network.simple.SimpleChannel;

import java.util.function.Supplier;

/**
 * Optional networking, only for emotes: when the server has the mod too, an emote you play is passed on to the players
 * around you who also have it. Without it on the server (or for players without the mod) nothing is sent and the mod
 * still works fully on your own screen.
 */
public final class LMNetwork {
    private LMNetwork() {}

    static final String VERSION = "1";
    public static final SimpleChannel CHANNEL = NetworkRegistry.newSimpleChannel(new ResourceLocation(LifelikeMotion.MODID, "main"),
            () -> VERSION, NetworkRegistry.acceptMissingOr(VERSION), NetworkRegistry.acceptMissingOr(VERSION));

    /** client → server: I play this emote (-1 = stop) */
    public record PlayEmote(int emote) {
        static void encode(PlayEmote m, FriendlyByteBuf b) {
            b.writeVarInt(m.emote + 1);
        }

        static PlayEmote decode(FriendlyByteBuf b) {
            return new PlayEmote(b.readVarInt() - 1);
        }

        static void handle(PlayEmote m, Supplier<NetworkEvent.Context> ctx) {
            ServerPlayer from = ctx.get().getSender();
            ctx.get().setPacketHandled(true);
            if (from == null) return;
            ShowEmote out = new ShowEmote(from.getId(), m.emote);
            for (ServerPlayer to : from.serverLevel().players()) {
                if (to == from || to.distanceToSqr(from) > 128 * 128 || !CHANNEL.isRemotePresent(to.connection.connection)) continue;
                CHANNEL.sendTo(out, to.connection.connection, NetworkDirection.PLAY_TO_CLIENT);
            }
        }
    }

    /** server → client: this player plays an emote (-1 = stop) */
    public record ShowEmote(int entityId, int emote) {
        static void encode(ShowEmote m, FriendlyByteBuf b) {
            b.writeVarInt(m.entityId);
            b.writeVarInt(m.emote + 1);
        }

        static ShowEmote decode(FriendlyByteBuf b) {
            return new ShowEmote(b.readVarInt(), b.readVarInt() - 1);
        }

        static void handle(ShowEmote m, Supplier<NetworkEvent.Context> ctx) {
            ctx.get().setPacketHandled(true);
            DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> com.lifelikemotion.client.emote.Emotes.remote(m.entityId, m.emote));
        }
    }

    public static void register() {
        CHANNEL.messageBuilder(PlayEmote.class, 0, NetworkDirection.PLAY_TO_SERVER)
                .encoder(PlayEmote::encode).decoder(PlayEmote::decode).consumerMainThread(PlayEmote::handle).add();
        CHANNEL.messageBuilder(ShowEmote.class, 1, NetworkDirection.PLAY_TO_CLIENT)
                .encoder(ShowEmote::encode).decoder(ShowEmote::decode).consumerMainThread(ShowEmote::handle).add();
    }
}
