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
"""Provides predefined NURBS curve shapes and data structures.

This module contains the `CurveData` type definition and various coordinate
presets used to generate controller shapes (e.g., ROOT, CAMERA, GRID).
"""

from __future__ import annotations

from typing import TypedDict


class CurveData(TypedDict, total=False):
    """Data structure defining the properties of a single NURBS curve.

    Attributes:
        degree (int): The degree of the NURBS curve (e.g., 1 for linear, 3 for cubic).
        points (list[list[float]]): A list of XYZ coordinates for the control vertices.
        knots (list[int] | None, optional): The knot vector array.
            If None, it will be automatically generated.
        periodic (bool, optional): True if the curve should be closed (periodic),
            False if open.
    """

    degree: int
    points: list[list[float]]
    knots: list[int] | None
    periodic: bool


ROOT: list[CurveData] = [
    {
        "degree": 1,
        "periodic": True,
        "points": [
            [0, 0, -10],
            [1.561, 0, -7.846],
            [3.061, 0, -7.391],
            [4.445, 0, -6.652],
            [5.657, 0, -5.657],
            [6.652, 0, -4.445],
            [7.391, 0, -3.061],
            [7.846, 0, -1.561],
            [8, 0, 0],
            [7.846, 0, 1.561],
            [7.391, 0, 3.061],
            [6.652, 0, 4.445],
            [5.657, 0, 5.657],
            [4.445, 0, 6.652],
            [3.061, 0, 7.391],
            [1.561, 0, 7.846],
            [0, 0, 8],
            [-1.561, 0, 7.846],
            [-3.061, 0, 7.391],
            [-4.445, 0, 6.652],
            [-5.657, 0, 5.657],
            [-6.652, 0, 4.445],
            [-7.391, 0, 3.061],
            [-7.846, 0, 1.561],
            [-8, 0, 0],
            [-7.846, 0, -1.561],
            [-7.391, 0, -3.061],
            [-6.652, 0, -4.445],
            [-5.657, 0, -5.657],
            [-4.445, 0, -6.652],
            [-3.061, 0, -7.391],
            [-1.561, 0, -7.846],
            [0, 0, -10],
        ],
    }
]
LOCAL: list[CurveData] = [
    {
        "degree": 1,
        "periodic": True,
        "points": [
            [3.5, 0, -7],
            [3.5, 0, -3.5],
            [7, 0, -3.5],
            [7, 0, 3.5],
            [3.5, 0, 3.5],
            [3.5, 0, 7],
            [-3.5, 0, 7],
            [-3.5, 0, 3.5],
            [-7, 0, 3.5],
            [-7, 0, -3.5],
            [-3.5, 0, -3.5],
            [-3.5, 0, -7],
            [3.5, 0, -7],
        ],
    }
]
BODY: list[CurveData] = [
    {
        "degree": 1,
        "periodic": True,
        "points": [
            [0, 0, -6.5],
            [1.95, 0, -3.25],
            [0.975, 0, -3.25],
            [0.975, 0, -0.975],
            [3.25, 0, -0.975],
            [3.25, 0, -1.95],
            [6.5, 0, 0],
            [3.25, 0, 1.95],
            [3.25, 0, 0.975],
            [0.975, 0, 0.975],
            [0.975, 0, 3.25],
            [1.95, 0, 3.25],
            [0, 0, 6.5],
            [-1.95, 0, 3.25],
            [-0.975, 0, 3.25],
            [-0.975, 0, 0.975],
            [-3.25, 0, 0.975],
            [-3.25, 0, 1.95],
            [-6.5, 0, 0],
            [-3.25, 0, -1.95],
            [-3.25, 0, -0.975],
            [-0.975, 0, -0.975],
            [-0.975, 0, -3.25],
            [-1.95, 0, -3.25],
            [0, 0, -6.5],
        ],
    }
]
CAMERA: list[CurveData] = [
    {
        "degree": 1,
        "periodic": False,
        "points": [
            [0, -2.247, -2.973],
            [0.438, -2.204, -2.973],
            [0.86, -2.076, -2.973],
            [1.249, -1.869, -2.973],
            [1.589, -1.589, -2.973],
            [1.869, -1.249, -2.973],
            [2.076, -0.86, -2.973],
            [2.204, -0.438, -2.973],
            [2.247, 0, -2.973],
            [2.204, 0.438, -2.973],
            [2.076, 0.86, -2.973],
            [1.869, 1.249, -2.973],
            [1.589, 1.589, -2.973],
            [1.249, 1.869, -2.973],
            [0.86, 2.076, -2.973],
            [0.438, 2.204, -2.973],
            [0, 2.247, -2.973],
            [-0.438, 2.204, -2.973],
            [-0.86, 2.076, -2.973],
            [-1.249, 1.869, -2.973],
            [-1.589, 1.589, -2.973],
            [-1.869, 1.249, -2.973],
            [-2.076, 0.86, -2.973],
            [-2.204, 0.438, -2.973],
            [-2.247, 0, -2.973],
            [-2.204, -0.438, -2.973],
            [-2.076, -0.86, -2.973],
            [-1.869, -1.249, -2.973],
            [-1.589, -1.589, -2.973],
            [-1.249, -1.869, -2.973],
            [-0.86, -2.076, -2.973],
            [-0.438, -2.204, -2.973],
            [0, -2.247, -2.973],
            [0, -2.247, 0],
            [0.438, -2.204, 0],
            [0.86, -2.076, 0],
            [1.249, -1.869, 0],
            [1.589, -1.589, 0],
            [1.869, -1.249, 0],
            [2.076, -0.86, 0],
            [2.204, -0.438, 0],
            [2.247, 0, 0],
            [2.247, 0, -2.973],
            [2.247, 0, 0],
            [2.204, 0.438, 0],
            [2.076, 0.86, 0],
            [1.869, 1.249, 0],
            [1.589, 1.589, 0],
            [1.249, 1.869, 0],
            [0.86, 2.076, 0],
            [0.438, 2.204, 0],
            [0, 2.247, 0],
            [0, 2.247, -2.973],
            [0, 2.247, 0],
            [-0.438, 2.204, 0],
            [-0.86, 2.076, 0],
            [-1.249, 1.869, 0],
            [-1.589, 1.589, 0],
            [-1.869, 1.249, 0],
            [-2.076, 0.86, 0],
            [-2.204, 0.438, 0],
            [-2.247, 0, 0],
            [-2.247, 0, -2.973],
            [-2.247, 0, 0],
            [-2.204, -0.438, 0],
            [-2.076, -0.86, 0],
            [-1.869, -1.249, 0],
            [-1.589, -1.589, 0],
            [-1.249, -1.869, 0],
            [-0.86, -2.076, 0],
            [-0.438, -2.204, 0],
            [0, -2.247, 0],
        ],
    },
    {
        "degree": 1,
        "periodic": False,
        "points": [
            [2.138, 5, 12.763],
            [-2.138, 5, 12.763],
            [-2.138, 5, 0],
            [2.138, 5, 0],
            [2.138, 5, 12.763],
            [2.138, -3.403, 12.763],
            [2.138, -3.403, 0],
            [2.138, 5, 0],
            [2.138, -3.403, 0],
            [-2.138, -3.403, 0],
            [-2.138, 5, 0],
            [-2.138, -3.403, 0],
            [-2.138, -3.403, 12.763],
            [-2.138, 5, 12.763],
            [-2.138, -3.403, 12.763],
            [2.138, -3.403, 12.763],
        ],
    },
]
FILM_OFFSET: list[CurveData] = [
    {
        "degree": 3,
        "periodic": True,
        "points": [
            [0.024, 0.024, 0],
            [0, 0.033, 0],
            [-0.024, 0.024, 0],
            [-0.033, 0, 0],
            [-0.024, -0.024, 0],
            [0, -0.033, 0],
            [0.024, -0.024, 0],
            [0.033, 0, 0],
            [0.024, 0.024, 0],
            [0, 0.033, 0],
            [-0.024, 0.024, 0],
        ],
    }
]
AIM_TARGET: list[CurveData] = [
    {
        "degree": 1,
        "periodic": False,
        "points": [[2, 0, 0], [-2, 0, 0]],
    },
    {
        "degree": 1,
        "periodic": False,
        "points": [[0, 2, 0], [0, -2, 0]],
    },
    {
        "degree": 1,
        "periodic": False,
        "points": [[0, 0, 2], [0, 0, -2]],
    },
]
CLIP_PLANE: list[CurveData] = [
    {
        "degree": 1,
        "periodic": True,
        "points": [
            [0.5, 0.5, 0],
            [0.5, -0.5, 0],
            [-0.5, -0.5, 0],
            [-0.5, 0.5, 0],
            [0.5, 0.5, 0],
        ],
    }
]
SETTING: list[CurveData] = [
    {
        "degree": 1,
        "periodic": True,
        "points": [
            [-0.14, 1, 0],
            [0.14, 1, 0],
            [0.174, 0.8, 0],
            [0.312, 0.754, 0],
            [0.443, 0.689, 0],
            [0.608, 0.806, 0],
            [0.806, 0.608, 0],
            [0.689, 0.443, 0],
            [0.754, 0.312, 0],
            [0.8, 0.174, 0],
            [1, 0.14, 0],
            [1, -0.14, 0],
            [0.8, -0.174, 0],
            [0.754, -0.312, 0],
            [0.689, -0.443, 0],
            [0.806, -0.608, 0],
            [0.608, -0.806, 0],
            [0.443, -0.689, 0],
            [0.312, -0.754, 0],
            [0.174, -0.8, 0],
            [0.14, -1, 0],
            [-0.14, -1, 0],
            [-0.174, -0.8, 0],
            [-0.312, -0.754, 0],
            [-0.443, -0.689, 0],
            [-0.608, -0.806, 0],
            [-0.806, -0.608, 0],
            [-0.689, -0.443, 0],
            [-0.754, -0.312, 0],
            [-0.8, -0.174, 0],
            [-1, -0.14, 0],
            [-1, 0.14, 0],
            [-0.8, 0.174, 0],
            [-0.754, 0.312, 0],
            [-0.689, 0.443, 0],
            [-0.806, 0.608, 0],
            [-0.608, 0.806, 0],
            [-0.443, 0.689, 0],
            [-0.312, 0.754, 0],
            [-0.174, 0.8, 0],
            [-0.14, 1, 0],
        ],
    },
    {
        "degree": 1,
        "periodic": True,
        "points": [
            [0, 0.306, 0],
            [0.06, 0.3, 0],
            [0.117, 0.283, 0],
            [0.17, 0.254, 0],
            [0.216, 0.216, 0],
            [0.254, 0.17, 0],
            [0.283, 0.117, 0],
            [0.3, 0.06, 0],
            [0.306, 0, 0],
            [0.3, -0.06, 0],
            [0.283, -0.117, 0],
            [0.254, -0.17, 0],
            [0.216, -0.216, 0],
            [0.17, -0.254, 0],
            [0.117, -0.283, 0],
            [0.06, -0.3, 0],
            [0, -0.306, 0],
            [-0.06, -0.3, 0],
            [-0.117, -0.283, 0],
            [-0.17, -0.254, 0],
            [-0.216, -0.216, 0],
            [-0.254, -0.17, 0],
            [-0.283, -0.117, 0],
            [-0.3, -0.06, 0],
            [-0.306, 0, 0],
            [-0.3, 0.06, 0],
            [-0.283, 0.117, 0],
            [-0.254, 0.17, 0],
            [-0.216, 0.216, 0],
            [-0.17, 0.254, 0],
            [-0.117, 0.283, 0],
            [-0.06, 0.3, 0],
            [0, 0.306, 0],
        ],
    },
]
GRID: list[CurveData] = [
    {
        "degree": 1,
        "periodic": False,
        "points": [
            [-0.5, 0.5, 0],
            [0.5, 0.5, 0],
            [0.5, -0.5, 0],
            [-0.5, -0.5, 0],
            [-0.5, 0.5, 0],
            [-0.1666666567325592, 0.5, 0],
            [-0.1666666567325592, -0.5, 0],
            [0.1666666716337204, -0.5, 0],
            [0.16666668653488159, 0.5, 0],
            [0.5, 0.5, 0],
            [0.5, 0.16666667163372034, 0],
            [-0.5, 0.16666668653488159, 0],
            [-0.5, -0.1666666567325592, 0],
            [0.5, -0.1666666567325592, 0],
        ],
    }
]
FRUSTUM: list[CurveData] = [
    {
        "degree": 1,
        "periodic": False,
        "points": [[0, 0, 0], [0, 0, 0]],
    },
    {
        "degree": 1,
        "periodic": False,
        "points": [[0, 0, 0], [0, 0, 0]],
    },
    {
        "degree": 1,
        "periodic": False,
        "points": [[0, 0, 0], [0, 0, 0]],
    },
    {
        "degree": 1,
        "periodic": False,
        "points": [[0, 0, 0], [0, 0, 0]],
    },
]
FILM_AREA: list[CurveData] = [
    {
        "degree": 1,
        "periodic": True,
        "points": [[3, 3, 0], [3, -3, 0], [-3, -3, 0], [-3, 3, 0], [3, 3, 0]],
    }
]
