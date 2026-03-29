# ==============================================================================
#
# Create Motion Curve
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING

try:
    from PySide2.QtCore import Qt, Slot
    from PySide2.QtWidgets import QWidget, QSpinBox, QDoubleSpinBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot
        from PySide6.QtWidgets import QWidget, QSpinBox, QDoubleSpinBox
from maya import cmds
from ..lib import logger, parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Create Motion Curve'
__version__: str = '1.10'
__doc__ = 'Create animation tail with CV curve.'
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
    method: parser.Variant[int] = parser.Variant(0)
    start_frame: parser.Variant[int] = parser.Variant(1)
    end_frame: parser.Variant[int] = parser.Variant(10)
    step_frame: parser.Variant[float] = parser.Variant(1.0)


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

        self.__method: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__method.set_labels(('Time Range', 'Start/End'))
        self.__method.button_group().idClicked.connect(self.set_valid_options)
        main_layout.addRow(widgets.FormLabel('Method'), self.__method)

        self.__start_frame: QSpinBox = QSpinBox(self)
        self.__start_frame.setRange(-9999, 9999)
        self.__start_frame.setMinimumWidth(70)
        self.__start_frame.setButtonSymbols(QSpinBox.NoButtons)
        main_layout.addRow(widgets.FormLabel('Start Frame'), self.__start_frame)
        self.__start_frame_index: int = main_layout.row_id()

        self.__end_frame: QSpinBox = QSpinBox(self)
        self.__end_frame.setRange(-9999, 9999)
        self.__end_frame.setMinimumWidth(70)
        self.__end_frame.setButtonSymbols(QSpinBox.NoButtons)
        main_layout.addRow(widgets.FormLabel('End Frame'), self.__end_frame)
        self.__end_frame_index: int = main_layout.row_id()

        self.__step_frame: QDoubleSpinBox = QDoubleSpinBox(self)
        self.__step_frame.setRange(0.001, 9999)
        self.__step_frame.setDecimals(3)
        self.__step_frame.setMinimumWidth(70)
        self.__step_frame.setButtonSymbols(QSpinBox.NoButtons)
        main_layout.addRow(widgets.FormLabel('Step Frame'), self.__step_frame)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__method.set_check_id(settings.method.value())
        self.__start_frame.setValue(settings.start_frame.value())
        self.__end_frame.setValue(settings.end_frame.value())
        self.__step_frame.setValue(settings.step_frame.value())
        self.set_valid_options()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.method.set_value(self.__method.check_id())
        settings.start_frame.set_value(self.__start_frame.value())
        settings.end_frame.set_value(self.__end_frame.value())
        settings.step_frame.set_value(self.__step_frame.value())
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
        layout: widgets.FormLayout = self.option_widget().layout()
        layout.set_row_enabled(
            self.__start_frame_index, self.__method.check_id() != 0
        )
        layout.set_row_enabled(
            self.__end_frame_index, self.__method.check_id() != 0
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
def apply(
    nodes: list[str],
    start_frame: int = 1,
    end_frame: int = 10,
    step_frame: float = 1,
    group_name: str = 'motion_curve_grp',
) -> bool:
    '''Create animation tail with CV curve from seleciton.'''
    if not cmds.objExists(group_name):
        group_name = cmds.group(name=group_name, empty=True)

    my_time: float = cmds.currentTime(query=True)
    cmds.currentTime(start_frame, update=True)
    curves: list[str] = []
    for node in nodes:
        point: list[float] = cmds.xform(
            node, query=True, worldSpace=True, translation=True
        )
        cleanup_name: str = node.replace('[', '')
        cleanup_name = cleanup_name.replace(']', '')
        cleanup_name = cleanup_name.replace('.', '_')
        curve: str = cmds.curve(name=f'{cleanup_name}_crv', point=point)
        curve = cmds.parent(curve, group_name)[0]
        curves.append(curve)

    current_frame = float(start_frame)
    while current_frame < end_frame:
        current_frame = current_frame + step_frame
        cmds.currentTime(current_frame, update=True)
        for i, node in enumerate(nodes):
            point = cmds.xform(
                node, query=True, worldSpace=True, translation=True
            )
            cmds.curve(curves[i], append=True, point=point)

    cmds.currentTime(my_time, update=True)
    return True


def option(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection: list[str] = cmds.ls(selection=True, flatten=True)
    if not selection:
        _logger.error('Select objects or components to create motion curve.')
        return

    settings: Settings = Settings.instance(__name__, True)
    start_frame: int = settings.start_frame.value()
    end_frame: int = settings.end_frame.value()
    if settings.method.value() == 0:
        start_frame = cmds.playbackOptions(query=True, min=True)
        end_frame = cmds.playbackOptions(query=True, max=True)

    result: bool = apply(
        selection,
        start_frame,
        end_frame,
        settings.step_frame.value(),
    )
    if result:
        _logger.info('Done.')
