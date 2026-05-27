# ==============================================================================
#
# Curve Rivet
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING

try:
    from PySide2.QtCore import Qt, Slot
    from PySide2.QtWidgets import QWidget, QSpinBox, QComboBox, QCheckBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot
        from PySide6.QtWidgets import QWidget, QSpinBox, QComboBox, QCheckBox
from maya import cmds
from maya.api import OpenMaya
from ..lib import logger, parser, widgets
from amaterasu.base import dcc

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Curve Rivet'
__version__: str = '1.10'
__doc__ = 'Generates objects along curves that strictly follow surface deformation using matrix constraints.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)

WORLD_DAG_PATH: str = '|'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    node_type: parser.Variant[int] = parser.Variant(
        0
    )  # Transform, Locator, Joint
    divisions: parser.Variant[int] = parser.Variant(4)
    use_up_vector: parser.Variant[bool] = parser.Variant(False)
    up_vector: parser.Variant[list[float]] = parser.Variant([0.0, 1.0, 0.0])


class MainWindow(widgets.StandardToolWidget):
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
        self.__main_layout: widgets.FormLayout = widgets.FormLayout(
            option_widget
        )

        self.__node_type: QComboBox = QComboBox(self)
        self.__node_type.addItems(['Transform', 'Locator', 'Joint'])
        self.__node_type.setMinimumWidth(70)
        self.__main_layout.addRow('Node Type', self.__node_type)

        self.__divisions: QSpinBox = QSpinBox(self)
        self.__divisions.setRange(2, 999)
        self.__divisions.setMinimumWidth(70)
        self.__main_layout.addRow(
            widgets.FormLabel('Divisions'), self.__divisions
        )

        self.__main_layout.addRow(widgets.HorizontalLine(self))

        self.__use_up_vector: QCheckBox = QCheckBox('Use Up Vector', self)
        self.__use_up_vector.clicked.connect(self.set_valid_options)
        self.__main_layout.addRow('', self.__use_up_vector)

        self.__up_vector: widgets.ThreeDoubleSpinBox = (
            widgets.ThreeDoubleSpinBox(self)
        )
        self.__main_layout.addRow(
            widgets.FormLabel('Up Vector'), self.__up_vector
        )
        self.__up_vector_index: int = self.__main_layout.row_id()

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__node_type.setCurrentIndex(settings.node_type.value())
        self.__divisions.setValue(settings.divisions.value())
        self.__use_up_vector.setChecked(settings.use_up_vector.value())
        self.__up_vector.set_value(*settings.up_vector.value())
        self.set_valid_options()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.node_type.set_value(self.__node_type.currentIndex())
        settings.divisions.set_value(self.__divisions.value())
        settings.use_up_vector.set_value(self.__use_up_vector.isChecked())
        settings.up_vector.set_value(self.__up_vector.value())
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

    @Slot()
    def set_valid_options(self) -> None:
        '''Synchronize with valid options.'''
        self.__main_layout.set_row_enabled(
            self.__up_vector_index, self.__use_up_vector.isChecked()
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
def __get_curve_fn(node: str) -> OpenMaya.MFnNurbsCurve:
    '''Return MFnNurbsCurve object.'''
    selection_list: OpenMaya.MSelectionList = OpenMaya.MSelectionList()
    selection_list.add(node)
    return OpenMaya.MFnNurbsCurve(selection_list.getDagPath(0))


def apply(
    curves: list[str],
    node_type: int = 0,
    divisions: int = 4,
    use_up_vector: bool = False,
    up_vector: list[float] | None = None,
) -> bool:
    '''Generates objects along curves that strictly follow surface deformation using matrix constraints.'''
    if up_vector is None:
        up_vector = [0.0, 1.0, 0.0]

    for curve in curves:
        curve_shapes: list[str] = (
            cmds.listRelatives(curve, shapes=True, path=True) or []
        )
        if not curve_shapes:
            continue

        curve_parents: list[str] = (
            cmds.listRelatives(curve, parent=True, path=True) or []
        )
        curve_parent: str = ''
        if curve_parents:
            curve_parent = curve_parents[0]

        curve_shape: str = curve_shapes[0]

        base_name: str = curve.split('|')[-1]
        base_name = base_name.split('_')[0]

        # Space
        curve_space: str = cmds.createNode(
            'transform', name=f'{base_name}Space_null'
        )
        if curve_parent:
            curve_space = cmds.parent(curve_space, curve_parent)[0]

        cmds.matchTransform(
            curve_space, curve, position=True, rotation=True, scale=True
        )

        # Space Matrix
        space_mtx: str = cmds.createNode(
            'multMatrix', name=f'{base_name}Space_multMtx'
        )
        cmds.connectAttr(f'{curve}.matrix', f'{space_mtx}.matrixIn[0]')
        cmds.connectAttr(f'{curve}.parentMatrix[0]', f'{space_mtx}.matrixIn[1]')
        cmds.connectAttr(
            f'{curve_space}.parentInverseMatrix[0]',
            f'{space_mtx}.matrixIn[2]',
        )

        # Space Decompose
        space_decompose: str = cmds.createNode(
            'decomposeMatrix', name=f'{base_name}Space_decomposeMtx'
        )
        cmds.connectAttr(
            f'{space_mtx}.matrixSum', f'{space_decompose}.inputMatrix'
        )
        cmds.connectAttr(
            f'{space_decompose}.outputTranslate', f'{curve_space}.translate'
        )
        cmds.connectAttr(
            f'{space_decompose}.outputRotate', f'{curve_space}.rotate'
        )
        cmds.connectAttr(
            f'{space_decompose}.outputScale', f'{curve_space}.scale'
        )
        cmds.connectAttr(
            f'{space_decompose}.outputShear', f'{curve_space}.shear'
        )

        curve_fn: OpenMaya.MFnNurbsCurve = __get_curve_fn(curve)
        length: float = curve_fn.length()
        controllers: list[str] = []
        for i in range(divisions):

            # Curve Info
            curve_info: str = cmds.createNode(
                'pointOnCurveInfo', name=f'{base_name}P{i}_poci'
            )
            cmds.setAttr(
                f'{curve_info}.parameter',
                curve_fn.findParamFromLength(length / (divisions - 1) * i),
            )
            cmds.connectAttr(f'{curve_shape}.local', f'{curve_info}.inputCurve')

            # --- Matrix Construction Logic ---
            mtx_4x4: str = cmds.createNode(
                'fourByFourMatrix', name=f'{base_name}P{i}_4x4mtx'
            )

            # Position
            cmds.connectAttr(f'{curve_info}.positionX', f'{mtx_4x4}.in30')
            cmds.connectAttr(f'{curve_info}.positionY', f'{mtx_4x4}.in31')
            cmds.connectAttr(f'{curve_info}.positionZ', f'{mtx_4x4}.in32')

            # Tangent (X-Axis)
            cmds.connectAttr(
                f'{curve_info}.normalizedTangentX', f'{mtx_4x4}.in00'
            )
            cmds.connectAttr(
                f'{curve_info}.normalizedTangentY', f'{mtx_4x4}.in01'
            )
            cmds.connectAttr(
                f'{curve_info}.normalizedTangentZ', f'{mtx_4x4}.in02'
            )

            if use_up_vector:
                # Binormal = Tangent x UpVector
                binormal = cmds.createNode(
                    'vectorProduct', name=f'{base_name}P{i}Binormal_vp'
                )
                cmds.setAttr(f'{binormal}.operation', 2)
                cmds.setAttr(f'{binormal}.normalizeOutput', True)
                cmds.setAttr(f'{binormal}.input2', *up_vector)
                cmds.connectAttr(
                    f'{curve_info}.normalizedTangent', f'{binormal}.input1'
                )

                # Normal = Binormal x Tangent
                vp_normal = cmds.createNode(
                    'vectorProduct', name=f'{base_name}P{i}Normal_vp'
                )
                cmds.setAttr(f'{vp_normal}.operation', 2)
                cmds.setAttr(f'{vp_normal}.normalizeOutput', True)

                cmds.connectAttr(f'{binormal}.output', f'{vp_normal}.input1')
                cmds.connectAttr(
                    f'{curve_info}.normalizedTangent', f'{vp_normal}.input2'
                )

                # Normal (Y-Axis)
                cmds.connectAttr(f'{vp_normal}.outputX', f'{mtx_4x4}.in10')
                cmds.connectAttr(f'{vp_normal}.outputY', f'{mtx_4x4}.in11')
                cmds.connectAttr(f'{vp_normal}.outputZ', f'{mtx_4x4}.in12')

                # Binormal (Z-Axis)
                cmds.connectAttr(f'{binormal}.outputX', f'{mtx_4x4}.in20')
                cmds.connectAttr(f'{binormal}.outputY', f'{mtx_4x4}.in21')
                cmds.connectAttr(f'{binormal}.outputZ', f'{mtx_4x4}.in22')

            else:
                # Binormal
                binormal = cmds.createNode(
                    'vectorProduct', name=f'{base_name}P{i}Binormal_vp'
                )
                cmds.setAttr(f'{binormal}.operation', 2)
                cmds.setAttr(f'{binormal}.normalizeOutput', True)
                cmds.connectAttr(
                    f'{curve_info}.normalizedTangent', f'{binormal}.input1'
                )
                cmds.connectAttr(
                    f'{curve_info}.normalizedNormal', f'{binormal}.input2'
                )

                # Normal (Y-Axis)
                cmds.connectAttr(
                    f'{curve_info}.normalizedNormalX', f'{mtx_4x4}.in10'
                )
                cmds.connectAttr(
                    f'{curve_info}.normalizedNormalY', f'{mtx_4x4}.in11'
                )
                cmds.connectAttr(
                    f'{curve_info}.normalizedNormalZ', f'{mtx_4x4}.in12'
                )

                # Binormal (Z-Axis)
                cmds.connectAttr(f'{binormal}.outputX', f'{mtx_4x4}.in20')
                cmds.connectAttr(f'{binormal}.outputY', f'{mtx_4x4}.in21')
                cmds.connectAttr(f'{binormal}.outputZ', f'{mtx_4x4}.in22')

            # Decompose
            decompose_mtx: str = cmds.createNode(
                'decomposeMatrix', name=f'{base_name}P{i}_decompose_mtx'
            )
            cmds.connectAttr(
                f'{mtx_4x4}.output', f'{decompose_mtx}.inputMatrix'
            )

            # Controller
            controller: str = ''
            if node_type == 0:
                controller = cmds.createNode(
                    'transform', name=f'{base_name}P{i}_null'
                )
                cmds.setAttr(f'{controller}.displayLocalAxis', True)

            elif node_type == 1:
                controller = cmds.spaceLocator(name=f'{base_name}P{i}_loc')[0]

            else:
                controller = cmds.joint(name=f'{base_name}P{i}_jnt')
                end_joint: str = cmds.joint(name=f'{base_name}P{i}End_jnt')
                cmds.setAttr(f'{end_joint}.translateX', 10)
                cmds.setAttr(f'{end_joint}.visibility', False)

            controller = cmds.parent(controller, curve_space)[0]
            if node_type == 2:
                cmds.setAttr(
                    f'{controller}.jointOrient', 0, 0, 0, type='double3'
                )
            cmds.connectAttr(
                f'{decompose_mtx}.outputTranslate', f'{controller}.translate'
            )
            cmds.connectAttr(
                f'{decompose_mtx}.outputRotate', f'{controller}.rotate'
            )
            cmds.connectAttr(
                f'{decompose_mtx}.outputScale', f'{controller}.scale'
            )
            cmds.connectAttr(
                f'{decompose_mtx}.outputShear', f'{controller}.shear'
            )
            controllers.append(controller)

        # Clean up
        # history_visibility.main([curve_space, *controllers], 0)
        dcc.node.hide_history([curve_space, *controllers])

    return True


def option(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main() -> None:
    '''Do it.'''
    nodes: list[str] = cmds.ls(selection=True)
    if not nodes:
        _logger.error('Select curves to create curve constraint.')
        return

    settings: Settings = Settings.instance(__name__, True)
    result: bool = apply(
        nodes,
        settings.node_type.value(),
        settings.divisions.value(),
        settings.use_up_vector.value(),
        settings.up_vector.value(),
    )
    if result:
        cmds.select(*nodes)
        _logger.info('Done.')
