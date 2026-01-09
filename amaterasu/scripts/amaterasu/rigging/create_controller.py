# ==============================================================================
#
# Create Controllerr
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt, QSize, QItemSelectionModel
    from PySide2.QtGui import QStandardItemModel, QStandardItem
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QGridLayout,
        QTabWidget,
        QListView,
        QLineEdit,
        QSpinBox,
        QDoubleSpinBox,
        QCheckBox,
        QPushButton,
        QLabel,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, QSize, QItemSelectionModel
        from PySide6.QtGui import QStandardItemModel, QStandardItem
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QGridLayout,
            QTabWidget,
            QListView,
            QLineEdit,
            QSpinBox,
            QDoubleSpinBox,
            QCheckBox,
            QPushButton,
            QLabel,
        )
from maya import cmds
from ..lib import parser, widgets
from ..edit import combine_shapes
from ..modify import renamer
from ..display import drawing_color
from ..display import outliner_color


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Create Controller'
__version__: str = '1.00'
__doc__ = 'Create controller for rigging.'
__copyright__ = 'Copyright(c) 2014-2024 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    shape: parser.Variant[int] = parser.Variant(0)
    prefix: parser.Variant[str] = parser.Variant('controller')
    name: parser.Variant[str] = parser.Variant('C')
    suffix: parser.Variant[str] = parser.Variant('ctrl')
    radius: parser.Variant[float] = parser.Variant(1.0)
    enable_line_width: parser.Variant[bool] = parser.Variant(False)
    line_width: parser.Variant[float] = parser.Variant(1.0)
    enable_line_color: parser.Variant[bool] = parser.Variant(False)
    line_color: parser.Variant[list[float]] = parser.Variant(
        [0.0, 0.275, 0.098]
    )
    offset_number: parser.Variant[int] = parser.Variant(0)


class Controller:
    '''Controller'''

    def create(
        self,
        prefix: str | None,
        name: str | None,
        suffix: str | None,
        radius: float = 1.0,
        line_width: float | None = None,
        lineColor: list[float] | None = None,
        offset_numer: int = 0,
        parent: str | None = None,
    ) -> str:
        '''Create Controller'''
        parent_matrix: list[float] = []
        node_name: str = '_'.join(
            filter(None, [prefix, name, suffix])
        )  # f'{prefix}_{name}_{suffix}'

        if parent is None:
            selection: list[str] = cmds.ls(selection=True, type='transform')
            if selection:
                parent = selection[0]
                parent_matrix = cmds.xform(
                    selection[0], query=True, matrix=True, worldSpace=True
                )
        else:
            parent_matrix = cmds.xform(
                parent, query=True, matrix=True, worldSpace=True
            )

        # Create Offset
        for i in range(offset_numer):
            transform_name: str = '_'.join(
                filter(None, [f'{prefix}Offset{i}', name, 'null'])
            )  # f'{prefix}Offset{i}_{name}_null'
            if parent:
                parent = cmds.createNode(
                    'transform', name=transform_name, parent=parent
                )

            else:
                parent = cmds.createNode('transform', name=transform_name)

        # Create Shape
        node_name = self.create_shape(node_name)
        self.set_cv_curve_style(node_name, radius, line_width, lineColor)
        if parent:
            node_name = cmds.parent(node_name, parent)[0]

        if parent_matrix:
            cmds.xform(node_name, matrix=parent_matrix, worldSpace=True)

        cmds.select(node_name)
        return node_name

    def create_shape(self, node_name: str) -> str:
        '''Creaate Shape'''
        return node_name

    def set_cv_curve_style(
        self,
        node_name: str,
        radius: float = 1.0,
        line_width: float | None = None,
        line_color: list[float] | None = None,
    ) -> None:
        '''Set curve style'''
        shapes: list[str] = (
            cmds.listRelatives(node_name, shapes=True, path=True) or []
        )
        for shape in shapes:
            cmds.scale(radius, radius, radius, shape + '.cv[*]')

        if line_width is not None:
            for shape in shapes:
                cmds.setAttr(f'{shape}.lineWidth', line_width)

        if line_color is not None:
            cmds.setAttr(f'{node_name}.overrideEnabled', True)
            cmds.setAttr(f'{node_name}.overrideRGBColors', 1)
            cmds.setAttr(
                f'{node_name}.overrideColorRGB', *line_color, type='double3'
            )

    @classmethod
    def widget(cls, icon: str) -> QStandardItem:
        '''Create widget.'''
        item = QStandardItem()
        item.setIcon(widgets.icon_from_file_name(icon))
        item.setData(cls())
        return item


class Circle(Controller):
    '''Circle'''

    def create_shape(self, node_name: str) -> str:
        '''Creaate Shape[override]'''
        node_name = cmds.circle(
            name=node_name,
            center=[0, 0, 0],
            normal=[0, 1, 0],
            sweep=360,
            radius=1,
            degree=3,
            sections=8,
            constructionHistory=False,
        )[0]
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        '''Create widget.[override]'''
        return super().widget('rigging/a_circle.png')


class Square(Controller):
    def create_shape(self, node_name: str) -> str:
        '''Creaate Shape[override]'''
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[(1, 0, -1), (1, 0, 1), (-1, 0, 1), (-1, 0, -1)],
            knot=[0, 1, 2, 3],
        )
        cmds.closeCurve(
            node_name,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        '''Create widget.[override]'''
        return super().widget('rigging/a_square.png')


class Triangle(Controller):
    def create_shape(self, node_name: str) -> str:
        '''Creaate Shape[override]'''
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[(0, 0, 1), (0.866026, 0, -0.5), (-0.866026, 0, -0.5)],
            knot=[0, 1, 2],
        )
        cmds.closeCurve(
            node_name,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        '''Create widget.[override]'''
        return super().widget('rigging/a_triangle.png')


class Cross(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0.5, 0, -1),
                (0.5, 0, -0.5),
                (1, 0, -0.5),
                (1, 0, 0.5),
                (0.5, 0, 0.5),
                (0.5, 0, 1),
                (-0.5, 0, 1),
                (-0.5, 0, 0.5),
                (-1, 0, 0.5),
                (-1, 0, -0.5),
                (-0.5, 0, -0.5),
                (-0.5, 0, -1),
            ],
            knot=[i for i in range(11 + 1)],
        )
        cmds.closeCurve(
            node_name,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_cross.png')


class Arrow1(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0, 0, -1),
                (0.6, 0, 0),
                (0.3, 0, 0),
                (0.3, 0, 1),
                (-0.3, 0, 1),
                (-0.3, 0, 0),
                (-0.6, 0, 0),
            ],
            knot=[i for i in range(6 + 1)],
        )
        cmds.closeCurve(
            node_name,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_arrow1.png')


class Arrow2(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0, 0, -1),
                (0.3, 0, -0.5),
                (0.15, 0, -0.5),
                (0.15, 0, 0.5),
                (0.3, 0, 0.5),
                (0, 0, 1),
                (-0.3, 0, 0.5),
                (-0.15, 0, 0.5),
                (-0.15, 0, -0.5),
                (-0.3, 0, -0.5),
            ],
            knot=[i for i in range(9 + 1)],
        )
        cmds.closeCurve(
            node_name,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_arrow2.png')


class Arrow3(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0, 0, -1),
                (0.3, 0, -0.5),
                (0.15, 0, -0.5),
                (0.15, 0, -0.15),
                (0.5, 0, -0.15),
                (0.5, 0, -0.3),
                (1, 0, 0),
                (0.5, 0, 0.3),
                (0.5, 0, 0.15),
                (0.15, 0, 0.15),
                (0.15, 0, 0.5),
                (0.3, 0, 0.5),
                (0, 0, 1),
                (-0.3, 0, 0.5),
                (-0.15, 0, 0.5),
                (-0.15, 0, 0.15),
                (-0.5, 0, 0.15),
                (-0.5, 0, 0.3),
                (-1, 0, 0),
                (-0.5, 0, -0.3),
                (-0.5, 0, -0.15),
                (-0.15, 0, -0.15),
                (-0.15, 0, -0.5),
                (-0.3, 0, -0.5),
            ],
            knot=[i for i in range(23 + 1)],
        )
        cmds.closeCurve(
            node_name,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_arrow3.png')


class Arrow4(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0.763255, 0, -1),
                (0.513251, 0, -0.499364),
                (0.410247, 0, -0.661048),
                (0.348945, 0, -0.610739),
                (0.241531, 0, -0.479855),
                (0.161715, 0, -0.33053),
                (0.112565, 0, -0.168503),
                (0.0959685, 0, 3.1461e-08),
                (-0.0959685, 0, -3.1461e-08),
                (-0.0756843, 0, -0.205948),
                (-0.0156114, 0, -0.403981),
                (0.0819415, 0, -0.586489),
                (0.213225, 0, -0.746459),
                (0.306873, 0, -0.823313),
                (0.203868, 0, -0.984998),
            ],
            knot=[i for i in range(14 + 1)],
        )
        cmds.closeCurve(
            node_name,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_arrow4.png')


class Arrow5(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0.763255, 0, -1),
                (0.513251, 0, -0.499364),
                (0.410247, 0, -0.661048),
                (0.348945, 0, -0.610739),
                (0.241531, 0, -0.479855),
                (0.161715, 0, -0.33053),
                (0.112565, 0, -0.168503),
                (0.0959685, 0, -3.1461e-08),
                (0.112565, 0, 0.168503),
                (0.161715, 0, 0.33053),
                (0.241531, 0, 0.479855),
                (0.348945, 0, 0.610739),
                (0.410247, 0, 0.661048),
                (0.513251, 0, 0.499364),
                (0.763255, 0, 1),
                (0.203868, 0, 0.984998),
                (0.306873, 0, 0.823313),
                (0.213225, 0, 0.746459),
                (0.0819415, 0, 0.586489),
                (-0.0156114, 0, 0.403981),
                (-0.0756843, 0, 0.205948),
                (-0.0959685, 0, 3.1461e-08),
                (-0.0756843, 0, -0.205948),
                (-0.0156114, 0, -0.403981),
                (0.0819415, 0, -0.586489),
                (0.213225, 0, -0.746459),
                (0.306873, 0, -0.823313),
                (0.203868, 0, -0.984998),
            ],
            knot=[i for i in range(27 + 1)],
        )
        cmds.closeCurve(
            node_name,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_arrow5.png')


class Arch(Controller):
    def create_shape(self, node_name: str) -> str:
        circleA: str = cmds.circle(
            name='ctl#',
            center=[0, 0, 0],
            normal=[0, 1, 0],
            sweep=180,
            radius=1,
            degree=3,
            sections=8,
            constructionHistory=False,
        )[0]
        cmds.setAttr(f'{circleA}.ry', -90)
        cmds.makeIdentity(
            circleA,
            apply=True,
            translate=True,
            rotate=True,
            scale=True,
            normal=False,
        )

        circleB: str = cmds.circle(
            name='ctl#',
            center=[0, 0, 0],
            normal=[0, 1, 0],
            sweep=180,
            radius=0.7,
            degree=3,
            sections=8,
            constructionHistory=False,
        )[0]
        cmds.setAttr(f'{circleB}.ry', -90)
        cmds.makeIdentity(
            circleB,
            apply=True,
            translate=True,
            rotate=True,
            scale=True,
            normal=False,
        )

        lineA: str = cmds.curve(
            name='ctl#', degree=1, point=[(-1, 0, 0), (-0.7, 0, 0)], knot=[0, 1]
        )
        lineB: str = cmds.curve(
            name='ctl#', degree=1, point=[(0.7, 0, 0), (1, 0, 0)], knot=[0, 1]
        )

        cmds.attachCurve(circleA, lineA, keepMultipleKnots=True, blendBias=0.5)
        cmds.attachCurve(circleB, lineB, keepMultipleKnots=True, blendBias=0.5)
        cmds.attachCurve(
            circleA, circleB, keepMultipleKnots=True, blendBias=0.5
        )
        cmds.delete(circleB, lineA, lineB)
        node_name = cmds.rename(circleA, node_name)
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_arch.png')


class Ellipse(Controller):
    def create_shape(self, node_name: str) -> str:
        circleA: str = cmds.circle(
            name='ctl#',
            center=[0, 0, 0],
            normal=[0, 1, 0],
            sweep=180,
            radius=0.5,
            degree=3,
            sections=8,
            constructionHistory=False,
        )[0]
        cmds.setAttr(f'{circleA}.tz', -0.5)
        cmds.setAttr(f'{circleA}.ry', -90)
        cmds.makeIdentity(
            circleA,
            apply=True,
            translate=True,
            rotate=True,
            scale=True,
            normal=False,
        )

        circleB: str = cmds.circle(
            name='ctl#',
            center=[0, 0, 0],
            normal=[0, 1, 0],
            sweep=180,
            radius=0.5,
            degree=3,
            sections=8,
            constructionHistory=False,
        )[0]
        cmds.setAttr(f'{circleB}.tz', 0.5)
        cmds.setAttr(f'{circleB}.ry', 90)
        cmds.makeIdentity(
            circleB,
            apply=True,
            translate=True,
            rotate=True,
            scale=True,
            normal=False,
        )

        lineA: str = cmds.curve(
            name='ctl#',
            degree=1,
            point=[(-0.5, 0, -0.5), (-0.5, 0, 0.5)],
            knot=[0, 1],
        )
        lineB: str = cmds.curve(
            name='ctl#',
            degree=1,
            point=[(0.5, 0, -0.5), (0.5, 0, 0.5)],
            knot=[0, 1],
        )

        cmds.attachCurve(circleA, lineA, keepMultipleKnots=True, blendBias=0.5)
        cmds.attachCurve(circleB, lineB, keepMultipleKnots=True, blendBias=0.5)
        cmds.attachCurve(
            circleA, circleB, keepMultipleKnots=True, blendBias=0.5
        )
        cmds.delete(circleB, lineA, lineB)
        node_name = cmds.rename(circleA, node_name)
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_ellipse.png')


class Star(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0, 0, -0.948926),
                (0.308316, 0, -0.324186),
                (1.0, 0, -0.22401),
                (0.498872, 0, 0.262274),
                (0.61665, 0, 0.948926),
                (0, 0, 0.62472),
                (-0.61665, 0, 0.948926),
                (-0.498884, 0, 0.262274),
                (-1.0, 0, -0.22401),
                (-0.30833, 0, -0.324186),
            ],
            knot=[i for i in range(9 + 1)],
        )
        cmds.closeCurve(
            node_name,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_star.png')


class VectorCircle(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0, 0, -1),
                (0.156072, 0, -0.784628),
                (0.306147, 0, -0.739104),
                (0.444456, 0, -0.665176),
                (0.565685, 0, -0.565685),
                (0.665176, 0, -0.444456),
                (0.739103, 0, -0.306147),
                (0.784628, 0, -0.156072),
                (0.8, 0, 1.3113e-07),
                (0.784628, 0, 0.156072),
                (0.739103, 0, 0.306147),
                (0.665175, 0, 0.444456),
                (0.565685, 0, 0.565685),
                (0.444456, 0, 0.665175),
                (0.306146, 0, 0.739103),
                (0.156072, 0, 0.784628),
                (-2.6226e-07, 0, 0.799999),
                (-0.156072, 0, 0.784628),
                (-0.306147, 0, 0.739103),
                (-0.444456, 0, 0.665175),
                (-0.565685, 0, 0.565685),
                (-0.665175, 0, 0.444456),
                (-0.739103, 0, 0.306146),
                (-0.784628, 0, 0.156072),
                (-0.799999, 0, -3.57628e-07),
                (-0.784627, 0, -0.156072),
                (-0.739103, 0, -0.306147),
                (-0.665175, 0, -0.444456),
                (-0.565685, 0, -0.565685),
                (-0.444455, 0, -0.665175),
                (-0.306146, 0, -0.739103),
                (-0.156072, 0, -0.784627),
            ],
            knot=[i for i in range(31 + 1)],
        )
        cmds.closeCurve(
            node_name,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_vector_circle.png')


class Gear(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (-0.140012, 0, -1),
                (0.140013, 0, -1),
                (0.173862, 0, -0.8),
                (0.312145, 0, -0.753583),
                (0.442747, 0, -0.688624),
                (0.608104, 0, -0.80611),
                (0.806111, 0, -0.608103),
                (0.688625, 0, -0.442747),
                (0.753584, 0, -0.312144),
                (0.800001, 0, -0.173861),
                (1.000001, 0, -0.140012),
                (1.000001, 0, 0.140013),
                (0.800001, 0, 0.173862),
                (0.753584, 0, 0.312145),
                (0.688625, 0, 0.442747),
                (0.806111, 0, 0.608104),
                (0.608104, 0, 0.806111),
                (0.442747, 0, 0.688625),
                (0.312145, 0, 0.753584),
                (0.173862, 0, 0.800001),
                (0.140013, 0, 1.000001),
                (-0.140012, 0, 1.000001),
                (-0.173861, 0, 0.800001),
                (-0.312144, 0, 0.753584),
                (-0.442747, 0, 0.688625),
                (-0.608103, 0, 0.806111),
                (-0.80611, 0, 0.608104),
                (-0.688624, 0, 0.442747),
                (-0.753583, 0, 0.312145),
                (-0.8, 0, 0.173862),
                (-1, 0, 0.140013),
                (-1, 0, -0.140012),
                (-0.8, 0, -0.173861),
                (-0.753583, 0, -0.312144),
                (-0.688624, 0, -0.442747),
                (-0.80611, 0, -0.608103),
                (-0.608103, 0, -0.80611),
                (-0.442747, 0, -0.688624),
                (-0.312144, 0, -0.753584),
                (-0.173861, 0, -0.8),
            ],
            knot=[i for i in range(39 + 1)],
        )
        cmds.closeCurve(
            node_name,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )

        curveB: str = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (-1.71224e-09, 0, -0.305877),
                (0.0596737, 0, -0.3),
                (0.117054, 0, -0.282594),
                (0.169937, 0, -0.254328),
                (0.216288, 0, -0.216288),
                (0.254328, 0, -0.169936),
                (0.282594, 0, -0.117054),
                (0.3, 0, -0.0596737),
                (0.305878, 0, -1.71224e-09),
                (0.3, 0, 0.0596737),
                (0.282595, 0, 0.117054),
                (0.254328, 0, 0.169937),
                (0.216289, 0, 0.216288),
                (0.169937, 0, 0.254328),
                (0.117055, 0, 0.282594),
                (0.0596744, 0, 0.3),
                (6.70209e-07, 0, 0.305878),
                (-0.0596731, 0, 0.3),
                (-0.117054, 0, 0.282594),
                (-0.169936, 0, 0.254328),
                (-0.216287, 0, 0.216289),
                (-0.254327, 0, 0.169937),
                (-0.282594, 0, 0.117055),
                (-0.3, 0, 0.0596744),
                (-0.305877, 0, 6.70209e-07),
                (-0.3, 0, -0.0596731),
                (-0.282594, 0, -0.117054),
                (-0.254328, 0, -0.169936),
                (-0.216288, 0, -0.216287),
                (-0.169936, 0, -0.254327),
                (-0.117054, 0, -0.282593),
                (-0.0596737, 0, -0.3),
            ],
            knot=[i for i in range(31 + 1)],
        )
        cmds.closeCurve(
            curveB,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )
        combine_shapes.apply(node_name, [curveB])
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_gear.png')


class Cube(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (1, 1, 1),
                (-1, 1, 1),
                (-1, 1, -1),
                (1, 1, -1),
                (1, 1, 1),
                (1, -1, 1),
                (1, -1, -1),
                (1, 1, -1),
                (1, -1, -1),
                (-1, -1, -1),
                (-1, 1, -1),
                (-1, -1, -1),
                (-1, -1, 1),
                (-1, 1, 1),
                (-1, -1, 1),
                (1, -1, 1),
            ],
            knot=[i for i in range(15 + 1)],
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_cube.png')


class Sphere(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.circle(
            name=node_name,
            center=[0, 0, 0],
            normal=[1, 0, 0],
            sweep=360,
            radius=1,
            degree=3,
            sections=8,
            constructionHistory=False,
        )[0]
        curveB: str = cmds.circle(
            center=[0, 0, 0],
            normal=[0, 1, 0],
            sweep=360,
            radius=1,
            degree=3,
            sections=8,
            constructionHistory=False,
        )[0]
        curveC: str = cmds.circle(
            center=[0, 0, 0],
            normal=[0, 0, 1],
            sweep=360,
            radius=1,
            degree=3,
            sections=8,
            constructionHistory=False,
        )[0]
        combine_shapes.apply(node_name, [curveB, curveC])
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_sphere.png')


class Pyramid(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0, 1, 0),
                (-1, -1, -1),
                (-1, -1, 1),
                (0, 1, 0),
                (-1, -1, 1),
                (1, -1, 1),
                (0, 1, 0),
                (1, -1, 1),
                (1, -1, -1),
                (0, 1, 0),
                (1, -1, -1),
                (-1, -1, -1),
            ],
            knot=[i for i in range(11 + 1)],
        )
        cmds.closeCurve(
            node_name,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_pyramid.png')


class TriPyramid(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0, 1, 0),
                (0.866026, -1, -0.5),
                (0, -1, 1),
                (0, 1, 0),
                (0, -1, 1),
                (-0.866026, -1, -0.5),
                (0, 1, 0),
                (-0.866026, -1, -0.5),
                (0.866026, -1, -0.5),
            ],
            knot=[i for i in range(8 + 1)],
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_tri_pyramid.png')


class Octahedron(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0, 1, 0),
                (0, 0, -1),
                (1, 0, 0),
                (0, 1, 0),
                (1, 0, 0),
                (0, 0, 1),
                (0, 1, 0),
                (0, 0, 1),
                (-1, 0, 0),
                (0, 1, 0),
                (-1, 0, 0),
                (0, 0, -1),
                (0, -1, 0),
                (1, 0, 0),
                (0, -1, 0),
                (0, 0, 1),
                (0, -1, 0),
                (-1, 0, 0),
            ],
            knot=[i for i in range(17 + 1)],
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_octahedron.png')


class Cylinder(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (4.47035e-07, 1, -0.999999),
                (0.195091, 1, -0.980784),
                (0.382683, 1, -0.923878),
                (0.55557, 1, -0.831468),
                (0.707106, 1, -0.707106),
                (0.831469, 1, -0.555569),
                (0.923879, 1, -0.382683),
                (0.980784, 1, -0.19509),
                (1, 1, 0),
                (0.980785, 1, 0.19509),
                (0.923879, 1, 0.382683),
                (0.831469, 1, 0.55557),
                (0.707107, 1, 0.707107),
                (0.55557, 1, 0.83147),
                (0.382683, 1, 0.923879),
                (0.19509, 1, 0.980785),
                (-1.63913e-07, 1, 1),
                (-0.19509, 1, 0.980785),
                (-0.382683, 1, 0.923879),
                (-0.55557, 1, 0.831469),
                (-0.707107, 1, 0.707106),
                (-0.831469, 1, 0.55557),
                (-0.923879, 1, 0.382683),
                (-0.980785, 1, 0.19509),
                (-0.999999, 1, -3.27826e-07),
                (-0.980785, 1, -0.195091),
                (-0.923879, 1, -0.382683),
                (-0.831469, 1, -0.55557),
                (-0.707106, 1, -0.707106),
                (-0.555569, 1, -0.831469),
                (-0.382683, 1, -0.923879),
                (-0.19509, 1, -0.980784),
                (4.47035e-07, 1, -0.999999),
                (4.47035e-07, -1, -0.999999),
                (0.195091, -1, -0.980784),
                (0.382683, -1, -0.923878),
                (0.55557, -1, -0.831468),
                (0.707106, -1, -0.707106),
                (0.831469, -1, -0.555569),
                (0.923879, -1, -0.382683),
                (0.980784, -1, -0.19509),
                (1, -1, 0),
                (1, 1, 0),
                (1, -1, 0),
                (0.980785, -1, 0.19509),
                (0.923879, -1, 0.382683),
                (0.831469, -1, 0.55557),
                (0.707107, -1, 0.707107),
                (0.55557, -1, 0.83147),
                (0.382683, -1, 0.923879),
                (0.19509, -1, 0.980785),
                (-1.63913e-07, -1, 1),
                (-1.63913e-07, 1, 1),
                (-1.63913e-07, -1, 1),
                (-0.19509, -1, 0.980785),
                (-0.382683, -1, 0.923879),
                (-0.55557, -1, 0.831469),
                (-0.707107, -1, 0.707106),
                (-0.831469, -1, 0.55557),
                (-0.923879, -1, 0.382683),
                (-0.980785, -1, 0.19509),
                (-0.999999, -1, -3.27826e-07),
                (-0.999999, 1, -3.27826e-07),
                (-0.999999, -1, -3.27826e-07),
                (-0.980785, -1, -0.195091),
                (-0.923879, -1, -0.382683),
                (-0.831469, -1, -0.55557),
                (-0.707106, -1, -0.707106),
                (-0.555569, -1, -0.831469),
                (-0.382683, -1, -0.923879),
                (-0.19509, -1, -0.980784),
                (4.47035e-07, -1, -0.999999),
            ],
            knot=[i for i in range(71 + 1)],
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_cylinder.png')


class Locator(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name, degree=1, point=[(1, 0, 0), (-1, 0, 0)], knot=[0, 1]
        )
        curveB: str = cmds.curve(
            name=node_name, degree=1, point=[(0, 1, 0), (0, -1, 0)], knot=[0, 1]
        )
        curveC: str = cmds.curve(
            name=node_name, degree=1, point=[(0, 0, 1), (0, 0, -1)], knot=[0, 1]
        )

        combine_shapes.apply(node_name, [curveB, curveC])
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_locator.png')


class Root(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.circle(
            name=node_name,
            center=[0, 0, 0],
            normal=[0, 1, 0],
            sweep=360,
            radius=1,
            degree=3,
            sections=8,
            constructionHistory=False,
        )[0]
        cmds.setAttr(f'{node_name}.ry', 180)
        cmds.makeIdentity(
            node_name,
            apply=True,
            translate=True,
            rotate=True,
            scale=True,
            normal=False,
        )

        curveB = cmds.curve(
            name=node_name,
            degree=1,
            point=[(0, 0, 1), (0.866026, 0, -0.5), (-0.866026, 0, -0.5)],
            knot=[0, 1, 2],
        )
        cmds.closeCurve(
            curveB,
            constructionHistory=False,
            preserveShape=1,
            replaceOriginal=True,
            blendBias=0.5,
            blendKnotInsertion=True,
            parameter=0.1,
        )
        combine_shapes.apply(node_name, [curveB])
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_root.png')


class Manipulator(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0, 1, 0),
                (0.15, 0.75, 0),
                (-0.15, 0.75, 0),
                (0, 1, 0),
                (0, 0.75, -0.15),
                (-6.95453e-09, 0.75, 0.15),
                (0, 1, 0),
                (0, 0, 0),
                (0, 0, -1),
                (-6.95453e-09, 0.15, -0.75),
                (0, -0.15, -0.75),
                (0, 0, -1),
                (-0.15, 0, -0.75),
                (0.15, 0, -0.75),
                (0, 0, -1),
                (0, 0, 0),
                (1, 0, 0),
                (0.75, 0.15, 0),
                (0.75, -0.15, 0),
                (1, 0, 0),
                (0.75, 0, -0.15),
                (0.75, 6.95453e-09, 0.15),
                (1, 0, 0),
                (0, 0, 0),
                (0, -1, 0),
                (0.15, -0.75, 0),
                (-0.15, -0.75, 0),
                (0, -1, 0),
                (0, -0.75, -0.15),
                (6.95453e-09, -0.75, 0.15),
                (0, -1, 0),
                (0, 0, 0),
                (0, 0, 1),
                (0.15, 0, 0.75),
                (-0.15, 0, 0.75),
                (0, 0, 1),
                (-6.95453e-09, -0.15, 0.75),
                (0, 0.15, 0.75),
                (0, 0, 1),
                (0, 0, 0),
                (-1, 0, 0),
                (-0.75, -6.95453e-09, 0.15),
                (-0.75, 0, -0.15),
                (-1, 0, 0),
                (-0.75, -0.15, 0),
                (-0.75, 0.15, 0),
                (-1, 0, 0),
            ],
            knot=[i for i in range(46 + 1)],
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_manipulator.png')


class Tag(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0, 0, 0),
                (-1.49012e-08, 0, -0.8),
                (0.0382683, 0, -0.807612),
                (0.0707107, 0, -0.829289),
                (0, 0, -0.9),
                (0.0707107, 0, -0.829289),
                (0.092388, 0, -0.861732),
                (0.1, 0, -0.9),
                (0.092388, 0, -0.938268),
                (0.0707107, 0, -0.970711),
                (0, 0, -0.9),
                (0.0707107, 0, -0.970711),
                (0.0382684, 0, -0.992388),
                (5.06639e-08, 0, -1),
                (-0.0382683, 0, -0.992388),
                (-0.0707107, 0, -0.970711),
                (0, 0, -0.9),
                (-0.0707107, 0, -0.970711),
                (-0.0923879, 0, -0.938268),
                (-0.1, 0, -0.9),
                (-0.092388, 0, -0.861732),
                (-0.0707107, 0, -0.829289),
                (0, 0, -0.9),
                (-0.0707107, 0, -0.829289),
                (-0.0382684, 0, -0.807612),
                (-1.49012e-08, 0, -0.8),
            ],
            knot=[i for i in range(25 + 1)],
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_tag.png')


class LineArrow1(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (-0.6, 0, 0),
                (0, 0, -1),
                (0.6, 0, 0),
                (0, 0, -1),
                (0, 0, 1),
            ],
            knot=[0, 1, 2, 3, 4],
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_line_arrow1.png')


class LineArrow2(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (-0.3, 0, -0.5),
                (0, 0, -1),
                (0.3, 0, -0.5),
                (0, 0, -1),
                (0, 0, 1),
                (0.3, 0, 0.5),
                (0, 0, 1),
                (-0.3, 0, 0.5),
            ],
            knot=[i for i in range(7 + 1)],
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_line_arrow2.png')


class LineArrow3(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (-0.285714, 0, -0.642857),
                (0, 0, -1),
                (0.285714, 0, -0.642857),
                (0, 0, -1),
                (0, 0, 0),
                (1, 0, 0),
                (0.642857, 0, -0.285714),
                (1, 0, 0),
                (0.642857, 0, 0.285714),
                (1, 0, 0),
                (0, 0, 0),
                (0, 0, 1),
                (0.285714, 0, 0.642857),
                (0, 0, 1),
                (-0.285714, 0, 0.642857),
                (0, 0, 1),
                (0, 0, 0),
                (-1, 0, 0),
                (-0.642857, 0, 0.285714),
                (-1, 0, 0),
                (-0.642857, 0, -0.285714),
            ],
            knot=[i for i in range(20 + 1)],
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_line_arrow3.png')


class LineArrow4(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0.203868, 0, -0.984998),
                (0.763255, 0, -1),
                (0.513251, 0, -0.499364),
                (0.763255, 0, -1),
                (0.35856, 0, -0.742181),
                (0.281085, 0, -0.678599),
                (0.161736, 0, -0.533172),
                (0.0730518, 0, -0.367256),
                (0.0184404, 0, -0.187226),
                (0, 0, 0),
            ],
            knot=[i for i in range(9 + 1)],
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_line_arrow4.png')


class LineArrow5(Controller):
    def create_shape(self, node_name: str) -> str:
        node_name = cmds.curve(
            name=node_name,
            degree=1,
            point=[
                (0.203868, 0, -0.984998),
                (0.763255, 0, -1),
                (0.513251, 0, -0.499364),
                (0.763255, 0, -1),
                (0.35856, 0, -0.742181),
                (0.281085, 0, -0.678599),
                (0.161736, 0, -0.533172),
                (0.0730518, 0, -0.367256),
                (0.0184404, 0, -0.187226),
                (0, 0, 0),
                (0.0184404, 0, 0.187226),
                (0.0730518, 0, 0.367256),
                (0.161736, 0, 0.533172),
                (0.281085, 0, 0.678599),
                (0.35856, 0, 0.742181),
                (0.763255, 0, 1),
                (0.513251, 0, 0.499364),
                (0.763255, 0, 1),
                (0.203868, 0, 0.984998),
            ],
            knot=[i for i in range(18 + 1)],
        )
        renamer.normalize_shape_name(node_name)
        return node_name

    @classmethod
    def widget(cls, icon: str = '') -> QStandardItem:
        return super().widget('rigging/a_line_arrow5.png')


class ModifyCvCurveOption(QWidget):
    '''Modify Cv Curve Option'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
        main_layout = QVBoxLayout(self)

        line_width_form = widgets.QFormLayout(self)
        main_layout.addLayout(line_width_form)

        line_width_layout = QHBoxLayout(self)

        self.__line_width = QDoubleSpinBox(self)
        self.__line_width.setRange(-9999, 9999)
        self.__line_width.setDecimals(2)
        self.__line_width.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.__line_width.setMinimumWidth(80)
        line_width_layout.addWidget(self.__line_width)

        button = QPushButton('Apply', self)
        button.clicked.connect(self.apply_line_width)
        main_layout.addWidget(button)

        line_width_form.addRow(
            widgets.FormLabel('Line Width'), line_width_layout
        )

        main_layout.addWidget(widgets.HorizontalLine(self))

        self.__color_option = drawing_color.MainWindow(self)
        self.__color_option.menu_bar().hide()
        main_layout.addWidget(self.__color_option)

    def line_width(self) -> QSpinBox:
        '''return line width widget.'''
        return self.__line_width

    def color_option(self) -> drawing_color.MainWindow:
        '''Return drawing color widget.'''
        return self.__color_option

    @widgets.undo
    def apply_line_width(self) -> None:
        ''''''
        selection: list[str] = cmds.ls(selection=True)
        for node in selection:
            shapes: list[str] = (
                cmds.listRelatives(node, shapes=True, path=True) or []
            )
            if not shapes:
                continue
            for shape in shapes:
                if not cmds.objExists(f'{shape}.lineWidth'):
                    continue

                cmds.setAttr(f'{shape}.lineWidth', self.__line_width.value())


class ControllerOption(QWidget):
    '''Controller Option'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
        self.__main_layout = widgets.FormLayout(self)

        self.__view = QListView(self)
        self.__view.setGridSize(QSize(32, 32))
        self.__view.setIconSize(QSize(32, 32))
        self.__view.setViewMode(QListView.IconMode)
        self.__view.setResizeMode(QListView.Adjust)
        self.__view.setMovement(QListView.Static)
        self.__view.setStyleSheet(
            'QListView::item:selected { background-color: #5285a6; }'
        )
        self.__view.setFocusPolicy(Qt.NoFocus)
        self.__main_layout.addRow(self.__view)

        model = QStandardItemModel()
        model.appendRow(Circle.widget())
        model.appendRow(Square.widget())
        model.appendRow(Triangle.widget())
        model.appendRow(Cross.widget())
        model.appendRow(Arrow1.widget())
        model.appendRow(Arrow2.widget())
        model.appendRow(Arrow3.widget())
        model.appendRow(Arrow4.widget())
        model.appendRow(Arrow5.widget())
        model.appendRow(Arch.widget())
        model.appendRow(Ellipse.widget())
        model.appendRow(Star.widget())
        model.appendRow(VectorCircle.widget())
        model.appendRow(Gear.widget())
        model.appendRow(Cube.widget())
        model.appendRow(Sphere.widget())
        model.appendRow(Pyramid.widget())
        model.appendRow(TriPyramid.widget())
        model.appendRow(Octahedron.widget())
        model.appendRow(Cylinder.widget())
        model.appendRow(Locator.widget())
        model.appendRow(Root.widget())
        model.appendRow(Manipulator.widget())
        model.appendRow(Tag.widget())
        model.appendRow(LineArrow1.widget())
        model.appendRow(LineArrow2.widget())
        model.appendRow(LineArrow3.widget())
        model.appendRow(LineArrow4.widget())
        model.appendRow(LineArrow5.widget())
        self.__view.setModel(model)

        name_layout = QHBoxLayout(self)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(0)

        self.__prefix = QLineEdit(self)
        name_layout.addWidget(self.__prefix)
        name_layout.addWidget(QLabel(' _ ', self))

        self.__name = QLineEdit(self)
        name_layout.addWidget(self.__name)
        name_layout.addWidget(QLabel(' _ ', self))

        self.__suffix = QLineEdit(self)
        name_layout.addWidget(self.__suffix)
        self.__main_layout.addRow(widgets.FormLabel('Name'), name_layout)

        self.__radius = QDoubleSpinBox(self)
        self.__radius.setRange(0, 9999)
        self.__radius.setDecimals(2)
        self.__radius.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.__radius.setMinimumWidth(80)
        self.__main_layout.addRow(widgets.FormLabel('Radius'), self.__radius)

        self.__main_layout.addRow(widgets.HorizontalLine(self))

        self.__enable_line_width = QCheckBox('Enable Line Width', self)
        self.__enable_line_width.stateChanged.connect(self.update_ui)
        self.__main_layout.addRow('', self.__enable_line_width)

        self.__line_width = QDoubleSpinBox(self)
        self.__line_width.setRange(0, 9999)
        self.__line_width.setDecimals(2)
        self.__line_width.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.__line_width.setMinimumWidth(80)
        self.__main_layout.addRow(
            widgets.FormLabel('Line Width'), self.__line_width
        )
        self.__line_width_index = self.__main_layout.row_id()

        self.__enable_line_color = QCheckBox('Enable Line Color', self)
        self.__enable_line_color.stateChanged.connect(self.update_ui)
        self.__main_layout.addRow('', self.__enable_line_color)

        self.__line_color = widgets.ColorSelectButton(self)
        self.__line_color.setFixedSize(QSize(68, 13))
        self.__main_layout.addRow(
            widgets.FormLabel('Line Color'), self.__line_color
        )
        self.__line_color_index = self.__main_layout.row_id()

        self.__main_layout.addRow(widgets.HorizontalLine(self))

        self.__offset_number = QSpinBox(self)
        self.__offset_number.setRange(0, 9999)
        self.__offset_number.setButtonSymbols(QSpinBox.NoButtons)
        self.__offset_number.setMinimumWidth(80)
        self.__main_layout.addRow(
            widgets.FormLabel('Offset Null'), self.__offset_number
        )

        button = QPushButton('Create Controller', self)
        button.clicked.connect(self.apply)
        self.__main_layout.addRow(button)

    def update_ui(self) -> None:
        '''Update UI.'''
        self.__main_layout.set_row_enabled(
            self.__line_width_index, self.__enable_line_width.isChecked()
        )
        self.__main_layout.set_row_enabled(
            self.__line_color_index, self.__enable_line_color.isChecked()
        )

    def view(self) -> QListView:
        '''return view widget.'''
        return self.__view

    def prefix(self) -> QLineEdit:
        '''Return prefix widget.'''
        return self.__prefix

    def name(self) -> QLineEdit:
        '''Return name widget.'''
        return self.__name

    def suffix(self) -> QLineEdit:
        '''Return suffix widget.'''
        return self.__suffix

    def radius(self) -> QDoubleSpinBox:
        '''Return radius widget.'''
        return self.__radius

    def enable_line_width(self) -> QCheckBox:
        '''Return enable line width widget.'''
        return self.__enable_line_width

    def line_width(self) -> QDoubleSpinBox:
        '''Return line width widget.'''
        return self.__line_width

    def enable_line_color(self) -> QCheckBox:
        '''Return enable line color widget.'''
        return self.__enable_line_color

    def line_color(self) -> widgets.ColorSelectButton:
        '''return line color widget.'''
        return self.__line_color

    def offset_number(self) -> QSpinBox:
        '''Return offset number widget.'''
        return self.__offset_number

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        indexes = self.__view.selectionModel().selectedIndexes()
        if not indexes:
            _logger.error('Select shape style from lsit.')
            return

        model = self.__view.model()
        creator = model.itemFromIndex(indexes[0]).data()
        creator.create(
            self.__prefix.text(),
            self.__name.text(),
            self.__suffix.text(),
            self.__radius.value(),
            (
                self.__line_width.value()
                if self.__enable_line_width.isChecked()
                else None
            ),
            (
                self.__line_color.color()
                if self.__enable_line_color.isChecked()
                else None
            ),
            self.__offset_number.value(),
        )


class MainWindow(widgets.ToolWidget):
    '''Tool main window'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)
        self.setWindowTitle(__product__)
        self.resize(400, 200)

        option_widget: QWidget = self.option_widget()
        main_layout = QGridLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        tab = QTabWidget(self)
        main_layout.addWidget(tab, 0, 0)

        self.__controller_option = ControllerOption(self)
        tab.addTab(self.__controller_option, 'Create')

        self.__color_option = ModifyCvCurveOption(self)
        tab.addTab(self.__color_option, 'Modify CV Curve')

        self.__outliner_option = outliner_color.MainWindow(self)
        self.__outliner_option.menu_bar().hide()
        self.__outliner_option.option_widget().layout().setContentsMargins(
            10, 10, 10, 10
        )
        tab.addTab(self.__outliner_option, 'Outliner')

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        view = self.__controller_option.view()
        view.selectionModel().setCurrentIndex(
            view.model().index(settings.shape.value(), 0),
            QItemSelectionModel.Select,
        )
        self.__controller_option.prefix().setText(settings.prefix.value())
        self.__controller_option.name().setText(settings.name.value())
        self.__controller_option.suffix().setText(settings.suffix.value())
        self.__controller_option.radius().setValue(settings.radius.value())
        self.__controller_option.enable_line_width().setChecked(
            settings.enable_line_width.value()
        )
        self.__controller_option.line_width().setValue(
            settings.line_width.value()
        )
        self.__controller_option.enable_line_color().setChecked(
            settings.enable_line_color.value()
        )
        self.__controller_option.line_color().set_color(
            *settings.line_color.value()
        )
        self.__controller_option.offset_number().setValue(
            settings.offset_number.value()
        )
        self.__controller_option.update_ui()

        self.__color_option.color_option().load_settings()
        self.__color_option.line_width().setValue(settings.line_width.value())

        self.__outliner_option.load_settings()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))

        view = self.__controller_option.view()
        indexes = view.selectionModel().selectedIndexes()
        if indexes:
            settings.shape.set_value(indexes[0].row())
        settings.prefix.set_value(self.__controller_option.prefix().text())
        settings.name.set_value(self.__controller_option.name().text())
        settings.suffix.set_value(self.__controller_option.suffix().text())
        settings.radius.set_value(self.__controller_option.radius().value())
        settings.enable_line_width.set_value(
            self.__controller_option.enable_line_width().isChecked()
        )
        settings.line_width.set_value(
            self.__controller_option.line_width().value()
        )
        settings.enable_line_color.set_value(
            self.__controller_option.enable_line_color().isChecked()
        )
        settings.line_color.set_value(
            self.__controller_option.line_color().color()
        )
        settings.offset_number.set_value(
            self.__controller_option.offset_number().value()
        )
        settings.write()

        self.__color_option.color_option().save_settings()
        self.__outliner_option.save_settings()

    # override
    def reset_settings(self) -> None:
        '''Reset ui settings.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()
        self.__color_option.color_option().reset_settings()
        self.__outliner_option.reset_settings()

    # override
    def about(self) -> None:
        '''Show a about dialog.[override]'''
        widgets.AboutDialog.info(
            self, __product__, __version__, __copyright__, __doc__
        )

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()
        main()


# ==============================================================================
#
# Functions
#
# ==============================================================================
def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
