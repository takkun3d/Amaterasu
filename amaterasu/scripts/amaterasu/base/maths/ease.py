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
"""Provides easing mathematical functions for animation interpolation.

Reference:
    http://nakamura001.hatenablog.com/entry/20111117/1321539246
"""

from __future__ import annotations


class Ease:
    """Base class for ease interpolations."""

    @staticmethod
    def ease_in(t: float, b: float, c: float, d: float) -> float:
        """Returns the ease-in interpolated value.

        Args:
            t (float): The current time.
            b (float): The start value.
            c (float): The difference between start and end values.
            d (float): The total duration.

        Returns:
            float: The interpolated value.
        """
        return 0.0

    @staticmethod
    def ease_out(t: float, b: float, c: float, d: float) -> float:
        """Returns the ease-out interpolated value.

        Args:
            t (float): The current time.
            b (float): The start value.
            c (float): The difference between start and end values.
            d (float): The total duration.

        Returns:
            float: The interpolated value.
        """
        return 0.0

    @staticmethod
    def ease_in_out(t: float, b: float, c: float, d: float) -> float:
        """Returns the ease-in-out interpolated value.

        Args:
            t (float): The current time.
            b (float): The start value.
            c (float): The difference between start and end values.
            d (float): The total duration.

        Returns:
            float: The interpolated value.
        """
        return 0.0


class EaseQuadratic(Ease):
    """Quadratic easing implementation."""

    @staticmethod
    def ease_in(t: float, b: float, c: float, d: float) -> float:
        """Returns the quadratic ease-in interpolated value.

        Args:
            t (float): The current time.
            b (float): The start value.
            c (float): The difference between start and end values.
            d (float): The total duration.

        Returns:
            float: The interpolated value.
        """
        t /= d
        return c * t * t + b

    @staticmethod
    def ease_out(t: float, b: float, c: float, d: float) -> float:
        """Returns the quadratic ease-out interpolated value.

        Args:
            t (float): The current time.
            b (float): The start value.
            c (float): The difference between start and end values.
            d (float): The total duration.

        Returns:
            float: The interpolated value.
        """
        t /= d
        return -c * t * (t - 2.0) + b

    @staticmethod
    def ease_in_out(t: float, b: float, c: float, d: float) -> float:
        """Returns the quadratic ease-in-out interpolated value.

        Args:
            t (float): The current time.
            b (float): The start value.
            c (float): The difference between start and end values.
            d (float): The total duration.

        Returns:
            float: The interpolated value.
        """
        t /= d / 2.0
        if t < 1:
            return c / 2.0 * t * t + b
        t = t - 1
        return -c / 2.0 * (t * (t - 2) - 1) + b


class EaseCubic(Ease):
    """Cubic easing implementation."""

    @staticmethod
    def ease_in(t: float, b: float, c: float, d: float) -> float:
        """Returns the cubic ease-in interpolated value.

        Args:
            t (float): The current time.
            b (float): The start value.
            c (float): The difference between start and end values.
            d (float): The total duration.

        Returns:
            float: The interpolated value.
        """
        t /= d
        return c * t * t * t + b

    @staticmethod
    def ease_out(t: float, b: float, c: float, d: float) -> float:
        """Returns the cubic ease-out interpolated value.

        Args:
            t (float): The current time.
            b (float): The start value.
            c (float): The difference between start and end values.
            d (float): The total duration.

        Returns:
            float: The interpolated value.
        """
        t /= d
        t = t - 1
        return c * (t * t * t + 1) + b

    @staticmethod
    def ease_in_out(t: float, b: float, c: float, d: float) -> float:
        """Returns the cubic ease-in-out interpolated value.

        Args:
            t (float): The current time.
            b (float): The start value.
            c (float): The difference between start and end values.
            d (float): The total duration.

        Returns:
            float: The interpolated value.
        """
        t /= d / 2.0
        if t < 1:
            return c / 2.0 * t * t * t + b
        t = t - 2
        return c / 2.0 * (t * t * t + 2) + b


class EaseExponential(Ease):
    """Exponential easing implementation."""

    @staticmethod
    def ease_in(t: float, b: float, c: float, d: float) -> float:
        """Returns the exponential ease-in interpolated value.

        Args:
            t (float): The current time.
            b (float): The start value.
            c (float): The difference between start and end values.
            d (float): The total duration.

        Returns:
            float: The interpolated value.
        """
        return c * 2 ** (10 * (t / d - 1)) + b

    @staticmethod
    def ease_out(t: float, b: float, c: float, d: float) -> float:
        """Returns the exponential ease-out interpolated value.

        Args:
            t (float): The current time.
            b (float): The start value.
            c (float): The difference between start and end values.
            d (float): The total duration.

        Returns:
            float: The interpolated value.
        """
        return float(c * (-(2.0 ** (-10.0 * t / d)) + 1.0) + b)

    @staticmethod
    def ease_in_out(t: float, b: float, c: float, d: float) -> float:
        """Returns the exponential ease-in-out interpolated value.

        Args:
            t (float): The current time.
            b (float): The start value.
            c (float): The difference between start and end values.
            d (float): The total duration.

        Returns:
            float: The interpolated value.
        """
        t /= d / 2.0
        if t < 1:
            return float(c / 2.0 * 2.0 ** (10.0 * (t - 1.0)) + b)

        t = t - 1
        return float(c / 2.0 * (-(2.0 ** (-10.0 * t)) + 2.0) + b)
