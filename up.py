#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Align rnv-color-palette-manager's muted and disabled text to the other four
apps, and say which of the two anything actually paints.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHAT MOVES, AND WHAT IT COSTS

  text_disabled   #666666 -> #555555  (DARK, IMAGE)
                  #999999 -> #aaaaaa  (LIGHT)

    Live: the batch export dialog and the menu bar both paint it. This app was
    the only one of five not on these values. Both old and new sit below every
    contrast floor and are meant to -- WCAG 1.4.3 exempts text in an inactive
    component. The change makes disabled text slightly fainter (3.03 -> 2.33 on
    the dark card, 2.46 -> 2.13 on the light one) and consistent with the rest.

  text_secondary  #aaaaaa -> #888888  (DARK, IMAGE)
                  #555555 -> #666666  (LIGHT)

    NOT LIVE. Nothing paints this key. ui/settings_dialog.py reads it into a
    local and never uses that local, which is exactly why a grep for it looks
    live and why it drifted unnoticed. Aligned anyway, and annotated, so that
    wiring it up later is one line and not a colour decision.

NO PIXEL MOVES FOR text_secondary. The only visible change in this pass is
disabled text, in the two places that paint it.

WHAT LANDS

  ui/colors.py                            six values, three NOT CONSUMED notes
  tests/test_muted_and_disabled_text.py   new

THE GUARD HOLDS THE STORY, NOT THE BYTES

The hierarchy test asserts primary reads stronger than muted reads stronger
than disabled, as an ORDER -- so a later retune of the ramp moves them together
and it still passes. The note test asserts in both directions: the key is
unpainted AND the notes are present. Paint it and the run fails, which is the
point.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-color-palette-manager"
DESCRIPTION = "align muted and disabled text"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = "NOT CONSUMED"
GUARD = "tests/test_muted_and_disabled_text.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

# Run them the way run_tests.py and CI run them. A bare `pytest` also collects
# snapshots/test_import_snapshots.py, whose basename collides with the one in
# tests/ and halts collection -- a pre-existing trap unrelated to this change.
SUITES = [
    ("pytest tests/", [sys.executable, "-m", "pytest", "tests/", "-q",
                       "-p", "no:cacheprovider"]),
    ("unittest suite", [sys.executable, "-m", "unittest",
                        "test_rnv_palette_manager"]),
]

NOTE_FULL = (
    "    # NOT CONSUMED. Nothing paints this key -- ui/settings_dialog.py reads it\n"
    "    # into a local and never uses that local, which is why a grep for it looks\n"
    "    # live. Aligned to the value the apps that DO paint a muted text use, so\n"
    "    # wiring it up stays one line and not a colour decision.\n")
NOTE_SHORT = "    # NOT CONSUMED -- see the note in the dark palette.\n"

TARGETS = {
    "DARK_THEME_COLORS":  {"'text_secondary'": "'#888888'",
                           "'text_disabled'":  "'#555555'"},
    "LIGHT_THEME_COLORS": {"'text_secondary'": "'#666666'",
                           "'text_disabled'":  "'#aaaaaa'"},
    "IMAGE_MODE_COLORS":  {"'text_secondary'": "'#888888'",
                           "'text_disabled'":  "'#555555'"},
}


def _bounds(lines):
    """Locate each theme dict. The three palettes carry identical text lines,
    so a plain string replace cannot tell dark from image -- the edit has to be
    scoped to the dict it belongs to."""
    starts = {}
    for i, line in enumerate(lines):
        m = re.match(r"^(DARK_THEME_COLORS|LIGHT_THEME_COLORS|IMAGE_MODE_COLORS)\s*:", line)
        if m:
            starts[m.group(1)] = i
    if set(starts) != set(TARGETS):
        raise SystemExit(f"expected three theme dicts, found {sorted(starts)}")
    order = sorted(starts.items(), key=lambda kv: kv[1])
    return {n: (st, order[i + 1][1] if i + 1 < len(order) else len(lines))
            for i, (n, st) in enumerate(order)}


def edits(tree) -> None:
    lines = tree.read(SENTINEL_FILE).splitlines(keepends=True)
    changed = 0
    for name, (st, en) in _bounds(lines).items():
        note = NOTE_FULL if name == "DARK_THEME_COLORS" else NOTE_SHORT
        for i in range(st, en):
            for key, value in TARGETS[name].items():
                if lines[i].strip().startswith(key + ":"):
                    new = f"    {key}: {value},\n"
                    if key == "'text_secondary'":
                        new = note + new
                    lines[i] = new
                    changed += 1
    if changed != 6:
        raise SystemExit(f"expected 6 values, changed {changed}")
    tree.write(SENTINEL_FILE, "".join(lines))


def checks(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if src.count("# NOT CONSUMED") != 3:
        raise SystemExit("expected a NOT CONSUMED note in each of the three "
                         "palettes")
    for old in ("'text_secondary': '#aaaaaa'", "'text_secondary': '#555555'",
                "'text_disabled': '#666666'", "'text_disabled': '#999999'"):
        if old in src:
            raise SystemExit(f"a pre-change value survives: {old}")
    if src.count("'text_disabled': '#555555'") != 2:
        raise SystemExit("expected two dark-side disabled values at #555555")
    if src.count("'text_disabled': '#aaaaaa'") != 1:
        raise SystemExit("expected one light disabled value at #aaaaaa")


GUARD_SOURCE = '"""\nMuted and disabled text: aligned to the ecosystem, and honest about which of\nthem anything actually paints.\n\n`text_disabled` is live -- the batch export dialog and the menu bar both read\nit. It is now #555555 dark / #aaaaaa light, matching the other four apps. Both\nsit below every contrast floor and are meant to: WCAG 1.4.3 exempts text in an\ninactive component, and disabled text that reads as clearly as enabled text is\nnot doing its job.\n\n`text_secondary` is NOT painted anywhere. It is defined in all three palettes,\nread into a local in ui/settings_dialog.py, and that local is never used. It is\nkept and kept correct so wiring it up is one line. The tests below hold that\nstory to the code: if someone paints it, the "NOT CONSUMED" notes beside the\nvalues become false and the run says so.\n"""\nfrom __future__ import annotations\n\nimport pathlib\nimport re\n\nimport pytest\n\nfrom ui.colors import (DARK_THEME_COLORS, IMAGE_MODE_COLORS,\n                       LIGHT_THEME_COLORS)\n\nTHEMES = {\n    "DARK": DARK_THEME_COLORS,\n    "LIGHT": LIGHT_THEME_COLORS,\n    "IMAGE": IMAGE_MODE_COLORS,\n}\nROOT = pathlib.Path(__file__).resolve().parent.parent\nCOLORS_PY = ROOT / "ui" / "colors.py"\n\n# The one place that reads the key without painting it. Named so the sweep\n# below can tell a dead read from a live one.\nKNOWN_DEAD_READ = "ui/settings_dialog.py"\n\n\ndef _luminance(value: str) -> float:\n    h = value.lstrip("#")\n    if len(h) == 8:                      # Qt #AARRGGBB\n        h = h[2:]\n    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]\n    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]\n    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]\n\n\ndef _contrast(a: str, b: str) -> float:\n    la, lb = _luminance(a), _luminance(b)\n    hi, lo = max(la, lb), min(la, lb)\n    return (hi + 0.05) / (lo + 0.05)\n\n\ndef test_all_three_palettes_carry_both_keys():\n    """Guard the guard: every test below iterates THEMES."""\n    assert set(THEMES) == {"DARK", "LIGHT", "IMAGE"}\n    for name, theme in THEMES.items():\n        for key in ("text_color", "text_secondary", "text_disabled"):\n            assert key in theme, f"{name} has no {key}"\n\n\n@pytest.mark.parametrize("name", sorted(THEMES))\ndef test_the_text_hierarchy_dims_in_order(name):\n    """primary reads strongest, muted next, disabled faintest.\n\n    Held as an ORDER rather than as three values, so a later retune of the ramp\n    moves them together and this still passes.\n    """\n    theme = THEMES[name]\n    ground = theme["card_bg"]            # a flat colour in all three palettes\n    primary = _contrast(theme["text_color"], ground)\n    muted = _contrast(theme["text_secondary"], ground)\n    disabled = _contrast(theme["text_disabled"], ground)\n    assert primary > muted > disabled, (\n        f"{name}: primary {primary:.2f} / muted {muted:.2f} / "\n        f"disabled {disabled:.2f} are not in descending order")\n\n\n@pytest.mark.parametrize("name", sorted(THEMES))\ndef test_disabled_text_stays_visibly_disabled(name):\n    """It is meant to fail the text floor. A disabled label that reads as\n    clearly as an enabled one is not communicating anything."""\n    theme = THEMES[name]\n    ratio = _contrast(theme["text_disabled"], theme["card_bg"])\n    assert ratio < 4.5, (\n        f"{name}: disabled text reads {ratio:.2f}:1 -- at that strength it no "\n        f"longer looks disabled")\n\n\ndef _references(key: str) -> list[str]:\n    sites = []\n    for path in ROOT.rglob("*.py"):\n        parts = path.parts\n        if any(p in parts for p in (".git", "__pycache__", "tests", "snapshots")):\n            continue\n        if path.name.startswith("test_") or path == COLORS_PY:\n            continue\n        # A delivery script sitting at the root mentions the key it moves.\n        # Sweeping it makes the guard fail on the very run that installs it --\n        # the same trap the repos\' placement guards already exempt `up*.py` for.\n        if path.parent == ROOT and path.name.startswith("up"):\n            continue\n        if key in path.read_text(encoding="utf-8", errors="replace"):\n            sites.append(path.relative_to(ROOT).as_posix())\n    return sorted(sites)\n\n\ndef test_the_sweep_is_actually_reading_something():\n    """A walk that finds nothing passes forever."""\n    assert _references("text_disabled"), (\n        "the sweep cannot find text_disabled, which IS painted -- it would not "\n        "find text_secondary either")\n\n\ndef test_the_not_consumed_note_is_still_true():\n    """Both directions. The note beside `text_secondary` tells the next reader\n    nothing paints it. If that stops being true the note is a lie, and a lie in\n    a palette is how a value gets trusted that should not be."""\n    sites = _references("text_secondary")\n    assert sites == [KNOWN_DEAD_READ], (\n        f"text_secondary is now referenced in {sites}. If it is being painted, "\n        f"delete the NOT CONSUMED notes in ui/colors.py -- they are no longer "\n        f"true.")\n\n    notes = len(re.findall(r"#\\s*NOT CONSUMED",\n                           COLORS_PY.read_text(encoding="utf-8")))\n    assert notes == 3, (\n        f"expected a NOT CONSUMED note beside each of the three "\n        f"text_secondary values, found {notes}")\n\n\ndef test_the_dead_read_is_still_dead():\n    """ui/settings_dialog.py assigns the key to a local and never uses it,\n    which is exactly why a grep for `text_secondary` looks live."""\n    source = (ROOT / KNOWN_DEAD_READ).read_text(encoding="utf-8")\n    # The lookarounds are load-bearing: `\\b` happily matches the identifier\n    # INSIDE the string key of `theme.get(\'text_secondary\', ...)`, which is the\n    # dict lookup and not a use of the local. Without them this test fails on\n    # the very line it exists to describe.\n    bare = re.compile(r"(?<![\'\\"])\\btext_secondary\\b(?![\'\\"])")\n    assigns, uses = [], []\n    for i, line in enumerate(source.splitlines(), 1):\n        for match in bare.finditer(line):\n            after = line[match.end():].lstrip()\n            (assigns if after.startswith("=") and not after.startswith("==")\n             else uses).append(f"{i}: {line.strip()[:60]}")\n    assert len(assigns) == 1, f"expected one assignment, found {assigns}"\n    assert not uses, (\n        f"the text_secondary local is now used -- it is live, and ui/colors.py "\n        f"still says it is not: {uses}")\n'


# ------------------------------------------------------------------ plumbing
def refuse_to_shadow() -> None:
    name = Path(__file__).name
    if name in SHADOWS:
        sys.exit(f"refusing to run as {name} -- it would shadow a module on "
                 f"sys.path. Rename to up.py and run again.")


class Tree:
    """Every edit lands here first. Disk is written only after all guards pass,
    so --check is a real rehearsal and a half-applied state is impossible."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}

    def read(self, rel: str) -> str:
        if rel not in self.files:
            p = self.root / rel
            if not p.exists():
                raise SystemExit(f"missing file: {rel}")
            self.files[rel] = p.read_text(encoding="utf-8")
        return self.files[rel]

    def write(self, rel: str, text: str) -> None:
        self.files[rel] = text

    def sub(self, rel: str, old: str, new: str, times: int = 1) -> None:
        src = self.read(rel)
        found = src.count(old)
        if found != times:
            raise SystemExit(
                f"{rel}: expected {times} occurrence(s) of the anchor, found "
                f"{found}. The file moved; re-derive this edit before trusting "
                f"the script.")
        self.write(rel, src.replace(old, new, times))

    def flush(self) -> list[str]:
        touched = []
        for rel, text in self.files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists() or p.read_text(encoding="utf-8") != text:
                p.write_text(text, encoding="utf-8")
                touched.append(rel)
        return touched


def _tail(out: str, lines: int = 40) -> str:
    text = out.strip()
    marker = "short test summary info"
    if marker in text:
        return text[max(0, text.rindex(marker) - 30):]
    return "\n".join(text.splitlines()[-lines:])


def _outcome(code: int, out: str) -> str:
    """"pass", "fail", "abort" or "env" -- only exit code 1 means a test failed.

    pytest exits 0 passed, 1 tests failed, 2 interrupted, 3 internal error,
    4 usage error, 5 nothing collected; a native abort arrives as 134 or -6.
    Treating every non-zero code as a failing assertion is how a tool reports
    a regression that never happened.
    """
    if code == 0:
        return "pass"
    if code in (134, -6, 139, -11) or "Fatal Python error" in out:
        return "abort"
    if code == 1 and "INTERNALERROR" not in out:
        return "fail"
    return "env"


ENV_HELP = """\
THE ENVIRONMENT IS NOT READY. NO TEST DISAGREED WITH THIS CHANGE -- the run
did not get far enough to ask one.

PyQt6 needs system libraries a fresh container does not ship; the give-away is
`ImportError: libGL.so.1`. Install those, then the Python packages:

    sudo apt-get update
    sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 \\
      libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \\
      libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 \\
      libxcb-xfixes0 libxcb-xkb1

    pip install -r requirements.txt -r tests/requirements-dev.txt
    python up.py --verify
"""

ABORT_HELP = """\
PYTHON ABORTED NATIVELY. That is not a failing assertion. On offscreen Linux
these suites can abort in Qt's thread teardown -- it surfaces during whatever
work is in flight and reads exactly like a regression in it.

Re-run:

    python up.py --verify

If it aborts every time on the same test, that is worth looking at. If it
comes and goes, this change is not involved.
"""


def run(label: str, args: list[str]) -> tuple[int, str]:
    """Stream to a temp file rather than capture_output: a long Qt suite emits
    megabytes, and buffering that in memory can get the run killed, which looks
    exactly like a failure."""
    print(f"  {label} ...", flush=True)
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8",
                                errors="replace") as fh:
        proc = subprocess.run(args, stdout=fh, stderr=subprocess.STDOUT, env=env)
        fh.seek(0)
        out = fh.read()
    return proc.returncode, out


def _step(label: str, args: list[str]) -> int:
    code, out = run(label, args)
    verdict = _outcome(code, out)
    print(_tail(out) if verdict != "pass"
          else "\n".join(out.strip().splitlines()[-3:]))
    if verdict == "env":
        print("\n" + ENV_HELP)
    elif verdict == "abort":
        print("\n" + ABORT_HELP)
    elif verdict == "fail":
        print("\nFAILED -- the suite is not green. Nothing was reverted; "
              "`git diff` shows exactly what landed.")
    return code


def verify() -> int:
    code = _step("guard",
                 [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                  GUARD])
    if code != 0:
        return code
    for label, args in SUITES:
        code = _step(label, args)
        if code != 0:
            return code
    print("\nGreen.")
    return 0


def apply(check_only: bool) -> int:
    root = Path.cwd()
    if not (root / SENTINEL_FILE).exists():
        raise SystemExit(f"run this from the root of a {REPO} checkout "
                         f"(no {SENTINEL_FILE} here)")
    if SENTINEL in (root / SENTINEL_FILE).read_text(encoding="utf-8"):
        raise SystemExit(f"already applied -- {SENTINEL!r} is present in "
                         f"{SENTINEL_FILE}")

    tree = Tree(root)
    edits(tree)
    tree.write(GUARD, GUARD_SOURCE)
    checks(tree)

    if check_only:
        print("--check: every edit composes and every guard passes. "
              "Nothing written.")
        return 0

    touched = tree.flush()
    print("wrote: " + ", ".join(touched) + "\n")
    return verify()


def finish() -> None:
    me = Path(__file__).resolve()
    print(f"removing {me.name}")
    me.unlink()


def main() -> int:
    refuse_to_shadow()
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--check", action="store_true",
                    help="rehearse every edit in memory, write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="run the suites only, change nothing")
    ap.add_argument("--finish", action="store_true", help="delete this script")
    args = ap.parse_args()
    if args.finish:
        finish()
        return 0
    if args.verify:
        return verify()
    return apply(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
