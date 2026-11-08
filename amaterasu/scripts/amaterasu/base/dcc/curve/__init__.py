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
"""Provides utilities and presets for generating NURBS curves in Maya.

This package contains data structures, predefined curve presets, and functions
to create complex NURBS curve shapes used for rigging and UI elements.
"""

from amaterasu.base.dcc.curve.create import create_curve, create_spherical_grid
from amaterasu.base.dcc.curve.preset import (
    AIM_TARGET,
    BODY,
    CAMERA,
    CLIP_PLANE,
    FILM_AREA,
    FILM_OFFSET,
    FRUSTUM,
    GRID,
    LOCAL,
    ROOT,
    SETTING,
    CurveData,
)

__all__: list[str] = [
    # preset
    "AIM_TARGET",
    "BODY",
    "CAMERA",
    "CLIP_PLANE",
    "FILM_AREA",
    "FILM_OFFSET",
    "FRUSTUM",
    "GRID",
    "LOCAL",
    "ROOT",
    "SETTING",
    "CurveData",
    # create
    "create_curve",
    "create_spherical_grid",
]
