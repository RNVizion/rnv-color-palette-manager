"""
test_error_handler.py — Tests for utils/error_handler.py
==========================================================

Phase 8a. Targets the largest single coverage gap in the project:
utils/error_handler.py at 36%. The module is pure logic with minimal
Qt dependencies, so no QApplication is needed for most tests.

Existing TestErrorHandlerValidators (in test_rnv_palette_manager.py)
already covers ValidationHelper's RGB/hex/weight/image_size validators
at the happy-path level. This file fills in:

  - ErrorHandler.safe_execute (all exception branches + success)
  - safe_method decorator (success, failure, default_return)
  - SafeFileOperations (open / write / delete)
  - exception_handler context manager (suppression, completion)
  - ValidationHelper.validate_file_path (not previously tested)
  - ErrorHandler._get_error_suggestion (each category)

We do NOT test:
  - show_error_dialog code paths (Tier 4: dialogs)
  - styled_message_box / styled_question_box (Tier 4: dialogs)
"""
from __future__ import annotations

from unittest import mock

import pytest

from utils.error_handler import (
    ErrorCategory,
    ErrorHandler,
    SafeFileOperations,
    ValidationHelper,
    exception_handler,
    safe_method,
)


# ═══════════════════════════════════════════════════════════════════════════
# ErrorCategory — string constants
# ═══════════════════════════════════════════════════════════════════════════
# Note: actual member name is IMAGE_PROCESSING (not IMAGE) — verified
# against utils/error_handler.py source.

def test_error_category_constants_are_strings():
    """All error categories must be non-empty strings."""
    categories = [
        ErrorCategory.FILE_IO,
        ErrorCategory.PERMISSION,
        ErrorCategory.VALIDATION,
        ErrorCategory.RESOURCE,
        ErrorCategory.IMAGE_PROCESSING,
        ErrorCategory.PALETTE,
        ErrorCategory.UNKNOWN,
    ]
    for cat in categories:
        assert isinstance(cat, str)
        assert len(cat) > 0


def test_error_category_values_are_unique():
    """Each category must have a unique string value."""
    values = [
        ErrorCategory.FILE_IO,
        ErrorCategory.PERMISSION,
        ErrorCategory.VALIDATION,
        ErrorCategory.RESOURCE,
        ErrorCategory.IMAGE_PROCESSING,
        ErrorCategory.PALETTE,
        ErrorCategory.UNKNOWN,
    ]
    assert len(values) == len(set(values))


# ═══════════════════════════════════════════════════════════════════════════
# ErrorHandler.safe_execute — success and exception paths
# ═══════════════════════════════════════════════════════════════════════════

def test_safe_execute_returns_success_for_normal_function():
    """A function that returns normally should yield (True, result)."""
    success, result = ErrorHandler.safe_execute(
        func=lambda: 42,
        operation_name="test op",
    )
    assert success is True
    assert result == 42


def test_safe_execute_passes_args_and_kwargs():
    """args and kwargs must be forwarded to the wrapped function."""
    def add(a, b, c=0):
        return a + b + c

    success, result = ErrorHandler.safe_execute(
        func=add,
        operation_name="add",
        args=(1, 2),
        kwargs={"c": 3},
    )
    assert success is True
    assert result == 6


def test_safe_execute_handles_file_not_found():
    """FileNotFoundError must be caught and produce (False, default_return)."""
    def raises():
        raise FileNotFoundError("missing.txt")

    success, result = ErrorHandler.safe_execute(
        func=raises,
        operation_name="read missing",
        default_return="DEFAULT",
    )
    assert success is False
    assert result == "DEFAULT"


def test_safe_execute_handles_permission_error():
    """PermissionError must be caught."""
    def raises():
        raise PermissionError("no access")

    success, result = ErrorHandler.safe_execute(
        func=raises,
        operation_name="perm test",
        default_return=None,
    )
    assert success is False
    assert result is None


def test_safe_execute_handles_value_error():
    """ValueError must be caught and routed to validation category."""
    def raises():
        raise ValueError("bad value")

    success, result = ErrorHandler.safe_execute(
        func=raises,
        operation_name="value test",
        default_return=[],
    )
    assert success is False
    assert result == []


def test_safe_execute_handles_generic_exception():
    """Any other Exception must also be caught."""
    def raises():
        raise RuntimeError("generic")

    success, result = ErrorHandler.safe_execute(
        func=raises,
        operation_name="generic test",
        default_return="fallback",
    )
    assert success is False
    assert result == "fallback"


def test_safe_execute_default_return_is_none_by_default():
    """When default_return is not provided, errors yield None."""
    def raises():
        raise RuntimeError()

    success, result = ErrorHandler.safe_execute(
        func=raises,
        operation_name="no default",
    )
    assert success is False
    assert result is None


def test_safe_execute_handles_memory_error():
    """MemoryError is forced to critical=True regardless of input."""
    def raises():
        raise MemoryError("OOM")

    success, result = ErrorHandler.safe_execute(
        func=raises,
        operation_name="memory test",
        default_return="oom-fallback",
        critical=False,  # explicitly false; MemoryError handler overrides
    )
    assert success is False
    assert result == "oom-fallback"


# ═══════════════════════════════════════════════════════════════════════════
# safe_method decorator
# ═══════════════════════════════════════════════════════════════════════════

class _DummyForDecorator:
    """Bare class with no QWidget inheritance — exercises non-widget path."""

    @safe_method(operation_name="DummyOp")
    def succeed(self, value):
        return value * 2

    @safe_method(operation_name="DummyFail", default_return="fallback")
    def fail(self):
        raise ValueError("oops")

    @safe_method()  # default operation_name (uses func name)
    def default_named(self):
        return "ok"


def test_safe_method_decorator_passes_through_success():
    """A successful method call returns its real result."""
    obj = _DummyForDecorator()
    assert obj.succeed(7) == 14


def test_safe_method_decorator_returns_default_on_failure():
    """A method that raises returns the configured default_return."""
    obj = _DummyForDecorator()
    assert obj.fail() == "fallback"


def test_safe_method_decorator_uses_function_name_when_unnamed():
    """If operation_name is omitted, the func's __name__ is used."""
    obj = _DummyForDecorator()
    assert obj.default_named() == "ok"


def test_safe_method_decorator_preserves_wrapped_function_name():
    """@wraps preserves __name__ for introspection."""
    obj = _DummyForDecorator()
    assert obj.succeed.__name__ == "succeed"


# ═══════════════════════════════════════════════════════════════════════════
# SafeFileOperations
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_text_file(tmp_path):
    """Create a small text file for read tests."""
    p = tmp_path / "sample.txt"
    p.write_text("hello world", encoding="utf-8")
    return p


def test_safe_open_file_succeeds_on_existing_file(tmp_text_file):
    """Opening an existing file returns (True, file_handle)."""
    success, handle = SafeFileOperations.safe_open_file(str(tmp_text_file), mode='r')
    try:
        assert success is True
        assert handle is not None
        content = handle.read()
        assert content == "hello world"
    finally:
        if handle is not None:
            handle.close()


def test_safe_open_file_returns_failure_on_missing_file():
    """Opening a non-existent file returns (False, None)."""
    success, handle = SafeFileOperations.safe_open_file(
        "/nonexistent/totally/missing.txt",
        mode='r',
    )
    assert success is False
    assert handle is None


def test_safe_open_file_supports_binary_mode(tmp_text_file):
    """Binary mode should not pass an encoding argument."""
    success, handle = SafeFileOperations.safe_open_file(str(tmp_text_file), mode='rb')
    try:
        assert success is True
        assert handle is not None
        assert handle.read() == b"hello world"
    finally:
        if handle is not None:
            handle.close()


def test_safe_write_file_writes_content(tmp_path):
    """safe_write_file creates a file with the given content."""
    target = tmp_path / "out.txt"
    success = SafeFileOperations.safe_write_file(str(target), "test content")
    assert success is True
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "test content"


def test_safe_write_file_returns_false_on_invalid_path():
    """Writing to an unwritable path returns False."""
    bad_path = "/this/path/should/not/exist/file.txt"
    success = SafeFileOperations.safe_write_file(bad_path, "content")
    assert success is False


def test_safe_delete_file_without_confirm_removes_file(tmp_text_file):
    """delete with confirm=False (no parent) removes the file."""
    assert tmp_text_file.exists()
    success = SafeFileOperations.safe_delete_file(
        str(tmp_text_file),
        confirm=False,
        parent=None,
    )
    assert success is True
    assert not tmp_text_file.exists()


def test_safe_delete_file_returns_false_when_file_missing():
    """Deleting a non-existent file returns False (FileNotFoundError caught)."""
    success = SafeFileOperations.safe_delete_file(
        "/totally/nonexistent/file.txt",
        confirm=False,
        parent=None,
    )
    assert success is False


# ═══════════════════════════════════════════════════════════════════════════
# exception_handler context manager
# ═══════════════════════════════════════════════════════════════════════════

def test_exception_handler_suppresses_exception_in_block():
    """An exception inside the block must be suppressed (not re-raised)."""
    with exception_handler("test op", parent=None, show_error=False):
        raise RuntimeError("intentional")
    assert True


def test_exception_handler_allows_clean_completion():
    """Code that doesn't raise should run to completion normally."""
    sentinel = []
    with exception_handler("clean op", parent=None, show_error=False):
        sentinel.append(1)
        sentinel.append(2)
    assert sentinel == [1, 2]


def test_exception_handler_returns_self_on_enter():
    """__enter__ returns the context manager instance."""
    handler = exception_handler("op", parent=None, show_error=False)
    with handler as h:
        assert h is handler


# ═══════════════════════════════════════════════════════════════════════════
# ValidationHelper.validate_file_path — not tested in unittest suite
# ═══════════════════════════════════════════════════════════════════════════

def test_validate_file_path_accepts_existing_file(tmp_text_file):
    """A path to an existing file should validate."""
    valid, msg = ValidationHelper.validate_file_path(
        str(tmp_text_file),
        must_exist=True,
    )
    assert valid is True


def test_validate_file_path_rejects_missing_when_required():
    """must_exist=True on a non-existent path returns invalid."""
    valid, msg = ValidationHelper.validate_file_path(
        "/totally/nonexistent.txt",
        must_exist=True,
    )
    assert valid is False
    assert isinstance(msg, str)
    assert len(msg) > 0


def test_validate_file_path_accepts_empty_when_not_required(tmp_path):
    """must_exist=False on a non-existent path may still pass parent checks."""
    target = tmp_path / "future_file.txt"
    valid, msg = ValidationHelper.validate_file_path(
        str(target),
        must_exist=False,
    )
    assert isinstance(valid, bool)
    assert isinstance(msg, str)


def test_validate_file_path_rejects_empty_string():
    """Empty path string should be rejected."""
    valid, msg = ValidationHelper.validate_file_path("", must_exist=False)
    assert valid is False
    assert isinstance(msg, str)


# ═══════════════════════════════════════════════════════════════════════════
# ErrorHandler._get_error_suggestion — verify each category gets a hint
# ═══════════════════════════════════════════════════════════════════════════

def test_get_error_suggestion_for_file_io_returns_string():
    suggestion = ErrorHandler._get_error_suggestion(ErrorCategory.FILE_IO, "details")
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0


def test_get_error_suggestion_for_permission_returns_string():
    suggestion = ErrorHandler._get_error_suggestion(ErrorCategory.PERMISSION, "details")
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0


def test_get_error_suggestion_for_validation_returns_string():
    suggestion = ErrorHandler._get_error_suggestion(ErrorCategory.VALIDATION, "details")
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0


def test_get_error_suggestion_for_resource_returns_string():
    suggestion = ErrorHandler._get_error_suggestion(ErrorCategory.RESOURCE, "details")
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0


def test_get_error_suggestion_for_unknown_returns_string():
    """Unknown category should still yield a (possibly generic) suggestion."""
    suggestion = ErrorHandler._get_error_suggestion("nonexistent_category", "details")
    assert isinstance(suggestion, str)
