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
"""Provides a hub for polygon mesh and component operations in Maya.

This subpackage acts as a facade, exposing component conversion utilities
and edge/face/vertex evaluations from its internal modules for convenient access.
"""

from __future__ import annotations
from amaterasu.base.dcc.mesh.component import (
    to_vertex,
    to_edge,
    to_contained_edge,
    to_face,
    to_uv,
    to_border_uv,
    to_uv_border_edges,
    group_by_node,
    get_index,
)
from amaterasu.base.dcc.mesh.edge import (
    get_crease_edges,
    get_hard_edges,
    get_nth_edges,
    edge_length_2d,
    edge_length_3d,
)
from amaterasu.base.dcc.mesh.face import (
    get_hard_edge_shells,
    duplicate_faces,
    extract_faces,
)
from amaterasu.base.dcc.mesh.uv import get_inverted_uv_faces
from amaterasu.base.dcc.mesh.material import get_shading_groups
from amaterasu.base.dcc.mesh.node import get_polygon_transforms

__all__: list[str] = [
    # component
    "to_vertex",
    "to_edge",
    "to_contained_edge",
    "to_face",
    "to_uv",
    "to_border_uv",
    "to_uv_border_edges",
    "group_by_node",
    "get_index",
    # edge
    "get_crease_edges",
    "get_hard_edges",
    "get_nth_edges",
    "edge_length_2d",
    "edge_length_3d",
    # facce
    "get_hard_edge_shells",
    "duplicate_faces",
    "extract_faces",
    # uv
    "get_inverted_uv_faces",
    # material
    "get_shading_groups",
    # node
    "get_polygon_transforms",
]
