#!/usr/bin/env python3
"""
RNV-COLLAPSE-TOOL-DO-NOT-SWEEP

Collapse #505050 onto grey 44, and give palette-manager the GREY_44 constant.

    python up.py             # apply, then verify
    python up.py --check     # rehearse every edit in memory, write nothing
    python up.py --verify    # run the suites only, change nothing
    python up.py --finish    # delete this file

WHY

The colour tree (2026-09-02) found five values named nowhere in the fleet. Rev
27 retires two of them into the light ladder and a third turned out to be
STATUS["error-text"] already. The last two were rendered beside their
neighbours and ruled on by Chris:

    #252525  ->  collapse onto APP card #2a2a2a
    #505050  ->  collapse onto grey 44   #444444

#252525 sat a third of the way from panel #1a1a1a to card #2a2a2a -- 1.1354
above one, 1.0679 below the other, neither a visible step. #505050 was one
application's private scrollbar handle where the other four already use
#444444. Neither was on the ladder or the ink grid. After this, neither exists.

THIS MOVES PIXELS. It is a ruling being applied, not a rename, and the guard
pins both the new values and the constants they are wired through.

WHAT MOVES HERE

    #505050  ->  #444444  (GREY_44)   {'dark': ['scroll_handle', 'scrollbar_handle'], 'image': ['scroll_handle']}

The guard reads the palettes by importing them and pins the new values, then
reads the source and asserts each key is wired through GREY_44 rather than
written as a fresh literal -- a script that swapped one literal for another
would pass the first check and fail the second.
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
DESCRIPTION = "collapse #505050 onto GREY_44"
SENTINEL_FILE = "ui/colors.py"
SENTINEL = "RNV-COLLAPSE-505050"
GUARD = "tests/test_collapse_505050.py"
SHADOWS = {"colors.py", "config.py", "conftest.py", "run_tests.py"}

SUITES = [
    ('run_tests.py (unittest + pytest)',
     [sys.executable, "run_tests.py"]),
]

OLD_HEX = "#505050"
NEW_HEX = "#444444"
CONST = "GREY_44"
KEYS = ['scroll_handle', 'scrollbar_handle']

EDITS = [
    ('ui/colors.py',
     'APP_PANEL_HOVER: Final[str] = "#3a3a3a"\n',
     'APP_PANEL_HOVER: Final[str] = "#3a3a3a"\n\n# grey(4) on the ink grid. The main button\'s pressed plate (ruled 2026-08-26)\n# and, from 2026-09-02, the scrollbar handle -- RNV-COLLAPSE-505050: this app\n# held #505050 for its handle where the other four already used #444444, and\n# #505050 was on neither the ladder nor the grid. Named here for the first\n# time in this app; rnv-text-transformer already calls it GREY_44.\nGREY_44: Final[str] = "#444444"\n',
     1),
    ('ui/colors.py',
     "    'scroll_handle': '#505050',\n",
     "    'scroll_handle': GREY_44,   # was #505050, see GREY_44\n",
     2),
    ('ui/colors.py',
     "    'scrollbar_handle': '#505050',\n",
     "    'scrollbar_handle': GREY_44,   # was #505050, see GREY_44\n",
     1),
    ('ui/colors.py',
     "    'hover_color': '#444444',\n",
     "    'hover_color': GREY_44,\n",
     2),
    ('ui/colors.py',
     "    'main_btn_pressed_bg': '#444444',\n",
     "    'main_btn_pressed_bg': GREY_44,\n",
     3),
]


def edits(tree) -> None:
    for rel, old, new, times in EDITS:
        tree.sub(rel, old, new, times)
    print(f"  {len(EDITS)} edit(s) composed")


def checks(tree) -> None:
    src = tree.read(SENTINEL_FILE)
    if f"'{OLD_HEX}'" in src or f'"{OLD_HEX}"' in src:
        raise SystemExit(f"{OLD_HEX} survived in {SENTINEL_FILE}")
    if src.count(SENTINEL) != 1:
        raise SystemExit("the ruling note did not land exactly once")
    for key in KEYS:
        pattern = re.compile(r"'%s':\s+%s\b" % (key, CONST))
        if not pattern.search(src):
            raise SystemExit(f"{key} is not wired through {CONST}")

    # The five #444444 entries that were already this value are now wired.
    # A literal '#444444' left in a palette after this would be a value this
    # file names and then does not use.
    src = tree.read("ui/colors.py")
    body = src[src.index("DARK_THEME_COLORS"):]
    if "'#444444'" in body:
        raise SystemExit("a palette still writes '#444444' as a literal after "
                         "GREY_44 was introduced")

    print(f"  guards: {OLD_HEX} is gone, {len(KEYS)} key(s) wired through {CONST}")


GUARD_SOURCE = r'''"""#505050 no longer exists in this application. RNV-COLLAPSE-GUARD

Ruled 2026-09-02: #505050 collapses onto GREY_44 #444444. The value was on
neither the surface ladder nor the ink grid, and its neighbours were not a
visible step away. This guard pins the ruling in both directions: the keys
hold the new value, and they hold it THROUGH the constant.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD_HEX = "#505050"
NEW_HEX = "#444444"
CONST = "GREY_44"
KEYS = ['scroll_handle', 'scrollbar_handle']
EXPECT = {'dark': ['scroll_handle', 'scrollbar_handle'], 'image': ['scroll_handle']}
PALETTE_FILE = "ui/colors.py"


def _palettes():
    from ui.colors import DARK_THEME_COLORS as D, IMAGE_MODE_COLORS as I, LIGHT_THEME_COLORS as L; P={'dark':D,'image':I,'light':L}
    return P


def test_the_ruled_keys_hold_the_new_value():
    for mode, keys in EXPECT.items():
        palette = _palettes()[mode]
        for key in keys:
            assert palette[key] == NEW_HEX, (
                f"{mode}[{key}] is {palette[key]}, ruled onto {NEW_HEX}")


def test_the_old_value_is_gone_from_every_palette():
    for mode, palette in _palettes().items():
        holders = [k for k, v in palette.items() if str(v).lower() == OLD_HEX]
        assert not holders, f"{mode} still holds {OLD_HEX} under {holders}"


def test_the_keys_are_wired_through_the_constant_not_rewritten():
    """Swapping one literal for another passes the value check and defeats
    the point. The constant is what a later substitution changes."""
    src = (ROOT / PALETTE_FILE).read_text(encoding="utf-8-sig")
    for key in KEYS:
        assert re.search(r"'%s':\s+%s\b" % (key, CONST), src), (
            f"{key} is not written as {CONST} in {PALETTE_FILE}")


def test_the_old_value_is_not_written_anywhere_in_source():
    """A sweep for the literal AS A STRING -- quoted. The palette file records
    "was #505050" in a comment beside each ruled key, and that mention is the
    provenance, not a use. The first version of this test matched the bare
    text and failed on its own script's comment: use versus mention, again.
    Excludes this guard and the delivery script, which quote the value in
    order to forbid it."""
    strays = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(p in {".git", "build", "dist", ".venv", "__pycache__"} for p in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if "RNV-COLLAPSE-GUARD" in text or "RNV-COLLAPSE-TOOL-DO-NOT-SWEEP" in text:
            continue
        if re.search(r"""['"]%s['"]""" % OLD_HEX, text, re.I):
            strays.append(str(path.relative_to(ROOT)))
    assert not strays, f"{OLD_HEX} is still written as a literal in: {strays}"
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
