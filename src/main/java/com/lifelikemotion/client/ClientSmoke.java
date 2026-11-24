package com.lifelikemotion.client;

import com.lifelikemotion.LifelikeMotion;
import net.minecraft.client.CameraType;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.server.IntegratedServer;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;

import java.util.ArrayList;
import java.util.List;

/**
 * CI only (-Dlifelikemotion.clientsmoke=true): in the test world, puts the player through every animation and takes a
 * screenshot of each (first person, third person, emotes, mobs), then quits.
 * "CLIENT SMOKE OK" in the log means every step ran.
 */
public final class ClientSmoke {
    private ClientSmoke() {}

    interface Step {
        boolean tick(int t);
    }

    static final List<Step> STEPS = new ArrayList<>();
    /** -Dlifelikemotion.baseline=true: the same shots with this mod's animations off, to compare with the game's own */
    static final boolean BASELINE = Boolean.getBoolean("lifelikemotion.baseline");
    /** -Dlifelikemotion.promo=true: the pictures for the mod's page instead of the tests (see {@link Promo}) */
    static final boolean PROMO = Boolean.getBoolean("lifelikemotion.promo");
    /** -Dlifelikemotion.only=fp_sword,fp_torch: only the shots starting with these (for quick local checks) */
    static final String[] ONLY = System.getProperty("lifelikemotion.only", "").isBlank() ? null : System.getProperty("lifelikemotion.only").split("[,+]");

    /** the items with our own 3D models (kept in step with tools/models.py) */
    /** batch 2 (kept in step with tools/models_food.py) */
    static final String[] FOOD_3D = {"apple", "golden_apple", "enchanted_golden_apple", "carrot", "golden_carrot",
            "potato", "baked_potato", "poisonous_potato", "beetroot", "melon_slice", "sweet_berries", "glow_berries",
            "chorus_fruit", "bread", "cookie", "pumpkin_pie", "beef", "cooked_beef", "porkchop", "cooked_porkchop",
            "mutton", "cooked_mutton", "rabbit", "cooked_rabbit", "chicken", "cooked_chicken", "rotten_flesh",
            "spider_eye", "dried_kelp", "cod", "cooked_cod", "salmon", "cooked_salmon", "tropical_fish", "pufferfish",
            "mushroom_stew", "rabbit_stew", "beetroot_soup", "suspicious_stew", "honey_bottle"};
    /** batch 3 (kept in step with tools/models_vessels.py) */
    static final String[] VESSELS_3D = {"bucket", "water_bucket", "lava_bucket", "milk_bucket", "powder_snow_bucket",
            "cod_bucket", "salmon_bucket", "tropical_fish_bucket", "pufferfish_bucket", "axolotl_bucket", "tadpole_bucket",
            "potion{Potion:\"minecraft:water\"}", "glass_bottle", "splash_potion{Potion:\"minecraft:healing\"}",
            "lingering_potion{Potion:\"minecraft:poison\"}", "experience_bottle", "dragon_breath"};
    /** batch 4 (kept in step with tools/models_materials.py) */
    static final String[] MATERIALS_3D = {
            "diamond", "emerald", "lapis_lazuli", "amethyst_shard", "quartz", "echo_shard", "prismarine_shard",
            "prismarine_crystals", "coal", "charcoal", "flint", "clay_ball", "raw_iron", "raw_gold", "raw_copper",
            "iron_ingot", "gold_ingot", "copper_ingot", "netherite_ingot", "netherite_scrap", "iron_nugget",
            "gold_nugget", "redstone", "glowstone_dust", "gunpowder", "sugar", "blaze_powder", "bone_meal",
            "ender_pearl", "ender_eye", "heart_of_the_sea", "nether_star", "blaze_rod", "brick", "nether_brick",
            "slime_ball", "magma_cream"};
    /** batch 5 (kept in step with tools/models_drops.py) */
    static final String[] DROPS_3D = {
            "stick", "bone", "string", "feather", "leather", "rabbit_hide", "rabbit_foot", "ink_sac", "glow_ink_sac",
            "honeycomb", "scute", "shulker_shell", "nautilus_shell", "phantom_membrane", "ghast_tear", "paper",
            "wheat", "egg", "snowball", "arrow", "spectral_arrow", "tipped_arrow{Potion:\"minecraft:healing\"}", "fire_charge", "bowl",
            "sugar_cane"};
    /** batch 6 (kept in step with tools/models_special.py) */
    static final String[] SPECIAL_3D = {
            "compass", "recovery_compass", "clock", "bow", "crossbow", "trident", "shield", "fishing_rod",
            "carrot_on_a_stick", "warped_fungus_on_a_stick", "spyglass", "shears", "flint_and_steel",
            "totem_of_undying", "lead", "name_tag", "saddle", "brush", "goat_horn", "book", "writable_book",
            "written_book", "enchanted_book", "knowledge_book", "map", "firework_rocket",
            "crossbow{Charged:1b,ChargedProjectiles:[{id:\"minecraft:arrow\",Count:1b}]}"};
    /** batch 7 (kept in step with tools/models_armor.py) */
    static final String[] ARMOR_3D = {
            "torch", "soul_torch", "redstone_torch", "lantern", "soul_lantern", "chain", "candle", "white_candle",
            "orange_candle", "magenta_candle", "light_blue_candle", "yellow_candle", "lime_candle", "pink_candle",
            "gray_candle", "light_gray_candle", "cyan_candle", "purple_candle", "blue_candle", "brown_candle",
            "green_candle", "red_candle", "black_candle", "leather_helmet", "leather_chestplate", "leather_leggings",
            "leather_boots", "chainmail_helmet", "chainmail_chestplate", "chainmail_leggings", "chainmail_boots",
            "iron_helmet", "iron_chestplate", "iron_leggings", "iron_boots", "golden_helmet", "golden_chestplate",
            "golden_leggings", "golden_boots", "diamond_helmet", "diamond_chestplate", "diamond_leggings",
            "diamond_boots", "netherite_helmet", "netherite_chestplate", "netherite_leggings", "netherite_boots",
            "turtle_helmet", "iron_chestplate{Trim:{material:\"minecraft:gold\",pattern:\"minecraft:coast\"}}",
            "diamond_helmet{Trim:{material:\"minecraft:amethyst\",pattern:\"minecraft:sentry\"}}",
            "leather_chestplate{display:{color:3949738}}"};
    static final String[] VEHICLES_3D = {
            "oak_boat", "oak_chest_boat", "spruce_boat", "spruce_chest_boat", "birch_boat", "birch_chest_boat",
            "jungle_boat", "jungle_chest_boat", "acacia_boat", "acacia_chest_boat", "dark_oak_boat",
            "dark_oak_chest_boat", "mangrove_boat", "mangrove_chest_boat", "cherry_boat", "cherry_chest_boat",
            "bamboo_raft", "bamboo_chest_raft", "minecart", "chest_minecart", "furnace_minecart", "hopper_minecart",
            "tnt_minecart", "command_block_minecart", "leather_horse_armor", "iron_horse_armor",
            "golden_horse_armor", "diamond_horse_armor", "leather_horse_armor{display:{color:3949738}}"};
    static final String[] MISC_3D = {
            "music_disc_13", "music_disc_cat", "music_disc_blocks", "music_disc_chirp", "music_disc_far",
            "music_disc_mall", "music_disc_mellohi", "music_disc_stal", "music_disc_strad", "music_disc_ward",
            "music_disc_11", "music_disc_wait", "music_disc_otherside", "music_disc_5", "music_disc_pigstep",
            "music_disc_relic", "disc_fragment_5", "creeper_spawn_egg", "pig_spawn_egg", "allay_spawn_egg",
            "sniffer_spawn_egg", "white_dye", "orange_dye", "magenta_dye", "light_blue_dye", "yellow_dye", "lime_dye",
            "pink_dye", "gray_dye", "light_gray_dye", "cyan_dye", "purple_dye", "blue_dye", "brown_dye", "green_dye",
            "red_dye", "black_dye"};
    static final String[] RELICS_3D = {
            "coast_armor_trim_smithing_template", "dune_armor_trim_smithing_template",
            "eye_armor_trim_smithing_template", "host_armor_trim_smithing_template",
            "netherite_upgrade_smithing_template", "raiser_armor_trim_smithing_template",
            "rib_armor_trim_smithing_template", "sentry_armor_trim_smithing_template",
            "shaper_armor_trim_smithing_template", "silence_armor_trim_smithing_template",
            "snout_armor_trim_smithing_template", "spire_armor_trim_smithing_template",
            "tide_armor_trim_smithing_template", "vex_armor_trim_smithing_template",
            "ward_armor_trim_smithing_template", "wayfinder_armor_trim_smithing_template",
            "wild_armor_trim_smithing_template", "angler_pottery_sherd", "archer_pottery_sherd",
            "arms_up_pottery_sherd", "blade_pottery_sherd", "brewer_pottery_sherd", "burn_pottery_sherd",
            "danger_pottery_sherd", "explorer_pottery_sherd", "friend_pottery_sherd", "heart_pottery_sherd",
            "heartbreak_pottery_sherd", "howl_pottery_sherd", "miner_pottery_sherd", "mourner_pottery_sherd",
            "plenty_pottery_sherd", "prize_pottery_sherd", "sheaf_pottery_sherd", "shelter_pottery_sherd",
            "skull_pottery_sherd", "snort_pottery_sherd"};
    static final String[] PLANTS_3D = {
            "dandelion", "poppy", "blue_orchid", "allium", "azure_bluet", "red_tulip", "orange_tulip",
            "white_tulip", "pink_tulip", "oxeye_daisy", "cornflower", "lily_of_the_valley", "wither_rose",
            "torchflower", "pink_petals", "sunflower", "lilac", "rose_bush", "peony", "pitcher_plant",
            "oak_sapling", "spruce_sapling", "birch_sapling", "jungle_sapling", "acacia_sapling",
            "dark_oak_sapling", "cherry_sapling", "mangrove_propagule", "grass", "tall_grass", "fern", "large_fern",
            "dead_bush", "seagrass", "kelp", "bamboo", "vine", "glow_lichen", "hanging_roots", "lily_pad",
            "red_mushroom", "brown_mushroom", "crimson_fungus", "warped_fungus", "crimson_roots", "warped_roots",
            "nether_sprouts", "weeping_vines", "twisting_vines", "nether_wart", "tube_coral", "dead_tube_coral",
            "tube_coral_fan", "dead_tube_coral_fan", "brain_coral", "dead_brain_coral", "brain_coral_fan",
            "dead_brain_coral_fan", "bubble_coral", "dead_bubble_coral", "bubble_coral_fan",
            "dead_bubble_coral_fan", "fire_coral", "dead_fire_coral", "fire_coral_fan", "dead_fire_coral_fan",
            "horn_coral", "dead_horn_coral", "horn_coral_fan", "dead_horn_coral_fan", "wheat_seeds",
            "pumpkin_seeds", "melon_seeds", "beetroot_seeds", "torchflower_seeds", "cocoa_beans", "pitcher_pod"};
    static final String[] BLOCKS_3D = {
            "oak_door", "spruce_door", "birch_door", "jungle_door", "acacia_door", "dark_oak_door", "mangrove_door",
            "cherry_door", "bamboo_door", "crimson_door", "warped_door", "iron_door", "oak_sign",
            "oak_hanging_sign", "spruce_sign", "spruce_hanging_sign", "birch_sign", "birch_hanging_sign",
            "jungle_sign", "jungle_hanging_sign", "acacia_sign", "acacia_hanging_sign", "dark_oak_sign",
            "dark_oak_hanging_sign", "mangrove_sign", "mangrove_hanging_sign", "cherry_sign", "cherry_hanging_sign",
            "bamboo_sign", "bamboo_hanging_sign", "crimson_sign", "crimson_hanging_sign", "warped_sign",
            "warped_hanging_sign", "white_bed", "orange_bed", "magenta_bed", "light_blue_bed", "yellow_bed",
            "lime_bed", "pink_bed", "gray_bed", "light_gray_bed", "cyan_bed", "purple_bed", "blue_bed", "brown_bed",
            "green_bed", "red_bed", "black_bed"};
    static final String[] ITEMS_3D = items3d();

    static String[] items3d() {
        java.util.List<String> l = new java.util.ArrayList<>();
        for (String t : new String[]{"wooden", "stone", "iron", "golden", "diamond", "netherite"})
            for (String k : new String[]{"sword", "pickaxe", "axe", "shovel", "hoe"}) l.add(t + "_" + k);
        l.addAll(java.util.List.of(FOOD_3D));
        l.addAll(java.util.List.of(VESSELS_3D));
        l.addAll(java.util.List.of(MATERIALS_3D));
        l.addAll(java.util.List.of(DROPS_3D));
        l.addAll(java.util.List.of(SPECIAL_3D));
        l.addAll(java.util.List.of(ARMOR_3D));
        l.addAll(java.util.List.of(VEHICLES_3D));
        l.addAll(java.util.List.of(MISC_3D));
        l.addAll(java.util.List.of(RELICS_3D));
        l.addAll(java.util.List.of(PLANTS_3D));
        l.addAll(java.util.List.of(BLOCKS_3D));
        return l.toArray(new String[0]);
    }

    static boolean wanted(String name) {
        if (ONLY == null) return true;
        for (String o : ONLY) if (name.startsWith(o)) return true;
        return false;
    }
    static int stepIndex, stepTick, shotNo, waited;
    static boolean built;
    /** keeps the camera still (the test's own turns excepted) */
    static Float yaw = 0f, pitch = 10f;

    @SubscribeEvent
    public static void onTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null) return;
        if (!built) {
            if (++waited < 80) return;
            built = true;
            build();
        }
        if (PROMO) mc.getToasts().clear();
        try {
            if (yaw != null) {
                mc.player.setYRot(yaw);
                mc.player.yRotO = yaw;
                mc.player.setYHeadRot(yaw);
                mc.player.yBodyRot = yaw;
            }
            if (pitch != null) {
                mc.player.setXRot(pitch);
                mc.player.xRotO = pitch;
            }
            if (stepIndex >= STEPS.size()) return;
            if (STEPS.get(stepIndex).tick(stepTick++)) {
                stepIndex++;
                stepTick = 0;
            }
        } catch (Throwable ex) {
            LifelikeMotion.LOG.error("[client smoke] step {} failed (com.lifelikemotion)", stepIndex, ex);
            stepIndex++;
            stepTick = 0;
        }
    }

    // ------------------------------------------------------------------ the script
    static void build() {
        Minecraft mc = Minecraft.getInstance();
        add(t -> {
            if (t == 0) {
                if (BASELINE) {
                    com.lifelikemotion.config.LMConfig.FP_ENABLED.set(false);
                    com.lifelikemotion.config.LMConfig.BODY_ENABLED.set(false);
                    com.lifelikemotion.config.LMConfig.MOBS_ENABLED.set(false);
                } else {
                    com.lifelikemotion.config.LMConfig.FP_ENABLED.set(true);
                    com.lifelikemotion.config.LMConfig.BODY_ENABLED.set(true);
                    com.lifelikemotion.config.LMConfig.MOBS_ENABLED.set(true);
                    // (the test stands still a lot: no show-offs of their own in the middle of other shots)
                    com.lifelikemotion.config.LMConfig.FP_IDLE_SHOW.set(false);
                    // the 3D items pack (normally switched on at the title screen, which quick play skips)
                    Packs.enableNow();
                }
            }
            return t > 140 && mc.getOverlay() == null;
        });
        if (PROMO) {
            Promo.build();
            finish();
            return;
        }
        add(t -> {
            if (t == 0) {
                cmd("gamemode creative");
                cmd("time set 6000");
                cmd("weather clear");
                cmd("gamerule doDaylightCycle false");
                cmd("gamerule doMobSpawning false");
                cmd("kill @e[type=!player]");
                cmd("tp @s 0 -60 0 0 10");
                // a pool to swim in, a ladder to climb, a wall to mine
                cmd("fill 6 -64 -3 14 -61 3 water");
                cmd("fill -4 -60 -1 -4 -52 1 stone");
                cmd("fill -3 -60 0 -3 -52 0 ladder[facing=east]");
                cmd("fill -1 -60 4 1 -58 4 stone");
            }
            return t > 30;
        });
        mc.options.bobView().set(true);

        // ---- films of first-person motion (for judging it as it moves)
        film("film");
        filmEat("filmeat");
        filmChop("filmchop");
        swingStills("still_mine", "diamond_pickaxe", com.lifelikemotion.client.fp.Clips.MINE, 0, 0.2f, 0.36f, 0.48f, 0.56f, 0.7f, 0.85f);
        swingStills("still_slasha", "diamond_sword", com.lifelikemotion.client.fp.Clips.SLASH_A, 0.18f, 0.3f, 0.38f, 0.44f, 0.5f, 0.6f, 0.75f);
        swingStills("still_slashb", "diamond_sword", com.lifelikemotion.client.fp.Clips.SLASH_B, 0.18f, 0.38f, 0.44f, 0.5f, 0.6f);
        swingStills("still_stab", "diamond_sword", com.lifelikemotion.client.fp.Clips.STAB, 0.22f, 0.4f);
        swingStills("still_chop", "diamond_axe", com.lifelikemotion.client.fp.Clips.CHOP, 0.26f, 0.38f, 0.45f, 0.5f, 0.6f);
        swingStills("still_dig", "diamond_shovel", com.lifelikemotion.client.fp.Clips.DIG, 0.22f, 0.46f, 0.66f);

        // ---- first person
        fp("fp_empty_idle", "air", null, 0);
        fp("fp_punch", "air", Motion.Action.ATTACK, 2);
        // 3D items: each held in first person, then all of them in the hand from the side and on the ground
        for (String it : ITEMS_3D) fp("item3d_" + it.replaceAll("\\{.*", ""), it, null, 0);
        if (wanted("item3d_ground")) add(t -> {
            if (t == 0) {
                mc.options.setCameraType(CameraType.FIRST_PERSON);
                give("air");
                cmd("kill @e[type=item]");
                cmd("tp @s 0 -58.4 -1.6 0 52");
                for (int i = 0; i < ITEMS_3D.length; i++)
                    cmd(String.format("summon item %.2f -60 %.2f {Item:{id:\"minecraft:%s\",Count:1b%s},PickupDelay:32767,Age:-32768,NoGravity:1b}",
                            -1.6 + (i % 5) * 0.8, 0.4 + (i / 5) * 0.62, ITEMS_3D[i].replaceAll("\\{.*", ""),
                            ITEMS_3D[i].contains("{") ? ",tag:" + ITEMS_3D[i].substring(ITEMS_3D[i].indexOf('{')) : ""));
            }
            if (t == 30) shot("item3d_ground");
            if (t == 31) cmd("kill @e[type=item]");
            return t > 34;
        });
        use("food_eat_apple", "apple", 14);
        use("food_eat_stew", "mushroom_stew", 14);
        // every show-off move, frozen at eight points in time, with an item it belongs to
        String[][] showItems = {{"sword_twirl_wipe", "iron_sword"}, {"sword_flip", "diamond_sword"}, {"tool_toss", "iron_axe"},
                {"tool_shoulder", "diamond_pickaxe"}, {"tool_twirl", "iron_pickaxe"}, {"shovel_spin", "iron_shovel"}, {"rod_flick", "fishing_rod"},
                {"small_toss", "oak_planks"}, {"turn_over", "bread"}, {"juggle", "snowball"}, {"light_raise", "lantern"},
                {"hand_flex", "air"}, {"hand_crack", "air"}, {"bow_pluck", "bow"}, {"shield_brace", "shield"}, {"trident_spin", "trident"},
                {"compass_look", "compass"}, {"book_read", "book"}, {"bucket_shake", "water_bucket"}, {"flint_strike", "flint_and_steel"},
                {"spyglass_peek", "spyglass"}, {"totem_raise", "totem_of_undying"}, {"egg_toss", "egg"}};
        for (String[] si : showItems) {
            com.lifelikemotion.client.fp.Flourishes.Move mv = null;
            for (var m : com.lifelikemotion.client.fp.Flourishes.ALL) if (m.name().equals(si[0])) mv = m;
            final var move = mv;
            if (move != null && wanted("show_" + si[0])) add(t -> {
                if (t == 0) {
                    mc.options.setCameraType(CameraType.FIRST_PERSON);
                    give(si[1]);
                }
                int i = (t - 12) / 3;
                if (t >= 12 && (t - 12) % 3 == 0 && i < 8) {
                    com.lifelikemotion.client.fp.Flourish.testMove = move;
                    com.lifelikemotion.client.fp.Flourish.testTime = 0.06f + i * 0.125f;
                }
                if (t >= 14 && (t - 14) % 3 == 0 && (t - 14) / 3 < 8) shot(String.format("show_%s_%d", si[0], (t - 14) / 3));
                if (t == 40) com.lifelikemotion.client.fp.Flourish.testMove = null;
                return t > 42;
            });
        }
        // (tuning: candidate carry poses, held still)
        Object[][] tune = {
                {"iron_sword", new float[]{-0.06f, -0.06f, 0, 30, 30, 18}}, {"iron_sword", new float[]{-0.02f, -0.04f, 0, 20, 20, 30}},
                {"iron_sword", new float[]{0.02f, -0.02f, 0.04f, -20, 10, 40}}, {"iron_sword", new float[]{-0.1f, -0.02f, -0.02f, 40, 45, 10}},
                {"diamond_axe", new float[]{0.02f, 0.10f, 0.05f, -55, -10, -10}}, {"diamond_axe", new float[]{-0.04f, 0.14f, 0.02f, -70, 0, -25}},
                {"diamond_axe", new float[]{0, 0.06f, 0.08f, -40, -20, -30}}, {"diamond_axe", new float[]{-0.08f, 0.04f, 0.0f, -30, 15, -15}},
                {"diamond_axe", new float[]{0.04f, 0.18f, 0.10f, -80, -10, -10}}, {"diamond_axe", new float[]{-0.06f, 0.0f, 0.02f, 15, 25, 25}}};
        for (int ti = 0; ti < tune.length; ti++) {
            String it = (String) tune[ti][0];
            float[] pose = (float[]) tune[ti][1];
            int n = ti;
            if (wanted("tune_pose")) add(t -> {
                if (t == 0) {
                    mc.options.setCameraType(CameraType.FIRST_PERSON);
                    give(it);
                    com.lifelikemotion.client.fp.Stance.testPose = pose;
                }
                if (t == 12) shot("tune_pose_" + n);
                if (t == 13) com.lifelikemotion.client.fp.Stance.testPose = null;
                return t > 14;
            });
        }
        // (tuning: where spins turn about)
        float[][] pivots = {{0, 0, 0}, {0, 0.15f, 0}, {0.05f, 0.2f, 0}, {0.08f, 0.25f, 0.05f}, {0, 0.3f, 0}};
        for (int pi = 0; pi < pivots.length; pi++) {
            float[] pv = pivots[pi];
            int n = pi;
            if (wanted("tune_pivot")) add(t -> {
                if (t == 0) {
                    mc.options.setCameraType(CameraType.FIRST_PERSON);
                    give("iron_sword");
                    com.lifelikemotion.client.fp.Flourish.pivotX = pv[0];
                    com.lifelikemotion.client.fp.Flourish.pivotY = pv[1];
                    com.lifelikemotion.client.fp.Flourish.pivotZ = pv[2];
                    com.lifelikemotion.client.fp.Flourish.testMove = com.lifelikemotion.client.fp.Flourishes.SWORD_TWIRL_WIPE;
                }
                for (int k = 0; k < 4; k++) {
                    if (t == 8 + k * 3) com.lifelikemotion.client.fp.Flourish.testTime = 0.16f + k * 0.05f;
                    if (t == 10 + k * 3) shot("tune_pivot_" + n + "_" + k);
                }
                if (t == 24) {
                    com.lifelikemotion.client.fp.Flourish.testMove = null;
                    com.lifelikemotion.client.fp.Flourish.pivotX = null;
                    com.lifelikemotion.client.fp.Flourish.pivotY = null;
                    com.lifelikemotion.client.fp.Flourish.pivotZ = null;
                }
                return t > 25;
            });
        }
        // carrying: standing, walking and running with each kind of item
        String[] carry = {"iron_sword", "diamond_axe", "oak_planks", "bread", "torch", "lantern", "air", "bow"};
        for (String it : carry) {
            move("carry_" + it + "_idle", it, false, false, false, 12, CameraType.FIRST_PERSON);
            move("carry_" + it + "_walk", it, true, false, false, 16, CameraType.FIRST_PERSON);
            move("carry_" + it + "_run", it, true, true, false, 16, CameraType.FIRST_PERSON);
        }
        // swimming, climbing, reins, rowing, on fire: with empty hands and with a sword
        for (String act : new String[]{"swim", "climb", "reins", "row", "fire"}) {
            for (String it : new String[]{"air", "iron_sword"}) {
                if (wanted("act_" + act)) add(t -> {
                    if (t == 0) {
                        mc.options.setCameraType(CameraType.FIRST_PERSON);
                        give(it);
                        com.lifelikemotion.client.fp.Activities.testActivity = act;
                    }
                    if (act.equals("climb") && t >= 10) com.lifelikemotion.client.fp.Activities.climbY = (t - 10) * 0.1;
                    if (t == 18) shot("act_" + act + "_" + it + "_a");
                    if (t == 22) shot("act_" + act + "_" + it + "_b");
                    if (t == 23) com.lifelikemotion.client.fp.Activities.testActivity = null;
                    return t > 30;
                });
            }
        }
        // one-shots: waking up stretch, a dropped-item toss
        if (wanted("shot_stretch")) add(t -> {
            if (t == 0) {
                give("air");
                com.lifelikemotion.client.fp.Activities.play(0, com.lifelikemotion.client.fp.Activities.STRETCH, 40);
                com.lifelikemotion.client.fp.Activities.play(1, com.lifelikemotion.client.fp.Activities.STRETCH, 40);
            }
            if (t == 16) shot("shot_stretch");
            return t > 44;
        });
        // physics: falling with a box, a bed, a lantern (mid-fall, and just after landing); a lantern after a sprint stops
        for (String it : new String[]{"oak_planks", "white_bed", "lantern", "water_bucket"}) {
            final boolean[] landed = {false};
            final int[] landT = {-1};
            if (wanted("phys_fall")) add(t -> {
                if (t == 0) {
                    mc.options.setCameraType(CameraType.FIRST_PERSON);
                    give(it);
                    cmd("tp @s 0 -44 -12 0 10");
                    landed[0] = false;
                    landT[0] = -1;
                }
                if (t == 14) shot("phys_fall_" + it + "_falling");
                if (t > 14 && landT[0] < 0 && mc.player.onGround()) landT[0] = t;
                if (landT[0] > 0 && t == landT[0] + 2) shot("phys_fall_" + it + "_landed");
                return landT[0] > 0 && t > landT[0] + 10 || t > 120;
            });
        }
        for (String it : new String[]{"lantern", "white_banner"}) {
            if (wanted("phys_run")) add(t -> {
                if (t == 0) {
                    mc.options.setCameraType(CameraType.FIRST_PERSON);
                    give(it);
                    cmd("tp @s 0 -60 -14 0 10");
                }
                if (t == 6) {
                    mc.options.keyUp.setDown(true);
                    mc.options.keySprint.setDown(true);
                    mc.player.setSprinting(true);
                }
                if (t == 20) shot("phys_run_" + it + "_running");
                if (t == 21) {
                    mc.options.keyUp.setDown(false);
                    mc.options.keySprint.setDown(false);
                    mc.player.setSprinting(false);
                }
                if (t == 25) shot("phys_run_" + it + "_stopped");
                if (t == 29) shot("phys_run_" + it + "_settling");
                return t > 40;
            });
        }
        // eating and drinking in their own ways
        use("eat_soup", "mushroom_stew", 18);
        use("eat_carrot", "carrot", 16);
        use("eat_milk", "milk_bucket", 18);
        // every swing, frozen at eight points in time (for tuning the keyframes)
        String[] clipItems = {"iron_sword", "iron_sword", "iron_sword", "diamond_axe", "diamond_pickaxe", "iron_shovel", "iron_hoe", "air", "oak_planks", "snowball", "bread",
                "water_bucket", "bucket", "flint_and_steel", "shears", "bone_meal", "iron_axe", "iron_shovel", "fishing_rod", "fishing_rod", "air", "air", "air", "iron_sword"};
        for (int c = 0; c < com.lifelikemotion.client.fp.Clips.ALL.length; c++) {
            com.lifelikemotion.client.fp.Clip clip = com.lifelikemotion.client.fp.Clips.ALL[c];
            String cn = com.lifelikemotion.client.fp.Clips.NAMES[c], item = clipItems[c];
            if (wanted("strip_" + cn)) add(t -> {
                if (t == 0) {
                    mc.options.setCameraType(CameraType.FIRST_PERSON);
                    give(item);
                    com.lifelikemotion.client.fp.FirstPersonAnimator.testClip = clip;
                }
                int i = (t - 12) / 3;
                if (t >= 12 && (t - 12) % 3 == 0 && i < 8) com.lifelikemotion.client.fp.FirstPersonAnimator.testSwing = 0.06f + i * 0.12f;
                if (t >= 14 && (t - 14) % 3 == 0 && (t - 14) / 3 < 8) shot(String.format("strip_%s_%d", cn, (t - 14) / 3));
                if (t == 40) {
                    com.lifelikemotion.client.fp.FirstPersonAnimator.testSwing = null;
                    com.lifelikemotion.client.fp.FirstPersonAnimator.testClip = null;
                }
                return t > 42;
            });
        }
        fp("fp_sword_idle", "iron_sword", null, 0);
        fp("fp_sword_slash_a_windup", "iron_sword", Motion.Action.ATTACK, 1);
        fp("fp_sword_slash_b_windup", "iron_sword", Motion.Action.ATTACK, 1);
        fp("fp_sword_slash_a", "iron_sword", Motion.Action.ATTACK, 2);
        fp("fp_sword_slash_b", "iron_sword", Motion.Action.ATTACK, 2);
        fp("fp_sword_followthrough", "iron_sword", Motion.Action.ATTACK, 4);
        fp("fp_axe_windup", "diamond_axe", Motion.Action.ATTACK, 1);
        fp("fp_axe_chop", "diamond_axe", Motion.Action.ATTACK, 3);
        fp("fp_pickaxe_mine", "diamond_pickaxe", Motion.Action.MINE, 2);
        fp("fp_shovel_scoop", "iron_shovel", Motion.Action.MINE, 3);
        fp("fp_block_idle", "oak_planks", null, 0);
        fp("fp_block_place", "oak_planks", Motion.Action.USE, 2);
        fp("fp_torch", "torch", null, 0);
        fp("fp_lantern", "lantern", null, 0);
        fp("fp_apple", "apple", null, 0);
        fp("fp_bow", "bow", null, 0);
        use("fp_eat_golden_apple", "golden_apple", 14);
        use("fp_drink_potion", "potion", 14);
        use("fp_bow_draw", "bow", 14);
        add(t -> {
            if (t == 6) cmd("kill @e[type=arrow]");
            return t > 8;
        });
        // turning fast: the hands trail
        if (wanted("fp_turning")) add(t -> {
            if (t == 0) give("iron_sword");
            if (t > 4 && t < 14) yaw = yaw + 12;
            if (t == 12) shot("fp_turning");
            if (t == 20) yaw = 0f;
            return t > 30;
        });
        move("fp_sprint", "iron_sword", true, true, false, 14, CameraType.FIRST_PERSON);
        move("fp_jump", "iron_sword", true, false, true, 5, CameraType.FIRST_PERSON);

        // ---- third person (seen from the front)
        move("tp_idle", "air", false, false, false, 20, CameraType.THIRD_PERSON_FRONT);
        move("tp_walk", "air", true, false, false, 14, CameraType.THIRD_PERSON_FRONT);
        move("tp_sprint", "iron_sword", true, true, false, 14, CameraType.THIRD_PERSON_FRONT);
        move("tp_jump_up", "air", false, false, true, 3, CameraType.THIRD_PERSON_FRONT);
        move("tp_jump_top", "air", false, false, true, 7, CameraType.THIRD_PERSON_FRONT);
        if (wanted("tp_falling")) add(t -> {
            if (t == 0) {
                mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT);
                cmd("tp @s 0 -50 0 0 10");
            }
            if (t == 8) shot("tp_falling");
            return t > 40;
        });
        tpSwing("tp_sword_slash", "iron_sword", 3);
        tpSwing("tp_sword_backhand", "iron_sword", 3);
        tpSwing("tp_axe_chop", "diamond_axe", 3);
        tpSwing("tp_punch", "air", 2);
        if (wanted("tp_eat")) add(t -> {
            if (t == 0) {
                mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT);
                give("golden_apple");
                mc.options.keyUse.setDown(true);
            }
            if (t == 14) shot("tp_eat");
            if (t == 15) mc.options.keyUse.setDown(false);
            return t > 40;
        });
        if (wanted("tp_sneak")) add(t -> {
            if (t == 0) {
                give("air");
                mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT);
                mc.options.keyShift.setDown(true);
            }
            if (t == 10) shot("tp_sneak");
            if (t == 11) mc.options.keyShift.setDown(false);
            return t > 20;
        });
        // water: treading, then swimming
        if (wanted("tp_tread_water")) add(t -> {
            if (t == 0) {
                mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT);
                cmd("tp @s 10 -62 0 0 10");
            }
            if (t == 30) shot("tp_tread_water");
            if (t == 31) {
                yaw = -90f;
                pitch = 20f;
                mc.options.keyUp.setDown(true);
                mc.options.keySprint.setDown(true);
            }
            if (t == 50) shot("tp_swim");
            if (t == 51) {
                mc.options.keyUp.setDown(false);
                mc.options.keySprint.setDown(false);
                yaw = 0f;
                pitch = 10f;
            }
            return t > 60;
        });
        // a ladder
        if (wanted("tp_climb_a")) add(t -> {
            if (t == 0) {
                mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
                cmd("tp @s -3 -60 0 90 0");
                yaw = 90f;
                pitch = 0f;
            }
            if (t == 6) mc.options.keyUp.setDown(true);
            if (t == 22) shot("tp_climb_a");
            if (t == 26) shot("tp_climb_b");
            if (t == 27) mc.options.keyUp.setDown(false);
            if (t == 30) {
                cmd("tp @s 0 -60 0 0 10");
                yaw = 0f;
                pitch = 10f;
            }
            return t > 40;
        });

        tpSwing("tp_place_block", "oak_planks", 3);

        // ---- emotes: third person from the front, and what your arms do in first person
        for (com.lifelikemotion.client.emote.Emote em : com.lifelikemotion.client.emote.Emote.values()) {
            String n = em.name().toLowerCase();
            if (wanted("emote_" + n)) add(t -> {
                if (t == 0) {
                    give("air");
                    cmd("tp @s 0 -60 -12 0 10");
                    mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT);
                }
                if (t == 5) com.lifelikemotion.client.emote.Emotes.play(em);
                if (t == 19) shot("emote_" + n);
                if (t == 20) mc.options.setCameraType(CameraType.FIRST_PERSON);
                if (t == 26 && em != com.lifelikemotion.client.emote.Emote.BOW && em != com.lifelikemotion.client.emote.Emote.SIT) shot("emote_" + n + "_first_person");
                if (t == 27) com.lifelikemotion.client.emote.Emotes.stop();
                return t > 34;
            });
        }
        if (wanted("emote_wheel")) add(t -> {
            if (t == 0) mc.setScreen(new com.lifelikemotion.client.emote.EmoteWheelScreen());
            if (t == 10) shot("emote_wheel");
            if (t == 11) mc.setScreen(null);
            return t > 14;
        });

        // ---- mobs
        if (wanted("mobs")) add(t -> {
            if (t == 0) {
                mc.options.setCameraType(CameraType.FIRST_PERSON);
                cmd("kill @e[type=item]");
                cmd("tp @s 0 -60 -20 0 15");
                String[] mobs = {"pig", "cow", "sheep", "chicken", "wolf", "zombie", "skeleton", "creeper", "villager", "spider"};
                for (int i = 0; i < mobs.length; i++) {
                    double x = -6 + (i % 5) * 3, z = -14 + (i / 5) * 3.5;
                    String tag = mobs[i].equals("wolf") ? ",Owner:[I;1,2,3,4],Tame:1b" : "";
                    cmd(String.format("summon %s %.1f -60 %.1f {NoAI:1b,Rotation:[180f,0f],PersistenceRequired:1b%s}", mobs[i], x, z, tag));
                }
            }
            if (t == 40) shot("mobs_a");
            if (t == 52) shot("mobs_b");
            if (t == 53) cmd("kill @e[type=!player]");
            return t > 58;
        });


        finish();
    }

    static void finish() {
        Minecraft mc = Minecraft.getInstance();
        add(t -> {
            if (t == 0) {
                LifelikeMotion.LOG.info("[client smoke] took {} screenshots", shotNo);
                LifelikeMotion.LOG.info("CLIENT SMOKE OK");
            }
            if (t == 40) mc.stop();
            return false;
        });
    }

    /** First person: hold an item, maybe swing it (a shot a few ticks into the swing). */
    static void fp(String name, String item, Motion.Action action, int at) {
        if (!wanted(name)) return;
        Minecraft mc = Minecraft.getInstance();
        add(t -> {
            if (t == 0) {
                mc.options.setCameraType(CameraType.FIRST_PERSON);
                give(item);
            }
            if (action == null) {
                if (t == 25) shot(name);
                return t > 27;
            }
            if (t == 20) {
                Motion.pending = action;
                mc.player.swing(InteractionHand.MAIN_HAND);
            }
            if (t == 21) com.lifelikemotion.client.fp.FirstPersonAnimator.testSwing = at / 6f;
            if (t == 26) shot(name);
            if (t == 27) com.lifelikemotion.client.fp.FirstPersonAnimator.testSwing = null;
            return t > 34;
        });
    }

    static final int FILM = 400;
    /** the film being shot (frames are taken every half tick, from the render loop), and the next frame's time */
    static String filmName;
    static float filmNext;
    static int filmFrame;

    @SubscribeEvent
    public static void onRenderTick(TickEvent.RenderTickEvent e) {
        if (e.phase != TickEvent.Phase.END || filmName == null) return;
        float t = Motion.ticks + e.renderTickTime;
        if (t < filmNext) return;
        shot(String.format("%s_%04d", filmName, filmFrame++));
        filmNext = (float) Math.floor(t * 2 + 1) / 2f;
    }

    static volatile long serverSleep;

    /** (the built-in server is slowed down with the client, so eating and the like finish when they should) */
    @SubscribeEvent
    public static void onServerTick(TickEvent.ServerTickEvent e) {
        if (e.phase != TickEvent.Phase.END || serverSleep <= 0) return;
        try {
            Thread.sleep(serverSleep);
        } catch (InterruptedException ignored) {
            Thread.currentThread().interrupt();
        }
    }

    /** slows the game's clock down (the test machine draws too few frames a second for a smooth film), or back */
    static void slowClock(float msPerTick) {
        serverSleep = (long) Math.max(0, msPerTick - 50);
        try {
            Minecraft mc = Minecraft.getInstance();
            for (var f : Minecraft.class.getDeclaredFields()) {
                if (f.getType() != net.minecraft.client.Timer.class) continue;
                f.setAccessible(true);
                Object timer = f.get(mc);
                var ms = net.minecraft.client.Timer.class.getDeclaredField("msPerTick");
                ms.setAccessible(true);
                ms.setFloat(timer, msPerTick);
            }
        } catch (ReflectiveOperationException ex) {
            LifelikeMotion.LOG.error("[client smoke] can't slow the clock", ex);
        }
    }

    /**
     * A film of first-person motion, one shot every tick ("film_0000"...): standing, walking, running with a jump,
     * turning, a sword combo on a zombie, fists, eating, mining a block and throwing snowballs, all through the game's
     * own input.
     */
    static void film(String name) {
        if (!wanted(name)) return;
        Minecraft mc = Minecraft.getInstance();
        add(t -> {
            var o = mc.options;
            if (t == 0) {
                o.setCameraType(CameraType.FIRST_PERSON);
                cmd("gamemode creative");
                cmd("kill @e[type=!player]");
                cmd("tp @s 40 -60 30 0 10");
                give("diamond_sword");
                yaw = 0f;
                pitch = 10f;
            }
            int f = t - 20;
            if (f == 0) {
                slowClock(450);
                filmName = name;
                filmFrame = 0;
                filmNext = Motion.ticks;
            }
            if (f == FILM) {
                filmName = null;
                slowClock(50);
            }
            switch (f) {
                case 30 -> o.keyUp.setDown(true);                                   // walk
                case 70 -> { o.keySprint.setDown(true); mc.player.setSprinting(true); }   // run
                case 92 -> o.keyJump.setDown(true);                                 // a jump while running
                case 95 -> o.keyJump.setDown(false);
                case 115 -> { o.keyUp.setDown(false); o.keySprint.setDown(false); mc.player.setSprinting(false); }
                case 140 -> cmd("summon husk ^ ^ ^2.6 {NoAI:1b,PersistenceRequired:1b,Health:200f,Attributes:[{Name:\"generic.max_health\",Base:200}]}");
                case 150, 164, 178 -> KeyMapping.click(o.keyAttack.getKey());       // a three-hit combo on it
                case 196 -> give("air");
                case 204, 213, 222, 231 -> KeyMapping.click(o.keyAttack.getKey());  // fists, in turn
                case 240 -> { cmd("kill @e[type=husk]"); give("apple"); }
                case 246 -> o.keyUse.setDown(true);                                 // eat
                case 286 -> o.keyUse.setDown(false);
                case 290 -> {
                    cmd("gamemode survival");
                    cmd("fill ~-1 ~ ~2 ~1 ~2 ~2 obsidian");
                    give("diamond_pickaxe");
                }
                case 298 -> o.keyAttack.setDown(true);                              // mine the block in front
                case 340 -> { o.keyAttack.setDown(false); give("snowball"); cmd("gamemode creative"); }
                case 352, 370 -> KeyMapping.click(o.keyUse.getKey());               // throw
                default -> {}
            }
            // a look round while standing: turn right and back
            if (f >= 120 && f < 140) yaw = (float) (Math.sin((f - 120) / 20.0 * Math.PI) * 70);
            if (f == 140) yaw = 0f;
            if (f == FILM) {
                o.keyUp.setDown(false);
                o.keyAttack.setDown(false);
                o.keyUse.setDown(false);
                cmd("gamemode creative");
                cmd("kill @e[type=!player]");
            }
            return f > FILM;
        });
    }

    /** Stills of one swing held at several points (u), for checking a swing's shape. */
    static void swingStills(String name, String item, com.lifelikemotion.client.fp.Clip clip, float... us) {
        if (!wanted(name)) return;
        Minecraft mc = Minecraft.getInstance();
        add(t -> {
            if (t == 0) {
                mc.options.setCameraType(CameraType.FIRST_PERSON);
                cmd("tp @s 40 -60 30 0 10");
                give(item);
                com.lifelikemotion.client.fp.FirstPersonAnimator.testClip = clip;
            }
            int i = (t - 20) / 3;
            if (t >= 20 && i < us.length) {
                if ((t - 20) % 3 == 0) com.lifelikemotion.client.fp.FirstPersonAnimator.testSwing = us[i];
                if ((t - 20) % 3 == 2) shot(String.format("%s_%02d", name, Math.round(us[i] * 100)));
            }
            if (t == 20 + us.length * 3) {
                com.lifelikemotion.client.fp.FirstPersonAnimator.testSwing = null;
                com.lifelikemotion.client.fp.FirstPersonAnimator.testClip = null;
            }
            return t > 22 + us.length * 3;
        });
    }

    /** A film of chopping a tree trunk with an axe (held down, so it chops again and again). */
    static void filmChop(String name) {
        if (!wanted(name)) return;
        Minecraft mc = Minecraft.getInstance();
        add(t -> {
            var o = mc.options;
            if (t == 0) {
                o.setCameraType(CameraType.FIRST_PERSON);
                cmd("gamemode survival");
                cmd("kill @e[type=!player]");
                cmd("tp @s 60 -60 30 0 10");
                give("diamond_axe");
                yaw = 0f;
                pitch = 10f;
            }
            if (t == 10) cmd("fill 59 -60 32 61 -55 37 oak_log");
            int f = t - 30;
            if (f == 0) {
                slowClock(450);
                filmName = name;
                filmFrame = 0;
                filmNext = Motion.ticks;
            }
            if (f == 6) o.keyAttack.setDown(true);
            if (f == 70) o.keyAttack.setDown(false);
            if (f == 80) {
                filmName = null;
                slowClock(50);
                cmd("gamemode creative");
                cmd("fill 59 -60 32 61 -55 37 air");
            }
            return f > 80;
        });
    }

    /** A film of eating and drinking: an apple, cooked chicken, a potion, a bowl of stew, a bucket of milk. */
    static void filmEat(String name) {
        if (!wanted(name)) return;
        Minecraft mc = Minecraft.getInstance();
        String[] food = {"apple", "cooked_chicken", "potion{Potion:\"minecraft:healing\"}", "mushroom_stew", "milk_bucket"};
        add(t -> {
            var o = mc.options;
            if (t == 0) {
                o.setCameraType(CameraType.FIRST_PERSON);
                cmd("gamemode survival");
                cmd("kill @e[type=!player]");
                cmd("effect give @s minecraft:hunger 3 255 true");
                cmd("tp @s 40 -60 30 0 10");
                yaw = 0f;
                pitch = 10f;
            }
            int f = t - 60;
            if (f == 0) {
                slowClock(450);
                filmName = name;
                filmFrame = 0;
                filmNext = Motion.ticks;
            }
            int each = 60, i = f / each, g = f % each;
            if (f >= 0 && i < food.length) {
                if (g == 0) give(food[i]);
                if (g == 8) o.keyUse.setDown(true);
                if (g == 50) o.keyUse.setDown(false);
            }
            if (f == each * food.length) {
                filmName = null;
                slowClock(50);
                cmd("gamemode creative");
            }
            return f > each * food.length;
        });
    }

    /** Hold the use key (eat, drink, draw a bow) and take a shot partway. */
    static void use(String name, String item, int at) {
        if (!wanted(name)) return;
        Minecraft mc = Minecraft.getInstance();
        add(t -> {
            if (t == 0) {
                mc.options.setCameraType(CameraType.FIRST_PERSON);
                give(item);
            }
            if (t == 10) mc.options.keyUse.setDown(true);
            if (t == 10 + at) shot(name);
            if (t == 11 + at) mc.options.keyUse.setDown(false);
            return t > 30 + at;
        });
    }

    static void tpSwing(String name, String item, int at) {
        if (!wanted(name)) return;
        Minecraft mc = Minecraft.getInstance();
        add(t -> {
            if (t == 0) {
                mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT);
                give(item);
            }
            if (t == 12) {
                Motion.pending = Motion.Action.ATTACK;
                mc.player.swing(InteractionHand.MAIN_HAND);
            }
            if (t == 13) com.lifelikemotion.client.body.BodyAnimator.testAttack = at / 6f;
            if (t == 18) shot(name);
            if (t == 19) com.lifelikemotion.client.body.BodyAnimator.testAttack = null;
            return t > 24;
        });
    }

    /** Walk / run / jump for a while and take a shot. */
    static void move(String name, String item, boolean forward, boolean sprint, boolean jump, int at, CameraType cam) {
        if (!wanted(name)) return;
        Minecraft mc = Minecraft.getInstance();
        add(t -> {
            if (t == 0) {
                mc.options.setCameraType(cam);
                give(item);
                cmd("tp @s 0 -60 -12 0 10");
            }
            if (t == 10) {
                mc.options.keyUp.setDown(forward);
                mc.options.keySprint.setDown(sprint);
                if (sprint) mc.player.setSprinting(true);
                mc.options.keyJump.setDown(jump);
            }
            if (t == 10 + at) shot(name);
            if (t == 11 + at) {
                mc.options.keyUp.setDown(false);
                mc.options.keySprint.setDown(false);
                mc.options.keyJump.setDown(false);
                mc.player.setSprinting(false);
            }
            return t > 30 + at;
        });
    }

    static void add(Step s) {
        STEPS.add(s);
    }

    static void give(String item) {
        Minecraft mc = Minecraft.getInstance();
        String id = item.contains("{") ? item.substring(0, item.indexOf('{')) : item;  // "potion{Potion:...}" = id + nbt
        ItemStack stack = id.equals("air") ? ItemStack.EMPTY
                : new ItemStack(BuiltInRegistries.ITEM.get(new ResourceLocation("minecraft", id)));
        mc.player.getInventory().selected = 0;
        cmd("item replace entity @s weapon.mainhand with minecraft:" + (stack.isEmpty() ? "air" : item));
    }

    static void shot(String name) {
        Minecraft mc = Minecraft.getInstance();
        if (BASELINE) name = "baseline_" + name;
        String file = String.format("%03d_%s.png", ++shotNo, name);
        Screenshot.grab(mc.gameDirectory, file, mc.getMainRenderTarget(), c -> {});
    }

    static void cmd(String command) {
        Minecraft mc = Minecraft.getInstance();
        IntegratedServer server = mc.getSingleplayerServer();
        if (server == null || mc.player == null) return;
        var id = mc.player.getUUID();
        server.execute(() -> {
            var sp = server.getPlayerList().getPlayer(id);
            if (sp == null) return;
            server.getCommands().performPrefixedCommand(sp.createCommandSourceStack().withPermission(4).withSuppressedOutput(), command);
        });
    }
}
