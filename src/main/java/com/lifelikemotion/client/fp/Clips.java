package com.lifelikemotion.client.fp;

/**
 * Every first-person swing, as keyframes: time, x, y, z, pitch, yaw, roll (see {@link Clip}).
 * x + toward the hand's side, y + up, z + toward the camera; pitch + tips forward/down, yaw + turns in across the
 * screen, roll + leans in toward the middle. Each starts and ends at rest.
 */
public final class Clips {
    private Clips() {}

    /** sword, forehand: cocked up and back over the shoulder, cut down across the screen, blade carried on
     *  past and laid over, then a little bounce back to rest */
    public static final Clip SLASH_A = Clip.of(
            0.0f, 0, 0, 0, 0, 0, 0,
            0.16f, 0.08f, 0.17f, 0.05f, -10, 6, -28,
            0.3f, -0.05f, 0.1f, -0.04f, 0, -6, 15,
            0.42f, -0.45f, -0.06f, -0.08f, 10, -16, 62,
            0.52f, -0.62f, -0.12f, -0.06f, 12, -20, 80,
            0.62f, -0.66f, -0.14f, -0.04f, 12, -20, 84,
            0.8f, -0.25f, -0.05f, 0, 4, -8, 30,
            0.92f, 0.03f, 0.01f, 0, -1, 1, -4,
            1.0f, 0, 0, 0, 0, 0, 0);

    /** sword, backhand: wound low across the body, whipped back out and up to the sword side, a bounce back */
    public static final Clip SLASH_B = Clip.of(
            0.0f, 0, 0, 0, 0, 0, 0,
            0.18f, -0.40f, 0.04f, -0.06f, 4, -14, 72,
            0.30f, -0.30f, 0.06f, -0.08f, 2, -8, 46,
            0.42f, 0.04f, 0.14f, -0.08f, -6, 6, -20,
            0.52f, 0.16f, 0.20f, -0.05f, -10, 10, -44,
            0.62f, 0.18f, 0.21f, -0.03f, -11, 10, -48,
            0.80f, 0.05f, 0.05f, 0, -3, 2, -10,
            0.92f, -0.01f, -0.01f, 0, 1, 0, 3,
            1.0f, 0, 0, 0, 0, 0, 0);

    /** sword, third in the combo: drawn back toward you, then thrust straight at the crosshair, held, pulled back */
    public static final Clip STAB = Clip.of(
            0.0f, 0, 0, 0, 0, 0, 0,
            0.22f, 0.06f, -0.02f, 0.1f, -10, 4, 6,
            0.4f, -0.3f, 0.1f, -0.3f, 55, 4, 10,
            0.56f, -0.3f, 0.1f, -0.27f, 52, 4, 10,
            0.8f, 0.02f, 0, 0.03f, -3, 0, 0,
            1.0f, 0, 0, 0, 0, 0, 0);

    /** axe: heaved up high, hangs a beat, brought down hard, bounces off what it hit, settles */
    public static final Clip CHOP = Clip.of(
            0.0f, 0, 0, 0, 0, 0, 0,
            0.24f, -0.08f, 0.3f, 0.06f, -40, 4, -6,
            0.36f, -0.08f, 0.32f, 0.06f, -45, 4, -6,
            0.5f, -0.18f, -0.14f, -0.16f, 50, -6, 8,
            0.57f, -0.18f, -0.1f, -0.15f, 42, -6, 8,
            0.64f, -0.18f, -0.13f, -0.16f, 47, -6, 8,
            0.86f, 0.01f, 0.01f, 0, -3, 0, 0,
            1.0f, 0, 0, 0, 0, 0, 0);

    /** pickaxe digging (a loop while the block breaks): a lift, a sharp strike into the block, a jolt, back */
    public static final Clip MINE = Clip.of(
            0.0f, 0, 0, 0, 0, 0, 0,
            0.32f, -0.02f, 0.14f, 0.03f, -30, 2, -4,
            0.56f, -0.12f, -0.06f, -0.18f, 40, -6, 6,
            0.64f, -0.12f, -0.04f, -0.17f, 34, -6, 6,
            0.72f, -0.12f, -0.05f, -0.18f, 37, -6, 6,
            1.0f, 0, 0, 0, 0, 0, 0);

    /** shovel: pulled back, driven in and down, scooped up and tipped, back */
    public static final Clip DIG = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.22f, 0.02f, 0.02f, 0.06f, -12, 0, -4,
            0.46f, -0.06f, -0.09f, -0.26f, 20, -4, 4,
            0.66f, -0.06f, 0.08f, -0.18f, -32, -4, 4,
            0.86f, 0, 0.01f, 0, -2, 0, 0,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** hoe: raised, then pulled down and back toward you */
    public static final Clip TILL = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.26f, 0, 0.16f, -0.06f, -36, 0, -4,
            0.52f, -0.04f, -0.06f, 0.08f, 26, -4, 2,
            0.62f, -0.04f, -0.04f, 0.07f, 22, -4, 2,
            1.00f, 0, 0, 0, 0, 0, 0);

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

    /** hitting with anything else (food, a torch, a block): a swat across */
    public static final Clip SWAT = Clip.of(
            0.0f, 0, 0, 0, 0, 0, 0,
            0.18f, 0.06f, 0.1f, 0.04f, -14, 6, -14,
            0.42f, -0.3f, -0.06f, -0.16f, 16, -14, 40,
            0.54f, -0.34f, -0.08f, -0.14f, 18, -15, 44,
            0.84f, 0.01f, 0, 0, -2, 0, 0,
            1.0f, 0, 0, 0, 0, 0, 0);


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

    /** how long each plays, in ticks (the game's own swing is 6: ours take their time) */
    public static int ticks(Clip c) {
        if (c == SLASH_A || c == SLASH_B || c == STAB) return 10;
        if (c == CHOP) return 13;
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

    public static final Clip[] ALL = {SLASH_A, SLASH_B, STAB, CHOP, MINE, DIG, TILL, PUNCH, PLACE, THROW, SWAT,
            POUR, SCOOP, STRIKE, SNIP, SPRINKLE, STRIP, FLATTEN, CAST, REEL, OPEN, PRESS, PULL, TOSS};
    public static final String[] NAMES = {"slash_a", "slash_b", "stab", "chop", "mine", "dig", "till", "punch", "place", "throw", "swat",
            "pour", "scoop", "strike", "snip", "sprinkle", "strip", "flatten", "cast", "reel", "open", "press", "pull", "toss"};
}
