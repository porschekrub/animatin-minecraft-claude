package com.lifelikemotion.config;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.AbstractSliderButton;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.CommonComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.util.Mth;
import net.minecraftforge.common.ForgeConfigSpec;

/** Mods → Lifelike Motion → Config. Changes apply right away. */
public class LMConfigScreen extends Screen {
    final Screen parent;

    public LMConfigScreen(Screen parent) {
        super(Component.literal("Lifelike Motion"));
        this.parent = parent;
    }

    record Row(String section, String label, String tip, Object value) {}

    static final Row[] ROWS = {
            new Row("First person", "Custom animations", "Your own swings, sway and bob (off: the game's)", LMConfig.FP_ENABLED),
            new Row(null, "Arm holds the item", "Show your arm holding what you carry", LMConfig.FP_ARMS_WITH_ITEMS),
            new Row(null, "Sway", "How much your hands lag when you look around", LMConfig.FP_SWAY),
            new Row(null, "Bob", "How much your hands bob when you walk, run and jump", LMConfig.FP_BOB),
            new Row(null, "Swing size", "How big slashes, chops and punches are", LMConfig.FP_SWING),
            new Row("Body", "Body animations", "Lively movement in third person", LMConfig.BODY_ENABLED),
            new Row(null, "Other players too", "Animate other players as well", LMConfig.BODY_OTHER_PLAYERS),
            new Row(null, "Strength", "How strong the body animations are", LMConfig.BODY_INTENSITY),
            new Row("Mobs", "Mob animations", "Livelier mobs", LMConfig.MOBS_ENABLED),
            new Row(null, "Strength", "How strong the mob animations are", LMConfig.MOBS_INTENSITY),
    };

    @Override
    protected void init() {
        int colW = 150, gap = 10;
        int left = width / 2 - colW - gap / 2, right = width / 2 + gap / 2;
        int top = 34, rowH = 22;
        // two columns: first person on the left, body and mobs on the right
        int[] y = {top + 12, top + 12};
        int col = 0;
        for (Row r : ROWS) {
            if (r.section() != null && !r.section().equals("First person")) {
                if (col == 1) y[1] += 14; // room for the "Mobs" heading
                col = 1;
            }
            addRenderableWidget((net.minecraft.client.gui.components.AbstractWidget) widget(r, col == 0 ? left : right, y[col], colW));
            y[col] += rowH;
        }
        addRenderableWidget(Button.builder(CommonComponents.GUI_DONE, b -> onClose()).bounds(width / 2 - 100, height - 28, 200, 20).build());
    }

    Object widget(Row r, int x, int y, int w) {
        Tooltip tip = Tooltip.create(Component.literal(r.tip()));
        if (r.value() instanceof ForgeConfigSpec.BooleanValue b) {
            Button btn = Button.builder(label(r.label(), b.get()), bb -> {
                b.set(!b.get());
                bb.setMessage(label(r.label(), b.get()));
                LMConfig.SPEC.save();
            }).bounds(x, y, w, 20).tooltip(tip).build();
            return btn;
        }
        ForgeConfigSpec.DoubleValue d = (ForgeConfigSpec.DoubleValue) r.value();
        double max = 2.0;
        AbstractSliderButton s = new AbstractSliderButton(x, y, w, 20, Component.empty(), d.get() / max) {
            {
                updateMessage();
            }

            @Override
            protected void updateMessage() {
                setMessage(Component.literal(r.label() + ": " + Math.round(value * max * 100) + "%"));
            }

            @Override
            protected void applyValue() {
                d.set(Mth.clamp(Math.round(value * max * 20) / 20.0, 0, max));
                LMConfig.SPEC.save();
            }
        };
        s.setTooltip(tip);
        return s;
    }

    static Component label(String name, boolean on) {
        return Component.literal(name + ": ").append(on ? CommonComponents.OPTION_ON : CommonComponents.OPTION_OFF);
    }

    @Override
    public void render(GuiGraphics g, int mx, int my, float partial) {
        renderBackground(g);
        g.drawCenteredString(font, title, width / 2, 12, 0xFFFFFF);
        int colW = 150, gap = 10;
        g.drawString(font, "First person", width / 2 - colW - gap / 2, 34, 0xFFD27F);
        g.drawString(font, "Body", width / 2 + gap / 2, 34, 0xFFD27F);
        g.drawString(font, "Mobs", width / 2 + gap / 2, 34 + 12 + 3 * 22 + 2, 0xFFD27F);
        g.drawCenteredString(font, Component.literal("3D items: Options → Resource Packs → \"Lifelike 3D Items\""), width / 2, height - 44, 0xA0A0A0);
        super.render(g, mx, my, partial);
    }

    @Override
    public void onClose() {
        LMConfig.SPEC.save();
        minecraft.setScreen(parent);
    }
}
