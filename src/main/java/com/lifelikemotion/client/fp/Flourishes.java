package com.lifelikemotion.client.fp;

/**
 * Show-off moves for standing still (and the inspect key), as keyframes about the hand: time, x, y, z, pitch, yaw,
 * roll (see {@link Clip}). Spins go past 360° and simply end there (it looks the same as 0).
 */
public final class Flourishes {
    private Flourishes() {}

    public record Move(String name, Clip clip, int ticks) {}

    // ---------------------------------------------------------------- swords
    /** brought up in front, spun round like a propeller, then laid flat and run along the blade, twice */
    public static final Move SWORD_TWIRL_WIPE = new Move("sword_twirl_wipe", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.10f, -0.20f, 0.20f, -0.04f, -8, 8, 0,
            0.16f, -0.22f, 0.24f, -0.05f, -8, 8, 80,
            0.23f, -0.22f, 0.24f, -0.05f, -8, 8, 200,
            0.30f, -0.22f, 0.24f, -0.05f, -8, 8, 320,
            0.35f, -0.22f, 0.22f, -0.05f, -8, 8, 360,
            0.44f, -0.22f, 0.10f, -0.04f, 0, 22, 430,
            0.54f, -0.12f, 0.10f, -0.04f, 0, 22, 430,
            0.64f, -0.30f, 0.10f, -0.04f, 0, 22, 430,
            0.74f, -0.14f, 0.10f, -0.04f, 0, 22, 430,
            0.82f, -0.18f, 0.10f, -0.04f, -4, 14, 410,
            1.00f, 0, 0, 0, 0, 0, 360), 90);
    /** tossed up end over end and caught */
    public static final Move SWORD_FLIP = new Move("sword_flip", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.16f, 0, -0.05f, 0, 10, 0, 0,
            0.30f, -0.05f, 0.20f, -0.03f, -100, 0, 0,
            0.42f, -0.06f, 0.30f, -0.04f, -230, 0, 0,
            0.56f, -0.04f, 0.16f, -0.02f, -340, 0, 0,
            0.64f, 0, -0.06f, 0.01f, -360, 0, 0,
            0.76f, 0, 0.01f, 0, -362, 0, 0,
            1.00f, 0, 0, 0, -360, 0, 0), 46);

    // ---------------------------------------------------------------- axes, pickaxes, hoes, shovels, rods
    /** flipped up in the air and caught with a dip */
    public static final Move TOOL_TOSS = new Move("tool_toss", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.18f, 0, -0.05f, 0, 10, 0, 0,
            0.34f, -0.04f, 0.22f, -0.02f, -120, 0, 0,
            0.48f, -0.05f, 0.30f, -0.03f, -240, 0, 0,
            0.62f, -0.03f, 0.10f, -0.01f, -345, 0, 0,
            0.70f, 0, -0.07f, 0.01f, -362, 0, 0,
            0.82f, 0, 0.01f, 0, -358, 0, 0,
            1.00f, 0, 0, 0, -360, 0, 0), 44);
    /** up onto the shoulder, two taps, back down */
    public static final Move TOOL_SHOULDER = new Move("tool_shoulder", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.22f, -0.04f, 0.14f, 0.02f, -70, 0, -25,
            0.34f, -0.04f, 0.11f, 0.02f, -62, 0, -25,
            0.42f, -0.04f, 0.14f, 0.02f, -70, 0, -25,
            0.52f, -0.04f, 0.11f, 0.02f, -62, 0, -25,
            0.60f, -0.04f, 0.14f, 0.02f, -70, 0, -25,
            0.80f, -0.04f, 0.14f, 0.02f, -70, 0, -25,
            1.00f, 0, 0, 0, 0, 0, 0), 60);
    /** spun round in front like a propeller */
    public static final Move TOOL_TWIRL = new Move("tool_twirl", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.15f, -0.18f, 0.18f, -0.03f, -6, 6, 0,
            0.30f, -0.20f, 0.22f, -0.03f, -6, 6, 140,
            0.45f, -0.20f, 0.22f, -0.03f, -6, 6, 290,
            0.56f, -0.20f, 0.20f, -0.03f, -6, 6, 365,
            0.66f, -0.16f, 0.15f, -0.03f, -6, 6, 358,
            1.00f, 0, 0, 0, 0, 0, 360), 44);
    /** a shovel turned round on its handle */
    public static final Move SHOVEL_SPIN = new Move("shovel_spin", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.16f, -0.08f, 0.06f, -0.02f, -6, 0, 0,
            0.34f, -0.08f, 0.07f, -0.02f, -6, 160, 0,
            0.52f, -0.08f, 0.07f, -0.02f, -6, 330, 0,
            0.62f, -0.08f, 0.07f, -0.02f, -6, 365, 0,
            0.72f, -0.07f, 0.06f, -0.02f, -6, 358, 0,
            1.00f, 0, 0, 0, 0, 360, 0), 42);
    /** a fishing rod given a couple of test flicks */
    public static final Move ROD_FLICK = new Move("rod_flick", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.20f, 0, 0.05f, 0.02f, -24, 0, 0,
            0.30f, 0, -0.02f, -0.03f, 16, 0, 0,
            0.42f, 0, 0.03f, 0.01f, -14, 0, 0,
            0.52f, 0, -0.01f, -0.02f, 9, 0, 0,
            0.64f, 0, 0.01f, 0, -3, 0, 0,
            1.00f, 0, 0, 0, 0, 0, 0), 40);

    // ---------------------------------------------------------------- blocks, food, small things
    /** tossed up spinning and caught */
    public static final Move SMALL_TOSS = new Move("small_toss", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.18f, 0, -0.04f, 0, 6, 0, 0,
            0.36f, -0.03f, 0.20f, -0.02f, -50, 150, 0,
            0.50f, -0.04f, 0.26f, -0.02f, -90, 260, 0,
            0.64f, -0.02f, 0.06f, 0, -130, 350, 0,
            0.72f, 0, -0.05f, 0.01f, -180, 360, 0,
            0.84f, 0, 0.01f, 0, -180, 362, 0,
            1.00f, 0, 0, 0, -180, 360, 0), 40);
    /** brought up close and turned over to look at, one side then the other */
    public static final Move TURN_OVER = new Move("turn_over", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.20f, -0.22f, 0.14f, 0.06f, -12, 55, 0,
            0.42f, -0.22f, 0.14f, 0.06f, -12, 70, 0,
            0.58f, -0.23f, 0.15f, 0.06f, 20, -40, 10,
            0.78f, -0.22f, 0.15f, 0.06f, 18, -48, 10,
            1.00f, 0, 0, 0, 0, 0, 0), 64);
    /** two quick tosses from hand to hand height, juggling */
    public static final Move JUGGLE = new Move("juggle", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.12f, 0, -0.03f, 0, 5, 0, 0,
            0.25f, -0.06f, 0.16f, -0.02f, -60, 0, 60,
            0.38f, -0.10f, -0.02f, 0, -120, 0, 120,
            0.50f, -0.10f, -0.03f, 0, -120, 0, 120,
            0.63f, -0.04f, 0.18f, -0.02f, -240, 0, 240,
            0.78f, 0, -0.03f, 0, -360, 0, 360,
            1.00f, 0, 0, 0, -360, 0, 360), 52);
    /** a lantern or torch lifted up high and swung gently, as if looking around in the dark */
    public static final Move LIGHT_RAISE = new Move("light_raise", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.22f, -0.18f, 0.34f, -0.10f, -14, 10, 0,
            0.38f, -0.16f, 0.35f, -0.10f, -14, 10, 18,
            0.54f, -0.20f, 0.35f, -0.10f, -14, 10, -16,
            0.68f, -0.18f, 0.34f, -0.10f, -14, 10, 7,
            0.80f, -0.14f, 0.24f, -0.08f, -10, 7, 0,
            1.00f, 0, 0, 0, 0, 0, 0), 70);

    // ---------------------------------------------------------------- an empty hand
    /** the hand comes up, the wrist turned one way and the other, fingers flexed */
    public static final Move HAND_FLEX = new Move("hand_flex", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.20f, -0.18f, 0.32f, -0.06f, -30, 18, 0,
            0.34f, -0.18f, 0.33f, -0.06f, -30, 18, -40,
            0.50f, -0.18f, 0.33f, -0.06f, -30, 18, 30,
            0.64f, -0.18f, 0.32f, -0.06f, -30, 18, -20,
            0.80f, -0.14f, 0.24f, -0.05f, -22, 14, 0,
            1.00f, 0, 0, 0, 0, 0, 0), 56);
    /** a fist brought up and shaken out, knuckles cracked */
    public static final Move HAND_CRACK = new Move("hand_crack", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.18f, -0.16f, 0.30f, -0.05f, -38, 14, 10,
            0.26f, -0.16f, 0.31f, -0.05f, -26, 14, 0,
            0.32f, -0.16f, 0.29f, -0.05f, -42, 14, 12,
            0.38f, -0.16f, 0.31f, -0.05f, -26, 14, 0,
            0.46f, -0.16f, 0.29f, -0.05f, -42, 14, 12,
            0.58f, -0.10f, 0.16f, -0.03f, -16, 8, -14,
            0.68f, -0.04f, 0.04f, 0, -4, 2, 10,
            0.78f, -0.03f, 0.03f, 0, -2, 0, -5,
            1.00f, 0, 0, 0, 0, 0, 0), 48);

    // ---------------------------------------------------------------- bows, shields, tridents
    /** a bow tilted over and its string plucked */
    public static final Move BOW_PLUCK = new Move("bow_pluck", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.24f, -0.14f, 0.12f, 0, 0, 0, -36,
            0.40f, -0.14f, 0.12f, 0, 0, 0, -36,
            0.44f, -0.07f, 0.06f, 0, 0, 0, -36,
            0.48f, -0.09f, 0.06f, 0, 0, 0, -33,
            0.52f, -0.075f, 0.06f, 0, 0, 0, -35,
            0.56f, -0.085f, 0.06f, 0, 0, 0, -34,
            0.76f, -0.06f, 0.04f, 0, 0, 0, -20,
            1.00f, 0, 0, 0, 0, 0, 0), 52);
    /** a shield braced up in front, then lowered */
    public static final Move SHIELD_BRACE = new Move("shield_brace", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.20f, -0.10f, 0.08f, -0.06f, -6, 18, 0,
            0.30f, -0.10f, 0.06f, -0.10f, -6, 18, 0,
            0.36f, -0.10f, 0.08f, -0.06f, -6, 18, 0,
            0.70f, -0.10f, 0.08f, -0.06f, -6, 18, 0,
            1.00f, 0, 0, 0, 0, 0, 0), 46);
    /** a trident spun twice */
    public static final Move TRIDENT_SPIN = new Move("trident_spin", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.14f, -0.12f, 0.08f, -0.03f, -6, 6, 0,
            0.30f, -0.14f, 0.09f, -0.03f, -6, 6, 240,
            0.48f, -0.14f, 0.09f, -0.03f, -6, 6, 520,
            0.58f, -0.14f, 0.09f, -0.03f, -6, 6, 725,
            0.68f, -0.12f, 0.08f, -0.03f, -6, 6, 718,
            1.00f, 0, 0, 0, 0, 0, 720), 50);

    public static final Move[] ALL = {SWORD_TWIRL_WIPE, SWORD_FLIP, TOOL_TOSS, TOOL_SHOULDER, TOOL_TWIRL, SHOVEL_SPIN, ROD_FLICK,
            SMALL_TOSS, TURN_OVER, JUGGLE, LIGHT_RAISE, HAND_FLEX, HAND_CRACK, BOW_PLUCK, SHIELD_BRACE, TRIDENT_SPIN};
}
