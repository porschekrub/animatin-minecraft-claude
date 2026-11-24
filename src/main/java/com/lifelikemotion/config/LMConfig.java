package com.lifelikemotion.config;

import net.minecraftforge.common.ForgeConfigSpec;

/** Client options (also on the in-game config screen: Mods → Lifelike Motion → Config). */
public final class LMConfig {
    private LMConfig() {}

    public static final ForgeConfigSpec SPEC;

    // first person
    public static final ForgeConfigSpec.BooleanValue FP_ENABLED;
    public static final ForgeConfigSpec.BooleanValue FP_ARMS_WITH_ITEMS, FP_BOTH_HANDS, FP_TRAILS;
    public static final ForgeConfigSpec.DoubleValue FP_CAMERA;
    public static final ForgeConfigSpec.BooleanValue FP_IDLE_SHOW;
    public static final ForgeConfigSpec.BooleanValue FP_AURAS;
    public static final ForgeConfigSpec.BooleanValue FP_PHYSICS, FP_USE_ANIMS, FP_REACTIONS, FP_WORLD_ACTIONS;
    public static final ForgeConfigSpec.DoubleValue FP_SPEED;
    public static final ForgeConfigSpec.DoubleValue FP_SWAY;
    public static final ForgeConfigSpec.DoubleValue FP_BOB;
    public static final ForgeConfigSpec.DoubleValue FP_SWING;
    // body
    public static final ForgeConfigSpec.BooleanValue BODY_ENABLED;
    public static final ForgeConfigSpec.BooleanValue BODY_OTHER_PLAYERS;
    public static final ForgeConfigSpec.DoubleValue BODY_INTENSITY;
    // mobs
    public static final ForgeConfigSpec.BooleanValue MOBS_ENABLED;
    public static final ForgeConfigSpec.DoubleValue MOBS_INTENSITY;
    // 3D items
    public static final ForgeConfigSpec.BooleanValue ITEMS_3D_PACK_ADDED;

    static {
        ForgeConfigSpec.Builder b = new ForgeConfigSpec.Builder();
        b.comment("First person: your arms, what they hold and how they move").push("firstPerson");
        FP_ENABLED = b.comment("Custom first-person animations (off = the game's own)").define("enabled", true);
        FP_ARMS_WITH_ITEMS = b.comment("Show your arm holding the item").define("armHoldsItem", true);
        FP_BOTH_HANDS = b.comment("Both fists up when your hands are empty, and your free hand at the side of the screen")
                .define("bothHands", true);
        FP_TRAILS = b.comment("A trail behind your blade when you swing").define("swingTrails", true);
        FP_CAMERA = b.comment("How much the camera kicks with your swings and shakes when you hit something (0 = never)")
                .defineInRange("cameraKick", 1.0, 0.0, 2.0);
        FP_IDLE_SHOW = b.comment("Show off what you hold (twirls, tosses...) when you stand still for a moment; the inspect key (I) always works")
                .define("idleShowOff", true);
        FP_AURAS = b.comment("Sparkles, embers and enchanting glyphs around legendary and enchanted things you hold").define("auras", true);
        FP_PHYSICS = b.comment("Physics for held things: inertia, floating when falling, cloth fluttering, lanterns swinging, liquids sloshing")
                .define("physics", true);
        FP_USE_ANIMS = b.comment("Own animations for using things: pouring and scooping buckets, striking flint, shears, bone meal, casting a rod...")
                .define("useAnimations", true);
        FP_REACTIONS = b.comment("Reactions: flinching when hit, patting out fire").define("reactions", true);
        FP_WORLD_ACTIONS = b.comment("Your hands swim, climb ladders, open chests and doors, press buttons, hold reins, row, stretch, toss dropped items")
                .define("worldActions", true);
        FP_SPEED = b.comment("Speed of show-off moves and other animations (swings go faster above 100%, never slower than the game's own)")
                .defineInRange("speed", 1.0, 0.5, 2.0);
        FP_SWAY = b.comment("How much your hands lag behind when you look around and move").defineInRange("sway", 1.0, 0.0, 2.0);
        FP_BOB = b.comment("How much your hands bob when you walk, run and jump").defineInRange("bob", 1.0, 0.0, 2.0);
        FP_SWING = b.comment("How big swings, chops and punches are").defineInRange("swing", 1.0, 0.25, 2.0);
        b.pop();

        b.comment("Body: how players move in third person").push("body");
        BODY_ENABLED = b.comment("Lively body movement").define("enabled", true);
        BODY_OTHER_PLAYERS = b.comment("Also animate other players").define("otherPlayers", true);
        BODY_INTENSITY = b.comment("Strength of the body animations").defineInRange("intensity", 1.0, 0.0, 2.0);
        b.pop();

        b.comment("Mobs").push("mobs");
        MOBS_ENABLED = b.comment("Lively mob animations").define("enabled", true);
        MOBS_INTENSITY = b.comment("Strength of the mob animations").defineInRange("intensity", 1.0, 0.0, 2.0);
        b.pop();

        b.comment("3D items come as a built-in resource pack: Options → Resource Packs → \"Lifelike 3D Items\"").push("items3d");
        ITEMS_3D_PACK_ADDED = b.comment("Set once the pack has been switched on for you the first time (it is not switched on again if you turn it off)")
                .define("packAddedOnce", false);
        b.pop();
        SPEC = b.build();
    }
}
