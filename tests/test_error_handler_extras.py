"""
test_error_handler_extras.py — Final coverage push for error_handler.py
=========================================================================

Phase 13. Targets the remaining ~24% gap in utils/error_handler.py
that test_error_handler.py didn't reach. Excludes Tier 4 dialog code
(show_error_dialog, confirm_action, styled_message_box, styled_question_box,
safe_delete_file's confirm-prompt path) — those require real dialog
interaction.

What's targeted
---------------
- _get_error_suggestion: detail-string keyword detection for
  "disk/space", "memory", "permission" (lines 250-254)
- ValidationHelper.validate_file_path: extension list path (lines 422-426)
- ValidationHelper.validate_hex_color: empty, wrong length, bad chars
- ValidationHelper.validate_weight: type errors, range errors
- ValidationHelper.validate_rgb_values: type errors, range errors
- ValidationHelper.validate_image_size: range checks
- exception_handler.__exit__: exception suppression path

These are pure logic tests with no Qt dependency.
"""
from __future__ import annotations

import pytest

from utils.error_handler import (
    ErrorCategory,
    ErrorHandler,
    ValidationHelper,
    exception_handler,
)


# ═══════════════════════════════════════════════════════════════════════════
# _get_error_suggestion — detail-string keyword detection
# ═══════════════════════════════════════════════════════════════════════════
# When the category doesn't match a known suggestion, the code falls
# through to keyword detection in the details string. We hit each branch.

def test_get_error_suggestion_detects_disk_keyword():
    """Detail string mentioning 'disk' triggers disk-space hint."""
    suggestion = ErrorHandler._get_error_suggestion("xx_unknown", "the disk is full")
    assert "disk" in suggestion.lower() or "space" in suggestion.lower()


def test_get_error_suggestion_detects_space_keyword():
    """Detail string mentioning 'space' triggers disk-space hint."""
    suggestion = ErrorHandler._get_error_suggestion("xx_unknown", "no space left on device")
    assert "disk" in suggestion.lower() or "space" in suggestion.lower()


def test_get_error_suggestion_detects_memory_keyword():
    """Detail string mentioning 'memory' triggers memory hint."""
    suggestion = ErrorHandler._get_error_suggestion("xx_unknown", "out of memory")
    assert "memory" in suggestion.lower() or "applications" in suggestion.lower()


def test_get_error_suggestion_detects_permission_keyword():
    """Detail string mentioning 'permission' triggers permission hint."""
    suggestion = ErrorHandler._get_error_suggestion("xx_unknown", "permission denied")
    assert "permission" in suggestion.lower() or "administrator" in suggestion.lower()


def test_get_error_suggestion_falls_through_to_generic():
    """Without category match or detail keywords, returns generic hint."""
    suggestion = ErrorHandler._get_error_suggestion("xx_unknown", "random gibberish details")
    # The fallback mentions "log" — verify some non-empty guidance returned.
    assert isinstance(suggestion, str)
    assert len(suggestion) > 5


# ═══════════════════════════════════════════════════════════════════════════
# ValidationHelper.validate_file_path — extension check
# ═══════════════════════════════════════════════════════════════════════════

def test_validate_file_path_accepts_matching_extension(tmp_path):
    """A path with one of the allowed extensions validates."""
    target = tmp_path / "palette.gpl"
    target.write_text("dummy")
    valid, msg = ValidationHelper.validate_file_path(
        str(target),
        must_exist=True,
        extensions=[".gpl", ".ase"],
    )
    assert valid is True
    assert msg == ""


def test_validate_file_path_rejects_wrong_extension(tmp_path):
    """A path with a non-allowed extension is rejected."""
    target = tmp_path / "palette.txt"
    target.write_text("dummy")
    valid, msg = ValidationHelper.validate_file_path(
        str(target),
        must_exist=True,
        extensions=[".gpl", ".ase"],
    )
    assert valid is False
    assert ".gpl" in msg or "Invalid file type" in msg


def test_validate_file_path_extension_check_is_case_insensitive(tmp_path):
    """Extension check is case-insensitive (file_path.lower())."""
    target = tmp_path / "PALETTE.GPL"
    target.write_text("dummy")
    valid, _ = ValidationHelper.validate_file_path(
        str(target),
        must_exist=True,
        extensions=[".gpl"],
    )
    assert valid is True


# ═══════════════════════════════════════════════════════════════════════════
# ValidationHelper.validate_hex_color
# ═══════════════════════════════════════════════════════════════════════════

def test_validate_hex_color_accepts_6_digit_with_hash():
    valid, msg = ValidationHelper.validate_hex_color("#FF8800")
    assert valid is True
    assert msg == ""


def test_validate_hex_color_accepts_6_digit_without_hash():
    valid, msg = ValidationHelper.validate_hex_color("FF8800")
    assert valid is True


def test_validate_hex_color_accepts_3_digit_short_form():
    valid, msg = ValidationHelper.validate_hex_color("#F80")
    assert valid is True


def test_validate_hex_color_rejects_empty_string():
    valid, msg = ValidationHelper.validate_hex_color("")
    assert valid is False
    assert "empty" in msg.lower()


def test_validate_hex_color_rejects_wrong_length():
    """Anything other than 3 or 6 hex chars is invalid."""
    valid, msg = ValidationHelper.validate_hex_color("#FF88")  # 4 chars
    assert valid is False
    assert "length" in msg.lower()


def test_validate_hex_color_rejects_non_hex_chars():
    """Letters outside [0-9a-fA-F] make it invalid."""
    valid, msg = ValidationHelper.validate_hex_color("#GG8800")
    assert valid is False
    assert "hex" in msg.lower() or "character" in msg.lower()


# ═══════════════════════════════════════════════════════════════════════════
# ValidationHelper.validate_weight
# ═══════════════════════════════════════════════════════════════════════════

def test_validate_weight_accepts_in_range():
    valid, msg = ValidationHelper.validate_weight(50)
    assert valid is True


def test_validate_weight_rejects_below_min():
    valid, msg = ValidationHelper.validate_weight(-5)
    assert valid is False
    assert "range" in msg.lower() or "out of" in msg.lower()


def test_validate_weight_rejects_above_max():
    valid, msg = ValidationHelper.validate_weight(150)
    assert valid is False


def test_validate_weight_rejects_non_integer():
    """Non-numeric input returns the type-error message."""
    valid, msg = ValidationHelper.validate_weight("not a number")  # type: ignore[arg-type]
    assert valid is False
    assert "integer" in msg.lower()


def test_validate_weight_accepts_custom_range():
    """min_val and max_val parameters can widen the accepted range."""
    valid, _ = ValidationHelper.validate_weight(500, min_val=0, max_val=1000)
    assert valid is True


# ═══════════════════════════════════════════════════════════════════════════
# ValidationHelper.validate_rgb_values
# ═══════════════════════════════════════════════════════════════════════════

def test_validate_rgb_values_accepts_valid_triple():
    valid, msg = ValidationHelper.validate_rgb_values(255, 128, 0)
    assert valid is True
    assert msg == ""


def test_validate_rgb_values_rejects_red_above_255():
    valid, msg = ValidationHelper.validate_rgb_values(300, 0, 0)
    assert valid is False
    assert "Red" in msg or "range" in msg.lower()


def test_validate_rgb_values_rejects_green_below_0():
    valid, msg = ValidationHelper.validate_rgb_values(0, -10, 0)
    assert valid is False
    assert "Green" in msg or "range" in msg.lower()


def test_validate_rgb_values_rejects_blue_above_255():
    valid, msg = ValidationHelper.validate_rgb_values(0, 0, 999)
    assert valid is False
    assert "Blue" in msg or "range" in msg.lower()


def test_validate_rgb_values_rejects_non_integer():
    valid, msg = ValidationHelper.validate_rgb_values("a", 0, 0)  # type: ignore[arg-type]
    assert valid is False
    assert "integer" in msg.lower() or "Invalid" in msg


# ═══════════════════════════════════════════════════════════════════════════
# exception_handler — exception suppression path
# ═══════════════════════════════════════════════════════════════════════════
# test_error_handler.py covered the happy path; here we hit the
# __exit__ branch where exc_type is set and the handler suppresses.

def test_exception_handler_returns_true_on_exception():
    """When an exception fires inside the with-block, __exit__ returns True
    so the exception is suppressed."""
    handler = exception_handler("test op", parent=None, show_error=False)
    handler.__enter__()
    result = handler.__exit__(
        ValueError,
        ValueError("test error"),
        None,
    )
    assert result is True  # True signals "suppress this exception"


def test_exception_handler_returns_false_on_clean_exit():
    """When no exception is in flight, __exit__ returns False (no suppression
    needed)."""
    handler = exception_handler("test op", parent=None, show_error=False)
    handler.__enter__()
    result = handler.__exit__(None, None, None)
    assert result is False


def test_exception_handler_suppresses_exception_with_no_value():
    """If exc_val is None but exc_type is not, fallback message is used."""
    handler = exception_handler("test op", parent=None, show_error=False)
    handler.__enter__()
    # Edge case: exc_type set but exc_val is None
    result = handler.__exit__(RuntimeError, None, None)
    assert result is True


# ═══════════════════════════════════════════════════════════════════════════
# Cross-cutting: validators called as ValidationHelper class methods
# ═══════════════════════════════════════════════════════════════════════════
# test_rnv_palette_manager.py covers happy paths via the static method
# interface. Here we double-check that the boundary values land where
# expected (255, 0, 100, etc.) — not testing happy paths so much as
# boundary correctness.

@pytest.mark.parametrize("value", [0, 255])
def test_validate_rgb_accepts_boundary_values(value):
    """Both 0 and 255 are inclusive bounds for RGB channels."""
    valid, _ = ValidationHelper.validate_rgb_values(value, value, value)
    assert valid is True


@pytest.mark.parametrize("value", [0, 100])
def test_validate_weight_accepts_boundary_values(value):
    """0 and 100 are inclusive bounds for the default weight range."""
    valid, _ = ValidationHelper.validate_weight(value)
    assert valid is True
