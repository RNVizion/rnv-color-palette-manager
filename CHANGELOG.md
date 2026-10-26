# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed

- **Colors come from rnv-brand.** `utils/colors.py` (moved there from
  `ui/`) is no longer edited by hand. `brand_map.json` names where each
  color comes from, a name in rnv-brand or a value this app owns with
  the reason, and `python tools/sync_colors.py` writes the values and
  `COLORS.md`, the chart of this app's colors. A daily `brand-sync`
  workflow opens a pull request when a brand color this app uses moves.
- **rnv-brand is pinned.** `tests/requirements-dev.txt` installs
  rnv-brand from GitHub at a fixed commit, so the tests that compare
  this app's colors with the brand run instead of skipping. Moving the
  pin is an edit to that one line.
- **One Python and one set of ranges.** Python 3.13 is declared and is
  what CI runs. `pyproject.toml`, `requirements.txt` and
  `tests/requirements-dev.txt` declare the same ranges (PyQt6
  `>=6.5.0,<7.0`, Pillow `>=10.0.0,<13.0`), the test tools use the
  ranges shared by all five RNV apps, and pytest-timeout is installed.
- **Test dependencies moved** to `tests/requirements-dev.txt`, from the
  repository root.
- **Theme colors reworked**, mostly in light mode: grays brought onto
  one ramp, hovers take the mode's gold, and text on the dark gold of
  light mode is white (black stays on the bright gold of dark and image
  modes).
- **Smaller images.** The Image Mode background is 3840 px on its long
  edge, and the settings gear and app icon are 512 px.
- **CI** uses the Node 24 versions of the GitHub actions (checkout v5,
  setup-python v6). The step that uploaded coverage data, which
  uploaded nothing, is gone.
- **Default Export Format is used.** The Export Palette dialog opens on
  the format chosen in Settings → Export. Exporting a palette still sets
  it to the format used. Before, the dialog always opened on Adobe
  Swatch Exchange.
- **Subtractive CMY mixes like inks.** Each color is a filter that
  passes part of each channel's light, and the mix multiplies them (a
  weighted geometric mean), so yellow and blue make a dark green. It
  used to average the cyan, magenta and yellow values, which always
  gave the same color as RGB weighted. The RNV Color Mixer uses the
  same formula, and the two agree.

### Added

- **Mix With... on the slot menu.** Right-click a slot, choose Mix
  With..., click a second slot and pick an algorithm: RGB weighted, HSV
  weighted, CIE LAB perceptual, RYB artist's wheel, subtractive CMY or
  Kubelka-Munk. The two colors are mixed in equal parts and the mix is
  added as a new slot right after the first one, in its group; Undo
  takes it away. The six mixing functions were in `core/color_math.py`
  and tested, but nothing in the app called them.
- **Setup scripts.** `in.sh` (Linux and Codespaces, including the Qt
  system libraries) and `in.ps1` (Windows, which makes `.venv` with
  Python 3.13) install the same two requirements files.
- **Atomic state writes.** The session, its crash-recovery flag and the
  export history are written through `utils/atomic_write.py`, so a crash
  or a full disk mid-save leaves the old file or the new one, never a
  mixture.
- **Accent images.** `ACCENT_IMAGES.md` lists every image with the gold
  drawn into its pixels, written by `tools/accent_images.py`; those
  images do not follow a color change.
- **Guard tests** that hold rules across the repository: the colors in
  sync with the map and the pinned brand, the brand pin, atomic state
  writes, a status never shown by color alone, the accent image list,
  the two setup scripts, test counts in the docs stated as floors that
  hold, workflow action versions, dependency ranges, the Python floor,
  image sizes, the Pillow compatibility helper, and tests that cannot
  fail.

### Fixed

- **SVG export** chooses each swatch label's ink by contrast. It used
  the average of the channels, which put white on pure green.
- **About dialog in light mode:** the version label and the credits
  line were drawn in the bright gold at 1.70:1 on the light panel; they
  now use the mode's gold for text.
- **Pillow 14 readiness:** pixel reads go through
  `utils/pil_compat.py`, since `Image.getdata()` is deprecated and is
  removed in Pillow 14.
- **`pip install .` left out `resources/`**, so an installed copy had no
  font, icons or images and no Image mode. The fonts, icons, button
  images and background now install beside the code, where the app looks
  for them.
- **Generate Gradient To... with more than one group.** The colors it
  fills in are placed after the first slot but were not counted in its
  group, so that group's last slots moved into the next group. They now
  join the first slot's group, and the other groups keep their slots.
- **Move to Group into a group further down.** The slot landed one
  place too early. Moved into an empty group, such as one just made with
  Add New Group, it stayed at the end of the group before, and that
  group's last slot moved instead. The slot you move now goes to the end
  of the group you choose.
- **The input field in the Gradient Steps and New Group prompts** was
  white in dark and image modes. It now takes the theme's input colors,
  as the Settings dialog's fields do, and so does the new Mix Colors
  prompt's algorithm list.
- **"Click target slot"** is shown whenever Generate Gradient To...,
  Mix With... or Check Contrast With... waits for a second slot. It was
  shown only with the size overlay turned on, which is off by default,
  and stayed on the overlay after the pick ended. A resize or a theme
  change no longer replaces or restyles it mid-pick.
- **Esc cancels picking a target slot.** It used to leave the pick
  waiting while it closed the search bar or deselected a slot.

### Documentation

- The 3.3.3 notes count seven color mixing algorithms; there are six,
  in `core/color_math.py`, offered by the slot menu's Mix With...
- Two Settings tooltips corrected: the size overlay sits in the
  top-right corner, not the top-left, and the default slot border is
  none, not thin.
- Documentation checked against the code and corrected throughout (#87 A).

---

## [3.3.13] - 2026-05-21

*Note: Patch versions 3.3.4 through 3.3.12 were internal iterations
not separately released. This is the first public increment since
3.3.3.*

### Fixed

- **Cross-platform line-ending consistency in text-format exports.**
  All 12 text-format export methods (`gpl`, `json`, `xml`, `css`, `svg`,
  `hex`, `hsv`, `hsl`, `colors`, `afpalette`, `clr`, `txt`) now produce
  byte-identical output across Windows, macOS, and Linux. Previously,
  Python's text-mode `open()` substituted `\r\n` for `\n` on Windows
  only, creating inconsistent palette files when users shared exports
  across platforms. Fix applied to three patterns: simple text writes
  (8 methods, added `newline='\n'`), JSON writes (2 methods, same fix),
  and ElementTree XML/CLR exports (2 methods, switched to binary mode
  with explicit file objects).
- **ASE export signature mismatch** that caused a `TypeError` when
  exporting to Adobe Swatch Exchange format. The `_export_ase` function
  was missing the `metadata` parameter that the `export_palette`
  dispatcher passes to all format methods.
- **`.gitattributes` precedence** so the `snapshots/** binary` rule
  reliably overrides extension-specific text rules. Snapshot files now
  preserve their exact byte content across platforms and Git operations.

### Added

- **Linux CI workflow** (`.github/workflows/tests-linux.yml`) running
  the full test suite on Ubuntu with Python 3.13 on every push and PR.
  Complements the existing Windows workflow for genuine cross-platform
  verification.
- **Build scripts** for both platforms: `build_windows.bat` and
  `build_linux.sh`. Both are test-gated by default with a `--skip-tests`
  escape hatch for faster development rebuilds.
- **Related Projects section** in README, cross-linking to
  [RNV Color Picker](https://github.com/RNVizion/rnv-color-picker)
  and [RNV Color Mixer](https://github.com/RNVizion/rnv-color-mixer).

### Engineering notes

The line-ending bug was discovered while debugging snapshot test
failures in [RNV Color Mixer](https://github.com/RNVizion/rnv-color-mixer),
where byte-level comparison surfaced the platform-dependent output.
[RNV Color Picker](https://github.com/RNVizion/rnv-color-picker) had
no snapshot tests at the time, so the same latent bug existed
undetected — palette files shared between Windows and Linux users
would have inconsistent byte content. A cross-project audit applied
the same systematic fix to all three repositories.

The investment in snapshot testing paid for itself directly: a class
of bug that was invisible in functional tests (the files still
"worked") became immediately visible in byte-level tests. The Color
Picker fix is verified by code review against the audit pattern;
adding equivalent snapshot tests there is a future improvement.

---

## [3.3.3] - 2026-05-07

Initial public release.

### Highlights

- 16+ palette format imports and exports (Adobe ASE/ACO/ACB,
  GIMP GPL, Procreate Swatches, Affinity, CSS, JSON, SVG, etc.)
- Seven color mixing algorithms including CIE LAB, Kubelka-Munk
  pigment simulation, and RYB artist's wheel
- WCAG 2.1 contrast checking and color blindness simulation
- Three theme modes: Dark, Light, and Image-background
- Session auto-save with crash recovery
- Comprehensive test suite: 745 tests, 70% coverage
- Performance benchmarks for hot-path color math
- Cross-platform: Windows, macOS, Linux
