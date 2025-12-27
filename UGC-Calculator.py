bl_info = {
    "name": "Rec Room Calculator",
    "author": "blueasis & snowfall",
    "version": (0, 0, 2),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > RR Avatar Calc",
    "description": "Calculates triangle budgets and price for Rec Room Avatar Studio",
    "category": "3D View",
}

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    StringProperty,
)

# ----------------------------
# Data
# ----------------------------

POLY = {
    "BELT": {"LOD0": 1000, "LOD1": 650, "LOD2": 250},
    "EAR": {"LOD0": 750, "LOD1": 475, "LOD2": 150},
    "EYE": {"LOD0": 1000, "LOD1": 650, "LOD2": 250},
    "HAIR": {"LOD0": 1300, "LOD1": 850, "LOD2": 250},
    "HAT": {"LOD0": 1000, "LOD1": 650, "LOD2": 250},
    "LEG": {"LOD0": 2500, "LOD1": 1650, "LOD2": 625},
    "MOUTH": {"LOD0": 750, "LOD1": 475, "LOD2": 150},
    "NECK": {"LOD0": 1000, "LOD1": 650, "LOD2": 250},
    "SHOE": {"LOD0": 2000, "LOD1": 1300, "LOD2": 500},
    "SHOULDER": {"LOD0": 1000, "LOD1": 650, "LOD2": 250},
    "WRIST": {"LOD0": 3000, "LOD1": 2000, "LOD2": 600},
}

TORSO_FB = {"LOD0": 3000, "LOD1": 2000, "LOD2": 750}
TORSO_MB = {"LOD0": 2200, "LOD1": 1500, "LOD2": 500}

BASE_PRICES = {
    "BELT": 700,
    "EAR": 500,
    "EYE": 500,
    "HAIR": 350,
    "HAT": 800,
    "LEG": 800,
    "MOUTH": 350,
    "NECK": 500,
    "SHOE": 800,
    "SHOULDER": 1000,
    "WRIST": 700,
    "TORSO": 1000,
}

FEATURED_MINIMUMS = {
    "BELT": 1400,
    "EAR": 1000,
    "EYE": 1000,
    "HAIR": 700,
    "HAT": 1600,
    "LEG": 1600,
    "MOUTH": 700,
    "NECK": 1000,
    "SHOE": 1600,
    "SHOULDER": 2000,
    "WRIST": 1400,
    "TORSO": 2000,
}

# ----------------------------
# Calculation
# ----------------------------

def _recalc(state) -> dict:
    torso_checked = bool(state.item_TORSO)

    fb = {"LOD0": 0, "LOD1": 0, "LOD2": 0}
    mb = {"LOD0": 0, "LOD1": 0, "LOD2": 0}
    base_total = 0
    featured_floor = 0
    material_count = 0

    for key in ("BELT", "EAR", "EYE", "HAIR", "HAT", "LEG", "MOUTH", "NECK", "SHOE", "SHOULDER", "WRIST", "TORSO"):
        if not getattr(state, f"item_{key}", False):
            continue

        base_total += BASE_PRICES.get(key, 0)
        featured_floor += FEATURED_MINIMUMS.get(key, 0)

        # Material count
        if key in ("HAIR", "EYE", "MOUTH"):
            material_count += 2
        else:
            material_count += 1

        if key == "TORSO":
            for lod in fb:
                fb[lod] += TORSO_FB[lod]
                mb[lod] += TORSO_MB[lod]
        else:
            for lod in fb:
                fb[lod] += POLY[key][lod]
                mb[lod] += POLY[key][lod]

    mult = 1.0

    if state.mod_emissive: mult *= 2.0
    if state.mod_fancy: mult *= 1.6
    if state.mod_gold: mult *= 1.1
    if state.mod_helmet: mult *= 2.0
    if state.mod_high_fidelity: mult *= 1.2
    if state.mod_animated: mult *= 2.4
    if state.mod_novelty: mult *= 1.6
    if state.mod_shiny: mult *= 1.4
    if state.mod_elevated_shoe: mult *= 1.8

    final_price = int(round(base_total * mult))
    if state.featured_pricing and final_price < featured_floor:
        final_price = int(featured_floor)

    return {
        "fb": fb,
        "mb": mb,
        "base_total": base_total,
        "featured_floor": featured_floor,
        "mult": mult,
        "final_price": final_price,
        "torso_checked": torso_checked,
        "material_count": material_count
    }

def _apply_preset(state, preset_value: str):
    for key in ("BELT", "EAR", "EYE", "HAIR", "HAT", "LEG", "MOUTH", "NECK", "SHOE", "SHOULDER", "WRIST", "TORSO"):
        setattr(state, f"item_{key}", False)

    if preset_value in ("", "none"):
        return

    def enable(keys):
        for k in keys:
            setattr(state, f"item_{k}", True)

    if preset_value == "onesie":
        enable(["TORSO", "LEG"])
    elif preset_value == "model":
        enable(["TORSO", "LEG", "SHOE", "WRIST", "HAT"])
    elif preset_value == "hairtris":
        enable(["HAIR", "EAR"])
    elif preset_value == "hqhelmet":
        enable(["EAR", "EYE", "HAIR", "HAT"])

# ----------------------------
# Easter egg flair animation
# ----------------------------

_EASTER_EGG_PRICE = 653997
_dance_timer_running = False
_dance_toggle = False

def _tag_redraw_all_view3d_safe():
    wm = bpy.context.window_manager
    if not wm: return
    for win in wm.windows:
        screen = win.screen
        if not screen: continue
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

def _dance_timer():
    global _dance_timer_running, _dance_toggle

    wm = bpy.context.window_manager
    if not wm or not wm.windows:
        _dance_timer_running = False
        return None

    scene = wm.windows[0].scene
    if not scene or not hasattr(scene, "rr_calc_state"):
        _dance_timer_running = False
        return None

    state = scene.rr_calc_state
    calc = _recalc(state)

    if calc["final_price"] == _EASTER_EGG_PRICE:
        _dance_toggle = not _dance_toggle
        state.flair_text = "╰(*°▽°*)╮" if _dance_toggle else "╭(*°▽°*)╯"
        _tag_redraw_all_view3d_safe()
        return 0.25

    state.flair_text = "╰(*°▽°*)╯"
    _tag_redraw_all_view3d_safe()
    _dance_timer_running = False
    return None

def _ensure_dance_timer_running():
    global _dance_timer_running
    if _dance_timer_running: return
    _dance_timer_running = True
    bpy.app.timers.register(_dance_timer, first_interval=0.25)

# ----------------------------
# Addon Preferences (Advanced Mode)
# ----------------------------

class RRCalcPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    advanced_mode: BoolProperty(
        name="Advanced Mode",
        default=False,
        description="Show extra info like base/multiplier and material count"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "advanced_mode")

# ----------------------------
# Properties
# ----------------------------

def _preset_items():
    return [
        ("", "Presets", "Choose a preset"),
        ("none", "None", "Clear selection"),
        ("onesie", "Onesie", "Enable Torso + Leg"),
        ("model", "Model Replacement", "Enable Torso + Leg + Shoe + Wrist + Hat"),
        ("hairtris", "Plz give more tris for hair", "Enable Hair + Ear"),
        ("hqhelmet", "HQ Helmet", "Enable Ear + Eye + Hair + Hat"),
    ]

def _on_preset_changed(self, context):
    _apply_preset(self, self.preset)

class RRCalcState(bpy.types.PropertyGroup):
    preset: EnumProperty(
        name="Preset",
        items=_preset_items(),
        default="",
        update=_on_preset_changed,
    )

    item_BELT: BoolProperty(name="Belt", default=False)
    item_EAR: BoolProperty(name="Ear", default=False)
    item_EYE: BoolProperty(name="Eye / Glasses", default=False)
    item_HAIR: BoolProperty(name="Hair", default=False)
    item_HAT: BoolProperty(name="Hat / Headwear", default=False)
    item_LEG: BoolProperty(name="Leg / Pants", default=False)
    item_MOUTH: BoolProperty(name="Mouth / Beard / Face", default=False)
    item_NECK: BoolProperty(name="Neck", default=False)
    item_SHOE: BoolProperty(name="Shoe / Feet", default=False)
    item_SHOULDER: BoolProperty(name="Shoulder / Back", default=False)
    item_TORSO: BoolProperty(name="Torso / Shirt", default=False)
    item_WRIST: BoolProperty(
        name="Wrist / Hands",
        default=False,
        description="Polygon budgets shown are for both hands combined. Each hand is half of the displayed value.",
    )

    featured_pricing: BoolProperty(
        name="Featured Pricing",
        default=False,
        description="Clamp the price to match featured minimums so your item is priced correctly.",
    )

    mod_emissive: BoolProperty(name="Emissive ×2", default=False)
    show_optional_mods: BoolProperty(name="Optional modifiers", default=False)

    mod_fancy: BoolProperty(name="Fancy ×1.6", default=False)
    mod_gold: BoolProperty(name="Gold ×1.1", default=False)
    mod_helmet: BoolProperty(name="Helmet ×2", default=False)
    mod_high_fidelity: BoolProperty(name="High Fidelity ×1.2", default=False)
    mod_animated: BoolProperty(name="Animated ×2.4", default=False)
    mod_novelty: BoolProperty(name="Novelty ×1.6", default=False)
    mod_shiny: BoolProperty(name="Shiny ×1.4", default=False)
    mod_elevated_shoe: BoolProperty(name="Elevated Shoe ×1.8", default=False)

    flair_text: StringProperty(
        name="Flair",
        default="╰(*°▽°*)╯",
        options={'SKIP_SAVE'},
    )

# ----------------------------
# UI Panel
# ----------------------------

class VIEW3D_PT_rr_calc(bpy.types.Panel):
    bl_label = "RR Avatar Calc"
    bl_idname = "VIEW3D_PT_rr_calc"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RR Avatar Calc"

    def draw(self, context):
        layout = self.layout
        state = context.scene.rr_calc_state
        addon_prefs = context.preferences.addons[__name__].preferences
        calc = _recalc(state)

        # Start/stop easter egg dance
        if calc["final_price"] == _EASTER_EGG_PRICE:
            _ensure_dance_timer_running()
        else:
            if state.flair_text != "╰(*°▽°*)╯":
                state.flair_text = "╰(*°▽°*)╯"

        # Items
        box_items = layout.box()
        row = box_items.row(align=True)
        row.label(text="Avatar Items")
        row.prop(state, "preset", text="")

        col = box_items.column(align=True)
        for prop in ["item_BELT","item_EAR","item_EYE","item_HAIR","item_HAT",
                     "item_LEG","item_MOUTH","item_NECK","item_SHOE","item_SHOULDER",
                     "item_TORSO","item_WRIST"]:
            col.prop(state, prop)

        # Modifiers
        box_mod = layout.box()
        box_mod.label(text="Price Modifiers")
        req = box_mod.column(align=True)
        req.prop(state, "featured_pricing")
        req.prop(state, "mod_emissive")
        box_mod.prop(state, "show_optional_mods", toggle=True)
        if state.show_optional_mods:
            colm = box_mod.column(align=True)
            for prop in ["mod_fancy","mod_gold","mod_helmet","mod_high_fidelity",
                         "mod_animated","mod_novelty","mod_shiny","mod_elevated_shoe"]:
                colm.prop(state, prop)

        # Mascot / easter egg above totals
        row = layout.row()
        row.alignment = 'CENTER'
        row.enabled = False
        row.label(text=state.flair_text)

        # Totals row
        totals_row = layout.row(align=True)
        box_tot = totals_row.box()
        box_tot.label(text="Full Body" if calc["torso_checked"] else "Triangles")
        colfb = box_tot.column(align=True)
        for lod in ["LOD0","LOD1","LOD2"]:
            colfb.label(text=f"{lod}: {calc['fb'][lod]}")

        if calc["torso_checked"]:
            box_mb = totals_row.box()
            box_mb.label(text="Bean Body")
            colmb = box_mb.column(align=True)
            for lod in ["LOD0","LOD1","LOD2"]:
                colmb.label(text=f"{lod}: {calc['mb'][lod]}")

        # Material count (Advanced Mode)
        if addon_prefs.advanced_mode:
            box_mat = layout.box()
            box_mat.label(text=f"Materials: {calc['material_count']}")

        # Price box
        box_price = layout.box()
        box_price.label(text=f"Price: {calc['final_price']}")
        if addon_prefs.advanced_mode:
            sub = box_price.column(align=True)
            sub.enabled = False
            sub.label(text=f"Base: {calc['base_total']}  Mult: {calc['mult']:.3g}")
            if state.featured_pricing:
                sub.label(text=f"Featured floor: {calc['featured_floor']}")

# ----------------------------
# Register / Unregister
# ----------------------------

classes = (
    RRCalcPreferences,
    RRCalcState,
    VIEW3D_PT_rr_calc,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.rr_calc_state = bpy.props.PointerProperty(type=RRCalcState)

def unregister():
    global _dance_timer_running
    _dance_timer_running = False

    if hasattr(bpy.types.Scene, "rr_calc_state"):
        del bpy.types.Scene.rr_calc_state

    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
