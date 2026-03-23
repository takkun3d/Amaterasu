# ==============================================================================
#
# Mirror Geometry
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
from maya import cmds

try:
    from PySide2.QtCore import Qt, Slot
    from PySide2.QtWidgets import (
        QWidget,
        QCheckBox,
        QDoubleSpinBox,
        QComboBox,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot
        from PySide6.QtWidgets import (
            QWidget,
            QCheckBox,
            QDoubleSpinBox,
            QComboBox,
        )
from ..lib import logger, parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Mirror Geometry'
__version__: str = '1.10'
__doc__ = 'Mirror geometry easily generates inverted meshes.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    cut_mesh: parser.Variant[bool] = parser.Variant(True)
    axis: parser.Variant[int] = parser.Variant(0)
    direction: parser.Variant[int] = parser.Variant(1)
    merge: parser.Variant[bool] = parser.Variant(True)
    soft_edge: parser.Variant[bool] = parser.Variant(True)
    threshold: parser.Variant[float] = parser.Variant(0.001)
    flip_uvs: parser.Variant[bool] = parser.Variant(True)
    uv_direction: parser.Variant[int] = parser.Variant(2)


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
        main_layout: widgets.FormLayout = widgets.FormLayout(option_widget)

        main_layout.addRow(
            widgets.FrameWidget('Mirror Options', False, False, self)
        )

        self.__cut_mesh: QCheckBox = QCheckBox(self)
        self.__cut_mesh.setText('Cut Geometry')
        main_layout.addRow('', self.__cut_mesh)

        self.__axis: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__axis.set_labels(('X', 'Y', 'Z'))
        main_layout.addRow(widgets.FormLabel('Axis'), self.__axis)

        self.__direction: QComboBox = QComboBox(self)
        self.__direction.addItem('+')
        self.__direction.addItem('-')
        main_layout.addRow(widgets.FormLabel('Direction'), self.__direction)

        main_layout.addRow(
            widgets.FrameWidget('Merge Options', False, False, self)
        )

        self.__merge: QCheckBox = QCheckBox(self)
        self.__merge.setText('Merge')
        self.__merge.clicked.connect(self.set_valid_options)
        main_layout.addRow('', self.__merge)

        self.__soft_edge: QCheckBox = QCheckBox(self)
        self.__soft_edge.setText('Apply Soft Edge')
        main_layout.addRow('', self.__soft_edge)
        self.__soft_edge_id: int = main_layout.row_id()

        self.__threshold: QDoubleSpinBox = QDoubleSpinBox(self)
        self.__threshold.setRange(0, 999)
        self.__threshold.setDecimals(5)
        self.__threshold.setButtonSymbols(QDoubleSpinBox.NoButtons)
        main_layout.addRow(widgets.FormLabel('Threshold'), self.__threshold)
        self.__threshold_id: int = main_layout.row_id()

        main_layout.addRow(
            widgets.FrameWidget('UV Options', False, False, self)
        )

        self.__flip_uvs: QCheckBox = QCheckBox(self)
        self.__flip_uvs.setText('Flip UVs')
        self.__flip_uvs.clicked.connect(self.set_valid_options)
        main_layout.addRow('', self.__flip_uvs)

        self.__uv_direction: QComboBox = QComboBox(self)
        self.__uv_direction.addItem('Local U')
        self.__uv_direction.addItem('Local V')
        self.__uv_direction.addItem('World U')
        self.__uv_direction.addItem('World V')
        main_layout.addRow(widgets.FormLabel('Direction'), self.__uv_direction)
        self.__uv_direction_id: int = main_layout.row_id()

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.__cut_mesh.setChecked(settings.cut_mesh.value())
        self.__axis.set_check_id(settings.axis.value())
        self.__direction.setCurrentIndex(settings.direction.value())
        self.__merge.setChecked(settings.merge.value())
        self.__soft_edge.setChecked(settings.soft_edge.value())
        self.__threshold.setValue(settings.threshold.value())
        self.__flip_uvs.setChecked(settings.flip_uvs.value())
        self.__uv_direction.setCurrentIndex(settings.uv_direction.value())
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.set_valid_options()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.cut_mesh.set_value(self.__cut_mesh.isChecked())
        settings.axis.set_value(self.__axis.check_id())
        settings.direction.set_value(self.__direction.currentIndex())
        settings.merge.set_value(self.__merge.isChecked())
        settings.soft_edge.set_value(self.__soft_edge.isChecked())
        settings.threshold.set_value(self.__threshold.value())
        settings.flip_uvs.set_value(self.__flip_uvs.isChecked())
        settings.uv_direction.set_value(self.__uv_direction.currentIndex())
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
    def apply(self) -> None:
        '''Apply[override]'''
        self.save_settings()
        main()

    @Slot()
    def set_valid_options(self) -> None:
        '''Synchronize with valid options.'''
        layout: widgets.FormLayout = self.option_widget().layout()
        layout.set_row_enabled(self.__soft_edge_id, self.__merge.isChecked())
        layout.set_row_enabled(self.__threshold_id, self.__merge.isChecked())
        layout.set_row_enabled(
            self.__uv_direction_id, self.__flip_uvs.isChecked()
        )


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(
    nodes: list[str],
    cut_mesh: bool = True,
    axis: int = 0,  # x=0, y=1, z=2
    direction: int = 1,  # Positive(+)=0, Negative(-)=1
    merge: bool = True,
    soft_edge: bool = True,
    threshold: float = 0.001,
    flip_uvs: bool = False,
    uv_direction: int = 0,
) -> bool:
    '''Invert selected polygons.'''
    smoothing_angle: float = 180.0 if soft_edge else 0.0
    uv_direction = uv_direction + 1 if flip_uvs else 0
    for node in nodes:
        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        if not shapes:
            _logger.warning('This has no shape : %s', node)
            continue

        shape: str = shapes[0]
        if cmds.objectType(shape) != 'mesh':
            _logger.warning('Does not match mesh : %s', shape)
            continue

        cmds.polyMirrorFace(
            shape,
            cutMesh=cut_mesh,
            axis=axis,
            axisDirection=direction,
            mirrorAxis=1,  # object
            mirrorPosition=0.0,
            mergeMode=merge,
            mergeThresholdType=1,  # Custom
            mergeThreshold=threshold,
            smoothingAngle=smoothing_angle,
            flipUVs=uv_direction,
            constructionHistory=False,
        )

    cmds.select(*nodes)
    return True


def option(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection = cmds.ls(selection=True, type='transform')
    if not selection:
        _logger.error('Select polygon to mirror geometry.')
        return

    settings: Settings = Settings.instance(__name__, True)
    result: bool = apply(
        selection,
        settings.cut_mesh.value(),
        settings.axis.value(),
        settings.direction.value(),
        settings.merge.value(),
        settings.soft_edge.value(),
        settings.threshold.value(),
        settings.flip_uvs.value(),
        settings.uv_direction.value(),
    )
    if result:
        _logger.info('Done.')
