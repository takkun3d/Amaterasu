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
"""Mathematical modules and interpolation functions for animation processing."""

from amaterasu.base.maths.ease import (
    Ease,
    EaseCubic,
    EaseExponential,
    EaseQuadratic,
)
from amaterasu.base.maths.interpolation import (
    remap,
    lerp,
    clamp,
)
from amaterasu.base.maths.vector import (
    normalize,
    cross_product,
    intersect_lines,
    average_intersection,
    average_direction,
)

__all__: list[str] = [
    # ease
    "Ease",
    "EaseCubic",
    "EaseExponential",
    "EaseQuadratic",
    # interpolation
    "remap",
    "lerp",
    "clamp",
    # vector
    "normalize",
    "cross_product",
    "intersect_lines",
    "average_intersection",
    "average_direction",
]
