package com.lifelikemotion.client.fp;

/**
 * Show-off moves for standing still (and the inspect key), as keyframes about the hand: time, x, y, z, pitch, yaw,
 * roll (see {@link Clip}). Spins go past 360° and simply end there (it looks the same as 0).
 */
public final class Flourishes {
    private Flourishes() {}

    /**
     * A move: the hand's keys; how long it takes; optionally the item's own keys on top of the hand's (thrown up and
     * caught: x, y, z, pitch, yaw, roll about its middle, the hand staying put); optionally your other hand on the item
     * (where along it from the grip 0 to the far end 1, how much 0..1); and sounds at points in it.
     */
    public record Move(String name, Clip clip, int ticks, Clip item, Clip off, Cue[] cues) {
        public Move(String name, Clip clip, int ticks) {
            this(name, clip, ticks, null, null, new Cue[0]);
        }
    }

    /** a sound at a point (0..1) in a move */
    public record Cue(float at, net.minecraft.sounds.SoundEvent sound, float volume, float pitch) {}

    /** laid flat across in front of you, your other hand runs along the blade to the tip, tilted to catch the light, then spun home */
    public static final Move SWORD_INSPECT = new Move("sword_inspect", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.09f, -0.12f, 0.09f, 0.05f, 6, 22, 68,
            0.13f, -0.15f, 0.105f, 0.06f, 9, 28, 84,
            0.16f, -0.14f, 0.1f, 0.06f, 8, 26, 80,
            0.42f, -0.15f, 0.11f, 0.06f, 10, 30, 82,
            0.47f, -0.16f, 0.13f, 0.07f, -4, 12, 58,
            0.5f, -0.17f, 0.14f, 0.07f, 14, 38, 88,
            0.53f, -0.17f, 0.135f, 0.07f, 11, 34, 84,
            0.62f, -0.17f, 0.14f, 0.07f, 12, 36, 86,
            0.67f, -0.18f, 0.12f, 0.06f, 4, 20, 140,
            0.71f, -0.17f, 0.1f, 0.05f, 0, 8, 230,
            0.75f, -0.16f, 0.07f, 0.04f, -2, 2, 265,
            0.79f, -0.014f, 0.03f, 0.02f, -2, 0, 340,
            0.84f, 0, -0.012f, 0, 2, 0, 364,
            0.9f, 0, 0.004f, 0, 0, 0, 359,
            1.00f, 0, 0, 0, 0, 0, 360), 84, null, Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.15f, 0.1f, 0, 0, 0, 0, 0,
            0.2f, 0.1f, 1, 0, 0, 0, 0,
            0.37f, 1, 1, 0, 0, 0, 0,
            0.42f, 1, 0, 0, 0, 0, 0,
            1.00f, 1, 0, 0, 0, 0, 0), new Cue[]{new Cue(0.12f, net.minecraft.sounds.SoundEvents.ARMOR_EQUIP_IRON, 0.5f, 1.3f), new Cue(0.21f, net.minecraft.sounds.SoundEvents.BRUSH_GENERIC, 0.6f, 1.7f), new Cue(0.46f, net.minecraft.sounds.SoundEvents.ARMOR_EQUIP_NETHERITE, 0.45f, 1.4f), new Cue(0.68f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.25f, 1.8f), new Cue(0.76f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.3f, 1.6f), new Cue(0.84f, net.minecraft.sounds.SoundEvents.ARMOR_EQUIP_IRON, 0.4f, 1.6f)});

    /** laid across in front of you, your other hand polishes the head, tilted to catch the light, then spun home */
    public static final Move TOOL_INSPECT = new Move("tool_inspect", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.09f, -0.06f, 0.09f, 0.05f, 6, 22, 64,
            0.13f, -0.09f, 0.105f, 0.06f, 9, 28, 80,
            0.16f, -0.08f, 0.1f, 0.06f, 8, 26, 76,
            0.42f, -0.09f, 0.11f, 0.06f, 10, 30, 78,
            0.47f, -0.1f, 0.13f, 0.07f, -4, 12, 54,
            0.5f, -0.11f, 0.14f, 0.07f, 14, 38, 84,
            0.53f, -0.11f, 0.135f, 0.07f, 11, 34, 80,
            0.62f, -0.11f, 0.14f, 0.07f, 12, 36, 82,
            0.67f, -0.12f, 0.12f, 0.06f, 4, 20, 136,
            0.71f, -0.11f, 0.1f, 0.05f, 0, 8, 226,
            0.75f, -0.1f, 0.07f, 0.04f, -2, 2, 265,
            0.79f, -0.008f, 0.03f, 0.02f, -2, 0, 340,
            0.84f, 0, -0.012f, 0, 2, 0, 364,
            0.9f, 0, 0.004f, 0, 0, 0, 359,
            1.00f, 0, 0, 0, 0, 0, 360), 84, null, Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.15f, 0.9f, 0, 0, 0, 0, 0,
            0.2f, 0.9f, 1, 0, 0, 0, 0,
            0.24f, 0.78f, 1, 0, 0, 0, 0,
            0.28f, 0.98f, 1, 0, 0, 0, 0,
            0.32f, 0.78f, 1, 0, 0, 0, 0,
            0.36f, 0.98f, 1, 0, 0, 0, 0,
            0.4f, 0.9f, 1, 0, 0, 0, 0,
            0.44f, 0.9f, 0, 0, 0, 0, 0,
            1.00f, 0.9f, 0, 0, 0, 0, 0), new Cue[]{new Cue(0.12f, net.minecraft.sounds.SoundEvents.ARMOR_EQUIP_IRON, 0.5f, 1.1f), new Cue(0.24f, net.minecraft.sounds.SoundEvents.BRUSH_GENERIC, 0.6f, 1.4f), new Cue(0.32f, net.minecraft.sounds.SoundEvents.BRUSH_GENERIC, 0.6f, 1.5f), new Cue(0.46f, net.minecraft.sounds.SoundEvents.ARMOR_EQUIP_IRON, 0.45f, 1), new Cue(0.68f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.25f, 1.6f), new Cue(0.76f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.3f, 1.4f), new Cue(0.84f, net.minecraft.sounds.SoundEvents.ARMOR_EQUIP_IRON, 0.4f, 1.3f)});

    /** flicked up into the air, spinning twice, caught with a dip, twirled and pointed ahead */
    public static final Move SWORD_TOSS = new Move("sword_toss", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.1f, 0, -0.07f, 0.02f, 14, 0, 0,
            0.17f, 0, 0.07f, -0.02f, -16, 0, 0,
            0.24f, 0, 0.02f, 0, -4, 0, 0,
            0.6f, 0, 0.03f, 0, -8, 0, 0,
            0.66f, 0, -0.08f, 0.02f, 16, 0, 0,
            0.72f, 0, 0.01f, 0, -4, 0, 0,
            0.76f, -0.05f, 0.03f, 0.01f, -4, 0, 120,
            0.8f, -0.08f, 0.05f, 0.02f, -5, 0, 240,
            0.84f, -0.09f, 0.05f, 0.02f, -6, 0, 360,
            0.88f, -0.1f, 0.05f, 0.02f, 12, 0, 360,
            0.92f, -0.09f, 0.05f, 0.02f, 9, 0, 360,
            1.00f, 0, 0, 0, 0, 0, 360), 72, Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.16f, 0, 0, 0, 0, 0, 0,
            0.18f, 0, 0, 0, 0, 0, 0,
            0.237f, -0.096f, 0.158f, 0.009f, 0, 0, 90,
            0.295f, -0.165f, 0.27f, 0.015f, 0, 0, 180,
            0.353f, -0.206f, 0.338f, 0.019f, 0, 0, 270,
            0.41f, -0.22f, 0.36f, 0.02f, 0, 0, 360,
            0.468f, -0.206f, 0.337f, 0.019f, 0, 0, 450,
            0.525f, -0.165f, 0.27f, 0.015f, 0, 0, 540,
            0.583f, -0.096f, 0.158f, 0.009f, 0, 0, 630,
            0.64f, 0, 0, 0, 0, 0, 720,
            0.68f, 0, 0, 0, 0, 0, 720,
            1.00f, 0, 0, 0, 0, 0, 720), null, new Cue[]{new Cue(0.17f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.3f, 1.8f), new Cue(0.34f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_NODAMAGE, 0.35f, 1.4f), new Cue(0.5f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_NODAMAGE, 0.35f, 1.6f), new Cue(0.64f, net.minecraft.sounds.SoundEvents.ARMOR_EQUIP_IRON, 0.6f, 1.2f), new Cue(0.78f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.25f, 2)});

    /** spun like a wheel in your hand, three times, brought up straight before your face in a salute, then flicked down to shake it clean */
    public static final Move SWORD_SALUTE = new Move("sword_salute", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.07f, -0.05f, 0.05f, 0.02f, -4, 0, -6,
            0.12f, -0.06f, 0.06f, 0.02f, -4, 0, -6,
            0.3f, -0.07f, 0.07f, 0.02f, -5, 0, -8,
            0.4f, -0.06f, 0.05f, 0.02f, -4, 0, -6,
            0.46f, -0.21f, 0.07f, 0.04f, 6, 0, -3,
            0.49f, -0.21f, 0.085f, 0.04f, 4, 0, -2,
            0.62f, -0.21f, 0.08f, 0.04f, 5, 0, -2,
            0.67f, 0.07f, -0.17f, 0, 22, 6, -52,
            0.71f, 0.06f, -0.15f, 0, 18, 5, -46,
            0.8f, 0.04f, -0.09f, 0, 10, 3, -30,
            0.9f, 0, 0.01f, 0, -2, 0, 1,
            1.00f, 0, 0, 0, 0, 0, 0), 80, Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.1f, 0, 0, 0, 0, 0, 0,
            0.127f, 0, 0, 0, 55.625f, 0, 0,
            0.153f, 0, 0, 0, 130, 0, 0,
            0.18f, 0, 0, 0, 219.375f, 0, 0,
            0.207f, 0, 0, 0, 320, 0, 0,
            0.233f, 0, 0, 0, 428.125f, 0, 0,
            0.26f, 0, 0, 0, 540, 0, 0,
            0.287f, 0, 0, 0, 651.875f, 0, 0,
            0.313f, 0, 0, 0, 760, 0, 0,
            0.34f, 0, 0, 0, 860.625f, 0, 0,
            0.367f, 0, 0, 0, 950, 0, 0,
            0.393f, 0, 0, 0, 1024.375f, 0, 0,
            0.42f, 0, 0, 0, 1080, 0, 0,
            1.00f, 0, 0, 0, 1080, 0, 0), null, new Cue[]{new Cue(0.14f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.2f, 2), new Cue(0.24f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.2f, 2), new Cue(0.34f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.2f, 1.9f), new Cue(0.47f, net.minecraft.sounds.SoundEvents.ARMOR_EQUIP_NETHERITE, 0.6f, 1.2f), new Cue(0.67f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.35f, 1.4f)});

    /** flipped up end over end, twice, and caught by the handle with a dip and a bounce */
    public static final Move TOOL_FLIP = new Move("tool_flip", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.1f, 0, -0.07f, 0.02f, 16, 0, 0,
            0.17f, 0, 0.07f, -0.02f, -18, 0, 0,
            0.24f, 0, 0.02f, 0, -4, 0, 0,
            0.62f, 0, 0.03f, 0, -8, 0, 0,
            0.68f, 0, -0.09f, 0.02f, 18, 0, 0,
            0.75f, 0, 0.015f, 0, -5, 0, 0,
            0.82f, 0, -0.01f, 0, 2, 0, 0,
            1.00f, 0, 0, 0, 0, 0, 0), 66, Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.16f, 0, 0, 0, 0, 0, 0,
            0.18f, 0, 0, 0, 0, 0, 0,
            0.24f, -0.079f, 0.166f, 0.009f, 90, 0, 0,
            0.3f, -0.135f, 0.285f, 0.015f, 180, 0, 0,
            0.36f, -0.169f, 0.356f, 0.019f, 270, 0, 0,
            0.42f, -0.18f, 0.38f, 0.02f, 360, 0, 0,
            0.48f, -0.169f, 0.356f, 0.019f, 450, 0, 0,
            0.54f, -0.135f, 0.285f, 0.015f, 540, 0, 0,
            0.6f, -0.079f, 0.166f, 0.009f, 630, 0, 0,
            0.66f, 0, 0, 0, 720, 0, 0,
            0.7f, 0, 0, 0, 720, 0, 0,
            1.00f, 0, 0, 0, 720, 0, 0), null, new Cue[]{new Cue(0.17f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.3f, 1.5f), new Cue(0.36f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_NODAMAGE, 0.35f, 1.2f), new Cue(0.52f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_NODAMAGE, 0.35f, 1.4f), new Cue(0.66f, net.minecraft.sounds.SoundEvents.WOOD_PLACE, 0.6f, 1.3f)});

    /** twirled round its handle three times, then raised up high in front of you, held, and brought down with a slam */
    public static final Move TOOL_SPIN_REST = new Move("tool_spin_rest", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.07f, -0.06f, 0.05f, 0.02f, -4, 0, -4,
            0.4f, -0.07f, 0.06f, 0.02f, -5, 0, -5,
            0.48f, -0.2f, 0.1f, 0.03f, 10, 0, -6,
            0.52f, -0.2f, 0.12f, 0.03f, 8, 0, -6,
            0.64f, -0.2f, 0.11f, 0.03f, 9, 0, -6,
            0.7f, -0.05f, -0.12f, 0.04f, 34, 0, -4,
            0.73f, -0.04f, -0.1f, 0.04f, 30, 0, -3,
            0.84f, -0.02f, -0.05f, 0.02f, 14, 0, -2,
            0.93f, 0, 0.01f, 0, -1, 0, 0,
            1.00f, 0, 0, 0, 0, 0, 0), 80, Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.08f, 0, 0, 0, 0, 0, 0,
            0.108f, 0, 0, 0, 0, 55.625f, 0,
            0.137f, 0, 0, 0, 0, 130, 0,
            0.165f, 0, 0, 0, 0, 219.375f, 0,
            0.193f, 0, 0, 0, 0, 320, 0,
            0.222f, 0, 0, 0, 0, 428.125f, 0,
            0.25f, 0, 0, 0, 0, 540, 0,
            0.278f, 0, 0, 0, 0, 651.875f, 0,
            0.307f, 0, 0, 0, 0, 760, 0,
            0.335f, 0, 0, 0, 0, 860.625f, 0,
            0.363f, 0, 0, 0, 0, 950, 0,
            0.392f, 0, 0, 0, 0, 1024.375f, 0,
            0.42f, 0, 0, 0, 0, 1080, 0,
            1.00f, 0, 0, 0, 0, 1080, 0), null, new Cue[]{new Cue(0.14f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.2f, 1.6f), new Cue(0.26f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.2f, 1.7f), new Cue(0.36f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP, 0.2f, 1.8f), new Cue(0.5f, net.minecraft.sounds.SoundEvents.ARMOR_EQUIP_IRON, 0.5f, 0.9f), new Cue(0.7f, net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_STRONG, 0.45f, 1)});


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


    // ---------------------------------------------------------------- one item each
    /** a compass brought up close and turned a little this way and that, finding north */
    public static final Move COMPASS_LOOK = new Move("compass_look", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.20f, -0.28f, 0.16f, 0.0f, -20, 58, 0,
            0.36f, -0.28f, 0.16f, 0.0f, -20, 50, -4,
            0.52f, -0.29f, 0.16f, 0.0f, -20, 64, 4,
            0.68f, -0.28f, 0.16f, 0.0f, -20, 57, 0,
            0.82f, -0.20f, 0.11f, 0.0f, -14, 40, 0,
            1.00f, 0, 0, 0, 0, 0, 0), 64);
    /** a book held up in front to read, pages flicked over three times */
    public static final Move BOOK_READ = new Move("book_read", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.18f, -0.30f, 0.14f, 0.02f, -14, 62, 0,
            0.34f, -0.30f, 0.14f, 0.02f, -14, 62, 0,
            0.38f, -0.30f, 0.15f, 0.02f, -14, 76, -22,
            0.43f, -0.30f, 0.14f, 0.02f, -14, 62, 0,
            0.53f, -0.30f, 0.14f, 0.02f, -14, 62, 0,
            0.57f, -0.30f, 0.15f, 0.02f, -14, 76, -22,
            0.62f, -0.30f, 0.14f, 0.02f, -14, 62, 0,
            0.70f, -0.30f, 0.14f, 0.02f, -14, 62, 0,
            0.74f, -0.30f, 0.15f, 0.02f, -14, 76, -22,
            0.79f, -0.30f, 0.14f, 0.02f, -14, 62, 0,
            1.00f, 0, 0, 0, 0, 0, 0), 90);
    /** a full bucket lifted and given a few shakes to hear it slosh */
    public static final Move BUCKET_SHAKE = new Move("bucket_shake", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.18f, -0.08f, 0.08f, 0, -6, 10, 0,
            0.26f, -0.15f, 0.10f, 0, -6, 10, -24,
            0.34f, -0.01f, 0.10f, 0, -6, 10, 24,
            0.42f, -0.15f, 0.10f, 0, -6, 10, -24,
            0.50f, -0.01f, 0.10f, 0, -6, 10, 24,
            0.58f, -0.13f, 0.09f, 0, -6, 10, -14,
            0.66f, -0.05f, 0.09f, 0, -6, 10, 7,
            0.76f, -0.08f, 0.07f, 0, -5, 8, 0,
            1.00f, 0, 0, 0, 0, 0, 0), 48);
    /** flint and steel struck twice (sparks fly from each strike) */
    public static final Move FLINT_STRIKE = new Move("flint_strike", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.22f, -0.12f, 0.08f, -0.06f, -14, 14, 0,
            0.32f, -0.14f, -0.01f, -0.10f, 34, 14, 0,
            0.40f, -0.12f, 0.09f, -0.06f, -16, 14, 0,
            0.52f, -0.14f, -0.01f, -0.10f, 34, 14, 0,
            0.60f, -0.12f, 0.08f, -0.06f, -14, 14, 0,
            0.76f, -0.10f, 0.06f, -0.04f, -8, 10, 0,
            1.00f, 0, 0, 0, 0, 0, 0), 44);
    /** the times (0..1) of the flint's strikes, for the sparks */
    public static final float[] FLINT_SPARKS = {0.32f, 0.52f};
    /** a spyglass lifted toward the eye for a look around, then lowered */
    public static final Move SPYGLASS_PEEK = new Move("spyglass_peek", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.22f, -0.30f, 0.28f, 0.16f, -8, 22, 0,
            0.38f, -0.30f, 0.28f, 0.16f, -8, 16, 0,
            0.54f, -0.30f, 0.28f, 0.16f, -8, 28, 0,
            0.70f, -0.30f, 0.28f, 0.16f, -8, 22, 0,
            0.84f, -0.20f, 0.18f, 0.10f, -6, 15, 0,
            1.00f, 0, 0, 0, 0, 0, 0), 66);
    /** a totem held up high, swaying, as if showing it off */
    public static final Move TOTEM_RAISE = new Move("totem_raise", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.20f, -0.14f, 0.40f, -0.12f, -15, 8, 0,
            0.34f, -0.14f, 0.43f, -0.12f, -15, 8, 7,
            0.48f, -0.14f, 0.41f, -0.12f, -15, 8, -7,
            0.62f, -0.14f, 0.43f, -0.12f, -15, 8, 5,
            0.76f, -0.12f, 0.36f, -0.10f, -12, 6, 0,
            1.00f, 0, 0, 0, 0, 0, 0), 64);
    /** an egg tossed high with a slow turn, caught gently, a careful wobble */
    public static final Move EGG_TOSS = new Move("egg_toss", Clip.of(
            0.00f, 0, 0, 0, 0, 0, 0,
            0.14f, 0, -0.04f, 0, 6, 0, 0,
            0.32f, -0.06f, 0.30f, -0.03f, -60, 0, 0,
            0.44f, -0.07f, 0.38f, -0.03f, -110, 0, 0,
            0.58f, -0.04f, 0.14f, -0.01f, -170, 0, 0,
            0.66f, 0, -0.06f, 0.01f, -180, 0, 0,
            0.74f, 0, -0.02f, 0, -180, 0, 9,
            0.82f, 0, -0.02f, 0, -180, 0, -7,
            0.90f, 0, 0, 0, -180, 0, 3,
            1.00f, 0, 0, 0, -180, 0, 0), 54);

    public static final Move[] ALL = {SWORD_INSPECT, SWORD_TOSS, SWORD_SALUTE, TOOL_INSPECT, TOOL_FLIP, TOOL_SPIN_REST, SWORD_TWIRL_WIPE, SWORD_FLIP, TOOL_TOSS, TOOL_SHOULDER, TOOL_TWIRL, SHOVEL_SPIN, ROD_FLICK,
            SMALL_TOSS, TURN_OVER, JUGGLE, LIGHT_RAISE, HAND_FLEX, HAND_CRACK, BOW_PLUCK, SHIELD_BRACE, TRIDENT_SPIN,
            COMPASS_LOOK, BOOK_READ, BUCKET_SHAKE, FLINT_STRIKE, SPYGLASS_PEEK, TOTEM_RAISE, EGG_TOSS};
}
