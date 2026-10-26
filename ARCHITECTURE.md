# Architecture Decisions

This document captures the non-obvious design decisions made in RNV Color Palette Manager. It explains the *why* behind choices that the code itself cannot explain — the tradeoffs, failed experiments, and platform-specific workarounds that shaped the current architecture.

For a mechanical overview of what each module does, see the [Project Architecture section](README.md#project-architecture) in the README.

---

## Package Layout: `core / ui / utils`

The codebase is split into three packages with a one-way dependency direction (each imports only from the packages to its right):

```
ui  →  core  →  utils
```

- **`core/`** contains color science and palette data logic. Apart from the slot widget (below), it has no dependency on the presentation layer — a `ColorMath` conversion or a `PaletteFormats.export_palette()` call works identically whether invoked from the GUI, a unit test, or a future CLI frontend.
- **`ui/`** contains Qt widgets, dialogs, and the theming system. It imports from `core` (to work with palettes) and `utils` (for logging, config, helpers).
- **`utils/`** contains infrastructure — logging, config, colors, settings persistence, session management, file utilities. It imports nothing from `core` or `ui`.

**The exception:** `core/color_slot.py` holds the slot widget (`ColorSlotWidget`, a `QWidget`) as well as its model, and it imports `ui.image_button` and `ui.image_upload_dialog`. It is the one place where `core` reaches into `ui`.

**Why this matters:** when a bug appears in color math, the fix lives in `core/` and can be unit-tested without a `QApplication`. When a theming bug appears, the fix lives in `ui/` and the test suite still passes without touching color math. This separation is what keeps the test suites practical to maintain.

**Mixing functions:** `core/color_math.py` holds six mixing functions (`weighted_rgb_mix`, `weighted_hsv_mix`, `lab_perceptual_mix`, `subtractive_cmy_mix`, `weighted_ryb_mix`, `kubelka_munk_mix`). `ColorMath.MIX_NAMES` gives each one its display name and `ColorMath.mix()` calls it by that name. The slot menu's **Mix With...** reaches them through `MainWindow.start_mix_from()`, which uses the same click-the-target-slot mode as the gradient and the contrast check (while a target is being picked, `MainWindow._refresh_size_overlay()` shows *Click target slot* in the size overlay whatever its setting, and `Escape` calls `_cancel_target_pick()`); `MainWindow.mix_slots()` mixes the two colors in equal parts and adds the result as a new slot after the first one, in its group, as one undo step.

**Alternative considered:** a flat layout (all modules at the repo root) matching an earlier version of the codebase. Rejected because the project grew past ~15 modules and the flat structure made dependency cycles easy to introduce by accident.

---

## Colors: one file, written from one map

All theme colors are named in `utils/colors.py`. No other file in the codebase contains hardcoded color literals — not even for SVG exports, session-restore fallbacks, or transparency overlays. Every hex string, every RGB tuple, every `rgba(…)` CSS value is named in that one file.

The values in it are not edited by hand. `brand_map.json` says where each color comes from — a name in rnv-brand, at the commit `tests/requirements-dev.txt` pins, or a value this app owns, with the reason — and `python tools/sync_colors.py` writes the values into `utils/colors.py` and writes `COLORS.md`. `tests/test_colors_in_sync.py` fails while the two disagree. The README's *Changing a color* section gives the steps.

**Why:** before the centralization pass, the codebase had ~60–65 hardcoded color literals scattered across 15 files. Changing the brand gold required a project-wide find-and-replace that inevitably missed edge cases — a light-mode tooltip would still show the old color, or an exported SVG would look wrong. With one file of names, and the values written from one map, a color changes in one place and the diff of `utils/colors.py` shows every value that moved. The gold drawn into the button and background images does not follow; `ACCENT_IMAGES.md` lists those images.

**Exceptions that are correct:** `color_search.py` retains a `CSS_NAMED_COLORS` lookup dictionary with named colors (`"red": (255, 0, 0)`, etc.). This is reference data for the search feature — users typing "red" in the search bar expect it to match `#FF0000` regardless of theme. These are not theme colors and correctly live in that module.

**Mode-aware selection border:** the selected slot's border gold is chosen at paint time in `ColorSlot.paintEvent()`. Dark and image modes use `BRAND_GOLD_RGB`, which shows on a dark ground; light mode uses the darker `BRAND_DARK_GOLD_RGB`, because the bright gold would wash out on a white background.

---

## Avoiding `app.setStyle("Fusion")`

Qt offers several widget styles (Fusion, Windows, Windows11, macOS). Fusion is popular because it produces consistent cross-platform rendering. **This project deliberately does not use it.**

**Why:** Fusion silently changes default layout margins on `QPushButton`, `QFrame`, and several other widgets. The change breaks `sizeHint()` calculations used by the color slot widgets — slot buttons would visually intrude into adjacent color slots at both maximized and minimum window sizes. The bug only appeared after opening the Settings dialog, because that's when the Fusion style propagated to child widgets.

**What's used instead:** the platform's native widget style with theme-specific stylesheets applied via `QApplication.setStyleSheet()`. This produces theme consistency at the CSS level while preserving native widget metrics.

---

## Three-Pass Post-Show Fix for Image Mode

The main window applies layout fixes after `show()` in up to three passes:

1. **`_post_show_fix()`** runs via `QTimer.singleShot(0, ...)` — fires in the next event loop iteration, fixing slot sizes, scene rects and overlay positions. In image mode it also runs `_force_image_mode_refresh()` inline, so the first paint the user sees is already correct, and schedules the second pass.
2. **`_post_show_fix_image()`** runs 400ms later, **only in image mode** — repeats the refresh, then updates the scene rect and resets the view.
3. **`_post_show_fix_image_final()`** runs 600ms after that (about a second after show), **only if image mode is still active** — repeats the refresh once more, and leaves the scene rect and view alone so it does not undo any zoom or pan the user has started.

**Why:** in Image Mode, `scroll_content` and `preview_frame` — child widgets, not the main window — carry `WA_TranslucentBackground` so the background image shows through the slots. The slots live inside a `QGraphicsProxyWidget`, and on a cold start the proxy's first rasterization can produce solid-black slots instead of the semi-transparent fills. A user-triggered theme cycle clears it, because going through a non-image theme turns the attribute off and on again, which rebuilds Qt's backing stores; calling `apply_theme()` alone does not, since setting an attribute that is already on is a no-op. `_force_image_mode_refresh()` reproduces that off-and-on toggle and then the tail of `cycle_theme()`.

The 400ms and later passes are insurance against timing edge cases on slower hardware; on a machine where the inline pass worked they are visual no-ops.

**Why not poll:** there's no Qt API to ask whether the backing store is ready. Fixed delays were simpler and more reliable than wrapping the paint in a retry loop.

---

## Custom Tooltip Implementation

The app renders tooltips using a custom `_ThemedToolTip` class instead of the native `QToolTip`. This adds complexity — a `WA_TranslucentBackground` singleton widget with its own `paintEvent` drawing a rounded-rect background.

**Why:** `QToolTip` on Windows creates an OS-level popup window with its own frame that ignores CSS `border-radius`. In Light and Image modes this produced visibly unstyled tooltips — sharp corners where the rest of the app uses rounded corners, and a system-gray background that clashed with the dark/image themes.

The custom implementation is one small `QLabel` subclass in the main script and gives pixel-perfect themed tooltips in all three modes. The application-level event filter in `MainWindow.eventFilter()` intercepts `QEvent.ToolTip` and renders the custom tooltip instead.

---

## Session Auto-Save Over Document-Based Save/Open

The app doesn't have a File → Save or File → Open in the traditional sense. There's Import Palette and Export Palette for format interchange, but the active workspace state (colors, locked slots, groups, metadata) is auto-saved to `~/.rnv_color_palette_manager/sessions/autosave.json` on a timer (every 5 minutes by default, set in Settings → General) and once more on close, and restored on next launch while *Restore last session on startup* is on.

**Why:** this is a creative tool, not a document editor. Users creating a palette don't think about "saving the file" — they think about the colors. Modeling the app around sessions (timed auto-save + crash recovery) matches user mental model and eliminates the "I forgot to save" failure case entirely.

**What's preserved across sessions:**
- All slot colors, lock states, and order
- Slot group names, counts, and collapsed states
- Palette metadata (name, description, author, timestamps)
- Color change history (for the History panel)
- Active theme

**Crash recovery:** a `.recovery_needed` flag file is created when auto-save starts and deleted when it stops or the app shuts down cleanly. If the flag exists on next launch and the auto-saved session is less than 24 hours old, the app knows the previous session crashed and offers to restore it; declining discards it. Both files are written atomically through `utils/atomic_write.py`.

---

## Two Test Suites: `unittest` and `pytest`

The project has two suites, and `python run_tests.py` runs both under coverage and merges the results. [TESTING.md](TESTING.md) is the full guide.

- **`test_rnv_palette_manager.py`** (repository root) uses the standard `unittest` module. It needs nothing beyond the app's own requirements: `python test_rnv_palette_manager.py` runs it on any machine with Python 3.13, PyQt6 and Pillow installed. It is the established baseline and is kept as it is.
- **`tests/`** is a pytest suite, with `tests/conftest.py` for shared setup and fixtures, pytest-qt for widget tests, Hypothesis for property tests, pytest-benchmark for benchmarks, and pytest-timeout installed beside them. Its tools, and rnv-brand at the pinned commit, come from `tests/requirements-dev.txt`. New tests go here, including the guard tests that hold rules across the repository.

**Why both:** the `unittest` file came first and still runs with no test dependencies at all. The pytest suite was added later (the phase table in TESTING.md records the steps) for what `unittest` makes awkward: fixtures, parametrization, property-based tests, `qtbot`, and benchmarks.

**Tradeoffs accepted:**
- Two styles of test in one repository (`def test_...(self):` classes in the root file, plain functions and fixtures in `tests/`)
- Shared helpers have to be reachable from both: the root suite imports `tests.color_values`, the pytest suite imports `color_values`
- The pytest suite needs `tests/requirements-dev.txt` installed, including network access for the rnv-brand pin

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
- `pathlib.Path` for filesystem operations (a few helpers in `core/palette_formats.py`, `utils/error_handler.py` and `utils/file_utils.py` still call `os.path`)
- `Final` annotations on true constants
- Dataclasses for structured data (`PaletteMetadata`, `PaletteState`, `SlotGroupData`, etc.)

**Why 3.13 specifically:** the `type` statement is a 3.12+ feature and produces cleaner type aliases than the old `TypeAlias` annotation. 3.13 was the current stable release when the project was finalized; 3.13+ is enforced in `pyproject.toml`.

**Consequence:** the codebase will not run on 3.11 or earlier. This is intentional — supporting legacy Python versions would require regressing to older idioms and fragmenting the type hints.

---

## Known Limitations Worth Documenting

- **Single-window design.** The app is not MDI/tabbed — one palette per window. A user working with multiple palettes simultaneously opens multiple instances. Design rationale: the preview grid, zoom/pan workspace, and session state all assume a single active palette. Multi-document support would require a substantial redesign of the session and undo systems.

- **99 slot maximum.** Enforced in `config.py` as `MAX_SLOTS: Final[int] = 99`. This is a UX constraint, not a technical one — the grid layout and preview grid become visually unwieldy beyond this. Users wanting more colors split into multiple palettes or use groups.

- **PyInstaller one-file builds have slow first launch.** The bundled executable extracts to a temp directory on each launch. First-run adds ~3 seconds. Switching to one-folder mode (documented in the `.spec` file) eliminates this but produces a directory rather than a single file.
