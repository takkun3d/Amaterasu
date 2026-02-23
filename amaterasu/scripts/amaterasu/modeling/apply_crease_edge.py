# ==============================================================================
#
# Apply Crease Edge
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget, QDoubleSpinBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QWidget, QDoubleSpinBox
from maya import cmds
from ..lib import parser, widgets, utility


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Apply Crease Edge'
__version__: str = '1.20'
__doc__ = 'Apply Crease Edge from hard edge.'
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
    crease_value: parser.Variant[float] = parser.Variant(2.0)


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

        self.__crease = QDoubleSpinBox(self)
        self.__crease.setRange(0.0, 2.0)
        self.__crease.setMinimumWidth(70)
        self.__crease.setButtonSymbols(QDoubleSpinBox.NoButtons)
        main_layout.addRow(widgets.FormLabel('Crease Value'), self.__crease)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__crease.setValue(settings.crease_value.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.crease_value.set_value(self.__crease.value())
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
        '''Apply'''
        self.save_settings()
        main()


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(edges: list[str], crease_value: float) -> bool:
    '''Crease edge from hard edge.'''
    components: dict[str, list[str]] = utility.to_each_geometry(edges)
    for geometry in components:
        set_crease_edges: list[str] = []
        remove_crease_edges: list[str] = []
        for edge in components[geometry]:
            if utility.is_hard_edge(edge):
                set_crease_edges.append(edge)
            else:
                remove_crease_edges.append(edge)

        if set_crease_edges:
            cmds.polyCrease(
                *set_crease_edges, value=crease_value, createHistory=False
            )

        if remove_crease_edges:
            cmds.polyCrease(*remove_crease_edges, value=0, createHistory=False)

    return True


def option(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection: list[str] = cmds.ls(selection=True)
    edges: list[str] = cmds.filterExpand(selectionMask=32)
    if not edges:
        selection = cmds.ls(selection=True, flatten=True)
        if not selection:
            _logger.error('Select objects or components to set crease.')
            cmds.select(*selection)
            return

        edges = utility.to_edge(selection)
        if not edges:
            _logger.error('Failed to get polygon edges.')
            cmds.select(*selection)
            return

    settings: Settings = Settings.instance(__name__, True)
    result: bool = apply(edges, settings.crease_value.value())
    if result:
        _logger.info('Done.')

    cmds.select(*selection)
