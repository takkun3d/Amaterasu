# ==============================================================================
#
# Select Each Nth Edges
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget, QSpinBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QWidget, QSpinBox
from maya import cmds
from ..lib import parser, widgets, utility


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Select Each Nth Edges'
__version__: str = '1.00'
__doc__ = 'Select each Nth edges.'
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
        main_layout.rowCount()

        self.__nth = QSpinBox(self)
        self.__nth.setRange(1, 99)
        self.__nth.setButtonSymbols(QSpinBox.NoButtons)
        self.__nth.setMinimumWidth(70)
        main_layout.addRow(widgets.FormLabel('N th'), self.__nth)

        self.__mode: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__mode.set_labels(('Loop', 'Ring'))
        main_layout.addRow(widgets.FormLabel('Mode'), self.__mode)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.__nth.setValue(settings.nth.value())
        self.__mode.set_check_id(settings.mode.value())
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.nth.set_value(self.__nth.value())
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
def apply(edges: list[str], nth: int = 1, mode: int = 1) -> bool:
    '''Select each Nth edges.'''
    nth += 1
    edge_dict: dict[str, list[str]] = utility.to_each_geometry(edges)
    result_edge_list: list[str] = []
    for key, items in edge_dict.items():
        for edge in items:
            id_ = int(utility.component_id(edge)[0])
            edge_loop_ids: list[int] = cmds.polySelect(
                key, noSelection=True, edgeLoop=id_
            )
            edge_ring_ids: list[int] = cmds.polySelect(
                key, noSelection=True, edgeRing=id_
            )

            first_loop_list_index: int = edge_loop_ids.index(id_)
            first_ring_list_index: int = edge_ring_ids.index(id_)

            if mode in (0, 2):
                for i in range(first_loop_list_index, len(edge_loop_ids), nth):
                    result_edge_list.append(f'{key}.e[{edge_loop_ids[i]}]')

                for i in range(first_loop_list_index, 0, nth * -1):
                    result_edge_list.append(f'{key}.e[{edge_loop_ids[i]}]')

            if mode in (1, 2):
                for i in range(first_ring_list_index, len(edge_ring_ids), nth):
                    result_edge_list.append(f'{key}.e[{edge_ring_ids[i]}]')

                for i in range(first_ring_list_index, 0, nth * -1):
                    result_edge_list.append(f'{key}.e[{edge_ring_ids[i]}]')

    result_edge_list = list(set(result_edge_list))
    cmds.select(*result_edge_list, replace=True)
    return True


def option() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection = cmds.filterExpand(selectionMask=32)
    if not selection:
        _logger.error('Select polygon edges.')
        return

    settings: Settings = Settings.instance(__name__, True)
    result: bool = apply(selection, settings.nth.value(), settings.mode.value())
    if result:
        _logger.info('Done.')
