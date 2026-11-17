package com.lifelikemotion.client.emote;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.util.Mth;
import org.lwjgl.glfw.GLFW;

/** The emote wheel: point the mouse at one and click (or let go of the key). */
public class EmoteWheelScreen extends Screen {
    int hovered = -1;

    public EmoteWheelScreen() {
        super(Component.translatable("screen.lifelikemotion.emotes"));
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    @Override
    public void render(GuiGraphics g, int mx, int my, float partial) {
        Emote[] all = Emote.values();
        int cx = width / 2, cy = height / 2;
        int r = Math.min(width, height) / 3;
        double dx = mx - cx, dy = my - cy;
        hovered = -1;
        if (dx * dx + dy * dy > 18 * 18) {
            double a = Math.atan2(dy, dx) + Math.PI / 2 + Math.PI / all.length;
            if (a < 0) a += Math.PI * 2;
            hovered = (int) (a / (Math.PI * 2 / all.length)) % all.length;
        }
        g.fill(0, 0, width, height, 0x60000000);
        for (int i = 0; i < all.length; i++) {
            double a = -Math.PI / 2 + i * Math.PI * 2 / all.length;
            int x = cx + (int) (Math.cos(a) * r), y = cy + (int) (Math.sin(a) * r);
            Component name = Component.translatable(all[i].key());
            int w = font.width(name) + 16;
            boolean h = i == hovered;
            g.fill(x - w / 2, y - 11, x + w / 2, y + 11, h ? 0xE0F0B040 : 0xB0202020);
            g.renderOutline(x - w / 2, y - 11, w, 22, h ? 0xFFFFFFFF : 0x80FFFFFF);
            g.drawCenteredString(font, name, x, y - 4, h ? 0x202020 : 0xFFFFFF);
        }
        g.drawCenteredString(font, title, cx, cy - 4, 0xFFFFFF);
        // a little pointer from the middle toward the mouse
        if (hovered >= 0) {
            double len = Math.min(Math.sqrt(dx * dx + dy * dy), r * 0.6);
            for (int k = 14; k < len; k += 3) {
                int px = cx + (int) (dx / Math.sqrt(dx * dx + dy * dy) * k), py = cy + (int) (dy / Math.sqrt(dx * dx + dy * dy) * k);
                g.fill(px - 1, py - 1, px + 1, py + 1, 0xC0FFFFFF);
            }
        }
        super.render(g, mx, my, partial);
    }

    @Override
    public boolean mouseClicked(double mx, double my, int button) {
        pick();
        return true;
    }

    @Override
    public boolean keyReleased(int key, int scan, int mods) {
        // let go of the key while pointing at one: that one (a quick tap leaves the wheel open to click)
        if (Emotes.KEY.matches(key, scan) && hovered >= 0) {
            pick();
            return true;
        }
        return super.keyReleased(key, scan, mods);
    }

    @Override
    public boolean keyPressed(int key, int scan, int mods) {
        // 1-8 pick directly
        if (key >= GLFW.GLFW_KEY_1 && key < GLFW.GLFW_KEY_1 + Emote.values().length) {
            hovered = key - GLFW.GLFW_KEY_1;
            pick();
            return true;
        }
        return super.keyPressed(key, scan, mods);
    }

    void pick() {
        Emote e = hovered >= 0 ? Emote.values()[Mth.clamp(hovered, 0, Emote.values().length - 1)] : null;
        onClose();
        if (e != null) Emotes.play(e);
    }
}
