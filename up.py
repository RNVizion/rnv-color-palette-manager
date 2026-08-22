#!/usr/bin/env python3
"""rnv-color-palette-manager -- error text per mode, a dead key, and the deps.

WHAT THIS CHANGES

1. ERROR TEXT BECOMES THEME-AWARE

   STATUS_ERROR_TEXT was ONE value, #ff6b6b, used in both modes. On this
   app's light dialog ground it reads 2.5454 -- far below the 4.5 text floor,
   and below even the 3.0 UI floor. It was the worst error-colour pairing in
   the family and nobody had recorded it.

       STATUS_ERROR             '#dc3545'                        register
       STATUS_ERROR_TEXT        '#ff6b6b'                        dark, unchanged
       STATUS_ERROR_TEXT_LIGHT  lighten(STATUS_ERROR, -20)       -> #c82131

   Light goes 2.5454 -> 5.1811 on #f5f5f5. Dark keeps #ff6b6b, which reads
   7.5674 on this app's #000000 dialog ground and was never short -- the
   ruling of this pass leaves passing dark values alone.

   STATUS_ERROR is introduced as the registered base so the light value is
   DERIVED rather than written down. A hand-written derivative orphans the
   moment its base moves; that is what happened to #c4a458 when the gold it
   tinted was retired. This app renders no error FILL, so the base itself is
   not drawn -- it is here to be derived from, and says so.

   The two call sites follow the file's own idiom. `_apply_theme` already
   writes `is_light = (self._theme_manager.current_theme == 'light')` to pick
   between ACCENT_PRESSED_TEXT_LIGHT and _DARK; the error text now picks the
   same way, through a small helper so both sites cannot drift apart.

2. A DEAD PALETTE KEY, DELETED

   'error': '#f44336' sat in all three palettes -- the Material red the
   family retired in favour of Bootstrap. It is an ORPHAN: no application
   code path reads it.

   That was not concluded from a grep. Each value was replaced in place with
   an instrumented string and the full suite run: across 774 tests the key
   was touched twice, both times by a test that sweeps every palette value,
   while a known-live control key lit up 34 times in the same run. A detector
   that can return "nothing found" needs a companion proving it is still
   looking -- the first version of that watcher reported "unused" for
   window_bg too, and was measuring nothing at all.

   Deleting it removes #f44336 from the family entirely.

3. TEST DEPENDENCIES MOVE

       requirements-dev.txt  ->  tests/requirements-dev.txt

   Twelve references across two workflows, two docs, and both build scripts.
   Two of them are `cache-dependency-path:` keys, which are the quiet ones:
   miss those and nothing fails -- the cache key simply stops matching and CI
   is slower forever, with no error to notice.

TREE DIAGRAMS ARE NOT PATHS

   README.md and TESTING.md draw the file in a tree, where indentation
   supplies the directory. Those entries move to sit under `tests/` rather
   than being rewritten to `tests/requirements-dev.txt`, which would read as
   tests/tests/... to anyone looking at the diagram.

USAGE

    python up.py --check     # dry run; every pass runs, nothing written
    python up.py             # apply
    python up.py --finish    # delete this script

Needs Python 3.12+ to run the suite afterwards (the repo uses PEP 695 `type`
statements); the script itself runs on 3.11. Safe to run twice.
"""

from __future__ import annotations

import os
import subprocess
import sys

COLORS = "ui/colors.py"
DIALOG = "ui/batch_export_dialog.py"
OLD_DEPS = "requirements-dev.txt"
NEW_DEPS = "tests/requirements-dev.txt"


# --------------------------------------------------------------------------
# 1. The colour
# --------------------------------------------------------------------------

ANCHOR = '''# ==================== Status Colors ====================
STATUS_ERROR_TEXT: Final[str] = "#ff6b6b"
"""Inline error/warning label text (e.g. batch export validation)."""
'''

REPLACEMENT = '''# ==================== Status Colors ====================
STATUS_ERROR: Final[str] = "#dc3545"
"""The registered error red. Not drawn by this app, which renders no error
fill -- it is here so the light value below can be DERIVED from it rather
than written down.

A written-down derivative orphans the moment its base moves. That is exactly
what happened to #c4a458, a tint of a gold that was later retired."""

STATUS_ERROR_TEXT: Final[str] = "#ff6b6b"
"""Inline error/warning label text on a DARK ground (e.g. batch export
validation).

7.5674 on this app's #000000 dialog background. Left alone by the error-red
pass: dark values that already clear the floor are not replaced to buy
uniformity."""

STATUS_ERROR_TEXT_LIGHT: Final[str] = lighten(STATUS_ERROR, -20)  # -> #c82131
"""The same label on a LIGHT ground.

STATUS_ERROR_TEXT reads 2.5454 on #f5f5f5 -- below the 4.5 text floor and
below even the 3.0 UI floor. This reads 5.1811, and clears 4.5:1 down to
#e8e8e8, the same coverage boundary BRAND_DARK_GOLD_DEEP publishes.

No red carries text at 4.5:1 on a real light panel, so light spends a
derivative on TEXT for exactly the reason the gold does: the fill and text
jobs occupy non-overlapping luminance bands. A uniform per-channel step holds
hue at 354.25 degrees, identical to the base."""
'''

HELPER_ANCHOR = """    def _apply_theme(self) -> None:
        if not self._theme_manager:
            return
"""

HELPER = '''    def _error_text_color(self) -> str:
        """The error label's colour for the theme currently in force.

        Follows the idiom _apply_theme already uses for ACCENT_PRESSED_TEXT:
        ask the theme manager, fall back to the dark value. Both call sites go
        through here so they cannot drift apart -- which is how one of two
        sibling sites ends up rendering a retired colour.
        """
        if self._theme_manager and self._theme_manager.current_theme == 'light':
            return STATUS_ERROR_TEXT_LIGHT
        return STATUS_ERROR_TEXT

'''

COLOUR_EDITS = (
    (COLORS, ANCHOR, REPLACEMENT, 1,
     "the registered base, the dark value, and the derived light value"),
    (COLORS,
     '    "STATUS_ERROR_TEXT",',
     '    "STATUS_ERROR",\n    "STATUS_ERROR_TEXT",\n'
     '    "STATUS_ERROR_TEXT_LIGHT",', 1,
     "__all__"),
    (DIALOG,
     "    STATUS_ERROR_TEXT,",
     "    STATUS_ERROR_TEXT,\n    STATUS_ERROR_TEXT_LIGHT,", 1,
     "import the light value"),
    (DIALOG, HELPER_ANCHOR, HELPER + HELPER_ANCHOR, 1,
     "one helper, so the two call sites cannot diverge"),
    (DIALOG,
     'self._lbl_status.setStyleSheet(f"color: {STATUS_ERROR_TEXT};")',
     'self._lbl_status.setStyleSheet(\n'
     '                f"color: {self._error_text_color()};")', 2,
     "both error labels ask for the current theme's value"),
)

BASELINE = "test_rnv_palette_manager.py"

# The dead key. Identical text in all three palettes, so the count is the
# assertion: three, or the tree is not what this was written against.
#
# The second edit is the one the value-watcher could not have found. That tool
# instruments palette VALUES and reports who reads them; it proved nothing in
# the application draws this colour. But `assertIn(key, theme)` tests the
# KEY's membership and never touches the value object at all, so a
# required-keys list is invisible to it. The suite found it the honest way --
# by going red -- and it is fixed here rather than worked around.
DEAD_KEY_EDITS = (
    (COLORS, "    'error': '#f44336',\n", "", 3,
     "the orphaned Material red, in all three palettes"),
    (BASELINE,
     '        "success","warning","error",\n',
     '        "success","warning",\n', 1,
     "the baseline suite's required-keys list, which asserts the key EXISTS "
     "-- key membership is invisible to a value watcher"),
)


# --------------------------------------------------------------------------
# 2. Dependencies
# --------------------------------------------------------------------------

DEP_REWRITES = (
    (".github/workflows/tests.yml",
     "cache-dependency-path: requirements-dev.txt",
     "cache-dependency-path: tests/requirements-dev.txt", 1,
     "LIVE-QUIET -- a stale cache key never errors, it just stops matching"),
    (".github/workflows/tests.yml",
     "pip install -r requirements-dev.txt",
     "pip install -r tests/requirements-dev.txt", 1,
     "LIVE -- CI fails outright without this"),
    (".github/workflows/tests-linux.yml",
     "cache-dependency-path: requirements-dev.txt",
     "cache-dependency-path: tests/requirements-dev.txt", 1,
     "LIVE-QUIET"),
    (".github/workflows/tests-linux.yml",
     "pip install -r requirements-dev.txt",
     "pip install -r tests/requirements-dev.txt", 1,
     "LIVE"),
    ("README.md",
     "├── requirements-dev.txt            # Test/benchmark dependencies (optional)\n",
     "", 1,
     "DOCS -- drop the root tree entry; it moves under tests/ below"),
    ("README.md",
     "├── tests/                          # Modern pytest suite (371 tests)\n",
     "├── tests/                          # Modern pytest suite (371 tests)\n"
     "│   └── requirements-dev.txt        # Test/benchmark dependencies\n", 1,
     "DOCS -- and draw it where it now lives"),
    ("README.md",
     "pip install -r requirements-dev.txt   # First-time setup",
     "pip install -r tests/requirements-dev.txt   # First-time setup", 1,
     "DOCS -- an instruction a reader will actually run"),
    ("TESTING.md",
     "pip install -r requirements-dev.txt\n",
     "pip install -r tests/requirements-dev.txt\n", 1,
     "DOCS"),
    ("TESTING.md",
     "├── requirements-dev.txt                # Test/benchmark dependencies\n",
     "", 1,
     "DOCS -- drop the root tree entry"),
    ("TESTING.md",
     "  installed. Run `pip install -r requirements-dev.txt` against the same",
     "  installed. Run `pip install -r tests/requirements-dev.txt` against the same",
     1, "DOCS"),
    ("build_linux.sh",
     "#   - Test dependencies:      pip install -r requirements-dev.txt",
     "#   - Test dependencies:      pip install -r tests/requirements-dev.txt",
     1, "DOCS -- a comment a human copies"),
    ("build_windows.bat",
     "REM   - Test dependencies:     pip install -r requirements-dev.txt",
     "REM   - Test dependencies:     pip install -r tests/requirements-dev.txt",
     1, "DOCS -- a comment a human copies"),
)

SELF_REWRITES = (
    ("# Install with: pip install -r requirements-dev.txt",
     "# Install with: pip install -r tests/requirements-dev.txt",
     "its own install line would name a path that no longer exists"),
)

EXPECTED_INCLUDES = 0

DEP_EXEMPT = {
    "tests/test_dependency_file_placement.py":
        "the guard; its job is to name the retired path",
}

# Tree-diagram lines: the basename is correct because indentation supplies
# the directory. Named explicitly, and asserted to exist, rather than waved
# through by a looser rule that would also hide a real stale reference.
DIAGRAM_LINES = {
    "README.md": "│   └── requirements-dev.txt        # Test/benchmark dependencies",
}


# --------------------------------------------------------------------------
# 3. Guards
# --------------------------------------------------------------------------

ERROR_GUARD_PATH = "tests/test_error_red.py"

ERROR_GUARD_SOURCE = r'''"""Error text is theme-aware, and the Material red is gone.

    STATUS_ERROR             #dc3545   registered base, derived from only
    STATUS_ERROR_TEXT        #ff6b6b   dark ground
    STATUS_ERROR_TEXT_LIGHT  #c82131   light ground, derived

Before this pass a single #ff6b6b served both modes and read 2.5454 on the
light dialog ground -- below the text floor and below the UI floor too.
"""

import pytest

from ui import colors

TEXT_FLOOR = 4.5


MIN_OPAQUE_ALPHA = 0xE0


def _rgb(value: str) -> str:
    """Six hex digits, from a value that may carry a Qt alpha channel.

    Image mode's window_bg is `#ED000000` -- eight digits, #AARRGGBB, which
    is Qt's order and NOT the CSS #RRGGBBAA. Read naively as #RRGGBB it
    becomes #ED0000, a red, and the contrast against it computes to 1.6448
    instead of the ~7.57 the eye actually sees. That is the 8-digit blind
    spot the family register warns about, and it caught this very test.

    The alpha is asserted rather than ignored: at 0xED the colour is 93%
    opaque, so treating it as its own RGB is a sound approximation. Below
    that it would not be, and this stops rather than quietly approximating.
    """
    h = value.lstrip("#")
    if len(h) == 8:
        alpha = int(h[0:2], 16)
        assert alpha >= MIN_OPAQUE_ALPHA, (
            f"{value} is only {alpha / 255:.0%} opaque; its effective colour "
            f"depends on what is behind it and cannot be measured here")
        return h[2:]
    assert len(h) == 6, f"expected 6 or 8 hex digits, got {value!r}"
    return h


def _luminance(value: str) -> float:
    h = _rgb(value)
    parts = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    parts = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
             for x in parts]
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]


def contrast(a: str, b: str) -> float:
    first, second = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (first + 0.05) / (second + 0.05)


def test_the_argb_reader_is_not_fooled_by_the_alpha_channel():
    """Guard the guard.

    If _rgb ever goes back to slicing the first six digits, every contrast
    number measured against image mode becomes fiction -- and fiction that
    reads as a FAILURE, which is the kind that gets 'fixed' by changing the
    colour rather than the reader.
    """
    assert _rgb("#ED000000") == "000000"
    assert _rgb("#f5f5f5") == "f5f5f5"
    assert contrast("#ffffff", "#ED000000") == pytest.approx(
        contrast("#ffffff", "#000000"))


def test_the_light_error_text_is_derived_not_written():
    assert colors.STATUS_ERROR_TEXT_LIGHT == colors.lighten(colors.STATUS_ERROR, -20)
    assert colors.STATUS_ERROR_TEXT_LIGHT != colors.STATUS_ERROR


def test_light_error_text_clears_its_own_dialog_ground():
    """The pairing this pass existed to fix: 2.5454 -> 5.1811."""
    ground = colors.LIGHT_THEME_COLORS["window_bg"]
    ratio = contrast(colors.STATUS_ERROR_TEXT_LIGHT, ground)
    assert ratio >= TEXT_FLOOR, \
        f"{colors.STATUS_ERROR_TEXT_LIGHT} on {ground} = {ratio:.4f}"


@pytest.mark.parametrize("ground", ["#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"])
def test_light_error_text_carries_to_the_published_boundary(ground):
    """#e8e8e8 is where the gold stops carrying text. The red is derived to
    the same boundary so the two rules need not be remembered separately."""
    ratio = contrast(colors.STATUS_ERROR_TEXT_LIGHT, ground)
    assert ratio >= TEXT_FLOOR, \
        f"{colors.STATUS_ERROR_TEXT_LIGHT} on {ground} = {ratio:.4f}"


def test_dark_error_text_was_left_alone_and_still_clears():
    """Dark was never short. Asserted so a later pass cannot move it quietly
    while everyone is looking at light."""
    assert colors.STATUS_ERROR_TEXT == "#ff6b6b"
    for name in ("DARK", "IMAGE_MODE"):
        palette = getattr(colors, name + "_THEME_COLORS", None) or \
            getattr(colors, "IMAGE_MODE_COLORS")
        ratio = contrast(colors.STATUS_ERROR_TEXT, palette["window_bg"])
        assert ratio >= TEXT_FLOOR, f"{name}: {ratio:.4f}"


def test_the_two_error_texts_are_not_the_same_value():
    """If these ever collapse onto one value, one of the two modes is short
    again -- which is the state this pass found the app in."""
    assert colors.STATUS_ERROR_TEXT != colors.STATUS_ERROR_TEXT_LIGHT


def test_the_retired_material_red_is_gone_from_every_palette():
    """It was an orphan -- no code path read it -- but an unread wrong value
    is still a wrong value waiting for a reader."""
    retired = "#f44336"
    for name in ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS"):
        palette = getattr(colors, name)
        offenders = [k for k, v in palette.items()
                     if isinstance(v, str) and v.lower() == retired]
        assert not offenders, f"{name} still carries {retired} on {offenders}"
        assert "error" not in palette, \
            f"{name} still has the dead 'error' key"


def test_that_check_is_actually_looking():
    """Guard the guard. The sweep above walks three palettes; if they ever
    turn up empty it would pass while checking nothing."""
    for name in ("DARK_THEME_COLORS", "LIGHT_THEME_COLORS", "IMAGE_MODE_COLORS"):
        palette = getattr(colors, name)
        assert len(palette) > 20, f"{name} has only {len(palette)} keys"
    planted = {"error": "#f44336"}
    assert [k for k, v in planted.items() if v.lower() == "#f44336"], \
        "the retired-value pattern no longer matches a known offender"


def test_both_error_labels_go_through_the_helper(qtbot):
    """The two call sites used to name the constant directly. One helper is
    what stops a future change fixing one of them and forgetting the other.
    """
    import inspect

    from ui import batch_export_dialog

    source = inspect.getsource(batch_export_dialog)
    assert source.count("self._error_text_color()") == 2
    assert "f\"color: {STATUS_ERROR_TEXT};\"" not in source, \
        "a call site still names the dark constant directly"
'''

GUARD_PATH = "tests/test_dependency_file_placement.py"

GUARD_SOURCE = r'''"""Test dependencies live at tests/requirements-dev.txt.

All six RNV repositories converge on that path. This file MENTIONS the
retired root-level path and is excluded from the sweep that forbids it --
the use/mention distinction.
"""

import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
WANTED = REPO / "tests" / "requirements-dev.txt"
RETIRED_AT_ROOT = REPO / "requirements-dev.txt"
NEEDLE = "requirements-dev.txt"

# Measured, not assumed. A file that had an include and silently lost it
# would make test_every_include_resolves pass vacuously.
EXPECTED_INCLUDES = 0

SKIP_DIRS = {".git", "build", "dist", "__pycache__", ".venv", ".pytest_cache",
             "htmlcov", "scripts", ".benchmarks", ".hypothesis"}
MENTION_ONLY = {pathlib.Path(__file__).name}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".ini",
                 ".cfg", ".sh", ".bat"}

# A tree diagram names a file by basename and supplies the directory through
# indentation, so this line -- drawn under `tests/` -- is correct as written.
# Rewriting it would read as tests/tests/... to anyone looking at the diagram.
DIAGRAM_LINES = {
    "README.md": "│   └── requirements-dev.txt        # Test/benchmark dependencies",
}


def _is_delivery_script(path):
    if "scripts" in path.parts:
        return True
    return path.parent == REPO and path.name.startswith("up")


def _files():
    for path in sorted(REPO.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in MENTION_ONLY or _is_delivery_script(path):
            continue
        yield path


def test_the_dependency_file_is_where_it_belongs():
    assert WANTED.is_file(), f"{WANTED} is missing"
    assert not RETIRED_AT_ROOT.exists(), \
        "requirements-dev.txt is still at the repository root"


def test_the_moved_file_still_has_content():
    lines = [ln.strip() for ln in WANTED.read_text(encoding="utf-8").splitlines()]
    packages = [ln for ln in lines if ln and not ln.startswith("#")]
    assert len(packages) >= 3, f"only {len(packages)} requirements found"


def test_every_include_resolves():
    """pip resolves a `-r` include RELATIVE TO THE FILE THAT CONTAINS IT.

    A file moved from the root into tests/ with `-r requirements.txt` intact
    starts asking for tests/requirements.txt -- a file nobody ever wrote. No
    path assertion catches it; CI dies at pip-install time naming a file that
    appears nowhere in the repository. That happened in rnv-color-picker
    during this same pass.
    """
    includes = [ln.strip().split(None, 1)[1].strip()
                for ln in WANTED.read_text(encoding="utf-8").splitlines()
                if ln.strip().startswith("-r ")]
    for include in includes:
        target = (WANTED.parent / include).resolve()
        assert target.is_file(), (
            f"{WANTED.name} includes {include!r} -> {target}, which does not "
            f"exist")
    assert len(includes) == EXPECTED_INCLUDES, (
        f"the file now has {len(includes)} include(s), not "
        f"{EXPECTED_INCLUDES}. If intended, update the constant -- the loop "
        f"above already checks each one resolves.")


def test_nothing_still_points_at_the_root_path():
    offenders = []
    for path in _files():
        allowed = DIAGRAM_LINES.get(path.relative_to(REPO).as_posix())
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if NEEDLE not in line or "tests/" + NEEDLE in line:
                continue
            if allowed is not None and line.rstrip() == allowed:
                continue
            offenders.append(
                f"{path.relative_to(REPO).as_posix()}: {line.strip()}")
    assert not offenders, \
        "these still name the root path:\n  " + "\n  ".join(offenders)


def test_the_cache_keys_were_not_forgotten():
    """The quiet ones.

    `cache-dependency-path:` never errors when it goes stale -- the key
    simply stops matching and every CI run reinstalls from scratch, forever,
    with nothing in the log to notice. Both workflows carry one.
    """
    for workflow in ("tests.yml", "tests-linux.yml"):
        text = (REPO / ".github" / "workflows" / workflow).read_text(
            encoding="utf-8")
        assert "cache-dependency-path: tests/requirements-dev.txt" in text, \
            f"{workflow} still caches on the old path"


def test_both_workflows_install_from_the_new_path():
    for workflow in ("tests.yml", "tests-linux.yml"):
        text = (REPO / ".github" / "workflows" / workflow).read_text(
            encoding="utf-8")
        assert "pip install -r tests/requirements-dev.txt" in text, workflow


def test_that_sweep_is_actually_looking():
    walked = {p.relative_to(REPO).as_posix() for p in _files()}
    assert len(walked) > 20, f"the sweep only found {len(walked)} files"
    for required in ("README.md", "TESTING.md", "build_linux.sh",
                     "build_windows.bat", ".github/workflows/tests.yml"):
        assert required in walked, f"{required} is not being swept"


def test_the_diagram_exemption_is_load_bearing():
    """Both directions. An exemption for a line that no longer exists is dead
    weight, and dead weight is a licence waiting for a future defect."""
    for rel, line in DIAGRAM_LINES.items():
        text = (REPO / rel).read_text(encoding="utf-8", errors="replace")
        assert line in text, (
            f"{rel} no longer contains the exempted diagram line "
            f"{line.strip()!r} -- remove it from DIAGRAM_LINES")


def test_the_mention_exemption_is_load_bearing():
    here = pathlib.Path(__file__)
    assert here.name in MENTION_ONLY
    assert NEEDLE in here.read_text(encoding="utf-8"), \
        "this file no longer mentions the path -- drop the exemption"
'''


# --------------------------------------------------------------------------
# Machinery
# --------------------------------------------------------------------------

class Halt(SystemExit):
    pass


def _this_script() -> str:
    return os.path.relpath(os.path.realpath(__file__),
                           os.path.realpath(os.getcwd())).replace(os.sep, "/")


class Tree:
    SKIP_DIRS = {".git", "__pycache__", "build", "dist", ".venv", "scripts",
                 ".pytest_cache", "htmlcov", ".benchmarks", ".hypothesis"}
    TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".ini",
                     ".cfg", ".sh", ".bat"}

    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.dirty: set[str] = set()

    def get(self, path: str) -> str:
        if path not in self.files:
            with open(path, "r", encoding="utf-8") as handle:
                self.files[path] = handle.read()
        return self.files[path]

    def sweep_text(self, path: str) -> str:
        if path in self.files:
            return self.files[path]
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()

    def set(self, path: str, text: str) -> None:
        self.files[path] = text
        self.dirty.add(path)

    def texts(self):
        me = _this_script()
        for root, dirs, names in os.walk("."):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            for name in sorted(names):
                if os.path.splitext(name)[1] not in self.TEXT_SUFFIXES:
                    continue
                path = os.path.relpath(os.path.join(root, name),
                                       ".").replace(os.sep, "/")
                if path != me:
                    yield path

    def flush(self) -> int:
        for path in sorted(self.dirty):
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(self.files[path])
        return len(self.dirty)


def git(*args: str) -> str:
    result = subprocess.run(("git",) + args, capture_output=True, text=True)
    if result.returncode:
        raise Halt(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


def lighten(value: str, step: int) -> str:
    h = value.lstrip("#")
    channels = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return "#" + "".join(f"{max(0, min(255, c + step)):02x}" for c in channels)


def contrast(a: str, b: str) -> float:
    def lum(value: str) -> float:
        h = value.lstrip("#")
        parts = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        parts = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
                 for x in parts]
        return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]
    first, second = sorted((lum(a), lum(b)), reverse=True)
    return (first + 0.05) / (second + 0.05)


ALL_EDITS = COLOUR_EDITS + DEAD_KEY_EDITS + DEP_REWRITES


def already_done() -> bool:
    if os.path.exists(COLORS) and "STATUS_ERROR_TEXT_LIGHT" in open(
            COLORS, encoding="utf-8").read():
        print("Already applied -- ui/colors.py defines STATUS_ERROR_TEXT_LIGHT.")
        print("Nothing to do. This is the idempotent exit, not an error.")
        return True
    return False


def check_fingerprint(tree: Tree) -> None:
    problems = []
    for path, old, _new, expected, why in ALL_EDITS:
        if not os.path.exists(path):
            problems.append(f"  {path} does not exist")
            continue
        count = tree.sweep_text(path).count(old)
        if count != expected:
            problems.append(
                f"  {path}: expected {expected} occurrence(s) of "
                f"{old.splitlines()[0].strip()[:56]!r}, found {count}\n"
                f"      ({why})")
    if not os.path.exists(OLD_DEPS):
        problems.append(f"  {OLD_DEPS} is not at the repository root")
    if os.path.exists(NEW_DEPS):
        problems.append(f"  {NEW_DEPS} already exists")
    if problems:
        raise Halt("This is not the tree this script was written against:\n"
                   + "\n".join(problems)
                   + "\n\nRun it from the root of a clean checkout of main.")


def apply_edits(tree: Tree, edits, heading: str) -> None:
    print(heading)
    for path, old, new, expected, why in edits:
        tree.set(path, tree.get(path).replace(old, new, expected))
        print(f"  {path}: {why}")


def assert_no_dep_reference_was_missed(tree: Tree) -> None:
    listed = {path for path, _o, _n, _c, _w in DEP_REWRITES}
    exempt = set(DEP_EXEMPT) | {OLD_DEPS, GUARD_PATH}
    unaccounted = []
    for path in tree.texts():
        if path in listed or path in exempt:
            continue
        for line in tree.sweep_text(path).splitlines():
            if "requirements-dev.txt" in line:
                unaccounted.append(f"{path}: {line.strip()}")
    if unaccounted:
        raise Halt(
            "These name the dependency file but are in neither the rewrite\n"
            "list nor the exemption list -- decide which each one is:\n  "
            + "\n  ".join(unaccounted))
    print(f"  every file naming the dependency path is accounted for "
          f"({len(listed)} files, {len(DEP_REWRITES)} references)")


def move_the_deps(tree: Tree, dry: bool) -> None:
    body = tree.get(OLD_DEPS)
    includes = [ln for ln in body.splitlines() if ln.strip().startswith("-r ")]
    if len(includes) != EXPECTED_INCLUDES:
        raise Halt(
            f"{OLD_DEPS} has {len(includes)} `-r` include(s), expected "
            f"{EXPECTED_INCLUDES}. pip resolves an include relative to the "
            f"file holding it, so each needs a `../` prefix after this move. "
            f"Refusing to move it blind.")
    for old_line, new_line, why in SELF_REWRITES:
        if old_line not in body:
            raise Halt(f"{OLD_DEPS} does not contain {old_line!r}\n  ({why})")
        body = body.replace(old_line, new_line, 1)
    tree.set(NEW_DEPS, body)
    if not dry:
        git("mv", OLD_DEPS, NEW_DEPS)
    print(f"  {OLD_DEPS} -> {NEW_DEPS}  (git mv; {EXPECTED_INCLUDES} includes)")


def install_guards(tree: Tree) -> None:
    tree.set(GUARD_PATH, GUARD_SOURCE)
    tree.set(ERROR_GUARD_PATH, ERROR_GUARD_SOURCE)
    print(f"  {GUARD_PATH}: {len(GUARD_SOURCE.splitlines())} lines")
    print(f"  {ERROR_GUARD_PATH}: {len(ERROR_GUARD_SOURCE.splitlines())} lines")


def verify(tree: Tree) -> None:
    problems = []
    derived = lighten("#dc3545", -20)
    if derived != "#c82131":
        problems.append(f"the derivation gives {derived}, expected #c82131")
    for ground in ("#ffffff", "#f5f5f5", "#eeeeee", "#e8e8e8"):
        ratio = contrast(derived, ground)
        if ratio < 4.5:
            problems.append(f"{derived} on {ground} = {ratio:.4f}")
    if contrast("#ff6b6b", "#000000") < 4.5:
        problems.append("the dark value no longer clears its own ground")

    colours = tree.get(COLORS)
    if "STATUS_ERROR_TEXT_LIGHT: Final[str] = lighten(STATUS_ERROR, -20)" \
            not in colours:
        problems.append("the light value is not computed from the base")
    if '"#ff6b6b"' not in colours:
        problems.append("the dark value was moved; it should be untouched")
    if "#f44336" in colours:
        problems.append("the retired Material red is still in ui/colors.py")
    if "'error':" in colours:
        problems.append("a palette still carries the dead 'error' key")
    for name in ('"STATUS_ERROR"', '"STATUS_ERROR_TEXT"',
                 '"STATUS_ERROR_TEXT_LIGHT"'):
        if colours.count(name + ",") != 1:
            problems.append(f"__all__ does not export {name} exactly once")

    baseline = tree.get(BASELINE)
    if '"error"' in baseline.split("REQUIRED", 1)[-1][:400]:
        problems.append("the baseline required-keys list still demands 'error'")

    dialog = tree.get(DIALOG)
    if dialog.count("self._error_text_color()") != 2:
        problems.append("both error labels must go through the helper")
    if 'f"color: {STATUS_ERROR_TEXT};"' in dialog:
        problems.append("a call site still names the dark constant directly")

    swept = 0
    for path in tree.texts():
        if path in DEP_EXEMPT or path in (OLD_DEPS, NEW_DEPS):
            continue
        swept += 1
        allowed = DIAGRAM_LINES.get(path)
        for line in tree.sweep_text(path).splitlines():
            if "requirements-dev.txt" not in line:
                continue
            if "tests/requirements-dev.txt" in line:
                continue
            if allowed is not None and line.rstrip() == allowed:
                continue
            problems.append(f"{path} still names the root path: {line.strip()}")
    if swept < 20:
        problems.append(f"the sweep visited only {swept} files; it is not looking")
    for path, line in DIAGRAM_LINES.items():
        if line not in tree.get(path):
            problems.append(
                f"{path} no longer contains the exempted diagram line "
                f"{line.strip()!r}; remove it from DIAGRAM_LINES")

    body = tree.get(NEW_DEPS)
    packages = [ln for ln in (l.strip() for l in body.splitlines())
                if ln and not ln.startswith("#")]
    if len(packages) < 3:
        problems.append(f"the moved file holds only {len(packages)} requirements")

    if problems:
        raise Halt("VERIFY FAILED -- nothing was written:\n  "
                   + "\n  ".join(problems))
    print(f"  verify: light {derived} clears 4.5 to #e8e8e8; dark #ff6b6b "
          f"untouched;")
    print(f"    #f44336 gone from every palette; {swept} files swept; "
          f"{len(packages)} requirements intact")


def finish() -> None:
    here = os.path.abspath(__file__)
    os.remove(here)
    print(f"Removed {here}")


def main() -> int:
    if "--finish" in sys.argv:
        finish()
        return 0

    dry = "--check" in sys.argv

    if not os.path.isdir(".git"):
        raise Halt("run this from the repository root (.git not found)")
    if already_done():
        return 0

    tree = Tree()
    check_fingerprint(tree)

    print("DRY RUN -- every pass runs, nothing is written\n" if dry
          else "Applying\n")

    apply_edits(tree, COLOUR_EDITS, "1. error text becomes theme-aware")
    apply_edits(tree, DEAD_KEY_EDITS,
                "\n2. the dead Material red, and the test that required it")

    print("\n3. dependencies")
    assert_no_dep_reference_was_missed(tree)
    move_the_deps(tree, dry)
    apply_edits(tree, DEP_REWRITES, "   references:")

    print("\n4. guards")
    install_guards(tree)

    print("\n5. verify the pending tree")
    verify(tree)

    if dry:
        print(f"\nDry run complete. {len(tree.dirty)} files would change; "
              f"none were written. The git mv did not run.")
        return 0

    written = tree.flush()
    print(f"\n6. wrote {written} files")

    print("\nDone. Now run, from the repository root (Python 3.12+):")
    print("    QT_QPA_PLATFORM=offscreen python run_tests.py")
    print(f"\nThen, once green:  python {_this_script()} --finish")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Halt as stop:
        print(f"\n{stop}", file=sys.stderr)
        sys.exit(1)
