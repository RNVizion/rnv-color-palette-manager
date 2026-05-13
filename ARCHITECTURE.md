# Architecture Decisions

This document captures the non-obvious design decisions made in RNV Color Palette Manager. It explains the *why* behind choices that the code itself cannot explain — the tradeoffs, failed experiments, and platform-specific workarounds that shaped the current architecture.

For a mechanical overview of what each module does, see the [Project Architecture section](README.md#project-architecture) in the README.

---

## Package Layout: `core / ui / utils`

The codebase is split into three packages that enforce a one-way dependency direction:

```
core  ←  ui  ←  utils
```

- **`core/`** contains color science and palette data logic. It has zero dependencies on presentation layer — a `ColorMath` conversion or a `PaletteFormats.export_palette()` call works identically whether invoked from the GUI, a unit test, or a future CLI frontend.
- **`ui/`** contains Qt widgets, dialogs, and the theming system. It imports from `core` (to work with palettes) and `utils` (for logging, config, helpers).
- **`utils/`** contains infrastructure — logging, config, settings persistence, session management, file utilities. It has no knowledge of color science or palette semantics.

**Why this matters:** when a bug appears in color mixing, the fix lives in `core/` and can be unit-tested without a `QApplication`. When a theming bug appears, the fix lives in `ui/` and the test suite still passes without touching color math. This separation is what makes the 374-test suite practical to maintain.

**Alternative considered:** a flat layout (all modules at the repo root) matching an earlier version of the codebase. Rejected because the project grew past ~15 modules and the flat structure made dependency cycles easy to introduce by accident.

---

## `colors.py` as the Single Source of Truth

All theme color values originate from `ui/colors.py`. No other file in the codebase contains hardcoded color literals — not even for SVG exports, session-restore fallbacks, or transparency overlays. Every hex string, every RGB tuple, every `rgba(…)` CSS value lives in one file.

**Why:** before the centralization pass, the codebase had ~60–65 hardcoded color literals scattered across 15 files. Changing the brand gold required a project-wide find-and-replace that inevitably missed edge cases — a light-mode tooltip would still show the old color, or an exported SVG would look wrong. After centralization, adjusting the accent color is a one-line edit.

**Exceptions that are correct:** `color_search.py` retains a `COLOR_NAMES` lookup dictionary with named color strings (`"red": (255,0,0)`, etc.). This is reference data for the search feature — users typing "red" in the search bar expect it to match `#FF0000` regardless of theme. These are not theme colors and correctly live in that module.

**Mode-aware exception:** `SLOT_SELECTED_COLOR` is defined in `colors.py` but resolves to different gold variants at paint time depending on active theme. Dark/image modes use the brighter `BRAND_GOLD_DARK_RGB`; light mode would blow out on a white background. This is intentional — the constant declares intent, the `paintEvent` resolves to the correct concrete color.

---

## Avoiding `app.setStyle("Fusion")`

Qt offers several widget styles (Fusion, Windows, Windows11, macOS). Fusion is popular because it produces consistent cross-platform rendering. **This project deliberately does not use it.**

**Why:** Fusion silently changes default layout margins on `QPushButton`, `QFrame`, and several other widgets. The change breaks `sizeHint()` calculations used by the color slot widgets — slot buttons would visually intrude into adjacent color slots at both maximized and minimum window sizes. The bug only appeared after opening the Settings dialog, because that's when the Fusion style propagated to child widgets.

**What's used instead:** the platform's native widget style with theme-specific stylesheets applied via `QApplication.setStyleSheet()`. This produces theme consistency at the CSS level while preserving native widget metrics.

---

## Two-Stage Post-Show Fix for Image Mode

The main window applies layout fixes after `show()` in two stages:

1. **`_post_show_fix()`** runs via `QTimer.singleShot(0, ...)` — fires in the next event loop iteration, fixing slot sizes and scene rects.
2. **`_post_show_fix_image()`** runs via `QTimer.singleShot(400, ...)` **only when image mode is active** — fixes transparency compositor issues.

**Why two stages:** in Image Mode, the main window uses `WA_TranslucentBackground` to let the background image show through transparent slot regions. On Windows, the DWM (Desktop Window Manager) compositor takes a variable amount of time to establish the translucency layer after `show()`. If a repaint happens before DWM is ready, transparent slots render as solid black.

`singleShot(0)` fires too early — the event loop has processed the paint event but DWM hasn't finished compositor setup. 400ms is empirically the shortest reliable delay across tested Windows 10/11 configurations.

**Why not poll:** there's no Qt API to query DWM compositor state. A fixed delay was simpler and more reliable than wrapping the paint in a retry loop.

---

## Custom Tooltip Implementation

The app renders tooltips using a custom `_ThemedToolTip` class instead of the native `QToolTip`. This adds complexity — a `WA_TranslucentBackground` singleton widget with its own `paintEvent` drawing a rounded-rect background.

**Why:** `QToolTip` on Windows creates an OS-level popup window with its own frame that ignores CSS `border-radius`. In Light and Image modes this produced visibly unstyled tooltips — sharp corners where the rest of the app uses rounded corners, and a system-gray background that clashed with the dark/image themes.

The custom implementation is ~80 lines and gives pixel-perfect themed tooltips in all three modes. The application-level event filter in `MainWindow.eventFilter()` intercepts `QEvent.ToolTip` and renders the custom tooltip instead.

---

## Session Auto-Save Over Document-Based Save/Open

The app doesn't have a File → Save or File → Open in the traditional sense. There's Import Palette and Export Palette for format interchange, but the active workspace state (colors, locked slots, groups, metadata) is auto-saved continuously to `~/.rnv_color_palette_manager/sessions/autosave.json` and restored on next launch.

**Why:** this is a creative tool, not a document editor. Users creating a palette don't think about "saving the file" — they think about the colors. Modeling the app around sessions (continuous auto-save + crash recovery) matches user mental model and eliminates the "I forgot to save" failure case entirely.

**What's preserved across sessions:**
- All slot colors, lock states, and order
- Slot group names, counts, and collapsed states
- Palette metadata (name, description, author, timestamps)
- Color change history (for the History panel)
- Active theme

**Crash recovery:** a `.recovery_needed` flag file is created on startup and deleted on clean shutdown. If the flag exists on next launch, the app knows the previous session crashed and offers to restore the last auto-saved state.

---

## `unittest` Instead of `pytest`

The test suite uses Python's standard `unittest` module rather than `pytest`.

**Why:** zero additional dependencies. The test suite runs via `python test_rnv_palette_manager.py` on any machine with Python 3.13 and PyQt6 already installed — no `pip install pytest` step, no `conftest.py`, no plugin ecosystem to maintain.

**Tradeoffs accepted:**
- More verbose test signatures (`def test_...(self):` instead of `def test_...():`)
- Less elegant parameterization (manual loops instead of `@pytest.mark.parametrize`)
- Simpler fixtures (`setUpClass` / `tearDownClass` instead of `@pytest.fixture`)

**Tradeoffs avoided:**
- Plugin version conflicts
- `conftest.py` scope confusion
- The "should I use `pytest` or `pytest-qt`?" decision

For a project this size, the standard library is sufficient and the no-dependency constraint is worth preserving.

---

## PyQt6 Cleanup via `os._exit()`

The test suite ends with `os._exit(0 if result.wasSuccessful() else 1)` instead of `sys.exit()`.

**Why:** PyQt6 performs internal cleanup at interpreter shutdown that can crash in headless test environments (specifically, `QApplication` destruction interacting with the offscreen Qt platform plugin). `sys.exit()` triggers this cleanup; `os._exit()` bypasses it.

The crash is not a real bug — it happens after all tests have already passed or failed, and the exit code is preserved. But it produces noisy stack traces in CI output that obscure actual test failures.

**Alternative considered:** properly teardown `QApplication` in `tearDownModule()`. Rejected because the PyQt6 cleanup bug is platform-dependent (only occurs on certain Qt versions / offscreen configurations) and writing correct teardown for all cases was more complex than the one-line bypass.

---

## Modern Python 3.13 Idioms

The codebase uses Python 3.13 features consistently throughout:

- `from __future__ import annotations` in every module (enables forward references without quoting)
- `type` alias syntax (`type RGB = tuple[int, int, int]`)
- `match/case` for theme dispatch and platform detection
- `X | None` union syntax instead of `Optional[X]`
- `pathlib.Path` for all filesystem operations (no `os.path`)
- `Final` annotations on true constants
- Dataclasses for structured data (`PaletteMetadata`, `PaletteState`, `SlotGroupData`, etc.)

**Why 3.13 specifically:** the `type` statement is a 3.12+ feature and produces cleaner type aliases than the old `TypeAlias` annotation. 3.13 was the current stable release when the project was finalized; 3.13+ is enforced in `pyproject.toml`.

**Consequence:** the codebase will not run on 3.11 or earlier. This is intentional — supporting legacy Python versions would require regressing to older idioms and fragmenting the type hints.

---

## Known Limitations Worth Documenting

- **Single-window design.** The app is not MDI/tabbed — one palette per window. A user working with multiple palettes simultaneously opens multiple instances. Design rationale: the preview grid, zoom/pan workspace, and session state all assume a single active palette. Multi-document support would require a substantial redesign of the session and undo systems.

- **99 slot maximum.** Enforced in `config.py` as `MAX_SLOTS: Final[int] = 99`. This is a UX constraint, not a technical one — the grid layout and preview grid become visually unwieldy beyond this. Users wanting more colors split into multiple palettes or use groups.

- **PyInstaller one-file builds have slow first launch.** The bundled executable extracts to a temp directory on each launch. First-run adds ~3 seconds. Switching to one-folder mode (documented in the `.spec` file) eliminates this but produces a directory rather than a single file.
