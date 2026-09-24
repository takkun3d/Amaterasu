# Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Provides generic 2D and 3D vector mathematical operations."""

from __future__ import annotations
import math
import itertools


def normalize(v: list[float]) -> list[float]:
    """Returns the normalized vector.

    Args:
        v (list[float]): The input vector [x, y, z] or [x, y].

    Returns:
        list[float]: The normalized vector.
    """
    squared_sum: float = sum(component**2 for component in v)
    norm: float = math.sqrt(squared_sum)
    if norm == 0:
        return [0.0] * len(v)
    return [component / norm for component in v]


def cross_product(a: list[float], b: list[float]) -> list[float]:
    """Returns the cross product of two 3D vectors.

    Args:
        a (list[float]): The first 3D vector.
        b (list[float]): The second 3D vector.

    Returns:
        list[float]: The resulting cross product vector.
    """
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def intersect_lines(line_a: list[float], line_b: list[float]) -> list[float]:
    """Calculates the intersection point of two infinite 2D lines.

    Args:
        line_a (list[float]): Coordinates for line A [x1, y1, x2, y2].
        line_b (list[float]): Coordinates for line B [x3, y3, x4, y4].

    Returns:
        list[float]: The [x, y] coordinate of the intersection, or an empty
            list if the lines are parallel.
    """
    x1, y1, x2, y2 = line_a
    x3, y3, x4, y4 = line_b

    denom: float = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return []

    px: float = (
        (x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)
    ) / denom

    py: float = (
        (x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)
    ) / denom
    return [px, py]


def average_intersection(lines: list[list[float]]) -> list[float]:
    """Calculates the average intersection point of multiple 2D lines.

    Args:
        lines (list[list[float]]): A list of line coordinates.

    Returns:
        list[float]: The average [x, y] intersection point, or an empty list
            if valid intersections cannot be found.
    """
    if len(lines) < 2:
        return []

    intersections: list[list[float]] = []
    for line_a, line_b in itertools.combinations(lines, 2):
        point: list[float] = intersect_lines(line_a, line_b)
        if point:
            intersections.append(point)

    if not intersections:
        return []

    count: int = len(intersections)
    avg_x: float = sum(p[0] for p in intersections) / count
    avg_y: float = sum(p[1] for p in intersections) / count
    return [avg_x, avg_y]


def average_direction(lines: list[list[float]]) -> list[float]:
    """Returns the accumulated directional vector from multiple 2D lines.

    Args:
        lines (list[list[float]]): A list of line coordinates.

    Returns:
        list[float]: The accumulated [dx, dy] directional vector.
    """
    dx_sum: float = 0.0
    dy_sum: float = 0.0
    for line in lines:
        dx: float = line[2] - line[0]
        dy: float = line[3] - line[1]
        length: float = math.hypot(dx, dy)
        if length > 0:
            dx_sum += dx / length
            dy_sum += dy / length

    return [dx_sum, dy_sum]
