"""
test_qt_color_slot_paint.py — ColorSlot.paintEvent visual tests
===================================================================

Phase 8b. ColorSlot's paintEvent is the largest uncovered branch in
core/color_slot.py. We don't test by spying on QPainter (fragile) — we
render the widget to a QPixmap and sample specific pixel positions.
This is closer to "what does the user see?" than method-call counting.

Border sampling note
--------------------
The slot draws thin border with `painter.drawRect(0, 0, w-1, h-1)` and
thick border with `painter.drawRect(1, 1, w-3, h-3)`. With pen widths
1 and 2 respectively, the actual filled border pixels are:
  - thin:  pixels at row/col 0 (a 1px outline)
  - thick: pixels at row/col 1 (a 2px outline)
Sample at (0, 0) for thin, (1, 1) for thick.
"""
from __future__ import annotations

import pytest
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QImage, QPixmap


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _render_to_image(widget) -> QImage:
    """Render a widget to a QImage so we can sample its pixels."""
    size: QSize = widget.size()
    if size.width() == 0 or size.height() == 0:
        widget.resize(100, 100)
        size = widget.size()

    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)
    widget.render(pixmap)
    return pixmap.toImage()


def _color_close(actual: QColor, expected: QColor, tolerance: int = 3) -> bool:
    """Whether two QColors match within a per-channel RGB tolerance."""
    return (
        abs(actual.red() - expected.red()) <= tolerance
        and abs(actual.green() - expected.green()) <= tolerance
        and abs(actual.blue() - expected.blue()) <= tolerance
    )


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def make_slot(qtbot):
    """Factory that creates a fresh ColorSlot for each test."""
    from core.color_slot import ColorSlot

    created = []

    def _make(color=None, theme_manager=None) -> "ColorSlot":
        slot = ColorSlot(
            color=color or QColor(255, 0, 0),
            base_size=100,
            theme_manager=theme_manager,
        )
        slot.resize(100, 100)
        qtbot.addWidget(slot)
        created.append(slot)
        return slot

    yield _make


# ═══════════════════════════════════════════════════════════════════════════
# SOLID COLOR PAINTING
# ═══════════════════════════════════════════════════════════════════════════

def test_paint_renders_solid_red(make_slot):
    """A red slot must paint red in its center."""
    slot = make_slot(color=QColor(255, 0, 0))

    image = _render_to_image(slot)
    center = image.pixelColor(50, 50)

    assert _color_close(center, QColor(255, 0, 0)), (
        f"Center pixel is {center.name()}, expected close to #ff0000"
    )


def test_paint_renders_solid_blue(make_slot):
    """A blue slot must paint blue in its center."""
    slot = make_slot(color=QColor(0, 0, 255))
    image = _render_to_image(slot)
    center = image.pixelColor(50, 50)
    assert _color_close(center, QColor(0, 0, 255))


def test_paint_renders_solid_green(make_slot):
    """A green slot must paint green in its center."""
    slot = make_slot(color=QColor(0, 255, 0))
    image = _render_to_image(slot)
    center = image.pixelColor(50, 50)
    assert _color_close(center, QColor(0, 255, 0))


# ═══════════════════════════════════════════════════════════════════════════
# IMAGE OVERRIDE
# ═══════════════════════════════════════════════════════════════════════════

def test_paint_uses_image_pixmap_when_set(make_slot):
    """When image_pixmap is set, the image is drawn instead of solid color."""
    slot = make_slot(color=QColor(255, 0, 0))

    yellow_pixmap = QPixmap(50, 50)
    yellow_pixmap.fill(QColor(255, 255, 0))
    slot.image_pixmap = yellow_pixmap
    slot.update()

    image = _render_to_image(slot)
    center = image.pixelColor(50, 50)

    assert _color_close(center, QColor(255, 255, 0)), (
        f"Center pixel is {center.name()}, expected close to yellow "
        f"(#ffff00). image_pixmap may not be drawn."
    )


# ═══════════════════════════════════════════════════════════════════════════
# BORDER STYLES
# ═══════════════════════════════════════════════════════════════════════════

def test_paint_no_border_by_default(make_slot):
    """Default border style is 'none' — no visible border at corner pixel."""
    slot = make_slot(color=QColor(0, 0, 0))
    assert slot.border_style == "none"

    image = _render_to_image(slot)
    corner = image.pixelColor(0, 0)
    assert _color_close(corner, QColor(0, 0, 0))


def test_paint_thin_border_is_drawn(make_slot):
    """border_style='thin' draws a 1px border at row/col 0."""
    from ui.colors import SLOT_BORDER_THIN_COLOR

    slot = make_slot(color=QColor(255, 255, 255))
    slot.border_style = "thin"

    image = _render_to_image(slot)
    border_pixel = image.pixelColor(0, 0)
    expected_border = QColor(*SLOT_BORDER_THIN_COLOR)

    assert _color_close(border_pixel, expected_border, tolerance=10), (
        f"Edge pixel {border_pixel.name()} should match thin border "
        f"color {expected_border.name()}"
    )


def test_paint_thick_border_is_drawn(make_slot):
    """border_style='thick' draws a 2px border with pen rect at (1,1).

    Source draws `painter.drawRect(1, 1, w-3, h-3)` with pen width 2,
    so the actual border outline pixels are at row/col 1 (inside) and
    row/col 2 (outside). Sample (1, 1) — the inner edge of the outline.
    """
    from ui.colors import SLOT_BORDER_THICK_COLOR

    slot = make_slot(color=QColor(255, 255, 255))
    slot.border_style = "thick"

    image = _render_to_image(slot)
    border_pixel = image.pixelColor(1, 1)
    expected = QColor(*SLOT_BORDER_THICK_COLOR)

    assert _color_close(border_pixel, expected, tolerance=15), (
        f"Border pixel at (1,1) is {border_pixel.name()}, "
        f"should match thick border color {expected.name()}"
    )


def test_paint_border_style_setter_rejects_invalid(make_slot):
    """border_style setter ignores invalid values silently."""
    slot = make_slot()

    slot.border_style = "thick"
    assert slot.border_style == "thick"

    slot.border_style = "garbage"
    assert slot.border_style == "thick"


# ═══════════════════════════════════════════════════════════════════════════
# SELECTION HIGHLIGHT
# ═══════════════════════════════════════════════════════════════════════════

def test_paint_selected_draws_gold_border(make_slot):
    """A selected slot draws a 3px gold border."""
    from ui.colors import BRAND_GOLD_RGB

    slot = make_slot(color=QColor(50, 50, 50))
    slot._selected = True

    image = _render_to_image(slot)
    border_pixel = image.pixelColor(2, 2)
    expected = QColor(*BRAND_GOLD_RGB)

    assert _color_close(border_pixel, expected, tolerance=10), (
        f"Selection border pixel {border_pixel.name()} should match "
        f"BRAND_GOLD_RGB {expected.name()}"
    )


def test_paint_unselected_does_not_draw_gold_border(make_slot):
    """An unselected slot does NOT draw the gold selection border."""
    from ui.colors import BRAND_GOLD_RGB

    fill = QColor(50, 50, 50)
    slot = make_slot(color=fill)
    slot._selected = False

    image = _render_to_image(slot)
    center = image.pixelColor(50, 50)
    gold = QColor(*BRAND_GOLD_RGB)

    assert _color_close(center, fill), (
        f"Center should be fill color {fill.name()}, got {center.name()}"
    )
    assert not _color_close(center, gold, tolerance=20), (
        "Unselected slot should not have gold anywhere in center"
    )


# ═══════════════════════════════════════════════════════════════════════════
# SEARCH HIGHLIGHT / DIM
# ═══════════════════════════════════════════════════════════════════════════

def test_paint_search_highlight_draws_glow_border(make_slot):
    """_search_highlight=True draws a glow border around the slot."""
    from ui.colors import SEARCH_HIGHLIGHT_COLOR

    slot = make_slot(color=QColor(0, 0, 0))
    slot._search_highlight = True

    image = _render_to_image(slot)
    border_pixel = image.pixelColor(2, 2)
    expected = QColor(*SEARCH_HIGHLIGHT_COLOR)

    assert _color_close(border_pixel, expected, tolerance=10), (
        f"Search highlight border pixel {border_pixel.name()} should "
        f"match SEARCH_HIGHLIGHT_COLOR {expected.name()}"
    )


def test_paint_search_dimmed_overlays_dark_layer(make_slot):
    """_search_dimmed=True overlays a semi-transparent dark layer."""
    fill = QColor(255, 255, 255)
    slot = make_slot(color=fill)
    slot._search_dimmed = True

    image = _render_to_image(slot)
    center = image.pixelColor(50, 50)

    assert center.red() < fill.red() or center.green() < fill.green() or center.blue() < fill.blue(), (
        f"Dimmed center pixel {center.name()} should be darker than fill "
        f"{fill.name()}. Dim overlay may not be applied."
    )


def test_paint_neither_highlight_nor_dim_leaves_center_as_fill(make_slot):
    """Without highlight/dim flags, center is the unmodified fill color."""
    fill = QColor(123, 45, 67)
    slot = make_slot(color=fill)
    slot._search_highlight = False
    slot._search_dimmed = False

    image = _render_to_image(slot)
    center = image.pixelColor(50, 50)

    assert _color_close(center, fill, tolerance=2), (
        f"Center {center.name()} should match fill {fill.name()} when "
        f"no highlight or dim is active"
    )
