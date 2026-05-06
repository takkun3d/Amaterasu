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
"""Provides a hub for spatial, matrix, and bounding-box operations in Maya.

This subpackage acts as a facade, exposing spatial utility functions
(such as bounding box evaluations, and future matrix/vector calculations)
from its internal modules for convenient access.
"""

from __future__ import annotations
from amaterasu.base.dcc.space.bounding_box import get_stacked_nodes
from amaterasu.base.dcc.space.unfreeze import (
    apply_affine_transformation,
    apply_align_to_components,
    apply_triangle_transformation,
)

__all__: list[str] = [
    # bounding_box
    "get_stacked_nodes",
    # unfreeze
    "apply_affine_transformation",
    "apply_align_to_components",
    "apply_triangle_transformation",
]
