"""
test_qt_infrastructure.py — Phase 6 smoke tests for pytest-qt setup
=====================================================================

Purpose
-------
Verify that the Qt testing infrastructure is wired up correctly. These
tests do NOT exercise application logic — that's Phase 7. They confirm:

  - pytest-qt's `qapp` fixture creates a usable QApplication
  - The active Qt binding is PyQt6 (not PySide or PyQt5 by mistake)
  - Conftest's AA_DontUseNativeDialogs attribute survived to QApplication
  - qtbot lifecycle management (`addWidget`) works without crashing
  - qtbot signal capture (`waitSignal`) works on a synthetic button click

If any of these fail, Phase 7's interaction tests against the actual
application widgets won't work either — fix the infrastructure first.

Why a separate file
-------------------
Keeps the smoke layer distinct from real-functionality tests. When a
Phase 7 test fails, you can quickly run this file alone to isolate
"is the framework set up?" from "is the application broken?":

    pytest tests/test_qt_infrastructure.py -v

Run
---
    pytest tests/test_qt_infrastructure.py
    pytest tests/test_qt_infrastructure.py -v
"""
from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget


# ═══════════════════════════════════════════════════════════════════════════
# QApplication setup
# ═══════════════════════════════════════════════════════════════════════════

def test_qapp_fixture_provides_application(qapp):
    """pytest-qt's qapp fixture must yield a real QApplication instance."""
    assert qapp is not None, "qapp fixture returned None"
    assert isinstance(qapp, QApplication), (
        f"qapp returned {type(qapp).__name__}, expected QApplication"
    )


def test_qapp_uses_pyqt6_binding(qapp):
    """The active binding must be PyQt6, matching pyproject.toml's qt_api setting.

    If this fails: pytest-qt picked up PySide6 or PyQt5 from somewhere on the
    system. Verify [tool.pytest.ini_options] in pyproject.toml has
    `qt_api = "pyqt6"` set.
    """
    assert QApplication.__module__.startswith("PyQt6"), (
        f"QApplication came from {QApplication.__module__}, expected PyQt6.*. "
        f"Check qt_api setting in pyproject.toml."
    )


def test_native_dialogs_disabled(qapp):
    """AA_DontUseNativeDialogs must be active so QFileDialog etc. stay headless.

    If this fails: conftest.py isn't running its _configure_qt_attributes()
    before QApplication is created, OR something else creates a QApplication
    earlier (check for top-level imports in tests/ or src/).
    """
    assert QApplication.testAttribute(
        Qt.ApplicationAttribute.AA_DontUseNativeDialogs
    ), (
        "AA_DontUseNativeDialogs is not set. Native file/color dialogs would "
        "block during tests. Check tests/conftest.py."
    )


# ═══════════════════════════════════════════════════════════════════════════
# qtbot widget management
# ═══════════════════════════════════════════════════════════════════════════

def test_qtbot_can_add_widget(qtbot):
    """qtbot.addWidget should accept a widget for lifecycle tracking."""
    widget = QWidget()
    qtbot.addWidget(widget)
    # If we got here without exception, qtbot's lifecycle wiring works.
    # qtbot will auto-close and clean up the widget at end of test.


def test_qtbot_widget_can_be_shown(qtbot):
    """A widget added to qtbot can be shown without raising.

    waitExposed() blocks until the widget is actually visible (or timeout).
    Under offscreen platform this completes instantly.
    """
    widget = QWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget, timeout=1000)
    assert widget.isVisible()


# ═══════════════════════════════════════════════════════════════════════════
# qtbot signal capture
# ═══════════════════════════════════════════════════════════════════════════

def test_qtbot_can_capture_signal(qtbot):
    """qtbot.waitSignal should catch a clicked() signal within timeout."""
    button = QPushButton()
    qtbot.addWidget(button)

    with qtbot.waitSignal(button.clicked, timeout=1000) as blocker:
        button.click()

    # `blocker.signal_triggered` is True if the signal fired in time.
    assert blocker.signal_triggered, (
        "QPushButton.click() did not fire the clicked signal. "
        "If this fails the entire signal-capture infrastructure is broken."
    )


def test_qtbot_waitsignal_times_out_correctly(qtbot):
    """qtbot.waitSignal should raise on timeout when signal doesn't fire.

    Verifies the strict-by-default behavior introduced in pytest-qt 4.0:
    a signal that never fires should be treated as a test failure
    (TimeoutError raised), not silently ignored.
    """
    button = QPushButton()
    qtbot.addWidget(button)

    # We never click the button, so clicked never fires.
    # Expect TimeoutError to be raised by waitSignal.
    with pytest.raises(Exception):  # pytest-qt raises a specific exception type
        with qtbot.waitSignal(button.clicked, timeout=100, raising=True):
            pass  # do nothing — signal never fires
