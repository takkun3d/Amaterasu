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
"""Flattens selected polygon faces onto a shared plane."""

from __future__ import annotations
from maya import cmds
from amaterasu.base import dcc, utils

__product__: str = "Flatten Faces"
__version__: str = "1.10"
_logger: utils.Logger = utils.get_logger(__product__)


def flatten(faces: list[str]) -> None:
    """Flatten the selected polygon faces onto a shared plane.

    Calculates the average normal of the selected faces and aligns the
    associated vertices to a plane defined by the averaged vertex positions
    and the averaged face normal vector.

    Args:
        faces: A list of strings representing the names of the selected
            polygon faces (e.g., ["pCube1.f[0]", "pCube1.f[1]"]).

    Returns:
        None
    """
    faces_each_geo: dict[str, list[str]] = dcc.mesh.group_by_node(faces)
    for _node, node_faces in faces_each_geo.items():
        vertices: list[str] = dcc.mesh.to_vertex(node_faces)
        positions: list[list[float]] = [
            cmds.pointPosition(v, local=True) for v in vertices
        ]
        num_verts: int = len(positions)

        center_pivot: list[float] = [
            sum(p[0] for p in positions) / num_verts,
            sum(p[1] for p in positions) / num_verts,
            sum(p[2] for p in positions) / num_verts,
        ]

        avg_normal: list[float] = get_average_normal(node_faces)

        # Plane equation: ax + by + cz = d
        d: float = sum(n * c for n, c in zip(avg_normal, center_pivot))
        for vertex, pos in zip(vertices, positions):
            new_pos: list[float] = project_to_plane(pos, avg_normal, d)
            cmds.move(*new_pos, vertex, absolute=True, objectSpace=True)  # type: ignore


def get_average_normal(faces: list[str]) -> list[float]:
    """Calculate the average normal vector of the provided faces."""
    normals: list[list[float]] = [dcc.mesh.face_normals(f) for f in faces]
    count: int = len(normals)
    return [sum(n[i] for n in normals) / count for i in range(3)]


def project_to_plane(
    point: list[float], normal: list[float], d: float
) -> list[float]:
    """Project a point onto a plane defined by a normal and distance d."""
    # dist = (normal dot point) - d
    dist: float = sum(n * p for n, p in zip(normal, point)) - d
    mag_sq: float = sum(n**2 for n in normal)
    if mag_sq == 0:
        return point

    return [p - (dist / mag_sq) * n for p, n in zip(point, normal)]


def main() -> None:
    """Execute the flatten faces operation based on user selection."""
    selection: list[str] = cmds.filterExpand(selectionMask=34) or []
    if not selection:
        _logger.error("No polygon faces selected.")
        return

    flatten(selection)
    _logger.info("Done.")
