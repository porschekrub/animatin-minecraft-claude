package com.lifelikemotion.client;

import com.lifelikemotion.client.emote.Emote;
import com.lifelikemotion.client.emote.Emotes;
import com.lifelikemotion.client.fp.Activities;
import com.lifelikemotion.client.fp.Clip;
import com.lifelikemotion.client.fp.Clips;
import com.lifelikemotion.client.fp.Flourish;
import com.lifelikemotion.client.fp.Flourishes;
import com.lifelikemotion.client.fp.FirstPersonAnimator;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;

import static com.lifelikemotion.client.ClientSmoke.*;

/**
 * Pictures for the mod's page (-Dlifelikemotion.promo=true, with the client test): builds a little scene (a village,
 * trees, a pond, animals), hides the HUD and pop-ups, and takes stills ("promo_...") and frame runs for animated GIFs
 * ("gif_<name>_<n>").
 */
final class Promo {
    private Promo() {}

    /** the HUD (hotbar, crosshair, hearts...) is left out, but not your hands (the game's F1 hides those too) */
    static boolean hideHud;

    static void onOverlay(net.minecraftforge.client.event.RenderGuiOverlayEvent.Pre e) {
        if (hideHud) e.setCanceled(true);
    }

    static void build() {
        Minecraft mc = Minecraft.getInstance();
        add(t -> {
            if (t == 0) {
                cmd("gamemode creative");
                cmd("time set 1500");
                cmd("weather clear");
                cmd("gamerule doDaylightCycle false");
                cmd("gamerule doWeatherCycle false");
                cmd("gamerule doMobSpawning false");
                cmd("kill @e[type=!player]");
                cmd("place structure minecraft:village_plains 0 -60 48");
                cmd("fill -9 -61 20 -3 -61 27 water");
                cmd("fill -9 -62 20 -3 -62 27 water");
                for (int[] p : new int[][]{{-7, 31}, {8, 27}, {-12, 38}, {13, 35}, {-14, 22}, {15, 18}})
                    cmd(String.format("place feature minecraft:%s %d -60 %d", p[0] % 2 == 0 ? "fancy_oak" : "oak", p[0], p[1]));
                cmd("place feature minecraft:flower_plain 2 -60 24");
                cmd("place feature minecraft:flower_plain -2 -60 30");
                cmd("place feature minecraft:patch_grass 0 -60 22");
                cmd("tp @s 0 -60 16 0 8");
            }
            if (t == 60) {
                for (String[] m : new String[][]{{"cow", "5 -60 26"}, {"pig", "-1 -60 29"}, {"sheep", "3 -60 31"}, {"chicken", "1 -60 25"}})
                    cmd("summon " + m[0] + " " + m[1] + " {NoAI:1b,PersistenceRequired:1b,Rotation:[160f,0f]}");
                hideHud = true;
            }
            return t > 140;
        });
        // ---- stills
        still("promo_sword_twirl", "diamond_sword", () -> pose(Flourishes.SWORD_TWIRL_WIPE, 0.24f), 8f);
        still("promo_sword_wipe", "diamond_sword", () -> pose(Flourishes.SWORD_TWIRL_WIPE, 0.6f), 8f);
        still("promo_sword_slash", "diamond_sword", () -> swing(Clips.SLASH_A, 0.42f), 8f);
        still("promo_axe_toss", "diamond_axe", () -> pose(Flourishes.TOOL_TOSS, 0.45f), 4f);
        still("promo_lantern", "lantern", () -> pose(Flourishes.LIGHT_RAISE, 0.45f), 6f);
        still("promo_book", "book", () -> pose(Flourishes.BOOK_READ, 0.3f), 10f);
        still("promo_compass", "compass", () -> pose(Flourishes.COMPASS_LOOK, 0.45f), 10f);
        still("promo_pour", "water_bucket", () -> swing(Clips.POUR, 0.5f), 25f);
        add(t -> {
            if (t == 0) {
                give("air");
                cmd("tp @s 0 -60 16 0 30");
                String[] items = {"diamond_sword", "golden_apple", "iron_pickaxe", "bread", "diamond", "cooked_beef", "emerald", "carrot", "torch"};
                for (int i = 0; i < items.length; i++)
                    cmd(String.format("summon item %.2f -60 %.2f {Item:{id:\"minecraft:%s\",Count:1b},PickupDelay:32767,Age:-32768}",
                            -1.6 + (i % 3) * 1.4, 19.0 + (i / 3) * 1.1, items[i]));
            }
            hold(0f, 50f);
            if (t == 40) shot("promo_items3d");
            if (t == 41) {
                cmd("kill @e[type=item]");
                release();
            }
            return t > 44;
        });
        // third person: waving at the village, then the animals
        add(t -> {
            if (t == 0) {
                give("air");
                cmd("tp @s 0 -60 22 180 0");
                mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
            }
            hold(0f, 10f);
            if (t == 4) Emotes.play(Emote.WAVE);
            if (t == 20) shot("promo_third_person_wave");
            if (t == 21) {
                Emotes.stop();
                mc.options.setCameraType(CameraType.FIRST_PERSON);
                release();
            }
            return t > 24;
        });
        add(t -> {
            if (t == 0) cmd("tp @s 3 -60 20 0 20");
            hold(0f, 20f);
            if (t == 30) shot("promo_animals");
            if (t == 31) release();
            return t > 32;
        });
        add(t -> {
            if (t == 0) {
                give("air");
                cmd("tp @s -6 -61 23 0 5");
                Activities.testActivity = "swim";
            }
            hold(0f, 5f);
            if (t == 22) shot("promo_swim");
            if (t == 23) {
                Activities.testActivity = null;
                cmd("tp @s 0 -60 16 0 8");
                release();
            }
            return t > 26;
        });
        add(t -> {
            if (t == 0) {
                give("golden_apple");
                mc.options.keyUse.setDown(true);
            }
            hold(0f, 8f);
            if (t == 14) shot("promo_eat");
            if (t == 15) {
                mc.options.keyUse.setDown(false);
                release();
            }
            return t > 40;
        });
        // ---- animated GIFs: posed moves (one frame every two ticks)
        gifPose("sword_twirl", "diamond_sword", Flourishes.SWORD_TWIRL_WIPE, 40);
        gifPose("axe_toss", "diamond_axe", Flourishes.TOOL_TOSS, 24);
        gifPose("lantern_raise", "lantern", Flourishes.LIGHT_RAISE, 28);
        gifPose("egg_toss", "egg", Flourishes.EGG_TOSS, 26);
        gifSwings("sword_combo", "diamond_sword", new Clip[]{Clips.SLASH_A, Clips.SLASH_B, Clips.STAB}, 11);
        gifSwings("pickaxe_mine", "diamond_pickaxe", new Clip[]{Clips.MINE, Clips.MINE}, 9);
        gifSwings("bucket_pour", "water_bucket", new Clip[]{Clips.POUR}, 16);
        // real time (one frame a tick)
        add(t -> {
            if (t == 0) {
                give("oak_planks");
                cmd("tp @s 0 -48 16 0 30");
            }
            hold(0f, 30f);
            if (t >= 2 && t < 44) shot(String.format("gif_fall_box_%03d", t - 2));
            if (t == 44) release();
            return t > 46;
        });
        add(t -> {
            if (t == 0) {
                give("lantern");
                cmd("tp @s 0 -60 8 0 5");
            }
            hold(0f, 5f);
            if (t == 6) {
                mc.options.keyUp.setDown(true);
                mc.options.keySprint.setDown(true);
                mc.player.setSprinting(true);
            }
            if (t == 22) {
                mc.options.keyUp.setDown(false);
                mc.options.keySprint.setDown(false);
                mc.player.setSprinting(false);
            }
            if (t >= 8 && t < 52) shot(String.format("gif_lantern_run_%03d", t - 8));
            if (t == 52) release();
            return t > 54;
        });
        add(t -> {
            if (t == 0) {
                give("air");
                cmd("tp @s 0 -60 22 180 0");
                mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
            }
            hold(0f, 10f);
            if (t == 4) Emotes.play(Emote.DANCE);
            if (t >= 10 && t < 50) shot(String.format("gif_dance_%03d", t - 10));
            if (t == 50) {
                Emotes.stop();
                mc.options.setCameraType(CameraType.FIRST_PERSON);
                release();
            }
            return t > 52;
        });
        add(t -> {
            if (t == 0) {
                give("air");
                cmd("tp @s -6 -61 23 0 5");
                Activities.testActivity = "swim";
            }
            hold(0f, 5f);
            if (t >= 10 && t < 46) shot(String.format("gif_swim_%03d", t - 10));
            if (t == 46) {
                Activities.testActivity = null;
                release();
            }
            return t > 48;
        });
        // the settings screen and the emote wheel (with the HUD)
        add(t -> {
            if (t == 0) {
                cmd("tp @s 0 -60 16 0 8");
                hideHud = false;
                com.lifelikemotion.config.LMConfig.FP_IDLE_SHOW.set(true);
                mc.setScreen(new com.lifelikemotion.config.LMConfigScreen(null));
            }
            if (t == 10) shot("promo_settings");
            if (t == 11) mc.setScreen(new com.lifelikemotion.client.emote.EmoteWheelScreen());
            if (t == 20) shot("promo_emote_wheel");
            if (t == 21) mc.setScreen(null);
            return t > 24;
        });
    }

    // ------------------------------------------------------------------ helpers
    interface Setup {
        void run();
    }

    static void pose(Flourishes.Move m, float u) {
        Flourish.testMove = m;
        Flourish.testTime = u;
    }

    static void swing(Clip c, float u) {
        FirstPersonAnimator.testClip = c;
        FirstPersonAnimator.testSwing = u;
    }

    static void clearPoses() {
        Flourish.testMove = null;
        FirstPersonAnimator.testClip = null;
        FirstPersonAnimator.testSwing = null;
    }

    static void hold(Float yaw, Float pitch) {
        ClientSmoke.yaw = yaw;
        ClientSmoke.pitch = pitch;
    }

    static void release() {
        ClientSmoke.yaw = 0f;
        ClientSmoke.pitch = 8f;
    }

    static void still(String name, String item, Setup setup, float pitch) {
        Minecraft mc = Minecraft.getInstance();
        add(t -> {
            if (t == 0) {
                mc.options.setCameraType(CameraType.FIRST_PERSON);
                give(item);
            }
            hold(0f, pitch);
            if (t == 14) setup.run();
            if (t == 18) shot(name);
            if (t == 19) {
                clearPoses();
                release();
            }
            return t > 20;
        });
    }

    static void gifPose(String name, String item, Flourishes.Move m, int frames) {
        add(t -> {
            if (t == 0) give(item);
            hold(0f, 8f);
            int i = (t - 12) / 2;
            if (t >= 12 && t % 2 == 0 && i < frames) pose(m, i / (float) (frames - 1));
            if (t >= 13 && t % 2 == 1 && i < frames) shot(String.format("gif_%s_%03d", name, i));
            if (t == 12 + frames * 2) clearPoses();
            return t > 14 + frames * 2;
        });
    }

    static void gifSwings(String name, String item, Clip[] clips, int framesEach) {
        int frames = clips.length * framesEach + 4;
        add(t -> {
            if (t == 0) give(item);
            hold(0f, 8f);
            int i = (t - 12) / 2;
            if (t >= 12 && t % 2 == 0 && i < frames) {
                int c = i / framesEach;
                if (c < clips.length) swing(clips[c], (i % framesEach + 1) / (float) framesEach);
                else clearPoses();
            }
            if (t >= 13 && t % 2 == 1 && i < frames) shot(String.format("gif_%s_%03d", name, i));
            if (t == 12 + frames * 2) clearPoses();
            return t > 14 + frames * 2;
        });
    }
}
