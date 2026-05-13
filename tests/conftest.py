"""
conftest.py — pytest configuration shared by all tests under tests/

Loaded automatically by pytest before any test module. Five responsibilities:

  1. Headless Qt environment    — set QT_QPA_PLATFORM=offscreen before any
                                  PyQt6 import.
  2. Qt application attributes  — set AA_DontUseNativeDialogs before any
                                  QApplication is created.
  3. sys.path bootstrap         — add the project root for `core.*` etc.
  4. Hypothesis profile         — register the project's settings.
  5. MainWindow & Shortcut      — explicit helpers for loading MainWindow
                                  and triggering its QShortcuts. See the
                                  function docstrings for the why.
"""
from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════════
# 1. Headless Qt platform — must run BEFORE any PyQt6 import
# ═══════════════════════════════════════════════════════════════════════════
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# ═══════════════════════════════════════════════════════════════════════════
# 2. Qt application attributes — must run BEFORE any QApplication() call
# ═══════════════════════════════════════════════════════════════════════════
def _configure_qt_attributes() -> None:
    try:
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        return
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs)


_configure_qt_attributes()


# ═══════════════════════════════════════════════════════════════════════════
# 3. Project root on sys.path
# ═══════════════════════════════════════════════════════════════════════════
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ═══════════════════════════════════════════════════════════════════════════
# 4. Hypothesis profile registration
# ═══════════════════════════════════════════════════════════════════════════
from hypothesis import HealthCheck, settings

settings.register_profile(
    "rnv_default",
    deadline=None,
    max_examples=200,
    print_blob=True,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("rnv_default")


# ═══════════════════════════════════════════════════════════════════════════
# 5a. MainWindow loader — bypass package/module name ambiguity
# ═══════════════════════════════════════════════════════════════════════════
import importlib.util

_main_window_class_cache = None


def _load_main_window():
    """Load the MainWindow class from RNV_Color_Palette_Manager.py.

    The project root contains BOTH `RNV_Color_Palette_Manager.py` (the main
    script) AND `__init__.py` — under pytest's path setup the empty package
    shadows the .py file. We use importlib to load by absolute path with a
    unique synthetic name, sidestepping the resolution ambiguity entirely.

    Cached after first call so the (expensive) module-level code runs once.
    """
    global _main_window_class_cache
    if _main_window_class_cache is not None:
        return _main_window_class_cache

    main_path = _PROJECT_ROOT / "RNV_Color_Palette_Manager.py"
    if not main_path.exists():
        raise FileNotFoundError(
            f"Cannot locate main script at {main_path}. "
            f"Expected the file to live alongside core/, ui/, utils/."
        )

    spec = importlib.util.spec_from_file_location("_rnv_main_app", main_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to build import spec for {main_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["_rnv_main_app"] = module
    spec.loader.exec_module(module)

    if not hasattr(module, "MainWindow"):
        raise ImportError(
            f"Loaded {main_path} but it has no 'MainWindow' class."
        )

    _main_window_class_cache = module.MainWindow
    return _main_window_class_cache


# ═══════════════════════════════════════════════════════════════════════════
# 5b. Shortcut trigger — workaround for offscreen-Qt input limitation
# ═══════════════════════════════════════════════════════════════════════════
def _trigger_shortcut(window, key_sequence_str: str) -> None:
    """Trigger a QShortcut on `window` by emitting its `activated` signal.

    Why this exists
    ---------------
    pytest-qt's `qtbot.keyClick(window, key)` doesn't reliably fire QShortcut
    handlers under the offscreen Qt platform. QShortcut's default context is
    `Qt.WindowShortcut`, which requires the window to be the OS-level active
    window. The offscreen platform on Windows doesn't make windows active in
    the way Qt expects, so keyboard events never reach the shortcut.

    What this tests
    ---------------
    By finding the QShortcut child of `window` whose key sequence matches
    `key_sequence_str` and emitting its `activated` signal directly, we
    verify two things:
      1. A QShortcut with that key sequence actually exists (the shortcut
         was registered in `_setup_shortcuts`).
      2. The QShortcut is connected to a callback (the connection from
         `_setup_shortcuts` is intact).

    What this doesn't test
    -----------------------
    Whether real keyboard input would route correctly. That's Qt's
    responsibility to test, not ours, and it's not testable in offscreen
    mode anyway.

    Args:
        window: The QWidget the QShortcut is parented to (typically MainWindow).
        key_sequence_str: Qt-style key sequence string, e.g. "Ctrl+N", "Escape".

    Raises:
        AssertionError: if no shortcut matches, or if multiple shortcuts share
            the same key sequence.
    """
    from PyQt6.QtGui import QKeySequence, QShortcut

    target = QKeySequence(key_sequence_str)
    matching = [
        s for s in window.findChildren(QShortcut)
        if s.key() == target
    ]

    if not matching:
        all_keys = sorted(
            s.key().toString() for s in window.findChildren(QShortcut)
        )
        raise AssertionError(
            f"No QShortcut with key sequence {key_sequence_str!r} found on "
            f"{type(window).__name__}. "
            f"Available shortcuts: {all_keys}"
        )

    if len(matching) > 1:
        raise AssertionError(
            f"{len(matching)} QShortcuts match {key_sequence_str!r}; "
            f"expected exactly 1. The shortcut registry has a duplicate."
        )

    matching[0].activated.emit()
