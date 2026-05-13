# Testing Guide — RNV Color Palette Manager

This document covers the test suite architecture, how to run tests, and the
patterns that have been worked out for testing PyQt6 widgets in offscreen
mode. It is the single source of truth for "how this project does testing."

---

## Quick start

```powershell
# Install test dependencies (one-time)
pip install -r requirements-dev.txt

# Run the full suite (unittest + pytest + coverage report)
python run_tests.py

# Run only one suite
python -m unittest test_rnv_palette_manager.py -v
python -m pytest tests/ -v

# Run a single pytest file
python -m pytest tests/test_qt_main_window.py -v

# Run benchmarks
python -m pytest tests/test_perf_color_math.py --benchmark-only
```

---

## Architecture

The project has **two coexisting test suites**, by design:

### 1. unittest suite — `test_rnv_palette_manager.py` (root)

- **374 tests across 21 classes**, single file.
- Run via `python -m unittest test_rnv_palette_manager.py`.
- Mirrors the pattern from the sibling Color Mixer project — single
  monolithic test file, ANSI-colored summary, `os._exit()` to bypass
  PyQt6 cleanup crashes on shutdown.
- Covers: pure logic, validators, palette format roundtrips, MainWindow
  integration smoke tests, undo/redo, settings, color history.
- **Frozen.** New tests do not go here; this file is the established
  baseline that's known to pass on every supported Python/Qt combo.

### 2. pytest suite — `tests/` directory

- **371 tests** across 14 files (including 25 performance benchmarks).
- Run via `python -m pytest tests/`.
- Uses pytest fixtures + pytest-qt + hypothesis where each pays off.
- Where new tests go.

The two suites are independently runnable. `run_tests.py` runs both and
merges their coverage data.

**Combined: 745 tests, 70% coverage, 0 hangs, 0 flakes.**

---

## File layout

```
.
├── test_rnv_palette_manager.py         # Frozen unittest suite (374 tests)
├── tests/
│   ├── conftest.py                     # Shared pytest fixtures & helpers
│   ├── test_color_math_properties.py   # Hypothesis property tests
│   ├── test_export_snapshots.py        # Export format snapshots
│   ├── test_import_snapshots.py        # Import format snapshots
│   ├── test_qt_infrastructure.py       # pytest-qt smoke tests
│   ├── test_qt_main_window.py          # MainWindow keyboard/click tests
│   ├── test_qt_color_slot.py           # ColorSlot mouse interaction tests
│   ├── test_qt_color_slot_paint.py     # ColorSlot paintEvent visual tests
│   ├── test_qt_drag_drop.py            # Drag/drop event handler tests
│   ├── test_qt_search_and_workflows.py # Search bar + end-to-end workflows
│   ├── test_error_handler.py           # error_handler.py logic tests
│   ├── test_error_handler_extras.py    # Validator + suggestion logic tests
│   ├── test_file_utils.py              # FileUtils helper tests
│   ├── test_session_manager.py         # SessionManager + state tests
│   ├── test_perf_color_math.py         # Benchmarks for color math
│   └── test_perf_palette_io.py         # Benchmarks for palette I/O
├── run_tests.py                        # Unified runner (both suites + coverage)
├── .coveragerc                         # Coverage configuration
├── pyproject.toml                      # Includes [tool.pytest.ini_options]
├── requirements-dev.txt                # Test/benchmark dependencies
└── .benchmarks/                        # pytest-benchmark history (created on first run)
```

The `tests/` directory has **no `__init__.py`**. Adding one breaks pytest
collection because the project root has its own `__init__.py` that imports
from `utils.config`.

---

## Coverage

Run via `python run_tests.py`. Combines coverage from both suites.

Current coverage (after Phase 13):

| Module | Coverage |
|---|---|
| `core/accessibility.py` | 100% |
| `core/color_harmonies.py` | 100% |
| `core/palette_metadata.py` | 100% |
| `ui/colors.py` | 100% |
| `utils/undo_manager.py` | 99% |
| `core/color_math.py` | 96% |
| `ui/slot_group.py` | 97% |
| `utils/session_manager.py` | 94% |
| `ui/theme_manager.py` | 92% |
| `ui/color_search.py` | 91% |
| `utils/file_utils.py` | 89% |
| `utils/color_history.py` | 86% |
| `core/color_extractor.py` | 85% |
| `utils/error_handler.py` | 84% |
| `utils/export_history.py` | 81% |
| `utils/config.py` | 78% |
| `core/palette_formats.py` | 77% |
| `utils/recent_palettes.py` | 76% |
| `utils/settings_manager.py` | 74% |
| `utils/pixmap_cache.py` | 66% |
| `ui/zoomable_graphics_view.py` | 62% |
| `RNV_Color_Palette_Manager.py` | 55% |
| `core/color_slot.py` | 48% |
| `utils/logger.py` | 47% |
| `ui/image_button.py` | 44% |
| `utils/font_loader.py` | 41% |
| `ui/preview_grid.py` | 31% |
| **Total** | **70%** |

The remaining uncovered code is primarily Tier 4 (dialogs, native file
pickers, Windows-specific font registration). These paths are only
exercisable with real OS-level UI interaction; they are deliberately
excluded from the coverage target.

---

## Testing philosophy: tiers

We classify code by how testable it is in offscreen Qt mode:

- **Tier 1: Pure logic** — color math, palette format parsers, validators,
  undo/redo. Tested exhaustively, including via Hypothesis property tests.
  Target coverage: 90%+.

- **Tier 2: Stateful but headless** — settings manager, session manager,
  color history, file utilities. Pure logic with file I/O. Tested with
  `tmp_path` fixtures. Target coverage: 75%+.

- **Tier 3: Qt widgets without dialogs** — MainWindow construction, slot
  rendering, keyboard shortcuts, drag/drop event handlers. Tested via
  pytest-qt with offscreen platform. Target coverage: 50%+.

- **Tier 4: Modal dialogs and OS-level integration** — file pickers, color
  pickers, error dialogs, settings dialogs, font loader Windows registry
  calls. **Not tested.** These require real OS interaction; testing them
  in offscreen mode produces meaningless results or hangs.

When in doubt, ask: "does this require keyboard/mouse focus, native file
chooser, or OS-level window activation to test?" If yes → Tier 4.

---

## Patterns for testing PyQt6 widgets

Seven patterns that took some work to figure out. Use them; don't reinvent.

### 1. Importing `MainWindow` from `RNV_Color_Palette_Manager.py`

**Problem:** The project root contains both `RNV_Color_Palette_Manager.py`
(the main script) and `__init__.py` (the package marker). Under pytest's
import resolution, the directory becomes a package and shadows the `.py`
file — `from RNV_Color_Palette_Manager import MainWindow` fails.

**Solution:** Use the `_load_main_window()` helper in `tests/conftest.py`.
It loads the module via `importlib.util.spec_from_file_location` with a
synthetic name `_rnv_main_app`, sidestepping the resolution conflict.
The result is cached so the (expensive) module-level construction runs
once per test session.

```python
from conftest import _load_main_window

@pytest.fixture(scope="module")
def main_window(qapp):
    MainWindow = _load_main_window()
    win = MainWindow()
    yield win
```

### 2. Triggering keyboard shortcuts

**Problem:** `qtbot.keyClick(window, Qt.Key.Key_N, Qt.KeyboardModifier.ControlModifier)`
does NOT reliably fire `QShortcut` handlers in offscreen Qt mode on
Windows. QShortcut's default context (`Qt.WindowShortcut`) requires the
window to be the OS-level active window, which doesn't happen in offscreen
mode.

**Solution:** `_trigger_shortcut(window, "Ctrl+N")` in `tests/conftest.py`.
It finds the QShortcut child by key sequence and emits its `activated`
signal directly. This verifies (a) the shortcut exists with the right key
binding, and (b) it's connected to a callback. We deliberately do NOT
test Qt's keyboard input layer — that's Qt's responsibility.

```python
from conftest import _trigger_shortcut

def test_ctrl_n_adds_slot(main_window):
    before = len(main_window.slots_widgets)
    _trigger_shortcut(main_window, "Ctrl+N")
    assert len(main_window.slots_widgets) == before + 1
```

### 3. Mocking signal connections

**Problem:** `mock.patch.object(main_window, "_on_search_changed", wraps=...)`
does NOT intercept signal connections. PyQt captures bound method
objects at signal-connect time (during `__init__`), so patching the
attribute later doesn't affect the connection.

**Solution:** Verify observable side effects, not mock call counts.

```python
# WRONG — doesn't intercept the real handler
with mock.patch.object(main_window, "_on_search_changed", wraps=...) as h:
    bar._emit_search()
    assert h.called  # FAILS even though handler ran

# RIGHT — observe the side effect
slot._search_highlight = False
bar._input.setText("red")
bar._emit_search()
assert slot._search_highlight  # True only if handler ran
```

### 4. Bounded cleanup loops

**Problem:** Unbounded `while undo()` loops can hang for 5+ minutes if
`update_grid()` gets into a slow path or the undo stack runs empty
unexpectedly. Offscreen Qt's `update_grid()` is known to be slow on
large slot counts.

**Solution:** Always cap cleanup loops at a small iteration count.

```python
def _undo_until(main_window, target_count: int, max_iters: int = 5) -> None:
    for _ in range(max_iters):
        if len(main_window.slots_widgets) <= target_count:
            return
        main_window.undo()
```

Worst case: a few slots leak between tests. Best case: no infinite hangs.
Always prefer the leak.

### 5. Constructing widgets that need a `theme_manager`

**Problem:** `ColorSlotWidget` and many other widgets read theme keys via
`main_window.theme_manager.get_current_theme()['button_bg']` etc. Hand-
rolling a mock dict is fragile because `ImageButton.apply_style()` consumes
many keys (`button_bg`, `button_text`, `button_hover_bg`, `border_color`,
plus several optional ones via `.get()`).

**Solution:** Use a real `ThemeManager()`. It takes no constructor args
and produces a complete theme dict guaranteed to satisfy all consumers.

```python
from ui.theme_manager import ThemeManager

mw = mock.MagicMock()
mw.theme_manager = ThemeManager()  # ← real, fully-keyed theme
mw.settings_manager = mock.MagicMock()
mw.settings_manager.single_click_edit = False
# ColorSlotWidget construction also schedules a deferred
# _sync_scroll_content_height callback. Set these to None so the safe
# early-return in color_slot.py:905 fires:
mw.scroll_content = None
mw.zoom_view = None
```

### 6. Testing paintEvent

Render the widget to a `QPixmap`, then sample specific pixels.

```python
def _render_to_image(widget) -> QImage:
    pixmap = QPixmap(widget.size())
    pixmap.fill(Qt.GlobalColor.transparent)
    widget.render(pixmap)
    return pixmap.toImage()

# Sample with tolerance to handle antialiasing
center = image.pixelColor(50, 50)
assert _color_close(center, expected, tolerance=3)
```

Border sampling positions matter. The slot draws:
- `thin` border with `drawRect(0, 0, w-1, h-1)` and pen width 1 → sample (0, 0)
- `thick` border with `drawRect(1, 1, w-3, h-3)` and pen width 2 → sample (1, 1)
- `selected` border with `drawRect(1, 1, w-3, h-3)` and pen width 3 → sample (2, 2)

### 7. Testing drag-and-drop event handlers

Don't try to simulate drag-and-drop with `qtbot.mouseDrag` — it's
unreliable in offscreen Qt. Test the event handlers directly with mock
events.

```python
from PyQt6.QtCore import QByteArray, QMimeData

def _make_drag_event(mime_format, payload):
    mime = QMimeData()
    mime.setData(mime_format, QByteArray(payload.encode()))
    event = mock.MagicMock()
    event.mimeData.return_value = mime
    return event

def test_drag_enter_accepts_slot_reorder_mime(qtbot):
    widget, _ = _make_slot_widget(qtbot)
    event = _make_drag_event("application/x-rnv-slot-index", "0")
    widget.dragEnterEvent(event)
    event.acceptProposedAction.assert_called_once()
```

### Bonus: Monkeypatching module-level path constants

When testing modules with persistent state on disk (like `session_manager`),
the module typically has constants pointing to the user's real config
directory. Monkeypatch these to `tmp_path` so tests don't pollute the
user's actual data:

```python
@pytest.fixture
def isolated_session_paths(tmp_path, monkeypatch):
    autosave = tmp_path / "autosave.json"
    flag = tmp_path / ".recovery_needed"
    monkeypatch.setattr(session_manager, "SESSION_AUTO_SAVE_PATH", autosave)
    monkeypatch.setattr(session_manager, "RECOVERY_FLAG_PATH", flag)
    return autosave, flag
```

This works because the module's methods reference these via the global
name (`SESSION_AUTO_SAVE_PATH.exists()`), not via closure. Monkeypatch
rebinds the module attribute, and method lookups see the new value.

---

## Hypothesis property tests

`test_color_math_properties.py` uses Hypothesis to generate random RGB
triples and verify mathematical properties (round-trips, idempotence,
range invariants). The profile is registered in `tests/conftest.py`:

```python
settings.register_profile(
    "rnv_default",
    deadline=None,             # don't time-bound color conversions
    max_examples=200,          # generous coverage of input space
    print_blob=True,           # reproducible failure messages
    suppress_health_check=[HealthCheck.too_slow],
)
```

Round-trip tests live in `test_color_math_properties.py`. Edge case
tests for known-tricky inputs (pure black, pure white, primary colors,
near-grayscale) live in the same file under explicit parametrize blocks.

---

## Snapshot tests

`test_export_snapshots.py` and `test_import_snapshots.py` use a fixed
canonical 16-color palette and metadata with frozen timestamps
(`"2025-01-01T00:00:00"`) to produce deterministic output for every
format. Snapshots live in `tests/snapshots/`.

To regenerate snapshots after intentional format changes:

```powershell
$env:UPDATE_SNAPSHOTS = "1"
python -m pytest tests/test_export_snapshots.py
$env:UPDATE_SNAPSHOTS = $null
```

Round-trip tolerance per format is configured in `tests/test_import_snapshots.py`'s
`TOLERANCES` dict — some formats (`.aco`) lose precision on color rounding,
so a 1-2 unit RGB tolerance is allowed.

---

## Benchmarks

`test_perf_color_math.py` and `test_perf_palette_io.py` use pytest-benchmark
to track performance regressions in hot-path code.

### Running benchmarks

```powershell
# Run benchmarks once (no comparison)
python -m pytest tests/test_perf_color_math.py --benchmark-only

# Save current run as the baseline
python -m pytest tests/test_perf_*.py --benchmark-only --benchmark-save=baseline

# Compare current run against the baseline
python -m pytest tests/test_perf_*.py --benchmark-only --benchmark-compare

# Fail if any benchmark regresses by 25% or more
python -m pytest tests/test_perf_*.py --benchmark-only --benchmark-compare-fail=mean:25%
```

Benchmark history is stored in `.benchmarks/` (gitignored). To establish
a new baseline after intentional optimizations or refactors, delete the
old saves and re-run with `--benchmark-save=baseline`.

### What's benchmarked

- **Color math (single)**: `rgb_to_hex`, `hex_to_rgb`, `rgb_to_hsv`,
  `rgb_to_hsl`, `rgb_to_lab`, `lab_to_rgb`, `color_distance`
- **Color math (mixing)**: All six mixing algorithms with a typical
  4-slot input plus worst-case 30-slot inputs for the slowest two
  (`lab_perceptual_mix`, `kubelka_munk_mix`)
- **Palette generation**: `generate_color_palette` with 5 and 30 colors
- **Palette I/O**: Export and import for JSON, GPL, ASE, SVG, ACO

These run as part of the regular pytest suite (each as a 1-iteration test)
during `python run_tests.py`. The full warm-up + iteration cycle only
runs when `--benchmark-only` is passed.

---

## Common gotchas

A few things that have bitten us:

### `QApplication` must be created with `AA_DontUseNativeDialogs`

Set in `tests/conftest.py` before any QApplication is created. Native
dialogs (file pickers, color pickers) block on real OS UI and hang tests
that accidentally reach them.

### `QT_QPA_PLATFORM=offscreen` must be set before any PyQt6 import

Also handled in `tests/conftest.py`. Set via `os.environ.setdefault`
at the top of the file, before any `from PyQt6...` line.

### `update_grid()` in offscreen Qt is slow with many slots

Adding 30+ slots to a MainWindow and calling `update_grid()` can take
seconds. Tests that need many slots should either use the existing
default palette (which has ~30 slots already) or use `add_slot_with_color`
sparingly and undo at the end with bounded iteration.

### `MagicMock()` auto-creates attributes on access

This means `getattr(mock_main_window, 'scroll_content', None)` returns a
MagicMock, not None — defeating the safe-default fallback. Set
`mw.scroll_content = None` explicitly when you want the fallback path.

### Pillow `DecompressionBombWarning`

A few tests use very large test images that exceed Pillow's default
decompression limit. The warnings are harmless and come from Pillow,
not our code. They're filtered at the project level.

---

## Test phases (history)

For context on why the suite is structured this way:

| Phase | Focus | Tests added |
|---|---|---|
| 1 | Decisions/scope | — |
| 2 | Coverage baseline (`.coveragerc`, `run_tests.py`) | — |
| 3 | Coverage gap triage | — |
| 4 | Hypothesis property tests | 47 |
| 5 | Export snapshot tests | 35 |
| 5b | Import snapshot tests | 33 |
| 6 | pytest infrastructure (pytest-qt, pyproject.toml) | 7 |
| 7 | pytest-qt interaction tests | 32 |
| 8 | error_handler + paint events + drag/drop | 49 |
| 9 | Performance benchmarks | 25 |
| 10 | (skipped — mutmut not pursued) | — |
| 11 | Documentation polish | — |
| 12 | file_utils + session_manager | 71 |
| 13 | error_handler validators (final 70% push) | 31 |

Total: **374 unittest + 371 pytest = 745 tests, 70% coverage.**

---

## When tests fail

A few quick-diagnosis tips:

- **`KeyError: 'button_bg'`** during widget construction → use a real
  `ThemeManager()` instead of a mock dict.
- **`TypeError: '<' not supported between instances of 'MagicMock'`** →
  set `main_window.scroll_content = None` and `zoom_view = None` on
  your stub.
- **Test hangs for minutes** → check for unbounded `while undo()` loops;
  use `_undo_until(window, target, max_iters=5)`.
- **`AttributeError: type object 'ErrorCategory' has no attribute 'IMAGE'`**
  → it's `IMAGE_PROCESSING`. Always grep `error_handler.py` source
  before assuming names.
- **`TypeError: ColorSlotWidget.__init__() got an unexpected keyword
  argument 'color'`** → signature is `(slot, preview_grid, main_window)`,
  all positional. Construct a `ColorSlot` first.
- **Pixel test fails with wrong color** → verify the sample position.
  Border styles draw at different rect positions: thin at (0,0), thick
  at (1,1), selection at (2,2).
- **`Exceptions caught in Qt event loop`** during a test that otherwise
  passes → a deferred `QTimer.singleShot` callback is firing and
  crashing on a MagicMock attribute. Set those attributes to `None`
  on the stub.
- **`fixture 'benchmark' not found`** → `pytest-benchmark` isn't
  installed. Run `pip install -r requirements-dev.txt` against the same
  Python that runs your tests.
- **Tests touching the user's real session files** → the
  `session_manager` module has path constants that point to the user's
  config dir. Use the `isolated_session_paths` fixture (or write your
  own with `monkeypatch.setattr`) to redirect to `tmp_path`.
