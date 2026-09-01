#!/usr/bin/env python3
"""
RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP

Rename the main-window button keys to main_btn_*, and give the dialogs the two
keys they were borrowing from that family.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

NOT ONE PIXEL MOVES. Every value the dialogs gain is the value they already
painted.

`button_*` holds the black-and-white MAIN scheme here, and the gold DIALOG
scheme in rnv-color-picker and rnv-icon-builder. One name, two schemes,
decided by which repository you have open -- and a name that cannot be carried
into a new project is not a standard. After this pass the name says where the
button lives:

    main_btn_*     the main window at launch
    dialog_btn_*   anything that opens later

THIS APP WAS ALREADY MOST OF THE WAY THERE

ui/colors.py already carries dialog_btn_hover_bg, with a comment saying in so
many words that the dialog hover is deliberately not the main one. The dialogs
also take their pressed state from accent. What they had no name for was the
plate and the label they REST on, so four reads reached into the main family
for those. This adds dialog_btn_bg and dialog_btn_text holding exactly those
values, and points the four reads at them.

    ui/about_dialog.py          the rest plate
    utils/dialog_helper.py      the rest plate
    ui/settings_dialog.py       the label
    ui/batch_export_dialog.py   the label

ONE READ OF THE MAIN PLATE INSIDE A DIALOG IS LEFT ALONE, ON PURPOSE

ui/settings_dialog.py resolves an INPUT background through
input_bg -> card_bg -> main_btn_bg. That last step is a surface fallback, not
a button, and repointing it at dialog_btn_bg would be renaming by proximity.
The guard asserts it stays as it is, so it is not tidied away later.

utils/color_history.py keeps the main family too, and is not a dialog: it is
ColorHistoryPanel, which lives in the main window.

WHAT MOVES

Eighty-nine quoted occurrences in twelve files, three comment mentions, six new
palette entries (two keys across three palettes), and four repointed reads.

DOCUMENTATION IS NOT TOUCHED, ON PURPOSE

TESTING.md names two of these keys and will be wrong about them until the
documentation pass, which runs once after alignment settles so it is written
against the finished state rather than chased through it. The guard sweeps
code, not prose, for the same reason.

WHAT THE GUARD ASSERTS

tests/test_button_key_names.py fails if an old name comes back, if any of the
three palettes loses a key, if any of the twenty-one main values or nine
dialog values moved, if a dialog starts reading the main family, or if the two
hover plates ever converge -- flattening them loses a scheme.

It reads the palettes by importing them rather than by parsing them, because a
static resolver returns None for a derived value and then compares None with
None and passes. That failure mode has appeared twice in this programme.
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
DESCRIPTION = "rename the main button keys and name the dialog rest plate"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = "'dialog_btn_bg'"
GUARD = "tests/test_button_key_names.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('run_tests.py (unittest + pytest)', [sys.executable, "run_tests.py"]),
]

OLD_KEYS = ("button_bg", "button_text", "button_hover_bg", "button_hover_text",
            "button_pressed_bg", "button_pressed_text", "button_border_color")
RENAME = {k: "main_" + k.replace("button_", "btn_") for k in OLD_KEYS}

#: path -> how many QUOTED occurrences that file holds. Written down so the
#: script refuses to run against a tree that has moved under it.
QUOTED = {
    "ui/colors.py": 21,
    "ui/image_button.py": 18,
    "RNV_Color_Palette_Manager.py": 16,
    "tests/test_button_press_step.py": 12,
    "test_rnv_palette_manager.py": 8,
    "tests/test_app_mirror.py": 3,
    "tests/test_qt_drag_drop.py": 3,
    "utils/color_history.py": 3,
    "ui/settings_dialog.py": 2,
    "ui/about_dialog.py": 1,
    "ui/batch_export_dialog.py": 1,
    "utils/dialog_helper.py": 1,
}

#: Comment text that names the keys. Renamed so the reasoning stays readable.
PROSE = [
    ("ui/colors.py",
     "    # Deliberately NOT button_hover_bg. That is the MAIN button's inverse",
     "    # Deliberately NOT main_btn_hover_bg. That is the MAIN button's inverse",
     3),
]

#: The dialog family, inserted beside the hover key it belongs with. Anchored
#: on the hover line rather than on a line number, and the dark and image
#: palettes share an anchor because they share the value.
INSERT = [
    ("    'dialog_btn_hover_bg': APP_PANEL_HOVER,\n",
     "    'dialog_btn_hover_bg': APP_PANEL_HOVER,\n"
     "    # The plate and label a dialog button RESTS on. Added 2026-09-01,\n"
     "    # holding what these dialogs already painted -- before this they\n"
     "    # reached into the main family for both, which is why one name\n"
     "    # ended up describing two schemes.\n"
     "    'dialog_btn_bg': BRAND_BLACK,\n"
     "    'dialog_btn_text': APP_TEXT,\n",
     2),
    ("    'dialog_btn_hover_bg': APP_HOVER_LIGHT,\n",
     "    'dialog_btn_hover_bg': APP_HOVER_LIGHT,\n"
     "    # The plate and label a dialog button RESTS on. Added 2026-09-01,\n"
     "    # holding what these dialogs already painted -- before this they\n"
     "    # reached into the main family for both, which is why one name\n"
     "    # ended up describing two schemes.\n"
     "    'dialog_btn_bg': '#ffffff',\n"
     "    'dialog_btn_text': '#000000',\n",
     1),
]

#: The four dialog reads, repointed after the rename has run.
REPOINT = [
    ("ui/about_dialog.py", "theme['main_btn_bg']", "theme['dialog_btn_bg']", 1),
    ("utils/dialog_helper.py", "colors['main_btn_bg']", "colors['dialog_btn_bg']", 1),
    ("ui/settings_dialog.py", "color: {theme['main_btn_text']};",
     "color: {theme['dialog_btn_text']};", 1),
    ("ui/batch_export_dialog.py", 'theme["main_btn_text"]',
     'theme["dialog_btn_text"]', 1),
]

_QUOTED_RE = re.compile(r"(['\"])(" + "|".join(sorted(RENAME, key=len, reverse=True))
                        + r")\1")


def _rename_quoted(text: str) -> tuple[str, int]:
    hits = 0

    def swap(m: re.Match) -> str:
        nonlocal hits
        hits += 1
        return f"{m.group(1)}{RENAME[m.group(2)]}{m.group(1)}"

    return _QUOTED_RE.sub(swap, text), hits


def edits(tree) -> None:
    total = 0
    for rel, expected in QUOTED.items():
        new, hits = _rename_quoted(tree.read(rel))
        if hits != expected:
            raise SystemExit(f"{rel}: expected {expected} quoted key(s), found "
                             f"{hits}. The file moved; re-derive this edit "
                             f"before trusting the script.")
        tree.write(rel, new)
        total += hits
    for rel, old, new, times in PROSE:
        tree.sub(rel, old, new, times)
    for old, new, times in INSERT:
        tree.sub(SENTINEL_FILE, old, new, times)
    for rel, old, new, times in REPOINT:
        tree.sub(rel, old, new, times)
    print(f"  renamed {total} quoted keys in {len(QUOTED)} files, "
          f"added 6 dialog entries, repointed {len(REPOINT)} dialog reads")


def checks(tree) -> None:
    for rel in QUOTED:
        text = tree.read(rel)
        for old in RENAME:
            if re.search(r"(['\"])" + old + r"\1", text):
                raise SystemExit(f"{rel}: {old!r} survived the rename")

    colors = tree.read(SENTINEL_FILE)
    for key, count in (("'dialog_btn_bg'", 3), ("'dialog_btn_text'", 3),
                       ("'dialog_btn_hover_bg'", 3)):
        if colors.count(key) != count:
            raise SystemExit(f"expected {count} {key} entries, found "
                             f"{colors.count(key)}")

    # The dialog family must hold the MAIN family's values, palette by palette.
    # Anything else means the rename painted something.
    import ast
    module = ast.parse(colors)
    palettes = []
    for node in ast.walk(module):
        if not isinstance(node, ast.Dict):
            continue
        pairs = {k.value: ast.unparse(v) for k, v in zip(node.keys, node.values)
                 if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        if "dialog_btn_bg" in pairs:
            palettes.append(pairs)
    if len(palettes) != 3:
        raise SystemExit(f"expected 3 palettes, found {len(palettes)}")
    for pairs in palettes:
        for dialog_key, main_key in (("dialog_btn_bg", "main_btn_bg"),
                                     ("dialog_btn_text", "main_btn_text")):
            if pairs[dialog_key] != pairs[main_key]:
                raise SystemExit(
                    f"{dialog_key} is {pairs[dialog_key]} where {main_key} is "
                    f"{pairs[main_key]}. The dialog family is supposed to hold "
                    f"what those dialogs already painted; a difference here is "
                    f"a colour decision hiding inside a rename.")

    for rel in ("ui/about_dialog.py", "utils/dialog_helper.py",
                "ui/batch_export_dialog.py"):
        if re.search(r"(['\"])main_btn_", tree.read(rel)):
            raise SystemExit(f"{rel} still reads the main family")

    settings = tree.read("ui/settings_dialog.py")
    if "theme.get('card_bg', theme['main_btn_bg'])" not in settings:
        raise SystemExit("the settings dialog's input-background fallback "
                         "chain changed shape; it is a surface fallback and "
                         "is meant to keep reading the main plate")
    print("  guards: no old name survives, three palettes carry both families, "
          "dialog values equal what those dialogs painted")


GUARD_SOURCE = r'''"""The button keys say where the button lives.

RNV-BUTTON-NAMING-GUARD

main_btn_* is the main window at launch. dialog_btn_* is anything that opens
later. Before this pass the main family here was called button_* -- the same
name that holds the GOLD DIALOG scheme in rnv-color-picker and
rnv-icon-builder. One name, two schemes, decided by which repository you had
open. These tests are what stop it drifting back.

This application's dialogs already had their own hover plate
(dialog_btn_hover_bg) and take their pressed state from accent. What they did
not have was a name for the plate and label they rest on -- they reached into
the main family for those. dialog_btn_bg and dialog_btn_text close that, with
the values those dialogs already painted.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OLD = ("button_bg", "button_text", "button_hover_bg", "button_hover_text",
       "button_pressed_bg", "button_pressed_text", "button_border_color")
NEW = tuple("main_" + n.replace("button_", "btn_") for n in OLD)
DIALOG = ("dialog_btn_bg", "dialog_btn_text", "dialog_btn_hover_bg")

PINNED_MAIN = {
    "dark": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",
             "main_btn_hover_bg": "#333333", "main_btn_hover_text": "#dddddd",
             "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#000000",
             "main_btn_border_color": "transparent"},
    "light": {"main_btn_bg": "#ffffff", "main_btn_text": "#000000",
              "main_btn_hover_bg": "#333333", "main_btn_hover_text": "#000000",
              "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#ffffff",
              "main_btn_border_color": "transparent"},
    "image": {"main_btn_bg": "#1a1a1a", "main_btn_text": "#dddddd",
              "main_btn_hover_bg": "#333333", "main_btn_hover_text": "#dddddd",
              "main_btn_pressed_bg": "#444444", "main_btn_pressed_text": "#000000",
              "main_btn_border_color": "transparent"},
}

#: The dialog family holds exactly what those dialogs painted before the
#: rename. If one of these ever stops matching its main counterpart that is
#: fine -- it means a dialog scheme was ruled on. What must not happen is a
#: value moving during a rename.
PINNED_DIALOG = {
    "dark": {"dialog_btn_bg": "#1a1a1a", "dialog_btn_text": "#dddddd",
             "dialog_btn_hover_bg": "#3a3a3a"},
    "light": {"dialog_btn_bg": "#ffffff", "dialog_btn_text": "#000000",
              "dialog_btn_hover_bg": "#eeeeee"},
    "image": {"dialog_btn_bg": "#1a1a1a", "dialog_btn_text": "#dddddd",
              "dialog_btn_hover_bg": "#3a3a3a"},
}

SKIP = {".git", "build", "dist", ".venv", "__pycache__"}

#: A sweep for a name cannot tell a USE from a MENTION, and the two files
#: certain to mention the old names are this guard -- which lists them in order
#: to forbid them -- and the delivery script that performs the rename. Skipped
#: by marker rather than by filename: the script arrives under whatever name it
#: is saved as.
MARKERS = ("RNV-BUTTON-NAMING-GUARD", "RNV-BUTTON-NAMING-TOOL-DO-NOT-SWEEP")

#: Dialogs, and the family each is allowed to read.
DIALOG_FILES = ("ui/about_dialog.py", "ui/batch_export_dialog.py",
                "utils/dialog_helper.py")


def _palettes():
    from ui.colors import (DARK_THEME_COLORS, LIGHT_THEME_COLORS,
                           IMAGE_MODE_COLORS)
    return {"dark": DARK_THEME_COLORS, "light": LIGHT_THEME_COLORS,
            "image": IMAGE_MODE_COLORS}


def _sources():
    for path in sorted(ROOT.rglob("*")):
        # Prose is not swept: docs are updated in one pass after alignment
        # settles, so they name the old keys until then, and failing on that
        # would be failing on a decision rather than on a defect.
        if path.is_dir() or path.suffix != ".py":
            continue
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(marker in text for marker in MARKERS):
            continue
        yield path, text


def test_no_old_button_key_name_survives():
    offenders = []
    for path, text in _sources():
        for old in OLD:
            if re.search(r"(['\"])" + old + r"\1", text):
                offenders.append(f"{path.relative_to(ROOT)}: {old}")
    assert not offenders, (
        "these are main-window button keys and must be named main_btn_*:\n  "
        + "\n  ".join(offenders))


def test_the_marker_exemption_covers_only_the_two_tools():
    marked = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(marker in text for marker in MARKERS):
            marked.append(path.relative_to(ROOT))
    assert len(marked) <= 2, f"unexpected marked file(s): {marked}"
    assert Path(__file__).relative_to(ROOT) in marked


def test_all_three_palettes_carry_both_families():
    for mode, palette in _palettes().items():
        missing = [n for n in NEW + DIALOG if n not in palette]
        assert not missing, f"{mode} palette missing {missing}"


def test_the_rename_moved_no_value():
    for mode, pins in PINNED_MAIN.items():
        palette = _palettes()[mode]
        actual = {k: palette.get(k) for k in pins}
        assert actual == pins, (
            f"the {mode} main button values changed.\n"
            f"  wanted {pins}\n  found  {actual}\n"
            "A rename that changes a value is not a rename.")


def test_the_dialog_family_holds_what_the_dialogs_already_painted():
    for mode, pins in PINNED_DIALOG.items():
        palette = _palettes()[mode]
        actual = {k: palette.get(k) for k in pins}
        assert actual == pins, (
            f"the {mode} dialog button values are not what those dialogs "
            f"painted before the rename.\n  wanted {pins}\n  found  {actual}")


def test_dialogs_read_the_dialog_family_and_not_the_main_one():
    for rel in DIALOG_FILES:
        src = (ROOT / rel).read_text(encoding="utf-8-sig")
        assert "dialog_btn_" in src, f"{rel} no longer reads the dialog family"
        assert not re.search(r"(['\"])main_btn_", src), (
            f"{rel} reads the main family. Dialogs open later and rest on the "
            f"dialog plate; wiring one to main_btn_* refuses the distinction "
            f"this rename exists to make.")


def test_the_settings_dialog_surface_fallback_is_still_a_surface_fallback():
    """One read of the main plate inside a dialog is deliberate and stays.

    ui/settings_dialog.py resolves an INPUT background through
    input_bg -> card_bg -> main_btn_bg. The last step is a surface fallback,
    not a button, and pointing it at dialog_btn_bg would be renaming by
    proximity. Asserted so it is not tidied away by the next reader.
    """
    src = (ROOT / "ui" / "settings_dialog.py").read_text(encoding="utf-8-sig")
    assert "theme.get('card_bg', theme['main_btn_bg'])" in src, (
        "the settings dialog's input-background fallback chain changed shape")
    assert "theme['dialog_btn_text']" in src, (
        "the settings dialog's button label should read the dialog family")


def test_the_two_schemes_are_still_different():
    """The dialog hover is a softer plate carrying gold; the main hover is the
    inverse scheme. They were separate before this pass and stay separate."""
    for mode, palette in _palettes().items():
        assert palette["dialog_btn_hover_bg"] != palette["main_btn_hover_bg"], (
            f"{mode}: the dialog hover plate and the main hover plate now hold "
            f"the same value ({palette['main_btn_hover_bg']}). Flattening the "
            f"two loses a scheme.")
'''


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
    if code in (-9, 137, -15, 143):
        return "killed"
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


KILLED_HELP = """\
THE TEST PROCESS WAS KILLED FROM OUTSIDE. No test failed and nothing crashed --
something stopped the run, and on a small runner that is almost always the
out-of-memory killer arriving part way through a long Qt suite.

Re-run:

    python up.py --verify

If it keeps dying at roughly the same point, run the suite on its own so you
can watch it, and close anything else heavy first:

    QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
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
    elif verdict == "killed":
        print("\n" + KILLED_HELP)
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
        # A script whose sentinel file is created by an EARLIER script cannot
        # tell "wrong directory" from "prerequisite not run", and the default
        # message asserts the first while the second is more likely. Such a
        # script sets MISSING_HELP and says which one to run.
        raise SystemExit(globals().get("MISSING_HELP") or
                         f"run this from the root of a {REPO} checkout "
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
