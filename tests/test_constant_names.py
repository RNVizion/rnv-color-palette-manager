"""A constant names a colour, not a role. RNV-NAME-GUARD

Ruled by Chris on 2026-09-02. Eleven names in this application answered both
questions at once -- what colour is this, and what is it painting -- and two
answered neither, because nothing used them.

The pairs that looked like palette keys were not: they were inline
`X if is_light else Y` branches whose two arms were black and white. The
branch was carrying the mode all along; only the arms needed naming honestly.
"""
from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path

from ui import colors

ROOT = Path(__file__).resolve().parent.parent
RETIRED = ('ACCENT_PRESSED_TEXT_DARK', 'ACCENT_PRESSED_TEXT_LIGHT', 'TEXTEDIT_BG_DARK', 'TEXTEDIT_BG_LIGHT', 'SELECTION_OVERLAY_TEXT', 'IMAGE_PREVIEW_BORDER', 'IMAGE_PREVIEW_BG', 'DARK_GOLD_DEEP', 'SLOT_SELECTED_COLOR', 'CHECKBOX_ACCENT', 'SVG_EXPORT_TEXT_DARK', 'SVG_EXPORT_TEXT_LIGHT')
SKIP = {".git", "build", "dist", ".venv", "__pycache__"}


def _code_only(text: str) -> str:
    """The file with every comment and string literal removed.

    A guard that sweeps for the thing it forbids must tell a use from a
    mention. Doing that by excluding files stops working the moment a third
    file has a legitimate reason to say the word; tokenising needs no list.
    """
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            out.append(tok.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text
    return " ".join(out)


def _sources():
    for path in sorted(ROOT.rglob("*.py")):
        if any(p in SKIP for p in path.parts):
            continue
        text = path.read_bytes().decode("utf-8-sig", errors="replace")
        if "RNV-NAME-GUARD" in text or "RNV-NAMING-TOOL-DO-NOT-SWEEP" in text:
            continue
        yield path, text


def test_the_retired_names_are_gone():
    strays = []
    for path, text in _sources():
        for old in RETIRED:
            if re.search(r"\b%s\b" % re.escape(old), text):
                strays.append(f"{path.relative_to(ROOT)}: {old}")
    assert not strays, "retired names are still in use:\n  " + "\n  ".join(strays)


def test_the_values_they_named_are_still_here():
    """A rename that loses a value is not a rename. These are the colours the
    eleven role names were standing in front of."""
    assert colors.TRUE_BLACK == "#000000"
    assert colors.WHITE == "#ffffff"
    assert colors.GREY_66 == "#666666"
    assert colors.GREY_F0 == "#f0f0f0"
    assert colors.BRAND_DARK_GOLD_DEEP == "#7e6529"


def test_the_checkbox_still_uses_the_mode_selected_gold():
    """CHECKBOX_ACCENT was Windows blue, exported, and used by nothing. The
    checked checkbox has always been painted with the accent. Deleting the
    dead constant must not have disturbed the live one."""
    src = (ROOT / "ui" / "settings_dialog.py").read_text(encoding="utf-8-sig")
    checked = re.search(
        r"QCheckBox::indicator:checked \{\{(?P<body>.*?)\}\}", src, re.S)
    assert checked, "the checked-checkbox rule is gone from the stylesheet"
    body = checked.group("body")
    assert "background-color: {accent}" in body, (
        "the checked checkbox no longer fills with the mode-selected accent")
    assert "border-color: {accent_dark}" in body
    for palette in (colors.DARK_THEME_COLORS, colors.LIGHT_THEME_COLORS):
        assert palette["accent"] in (colors.BRAND_GOLD, colors.BRAND_DARK_GOLD)


def test_no_windows_blue_anywhere():
    """The value it held is on no ladder, no grid and no brand."""
    strays = []
    for path, text in _sources():
        if re.search(r"""['"]#0078d4['"]""", text, re.I):
            strays.append(str(path.relative_to(ROOT)))
    assert not strays, f"#0078d4 is back in: {strays}"


def test_the_ink_rule_is_a_real_contrast_measurement():
    assert colors.contrast_ink("#ffffff") == colors.TRUE_BLACK
    assert colors.contrast_ink("#000000") == colors.WHITE
    assert round(colors.contrast_ratio("#ffffff", "#000000"), 2) == 21.0


def test_the_exported_svg_labels_follow_the_rule():
    """snapshots/canonical.svg pins the export byte for byte. Pure red and
    pure green used to carry white labels at 4.00:1 and 1.37:1, because the
    mean of the channels called them dark. They carry black now."""
    svg = (ROOT / "snapshots" / "canonical.svg").read_text(encoding="utf-8")
    pairs = re.findall(
        r'<rect x="\d+"[^>]*fill="(#[0-9a-fA-F]{6})"[^>]*/>\s*'
        r'<text[^>]*fill="(#[0-9a-fA-F]{6})"', svg)
    assert len(pairs) == 5, f"expected 5 swatches in the snapshot, found {len(pairs)}"
    for ground, ink in pairs:
        assert ink.lower() == colors.contrast_ink(ground), (
            f"the snapshot writes {ink} on {ground}; the rule says "
            f"{colors.contrast_ink(ground)}")


def test_the_ink_rule_gets_saturated_colour_right():
    """The case sum(color) / 3 got wrong. Pure green is a LIGHT ground."""
    assert colors.contrast_ink((0, 255, 0)) == colors.TRUE_BLACK
    assert colors.contrast_ratio((0, 255, 0), colors.TRUE_BLACK) > 15
    assert sum((0, 255, 0)) / 3 < 128       # what the old rule saw


def test_no_call_site_measures_brightness_by_hand():
    """Reads code with comments and strings removed, so the note above the
    replaced call site -- which names the arithmetic it retired -- does not
    fail the sweep that forbids it."""
    mean = re.compile(r"sum \( colou?r \) / 3|\( r \+ g \+ b \) / 3")
    luma = re.compile(r"\* 299\b|\* 587\b|\* 114\b")
    strays = []
    for path, text in _sources():
        code = _code_only(text)
        if mean.search(code) or luma.search(code):
            strays.append(str(path.relative_to(ROOT)))
    assert not strays, f"hand-rolled brightness rules are back in: {strays}"


def test_every_source_file_is_utf8():
    """core/palette_formats.py carried cp1252 em-dashes. CPython let it run
    because they sat in comments; an audit script read it with plain UTF-8,
    swallowed the decode error, skipped the file, and reported four live
    constants as dead. A sweep that cannot read a file is worse than one that
    fails."""
    bad = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(p in SKIP for p in path.parts):
            continue
        try:
            path.read_bytes().decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            bad.append(f"{path.relative_to(ROOT)}: {exc}")
    assert not bad, "not valid UTF-8:\n  " + "\n  ".join(bad)
