# ==============================================================================
#
# Unfreeze transformations
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import math

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

from maya import cmds
from maya.api import OpenMaya
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Unfreeze transformations'
__version__: str = '1.20'
__doc__ = 'Restores transformations of a frozen model using a reference object.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')


class MainWindow(widgets.ToolWidget):
    '''Tool main window'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
        unique_id: str = '',
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

        option_widget: QWidget = self.option_widget()
        main_layout: QVBoxLayout = QVBoxLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ----------------------------------------------------------------------
        # Affine Transformation
        frame: widgets.FrameWidget = widgets.FrameWidget(
            'Unfreeze Solid Transformation',
            False,
            False,
            self,
        )
        main_layout.addWidget(frame)

        layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.addLayout(layout)

        form_layout: widgets.FormLayout = widgets.FormLayout(self)
        form_layout.setFieldGrowthPolicy(
            widgets.FormLayout.AllNonFixedFieldsGrow
        )
        layout.addLayout(form_layout)

        self.__affine_src: widgets.NodePicker = widgets.NodePicker(1, self)
        form_layout.addRow(widgets.FormLabel('Source'), self.__affine_src)

        self.__affine_dsts: widgets.NodePicker = widgets.NodePicker(-1, self)
        form_layout.addRow(
            widgets.FormLabel('Destinations'), self.__affine_dsts
        )

        form_layout.addRow(
            '',
            QLabel(
                '<strong>*Requires non-planar polygon geometry.</strong>', self
            ),
        )

        button: QPushButton = QPushButton('Apply', self)
        button.clicked.connect(self.affine_transformation)
        form_layout.addRow('', button)

        main_layout.addWidget(widgets.HorizontalLine(self))

        # ----------------------------------------------------------------------
        # Triangle Transformation
        frame = widgets.FrameWidget(
            'Unfreeze Planar Transformation',
            False,
            False,
            self,
        )
        main_layout.addWidget(frame)

        layout = QVBoxLayout(self)
        main_layout.addLayout(layout)

        form_layout = widgets.FormLayout(self)
        form_layout.setFieldGrowthPolicy(
            widgets.FormLayout.AllNonFixedFieldsGrow
        )
        layout.addLayout(form_layout)

        self.__planar_src: widgets.NodePicker = widgets.NodePicker(1, self)
        form_layout.addRow(widgets.FormLabel('Source'), self.__planar_src)

        self.__planar_dsts: widgets.NodePicker = widgets.NodePicker(-1, self)
        form_layout.addRow(
            widgets.FormLabel('Destinations'), self.__planar_dsts
        )

        form_layout.addRow(
            '', QLabel('<strong>*Requires polygon geometry.</strong>', self)
        )

        button = QPushButton('Apply', self)
        button.clicked.connect(self.triangle_transformation)
        form_layout.addRow('', button)

        main_layout.addWidget(widgets.HorizontalLine(self))

        # ----------------------------------------------------------------------
        # Align to Components
        frame = widgets.FrameWidget(
            'Manual Unfreeze Transformation',
            False,
            False,
            self,
        )
        main_layout.addWidget(frame)

        layout = QVBoxLayout(self)
        main_layout.addLayout(layout)

        form_layout = widgets.FormLayout(self)
        form_layout.setFieldGrowthPolicy(
            widgets.FormLayout.AllNonFixedFieldsGrow
        )
        layout.addLayout(form_layout)

        self.__pivot: widgets.NodePicker = widgets.NodePicker(1, self)
        form_layout.addRow(widgets.FormLabel('Pivot'), self.__pivot)

        self.__aim: widgets.NodePicker = widgets.NodePicker(1, self)
        form_layout.addRow(widgets.FormLabel('Aim Target (X+)'), self.__aim)

        self.__up: widgets.NodePicker = widgets.NodePicker(1, self)
        form_layout.addRow(widgets.FormLabel('Up Target (Y+)'), self.__up)

        form_layout.addRow(
            '',
            QLabel('<strong>*Affects Translate & Rotate only.</strong>', self),
        )

        button = QPushButton('Apply', self)
        button.clicked.connect(self.align_to_components)
        form_layout.addRow('', button)

        # End
        main_layout.addStretch(True)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.write()

    # override
    def reset_settings(self) -> None:
        '''Reset ui settings.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()

    # override
    def about(self) -> None:
        '''Show a about dialog.[override]'''
        widgets.AboutDialog.info(
            self, __product__, __version__, __copyright__, __doc__
        )

    @widgets.undo
    def affine_transformation(self) -> None:
        '''Apply'''
        self.save_settings()
        src: str = self.__affine_src.text()
        if not src:
            _logger.error(
                'Source node is required to unfreeze transformations.'
            )
            return

        dsts: list[str] = self.__affine_dsts.text_as_list()
        if not dsts:
            _logger.error(
                'Destination node is required to unfreeze transformations.'
            )
            return

        result: bool = affine_transformation(src, dsts)
        if result:
            _logger.info('Done.')

    @widgets.undo
    def triangle_transformation(self) -> None:
        '''Apply'''
        self.save_settings()
        src: str = self.__planar_src.text()
        if not src:
            _logger.error(
                'Source node is required to unfreeze transformations.'
            )
            return

        dsts: list[str] = self.__planar_dsts.text_as_list()
        if not dsts:
            _logger.error(
                'Destination node is required to unfreeze transformations.'
            )
            return

        result: bool = triangle_transformation(src, dsts)
        if result:
            _logger.info('Done.')

    @widgets.undo
    def align_to_components(self) -> None:
        '''Apply Manual Transformation'''
        self.save_settings()

        pivot: str = self.__pivot.text()
        aim: str = self.__aim.text()
        up: str = self.__up.text()

        if not pivot:
            _logger.error('Pivot field is required.')
            return

        if not aim:
            _logger.error('Aim Target field is required.')
            return

        if not up:
            _logger.error('Up Target field is required.')
            return

        selection: list[str] = cmds.ls(selection=True, type='transform')
        if not selection:
            _logger.error('Select node to apply manual unfreeze.')
            return

        result: bool = align_to_components(selection, pivot, aim, up)
        if result:
            _logger.info('Done.')


# ==============================================================================
#
# Functions
#
# ==============================================================================
def __get_mesh_fn(node: str) -> OpenMaya.MFnMesh:
    '''Return MFnMesh object.'''
    selection_list: OpenMaya.MSelectionList = OpenMaya.MSelectionList()
    selection_list.add(node)
    return OpenMaya.MFnMesh(selection_list.getDagPath(0))


def __get_point(node: str) -> OpenMaya.MPoint | None:
    '''Get world position from node name (Vertex or Transform pivot).'''
    try:
        # Use xform to support both vertices and transforms/locators
        pos: list[float] = cmds.xform(
            node, query=True, translation=True, worldSpace=True
        )
        return OpenMaya.MPoint(pos[0], pos[1], pos[2])

    except RuntimeError:
        return None

    except TypeError:
        return None


def _get_matrix_4_points(
    mesh_fn: OpenMaya.MFnMesh,
    vtx_ids: tuple[int, int, int, int],
    space: int,
) -> OpenMaya.MMatrix:
    '''Construct matrix using 4 points (Solid).'''
    points: list[OpenMaya.MPoint] = [
        mesh_fn.getPoint(i, space) for i in vtx_ids
    ]
    return OpenMaya.MMatrix(
        [
            [points[0].x, points[0].y, points[0].z, 1],
            [points[1].x, points[1].y, points[1].z, 1],
            [points[2].x, points[2].y, points[2].z, 1],
            [points[3].x, points[3].y, points[3].z, 1],
        ]
    )


def _get_matrix_3_points(
    mesh_fn: OpenMaya.MFnMesh,
    vtx_ids: tuple[int, int, int, OpenMaya.MPoint],
    space: int,
) -> OpenMaya.MMatrix:
    '''Construct matrix using 3 points + virtual point (Planar).'''
    points: list[OpenMaya.MPoint] = [
        mesh_fn.getPoint(i, space) for i in vtx_ids[0:3]
    ]

    p_0: OpenMaya.MPoint = points[0]
    p_1: OpenMaya.MPoint = points[1]
    p_2: OpenMaya.MPoint = points[2]
    p_3: OpenMaya.MPoint = OpenMaya.MPoint()

    if space == OpenMaya.MSpace.kObject:
        # Use the virtual point stored in vtx_ids for Source
        p_3 = vtx_ids[3]
    else:
        # Recalculate virtual point for Destination to match local normal
        vector_ab: OpenMaya.MVector = (p_1 - p_0).normal()
        vector_ac: OpenMaya.MVector = (p_2 - p_0).normal()
        normal: OpenMaya.MVector = (vector_ab ^ vector_ac).normal()
        p_3 = p_0 + normal

    return OpenMaya.MMatrix(
        [
            [p_0.x, p_0.y, p_0.z, 1],
            [p_1.x, p_1.y, p_1.z, 1],
            [p_2.x, p_2.y, p_2.z, 1],
            [p_3.x, p_3.y, p_3.z, 1],
        ]
    )


def _apply_matrix(
    dst: str,
    target_world_matrix: OpenMaya.MMatrix,
    pivots: list[float],
    rotate_order: int,
    rotate_axis: tuple[float, float, float],
    handle: tuple[float, float, float],
) -> None:
    '''Applies the calculated matrix to the destination node with proper decomposition.'''

    # Apply Inverse Matrix
    inverse_matrix: OpenMaya.MMatrix = target_world_matrix.inverse()
    cmds.xform(dst, matrix=[v for v in inverse_matrix], worldSpace=True)

    # Freeze And Reset Transformations.
    cmds.makeIdentity(dst, apply=True, translate=True, rotate=True, scale=True)
    cmds.makeIdentity(dst, apply=False, translate=True, rotate=True, scale=True)

    # Matrix Decomposition
    t_mtx: OpenMaya.MTransformationMatrix = OpenMaya.MTransformationMatrix(
        target_world_matrix
    )

    # Translate: Translate = Translation - Pivot + (Pivot * Target Matrix)
    translation: OpenMaya.MVector = t_mtx.translation(
        OpenMaya.MSpace.kTransform
    )
    pivot: OpenMaya.MVector = OpenMaya.MVector(pivots[0], pivots[1], pivots[2])
    transformed_pivot: OpenMaya.MVector = pivot * target_world_matrix
    translation = translation - pivot + transformed_pivot
    translate: list[float] = [
        translation.x,
        translation.y,
        translation.z,
    ]

    # Rotate: Reorder original rotate order.
    rotation: OpenMaya.MEulerRotation = t_mtx.rotation()
    rotation = rotation.reorderIt(rotate_order)
    rotate: list[float] = [
        math.degrees(rotation.x),
        math.degrees(rotation.y),
        math.degrees(rotation.z),
    ]

    scale: list[float] = t_mtx.scale(OpenMaya.MSpace.kTransform)
    shear: list[float] = t_mtx.shear(OpenMaya.MSpace.kTransform)

    # Restore node settings.
    cmds.xform(dst, rotatePivot=pivots[0:3], objectSpace=True)
    cmds.xform(dst, scalePivot=pivots[3:6], objectSpace=True)
    cmds.setAttr(f'{dst}.rotateOrder', rotate_order)
    cmds.setAttr(f'{dst}.rotateAxis', *rotate_axis)
    cmds.setAttr(f'{dst}.selectHandle', *handle)

    # Apply results.
    cmds.setAttr(f'{dst}.translate', *translate)
    cmds.setAttr(f'{dst}.rotate', *rotate)
    cmds.setAttr(f'{dst}.scale', *scale)
    cmds.setAttr(f'{dst}.shear', *shear)


def find_best_stable_4_points(
    mesh_fn: OpenMaya.MFnMesh,
) -> tuple[int, int, int, int] | None:
    '''Algorithm to find the best 4 points to minimize calculation errors.'''

    # Check num of points.
    points: OpenMaya.MPointArray = mesh_fn.getPoints(OpenMaya.MSpace.kObject)
    num_points: int = len(points)
    if num_points < 4:
        return None

    index_a: int = -1
    index_b: int = -1
    index_c: int = -1
    index_d: int = -1
    max_dist_square: float = -1.0

    # Find Point A: Furthest point from the first point.
    point_0: OpenMaya.MPoint = points[0]
    for i in range(num_points):
        distance_to: float = point_0.distanceTo(points[i])
        if distance_to > max_dist_square:
            max_dist_square = distance_to
            index_a = i

    # Find Point B: Furthest point from Point A.
    point_a: OpenMaya.MPoint = points[index_a]
    max_dist_square = -1.0
    for i in range(num_points):
        distance_to = point_a.distanceTo(points[i])
        if distance_to > max_dist_square:
            max_dist_square = distance_to
            index_b = i

    # Find Point C: Furthest point from Line Segment AB.
    point_b: OpenMaya.MPoint = points[index_b]
    max_dist_square = -1.0
    vector_ab: OpenMaya.MVector = (point_b - point_a).normal()
    for i in range(num_points):
        vec_ap = points[i] - point_a
        dist_sq = (vector_ab ^ vec_ap).length()
        if dist_sq > max_dist_square:
            max_dist_square = dist_sq
            index_c = i

    # Find Point D: Furthest point from Plane ABC.
    point_c = points[index_c]
    max_height: float = -1.0
    vector_ac: OpenMaya.MVector = (point_c - point_a).normal()
    normal: OpenMaya.MVector = (vector_ab ^ vector_ac).normal()
    for i in range(num_points):
        vec_ap = points[i] - point_a
        height = abs(vec_ap * normal)
        if height > max_height:
            max_height = height
            index_d = i

    # Check max height.
    if max_height < 0.000001:
        return None

    # Check index.
    indexes: tuple[int, int, int, int] = (index_a, index_b, index_c, index_d)
    if len(indexes) != len(set(indexes)):
        return None

    return indexes


def find_best_stable_3_points(
    mesh_fn: OpenMaya.MFnMesh,
) -> tuple[int, int, int, OpenMaya.MPoint] | None:
    '''Algorithm to find the best 3 points to minimize calculation errors.'''
    # Check num of points.
    points: OpenMaya.MPointArray = mesh_fn.getPoints(OpenMaya.MSpace.kObject)
    num_points: int = len(points)
    if num_points < 3:
        return None

    index_a: int = -1
    index_b: int = -1
    index_c: int = -1
    max_dist_square: float = -1.0

    # Find Point A: Furthest point from the first point.
    point_0: OpenMaya.MPoint = points[0]
    for i in range(num_points):
        distance_to: float = point_0.distanceTo(points[i])
        if distance_to > max_dist_square:
            max_dist_square = distance_to
            index_a = i

    # Find Point B: Furthest point from Point A.
    point_a: OpenMaya.MPoint = points[index_a]
    max_dist_square = -1.0
    for i in range(num_points):
        distance_to = point_a.distanceTo(points[i])
        if distance_to > max_dist_square:
            max_dist_square = distance_to
            index_b = i

    # Find Point C: Furthest point from Line Segment AB.
    point_b: OpenMaya.MPoint = points[index_b]
    max_dist_square = -1.0
    vector_ab: OpenMaya.MVector = (point_b - point_a).normal()
    for i in range(num_points):
        vec_ap = points[i] - point_a
        dist_sq = (vector_ab ^ vec_ap).length()
        if dist_sq > max_dist_square:
            max_dist_square = dist_sq
            index_c = i

    # Find Point D: Furthest point from Plane ABC.
    point_c = points[index_c]
    vector_ac: OpenMaya.MVector = (point_c - point_a).normal()
    normal: OpenMaya.MVector = (vector_ab ^ vector_ac).normal()

    point_d: OpenMaya.MPoint = point_a + normal

    # Check index.
    indexes: tuple[int, int, int] = (index_a, index_b, index_c)
    if len(indexes) != len(set(indexes)):
        return None

    return (index_a, index_b, index_c, point_d)


def affine_transformation(src: str, dsts: list[str]) -> bool:
    '''Affine Transformation'''

    src_fn: OpenMaya.MFnMesh = __get_mesh_fn(src)
    vtx_ids: tuple[int, int, int, int] | None = find_best_stable_4_points(
        src_fn
    )
    if not vtx_ids:
        _logger.error('Failed to find valid points for calculation. %s', src)
        return False

    # Get Source Transform Informations
    pivots: list[float] = cmds.xform(
        src, query=True, pivots=True, objectSpace=True
    )

    src_inverse_mtx: OpenMaya.MMatrix = _get_matrix_4_points(
        src_fn, vtx_ids, OpenMaya.MSpace.kObject
    ).inverse()

    rotate_order: int = cmds.getAttr(f'{src}.rotateOrder')
    rotate_axis: tuple[float, float, float] = cmds.getAttr(f'{src}.rotateAxis')[
        0
    ]
    handle: tuple[float, float, float] = cmds.getAttr(f'{src}.selectHandle')[0]

    # Process targets
    for dst in dsts:
        dst_fn: OpenMaya.MFnMesh = __get_mesh_fn(dst)
        if src_fn.numVertices != dst_fn.numVertices:
            _logger.error('Topology Mismatch : %s', dst)
            continue

        # Reset
        cmds.makeIdentity(
            dst, apply=True, translate=True, rotate=True, scale=True
        )
        cmds.makeIdentity(
            dst, apply=False, translate=True, rotate=True, scale=True
        )

        # Calculate Affine Matrix (Local -> World)
        dst_matrix: OpenMaya.MMatrix = _get_matrix_4_points(
            dst_fn, vtx_ids, OpenMaya.MSpace.kWorld
        )

        # Calculate the Target World Matrix
        target_world_matrix: OpenMaya.MMatrix = src_inverse_mtx * dst_matrix

        # Apply using common function
        _apply_matrix(
            dst,
            target_world_matrix,
            pivots,
            rotate_order,
            rotate_axis,
            handle,
        )

    return True


def triangle_transformation(src: str, dsts: list[str]) -> bool:
    '''Triangle Transformation'''

    src_fn: OpenMaya.MFnMesh = __get_mesh_fn(src)
    vtx_ids: tuple[int, int, int, OpenMaya.MPoint] | None = (
        find_best_stable_3_points(src_fn)
    )
    if not vtx_ids:
        _logger.error('Failed to find valid points for calculation. %s', src)
        return False

    # Get Source Transform Informations
    pivots: list[float] = cmds.xform(
        src, query=True, pivots=True, objectSpace=True
    )

    src_inverse_mtx: OpenMaya.MMatrix = _get_matrix_3_points(
        src_fn, vtx_ids, OpenMaya.MSpace.kObject
    ).inverse()

    rotate_order: int = cmds.getAttr(f'{src}.rotateOrder')
    rotate_axis: tuple[float, float, float] = cmds.getAttr(f'{src}.rotateAxis')[
        0
    ]
    handle: tuple[float, float, float] = cmds.getAttr(f'{src}.selectHandle')[0]

    # Process targets
    for dst in dsts:
        dst_fn: OpenMaya.MFnMesh = __get_mesh_fn(dst)
        if src_fn.numVertices != dst_fn.numVertices:
            _logger.error('Topology Mismatch : %s', dst)
            continue

        # Reset
        cmds.makeIdentity(
            dst, apply=True, translate=True, rotate=True, scale=True
        )
        cmds.makeIdentity(
            dst, apply=False, translate=True, rotate=True, scale=True
        )

        # Calculate Affine Matrix (Local -> World)
        dst_matrix: OpenMaya.MMatrix = _get_matrix_3_points(
            dst_fn, vtx_ids, OpenMaya.MSpace.kWorld
        )

        # Calculate the Target World Matrix
        target_world_matrix: OpenMaya.MMatrix = src_inverse_mtx * dst_matrix

        # Apply using common function
        _apply_matrix(
            dst,
            target_world_matrix,
            pivots,
            rotate_order,
            rotate_axis,
            handle,
        )

    return True


def align_to_components(
    target_nodes: list[str], pivot_node: str, aim_node: str, up_node: str
) -> bool:
    '''Manual Transformation using 3 points (Pivot, Aim, Up).'''

    # 1. Get Coordinates
    p: OpenMaya.MPoint | None = __get_point(pivot_node)
    a: OpenMaya.MPoint | None = __get_point(aim_node)
    u: OpenMaya.MPoint | None = __get_point(up_node)

    if not p:
        _logger.error('Failed to get coordinates from selections : %s', p)
        return False

    if not a:
        _logger.error('Failed to get coordinates from selections : %s', a)
        return False

    if not u:
        _logger.error('Failed to get coordinates from selections : %s', u)
        return False

    # Process targets
    for target_node in target_nodes:

        # Reset
        cmds.makeIdentity(
            target_node, apply=True, translate=True, rotate=True, scale=True
        )
        cmds.makeIdentity(
            target_node, apply=False, translate=True, rotate=True, scale=True
        )

        # Construct Matrix (Aim=X, Up=Y)
        vec_x: OpenMaya.MVector = (a - p).normal()
        vec_up_temp: OpenMaya.MVector = (u - p).normal()
        vec_z: OpenMaya.MVector = (vec_x ^ vec_up_temp).normal()
        vec_y: OpenMaya.MVector = (vec_z ^ vec_x).normal()
        target_world_matrix = OpenMaya.MMatrix(
            [
                [vec_x.x, vec_x.y, vec_x.z, 0],
                [vec_y.x, vec_y.y, vec_y.z, 0],
                [vec_z.x, vec_z.y, vec_z.z, 0],
                [p.x, p.y, p.z, 1],
            ]
        )

        # Get current node settings to preserve them
        rotate_order: int = cmds.getAttr(f'{target_node}.rotateOrder')
        rotate_axis: tuple[float, float, float] = cmds.getAttr(
            f'{target_node}.rotateAxis'
        )[0]
        handle: tuple[float, float, float] = cmds.getAttr(
            f'{target_node}.selectHandle'
        )[0]

        # Resetting the Local Pivot to 0,0,0.
        zero_pivots = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        _apply_matrix(
            target_node,
            target_world_matrix,
            zero_pivots,
            rotate_order,
            rotate_axis,
            handle,
        )

    return True


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
