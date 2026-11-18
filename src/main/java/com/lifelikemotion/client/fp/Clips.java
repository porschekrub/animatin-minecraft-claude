package com.lifelikemotion.client.fp;

/**
 * Every first-person swing, as keyframes: time, x, y, z, pitch, yaw, roll (see {@link Clip}).
 * x + toward the hand's side, y + up, z + toward the camera; pitch + tips forward/down, yaw + turns in across the
 * screen, roll + leans in toward the middle. Each starts and ends at rest.
 */
public final class Clips {
    private Clips() {}

    /** sword, forehand: cocked up on the sword side, cut down and across, blade laid over, settle */
    public static final Clip SLASH_A = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.14f, 0.06f, 0.13f, 0.05f, -28, 14, 22,
            0.30f, -0.08f, 0.05f, -0.04f, -8, -5, 30,
            0.42f, -0.24f, -0.02f, -0.10f, 6, -28, 34,
            0.55f, -0.30f, -0.08f, -0.08f, 18, -36, 42,
            0.76f, -0.10f, -0.04f, -0.02f, 6, -12, 14,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** sword, backhand: wound low across the body, swept back out and up, a little overshoot */
    public static final Clip SLASH_B = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.16f, -0.28f, -0.04f, -0.07f, 10, -38, 34,
            0.32f, -0.14f, 0.02f, -0.10f, 0, -15, 10,
            0.46f, 0.03f, 0.08f, -0.08f, -14, 10, -22,
            0.60f, 0.06f, 0.10f, -0.03f, -18, 14, -28,
            0.80f, 0.02f, 0.03f, 0, -6, 4, -8,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** sword, third in the combo: drawn back, then a straight stab forward, held a beat */
    public static final Clip STAB = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.18f, 0.03f, -0.02f, 0.04f, -6, 0, 6,
            0.38f, -0.16f, 0.06f, -0.28f, 22, 10, 10,
            0.55f, -0.16f, 0.06f, -0.26f, 20, 10, 10,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** axe: heaved up, hangs at the top, brought down hard, a small bounce off the target */
    public static final Clip CHOP = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.22f, 0.02f, 0.18f, -0.02f, -14, 4, -10,
            0.30f, 0.02f, 0.19f, -0.02f, -16, 4, -10,
            0.48f, -0.06f, -0.05f, -0.15f, 38, -6, 4,
            0.56f, -0.06f, -0.03f, -0.14f, 32, -6, 4,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** pickaxe digging: a quick lift and a sharp strike into the block, again and again */
    public static final Clip MINE = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.25f, 0, 0.10f, -0.01f, -12, 0, -4,
            0.48f, -0.04f, -0.04f, -0.12f, 30, -4, 4,
            0.56f, -0.04f, -0.02f, -0.10f, 24, -4, 4,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** shovel: pulled back, pushed in, scooped up */
    public static final Clip DIG = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.22f, 0.02f, -0.02f, 0.03f, -6, 0, -4,
            0.45f, -0.05f, 0, -0.22f, 6, -4, 4,
            0.62f, -0.05f, 0.06f, -0.18f, -26, -4, 4,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** hoe: raised, then pulled down toward you */
    public static final Clip TILL = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.25f, 0, 0.12f, -0.04f, -30, 0, -4,
            0.50f, -0.03f, -0.04f, 0.06f, 22, -4, 2,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** empty hand: a short cock back, a straight jab, back */
    public static final Clip PUNCH = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.12f, 0.03f, -0.03f, 0.06f, 0, 0, 0,
            0.32f, -0.20f, 0.10f, -0.42f, -10, 14, 0,
            0.45f, -0.18f, 0.09f, -0.38f, -9, 12, 0,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** putting a block down / using something: a firm push forward */
    public static final Clip PLACE = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.35f, -0.05f, 0.04f, -0.18f, 14, -6, 0,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** snowballs, eggs, pearls: wound back over the shoulder, flung forward */
    public static final Clip THROW = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.25f, 0.05f, 0.12f, 0.14f, -40, 6, -6,
            0.50f, -0.08f, 0.08f, -0.30f, 28, -6, 4,
            1.00f, 0, 0, 0, 0, 0, 0);

    /** hitting with anything else (food, a torch, a block): a swat */
    public static final Clip SWAT = Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.15f, 0.03f, 0.06f, 0.03f, -14, 4, -4,
            0.40f, -0.08f, 0, -0.2f, 18, -10, 8,
            1.00f, 0, 0, 0, 0, 0, 0);


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

    public static final Clip[] ALL = {SLASH_A, SLASH_B, STAB, CHOP, MINE, DIG, TILL, PUNCH, PLACE, THROW, SWAT,
            POUR, SCOOP, STRIKE, SNIP, SPRINKLE, STRIP, FLATTEN, CAST, REEL, OPEN, PRESS, PULL, TOSS};
    public static final String[] NAMES = {"slash_a", "slash_b", "stab", "chop", "mine", "dig", "till", "punch", "place", "throw", "swat",
            "pour", "scoop", "strike", "snip", "sprinkle", "strip", "flatten", "cast", "reel", "open", "press", "pull", "toss"};
}
