# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
