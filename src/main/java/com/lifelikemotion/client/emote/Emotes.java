package com.lifelikemotion.client.emote;

import com.lifelikemotion.net.LMNetwork;
import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraftforge.client.event.RegisterKeyMappingsEvent;
import net.minecraftforge.client.settings.KeyConflictContext;
import net.minecraftforge.event.TickEvent;
import org.lwjgl.glfw.GLFW;

import java.util.HashMap;
import java.util.Map;

/**
 * Who is playing which emote. Hold the emote key (B) for the wheel; pick one. Moving (or attacking, or using an item)
 * ends it. On a server that has the mod too, other players with the mod see your emotes and you see theirs.
 */
public final class Emotes {
    private Emotes() {}

    public static final KeyMapping KEY = new KeyMapping("key.lifelikemotion.emote", KeyConflictContext.IN_GAME,
            InputConstants.Type.KEYSYM.getOrCreate(GLFW.GLFW_KEY_B), "key.categories.lifelikemotion");

    public record Playing(Emote emote, long start) {}

    static final Map<Integer, Playing> PLAYING = new HashMap<>();
    static long clock;

    public static void registerKeys(RegisterKeyMappingsEvent e) {
        e.register(KEY);
    }

    public static void onClientTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null) {
            PLAYING.clear();
            return;
        }
        clock++;
        while (KEY.consumeClick()) if (mc.screen == null) mc.setScreen(new EmoteWheelScreen());
        // ends: run out, or you moved / swung / used something
        Playing mine = PLAYING.get(mc.player.getId());
        if (mine != null) {
            var in = mc.player.input;
            boolean moved = in != null && (Math.abs(in.leftImpulse) > 0.01f || Math.abs(in.forwardImpulse) > 0.01f || in.jumping || in.shiftKeyDown);
            if (moved || mc.player.swinging || mc.player.isUsingItem() || over(mine)) stop();
        }
        PLAYING.entrySet().removeIf(en -> {
            Entity who = mc.level.getEntity(en.getKey());
            // other players: their emote ends when they walk off (in case the stop never arrives)
            boolean walked = who != null && who != mc.player && who.walkDist - who.walkDistO > 0.05f;
            return over(en.getValue()) || who == null || walked;
        });
    }

    static boolean over(Playing p) {
        return p.emote().duration > 0 && clock - p.start() > p.emote().duration;
    }

    /** The local player plays an emote (and tells the server, if it has the mod). */
    public static void play(Emote emote) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null) return;
        PLAYING.put(mc.player.getId(), new Playing(emote, clock));
        send(emote.ordinal());
    }

    public static void stop() {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || PLAYING.remove(mc.player.getId()) == null) return;
        send(-1);
    }

    static void send(int id) {
        var conn = Minecraft.getInstance().getConnection();
        if (conn != null && LMNetwork.CHANNEL.isRemotePresent(conn.getConnection())) LMNetwork.CHANNEL.sendToServer(new LMNetwork.PlayEmote(id));
    }

    /** from the server: another player's emote */
    public static void remote(int entityId, int id) {
        Emote e = Emote.byId(id);
        if (e == null) PLAYING.remove(entityId);
        else PLAYING.put(entityId, new Playing(e, clock));
    }

    /** What this player is doing now, and for how long (ticks, with the partial tick). */
    public static Playing of(Entity e) {
        return e instanceof Player ? PLAYING.get(e.getId()) : null;
    }

    public static float time(Playing p, float partial) {
        return clock - p.start() + partial;
    }
}
