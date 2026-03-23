# ==============================================================================
#
# Round Off Time
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QWidget
from maya import cmds
from ..lib import logger, parser, utility, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Round Off Time'
__version__: str = '1.20'
__doc__ = 'Round off time of keyframe from selected node.'
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
    hierarchy: parser.Variant[int] = parser.Variant(1)


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

        self.__hierarchy: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__hierarchy.set_labels(('Selected', 'Below'))
        main_layout.addRow(widgets.FormLabel('Hierarchy'), self.__hierarchy)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__hierarchy.set_check_id(settings.hierarchy.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.hierarchy.set_value(self.__hierarchy.check_id())
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
def apply(nodes: list[str]) -> bool:
    '''Insert keyframe'''
    for node in nodes:
        connected_curves: list[str] = utility.get_anim_curves(node)
        for curve in connected_curves:
            times: list[float] = cmds.keyframe(
                curve, query=True, timeChange=True
            )
            for time in times:
                if int(time) == time:
                    continue

                cmds.setKeyframe(curve, insert=True, time=round(time))
                cmds.cutKey(curve, time=(time, time))

    return True


def option(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select node to round off keyframe time.')
        return

    settings: Settings = Settings.instance(__name__, True)
    if settings.hierarchy.value():
        temp_selection: list[str] = []
        for node in selection:
            children: list[str] = (
                cmds.listRelatives(
                    node, children=True, allDescendents=True, path=True
                )
                or []
            )
            children.reverse()
            temp_selection.append(node)
            temp_selection.extend(children)

        selection = temp_selection

    result: bool = apply(selection)
    if result:
        _logger.info('Done.')
