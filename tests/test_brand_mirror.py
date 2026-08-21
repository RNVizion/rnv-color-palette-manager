"""
Brand mirror and provenance guard.   RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN

This file NAMES RETIRED VALUES ON PURPOSE. Any sweep for a gold literal must
exclude it by the marker above, or it rewrites the very list that says which
values must never come back.

Ported from rnv-text-transformer, wired to this app's palettes.
"""
from __future__ import annotations

import ast
import pathlib
import subprocess

import pytest

from ui import colors as C

PALETTES = {
    "DARK": C.DARK_THEME_COLORS,
    "LIGHT": C.LIGHT_THEME_COLORS,
    "IMAGE": C.IMAGE_MODE_COLORS,
}

RETIRED = {
    "#b19145": "the old dark gold -- 2.997638 on white, under every floor it claimed",
    "(177, 145, 69)": "its RGB tuple, which a hex census cannot see",
    "(177,145,69)": "the same tuple without spaces",
}

GOLD_KEYS = ("accent", "accent_dark", "accent_ink")


def _luminance(value: str) -> float:
    h = value.lstrip("#")
    if len(h) == 8:
        h = h[2:]
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ------------------------------------------------------------- provenance

def test_provenance_covers_every_gold_constant():
    named = {n for n in dir(C)
             if n.startswith("BRAND_") and isinstance(getattr(C, n), str)}
    missing = named - set(C.GOLD_PROVENANCE)
    assert not missing, f"gold constants with no provenance entry: {sorted(missing)}"


def test_provenance_has_no_phantom_entries():
    phantom = [n for n in C.GOLD_PROVENANCE if not hasattr(C, n)]
    assert not phantom, f"provenance names nothing: {phantom}"


def test_register_values_match_rnv_brand():
    assert C.BRAND_GOLD == "#d2bc93"
    assert C.BRAND_DARK_GOLD == "#8c7337"


def test_the_derivation_steps_are_the_published_ones():
    assert C.BRAND_DARK_GOLD_DEEP == C.lighten(C.BRAND_DARK_GOLD, -14)
    assert C.BRAND_GOLD_HOVER == C.lighten(C.BRAND_GOLD, 13)
    assert C.BRAND_DARK_GOLD_DEEP == "#7e6529"
    assert C.BRAND_GOLD_HOVER == "#dfc9a0"


def test_derived_constants_are_not_written_as_literals():
    """A derivative restated by hand is orphaned the moment the base moves."""
    src = pathlib.Path(C.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    literals = {n.target.id for n in ast.walk(tree)
                if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
                and isinstance(n.value, ast.Constant)}
    for name, kind in C.GOLD_PROVENANCE.items():
        if kind == "derived":
            assert name not in literals, f"{name} is derived but written as a literal"


def test_the_rgb_tuples_are_derived_from_the_hex():
    """The trap this pass closed. Hand-written, they keep the retired gold
    through a value change, and a test asserting the two agree stays green."""
    assert C.BRAND_GOLD_RGB == C._to_rgb(C.BRAND_GOLD)
    assert C.BRAND_DARK_GOLD_RGB == C._to_rgb(C.BRAND_DARK_GOLD)
    src = pathlib.Path(C.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if (isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
                and node.target.id.endswith("_GOLD_RGB")):
            assert isinstance(node.value, ast.Call), (
                f"{node.target.id} is restated, not derived")


def test_lighten_holds_hue():
    base = C._to_rgb(C.BRAND_DARK_GOLD)
    deep = C._to_rgb(C.BRAND_DARK_GOLD_DEEP)
    assert {b - d for b, d in zip(base, deep)} == {14}, "the step is not uniform"


# ------------------------------------------------------ two golds per mode

@pytest.mark.parametrize("name", sorted(PALETTES))
def test_two_golds_per_mode(name):
    """One registered gold and one derivative. A third means a role went
    unshared -- and no contrast check would object, because an orphaned gold
    can be perfectly legible."""
    palette = PALETTES[name]
    golds = {palette[k].lower() for k in GOLD_KEYS}
    assert len(golds) == 2, (
        f"{name} renders {len(golds)} golds: {sorted(golds)}")


@pytest.mark.parametrize("name", sorted(PALETTES))
def test_the_gold_key_list_still_matches_the_palette(name):
    """Guard the guard: rename a gold key and the count above would silently
    measure fewer of them and keep passing."""
    missing = [k for k in GOLD_KEYS if k not in PALETTES[name]]
    assert not missing, f"{name} no longer has {missing}"


def test_light_ink_clears_every_ground_it_draws_on():
    ink = PALETTES["LIGHT"]["accent_ink"]
    for ground in ("#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"):
        assert contrast(ink, ground) >= 4.5, f"{ink} on {ground}"


def test_dark_reuses_its_accent_for_ink():
    for name in ("DARK", "IMAGE"):
        assert PALETTES[name]["accent_ink"] == PALETTES[name]["accent"], name


def test_hover_moves_away_from_the_ground():
    light = PALETTES["LIGHT"]
    assert _luminance(light["accent_ink"]) < _luminance(light["accent"])
    for name in ("DARK", "IMAGE"):
        p = PALETTES[name]
        assert _luminance(p["accent_dark"]) > _luminance(p["accent"]), (
            f"{name} accent_dark must move lighter, away from a dark ground")


def test_the_light_gold_stays_out_of_the_dark_palettes():
    for name in ("DARK", "IMAGE"):
        offenders = [k for k, v in PALETTES[name].items()
                     if isinstance(v, str) and v.lower() == C.BRAND_DARK_GOLD.lower()]
        assert not offenders, (
            f"{name} carries the light-mode gold on {offenders}")


def test_text_on_gold_is_black_and_stays_black():
    """This is the only one of the five that paints black on the light fill.
    It is what the register prefers and the better number. Not to be flattened
    to match the others."""
    for name, palette in PALETTES.items():
        assert palette["accent_text"] == "#000000", name
    assert contrast("#000000", PALETTES["LIGHT"]["accent"]) >= 4.5


# ------------------------------------------------------------ retired values

def _sources():
    root = pathlib.Path(C.__file__).resolve().parent.parent
    out = subprocess.run(["git", "ls-files"], cwd=root,
                         capture_output=True, text=True).stdout.split()
    for rel in out:
        path = root / rel
        if path.suffix.lower() not in (".py", ".qss", ".css", ".md"):
            continue
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8-sig" if raw.startswith(b"\xef\xbb\xbf")
                              else "utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="surrogateescape")
        if "RNV-GOLD-GUARD-FILE-NAMES-RETIRED-VALUES-BY-DESIGN" in text or "RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP" in text:
            continue
        yield rel, text


def test_retired_values_do_not_appear():
    hits = []
    for rel, text in _sources():
        low = text.lower()
        for value, why in RETIRED.items():
            if value.lower() in low:
                hits.append(f"{rel}: {value} ({why})")
    assert not hits, "retired gold still present -- " + "; ".join(hits)


def test_the_retired_scan_is_still_looking():
    files = list(_sources())
    assert len(files) > 15, f"the scan found only {len(files)} files"
    assert any(rel == "ui/colors.py" for rel, _ in files), \
        "the scan is not reading the colour file"


def test_the_old_identifier_is_gone():
    for rel, text in _sources():
        assert "BRAND_GOLD_DARK" not in text, (
            f"{rel} still uses the retired identifier BRAND_GOLD_DARK")
