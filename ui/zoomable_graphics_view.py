"""
Zoomable and pannable graphics view for color slots.
Optimized for Python 3.13.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QGraphicsProxyWidget
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainter


class ZoomableGraphicsView(QGraphicsView):
    """Graphics view with zoom and pan capabilities"""
    
    def __init__(self, widget: QWidget, parent: QWidget | None = None) -> None:
        self.scene = QGraphicsScene()
        self.proxy: QGraphicsProxyWidget = self.scene.addWidget(widget)
        super().__init__(self.scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.scale_factor: float = 1.0
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.update_scene_rect()

    def update_scene_rect(self) -> None:
        """Update scene rectangle based on widget size.
        Expands width to at least the viewport width so AlignHCenter
        on the grid layout has room to center the content.
        """
        if self.proxy and self.proxy.widget():
            content_widget = self.proxy.widget()
            content_rect = QRectF(content_widget.rect())
            vp_width = self.viewport().width()
            scene_width = max(content_rect.width(), vp_width)
            rect = QRectF(0, 0, scene_width, content_rect.height())
            self.scene.setSceneRect(rect)
            # Keep proxy centered horizontally in the expanded scene
            proxy_x = (scene_width - content_rect.width()) / 2
            self.proxy.setPos(proxy_x, 0)

    def wheelEvent(self, event) -> None:
        """Handle mouse wheel for zooming"""
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        zoom_factor = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor
        
        mouse_view_pos = event.position().toPoint()
        old_scene_pos = self.mapToScene(mouse_view_pos)
        
        self.scale(zoom_factor, zoom_factor)
        self.scale_factor *= zoom_factor
        
        new_scene_pos = self.mapToScene(mouse_view_pos)
        delta = new_scene_pos - old_scene_pos
        self.translate(delta.x(), delta.y())
        
        event.accept()

    def reset_view(self) -> None:
        """Reset zoom and pan to default.
        Resets transform and scrolls to top-left (0,0) of the scene.
        AlignHCenter on the grid layout centers the content within the
        scroll_content widget, so the grid appears centered at origin.
        """
        self.resetTransform()
        self.scale_factor = 1.0
        self.update_scene_rect()
        self.horizontalScrollBar().setValue(0)
        self.verticalScrollBar().setValue(0)