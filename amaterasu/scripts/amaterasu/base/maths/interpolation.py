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
"""Provides standard mathematical interpolation and clamping functions."""

from __future__ import annotations


def remap(x0: float, y0: float, x1: float, y1: float, x: float) -> float:
    """Maps a value from one range to another range.

    Args:
        x0 (float): The start coordinate of the input range.
        y0 (float): The start coordinate of the output range.
        x1 (float): The end coordinate of the input range.
        y1 (float): The end coordinate of the output range.
        x (float): The current input coordinate to evaluate.

    Returns:
        float: The mapped output value.
    """
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def lerp(x: float, y: float, f: float) -> float:
    """Calculates the linear interpolation between x and y based on a factor.

    Args:
        x (float): The start value.
        y (float): The end value.
        f (float): The blend factor (0.0 to 1.0).

    Returns:
        float: The blended value.
    """
    return (x * (1.0 - f)) + (y * f)


def clamp(value: float, start_value: float, end_value: float) -> float:
    """Clamps a value securely between a start and end range.

    Args:
        value (float): The value to evaluate.
        start_value (float): One boundary of the clamping range.
        end_value (float): The other boundary of the clamping range.

    Returns:
        float: The clamped value.
    """
    min_value: float = min(start_value, end_value)
    max_value: float = max(start_value, end_value)
    return max(min(value, max_value), min_value)
