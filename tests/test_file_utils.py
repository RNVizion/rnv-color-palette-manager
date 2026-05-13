"""
test_file_utils.py — Tests for utils/file_utils.py
====================================================

Phase 12a. Targets ~50% of file_utils.py that's still uncovered:
the helpers used by export, import, palette saving, and recovery.

Strategy: pure logic tests with `tmp_path` fixtures. No Qt, no
project state, no network. Each test is self-contained.

What's covered
--------------
- ensure_file_extension: extension-or-not, empty path, dotted path
- validate_file_path: existence, writability, missing parent
- get_safe_filename: invalid chars, length truncation, empty input,
  trim trailing dots/spaces, custom replacement
- create_directory_if_not_exists: success, idempotent, nested
- get_file_size_bytes / formatted: B / KB / MB ranges, missing file
- backup_file: single backup, rotation, max-backups behavior
- get_unique_filename: collision counter
- get_file_extension: lowercase normalization
- is_valid_image_file / is_valid_palette_file: known and unknown extensions
- copy_file / move_file / delete_file: success and missing-source
- list_files: pattern match, recursive
- module-level convenience functions
"""
from __future__ import annotations

from pathlib import Path

import pytest

from utils.file_utils import (
    FileUtils,
    ensure_extension,
    safe_filename,
    file_exists,
    mkdir,
)


# ═══════════════════════════════════════════════════════════════════════════
# ensure_file_extension
# ═══════════════════════════════════════════════════════════════════════════

def test_ensure_file_extension_adds_when_missing():
    assert FileUtils.ensure_file_extension("palette", ".gpl") == "palette.gpl"


def test_ensure_file_extension_keeps_existing():
    """An existing extension is not replaced."""
    assert FileUtils.ensure_file_extension("palette.json", ".gpl") == "palette.json"


def test_ensure_file_extension_handles_empty_path():
    """An empty path is returned unchanged."""
    assert FileUtils.ensure_file_extension("", ".gpl") == ""


def test_ensure_file_extension_with_path_components():
    """Extension is added to filename, path components untouched."""
    result = FileUtils.ensure_file_extension("/some/path/palette", ".ase")
    assert result == "/some/path/palette.ase"


# ═══════════════════════════════════════════════════════════════════════════
# validate_file_path
# ═══════════════════════════════════════════════════════════════════════════

def test_validate_file_path_returns_false_for_empty():
    assert FileUtils.validate_file_path("") is False


def test_validate_file_path_accepts_existing_file(tmp_path):
    target = tmp_path / "exists.txt"
    target.write_text("hello")
    assert FileUtils.validate_file_path(str(target), must_exist=True) is True


def test_validate_file_path_rejects_missing_when_required(tmp_path):
    missing = tmp_path / "nope.txt"
    assert FileUtils.validate_file_path(str(missing), must_exist=True) is False


def test_validate_file_path_accepts_writable_directory(tmp_path):
    target = tmp_path / "future.txt"
    assert FileUtils.validate_file_path(
        str(target), must_exist=False, check_writable=True
    ) is True


def test_validate_file_path_rejects_path_with_missing_parent(tmp_path):
    """A path whose parent directory doesn't exist returns False."""
    missing_parent = tmp_path / "no_such_dir" / "file.txt"
    assert FileUtils.validate_file_path(str(missing_parent)) is False


# ═══════════════════════════════════════════════════════════════════════════
# get_safe_filename
# ═══════════════════════════════════════════════════════════════════════════

def test_get_safe_filename_replaces_invalid_chars():
    """Windows-illegal characters are replaced."""
    result = FileUtils.get_safe_filename('my:file*name.gpl')
    assert ':' not in result
    assert '*' not in result
    assert result == 'my_file_name.gpl'


def test_get_safe_filename_handles_all_invalid_chars():
    """All chars in INVALID_FILENAME_CHARS are replaced."""
    raw = 'a<b>c:d"e/f\\g|h?i*j.txt'
    result = FileUtils.get_safe_filename(raw)
    for bad_char in '<>:"/\\|?*':
        assert bad_char not in result


def test_get_safe_filename_returns_unnamed_for_empty():
    assert FileUtils.get_safe_filename("") == "unnamed"


def test_get_safe_filename_strips_trailing_dots_and_spaces():
    """Windows hates trailing dots and spaces in filenames."""
    assert FileUtils.get_safe_filename("file...   ") == "file"


def test_get_safe_filename_truncates_long_names():
    """Names longer than max_length are truncated, preserving extension."""
    long_name = "a" * 300 + ".txt"
    result = FileUtils.get_safe_filename(long_name, max_length=255)
    assert len(result) <= 255
    assert result.endswith(".txt")


def test_get_safe_filename_uses_custom_replacement():
    """The replacement character can be customized."""
    result = FileUtils.get_safe_filename("a:b", replacement="-")
    assert result == "a-b"


def test_get_safe_filename_returns_unnamed_when_only_invalid_chars():
    """If the input is all invalid characters, fall back to 'unnamed'."""
    result = FileUtils.get_safe_filename("...   ")
    assert result == "unnamed"


# ═══════════════════════════════════════════════════════════════════════════
# create_directory_if_not_exists
# ═══════════════════════════════════════════════════════════════════════════

def test_create_directory_creates_new(tmp_path):
    target = tmp_path / "newdir"
    assert not target.exists()
    assert FileUtils.create_directory_if_not_exists(target) is True
    assert target.exists()


def test_create_directory_is_idempotent(tmp_path):
    """Creating an already-existing directory is fine."""
    target = tmp_path / "exists"
    target.mkdir()
    assert FileUtils.create_directory_if_not_exists(target) is True


def test_create_directory_creates_nested_path(tmp_path):
    """Nested directories are created with parents=True."""
    target = tmp_path / "a" / "b" / "c"
    assert FileUtils.create_directory_if_not_exists(target) is True
    assert target.exists()


# ═══════════════════════════════════════════════════════════════════════════
# get_file_size_bytes / get_file_size_formatted
# ═══════════════════════════════════════════════════════════════════════════

def test_get_file_size_bytes_returns_size(tmp_path):
    target = tmp_path / "sized.txt"
    target.write_bytes(b"X" * 100)
    assert FileUtils.get_file_size_bytes(target) == 100


def test_get_file_size_bytes_returns_zero_for_missing():
    assert FileUtils.get_file_size_bytes("/nonexistent/file.bin") == 0


def test_get_file_size_formatted_bytes(tmp_path):
    """Files under 1 KB show as 'N B'."""
    target = tmp_path / "tiny.txt"
    target.write_bytes(b"X" * 50)
    result = FileUtils.get_file_size_formatted(target)
    assert "B" in result
    assert "KB" not in result and "MB" not in result


def test_get_file_size_formatted_kilobytes(tmp_path):
    """Files in KB range show as '... KB'."""
    target = tmp_path / "medium.bin"
    target.write_bytes(b"X" * (5 * 1024))  # 5 KB
    result = FileUtils.get_file_size_formatted(target)
    assert "KB" in result


def test_get_file_size_formatted_megabytes(tmp_path):
    """Files >= 1 MB show as '... MB'."""
    target = tmp_path / "big.bin"
    target.write_bytes(b"X" * (2 * 1024 * 1024))  # 2 MB
    result = FileUtils.get_file_size_formatted(target)
    assert "MB" in result


def test_get_file_size_formatted_unknown_for_missing():
    assert FileUtils.get_file_size_formatted("/no/such/file") == "Unknown"


# ═══════════════════════════════════════════════════════════════════════════
# backup_file
# ═══════════════════════════════════════════════════════════════════════════

def test_backup_file_creates_first_backup(tmp_path):
    """First backup gets the suffix '1'."""
    source = tmp_path / "data.json"
    source.write_text("original")

    backup_path = FileUtils.backup_file(source, max_backups=5)
    assert backup_path is not None
    assert Path(backup_path).exists()
    assert Path(backup_path).read_text() == "original"


def test_backup_file_returns_none_for_missing_source(tmp_path):
    """No backup if the source doesn't exist."""
    missing = tmp_path / "ghost.json"
    assert FileUtils.backup_file(missing) is None


def test_backup_file_single_backup_mode(tmp_path):
    """max_backups=1 uses simple suffix without numeric counter."""
    source = tmp_path / "single.json"
    source.write_text("data")

    backup = FileUtils.backup_file(source, backup_suffix=".bak", max_backups=1)
    assert backup is not None
    assert backup.endswith(".bak")
    assert not backup.endswith(".bak1")


def test_backup_file_creates_separate_backups_until_full(tmp_path):
    """Up to max_backups separate backup files accumulate."""
    source = tmp_path / "rotate.json"
    source.write_text("data")

    paths = []
    for _ in range(3):
        path = FileUtils.backup_file(source, max_backups=3)
        assert path is not None
        paths.append(path)

    # Three distinct backup files were created
    assert len(set(paths)) == 3
    for p in paths:
        assert Path(p).exists()


def test_backup_file_rotates_when_max_reached(tmp_path):
    """Once max_backups is reached, oldest is rotated out."""
    source = tmp_path / "rot.json"
    source.write_text("v1")

    # Fill all 3 backup slots
    for _ in range(3):
        FileUtils.backup_file(source, max_backups=3)

    # Now trigger rotation (oldest removed, others shifted down)
    source.write_text("v_latest")
    new_backup = FileUtils.backup_file(source, max_backups=3)

    assert new_backup is not None
    # The newest backup should contain the latest content
    assert Path(new_backup).read_text() == "v_latest"


# ═══════════════════════════════════════════════════════════════════════════
# get_unique_filename
# ═══════════════════════════════════════════════════════════════════════════

def test_get_unique_filename_returns_base_when_no_collision(tmp_path):
    name = FileUtils.get_unique_filename(tmp_path, "palette", ".gpl")
    assert name == "palette.gpl"


def test_get_unique_filename_appends_counter_on_collision(tmp_path):
    """When the base name exists, append _1, _2, etc."""
    (tmp_path / "palette.gpl").write_text("first")

    name = FileUtils.get_unique_filename(tmp_path, "palette", ".gpl")
    assert name == "palette_1.gpl"

    # Create the _1 file too
    (tmp_path / "palette_1.gpl").write_text("second")

    name = FileUtils.get_unique_filename(tmp_path, "palette", ".gpl")
    assert name == "palette_2.gpl"


# ═══════════════════════════════════════════════════════════════════════════
# get_file_extension
# ═══════════════════════════════════════════════════════════════════════════

def test_get_file_extension_lowercases():
    """Extension is normalized to lowercase."""
    assert FileUtils.get_file_extension("PALETTE.GPL") == ".gpl"


def test_get_file_extension_includes_dot():
    assert FileUtils.get_file_extension("file.txt") == ".txt"


def test_get_file_extension_returns_empty_for_no_extension():
    assert FileUtils.get_file_extension("README") == ""


# ═══════════════════════════════════════════════════════════════════════════
# is_valid_image_file / is_valid_palette_file
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("ext", [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"])
def test_is_valid_image_file_accepts_known_extensions(ext):
    assert FileUtils.is_valid_image_file(f"image{ext}") is True


@pytest.mark.parametrize("ext", [".txt", ".gpl", ".pdf", ""])
def test_is_valid_image_file_rejects_unknown_extensions(ext):
    assert FileUtils.is_valid_image_file(f"file{ext}") is False


@pytest.mark.parametrize("ext", [".gpl", ".ase", ".aco", ".json", ".css", ".svg"])
def test_is_valid_palette_file_accepts_known_extensions(ext):
    assert FileUtils.is_valid_palette_file(f"palette{ext}") is True


@pytest.mark.parametrize("ext", [".png", ".pdf", ".doc", ""])
def test_is_valid_palette_file_rejects_unknown_extensions(ext):
    assert FileUtils.is_valid_palette_file(f"file{ext}") is False


# ═══════════════════════════════════════════════════════════════════════════
# copy_file / move_file / delete_file
# ═══════════════════════════════════════════════════════════════════════════

def test_copy_file_copies_content(tmp_path):
    source = tmp_path / "src.txt"
    source.write_text("hello")
    dest = tmp_path / "dst.txt"

    assert FileUtils.copy_file(source, dest) is True
    assert dest.read_text() == "hello"
    assert source.exists()  # Source still there after copy


def test_copy_file_returns_false_for_missing_source(tmp_path):
    dest = tmp_path / "dst.txt"
    assert FileUtils.copy_file("/nonexistent.txt", dest) is False


def test_move_file_moves_content(tmp_path):
    source = tmp_path / "src.txt"
    source.write_text("data")
    dest = tmp_path / "dst.txt"

    assert FileUtils.move_file(source, dest) is True
    assert dest.read_text() == "data"
    assert not source.exists()  # Source gone after move


def test_delete_file_removes_existing(tmp_path):
    target = tmp_path / "doomed.txt"
    target.write_text("delete me")

    assert FileUtils.delete_file(target) is True
    assert not target.exists()


def test_delete_file_succeeds_for_missing_file(tmp_path):
    """Deleting a non-existent file is treated as success (idempotent)."""
    missing = tmp_path / "ghost.txt"
    assert FileUtils.delete_file(missing) is True


# ═══════════════════════════════════════════════════════════════════════════
# list_files
# ═══════════════════════════════════════════════════════════════════════════

def test_list_files_returns_matching_pattern(tmp_path):
    """Pattern matching uses glob syntax."""
    (tmp_path / "a.gpl").write_text("")
    (tmp_path / "b.gpl").write_text("")
    (tmp_path / "c.txt").write_text("")

    gpl_files = FileUtils.list_files(tmp_path, pattern="*.gpl")
    assert len(gpl_files) == 2


def test_list_files_recursive_descends_subdirs(tmp_path):
    """recursive=True finds files in subdirectories."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "top.gpl").write_text("")
    (sub / "nested.gpl").write_text("")

    files = FileUtils.list_files(tmp_path, pattern="*.gpl", recursive=True)
    assert len(files) == 2


def test_list_files_returns_empty_for_missing_directory():
    """Missing directory returns empty list, not exception."""
    result = FileUtils.list_files("/no/such/dir")
    assert result == []


# ═══════════════════════════════════════════════════════════════════════════
# Module-level convenience functions
# ═══════════════════════════════════════════════════════════════════════════

def test_ensure_extension_convenience():
    assert ensure_extension("file", ".txt") == "file.txt"


def test_safe_filename_convenience():
    assert safe_filename("a:b") == "a_b"


def test_file_exists_convenience(tmp_path):
    target = tmp_path / "real.txt"
    target.write_text("")
    assert file_exists(str(target)) is True
    assert file_exists(str(tmp_path / "ghost.txt")) is False


def test_mkdir_convenience(tmp_path):
    target = tmp_path / "convenience_dir"
    assert mkdir(target) is True
    assert target.exists()
