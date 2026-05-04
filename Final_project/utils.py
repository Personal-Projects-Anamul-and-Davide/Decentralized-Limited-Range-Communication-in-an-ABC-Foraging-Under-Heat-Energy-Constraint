"""
utils.py
--------
Food-cluster generation with a Gaussian intensity profile.

generate_food_clusters(width, height, num_clusters, coverage, random_gen)
  → np.ndarray shape (width, height) dtype int, values 0-100
"""

import math
import numpy as np


def generate_food_clusters(
    width: int,
    height: int,
    num_clusters: int,
    coverage: float,
    random_gen,
    min_separation: int = 8,
) -> np.ndarray:
    """
    Place `num_clusters` Gaussian-shaped food patches on the grid.

    Parameters
    ----------
    width, height    : grid dimensions
    num_clusters     : number of independent food patches
    coverage         : fraction of total cells that contain food (0–1)
    random_gen       : Mesa random generator (has .random(), .randint())
    min_separation   : minimum Chebyshev distance between cluster centres

    Returns
    -------
    np.ndarray (width, height) int, values 0–100
    """
    food_grid = np.zeros((width, height), dtype=int)
    total_food_cells = int(width * height * coverage)
    # Cluster radius scales so all clusters together cover ~coverage fraction
    radius = max(3, int(math.sqrt(total_food_cells / (num_clusters * math.pi))))

    centres: list[tuple[int, int]] = []

    for _ in range(num_clusters):
        # Try to honour minimum separation between centres
        placed = False
        for _attempt in range(60):
            cx = random_gen.randint(radius, width  - 1 - radius)
            cy = random_gen.randint(radius, height - 1 - radius)
            if all(
                max(abs(cx - ox), abs(cy - oy)) >= min_separation
                for ox, oy in centres
            ):
                centres.append((cx, cy))
                placed = True
                break
        if not placed:                           # fallback – no separation guarantee
            cx = random_gen.randint(0, width  - 1)
            cy = random_gen.randint(0, height - 1)
            centres.append((cx, cy))

        # Gaussian intensity profile
        sigma2 = float(radius ** 2)
        scan   = radius * 2 + 1
        for dx in range(-scan, scan + 1):
            for dy in range(-scan, scan + 1):
                nx, ny = cx + dx, cy + dy
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                dist2     = float(dx * dx + dy * dy)
                intensity = math.exp(-dist2 / (2.0 * sigma2))
                if intensity > 0.05:
                    base   = int(intensity * 80)
                    jitter = random_gen.randint(-10, 10)
                    val    = max(0, min(100, base + jitter))
                    # Keep the maximum so overlapping clusters stay rich
                    if val > food_grid[nx][ny]:
                        food_grid[nx][ny] = val

    return food_grid
