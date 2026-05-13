"""
Color extraction from images using k-means clustering.
Lightweight implementation without sklearn dependency.
Optimized for Python 3.13.
"""
from __future__ import annotations

import random
import math
from collections import defaultdict

from PIL import Image

from utils.logger import Logger, get_logger_instance

logger: Logger = get_logger_instance(__name__)

# Type aliases
type RGB = tuple[int, int, int]


class ColorExtractor:
    """Extract dominant colors from images using k-means clustering."""

    # Maximum image dimension for sampling (resize larger images)
    MAX_SAMPLE_SIZE: int = 150
    # Maximum iterations for k-means convergence
    MAX_ITERATIONS: int = 20
    # Convergence threshold (centroid movement < this = done)
    CONVERGENCE_THRESHOLD: float = 2.0

    @staticmethod
    def extract_palette(
        image: Image.Image,
        num_colors: int = 5,
        quality: int = 1,
    ) -> list[RGB]:
        """
        Extract dominant colors from a PIL Image.

        Args:
            image: PIL Image (will be converted to RGB).
            num_colors: Number of dominant colors to extract (3-10).
            quality: Sampling quality (1=best, 10=fastest).
                     Higher values skip more pixels.

        Returns:
            List of RGB tuples sorted by dominance (most dominant first).
        """
        num_colors = max(2, min(12, num_colors))
        quality = max(1, min(10, quality))

        logger.info(f"Extracting {num_colors} colors (quality={quality})...")

        # Prepare pixel data
        pixels = ColorExtractor._sample_pixels(image, quality)
        if len(pixels) < num_colors:
            logger.warning(f"Only {len(pixels)} pixels sampled, returning as-is")
            return pixels[:num_colors]

        # Run k-means
        centroids, assignments = ColorExtractor._kmeans(pixels, num_colors)

        # Sort by cluster size (most dominant first)
        cluster_sizes: dict[int, int] = defaultdict(int)
        for assignment in assignments:
            cluster_sizes[assignment] += 1

        sorted_indices = sorted(
            range(len(centroids)),
            key=lambda i: cluster_sizes.get(i, 0),
            reverse=True,
        )

        result = [centroids[i] for i in sorted_indices]
        logger.success(f"Extracted {len(result)} colors")
        return result

    @staticmethod
    def _sample_pixels(image: Image.Image, quality: int) -> list[RGB]:
        """
        Sample pixels from an image, resizing if necessary.

        Filters out near-white and near-black pixels to get
        more meaningful palette colors.
        """
        img = image.convert("RGB")

        # Resize for performance
        max_dim = ColorExtractor.MAX_SAMPLE_SIZE
        if img.width > max_dim or img.height > max_dim:
            ratio = min(max_dim / img.width, max_dim / img.height)
            new_size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        raw_pixels = list(img.getdata())

        # Sample with quality step
        pixels: list[RGB] = []
        for i in range(0, len(raw_pixels), quality):
            r, g, b = raw_pixels[i]
            # Filter near-white and near-black
            if r > 245 and g > 245 and b > 245:
                continue
            if r < 10 and g < 10 and b < 10:
                continue
            pixels.append((r, g, b))

        # If filtering removed too many, fall back to unfiltered
        if len(pixels) < 10:
            pixels = [raw_pixels[i] for i in range(0, len(raw_pixels), quality)]

        logger.debug(f"Sampled {len(pixels)} pixels from {len(raw_pixels)} total")
        return pixels

    @staticmethod
    def _kmeans(
        pixels: list[RGB],
        k: int,
    ) -> tuple[list[RGB], list[int]]:
        """
        K-means clustering on RGB pixel data.

        Uses k-means++ initialization for better starting centroids.

        Args:
            pixels: List of RGB tuples.
            k: Number of clusters.

        Returns:
            Tuple of (centroids, assignments).
        """
        n = len(pixels)

        # K-means++ initialization
        centroids = ColorExtractor._kmeans_pp_init(pixels, k)

        assignments = [0] * n

        for iteration in range(ColorExtractor.MAX_ITERATIONS):
            # Assignment step: assign each pixel to nearest centroid
            new_assignments = []
            for pixel in pixels:
                min_dist = float("inf")
                best = 0
                for ci, centroid in enumerate(centroids):
                    dist = ColorExtractor._color_dist_sq(pixel, centroid)
                    if dist < min_dist:
                        min_dist = dist
                        best = ci
                new_assignments.append(best)

            # Update step: recompute centroids
            sums: dict[int, list[int]] = {}
            counts: dict[int, int] = {}
            for ci in range(k):
                sums[ci] = [0, 0, 0]
                counts[ci] = 0

            for pi, ci in enumerate(new_assignments):
                px = pixels[pi]
                sums[ci][0] += px[0]
                sums[ci][1] += px[1]
                sums[ci][2] += px[2]
                counts[ci] += 1

            new_centroids: list[RGB] = []
            max_movement = 0.0
            for ci in range(k):
                if counts[ci] > 0:
                    new_c: RGB = (
                        sums[ci][0] // counts[ci],
                        sums[ci][1] // counts[ci],
                        sums[ci][2] // counts[ci],
                    )
                else:
                    # Empty cluster: reinitialize to random pixel
                    new_c = random.choice(pixels)

                movement = math.sqrt(
                    ColorExtractor._color_dist_sq(centroids[ci], new_c)
                )
                max_movement = max(max_movement, movement)
                new_centroids.append(new_c)

            centroids = new_centroids
            assignments = new_assignments

            # Check convergence
            if max_movement < ColorExtractor.CONVERGENCE_THRESHOLD:
                logger.debug(f"K-means converged at iteration {iteration + 1}")
                break

        return centroids, assignments

    @staticmethod
    def _kmeans_pp_init(pixels: list[RGB], k: int) -> list[RGB]:
        """
        K-means++ initialization: pick starting centroids that are
        spread apart for better convergence.
        """
        centroids: list[RGB] = [random.choice(pixels)]

        for _ in range(1, k):
            # Compute distance from each pixel to nearest centroid
            distances: list[float] = []
            for pixel in pixels:
                min_d = min(
                    ColorExtractor._color_dist_sq(pixel, c) for c in centroids
                )
                distances.append(min_d)

            # Weighted random selection (proportional to distance^2)
            total = sum(distances)
            if total == 0:
                centroids.append(random.choice(pixels))
                continue

            threshold = random.random() * total
            cumulative = 0.0
            for pi, d in enumerate(distances):
                cumulative += d
                if cumulative >= threshold:
                    centroids.append(pixels[pi])
                    break
            else:
                centroids.append(random.choice(pixels))

        return centroids

    @staticmethod
    def _color_dist_sq(c1: RGB, c2: RGB) -> float:
        """Squared Euclidean distance between two RGB colors."""
        return float(
            (c1[0] - c2[0]) ** 2
            + (c1[1] - c2[1]) ** 2
            + (c1[2] - c2[2]) ** 2
        )
