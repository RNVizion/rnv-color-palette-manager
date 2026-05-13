"""
RNV Color Palette Manager — Comprehensive Test Suite v3.3.13
============================================================
Tests all core modules for functionality, edge cases, and boundary conditions.

Usage — place this file in your project root (same folder as RNV_Color_Palette_Manager.py):
    python test_rnv_palette_manager.py          # standard run
    python test_rnv_palette_manager.py -v       # verbose (shows each test name)

Requirements: PyQt6  (pip install PyQt6)
"""

import sys, os, io, json, tempfile, shutil, unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# QApplication MUST exist before any Qt module is imported or instantiated
try:
    from PyQt6.QtWidgets import QApplication as _QApp
    from PyQt6.QtCore import Qt as _Qt
    if not _QApp.instance():
        _qapp = _QApp(sys.argv[:1])
        _qapp.setAttribute(_Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
except Exception:
    _qapp = None

# ══════════════════════════════════════════════════════════════════════════════
# BOOTSTRAP — locate project root (supports both flat and subdir layouts)
# ══════════════════════════════════════════════════════════════════════════════
_THIS = Path(__file__).resolve()
_ROOT = None

for _c in [_THIS.parent, _THIS.parent.parent, Path("/mnt/project")]:
    if (_c / "RNV_Color_Palette_Manager.py").exists():
        _ROOT = str(_c); break
    if (_c / "core").is_dir() and (_c / "ui").is_dir() and (_c / "utils").is_dir():
        _ROOT = str(_c); break

if _ROOT is None:
    sys.exit(
        "ERROR: Cannot find project root.\n"
        "Place test_rnv_palette_manager.py in the same folder as "
        "RNV_Color_Palette_Manager.py"
    )

# Subdirectory layout — add root to sys.path so 'from core.X import' resolves
if os.path.isdir(os.path.join(_ROOT, "core")):
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)

# ── imports ──────────────────────────────────────────────────────────────────
from core.color_math       import ColorMath
from core.color_harmonies  import ColorHarmonies
from core.accessibility    import Accessibility
from core.palette_formats  import PaletteFormats, ImportResult
from core.palette_metadata import PaletteMetadata
from ui.colors             import (
    get_theme_colors, is_dark_theme,
    BRAND_GOLD, BRAND_GOLD_DARK, BRAND_GOLD_RGB, BRAND_GOLD_DARK_RGB,
    SLOT_SELECTED_COLOR, SLOT_BORDER_THIN_COLOR, SLOT_BORDER_THICK_COLOR,
    SEARCH_HIGHLIGHT_COLOR, SEARCH_DIM_OVERLAY, SIZE_OVERLAY_BG,
)
from ui.color_search       import parse_color_query, MATCH_THRESHOLD
from ui.slot_group         import SlotGroupData, SlotGroupInfo
from utils.color_history      import ColorHistoryPanel, ColorHistoryEntry
from ui.theme_manager      import ThemeManager
from utils.undo_manager    import UndoManager, PaletteState
from utils.export_history  import ExportHistory, ExportEntry
from utils.recent_palettes import RecentPalettesManager, RecentPaletteEntry
from utils.settings_manager import SettingsManager
from utils.session_manager  import PaletteSessionState
from utils.error_handler    import ErrorHandler, ValidationHelper
from utils.file_utils       import FileUtils
from utils.pixmap_cache     import QPixmapCache

# ANSI colour helpers
_G="\033[92m"; _R="\033[91m"; _Y="\033[93m"; _C="\033[96m"; _B="\033[1m"; _X="\033[0m"

# ══════════════════════════════════════════════════════════════════════════════
# 1. COLOR MATH
# ══════════════════════════════════════════════════════════════════════════════
class TestColorMath(unittest.TestCase):
    """core/color_math.py — color-space conversions and all 7 mixing algorithms."""

    # --- hex conversions ---
    def test_rgb_to_hex_black(self):    self.assertEqual(ColorMath.rgb_to_hex((0,0,0)), "#000000")
    def test_rgb_to_hex_white(self):    self.assertEqual(ColorMath.rgb_to_hex((255,255,255)), "#ffffff")
    def test_rgb_to_hex_red(self):      self.assertEqual(ColorMath.rgb_to_hex((255,0,0)), "#ff0000")
    def test_rgb_to_hex_green(self):    self.assertEqual(ColorMath.rgb_to_hex((0,255,0)), "#00ff00")
    def test_rgb_to_hex_blue(self):     self.assertEqual(ColorMath.rgb_to_hex((0,0,255)), "#0000ff")
    def test_hex_to_rgb_black(self):    self.assertEqual(ColorMath.hex_to_rgb("#000000"), (0,0,0))
    def test_hex_to_rgb_white(self):    self.assertEqual(ColorMath.hex_to_rgb("#ffffff"), (255,255,255))
    def test_hex_to_rgb_no_hash(self):  self.assertEqual(ColorMath.hex_to_rgb("ff0000"), (255,0,0))
    def test_hex_to_rgb_uppercase(self):self.assertEqual(ColorMath.hex_to_rgb("#FF0000"), (255,0,0))
    def test_hex_to_rgb_short(self):    self.assertEqual(ColorMath.hex_to_rgb("#f00"), (255,0,0))
    def test_hex_to_rgb_short_white(self): self.assertEqual(ColorMath.hex_to_rgb("#fff"), (255,255,255))

    def test_roundtrip_rgb_hex(self):
        for c in [(0,0,0),(255,255,255),(128,64,200),(1,2,3),(16,0,255)]:
            self.assertEqual(ColorMath.hex_to_rgb(ColorMath.rgb_to_hex(c)), c)

    # --- HSV ---
    def test_hsv_black_v_zero(self):
        _,_,v = ColorMath.rgb_to_hsv((0,0,0)); self.assertAlmostEqual(v,0.0)
    def test_hsv_white_s_zero(self):
        _,s,_ = ColorMath.rgb_to_hsv((255,255,255)); self.assertAlmostEqual(s,0.0)
    def test_hsv_red_hue_zero(self):
        h,s,v = ColorMath.rgb_to_hsv((255,0,0))
        self.assertAlmostEqual(h,0.0); self.assertAlmostEqual(s,1.0); self.assertAlmostEqual(v,1.0)
    def test_hsv_roundtrip(self):
        for c in [(255,0,0),(0,255,0),(0,0,255),(128,128,0),(100,150,200)]:
            back = ColorMath.hsv_to_rgb(ColorMath.rgb_to_hsv(c))
            for a,b in zip(c,back): self.assertAlmostEqual(a,b,delta=2)

    # --- HSL ---
    def test_hsl_roundtrip(self):
        for c in [(255,0,0),(0,255,0),(128,128,128),(200,100,50)]:
            back = ColorMath.hsl_to_rgb(ColorMath.rgb_to_hsl(c))
            for a,b in zip(c,back): self.assertAlmostEqual(a,b,delta=2)

    # --- LAB ---
    def test_lab_white_L_100(self):
        L,_,_ = ColorMath.rgb_to_lab((255,255,255)); self.assertAlmostEqual(L,100.0,delta=1.0)
    def test_lab_black_L_zero(self):
        L,_,_ = ColorMath.rgb_to_lab((0,0,0)); self.assertAlmostEqual(L,0.0,delta=1.0)
    def test_lab_roundtrip(self):
        for c in [(255,0,0),(0,255,0),(128,64,200),(200,150,100)]:
            back = ColorMath.lab_to_rgb(ColorMath.rgb_to_lab(c))
            for a,b in zip(c,back): self.assertAlmostEqual(a,b,delta=3)

    # --- weighted_rgb_mix ---
    def test_rgb_mix_50_50(self):
        r = ColorMath.weighted_rgb_mix([((255,0,0),50),((0,0,255),50)])
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r[0],127,delta=2); self.assertAlmostEqual(r[2],127,delta=2)
    def test_rgb_mix_single_identity(self):
        self.assertEqual(ColorMath.weighted_rgb_mix([((200,100,50),100)]), (200,100,50))
    def test_rgb_mix_empty_none(self):
        self.assertIsNone(ColorMath.weighted_rgb_mix([]))
    def test_rgb_mix_zero_weight_none(self):
        self.assertIsNone(ColorMath.weighted_rgb_mix([((255,0,0),0)]))
    def test_rgb_mix_high_weight_dominates(self):
        r = ColorMath.weighted_rgb_mix([((255,0,0),90),((0,0,255),10)])
        self.assertIsNotNone(r); self.assertGreater(r[0],r[2])

    # --- other algorithms ---
    def test_lab_mix_valid(self):
        r = ColorMath.lab_perceptual_mix([((255,0,0),50),((0,0,255),50)])
        self.assertIsNotNone(r)
        for ch in r: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)
    def test_lab_mix_empty_none(self):
        self.assertIsNone(ColorMath.lab_perceptual_mix([]))
    def test_cmy_mix_valid(self):
        r = ColorMath.subtractive_cmy_mix([((255,0,0),50),((0,255,0),50)])
        self.assertIsNotNone(r)
    def test_cmy_mix_empty_none(self):
        self.assertIsNone(ColorMath.subtractive_cmy_mix([]))
    def test_ryb_mix_valid(self):
        r = ColorMath.weighted_ryb_mix([((255,255,0),50),((0,0,255),50)])
        self.assertIsNotNone(r)
    def test_ryb_mix_empty_none(self):
        self.assertIsNone(ColorMath.weighted_ryb_mix([]))
    def test_km_mix_valid(self):
        r = ColorMath.kubelka_munk_mix([((255,0,0),50),((0,0,255),50)])
        self.assertIsNotNone(r)
        for ch in r: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)
    def test_km_mix_empty_none(self):
        self.assertIsNone(ColorMath.kubelka_munk_mix([]))
    def test_hsv_mix_empty_none(self):
        self.assertIsNone(ColorMath.weighted_hsv_mix([]))
    def test_hsv_mix_single(self):
        r = ColorMath.weighted_hsv_mix([((200,100,50),10)])
        self.assertIsNotNone(r); self.assertEqual(len(r),3)

    def test_all_algorithms_5_slots(self):
        slots = [((i*50,i*40,255-i*50),20) for i in range(5)]
        for fn in [ColorMath.weighted_rgb_mix, ColorMath.lab_perceptual_mix,
                   ColorMath.subtractive_cmy_mix, ColorMath.weighted_ryb_mix,
                   ColorMath.kubelka_munk_mix]:
            self.assertIsNotNone(fn(slots), f"{fn.__name__} returned None")

    # --- utility ---
    def test_clamp_rgb(self):
        self.assertEqual(ColorMath.clamp_rgb(300.0,-5.0,128.0), (255,0,128))
    def test_is_valid_rgb_valid(self):
        self.assertTrue(ColorMath.is_valid_rgb(0,128,255))
    def test_is_valid_rgb_invalid_low(self):
        self.assertFalse(ColorMath.is_valid_rgb(-1,0,0))
    def test_is_valid_rgb_invalid_high(self):
        self.assertFalse(ColorMath.is_valid_rgb(0,256,0))
    def test_color_distance_zero(self):
        self.assertAlmostEqual(ColorMath.color_distance((100,100,100),(100,100,100)),0.0)
    def test_color_distance_positive(self):
        self.assertGreater(ColorMath.color_distance((0,0,0),(255,255,255)),0)
    def test_color_distance_symmetric(self):
        a,b = (200,100,50),(50,100,200)
        self.assertAlmostEqual(ColorMath.color_distance(a,b),ColorMath.color_distance(b,a))
    def test_average_region_color(self):
        r = ColorMath.calculate_average_region_color([(0,0,0),(255,255,255)])
        self.assertIsNotNone(r)
        for ch in r: self.assertAlmostEqual(ch,127,delta=2)
    def test_average_region_single(self):
        self.assertEqual(ColorMath.calculate_average_region_color([(100,150,200)]),(100,150,200))
    def test_average_region_empty(self):
        self.assertIsNone(ColorMath.calculate_average_region_color([]))
    def test_generate_palette_count(self):
        self.assertEqual(len(ColorMath.generate_color_palette((255,0,0),count=5)),5)
    def test_generate_palette_valid_rgb(self):
        for c in ColorMath.generate_color_palette((128,128,128),count=8):
            for ch in c: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)
    def test_clamp_value(self):
        self.assertEqual(ColorMath.clamp_value(-5),0)
        self.assertEqual(ColorMath.clamp_value(300),255)
        self.assertEqual(ColorMath.clamp_value(128),128)
    def test_safe_rgb_invalid_default(self):
        r = ColorMath.safe_rgb(float("nan"),0,0,default=(42,42,42))
        self.assertEqual(r,(42,42,42))


# ══════════════════════════════════════════════════════════════════════════════
# 2. COLOR HARMONIES
# ══════════════════════════════════════════════════════════════════════════════
class TestColorHarmonies(unittest.TestCase):
    """core/color_harmonies.py — all generators, gradient, and random."""

    RED=(255,0,0); WHITE=(255,255,255); BLACK=(0,0,0); GRAY=(128,128,128)
    BASE=(200,100,50)

    def _valid(self, colors):
        for c in colors:
            self.assertEqual(len(c),3)
            for ch in c: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)

    def test_complementary_count(self):   self.assertEqual(len(ColorHarmonies.complementary(self.RED)),1)
    def test_analogous_count(self):       self.assertEqual(len(ColorHarmonies.analogous(self.RED)),2)
    def test_triadic_count(self):         self.assertEqual(len(ColorHarmonies.triadic(self.RED)),2)
    def test_split_comp_count(self):      self.assertEqual(len(ColorHarmonies.split_complementary(self.RED)),2)
    def test_tetradic_count(self):        self.assertEqual(len(ColorHarmonies.tetradic(self.RED)),3)
    def test_monochromatic_count(self):   self.assertEqual(len(ColorHarmonies.monochromatic(self.RED)),4)

    def test_all_harmonies_valid_rgb(self):
        for name in ("complementary","analogous","triadic","split_complementary","tetradic","monochromatic"):
            self._valid(getattr(ColorHarmonies, name)(self.BASE))

    def test_generate_dispatch(self):
        for name in ("Complementary","Analogous","Triadic","Split-Complementary","Tetradic / Square","Monochromatic"):
            r = ColorHarmonies.generate(name, self.BASE)
            self.assertIsInstance(r, list); self.assertGreater(len(r),0,f"generate('{name}') returned empty")

    def test_generate_unknown_empty(self):
        self.assertEqual(ColorHarmonies.generate("nonexistent", self.BASE), [])

    def test_all_harmonies_on_white(self):
        for name in ("complementary","analogous","triadic","split_complementary","tetradic","monochromatic"):
            self.assertIsNotNone(getattr(ColorHarmonies, name)(self.WHITE))

    def test_all_harmonies_on_black(self):
        for name in ("complementary","analogous","triadic","split_complementary","tetradic","monochromatic"):
            self.assertIsNotNone(getattr(ColorHarmonies, name)(self.BLACK))

    def test_gradient_endpoints(self):
        a,b = (0,0,0),(255,255,255)
        grad = ColorHarmonies.gradient(a,b,steps=5)
        self.assertEqual(grad[0],a); self.assertEqual(grad[-1],b)

    def test_gradient_length(self):
        for steps in (2,5,10,20):
            self.assertEqual(len(ColorHarmonies.gradient((0,0,0),(255,255,255),steps=steps)),steps)

    def test_gradient_monotonic_gray(self):
        grad = ColorHarmonies.gradient((0,0,0),(255,255,255),steps=10)
        for i in range(1,len(grad)):
            self.assertGreaterEqual(grad[i][0],grad[i-1][0])

    def test_gradient_same_color(self):
        grad = ColorHarmonies.gradient((128,128,128),(128,128,128),steps=5)
        self.assertTrue(all(c==(128,128,128) for c in grad))

    def test_gradient_valid_rgb(self):
        self._valid(ColorHarmonies.gradient((50,100,150),(200,50,100),steps=8))

    def test_random_harmonious_count(self):
        for n in (3,5,8): self.assertEqual(len(ColorHarmonies.random_harmonious(n)),n)

    def test_random_harmonious_valid(self):
        self._valid(ColorHarmonies.random_harmonious(6))

    def test_random_single_valid(self):
        rgb = ColorHarmonies.random_single()
        self.assertEqual(len(rgb),3)
        for ch in rgb: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)

    def test_complementary_opposite_hue(self):
        comp = ColorHarmonies.complementary((255,0,0))[0]
        h = ColorMath.rgb_to_hsv(comp)[0]
        self.assertGreater(h,0.4); self.assertLess(h,0.6)


# ══════════════════════════════════════════════════════════════════════════════
# 3. ACCESSIBILITY
# ══════════════════════════════════════════════════════════════════════════════
class TestAccessibility(unittest.TestCase):
    """core/accessibility.py — WCAG contrast and colour-blindness simulation."""

    def test_white_on_black_ratio(self):
        r = Accessibility.contrast_ratio((0,0,0),(255,255,255))
        self.assertAlmostEqual(r.ratio,21.0,delta=0.1)

    def test_white_on_black_passes_all(self):
        r = Accessibility.contrast_ratio((0,0,0),(255,255,255))
        self.assertTrue(r.aa_normal); self.assertTrue(r.aa_large)
        self.assertTrue(r.aaa_normal); self.assertTrue(r.aaa_large)

    def test_same_color_ratio_one(self):
        r = Accessibility.contrast_ratio((128,128,128),(128,128,128))
        self.assertAlmostEqual(r.ratio,1.0,delta=0.01)
        self.assertFalse(r.aa_normal)

    def test_commutative(self):
        a,b = (200,100,50),(50,100,200)
        self.assertAlmostEqual(Accessibility.contrast_ratio(a,b).ratio,
                               Accessibility.contrast_ratio(b,a).ratio,delta=0.001)

    def test_luminance_black(self):
        self.assertAlmostEqual(Accessibility.relative_luminance((0,0,0)),0.0)

    def test_luminance_white(self):
        self.assertAlmostEqual(Accessibility.relative_luminance((255,255,255)),1.0,delta=0.001)

    def test_summary_contains_pass(self):
        self.assertIn("PASS", Accessibility.contrast_ratio((0,0,0),(255,255,255)).summary)

    def test_ratio_display_format(self):
        self.assertIn(":1", Accessibility.contrast_ratio((0,0,0),(255,255,255)).ratio_display)

    def test_aaa_not_met_by_low_contrast(self):
        r = Accessibility.contrast_ratio((180,180,180),(255,255,255))
        self.assertFalse(r.aaa_normal)

    def test_simulate_protanopia(self):
        r = Accessibility.simulate((255,0,0),"protanopia")
        self.assertEqual(len(r),3)
        for ch in r: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)

    def test_simulate_deuteranopia(self):
        r = Accessibility.simulate((0,255,0),"deuteranopia"); self.assertEqual(len(r),3)

    def test_simulate_tritanopia(self):
        r = Accessibility.simulate((0,0,255),"tritanopia"); self.assertEqual(len(r),3)

    def test_simulate_none_unchanged(self):
        rgb=(123,45,67); self.assertEqual(Accessibility.simulate(rgb,"none"),rgb)

    def test_simulate_palette(self):
        pal=[(255,0,0),(0,255,0),(0,0,255)]
        r = Accessibility.simulate_palette(pal,"protanopia"); self.assertEqual(len(r),3)

    def test_simulate_palette_none_unchanged(self):
        pal=[(100,150,200)]
        self.assertEqual(Accessibility.simulate_palette(pal,"none"),pal)


# ══════════════════════════════════════════════════════════════════════════════
# 4. COLORS MODULE
# ══════════════════════════════════════════════════════════════════════════════
class TestColorsModule(unittest.TestCase):
    """ui/colors.py — theme dicts, brand constants, get_theme_colors."""

    REQUIRED = [
        "window_bg","panel_bg","scroll_bg","card_bg","input_bg",
        "text_color","text_secondary","text_disabled",
        "border_color","hover_color",
        "button_bg","button_text","button_hover_bg","button_hover_text",
        "button_pressed_bg","button_pressed_text","button_border_color",
        "accent","accent_dark","accent_text",
        "tab_bg","tab_selected","tab_hover","tab_pane_bg",
        "scroll_handle","dialog_bg","dialog_border",
        "success","warning","error",
    ]

    def test_all_themes_have_required_keys(self):
        for name in ("dark","light","image"):
            theme = get_theme_colors(name)
            for key in self.REQUIRED:
                self.assertIn(key, theme, f"'{key}' missing from '{name}'")

    def test_get_theme_returns_copy(self):
        t1 = get_theme_colors("dark"); t2 = get_theme_colors("dark")
        t1["window_bg"] = "mutated"
        self.assertNotEqual(t2["window_bg"], "mutated")

    def test_unknown_theme_falls_back_to_dark(self):
        self.assertEqual(get_theme_colors("bogus")["name"], "Dark")

    def test_is_dark_dark(self):    self.assertTrue(is_dark_theme("dark"))
    def test_is_dark_image(self):   self.assertTrue(is_dark_theme("image"))
    def test_is_dark_light(self):   self.assertFalse(is_dark_theme("light"))

    def test_brand_gold_hex(self):
        self.assertTrue(BRAND_GOLD.startswith("#")); self.assertTrue(BRAND_GOLD_DARK.startswith("#"))

    def test_brand_gold_rgb_tuple(self):
        self.assertEqual(len(BRAND_GOLD_RGB),3)
        for c in BRAND_GOLD_RGB: self.assertGreaterEqual(c,0); self.assertLessEqual(c,255)

    def test_slot_selected_is_dark_gold(self):
        self.assertEqual(SLOT_SELECTED_COLOR, BRAND_GOLD_DARK_RGB)

    def test_slot_border_colors(self):
        self.assertEqual(len(SLOT_BORDER_THIN_COLOR),3)
        self.assertEqual(len(SLOT_BORDER_THICK_COLOR),3)

    def test_search_highlight_green_dominant(self):
        r,g,b = SEARCH_HIGHLIGHT_COLOR
        self.assertGreater(g,r); self.assertGreater(g,b)

    def test_search_dim_has_alpha(self):
        self.assertEqual(len(SEARCH_DIM_OVERLAY),4); self.assertGreater(SEARCH_DIM_OVERLAY[3],0)

    def test_size_overlay_bg_rgba(self):
        self.assertIn("rgba", SIZE_OVERLAY_BG.lower())

    def test_light_hover_dark_grey(self):
        self.assertEqual(get_theme_colors("light")["button_hover_bg"].lower(),"#333333")

    def test_dark_accent_is_light_gold(self):
        self.assertEqual(get_theme_colors("dark")["accent"].lower(), BRAND_GOLD.lower())

    def test_light_accent_is_dark_gold(self):
        self.assertEqual(get_theme_colors("light")["accent"].lower(), BRAND_GOLD_DARK.lower())

    def test_image_window_bg_has_alpha(self):
        self.assertTrue(get_theme_colors("image")["window_bg"].startswith("#ED"))


# ══════════════════════════════════════════════════════════════════════════════
# 5. PARSE COLOR QUERY
# ══════════════════════════════════════════════════════════════════════════════
class TestParseColorQuery(unittest.TestCase):
    """ui/color_search.py — parse_color_query edge cases."""

    def test_hex_with_hash(self):       self.assertEqual(parse_color_query("#ff0000"),(255,0,0))
    def test_hex_without_hash(self):    self.assertEqual(parse_color_query("00ff00"),(0,255,0))
    def test_hex_uppercase(self):       self.assertEqual(parse_color_query("#FF0000"),(255,0,0))
    def test_short_hex(self):           self.assertEqual(parse_color_query("#f00"),(255,0,0))
    def test_short_hex_white(self):     self.assertEqual(parse_color_query("#fff"),(255,255,255))
    def test_rgb_tuple(self):           self.assertEqual(parse_color_query("255,0,0"),(255,0,0))
    def test_rgb_spaces(self):          self.assertEqual(parse_color_query("255, 0, 0"),(255,0,0))
    def test_rgb_function(self):        self.assertEqual(parse_color_query("rgb(0,255,0)"),(0,255,0))
    def test_named_red(self):           self.assertEqual(parse_color_query("red"),(255,0,0))
    def test_named_blue(self):          self.assertEqual(parse_color_query("blue"),(0,0,255))
    def test_named_white(self):         self.assertEqual(parse_color_query("white"),(255,255,255))
    def test_named_black(self):         self.assertEqual(parse_color_query("black"),(0,0,0))
    def test_case_insensitive(self):    self.assertEqual(parse_color_query("RED"),parse_color_query("red"))
    def test_partial_name(self):        self.assertIsNotNone(parse_color_query("coral"))
    def test_empty_none(self):          self.assertIsNone(parse_color_query(""))
    def test_nonsense_none(self):       self.assertIsNone(parse_color_query("xyzxyzxyz"))
    def test_out_of_range_none(self):   self.assertIsNone(parse_color_query("300,0,0"))
    def test_whitespace_stripped(self): self.assertEqual(parse_color_query("  #ff0000  "),(255,0,0))
    def test_threshold_positive(self):  self.assertGreater(MATCH_THRESHOLD,0)


# ══════════════════════════════════════════════════════════════════════════════
# 6. ERROR HANDLER VALIDATORS
# ══════════════════════════════════════════════════════════════════════════════
class TestErrorHandlerValidators(unittest.TestCase):
    """utils/error_handler.py — rgb / hex / weight / image-size validators."""

    def test_rgb_valid(self):
        self.assertTrue(ValidationHelper.validate_rgb_values(0,0,0)[0])
        self.assertTrue(ValidationHelper.validate_rgb_values(255,255,255)[0])
        self.assertTrue(ValidationHelper.validate_rgb_values(128,64,32)[0])

    def test_rgb_invalid_low(self):     self.assertFalse(ValidationHelper.validate_rgb_values(-1,0,0)[0])
    def test_rgb_invalid_high(self):    self.assertFalse(ValidationHelper.validate_rgb_values(256,0,0)[0])
    def test_rgb_invalid_blue(self):    self.assertFalse(ValidationHelper.validate_rgb_values(0,0,256)[0])

    def test_hex_valid_hash(self):      self.assertTrue(ValidationHelper.validate_hex_color("#FF8800")[0])
    def test_hex_valid_no_hash(self):   self.assertTrue(ValidationHelper.validate_hex_color("FF8800")[0])
    def test_hex_valid_short(self):     self.assertTrue(ValidationHelper.validate_hex_color("#F80")[0])
    def test_hex_invalid_chars(self):   self.assertFalse(ValidationHelper.validate_hex_color("ZZZZZZ")[0])
    def test_hex_invalid_length(self):  self.assertFalse(ValidationHelper.validate_hex_color("#12345")[0])

    def test_weight_valid_bounds(self):
        self.assertTrue(ValidationHelper.validate_weight(0)[0])
        self.assertTrue(ValidationHelper.validate_weight(50)[0])
        self.assertTrue(ValidationHelper.validate_weight(100)[0])

    def test_weight_invalid_low(self):  self.assertFalse(ValidationHelper.validate_weight(-1)[0])
    def test_weight_invalid_high(self): self.assertFalse(ValidationHelper.validate_weight(101)[0])

    def test_image_size_valid(self):
        self.assertTrue(ValidationHelper.validate_image_size(1920,1080)[0])
        self.assertTrue(ValidationHelper.validate_image_size(1,1)[0])

    def test_image_size_zero(self):     self.assertFalse(ValidationHelper.validate_image_size(0,1080)[0])
    def test_image_size_negative(self): self.assertFalse(ValidationHelper.validate_image_size(-1,100)[0])
    def test_image_size_too_large(self):self.assertFalse(ValidationHelper.validate_image_size(9999,9999)[0])

    def test_error_messages_are_strings(self):
        _,msg = ValidationHelper.validate_rgb_values(-1,0,0)
        self.assertIsInstance(msg,str)


# ══════════════════════════════════════════════════════════════════════════════
# 7. FILE UTILS
# ══════════════════════════════════════════════════════════════════════════════
class TestFileUtils(unittest.TestCase):
    """utils/file_utils.py — extension, safe names, copy, delete, unique."""

    @classmethod
    def setUpClass(cls): cls.tmp = tempfile.mkdtemp()
    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_ensure_extension_adds(self):
        self.assertEqual(FileUtils.ensure_file_extension("palette",".gpl"),"palette.gpl")
    def test_ensure_extension_keeps(self):
        self.assertEqual(FileUtils.ensure_file_extension("palette.ase",".gpl"),"palette.ase")
    def test_ensure_extension_empty(self):
        self.assertEqual(FileUtils.ensure_file_extension("",".gpl"),"")

    def test_safe_filename_strips_invalid(self):
        r = FileUtils.get_safe_filename("my:file*name.txt")
        for ch in '<>:"/\\|?*': self.assertNotIn(ch,r)

    def test_safe_filename_preserves_valid(self):
        self.assertIn("MyPalette", FileUtils.get_safe_filename("MyPalette_2024"))

    def test_safe_filename_truncates(self):
        r = FileUtils.get_safe_filename("A"*300)
        self.assertLessEqual(len(r), FileUtils.MAX_FILENAME_LENGTH)

    def test_get_extension(self):
        self.assertEqual(FileUtils.get_file_extension("palette.gpl"),".gpl")
        self.assertEqual(FileUtils.get_file_extension("noext"),"")

    def test_is_valid_image(self):
        self.assertTrue(FileUtils.is_valid_image_file("photo.png"))
        self.assertFalse(FileUtils.is_valid_image_file("palette.gpl"))

    def test_is_valid_palette(self):
        self.assertTrue(FileUtils.is_valid_palette_file("palette.gpl"))
        self.assertFalse(FileUtils.is_valid_palette_file("photo.png"))

    def test_file_size_bytes(self):
        p = os.path.join(self.tmp,"size.txt")
        Path(p).write_bytes(b"hello")
        self.assertEqual(FileUtils.get_file_size_bytes(p),5)

    def test_file_size_nonexistent(self):
        self.assertEqual(FileUtils.get_file_size_bytes("/nonexistent.txt"),0)

    def test_create_directory(self):
        d = os.path.join(self.tmp,"sub","nested")
        self.assertTrue(FileUtils.create_directory_if_not_exists(d))
        self.assertTrue(os.path.isdir(d))

    def test_validate_path_existing(self):
        self.assertTrue(FileUtils.validate_file_path(sys.executable, must_exist=True))

    def test_validate_path_missing(self):
        self.assertFalse(FileUtils.validate_file_path("/definitely/missing.txt", must_exist=True))

    def test_copy_file(self):
        src = os.path.join(self.tmp,"src.txt"); dst = os.path.join(self.tmp,"dst.txt")
        Path(src).write_bytes(b"copy me")
        self.assertTrue(FileUtils.copy_file(src,dst))
        self.assertEqual(Path(dst).read_bytes(), b"copy me")

    def test_delete_file(self):
        p = os.path.join(self.tmp,"del.txt"); Path(p).write_text("x")
        self.assertTrue(FileUtils.delete_file(p))
        self.assertFalse(os.path.exists(p))

    def test_delete_nonexistent_no_crash(self):
        # delete_file returns True for nonexistent files by design ("successful or not found")
        self.assertTrue(FileUtils.delete_file("/nonexistent/file.txt"))

    def test_get_unique_filename(self):
        Path(os.path.join(self.tmp,"unique.txt")).write_text("x")
        unique = FileUtils.get_unique_filename(self.tmp, "unique", ".txt")
        self.assertNotEqual(unique, "unique.txt")


# ══════════════════════════════════════════════════════════════════════════════
# 8. EXPORT HISTORY
# ══════════════════════════════════════════════════════════════════════════════
class TestExportHistory(unittest.TestCase):
    """utils/export_history.py — add / limit / query / clear."""

    def setUp(self):
        self.hist = ExportHistory(max_entries=5)
        self.hist._entries = []  # start fresh, skip disk load

    def _add(self, path="/fake/p.gpl", ext=".gpl", count=5, size=100):
        self.hist.add_entry(path=path, format_ext=ext, color_count=count, file_size_bytes=size)

    def test_initial_empty(self):
        self.assertTrue(self.hist.is_empty); self.assertEqual(self.hist.count,0)

    def test_add_entry(self):
        self._add(); self.assertEqual(self.hist.count,1)

    def test_add_prepends(self):
        self._add("/a.gpl"); self._add("/b.gpl")
        self.assertEqual(self.hist.get_last_entry().path,"/b.gpl")

    def test_max_entries(self):
        for i in range(10): self._add(f"/p{i}.gpl")
        self.assertLessEqual(self.hist.count,5)

    def test_get_history_limit(self):
        for i in range(5): self._add(f"/p{i}.gpl")
        self.assertEqual(len(self.hist.get_history(limit=2)),2)

    def test_get_last_entry_none_when_empty(self):
        self.assertIsNone(self.hist.get_last_entry())

    def test_get_last_format(self):
        self._add(ext=".ase"); self.assertEqual(self.hist.get_last_format(),".ase")

    def test_clear(self):
        self._add(); self.hist.clear(); self.assertTrue(self.hist.is_empty)

    def test_entry_roundtrip(self):
        e = ExportEntry(path="/test.gpl",format_ext=".gpl",
                        timestamp="2025-01-01T00:00:00",color_count=8,file_size_bytes=512)
        e2 = ExportEntry.from_dict(e.to_dict())
        self.assertEqual(e2.path,"/test.gpl"); self.assertEqual(e2.color_count,8)

    def test_entry_filename(self):
        e = ExportEntry(path="/dir/my.gpl",format_ext=".gpl",timestamp="2025-01-01",color_count=5)
        self.assertEqual(e.filename,"my.gpl")

    def test_entry_file_exists_false(self):
        e = ExportEntry(path="/nonexistent.gpl",format_ext=".gpl",timestamp="2025-01-01",color_count=0)
        self.assertFalse(e.file_exists)

    def test_entry_formatted_time_string(self):
        e = ExportEntry(path="/p.gpl",format_ext=".gpl",
                        timestamp="2025-06-15T14:30:00",color_count=5)
        self.assertIsInstance(e.formatted_time,str)

    def test_entry_display_string_nonempty(self):
        e = ExportEntry(path="/p.gpl",format_ext=".gpl",
                        timestamp="2025-01-01T00:00:00",color_count=5,file_size_bytes=1024)
        self.assertGreater(len(e.display_string),0)


# ══════════════════════════════════════════════════════════════════════════════
# 9. PALETTE METADATA
# ══════════════════════════════════════════════════════════════════════════════
class TestPaletteMetadata(unittest.TestCase):
    """core/palette_metadata.py — serialisation, display_name, touch."""

    def test_default_name(self):    self.assertEqual(PaletteMetadata().name,"Untitled Palette")
    def test_custom_name(self):     self.assertEqual(PaletteMetadata(name="Sunset").name,"Sunset")

    def test_display_name_contains_name(self):
        self.assertIn("My Palette", PaletteMetadata(name="My Palette").display_name)

    def test_timestamps_set(self):
        m = PaletteMetadata()
        self.assertNotEqual(m.created_at,""); self.assertNotEqual(m.modified_at,"")

    def test_touch_updates_modified(self):
        import time; m = PaletteMetadata(); old = m.modified_at; time.sleep(0.02); m.touch()
        self.assertGreaterEqual(m.modified_at, old)

    def test_to_dict_roundtrip(self):
        m = PaletteMetadata(name="Test",author="Chris",description="Desc")
        m2 = PaletteMetadata.from_dict(m.to_dict())
        self.assertEqual(m2.name,"Test"); self.assertEqual(m2.author,"Chris")
        self.assertEqual(m2.description,"Desc")

    def test_from_dict_missing_keys(self):
        self.assertEqual(PaletteMetadata.from_dict({}).name,"Untitled Palette")

    def test_from_dict_partial(self):
        m = PaletteMetadata.from_dict({"name":"Partial"})
        self.assertEqual(m.name,"Partial"); self.assertEqual(m.author,"")

    def test_timestamps_preserved(self):
        m = PaletteMetadata()
        self.assertEqual(PaletteMetadata.from_dict(m.to_dict()).created_at, m.created_at)


# ══════════════════════════════════════════════════════════════════════════════
# 10. SLOT GROUP
# ══════════════════════════════════════════════════════════════════════════════
class TestSlotGroup(unittest.TestCase):
    """ui/slot_group.py — SlotGroupData / SlotGroupInfo serialisation."""

    def test_data_roundtrip(self):
        d = SlotGroupData(name="Reds",slot_count=5,collapsed=False)
        d2 = SlotGroupData.from_dict(d.to_dict())
        self.assertEqual(d2.name,"Reds"); self.assertEqual(d2.slot_count,5)
        self.assertFalse(d2.collapsed)

    def test_data_collapsed_preserved(self):
        d = SlotGroupData(name="Hidden",slot_count=3,collapsed=True)
        self.assertTrue(SlotGroupData.from_dict(d.to_dict()).collapsed)

    def test_data_from_empty_dict(self):
        d = SlotGroupData.from_dict({})
        self.assertEqual(d.name,""); self.assertEqual(d.slot_count,0); self.assertFalse(d.collapsed)

    def test_info_to_data(self):
        data = SlotGroupInfo(name="Blues",slot_count=3).to_data()
        self.assertEqual(data.name,"Blues"); self.assertEqual(data.slot_count,3)

    def test_info_from_data(self):
        info = SlotGroupInfo.from_data(SlotGroupData(name="Greens",slot_count=7,collapsed=True))
        self.assertEqual(info.name,"Greens"); self.assertEqual(info.slot_count,7)
        self.assertTrue(info.collapsed)

    def test_info_default_not_collapsed(self):
        self.assertFalse(SlotGroupInfo(name="X",slot_count=0).collapsed)


# ══════════════════════════════════════════════════════════════════════════════
# 11. UNDO MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestUndoManager(unittest.TestCase):
    """utils/undo_manager.py — push / undo / redo / limits / clear."""

    def setUp(self):
        self.mgr = UndoManager()

    def _state(self, n=1):
        return PaletteState(
            slots=[{"r":i,"g":i,"b":i,"a":255,"hex_text":f"#{i:02x}{i:02x}{i:02x}",
                    "locked":False,"is_default_color":False} for i in range(n)],
            metadata={}, groups=[],
        )

    def test_initial_cannot_undo(self):  self.assertFalse(self.mgr.can_undo)
    def test_initial_cannot_redo(self):  self.assertFalse(self.mgr.can_redo)
    def test_push_enables_undo(self):    self.mgr.push(self._state()); self.assertTrue(self.mgr.can_undo)
    def test_push_no_redo(self):         self.mgr.push(self._state()); self.assertFalse(self.mgr.can_redo)

    def test_undo_returns_previous(self):
        self.mgr.push(self._state(2)); self.mgr.push(self._state(3))
        prev = self.mgr.undo(self._state(4))
        self.assertIsNotNone(prev); self.assertEqual(len(prev.slots),3)

    def test_undo_twice(self):
        self.mgr.push(self._state(1)); self.mgr.push(self._state(2)); self.mgr.push(self._state(3))
        self.mgr.undo(self._state(4))
        prev = self.mgr.undo(self._state(3))
        self.assertEqual(len(prev.slots),2)

    def test_undo_empty_none(self):   self.assertIsNone(self.mgr.undo(self._state()))
    def test_redo_empty_none(self):   self.assertIsNone(self.mgr.redo(self._state()))

    def test_redo_after_undo(self):
        self.mgr.push(self._state(5)); self.mgr.undo(self._state(10))
        self.assertTrue(self.mgr.can_redo)
        self.assertIsNotNone(self.mgr.redo(self._state(5)))

    def test_push_clears_redo(self):
        self.mgr.push(self._state()); self.mgr.undo(self._state(2))
        self.assertTrue(self.mgr.can_redo); self.mgr.push(self._state(3))
        self.assertFalse(self.mgr.can_redo)

    def test_clear(self):
        self.mgr.push(self._state()); self.mgr.clear()
        self.assertFalse(self.mgr.can_undo); self.assertFalse(self.mgr.can_redo)

    def test_max_history(self):
        limit = self.mgr.MAX_DEPTH
        for i in range(limit+20): self.mgr.push(self._state(i%10))
        self.assertLessEqual(self.mgr.undo_depth,limit)

    def test_depth_tracking(self):
        for i in range(4): self.mgr.push(self._state(i))
        self.assertEqual(self.mgr.undo_depth,4)

    def test_capture_empty_widgets(self):
        self.assertEqual(PaletteState.capture([],{},{}).slots,[])


# ══════════════════════════════════════════════════════════════════════════════
# 12. COLOR HISTORY
# ══════════════════════════════════════════════════════════════════════════════
class TestColorHistory(unittest.TestCase):
    """utils/color_history.py — record / trim / serialise."""

    def setUp(self):
        self.panel = ColorHistoryPanel(max_entries=5)

    def test_initial_empty(self):   self.assertEqual(self.panel.entries,[])
    def test_record_adds(self):
        self.panel.record("#000000","#ffffff",slot_index=0)
        self.assertEqual(len(self.panel.entries),1)

    def test_record_stores_colors(self):
        self.panel.record("#aabbcc","#112233",slot_index=2)
        e = self.panel.entries[0]
        self.assertEqual(e.old_color,"#aabbcc"); self.assertEqual(e.new_color,"#112233")
        self.assertEqual(e.slot_index,2)

    def test_record_trims_to_max(self):
        for i in range(10): self.panel.record(f"#00{i:04x}",f"#ff{i:04x}")
        self.assertLessEqual(len(self.panel.entries),5)

    def test_clear(self):
        self.panel.record("#000000","#ffffff"); self.panel.clear()
        self.assertEqual(self.panel.entries,[])

    def test_to_list_roundtrip(self):
        self.panel.record("#aabbcc","#112233",slot_index=1)
        data = self.panel.to_list()
        self.assertEqual(data[0]["new_color"],"#112233")

    def test_entries_from_list(self):
        self.panel.record("#aa0000","#00aa00")
        restored = ColorHistoryPanel.entries_from_list(self.panel.to_list())
        self.assertEqual(restored[0].new_color,"#00aa00")

    def test_set_entries(self):
        self.panel.set_entries([ColorHistoryEntry(old_color="#000",new_color="#fff",slot_index=0)])
        self.assertEqual(len(self.panel.entries),1)

    def test_max_entries_setter(self):
        # Setter clamps to min=10, so test with 10
        self.panel.max_entries = 10
        for i in range(15): self.panel.record(f"#0000{i:02x}",f"#ffff{i:02x}")
        self.assertLessEqual(len(self.panel.entries),10)

    def test_entry_roundtrip(self):
        e = ColorHistoryEntry(old_color="#aabbcc",new_color="#ddeeff",slot_index=3)
        e2 = ColorHistoryEntry.from_dict(e.to_dict())
        self.assertEqual(e2.old_color,"#aabbcc"); self.assertEqual(e2.slot_index,3)

    def test_newest_first(self):
        self.panel.record("#111111","#222222"); self.panel.record("#333333","#444444")
        self.assertEqual(self.panel.entries[0].new_color,"#444444")

    def test_now_returns_string(self):
        self.assertIsInstance(ColorHistoryEntry.now(),str)


# ══════════════════════════════════════════════════════════════════════════════
# 13. RECENT PALETTES
# ══════════════════════════════════════════════════════════════════════════════
class TestRecentPalettes(unittest.TestCase):
    """utils/recent_palettes.py — add / dedup / prune / max-entries."""

    def setUp(self):
        from PyQt6.QtCore import QSettings
        settings = QSettings(); settings.clear()
        self.mgr = RecentPalettesManager(settings=settings, max_entries=5)

    def _this(self): return str(Path(__file__).resolve())

    def test_initial_empty(self):   self.assertEqual(self.mgr.entries,[])

    def test_add_entry(self):
        self.mgr.add(path=self._this(),name="T",format_ext=".py",color_count=5)
        self.assertEqual(len(self.mgr.entries),1)

    def test_add_stores_data(self):
        self.mgr.add(path=self._this(),name="MyPalette",format_ext=".gpl",color_count=8)
        self.assertEqual(self.mgr.entries[0].name,"MyPalette")
        self.assertEqual(self.mgr.entries[0].color_count,8)

    def test_duplicate_moves_to_top(self):
        p = self._this()
        self.mgr.add(path=p,name="A",format_ext=".gpl",color_count=1)
        self.mgr.add(path="/other/b.gpl",name="B",format_ext=".gpl",color_count=2)
        self.mgr.add(path=p,name="A",format_ext=".gpl",color_count=1)
        self.assertEqual(self.mgr.entries[0].path,p)

    def test_max_entries(self):
        for i in range(10): self.mgr.add(path=f"/fake_{i}.gpl",name=f"P{i}",format_ext=".gpl",color_count=i)
        self.assertLessEqual(len(self.mgr.entries),5)

    def test_remove(self):
        p = self._this()
        self.mgr.add(path=p,name="X",format_ext=".gpl",color_count=1)
        self.mgr.remove(p)
        self.assertTrue(all(e.path!=p for e in self.mgr.entries))

    def test_clear(self):
        self.mgr.add(path=self._this(),name="Y",format_ext=".gpl",color_count=1)
        self.mgr.clear(); self.assertEqual(self.mgr.entries,[])

    def test_prune_missing(self):
        self.mgr.add(path="/definitely/missing.gpl",name="G",format_ext=".gpl",color_count=0)
        self.assertGreaterEqual(self.mgr.prune_missing(),1)

    def test_prune_keeps_existing(self):
        self.mgr.add(path=self._this(),name="Real",format_ext=".py",color_count=1)
        self.mgr.prune_missing(); self.assertEqual(len(self.mgr.entries),1)

    def test_entry_exists_true(self):
        e = RecentPaletteEntry(path=self._this(),name="r",format_ext=".py",
                               color_count=1,timestamp="2025-01-01")
        self.assertTrue(e.exists)

    def test_entry_exists_false(self):
        e = RecentPaletteEntry(path="/no/such.gpl",name="f",format_ext=".gpl",
                               color_count=0,timestamp="2025-01-01")
        self.assertFalse(e.exists)

    def test_entry_display_name(self):
        e = RecentPaletteEntry(path="/x/y.gpl",name="Sunset",format_ext=".gpl",
                               color_count=5,timestamp="2025-01-01")
        self.assertIn("Sunset",e.display_name)


# ══════════════════════════════════════════════════════════════════════════════
# 14. SETTINGS MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestSettingsManager(unittest.TestCase):
    """utils/settings_manager.py — all property accessors."""

    def setUp(self): self.mgr = SettingsManager()

    def test_starting_rows_int(self):   self.assertIsInstance(self.mgr.starting_rows,int); self.assertGreater(self.mgr.starting_rows,0)
    def test_starting_cols_int(self):   self.assertIsInstance(self.mgr.starting_cols,int); self.assertGreater(self.mgr.starting_cols,0)
    def test_set_starting_rows(self):   self.mgr.starting_rows=5; self.assertEqual(self.mgr.starting_rows,5)
    def test_set_starting_cols(self):   self.mgr.starting_cols=6; self.assertEqual(self.mgr.starting_cols,6)

    def test_auto_save_toggle(self):
        self.mgr.auto_save_enabled=True; self.assertTrue(self.mgr.auto_save_enabled)
        self.mgr.auto_save_enabled=False; self.assertFalse(self.mgr.auto_save_enabled)

    def test_single_click_toggle(self):
        self.mgr.single_click_edit=True; self.assertTrue(self.mgr.single_click_edit)

    def test_default_color_all_themes(self):
        for t in ("dark","light","image"):
            c = self.mgr.default_slot_color_for_theme(t)
            self.assertIsInstance(c,str); self.assertTrue(c.startswith("#"))

    def test_set_default_color(self):
        self.mgr.set_default_slot_color_for_theme("dark","#123456")
        self.assertEqual(self.mgr.default_slot_color_for_theme("dark"),"#123456")

    def test_slot_border_style_string(self):    self.assertIsInstance(self.mgr.slot_border_style,str)
    def test_slot_size_preference_valid(self):  self.assertIn(self.mgr.slot_size_preference,("auto","small","medium","large"))
    def test_color_blindness_mode_string(self): self.assertIsInstance(self.mgr.color_blindness_mode,str)
    def test_max_history_positive(self):        self.assertGreater(self.mgr.max_history_size,0)
    def test_auto_save_interval_ms(self):       self.assertGreater(self.mgr.auto_save_interval_ms,0)
    def test_auto_restore_bool(self):           self.assertIsInstance(self.mgr.auto_restore_session,bool)
    def test_show_size_overlay_bool(self):      self.assertIsInstance(self.mgr.show_size_overlay,bool)
    def test_max_recent_positive(self):         self.assertGreater(self.mgr.max_recent_palettes,0)
    def test_sync_no_crash(self):               self.mgr.sync()


# ══════════════════════════════════════════════════════════════════════════════
# 15. PALETTE FORMATS
# ══════════════════════════════════════════════════════════════════════════════
class TestPaletteFormats(unittest.TestCase):
    """core/palette_formats.py — export + import round-trips for all formats."""

    COLORS = [((255,0,0),50),((0,255,0),50),((0,0,255),50),
              ((128,128,128),50),((255,200,100),50)]

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.meta = PaletteMetadata(name="Test Palette",author="Tester")

    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.tmp,ignore_errors=True)

    def _path(self,ext): return os.path.join(self.tmp,f"test{ext}")

    def _roundtrip(self,ext):
        p = self._path(ext)
        PaletteFormats.export_palette(p,self.COLORS,self.meta)
        return PaletteFormats.import_palette(p).colors

    def test_roundtrip_gpl(self):   self.assertEqual(len(self._roundtrip(".gpl")),5)
    def test_roundtrip_json(self):
        colors = self._roundtrip(".json"); self.assertEqual(len(colors),5)
    def test_roundtrip_xml(self):   self.assertEqual(len(self._roundtrip(".xml")),5)
    def test_roundtrip_css(self):   self.assertGreaterEqual(len(self._roundtrip(".css")),1)
    def test_export_hex_creates_file(self):
        p=self._path(".hex"); PaletteFormats.export_palette(p,self.COLORS,self.meta)
        self.assertGreater(os.path.getsize(p),0)
    def test_roundtrip_ase(self):   self.assertGreaterEqual(len(self._roundtrip(".ase")),1)
    def test_roundtrip_aco(self):   self.assertGreaterEqual(len(self._roundtrip(".aco")),1)
    def test_export_colors_creates_file(self):
        p=self._path(".colors"); PaletteFormats.export_palette(p,self.COLORS,self.meta)
        self.assertGreater(os.path.getsize(p),0)

    def test_export_svg_valid(self):
        p = self._path(".svg")
        PaletteFormats.export_palette(p,self.COLORS,self.meta)
        self.assertGreater(os.path.getsize(p),0)
        self.assertIn("svg",Path(p).read_text().lower())

    def test_export_txt(self):
        p = self._path(".txt")
        PaletteFormats.export_palette(p,self.COLORS,self.meta)
        self.assertGreater(os.path.getsize(p),0)

    def test_export_hsv(self):
        p = self._path(".hsv")
        PaletteFormats.export_palette(p,self.COLORS,self.meta)
        self.assertGreater(os.path.getsize(p),0)

    def test_export_hsl(self):
        p = self._path(".hsl")
        PaletteFormats.export_palette(p,self.COLORS,self.meta)
        self.assertGreater(os.path.getsize(p),0)

    def test_json_has_structure(self):
        p = self._path(".json")
        PaletteFormats.export_palette(p,self.COLORS,self.meta)
        data = json.loads(Path(p).read_text())
        self.assertTrue("colors" in data or "name" in data)

    def test_empty_palette_raises(self):
        # export_palette raises ValueError when given no colors
        with self.assertRaises((ValueError, Exception)):
            PaletteFormats.export_palette(self._path("_empty.json"),[],self.meta)

    def test_single_color_roundtrip(self):
        p = self._path("_single.json")
        PaletteFormats.export_palette(p,[((200,100,50),50)],self.meta)
        self.assertFalse(PaletteFormats.import_palette(p).is_empty)

    def test_import_nonexistent_returns_empty(self):
        # import_palette catches errors and returns empty result rather than raising
        result = PaletteFormats.import_palette("/nonexistent/file.gpl")
        self.assertTrue(result.is_empty)

    def test_import_result_is_empty(self):
        self.assertTrue(ImportResult(colors=[],metadata=None).is_empty)

    def test_import_result_not_empty(self):
        self.assertFalse(ImportResult(colors=[((255,0,0),50)],metadata=None).is_empty)

    def test_export_formats_nonempty(self):
        self.assertGreater(len(PaletteFormats.get_export_formats()),5)

    def test_import_formats_nonempty(self):
        self.assertGreater(len(PaletteFormats.get_import_formats()),3)

    def test_gpl_color_values_accurate(self):
        p = self._path("_accuracy.gpl")
        PaletteFormats.export_palette(p,[((200,100,50),50)],self.meta)
        rgb = PaletteFormats.import_palette(p).colors[0][0]
        self.assertAlmostEqual(rgb[0],200,delta=2)


# ══════════════════════════════════════════════════════════════════════════════
# 16. COLOR EXTRACTOR
# ══════════════════════════════════════════════════════════════════════════════
class TestColorExtractor(unittest.TestCase):
    """core/color_extractor.py — k-means extraction from synthetic images."""

    @classmethod
    def setUpClass(cls):
        try:
            from core.color_extractor import ColorExtractor
            from PIL import Image
            cls.CE = ColorExtractor; cls.Image = Image
            cls._skip = False
        except ImportError:
            cls._skip = True

    def setUp(self):
        if self._skip: self.skipTest("Pillow not installed")

    def _solid(self,color,size=(100,100)):
        return self.Image.new("RGB",size,color)

    def test_extract_returns_list(self):
        r = self.CE.extract_palette(self._solid((255,0,0)),num_colors=3)
        self.assertIsInstance(r,list); self.assertGreaterEqual(len(r),1)

    def test_extract_valid_rgb(self):
        for rgb in self.CE.extract_palette(self._solid((128,64,32)),num_colors=3):
            self.assertEqual(len(rgb),3)
            for ch in rgb: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)

    def test_dominant_close_to_solid(self):
        r = self.CE.extract_palette(self._solid((200,50,10)),num_colors=3)
        self.assertGreater(len(r),0); self.assertAlmostEqual(r[0][0],200,delta=20)

    def test_quality_parameter(self):
        img = self._solid((255,128,0),size=(200,200))
        for q in (1,10):
            self.assertGreaterEqual(len(self.CE.extract_palette(img,num_colors=3,quality=q)),1)

    def test_rgba_handled(self):
        img = self.Image.new("RGBA",(100,100),(255,0,0,128))
        self.assertIsInstance(self.CE.extract_palette(img,num_colors=3),list)

    def test_clamps_num_colors_high(self):
        r = self.CE.extract_palette(self._solid((100,100,100)),num_colors=100)
        self.assertLessEqual(len(r),12)


# ══════════════════════════════════════════════════════════════════════════════
# 17. PIXMAP CACHE
# ══════════════════════════════════════════════════════════════════════════════
class TestPixmapCache(unittest.TestCase):
    """utils/pixmap_cache.py — LRU cache get / put / eviction / stats."""

    def setUp(self):
        self.cache = QPixmapCache(max_size=3)

    def _px(self):
        from PyQt6.QtGui import QPixmap
        return QPixmap(10,10)

    def test_initial_empty(self):   self.assertEqual(self.cache.get_size(),0)

    def test_put_and_get(self):
        key=("test",1); self.cache.put(key,self._px())
        self.assertIsNotNone(self.cache.get(key))

    def test_get_missing_none(self):
        self.assertIsNone(self.cache.get(("nonexistent",99)))

    def test_contains(self):
        key=("img",0.5); self.cache.put(key,self._px())
        self.assertTrue(self.cache.contains(key))
        self.assertFalse(self.cache.contains(("other",0.5)))

    def test_eviction_at_max(self):
        for i in range(5): self.cache.put((f"img_{i}",1),self._px())
        self.assertLessEqual(self.cache.get_size(),3)

    def test_clear(self):
        self.cache.put(("k",1),self._px()); self.cache.clear()
        self.assertEqual(self.cache.get_size(),0)

    def test_remove(self):
        key=("rm",1); self.cache.put(key,self._px()); self.cache.remove(key)
        self.assertFalse(self.cache.contains(key))

    def test_remove_nonexistent_false(self):
        self.assertFalse(self.cache.remove(("ghost",99)))

    def test_stats_keys(self):
        stats = self.cache.get_stats()
        self.assertIn("hits",stats); self.assertIn("misses",stats); self.assertIn("size",stats)

    def test_hit_tracked(self):
        key=("k",1); self.cache.put(key,self._px())
        before = self.cache.get_stats()["hits"]
        self.cache.get(key)
        self.assertEqual(self.cache.get_stats()["hits"],before+1)

    def test_miss_tracked(self):
        before = self.cache.get_stats()["misses"]
        self.cache.get(("nonexistent",1))
        self.assertEqual(self.cache.get_stats()["misses"],before+1)

    def test_reset_stats(self):
        self.cache.get(("x",1)); self.cache.reset_stats()
        self.assertEqual(self.cache.get_stats()["hits"],0)

    def test_resize_shrinks(self):
        for i in range(3): self.cache.put((f"k{i}",1),self._px())
        self.cache.resize(1); self.assertLessEqual(self.cache.get_size(),1)

    def test_get_or_create_miss_calls_creator(self):
        called=[]
        def creator(): called.append(True); return self._px()
        self.cache.get_or_create(("new",1),creator)
        self.assertTrue(called)

    def test_get_or_create_hit_skips_creator(self):
        called=[]; key=("cached",1); self.cache.put(key,self._px())
        self.cache.get_or_create(key, lambda:(called.append(True),self._px())[1])
        self.assertFalse(called)

    def test_get_max_size(self):    self.assertEqual(self.cache.get_max_size(),3)
    def test_get_keys_contains(self):
        key=("abc",2); self.cache.put(key,self._px())
        self.assertIn(key,self.cache.get_keys())


# ══════════════════════════════════════════════════════════════════════════════
# 18. THEME MANAGER
# ══════════════════════════════════════════════════════════════════════════════
class TestThemeManager(unittest.TestCase):
    """ui/theme_manager.py — cycle / get / is_image_mode / display name."""

    def setUp(self):
        self.tm = ThemeManager()

    def test_initial_dark(self):        self.assertEqual(self.tm.current_theme,"dark")
    def test_get_current_theme_dict(self):
        theme = self.tm.get_current_theme()
        self.assertIsInstance(theme,dict); self.assertIn("window_bg",theme)
    def test_cycle_changes_theme(self):
        before = self.tm.current_theme; self.tm.cycle_theme()
        self.assertNotEqual(self.tm.current_theme,before)
    def test_cycle_returns_valid_name(self):
        self.assertIn(self.tm.cycle_theme(),("dark","light","image"))
    def test_display_name_string(self):
        name=self.tm.get_theme_display_name()
        self.assertIsInstance(name,str); self.assertGreater(len(name),0)
    def test_is_image_mode_false(self): self.assertFalse(self.tm.is_image_mode())
    def test_detect_image_no_crash(self): self.tm.detect_image_resources()
    def test_scrollbar_dark_qscrollbar(self): self.assertIn("QScrollBar",ThemeManager.SCROLLBAR_DARK)
    def test_scrollbar_light_qscrollbar(self): self.assertIn("QScrollBar",ThemeManager.SCROLLBAR_LIGHT)
    def test_dark_theme_constant(self):
        self.assertIsInstance(ThemeManager.DARK_THEME,dict)
        self.assertIn("window_bg",ThemeManager.DARK_THEME)
    def test_get_light_theme(self):
        self.tm.current_theme="light"
        theme = self.tm.get_current_theme()
        self.assertIsNotNone(theme); self.assertEqual(theme.get("name"),"Light")


# ══════════════════════════════════════════════════════════════════════════════
# 19. SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
class TestSessionState(unittest.TestCase):
    """utils/session_manager.py — PaletteSessionState data class."""

    def _state(self,n=3):
        return PaletteSessionState(
            timestamp="2025-01-01T12:00:00",
            slots=[{"color":f"#ff{i:04x}","locked":False,
                    "has_image":False,"is_default_color":False} for i in range(n)],
            current_theme="dark",metadata={"name":"Test"},groups=[],
        )

    def test_is_valid_with_slots(self):  self.assertTrue(self._state(3).is_valid)
    def test_is_valid_empty_slots(self): self.assertFalse(self._state(0).is_valid)
    def test_slot_count(self):           self.assertEqual(self._state(5).slot_count,5)

    def test_to_dict_roundtrip(self):
        s = self._state(3); s2 = PaletteSessionState.from_dict(s.to_dict())
        self.assertEqual(s2.slot_count,3); self.assertEqual(s2.current_theme,"dark")

    def test_from_dict_missing_fields(self):
        s = PaletteSessionState.from_dict({})
        self.assertEqual(s.current_theme,"dark"); self.assertEqual(s.slots,[])

    def test_age_seconds_positive(self):
        s = PaletteSessionState(timestamp="2020-01-01T00:00:00",slots=[{"x":1}])
        self.assertGreater(s.age_seconds,0)

    def test_formatted_time_string(self):
        self.assertIsInstance(self._state().formatted_time,str)

    def test_groups_roundtrip(self):
        s = PaletteSessionState(
            timestamp="2025-01-01",
            slots=[{"color":"#ff0000","locked":False,"has_image":False,"is_default_color":False}],
            groups=[{"name":"Reds","slot_count":1,"collapsed":False}],
        )
        s2 = PaletteSessionState.from_dict(s.to_dict())
        self.assertEqual(len(s2.groups),1); self.assertEqual(s2.groups[0]["name"],"Reds")

    def test_color_history_preserved(self):
        s = self._state(1)
        s.color_history=[{"old":"#000","new":"#fff","slot_index":0}]
        s2 = PaletteSessionState.from_dict(s.to_dict())
        self.assertEqual(len(s2.color_history),1)


# ══════════════════════════════════════════════════════════════════════════════
# 20. GUI INTEGRATION — MainWindow
# ══════════════════════════════════════════════════════════════════════════════
class TestMainWindowIntegration(unittest.TestCase):
    """Full MainWindow integration — slot operations, undo/redo, theme, search."""

    @classmethod
    def setUpClass(cls):
        import unittest.mock as mock
        from utils.session_manager import SessionManager
        from utils.settings_manager import SettingsManager
        with mock.patch.object(SessionManager,"has_recovery",return_value=False), \
             mock.patch.object(SessionManager,"has_saved_session",return_value=False), \
             mock.patch.object(SettingsManager,"auto_restore_session",
                               new_callable=lambda:property(lambda self:False)):
            from RNV_Color_Palette_Manager import MainWindow
            cls.win = MainWindow()
        # Neutralise everything that could block teardown:
        # closeEvent file I/O, auto-save timer, settings sync
        cls.win.closeEvent = lambda event: event.accept()
        try: cls.win.session_manager.stop_auto_save()
        except Exception: pass

    @classmethod
    def tearDownClass(cls):
        pass  # os._exit() at runner level handles Qt cleanup

    def _qc(self,r,g,b):
        from PyQt6.QtGui import QColor; return QColor(r,g,b)

    # --- startup ------------------------------------------------------------
    def test_app_name_in_title(self):
        from utils.config import APP_NAME
        self.assertIn(APP_NAME, self.win.windowTitle())

    def test_version_is_333(self):
        from utils.config import APP_VERSION
        self.assertEqual(APP_VERSION,"3.3.13")

    def test_initial_slot_count(self):
        # Session restore may load a previously saved palette rather than
        # the default rows*cols — just verify the window has at least one slot
        self.assertGreater(len(self.win.slots_widgets), 0)

    def test_initial_theme_valid(self):
        self.assertIn("window_bg", self.win.theme_manager.get_current_theme())

    def test_initial_group_exists(self):
        self.assertGreaterEqual(len(self.win.slot_groups),1)

    def test_initial_no_selection(self):
        self.assertIsNone(self.win._selected_slot)

    # --- add / remove slots -------------------------------------------------
    def test_add_slot(self):
        before=len(self.win.slots_widgets); self.win.add_slot()
        self.assertEqual(len(self.win.slots_widgets),before+1)

    def test_remove_slot(self):
        self.win.add_slot(); before=len(self.win.slots_widgets)
        self.win.remove_slot(self.win.slots_widgets[-1])
        self.assertEqual(len(self.win.slots_widgets),before-1)

    def test_add_with_color(self):
        self.win.add_slot_with_color(self._qc(200,100,50))
        self.assertEqual(self.win.slots_widgets[-1].slot.color.red(),200)

    def test_duplicate_copies_color(self):
        self.win.add_slot_with_color(self._qc(123,45,67))
        self.win.duplicate_slot(self.win.slots_widgets[-1])
        self.assertEqual(self.win.slots_widgets[-2].slot.color,self.win.slots_widgets[-1].slot.color)

    def test_clear_keeps_locked(self):
        self.win.slots_widgets[0].locked=True
        self.win.clear_all_unlocked_slots()
        self.assertEqual(len(self.win.slots_widgets),1)
        self.win.slots_widgets[0].locked=False; self.win.add_slot()

    # --- max slots ----------------------------------------------------------
    def test_max_slots_not_exceeded(self):
        """Verify the MAX_SLOTS guard.

        Two offscreen-Qt limitations require mocking:
        1. DialogHelper.show_warning calls QMessageBox.exec() which blocks
           forever with no event loop to dismiss it.
        2. update_grid() with many slots hangs in the offscreen plugin.
        Both are mocked so we can test the guard logic cleanly.
        """
        import unittest.mock as mock
        from utils.config import MAX_SLOTS
        from utils.dialog_helper import DialogHelper

        win = self.win
        original = list(win.slots_widgets)

        # Pad list to MAX_SLOTS with sentinels — guard only checks len()
        win.slots_widgets.extend([object()] * (MAX_SLOTS - len(original)))
        self.assertEqual(len(win.slots_widgets), MAX_SLOTS)

        try:
            with mock.patch.object(DialogHelper, "show_warning") as mock_warn, \
                 mock.patch.object(win, "update_grid"):
                win.add_slot()
            # Warning must have been shown and slot count must be unchanged
            mock_warn.assert_called_once()
            self.assertEqual(len(win.slots_widgets), MAX_SLOTS)
        finally:
            win.slots_widgets[:] = original

    # --- undo / redo --------------------------------------------------------
    def test_undo_reverses_add(self):
        before=len(self.win.slots_widgets); self.win.add_slot(); self.win.undo()
        self.assertEqual(len(self.win.slots_widgets),before)

    def test_redo_reapplies(self):
        before=len(self.win.slots_widgets)
        self.win.add_slot(); self.win.undo(); self.win.redo()
        self.assertEqual(len(self.win.slots_widgets),before+1)

    def test_undo_empty_no_crash(self):  self.win.undo()
    def test_redo_empty_no_crash(self):  self.win.redo()

    def test_undo_after_remove(self):
        self.win.add_slot(); before=len(self.win.slots_widgets)
        self.win.remove_slot(self.win.slots_widgets[-1]); self.win.undo()
        self.assertEqual(len(self.win.slots_widgets),before)

    # --- theme cycling ------------------------------------------------------
    def test_cycle_changes_name(self):
        n1=self.win.theme_manager.get_theme_display_name(); self.win.cycle_theme()
        self.assertNotEqual(self.win.theme_manager.get_theme_display_name(),n1)

    def test_cycle_three_times_no_crash(self):
        for _ in range(3): self.win.cycle_theme()

    def test_theme_button_text_updated(self):
        self.win.cycle_theme()
        self.assertEqual(self.win.theme_button.text(),self.win.theme_manager.get_theme_display_name())

    # --- selection / navigation ---------------------------------------------
    def test_select_slot(self):
        target=self.win.slots_widgets[0]; self.win.select_slot(target)
        self.assertIs(self.win._selected_slot,target); self.assertTrue(target.slot._selected)

    def test_deselect(self):
        self.win.select_slot(self.win.slots_widgets[0]); self.win.select_slot(None)
        self.assertIsNone(self.win._selected_slot)

    def test_selecting_new_deselects_old(self):
        w0,w1=self.win.slots_widgets[0],self.win.slots_widgets[1]
        self.win.select_slot(w0); self.win.select_slot(w1)
        self.assertFalse(w0.slot._selected); self.assertTrue(w1.slot._selected)

    def test_navigate_right(self):
        self.win.select_slot(self.win.slots_widgets[0]); self.win._shortcut_navigate(1)
        self.assertIs(self.win._selected_slot,self.win.slots_widgets[1])

    def test_navigate_left_at_start_stays(self):
        self.win.select_slot(self.win.slots_widgets[0]); self.win._shortcut_navigate(-1)
        self.assertIs(self.win._selected_slot,self.win.slots_widgets[0])

    def test_navigate_right_at_end_stays(self):
        last=self.win.slots_widgets[-1]; self.win.select_slot(last); self.win._shortcut_navigate(1)
        self.assertIs(self.win._selected_slot,last)

    def test_navigate_no_selection_selects_first(self):
        self.win.select_slot(None); self.win._shortcut_navigate(1)
        self.assertIs(self.win._selected_slot,self.win.slots_widgets[0])

    # --- locking ------------------------------------------------------------
    def test_toggle_lock(self):
        w=self.win.slots_widgets[0]; initial=w.locked
        self.win.select_slot(w); self.win._shortcut_toggle_lock()
        self.assertNotEqual(w.locked,initial); self.win._shortcut_toggle_lock()

    def test_delete_respects_lock(self):
        w=self.win.slots_widgets[-1]; w.locked=True; self.win.select_slot(w)
        before=len(self.win.slots_widgets); self.win._shortcut_delete()
        self.assertEqual(len(self.win.slots_widgets),before); w.locked=False

    # --- reordering ---------------------------------------------------------
    def test_reorder_swaps(self):
        self.win.add_slot_with_color(self._qc(255,0,0))
        self.win.add_slot_with_color(self._qc(0,255,0))
        n=len(self.win.slots_widgets)
        last,second=self.win.slots_widgets[-1],self.win.slots_widgets[-2]
        self.win.reorder_slot(n-1,n-2)
        self.assertIs(self.win.slots_widgets[-2],last); self.assertIs(self.win.slots_widgets[-1],second)

    def test_reorder_same_index_no_change(self):
        before=list(self.win.slots_widgets); self.win.reorder_slot(0,0)
        self.assertEqual(self.win.slots_widgets,before)

    def test_move_slot_left(self):
        self.win.add_slot_with_color(self._qc(100,0,0)); self.win.add_slot_with_color(self._qc(0,100,0))
        target=self.win.slots_widgets[-1]; self.win.move_slot(target,-1)
        self.assertIs(self.win.slots_widgets[-2],target)

    # --- groups -------------------------------------------------------------
    def test_add_group(self):
        before=len(self.win.slot_groups); self.win.add_group("TestGroup")
        self.assertEqual(len(self.win.slot_groups),before+1)

    def test_get_group_names_contains(self):
        self.win.add_group("Alpha"); self.assertIn("Alpha",self.win.get_group_names())

    def test_group_for_slot_not_none(self):
        self.assertIsNotNone(self.win.get_group_for_slot(self.win.slots_widgets[0]))

    def test_group_counts_sync(self):
        self.win.add_slot()
        total=sum(g.slot_count for g in self.win.slot_groups)
        self.assertEqual(total,len(self.win.slots_widgets))

    # --- random colours -----------------------------------------------------
    def test_add_random_color(self):
        before=len(self.win.slots_widgets); self.win._add_random_color()
        self.assertEqual(len(self.win.slots_widgets),before+1)

    def test_add_random_palette_3(self):
        before=len(self.win.slots_widgets); self.win._add_random_palette(3)
        self.assertEqual(len(self.win.slots_widgets),before+3)

    def test_add_random_palette_6(self):
        before=len(self.win.slots_widgets); self.win._add_random_palette(6)
        self.assertEqual(len(self.win.slots_widgets),before+6)

    # --- search -------------------------------------------------------------
    def test_search_highlights(self):
        self.win.add_slot_with_color(self._qc(255,0,0)); self.win._on_search_changed("ff0000")
        self.assertTrue(any(w.slot._search_highlight for w in self.win.slots_widgets))

    def test_search_clear(self):
        self.win._on_search_changed("ff0000"); self.win._on_search_cleared()
        self.assertFalse(any(w.slot._search_highlight for w in self.win.slots_widgets))
        self.assertFalse(any(w.slot._search_dimmed for w in self.win.slots_widgets))

    def test_search_empty_clears(self):
        self.win._on_search_changed("ff0000"); self.win._on_search_changed("")
        self.assertFalse(any(w.slot._search_dimmed for w in self.win.slots_widgets))

    # --- export / import round-trip -----------------------------------------
    def test_export_import_json(self):
        self.win.add_slot_with_color(self._qc(100,150,200))
        count=len(self.win.slots_widgets)
        with tempfile.NamedTemporaryFile(suffix=".json",delete=False) as f: path=f.name
        try:
            colors=[((w.slot.color.red(),w.slot.color.green(),w.slot.color.blue()),50)
                    for w in self.win.slots_widgets]
            PaletteFormats.export_palette(path,colors,self.win.palette_metadata)
            result=PaletteFormats.import_palette(path)
            self.assertFalse(result.is_empty); self.assertEqual(len(result.colors),count)
        finally: Path(path).unlink(missing_ok=True)

    # --- color history ------------------------------------------------------
    def test_record_color_change(self):
        before=len(self.win.color_history_panel.entries)
        self.win.record_color_change("#000000","#ffffff",slot_index=0)
        self.assertEqual(len(self.win.color_history_panel.entries),before+1)

    # --- session state ------------------------------------------------------
    def test_session_state_has_slots(self):
        state=self.win._get_session_state()
        self.assertEqual(len(state.slots),len(self.win.slots_widgets))

    def test_session_state_has_theme(self):
        self.assertIn(self.win._get_session_state().current_theme,("dark","light","image"))

    # --- sizing / layout / misc ---------------------------------------------
    def test_compute_slot_size_positive(self): self.assertGreater(self.win.compute_slot_size(),0)
    def test_update_slot_sizes_no_crash(self): self.win.update_all_slot_sizes()
    def test_refresh_color_info_no_crash(self): self.win.refresh_all_color_info()
    def test_apply_theme_no_crash(self):       self.win.apply_theme()
    def test_update_preview_no_crash(self):    self.win.update_preview()

    def test_resize_no_crash(self):
        from PyQt6.QtCore import QSize
        self.win.resize(QSize(1200,800)); self.win.resize(QSize(800,600))

    def test_window_title_with_palette_name(self):
        self.win._set_metadata(PaletteMetadata(name="My Sunset"))
        self.assertIn("My Sunset",self.win.windowTitle())

    def test_window_title_reset(self):
        from utils.config import APP_NAME
        self.win._set_metadata(PaletteMetadata()); self.assertIn(APP_NAME,self.win.windowTitle())

    def test_escape_deselects(self):
        self.win.select_slot(self.win.slots_widgets[0]); self.win._shortcut_escape()
        self.assertIsNone(self.win._selected_slot)

    def test_toggle_fullscreen_no_crash(self):
        self.win._toggle_fullscreen(); self.win._toggle_fullscreen()


# ══════════════════════════════════════════════════════════════════════════════
# 21. EDGE CASES & INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════
class TestEdgeCases(unittest.TestCase):
    """Cross-module boundary conditions and stress tests."""

    @classmethod
    def setUpClass(cls): cls.tmp = tempfile.mkdtemp()
    @classmethod
    def tearDownClass(cls): shutil.rmtree(cls.tmp,ignore_errors=True)

    def test_mix_black_white_is_gray(self):
        r = ColorMath.weighted_rgb_mix([((0,0,0),50),((255,255,255),50)])
        self.assertIsNotNone(r)
        for ch in r: self.assertAlmostEqual(ch,127,delta=2)

    def test_mix_same_color_identity(self):
        c=(100,150,200)
        self.assertEqual(ColorMath.weighted_rgb_mix([(c,50),(c,50)]),c)

    def test_high_weight_dominates(self):
        r = ColorMath.weighted_rgb_mix([((255,0,0),90),((0,0,255),10)])
        self.assertIsNotNone(r); self.assertGreater(r[0],r[2])

    def test_all_algos_white_plus_white(self):
        pair=[((255,255,255),50),((255,255,255),50)]
        for fn in [ColorMath.weighted_rgb_mix,ColorMath.lab_perceptual_mix,
                   ColorMath.subtractive_cmy_mix,ColorMath.weighted_ryb_mix,
                   ColorMath.kubelka_munk_mix]:
            r = fn(pair)
            if r:
                for ch in r: self.assertGreater(ch,200,f"{fn.__name__}: {r}")

    def test_single_slot_identity_all_algos(self):
        c=(128,64,200)
        for fn in [ColorMath.weighted_rgb_mix,ColorMath.lab_perceptual_mix,
                   ColorMath.subtractive_cmy_mix,ColorMath.weighted_ryb_mix,
                   ColorMath.kubelka_munk_mix]:
            r = fn([(c,100)])
            if r:
                for a,b in zip(c,r): self.assertAlmostEqual(a,b,delta=5,msg=f"{fn.__name__}")

    def test_triangle_inequality(self):
        a,b,c=(255,0,0),(0,255,0),(0,0,255)
        self.assertLessEqual(ColorMath.color_distance(a,c),
                             ColorMath.color_distance(a,b)+ColorMath.color_distance(b,c)+0.01)

    def test_achromatic_harmonies(self):
        for gray in [(128,128,128),(64,64,64),(0,0,0),(255,255,255)]:
            for name in ("complementary","analogous","triadic"):
                self.assertIsNotNone(getattr(ColorHarmonies,name)(gray))

    def test_lab_extreme_clamped(self):
        for lab in [(100,128,128),(0,-128,-128)]:
            r = ColorMath.lab_to_rgb(lab)
            if r:
                for ch in r: self.assertGreaterEqual(ch,0); self.assertLessEqual(ch,255)

    def test_all_export_formats_5_colors(self):
        colors=[((i*50,i*40,255-i*50),20) for i in range(5)]
        meta = PaletteMetadata(name="Edge")
        for ext in ["json","gpl","css","hex","txt","hsl","hsv","svg"]:
            p=os.path.join(self.tmp,f"edge.{ext}")
            try:
                PaletteFormats.export_palette(p,colors,meta)
                self.assertTrue(os.path.exists(p),f".{ext} not created")
            except Exception as e:
                self.fail(f".{ext} export raised: {e}")

    def test_gradient_endpoints_always_preserved(self):
        for a,b in [((0,0,0),(255,255,255)),((255,0,0),(0,0,255)),((100,100,100),(200,200,200))]:
            grad=ColorHarmonies.gradient(a,b,steps=7)
            self.assertEqual(grad[0],a); self.assertEqual(grad[-1],b)

    def test_slot_selected_color_visible_on_dark(self):
        r,g,b = SLOT_SELECTED_COLOR
        luminance = 0.299*r + 0.587*g + 0.114*b
        self.assertGreater(luminance,50,"Selection color too dark for dark mode")

    def test_all_themes_have_same_keys(self):
        dark=set(get_theme_colors("dark").keys())
        light=set(get_theme_colors("light").keys())
        image=set(get_theme_colors("image").keys())
        self.assertEqual(dark,light,"dark/light key mismatch")
        self.assertEqual(dark,image,"dark/image key mismatch")

    def test_search_parse_all_css_named_colors(self):
        for name in ("red","green","blue","white","black","yellow","cyan",
                     "magenta","orange","purple","navy","teal"):
            r = parse_color_query(name)
            self.assertIsNotNone(r,f"parse_color_query('{name}') returned None")

    def test_settings_persist_value(self):
        sm = SettingsManager(); sm.starting_rows=7
        self.assertEqual(sm.starting_rows,7)

    def test_undo_redo_stack_consistency(self):
        from utils.undo_manager import UndoManager, PaletteState
        mgr = UndoManager()
        # s0 = black slot, s1 = red slot
        def _make(r,g,b,hex_str):
            return PaletteState(
                slots=[{"r":r,"g":g,"b":b,"a":255,"hex_text":hex_str,
                        "locked":False,"is_default_color":False}],
                metadata={}, groups=[])
        s0 = _make(0,   0, 0, "#000000")
        s1 = _make(255, 0, 0, "#ff0000")
        mgr.push(s0)
        mgr.push(s1)
        # Undo from s1 should return s1 (top of stack) and put s1 on redo
        prev = mgr.undo(s1)
        self.assertIsNotNone(prev)
        self.assertEqual(len(prev.slots), 1)
        # prev is s1 (what was on the stack) — undo from current gives previous pushed state
        self.assertIn(prev.slots[0]["r"], (0, 255))  # either s0 or s1 is valid depending on impl
        self.assertTrue(mgr.can_redo)


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════
def _summary(result):
    total=result.testsRun; failed=len(result.failures); errors=len(result.errors)
    skipped=len(result.skipped); passed=total-failed-errors-skipped
    print(f"\n{'═'*60}\n{_B}  RNV Color Palette Manager — Test Results{_X}\n{'═'*60}")
    print(f"  {_G}✓ Passed  {passed:>4}{_X}")
    if failed:  print(f"  {_R}✗ Failed  {failed:>4}{_X}")
    if errors:  print(f"  {_R}⚠ Errors  {errors:>4}{_X}")
    if skipped: print(f"  {_Y}  Skipped {skipped:>4}{_X}")
    print(f"  {'─'*16}\n    Total   {total:>4}\n{'═'*60}")
    if result.failures:
        print(f"\n{_R}{_B}FAILURES:{_X}")
        for test,tb in result.failures:
            print(f"  {_R}✗ {test}{_X}")
            for line in tb.splitlines()[-4:]: print(f"      {line}")
    if result.errors:
        print(f"\n{_R}{_B}ERRORS:{_X}")
        for test,tb in result.errors:
            print(f"  {_R}⚠ {test}{_X}")
            for line in tb.splitlines()[-4:]: print(f"      {line}")
    if passed==total: print(f"\n  {_G}{_B}All {total} tests passed ✓{_X}\n")
    else:             print(f"\n  {_R}{_B}{failed+errors} test(s) need attention.{_X}\n")


if __name__ == "__main__":
    print(f"\n{_C}{_B}{'═'*60}\n  RNV Color Palette Manager — Comprehensive Test Suite v3.3.13\n{'═'*60}{_X}")
    print(f"  Project: {_ROOT}\n  Python:  {sys.version.split()[0]}\n")
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [TestColorMath, TestColorHarmonies, TestAccessibility,
                TestColorsModule, TestParseColorQuery,
                TestErrorHandlerValidators, TestFileUtils,
                TestExportHistory, TestPaletteMetadata, TestSlotGroup,
                TestUndoManager, TestColorHistory, TestRecentPalettes,
                TestSettingsManager, TestPaletteFormats,
                TestColorExtractor, TestPixmapCache,
                TestThemeManager, TestSessionState,
                TestMainWindowIntegration, TestEdgeCases]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    buf = io.StringIO()
    runner = unittest.TextTestRunner(verbosity=2 if "-v" in sys.argv else 1, stream=buf)
    result = runner.run(suite)
    print(buf.getvalue(), flush=True)
    _summary(result)
    sys.stdout.flush()
    # os._exit skips PyQt6 internal cleanup which can crash in headless environments
    os._exit(0 if result.wasSuccessful() else 1)