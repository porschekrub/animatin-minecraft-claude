package com.lifelikemotion.client;

import net.minecraft.world.item.*;
import net.minecraftforge.client.extensions.common.IClientItemExtensions;

/** What kind of thing is in the hand: decides how it is held and swung. */
public enum ItemKind {
    EMPTY, SWORD, AXE, PICKAXE, SHOVEL, HOE, BLOCK, FOOD, DRINK, LIGHT, ROD, THROWABLE, OTHER,
    /** drawn by the game itself (bows, crossbows, maps, shields, tridents, spyglasses, horns, brushes, modded renderers) */
    SPECIAL;

    public static ItemKind of(ItemStack s) {
        if (s.isEmpty()) return EMPTY;
        Item i = s.getItem();
        if (i instanceof ProjectileWeaponItem || i instanceof TridentItem || i instanceof MapItem || i instanceof ShieldItem
                || i instanceof SpyglassItem || i instanceof InstrumentItem || i instanceof BrushItem || i instanceof ComplexItem
                || IClientItemExtensions.of(s) != IClientItemExtensions.DEFAULT)
            return SPECIAL;
        if (i instanceof SwordItem) return SWORD;
        if (i instanceof AxeItem) return AXE;
        if (i instanceof PickaxeItem) return PICKAXE;
        if (i instanceof ShovelItem) return SHOVEL;
        if (i instanceof HoeItem) return HOE;
        UseAnim ua = s.getUseAnimation();
        if (ua == UseAnim.DRINK) return DRINK;
        if (ua == UseAnim.EAT || s.isEdible()) return FOOD;
        if (i instanceof FishingRodItem || i instanceof FoodOnAStickItem<?>) return ROD;
        if (i instanceof SnowballItem || i instanceof EggItem || i instanceof EnderpearlItem || i instanceof ThrowablePotionItem
                || i instanceof ExperienceBottleItem || i instanceof FireChargeItem)
            return THROWABLE;
        if (i instanceof BlockItem bi) {
            var b = bi.getBlock();
            if (b instanceof net.minecraft.world.level.block.TorchBlock || b instanceof net.minecraft.world.level.block.LanternBlock
                    || b instanceof net.minecraft.world.level.block.EndRodBlock)
                return LIGHT;
            return BLOCK;
        }
        if (i instanceof TieredItem || i instanceof ShearsItem || i instanceof FlintAndSteelItem) return PICKAXE;
        return OTHER;
    }

    public boolean tool() {
        return this == SWORD || this == AXE || this == PICKAXE || this == SHOVEL || this == HOE || this == ROD;
    }
}
