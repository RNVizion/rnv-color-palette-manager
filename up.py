#!/usr/bin/env python3
"""
RNV-GOLD-ALIGNMENT-TOOL-DO-NOT-SWEEP

Make the main button's plate step on press, in rnv-color-palette-manager.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

THE RULING

Rendered all three states side by side, in all three modes, across the five
desktop apps on 2026-08-26. The basic black-and-white scheme moves the plate
twice -- rest to hover lifts it, hover to pressed lifts it again -- and the
label inverts on press.

This app held the plate still: button_pressed_bg was the same #333333 as
button_hover_bg, so pressing changed only the label. Two apps did it that way
and three stepped; the step won on the render.

WHAT MOVES

  ui/colors.py                       button_pressed_bg #333333 -> #444444,
                                     once each in DARK, LIGHT and IMAGE
  tests/test_button_press_step.py    new: holds the RELATIONSHIP rather than
                                     the byte -- pressed lifts from hover, the
                                     label inverts -- so a later retune of the
                                     ramp passes and a collapse back onto
                                     hover fails

WHAT DOES NOT MOVE

Hover is untouched at #333333, and test_light_hover_dark_grey still pins it.
The label colours are untouched. tests/test_contrast_pairs.py sweeps gold ink
against its grounds and never reaches button states, so it is unaffected.

DEFERRED ON PURPOSE

The new value is a bare literal, like every other value in these three dicts.
Giving it a constant would mint one name into a dict of ninety-odd unnamed
strings, ahead of the ramp-naming pass that will name all of them at once.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "rnv-color-palette-manager"
DESCRIPTION = "make the main button plate step on press"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = "'button_pressed_bg': '#444444'"
GUARD = "tests/test_button_press_step.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

OLD = "    'button_pressed_bg': '#333333',"
NEW = "    'button_pressed_bg': '#444444',"

# Run them the way .github/workflows/tests-linux.yml runs them. A bare `pytest`
# also collects snapshots/test_import_snapshots.py, whose basename collides
# with the one in tests/ and halts collection -- a pre-existing trap that has
# nothing to do with this change.
SUITES = [
    ("pytest tests/", [sys.executable, "-m", "pytest", "tests/", "-q",
                       "-p", "no:cacheprovider"]),
    ("unittest suite", [sys.executable, "-m", "unittest",
                        "test_rnv_palette_manager"]),
]


def edits(tree) -> None:
    tree.sub(SENTINEL_FILE, OLD, NEW, times=3)


def checks(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if src.count(NEW) != 3:
        raise SystemExit(f"expected 3 pressed plates at #444444, "
                         f"found {src.count(NEW)}")
    if OLD in src:
        raise SystemExit("a pressed plate is still #333333")
    # hover must not have been caught by the same value
    if src.count("    'button_hover_bg': '#333333',") != 3:
        raise SystemExit("the hover plate moved -- it must stay at #333333")


GUARD_SOURCE = '"""\nThe main button\'s plate steps on press.\n\nRULED 2026-08-26, after rendering all three states side by side in all three\nmodes across the five desktop apps. The basic black-and-white scheme moves the\nplate twice: rest -> hover lifts it, hover -> pressed lifts it again. The label\nflips on press independently.\n\nThis app used to hold the plate still on press, so pressing changed only the\nlabel. Two apps did it that way and three stepped; the step won.\n\nWhat these tests hold is the RELATIONSHIP, not the byte. If the ramp is\nretuned later the values move together and these still pass; if someone\ncollapses pressed back onto hover, they fail and say why.\n"""\nfrom __future__ import annotations\n\nimport pytest\n\nfrom ui.colors import (DARK_THEME_COLORS, IMAGE_MODE_COLORS,\n                       LIGHT_THEME_COLORS)\n\nTHEMES = {\n    "DARK": DARK_THEME_COLORS,\n    "LIGHT": LIGHT_THEME_COLORS,\n    "IMAGE": IMAGE_MODE_COLORS,\n}\n\n\ndef _lum(value: str) -> float:\n    h = value.lstrip("#")\n    if len(h) == 8:                      # Qt #AARRGGBB\n        h = h[2:]\n    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]\n    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]\n    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]\n\n\ndef test_all_three_themes_are_present():\n    """Guard the guard. Every test below iterates THEMES; if a rename emptied\n    it they would all pass while checking nothing."""\n    assert set(THEMES) == {"DARK", "LIGHT", "IMAGE"}\n    for name, theme in THEMES.items():\n        for key in ("button_bg", "button_hover_bg", "button_pressed_bg",\n                    "button_text", "button_pressed_text"):\n            assert key in theme, f"{name} has no {key}"\n\n\n@pytest.mark.parametrize("name", sorted(THEMES))\ndef test_the_plate_steps_on_press(name):\n    theme = THEMES[name]\n    hover, pressed = theme["button_hover_bg"], theme["button_pressed_bg"]\n    assert hover != pressed, (\n        f"{name}: pressed plate {pressed} is the hover plate. The press then "\n        f"changes only the label, which is the behaviour this ruling retired.")\n\n\n@pytest.mark.parametrize("name", sorted(THEMES))\ndef test_the_plate_lifts_rather_than_darkens(name):\n    """Each state is lighter than the one before it, in every mode.\n\n    Light mode inverts the ground but not this: the plate goes dark on hover\n    and then one step lighter on press, so the movement reads the same way in\n    both themes.\n    """\n    theme = THEMES[name]\n    rest, hover, pressed = (theme["button_bg"], theme["button_hover_bg"],\n                            theme["button_pressed_bg"])\n    if name == "LIGHT":\n        # rest is the white card; hover drops to the dark plate deliberately.\n        assert _lum(hover) < _lum(rest), f"{name}: hover should darken from rest"\n    else:\n        assert _lum(hover) > _lum(rest), f"{name}: hover should lift from rest"\n    assert _lum(pressed) > _lum(hover), (\n        f"{name}: pressed plate {pressed} does not lift from hover {hover}")\n\n\n@pytest.mark.parametrize("name", sorted(THEMES))\ndef test_the_label_flips_on_press(name):\n    """The plate moving is only half of it. The label inverts at the same\n    moment, and that is what makes the press read as a press rather than as a\n    hover that got brighter."""\n    theme = THEMES[name]\n    resting, pressed = theme["button_text"], theme["button_pressed_text"]\n    assert resting != pressed, f"{name}: the label does not change on press"\n    assert (_lum(resting) > 0.5) != (_lum(pressed) > 0.5), (\n        f"{name}: {resting} -> {pressed} is not an inversion")\n'


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
    code = _step("press-step guard",
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
