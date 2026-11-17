package com.lifelikemotion.client.emote;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import org.lwjgl.glfw.GLFW;

import java.util.ArrayList;
import java.util.List;

/**
 * The emote wheel: the game's own buttons in a ring, no darkening of the world behind. Point the mouse at one and
 * click (or let go of the key), or press 1-8.
 */
public class EmoteWheelScreen extends Screen {
    int hovered = -1;
    final List<Button> buttons = new ArrayList<>();

    public EmoteWheelScreen() {
        super(Component.translatable("screen.lifelikemotion.emotes"));
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    @Override
    protected void init() {
        buttons.clear();
        Emote[] all = Emote.values();
        int cx = width / 2, cy = height / 2;
        int r = Math.min(width, height) / 3;
        for (int i = 0; i < all.length; i++) {
            double a = -Math.PI / 2 + i * Math.PI * 2 / all.length;
            int x = cx + (int) (Math.cos(a) * r), y = cy + (int) (Math.sin(a) * r);
            Emote em = all[i];
            Button b = Button.builder(Component.literal((i + 1) + "  ").append(Component.translatable(em.key())), bb -> choose(em))
                    .bounds(x - 45, y - 10, 90, 20).build();
            buttons.add(b);
            addRenderableWidget(b);
        }
    }

    @Override
    public void renderBackground(GuiGraphics g) {
        // (no dark overlay: the world stays as bright as it is)
    }

    @Override
    public void render(GuiGraphics g, int mx, int my, float partial) {
        Emote[] all = Emote.values();
        int cx = width / 2, cy = height / 2;
        double dx = mx - cx, dy = my - cy;
        hovered = -1;
        if (dx * dx + dy * dy > 18 * 18) {
            double a = Math.atan2(dy, dx) + Math.PI / 2 + Math.PI / all.length;
            if (a < 0) a += Math.PI * 2;
            hovered = (int) (a / (Math.PI * 2 / all.length)) % all.length;
        }
        // the pointed-at button lights up like a hovered one
        for (int i = 0; i < buttons.size(); i++) buttons.get(i).setFocused(i == hovered);
        g.drawCenteredString(font, title, cx, cy - 4, 0xFFFFFF);
        super.render(g, mx, my, partial);
    }

    @Override
    public boolean mouseClicked(double mx, double my, int button) {
        if (super.mouseClicked(mx, my, button)) return true;
        if (hovered >= 0) choose(Emote.values()[hovered]);
        return true;
    }

    @Override
    public boolean keyReleased(int key, int scan, int mods) {
        // let go of the key while pointing at one: that one (a quick tap leaves the wheel open to click)
        if (Emotes.KEY.matches(key, scan) && hovered >= 0) {
            choose(Emote.values()[hovered]);
            return true;
        }
        return super.keyReleased(key, scan, mods);
    }

    @Override
    public boolean keyPressed(int key, int scan, int mods) {
        if (key >= GLFW.GLFW_KEY_1 && key < GLFW.GLFW_KEY_1 + Emote.values().length) {
            choose(Emote.values()[key - GLFW.GLFW_KEY_1]);
            return true;
        }
        return super.keyPressed(key, scan, mods);
    }

    void choose(Emote e) {
        onClose();
        Emotes.play(e);
    }
}
