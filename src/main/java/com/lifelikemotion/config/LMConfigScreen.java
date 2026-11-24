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

    /** col: which of the three columns; section: a heading above this row */
    record Row(int col, String section, String label, String tip, Object value) {}

    static final Row[] ROWS = {
            new Row(0, "First person", "Custom animations", "Your own swings, sway and bob (off: the game's)", LMConfig.FP_ENABLED),
            new Row(0, null, "Arm always holds the item", "Your arm holding what you carry (else only eating and showing off)", LMConfig.FP_ARMS_WITH_ITEMS),
            new Row(0, null, "Both hands", "Both fists up when empty, your free hand at the side", LMConfig.FP_BOTH_HANDS),
            new Row(0, null, "Swing trails", "A trail behind your blade when you swing", LMConfig.FP_TRAILS),
            new Row(0, null, "Show off when still", "Twirls and tosses by themselves when you stand still (key Y any time)", LMConfig.FP_IDLE_SHOW),
            new Row(0, null, "Physics", "Inertia, floating when falling, cloth, swinging lanterns, sloshing liquids", LMConfig.FP_PHYSICS),
            new Row(0, null, "Use animations", "Pouring, scooping, striking flint, shears, bone meal, casting a rod...", LMConfig.FP_USE_ANIMS),
            new Row(0, null, "Reactions", "Flinching when hit, patting out fire", LMConfig.FP_REACTIONS),
            new Row(1, "First person (more)", "World actions", "Swimming, climbing, opening, buttons, reins, rowing, stretching, tossing", LMConfig.FP_WORLD_ACTIONS),
            new Row(1, null, "Item auras", "Sparkles, embers and glyphs around legendary and enchanted things", LMConfig.FP_AURAS),
            new Row(1, null, "Speed", "Speed of show-offs and other animations", LMConfig.FP_SPEED),
            new Row(1, null, "Sway", "How much your hands lag when you look around", LMConfig.FP_SWAY),
            new Row(1, null, "Bob", "How much your hands bob when you walk, run and jump", LMConfig.FP_BOB),
            new Row(1, null, "Swing size", "How big slashes, chops and punches are", LMConfig.FP_SWING),
            new Row(1, null, "Camera kick", "The camera kicks with swings and shakes on hits", LMConfig.FP_CAMERA),
            new Row(2, "Body", "Body animations", "Lively movement in third person", LMConfig.BODY_ENABLED),
            new Row(2, null, "Other players too", "Animate other players as well", LMConfig.BODY_OTHER_PLAYERS),
            new Row(2, null, "Strength", "How strong the body animations are", LMConfig.BODY_INTENSITY),
            new Row(2, "Mobs", "Mob animations", "Livelier mobs", LMConfig.MOBS_ENABLED),
            new Row(2, null, "Strength", "How strong the mob animations are", LMConfig.MOBS_INTENSITY),
    };

    static final int COL_W = 150, GAP = 6, TOP = 30, ROW_H = 21, HEAD = 12;

    int colX(int col) {
        return width / 2 - (3 * COL_W + 2 * GAP) / 2 + col * (COL_W + GAP);
    }

    /** where each row (and each heading) goes: [rowIndex] = y; headings get their own space */
    int[] layout(java.util.List<int[]> headings) {
        int[] y = new int[ROWS.length];
        int[] cy = {TOP, TOP, TOP};
        for (int i = 0; i < ROWS.length; i++) {
            Row r = ROWS[i];
            if (r.section() != null) {
                if (cy[r.col()] > TOP) cy[r.col()] += 4;
                if (headings != null) headings.add(new int[]{r.col(), cy[r.col()], i});
                cy[r.col()] += HEAD;
            }
            y[i] = cy[r.col()];
            cy[r.col()] += ROW_H;
        }
        return y;
    }

    @Override
    protected void init() {
        int[] y = layout(null);
        for (int i = 0; i < ROWS.length; i++)
            addRenderableWidget((net.minecraft.client.gui.components.AbstractWidget) widget(ROWS[i], colX(ROWS[i].col()), y[i], COL_W));
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
        double max = 2.0, min = d == LMConfig.FP_SPEED ? 0.5 : d == LMConfig.FP_SWING ? 0.25 : 0;
        AbstractSliderButton s = new AbstractSliderButton(x, y, w, 20, Component.empty(), (d.get() - min) / (max - min)) {
            {
                updateMessage();
            }

            @Override
            protected void updateMessage() {
                setMessage(Component.literal(r.label() + ": " + Math.round((min + value * (max - min)) * 100) + "%"));
            }

            @Override
            protected void applyValue() {
                d.set(Mth.clamp(Math.round((min + value * (max - min)) * 20) / 20.0, min, max));
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
        java.util.List<int[]> heads = new java.util.ArrayList<>();
        layout(heads);
        for (int[] h : heads) g.drawString(font, ROWS[h[2]].section(), colX(h[0]), h[1] + 2, 0xFFD27F);
        super.render(g, mx, my, partial);
    }

    @Override
    public void onClose() {
        LMConfig.SPEC.save();
        minecraft.setScreen(parent);
    }
}
