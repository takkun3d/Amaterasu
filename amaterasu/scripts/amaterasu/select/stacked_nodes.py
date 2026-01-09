# ==============================================================================
#
# Select Stacked Nodes
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import itertools

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QWidget
from maya import cmds
from ..lib import parser, widgets

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Select Stacked Nodes'
__version__: str = '1.10'
__doc__ = 'Select stacked nodes.'
__copyright__ = 'Copyright(c) 2020-2025 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    nth: parser.Variant[int] = parser.Variant(1)
    mode: parser.Variant[int] = parser.Variant(1)


class MainWindow(widgets.StandardToolWidget):
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
        main_layout: widgets.FormLayout = widgets.FormLayout(option_widget)

        self.__mode: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__mode.set_labels(('ALL', '1-Last'))
        main_layout.addRow(widgets.FormLabel('Mode'), self.__mode)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.__mode.set_check_id(settings.mode.value())
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.mode.set_value(self.__mode.check_id())
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


# ==============================================================================
#
# Functions
#
# ==============================================================================
def option() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()


def apply(targets: list[str], seek: int = 1) -> None:
    '''Select stacked nodes.'''

    # Create data from selected nodes or Transforms in the scene.
    # [(geometry, matrix), ...]
    data_list: list[tuple[str, list[float]]] = [
        (
            x,
            [
                round(y, 15)
                for y in cmds.xform(
                    x, query=True, boundingBox=True, worldSpace=True
                )
            ],
        )
        for x in targets
        if cmds.listRelatives(x, shapes=True, path=True)
    ]

    # Group geometries by their matrix
    # [[(geometry, matrix), ...], ...]
    geometries_by_matrix: list[tuple[str, list[float]]] = [
        y
        for y in [
            list(g)
            for k, g in itertools.groupby(
                sorted(data_list, key=lambda x: x[1]), lambda x: x[1]
            )
        ]
        if len(y) > 1
    ]

    # Extract selected nodes from the specified position.
    # [geometry, ...]
    selection_list: list[str] = [
        y[0] for x in geometries_by_matrix for y in x[seek:]
    ]

    if selection_list:
        cmds.select(*selection_list)
        _logger.info('Done.')
    else:
        _logger.info('There were no stacked nodes in this scene.')


def main() -> None:
    '''Do it.'''
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        selection = cmds.ls(transforms=True)

    settings: Settings = Settings.instance(__name__, True)
    apply(selection, settings.mode.value())
