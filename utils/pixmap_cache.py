"""
RNV Color Palette Manager - QPixmap Cache
LRU cache for faster image/pixmap operations.

Features:
- LRU (Least Recently Used) eviction policy
- Configurable cache size
- Statistics tracking for performance monitoring
- Specialized ImagePixmapCache for color slot operations
- ThumbnailCache for preview grid thumbnails

Usage Examples:
    self.pixmap_cache = QPixmapCache(max_size=15)

    pixmap = self.pixmap_cache.get_or_create(
        cache_key=(self.image_path, zoom_level),
        creator=lambda: self._create_pixmap(zoom_level),
    )

    self.pixmap_cache.clear()
    self.pixmap_cache.print_stats()

Version: 1.0
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Callable, Any

from PyQt6.QtGui import QPixmap

from utils.logger import Logger, get_logger_instance

logger: Logger = get_logger_instance(__name__)


class QPixmapCache:
    """
    LRU (Least Recently Used) cache for QPixmap objects.

    Example:
        cache = QPixmapCache(max_size=15)
        pixmap = cache.get_or_create(
            cache_key=("image.png", 1.5, (256, 256)),
            creator=lambda: create_scaled_pixmap(1.5),
        )
    """

    def __init__(self, max_size: int = 15) -> None:
        """
        Initialize pixmap cache.

        Args:
            max_size: Maximum number of pixmaps to cache (default: 15).
        """
        self._cache: OrderedDict[tuple, QPixmap] = OrderedDict()
        self._max_size = max_size

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: tuple) -> QPixmap | None:
        """Get pixmap from cache, or None if not found."""
        if key in self._cache:
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]

        self._misses += 1
        return None

    def put(self, key: tuple, pixmap: QPixmap) -> None:
        """Add pixmap to cache with LRU eviction."""
        if key in self._cache:
            del self._cache[key]

        self._cache[key] = pixmap
        self._cache.move_to_end(key)

        while len(self._cache) > self._max_size:
            evicted_key = next(iter(self._cache))
            del self._cache[evicted_key]
            self._evictions += 1

    def get_or_create(
        self,
        cache_key: tuple,
        creator: Callable[[], QPixmap],
    ) -> QPixmap:
        """
        Get from cache or create if not found (recommended method).

        Args:
            cache_key: Cache key (tuple).
            creator: Function to create pixmap if not in cache.

        Returns:
            Cached or newly created QPixmap.
        """
        pixmap = self.get(cache_key)

        if pixmap is not None:
            return pixmap

        pixmap = creator()

        if pixmap is not None and not pixmap.isNull():
            self.put(cache_key, pixmap)

        return pixmap

    def clear(self) -> int:
        """Clear all cached pixmaps. Returns number cleared."""
        count = len(self._cache)
        self._cache.clear()
        return count

    def remove(self, key: tuple) -> bool:
        """Remove specific pixmap from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def resize(self, new_max_size: int) -> None:
        """Change cache size limit, evicting oldest if needed."""
        self._max_size = new_max_size
        while len(self._cache) > self._max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._evictions += 1

    def get_size(self) -> int:
        """Get current number of cached pixmaps."""
        return len(self._cache)

    def get_max_size(self) -> int:
        """Get maximum cache size."""
        return self._max_size

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics dictionary."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0

        return {
            'size': len(self._cache),
            'max_size': self._max_size,
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': hit_rate,
            'evictions': self._evictions,
        }

    def print_stats(self) -> None:
        """Print cache statistics via logger."""
        stats = self.get_stats()
        logger.debug("=" * 50)
        logger.debug("QPixmap Cache Statistics:")
        logger.debug(f"  Cache Size:     {stats['size']}/{stats['max_size']}")
        logger.debug(f"  Cache Hits:     {stats['hits']}")
        logger.debug(f"  Cache Misses:   {stats['misses']}")
        logger.debug(f"  Hit Rate:       {stats['hit_rate']:.1f}%")
        logger.debug(f"  Evictions:      {stats['evictions']}")
        logger.debug("=" * 50)

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get_keys(self) -> list[tuple]:
        """Get list of all cache keys (oldest first)."""
        return list(self._cache.keys())

    def contains(self, key: tuple) -> bool:
        """Check if key is in cache without affecting LRU order."""
        return key in self._cache


class ImagePixmapCache(QPixmapCache):
    """
    Specialized QPixmap cache for image display with helper methods.

    Example:
        cache = ImagePixmapCache(max_size=15)
        cache.set_current_image("/path/to/image.png")
        pixmap = cache.get_for_zoom(
            image_path, 1.5, (800, 600),
            creator=lambda: create_pixmap(1.5),
        )
    """

    def __init__(self, max_size: int = 15) -> None:
        super().__init__(max_size)
        self.current_image_path: str | None = None

    def set_current_image(self, image_path: str) -> int:
        """Set current image, clearing cache for previous image."""
        if self.current_image_path != image_path:
            cleared = self.clear()
            self.current_image_path = image_path
            return cleared
        return 0

    def get_for_zoom(
        self,
        image_path: str,
        zoom_level: float,
        image_size: tuple[int, int],
        creator: Callable[[], QPixmap],
    ) -> QPixmap:
        """Get or create pixmap for specific zoom level."""
        cache_key = (image_path, zoom_level, image_size)
        return self.get_or_create(cache_key, creator)

    def get_for_size(
        self,
        image_path: str,
        target_size: int,
        creator: Callable[[], QPixmap],
    ) -> QPixmap:
        """Get or create pixmap for specific target size."""
        cache_key = (image_path, "size", target_size)
        return self.get_or_create(cache_key, creator)

    def invalidate_image(self, image_path: str) -> int:
        """Remove all cached pixmaps for a specific image."""
        keys_to_remove = [
            key for key in self.get_keys()
            if len(key) > 0 and key[0] == image_path
        ]
        for key in keys_to_remove:
            self.remove(key)
        return len(keys_to_remove)


class ThumbnailCache(QPixmapCache):
    """
    Specialized cache for preview thumbnails.

    Optimized for the preview grid where multiple color slots
    may have image thumbnails that need caching.

    Example:
        cache = ThumbnailCache(max_size=50)
        thumb = cache.get_thumbnail(
            source_path="/path/to/image.png",
            size=64,
            creator=lambda: generate_thumbnail(64),
        )
    """

    def __init__(self, max_size: int = 50) -> None:
        super().__init__(max_size)

    def get_thumbnail(
        self,
        source_path: str,
        size: int,
        creator: Callable[[], QPixmap],
        variant: str = "default",
    ) -> QPixmap:
        """Get or create thumbnail for an image at specific size."""
        cache_key = (source_path, size, variant)
        return self.get_or_create(cache_key, creator)

    def invalidate_source(self, source_path: str) -> int:
        """Remove all cached thumbnails for a source image."""
        keys_to_remove = [
            key for key in self.get_keys()
            if len(key) > 0 and key[0] == source_path
        ]
        for key in keys_to_remove:
            self.remove(key)
        return len(keys_to_remove)


# ==================== Helper Functions ====================

def create_cache_key(
    identifier: str,
    *args,
    **kwargs,
) -> tuple:
    """
    Create standardized cache key from various parameters.

    Example:
        key = create_cache_key('/path/to/image.jpg', 1.5, (800, 600), quality='high')
    """
    key_parts = [identifier] + list(args)

    if kwargs:
        params_tuple = tuple(sorted(kwargs.items()))
        key_parts.append(params_tuple)

    return tuple(key_parts)


# ==================== Module Exports ====================

__all__: list[str] = [
    'QPixmapCache',
    'ImagePixmapCache',
    'ThumbnailCache',
    'create_cache_key',
]