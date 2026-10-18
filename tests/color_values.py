"""Every color value the tests need that is not one of the application's own.

RNV-COLOR-SYNC (#53 A), 2026-10-17. The application's colors, brand and its
own, are named in ui/colors.py, which brand_map.json names, and a test reads
them from there. Every other color value a test or the root suite writes is
named here, once, with why, grouped by kind. tests/test_color_values.py holds
this file: no color value is written anywhere else, each name says what kind
it is and why, each is used, and each REGISTER_ value is the brand's at the pin.

Tests under tests/ read it as `from color_values import ...`; the root suite,
run from the repository root, as `from tests.color_values import ...`.

RNV-COLLAPSE-GUARD
    tests/test_collapse_505050.py sweeps every evaluated string for #505050 in
    any spelling and skips files carrying this; this file names it, as OLD_HEX
    and in each spelling the decoder must read, in order to forbid it.
RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN
    tests/test_brand_mirror.py scans raw text for the retired dark gold #b19145
    and its two tuple spellings, and skips files carrying this; this file names
    them as that guard's RETIRED list.
RNV-NAME-GUARD
    tests/test_constant_names.py sweeps raw text for the retired Windows blue,
    quoted, and skips files carrying this; this file names it as
    RETIRED_WINDOWS_BLUE, which that sweep's pattern is built from.
"""

# ---------------------------------------------------------------------------
# Examples: samples given to a helper, a reader or the color math
# ---------------------------------------------------------------------------

EXAMPLE_BLACK = "#000000"
"""Pure black as a sample: a ColorMath conversion's input or output, a ground
for contrast() and contrast_ink(), and what a reader or the integer sweep makes
of black in its self-test. It equals TRUE_BLACK and does not mean it."""

EXAMPLE_BLACK_SHORT = "#000"
"""Black in three digits, written in the ink guard's sample sheet; the reader
must expand it to EXAMPLE_BLACK."""

EXAMPLE_BLACK_BARE = "000000"
"""The six digits the ARGB reader in tests/test_error_red.py must take from
EXAMPLE_ARGB_BLACK_AT_ED: alpha dropped, no hash."""

EXAMPLE_WHITE = "#ffffff"
"""Pure white as a sample: a ColorMath conversion's input or output, a ground
for contrast() and contrast_ink(), and what the ink guard's reader makes of
`white`. It equals WHITE and does not mean it."""

EXAMPLE_WHITE_SHORT = "#fff"
"""White in three digits: hex_to_rgb must expand the shorthand."""

EXAMPLE_RED = "#ff0000"
"""(255, 0, 0) as rgb_to_hex writes it."""

EXAMPLE_RED_UPPER = "#FF0000"
"""The same red in upper case: hex_to_rgb must read either case."""

EXAMPLE_RED_SHORT = "#f00"
"""The same red in three digits: hex_to_rgb must expand the shorthand."""

EXAMPLE_RED_BARE = "ff0000"
"""The same red with no hash: hex_to_rgb must take it."""

EXAMPLE_GREEN = "#00ff00"
"""(0, 255, 0) as rgb_to_hex writes it."""

EXAMPLE_BLUE = "#0000ff"
"""(0, 0, 255) as rgb_to_hex writes it."""

EXAMPLE_SHORT_GRAY = "#555"
"""A three-digit gray the collapse guard's decoder must expand. The point is
the shorthand, not the gray."""

EXAMPLE_SHORT_GRAY_EXPANDED = "#555555"
"""What the decoder must make of EXAMPLE_SHORT_GRAY. It equals GRAY_55 and does
not mean it."""

EXAMPLE_ARGB_ALPHA_FIRST = "#96444444"
"""An eight-digit #AARRGGBB the collapse guard's decoder must read ALPHA FIRST.
It equals image mode's scrollbar handle today; the test is of the decoder, so
it must not follow the palette."""

EXAMPLE_ARGB_ALPHA_FIRST_DECODED = "#444444"
"""The color EXAMPLE_ARGB_ALPHA_FIRST holds once its alpha is taken off the
front."""

EXAMPLE_ARGB_ALPHA_FIRST_MISREAD = "#964444"
"""What EXAMPLE_ARGB_ALPHA_FIRST becomes if the first six digits are taken
instead of the last: a real color and the wrong one."""

EXAMPLE_HAND_EDIT = "#123456"
"""A value a person might type over a color file line by hand, which the sync
must put back; and the color of a constant the map does not hold."""

EXAMPLE_HAND_EDIT_FALLBACK = "#654321"
"""The hand edit to use when the line already holds EXAMPLE_HAND_EDIT."""

EXAMPLE_MOVED_ACCENT = "#6f94bc"
"""A hypothetical new value for the brand's accent, to show a brand move reaches
the one line that takes it."""

EXAMPLE_MOVED_ACCENT_FALLBACK = "#456c91"
"""The moved accent to use when the accent already is EXAMPLE_MOVED_ACCENT."""

EXAMPLE_CHARCOAL = "#1a1a1a"
"""A base handed to translucent() and translucent_rgba(). It equals BRAND_BLACK
today; the composed values the tests expect are written out, so the base must
not follow the brand. Lower case: the round trip compares it as written."""

EXAMPLE_CHARCOAL_BARE_UPPER = "1A1A1A"
"""EXAMPLE_CHARCOAL with no hash and in upper case, both of which translucent()
accepts and lower-cases."""

EXAMPLE_CHARCOAL_AT_ED = "#ed1a1a1a"
"""translucent(EXAMPLE_CHARCOAL, 0xED): eight digits, alpha first, lower case."""

EXAMPLE_CHARCOAL_RGBA_191 = "rgba(26, 26, 26, 191)"
"""translucent_rgba(EXAMPLE_CHARCOAL, 191), in the spelling it writes."""

EXAMPLE_BLACK_RGBA_200 = "rgba(0, 0, 0, 200)"
"""translucent_rgba(EXAMPLE_BLACK, 0xC8), in the spelling it writes. It equals
SIZE_OVERLAY_BG and does not mean it: the test is of the helper."""

EXAMPLE_TAN = "#d2bc93"
"""A base handed to the alpha helpers. It equals BRAND_GOLD today and must not
follow it: the composed value the test expects is written out."""

EXAMPLE_TAN_AT_33 = "#33d2bc93"
"""translucent(EXAMPLE_TAN, 0x33)."""

EXAMPLE_MID_GRAY = "#444444"
"""A base for the alpha helpers' round trip, and what the integer sweep reads
from its probe's QColor(68, 68, 68). It equals GRAY_44 and does not mean it."""

EXAMPLE_ARGB_BLACK_AT_ED = "#ed000000"
"""An eight-digit #AARRGGBB the ARGB reader in tests/test_error_red.py must not
read as EXAMPLE_ARGB_BLACK_AT_ED_MISREAD. It equals image mode's window ground
today; the test is of the reader."""

EXAMPLE_ARGB_BLACK_AT_ED_MISREAD = "#ed0000"
"""What EXAMPLE_ARGB_BLACK_AT_ED becomes read naively as #RRGGBB: a red. The
contrast against it computes to 1.6448 instead of the ~7.57 the eye sees."""

EXAMPLE_OFF_WHITE = "#f5f5f5"
"""A six-digit value the ARGB reader must pass through unchanged. It equals
APP_SURFACE_LIGHT_3 and does not mean it."""

EXAMPLE_OFF_WHITE_BARE = "f5f5f5"
"""What the ARGB reader gives back for EXAMPLE_OFF_WHITE: its six digits."""

EXAMPLE_SWEEP_PROBE_HEX = "#ffcccc"
"""The hex in the named-and-used sweep's probe line, which the sweep must report,
and in the probe's prose, which it must not."""

EXAMPLE_SWEEP_PROBE_RGBA = "rgba(255, 255, 255, 230)"
"""The rgba() in the named-and-used sweep's probe line, in the single-spaced form
the sweep reports it in."""

EXAMPLE_CLEAR_RGBA = "rgba(0, 0, 0, 0)"
"""Clear: alpha 0, how a widget is told to paint nothing. The named-and-used
sweep's quiet probe holds it, and the sweep must not report it as a color."""

EXAMPLE_STATUS_ERROR_LIGHTENED = "#b44753"
"""lighten(REGISTER_STATUS_ERROR, -20): what the retired rule for the light
error text yields against the register's error base since 2026-09-03. Neither
the old RETIRED_ERROR_TEXT_LIGHT_ORPHAN nor the registered value; a third
answer, which is why the light error text is registered, not derived."""

EXAMPLE_BENCH_PURPLE = "#7B2DC8"
"""The input to the hex_to_rgb benchmark, in upper case: (123, 45, 200), the
color the other conversion benchmarks use."""

# ---------------------------------------------------------------------------
# Data: what a user, the search box, a record or the settings supply
# ---------------------------------------------------------------------------

DATA_QUERY_RED = "#ff0000"
"""Red typed into the search box, as parse_color_query reads it."""

DATA_QUERY_RED_UPPER = "#FF0000"
"""The same search in upper case."""

DATA_QUERY_RED_SHORT = "#f00"
"""The same search in three digits."""

DATA_QUERY_RED_BARE = "ff0000"
"""The same search with no hash, as the main window's search box receives it."""

DATA_QUERY_RED_PADDED = "  #ff0000  "
"""The same search with spaces round it, which the parser must strip. The spaces
are the point."""

DATA_QUERY_GREEN_BARE = "00ff00"
"""Green typed into the search box with no hash."""

DATA_QUERY_GREEN_RGB = "rgb(0,255,0)"
"""Green typed as rgb() with no spaces, which is the case the test is about."""

DATA_QUERY_WHITE_SHORT = "#fff"
"""White typed into the search box in three digits."""

DATA_HEX_INPUT_ORANGE = "#FF8800"
"""A valid hex as a person types it, for ValidationHelper.validate_hex_color."""

DATA_HEX_INPUT_ORANGE_BARE = "FF8800"
"""The same hex typed with no hash, which validate_hex_color accepts."""

DATA_HEX_INPUT_ORANGE_SHORT = "#F80"
"""The same orange typed in three digits, which validate_hex_color accepts."""

DATA_HISTORY_BLACK = "#000000"
"""A slot change's color in a color-history record. It equals TRUE_BLACK and
does not mean it: a record holds what the user chose."""

DATA_HISTORY_WHITE = "#ffffff"
"""A slot change's color in a color-history record. It equals WHITE and does
not mean it."""

DATA_HISTORY_BLACK_SHORT = "#000"
"""Black as a color-history record or a session's history holds it, in three
digits."""

DATA_HISTORY_WHITE_SHORT = "#fff"
"""White as a color-history record or a session's history holds it, in three
digits."""

DATA_HISTORY_SLATE = "#aabbcc"
"""A slot change's old color in a color-history record."""

DATA_HISTORY_NAVY = "#112233"
"""A slot change's new color in a color-history record."""

DATA_HISTORY_PALE_BLUE = "#ddeeff"
"""A slot change's new color in a history entry's round trip."""

DATA_HISTORY_DARK_RED = "#aa0000"
"""A slot change's old color, for the history's list round trip."""

DATA_HISTORY_GREEN = "#00aa00"
"""A slot change's new color, for the history's list round trip."""

DATA_HISTORY_GRAY_1 = "#111111"
"""The first of four distinct history colors, recorded oldest first, for the
newest-first check."""

DATA_HISTORY_GRAY_2 = "#222222"
"""The second of the four history colors."""

DATA_HISTORY_GRAY_3 = "#333333"
"""The third of the four history colors. It equals APP_BORDER and does not
mean it."""

DATA_HISTORY_GRAY_4 = "#444444"
"""The last of the four history colors, which must come back first. It equals
GRAY_44 and does not mean it."""

DATA_SETTINGS_SLOT_COLOR = "#123456"
"""A default slot color a person sets for dark mode, round-tripped through
SettingsManager."""

DATA_SLOT_RED = "#ff0000"
"""A red slot's color: what a saved session and an undo state hold beside its
channels (255, 0, 0), and what a slot made from those channels must paint."""

DATA_SLOT_BLACK = "#000000"
"""A slot's hex as an undo state holds it, beside its channels (0, 0, 0)."""

DATA_IMAGE_YELLOW = "#ffff00"
"""The fill of an image set on a slot, from its channels (255, 255, 0), which the
slot must paint in place of its own color."""

# ---------------------------------------------------------------------------
# Retired: values the application no longer uses, kept so a test can say so
# ---------------------------------------------------------------------------

RETIRED_OLD_DARK_GOLD = "#b19145"
"""The old light-mode gold, retired 2026-08-17: 2.997638 on white, under every
floor it claimed. Lower case: the gold guard compares lower-cased text."""

RETIRED_OLD_DARK_GOLD_RGB_SPACED = "(177, 145, 69)"
"""The old gold as the RGB tuple a hex census cannot see, written with spaces,
as the gold guard searches raw text for it."""

RETIRED_OLD_DARK_GOLD_RGB_TIGHT = "(177,145,69)"
"""The same tuple without spaces."""

RETIRED_OLD_HOVER_GOLD = "#c4a458"
"""The hover tint once written out beside RETIRED_OLD_DARK_GOLD. When that base
moved, the tint stayed behind: a value derived from something no longer in the
palette, the failure every "derived, not written" rule in this fleet cites."""

RETIRED_GRAY_E0 = "#e0e0e0"
"""APP["text"] until 2026-08-28, and two light surfaces nothing read: one hex
doing two jobs. The ink moved to APP_TEXT; the surfaces went on 2026-10-04."""

RETIRED_GRAY_50 = "#505050"
"""The handle and plate gray ruled onto GRAY_44 (RNV-COLLAPSE-505050), the
collapse guard's OLD_HEX."""

RETIRED_GRAY_50_DIGITS = "505050"
"""Its six digits, which no spelling of image mode's scrollbar handle may hold."""

RETIRED_GRAY_50_ARGB_96 = "#96505050"
"""The retired gray at alpha 0x96, alpha first, for the decoder's self-test."""

RETIRED_GRAY_50_ARGB_FF_UPPER = "#FF505050"
"""The retired gray opaque, alpha first, in upper case on purpose: the decoder
must read either case."""

RETIRED_GRAY_50_RGBA_100 = "rgba(80, 80, 80, 100)"
"""The exact spelling image mode painted its scrollbar handle in until
2026-09-25, while the first version of the collapse guard reported it gone."""

RETIRED_GRAY_50_RGBA_FRACTION = "rgba(80,80,80,0.6)"
"""The retired gray as a compact rgba() with a fractional alpha."""

RETIRED_GRAY_50_RGB = "rgb(80, 80, 80)"
"""The retired gray as rgb()."""

RETIRED_SCROLLBAR_BORDER_LITERAL = "rgba(51, 51, 51, 100)"
"""The literal image mode's scrollbar border was written as until 2026-09-25,
whose alpha SCROLLBAR_BORDER_ALPHA keeps. Now translucent(APP_BORDER, ...)."""

RETIRED_SIZE_OVERLAY_LITERAL = "rgba(0, 0, 0, 200)"
"""The literal the size overlay was written as until 2026-09-25, whose alpha
SIZE_OVERLAY_ALPHA keeps. SIZE_OVERLAY_BG still spells the same, now derived;
this records the literal, and does not follow it."""

RETIRED_SLOT_IMAGE_LITERAL = "rgba(0, 0, 0, 171)"
"""The literal a new image-mode slot's fill was written as, whose alpha
SLOT_IMAGE_ALPHA keeps."""

RETIRED_WINDOW_OVERLAY_LITERAL = "#ED000000"
"""The literal APP_WINDOW_OVERLAY was written as until 2026-09-24, in upper
case. The six-digit sweep of 2026-08-29 never matched it to TRUE_BLACK, and
RNV-LOWER-EIGHT (2026-09-25) writes eight digits in lower case."""

RETIRED_PANEL_OVERLAY_LITERAL = "#ED1A1A1A"
"""The literal APP_PANEL_OVERLAY was written as until 2026-09-24, in upper
case, which RNV-LOWER-EIGHT retired."""

RETIRED_GRAY_D0 = "#d0d0d0"
"""The light hover plate rnv-brand retired as an interaction ground: gold text
on it read 3.6013. Lower case: the test compares lower-cased values."""

RETIRED_GRAY_FA = "#fafafa"
"""A light stray collapsed onto the register's surface-light-2 on 2026-09-06."""

RETIRED_GRAY_F8 = "#f8f8f8"
"""A light stray collapsed onto the register's surface-light-2 on 2026-09-06."""

RETIRED_GRAY_F0 = "#f0f0f0"
"""The light stray ui/image_upload_dialog.py painted, collapsed onto GRAY_EE on
2026-09-06."""

RETIRED_MATERIAL_RED = "#f44336"
"""Material's red, a palette's dead 'error' entry until it was ruled out.
Lower case: the tests compare lower-cased values."""

RETIRED_MATERIAL_GREEN = "#4caf50"
"""Material's green, ruled out as a status value 2026-09-02."""

RETIRED_OWN_DARK_ERROR_TEXT = "#ff6b6b"
"""This application's own dark error text, ruled out 2026-09-02 for the
register's."""

RETIRED_BOOTSTRAP_GREEN = "#28a745"
"""Bootstrap's success green, retired by the register 2026-09-03
(RNV-STATUS-FAMILY)."""

RETIRED_BOOTSTRAP_AMBER = "#ffc107"
"""Bootstrap's warning amber, retired 2026-09-03."""

RETIRED_BOOTSTRAP_RED = "#dc3545"
"""Bootstrap's error red, retired 2026-09-03; the base of the two orphans below."""

RETIRED_ERROR_TEXT_ORPHAN = "#e56b77"
"""The dark error text derived from RETIRED_BOOTSTRAP_RED, retired with it."""

RETIRED_ERROR_TEXT_LIGHT_ORPHAN = "#c82131"
"""The light error text derived from RETIRED_BOOTSTRAP_RED, retired with it. It
read 4.6100 on REGISTER_GOLD_TEXT_GROUND_FLOOR."""

RETIRED_REV30_SUCCESS_TEXT_LIGHT = "#8a6581"
"""The register's light success text at rev 30, walked against
APP_SURFACE_LIGHT_3; rev 31 re-walked it against
REGISTER_GOLD_TEXT_GROUND_FLOOR. This application never drew it."""

RETIRED_REV30_WARNING_TEXT_LIGHT = "#976633"
"""The register's light warning text at rev 30, re-walked at rev 31. This
application never drew it."""

RETIRED_REV30_ERROR_TEXT_LIGHT = "#b84e58"
"""The register's light error text at rev 30, which read 4.0150 on
REGISTER_GOLD_TEXT_GROUND_FLOOR; rev 31 re-walked it to STATUS_ERROR_TEXT_LIGHT."""

RETIRED_CSS_GRAY = "#808080"
"""The CSS `gray` six muted labels in two dialogs were written in, in every
mode, until RNV-MUTED-DESCRIPTIONS (2026-09-27) drew them in text_secondary."""

RETIRED_WINDOWS_BLUE = "#0078d4"
"""The Windows blue a constant nothing used held until 2026-09-02: on no ladder,
no grid and no brand."""

# ---------------------------------------------------------------------------
# Register: values the brand publishes that this application does not draw
# ---------------------------------------------------------------------------

REGISTER_GOLD_TEXT_GROUND_FLOOR = "#e8e8e8"
"""The darkest light ground the gold family carries text on, and the floor the
light status texts were re-walked to. The application draws no ground at it.
Lower case: the tests compare lower-cased values."""

REGISTER_APP_SURFACE_LIGHT_2 = "#fbfbfb"
"""The register's second light surface rung: a rung the light texts are measured
on, and the rung two light strays collapsed onto. This application draws none."""

REGISTER_APP_PRESSED_LIGHT = "#e0e0e0"
"""The register's light pressed plate, where no brand text carries: the boundary
the light texts are held to fail at."""

REGISTER_STATUS_ERROR = "#c75b64"
"""The register's error fill, which this application does not carry: the base
the light error text is shown not to be derived from."""

# ---------------------------------------------------------------------------
# Invalid: written wrongly on purpose, for a test that refuses it
# ---------------------------------------------------------------------------

INVALID_HEX_FIVE_DIGITS = "#12345"
"""Five digits: validate_hex_color must refuse it and the collapse decoder must
not read a color in it."""

INVALID_HEX_FOUR_DIGITS = "#FF88"
"""Four digits, which validate_hex_color must refuse for its length."""

INVALID_HEX_NOT_HEX = "#GG8800"
"""Six characters, two of them not hex digits."""

INVALID_HEX_NOT_HEX_BARE = "ZZZZZZ"
"""Six characters with no hash, none of them hex digits."""

INVALID_BASE_FIVE_DIGITS = "#1a1a1"
"""A base one digit short, which translucent() and translucent_rgba() refuse."""

INVALID_BASE_EIGHT_DIGITS = "#1a1a1a1a"
"""A base that already carries an alpha, which the alpha helpers refuse."""

INVALID_BASE_NOT_HEX = "#gggggg"
"""A base of six characters that are not hex digits."""

# ---------------------------------------------------------------------------

REGISTER_REFS = {
    "REGISTER_GOLD_TEXT_GROUND_FLOOR": "GOLD_TEXT_GROUND_FLOOR",
    "REGISTER_APP_SURFACE_LIGHT_2": "APP.surface-light-2",
    "REGISTER_APP_PRESSED_LIGHT": "APP.pressed-light",
    "REGISTER_STATUS_ERROR": "STATUS.error",
}
"""Each REGISTER_ value's name in the brand; tests/test_color_values.py holds
the value to the brand at the pin."""
