package com.lifelikemotion.client.fp;

/**
 * Every first-person swing, as keyframes: time, x, y, z, pitch, yaw, roll (see {@link Clip}).
 * x + toward the hand's side, y + up, z + toward the camera; pitch + tips forward/down, yaw + turns in across the
 * screen, roll + leans in toward the middle. Each starts and ends at rest.
 */
public final class Clips {
    private Clips() {}

    /** sword, first of the combo: a flat swipe right to left across the screen, the blade laid over and pointing the way it goes */
    public static final Clip SLASH_A = Clip.arm(
            0.00f, 0, 0, 0, 0, 0, 0, 0,
            0.18f, -4, 2, -24, 62, 20, 0, -0.01f,
            0.28f, -5, 2, -26, 64, 20, 0, -0.01f,
            0.40f, 6, 0, 14, 68, 22, 0.06f, 0.02f,
            0.50f, 12, -2, 38, 72, 22, 0.06f, 0.05f,
            0.60f, 14, -2, 42, 74, 22, 0.05f, 0.05f,
            0.82f, -2, 0, -3, -2, -1, 0, 0,
            1.00f, 0, 0, 0, 0, 0, 0, 0);

    /** sword, second of the combo: flipped round so the blade points right, swiped back left to right */
    public static final Clip SLASH_B = Clip.arm(
            0.00f, 0, 0, 0, 0, 0, 0, 0,
            0.18f, 30, -10, 20, -110, 60, 0.06f, 0.16f,
            0.28f, 31, -10, 22, -110, 60, 0.06f, 0.16f,
            0.40f, 14, -10, 2, -94, 46, 0.08f, 0.13f,
            0.50f, -2, -10, -14, -80, 32, 0.08f, 0.11f,
            0.60f, -5, -10, -18, -76, 28, 0.07f, 0.1f,
            0.82f, 2, 0, 3, -4, 1, 0, 0,
            1.00f, 0, 0, 0, 0, 0, 0, 0);

    /** sword, third of the combo: drawn back, then thrust straight at the crosshair, held, pulled back */
    public static final Clip STAB = Clip.arm(
            0.00f, 0, 0, 0, 0, 0, 0, 0,
            0.22f, 4, 8, 0, 8, -10, -0.10f, 0.02f,
            0.40f, 14, -6, 0, 10, 22, 0.34f, 0.06f,
            0.56f, 14, -5, 0, 10, 20, 0.31f, 0.06f,
            0.82f, -1, 0, 0, 0, -1, -0.01f, 0,
            1.00f, 0, 0, 0, 0, 0, 0, 0);

    /** an axe at work (a loop while the wood breaks): heaved up to the right, brought down and across into the trunk */
    public static final Clip CHOP = Clip.arm(
            0f, 0f, 0f, 0f, 0f, 0f, 0f, 0f,
            0.3f, 0f, 0f, 0f, -24f, 18f, 0f, 0.06f,
            0.4f, 0f, 0f, 0f, -25f, 19f, 0f, 0.065f,
            0.56f, 4f, -2f, 14f, 6f, -24f, 0.24f, -0.03f,
            0.64f, 4f, -2f, 14f, 6f, -21f, 0.23f, -0.02f,
            0.72f, 4f, -2f, 14f, 6f, -23f, 0.23f, -0.025f,
            1f, 0f, 0f, 0f, 0f, 0f, 0f, 0f);

    /** a pickaxe at work (a loop while the block breaks): raised up high, swung down into the block, a jolt as it bites */
    public static final Clip MINE = Clip.arm(
            0f, 0f, 0f, 0f, 0f, 0f, 0f, 0f,
            0.34f, 0f, 0f, 0f, -12f, 14f, 0f, 0.05f,
            0.42f, 0f, 0f, 0f, -12f, 15f, 0f, 0.055f,
            0.58f, 2f, -2f, 12f, -2f, -22f, 0.22f, -0.03f,
            0.66f, 2f, -2f, 12f, -2f, -19f, 0.21f, -0.02f,
            0.74f, 2f, -2f, 12f, -2f, -21f, 0.21f, -0.025f,
            1f, 0f, 0f, 0f, 0f, 0f, 0f, 0f);

    /** a shovel at work: lifted, driven down into the ground, levered up with its load */
    public static final Clip DIG = Clip.arm(
            0f, 0f, 0f, 0f, 0f, 0f, 0f, 0f,
            0.26f, 0f, 2f, 4f, -6f, 16f, -0.06f, 0.06f,
            0.46f, 4f, -8f, 16f, 0f, -36f, 0.3f, -0.06f,
            0.58f, 4f, -8f, 16f, 0f, -33f, 0.29f, -0.055f,
            0.78f, 0f, 2f, 6f, 0f, 14f, 0.06f, 0.06f,
            1f, 0f, 0f, 0f, 0f, 0f, 0f, 0f);

    /** a hoe at work: raised, struck down into the ground, pulled back toward you */
    public static final Clip TILL = Clip.arm(
            0f, 0f, 0f, 0f, 0f, 0f, 0f, 0f,
            0.26f, 0f, 0f, 0f, -8f, 18f, 0f, 0.04f,
            0.46f, 2f, -5f, 12f, 2f, -28f, 0.2f, -0.1f,
            0.64f, 1f, -3f, 8f, 2f, -10f, 0.02f, -0.1f,
            0.86f, 0f, 0f, 0f, 0f, 1f, 0f, 0f,
            1f, 0f, 0f, 0f, 0f, 0f, 0f, 0f);

    /** empty hand: a short cock back, a snappy jab at the crosshair, a beat, back */
    public static final Clip PUNCH = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.14f, 0.04f, -0.04f, 0.08f, 4, -4, 0,
            0.32f, -0.24f, 0.12f, -0.46f, -8, 16, 0,
            0.46f, -0.22f, 0.11f, -0.42f, -7, 14, 0,
            0.76f, 0.01f, 0, 0.03f, 0, 0, 0,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** putting a block down / using something: pushed firmly forward, a squash, back with a little bounce */
    public static final Clip PLACE = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.34f, -0.07f, 0.04f, -0.22f, 18, -8, 0,
            0.46f, -0.07f, 0.03f, -0.20f, 14, -8, 0,
            0.74f, 0.01f, 0, 0.03f, -3, 0, 0,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** snowballs, eggs, pearls: wound right back over the shoulder, whipped forward, the arm following through
     *  down and across, back */
    public static final Clip THROW = Clip.of(
            0.0f, 0, 0, 0, 0, 0, 0,
            0.26f, 0.12f, 0.26f, 0.2f, -55, 10, -12,
            0.42f, -0.2f, 0.16f, -0.3f, 30, -10, 6,
            0.56f, -0.45f, -0.22f, -0.18f, 60, -25, 20,
            0.8f, -0.08f, -0.05f, 0, 10, -4, 4,
            1.0f, 0, 0, 0, 0, 0, 0);

    /** hitting or breaking with anything else (a block, food, a torch): a small strike down */
    public static final Clip SWAT = Clip.arm(
            0f, 0f, 0f, 0f, 0f, 0f, 0f, 0f,
            0.24f, 0f, 0f, 0f, -8f, 10f, 0f, 0.03f,
            0.46f, 1f, -2f, 0f, 2f, -20f, 0.04f, -0.1f,
            0.56f, 1f, -2f, 0f, 2f, -22f, 0.04f, -0.11f,
            0.84f, 0f, 0f, 0f, 0f, 1f, 0f, 0f,
            1f, 0f, 0f, 0f, 0f, 0f, 0f, 0f);


    // ---------------------------------------------------------------- using things
    /** a full bucket: held out and tipped right over, then righted */
    public static final Clip POUR = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.20f, -0.04f, 0.04f, -0.10f, 10, 6, 0,
            0.42f, -0.06f, 0.02f, -0.14f, 75, 10, -10,
            0.60f, -0.06f, 0.02f, -0.14f, 80, 10, -12,
            1.00f, 0, 0, 0, 0, 0, 0);
    /** an empty bucket: dipped down and forward, scooped up */
    public static final Clip SCOOP = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.25f, -0.03f, -0.10f, -0.14f, 40, 0, 0,
            0.45f, -0.03f, -0.06f, -0.18f, 50, 0, 0,
            0.65f, -0.02f, 0.06f, -0.06f, -20, 0, 0,
            1.00f, 0, 0, 0, 0, 0, 0);
    /** flint and steel: two quick strikes */
    public static final Clip STRIKE = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.15f, -0.08f, 0.07f, -0.10f, -16, 10, 0,
            0.28f, -0.09f, -0.01f, -0.14f, 32, 10, 0,
            0.40f, -0.08f, 0.07f, -0.10f, -16, 10, 0,
            0.52f, -0.09f, -0.01f, -0.14f, 32, 10, 0,
            1.00f, 0, 0, 0, 0, 0, 0);
    /** shears: pushed in, two quick snips */
    public static final Clip SNIP = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.20f, -0.06f, 0.02f, -0.16f, 8, 8, 0,
            0.30f, -0.06f, 0.02f, -0.16f, 8, 8, 28,
            0.40f, -0.06f, 0.02f, -0.16f, 8, 8, -8,
            0.50f, -0.06f, 0.02f, -0.16f, 8, 8, 28,
            0.60f, -0.06f, 0.02f, -0.16f, 8, 8, -4,
            1.00f, 0, 0, 0, 0, 0, 0);
    /** bone meal and seeds: held out over the spot and shaken out */
    public static final Clip SPRINKLE = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.20f, -0.08f, 0.04f, -0.16f, 40, 10, 0,
            0.30f, -0.04f, 0.07f, -0.16f, 52, 10, 22,
            0.40f, -0.12f, 0.04f, -0.16f, 44, 10, -22,
            0.50f, -0.04f, 0.07f, -0.16f, 52, 10, 22,
            0.60f, -0.10f, 0.04f, -0.16f, 44, 10, -14,
            1.00f, 0, 0, 0, 0, 0, 0);
    /** an axe drawn along a log, shaving the bark off */
    public static final Clip STRIP = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.20f, 0.04f, 0.06f, -0.06f, 10, -16, -6,
            0.50f, -0.16f, -0.02f, -0.14f, 22, 20, 10,
            0.62f, -0.17f, -0.03f, -0.14f, 24, 22, 10,
            1.00f, 0, 0, 0, 0, 0, 0);
    /** a shovel pressed flat into the ground */
    public static final Clip FLATTEN = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.22f, -0.02f, 0.06f, -0.04f, -12, 0, 0,
            0.45f, -0.04f, -0.03f, -0.14f, 28, 0, 0,
            0.58f, -0.04f, -0.02f, -0.14f, 26, 0, 0,
            1.00f, 0, 0, 0, 0, 0, 0);
    /** a fishing rod: drawn back over the shoulder, whipped forward */
    public static final Clip CAST = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.25f, 0.04f, 0.10f, 0.08f, -50, -6, -8,
            0.45f, -0.04f, 0.02f, -0.12f, 34, 6, 4,
            0.58f, -0.04f, 0.00f, -0.12f, 30, 6, 4,
            1.00f, 0, 0, 0, 0, 0, 0);
    /** a fishing rod: yanked up and back to pull the line in */
    public static final Clip REEL = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.20f, 0, -0.03f, -0.04f, 12, 0, 0,
            0.42f, 0.03f, 0.10f, 0.08f, -40, -4, -6,
            0.60f, 0.03f, 0.09f, 0.07f, -36, -4, -6,
            1.00f, 0, 0, 0, 0, 0, 0);

    // ---------------------------------------------------------------- working the world
    /** a chest, door or gate: reach out, take hold, pull it open */
    public static final Clip OPEN = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.30f, -0.22f, 0.18f, -0.42f, -16, 24, 20,
            0.42f, -0.22f, 0.18f, -0.42f, -16, 24, 34,
            0.65f, -0.04f, 0.06f, -0.06f, 4, 8, 10,
            1.00f, 0, 0, 0, 0, 0, 0);
    /** a button: one finger out, a firm poke */
    public static final Clip PRESS = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.25f, -0.24f, 0.20f, -0.30f, -10, 16, 0,
            0.38f, -0.26f, 0.20f, -0.48f, -10, 16, 0,
            0.50f, -0.24f, 0.20f, -0.34f, -10, 16, 0,
            1.00f, 0, 0, 0, 0, 0, 0);
    /** a lever: reach, grip, pull it down toward you */
    public static final Clip PULL = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.25f, -0.22f, 0.26f, -0.40f, -20, 16, 0,
            0.50f, -0.12f, -0.02f, -0.12f, 20, 12, 0,
            0.62f, -0.12f, -0.03f, -0.11f, 22, 12, 0,
            1.00f, 0, 0, 0, 0, 0, 0);
    /** dropping something: a little toss forward */
    public static final Clip TOSS = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.20f, 0.02f, -0.04f, 0.04f, 10, 0, 0,
            0.42f, -0.06f, 0.10f, -0.20f, -26, 10, 0,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** an axe used as a weapon: a heavy overhead blow, slower than a sword's */
    public static final Clip AXE_HIT = Clip.arm(
            0f, 0f, 0f, 0f, 0f, 0f, 0f, 0f,
            0.28f, 0f, 0f, 0f, -24f, 12f, 0f, 0.06f,
            0.38f, 0f, 0f, 0f, -25f, 13f, 0f, 0.065f,
            0.52f, 1f, -4f, 0f, 0f, -34f, 0.07f, -0.17f,
            0.62f, 1f, -4f, 0f, 0f, -37f, 0.07f, -0.19f,
            0.84f, 0f, 0f, 0f, 0f, 2f, 0f, 0.01f,
            1f, 0f, 0f, 0f, 0f, 0f, 0f, 0f);

    /** a sword cutting through blocks (cobwebs, bamboo, leaves): quick small cuts down and across */
    public static final Clip HACK = Clip.arm(
            0f, 0f, 0f, 0f, 0f, 0f, 0f, 0f,
            0.3f, 0f, 0f, 0f, -20f, 4f, 0f, 0.02f,
            0.52f, 3f, -2f, 0f, 18f, -14f, 0.03f, -0.1f,
            0.62f, 3f, -2f, 0f, 20f, -16f, 0.03f, -0.11f,
            1f, 0f, 0f, 0f, 0f, 0f, 0f, 0f);

    /** how long each plays, in ticks (the game's own swing is 6: ours take their time) */
    public static int ticks(Clip c) {
        if (c == SLASH_A || c == SLASH_B) return 11;
        if (c == STAB) return 10;
        if (c == AXE_HIT) return 12;
        if (c == CHOP) return 10;
        if (c == HACK) return 7;
        if (c == MINE) return 7;
        if (c == DIG || c == TILL || c == THROW) return 11;
        if (c == PUNCH) return 8;
        if (c == PLACE) return 7;
        if (c == SWAT) return 9;
        if (c == POUR) return 18;
        if (c == SCOOP || c == SPRINKLE || c == STRIP || c == CAST) return 14;
        if (c == TOSS || c == PRESS) return 10;
        return 12;
    }

    public static final Clip[] ALL = {SLASH_A, SLASH_B, STAB, AXE_HIT, HACK, CHOP, MINE, DIG, TILL, PUNCH, PLACE, THROW, SWAT,
            POUR, SCOOP, STRIKE, SNIP, SPRINKLE, STRIP, FLATTEN, CAST, REEL, OPEN, PRESS, PULL, TOSS};
    public static final String[] NAMES = {"slash_a", "slash_b", "stab", "axe_hit", "hack", "chop", "mine", "dig", "till", "punch", "place", "throw", "swat",
            "pour", "scoop", "strike", "snip", "sprinkle", "strip", "flatten", "cast", "reel", "open", "press", "pull", "toss"};
}
