# ==============================================================================
#
# Remove Half
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget, QComboBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QWidget, QComboBox
from maya.OpenMaya import (
    MGlobal,
    MObject,
    MDagPath,
    MPoint,
    MSpace,
    MSelectionList,
    MItSelectionList,
    MItMeshPolygon,
    MFnTransform,
)
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Remove Half'
__version__: str = '1.20'
__doc__ = 'Remove half from selected node.'
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
    axis: parser.Variant[int] = parser.Variant(0)
    direction: parser.Variant[int] = parser.Variant(1)
    space: parser.Variant[int] = parser.Variant(1)


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

        self.__axis: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__axis.set_labels(('X', 'Y', 'Z'))
        main_layout.addRow(widgets.FormLabel('Axis'), self.__axis)

        self.__direction: QComboBox = QComboBox(self)
        self.__direction.addItem('+')
        self.__direction.addItem('-')
        main_layout.addRow(widgets.FormLabel('Direction'), self.__direction)

        self.__space: QComboBox = QComboBox(self)
        self.__space.addItem('Local')
        self.__space.addItem('World')
        main_layout.addRow(widgets.FormLabel('Space'), self.__space)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__axis.set_check_id(settings.axis.value())
        self.__direction.setCurrentIndex(settings.direction.value())
        self.__space.setCurrentIndex(settings.space.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.axis.set_value(self.__axis.check_id())
        settings.direction.set_value(self.__direction.currentIndex())
        settings.space.set_value(self.__space.currentIndex())
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
def apply(
    selection: MSelectionList, axis: int = 0, direction: int = 1, space: int = 0
) -> bool:
    '''Remove half.'''
    select_iter: MItSelectionList = MItSelectionList(selection)
    dagPath: MDagPath = MDagPath()
    component: MObject = MObject()
    delete_component: MSelectionList = MSelectionList()
    while not select_iter.isDone():
        select_iter.getDagPath(dagPath, component)
        poly_iter: MItMeshPolygon = MItMeshPolygon(dagPath, component)
        center: MPoint = MPoint(0, 0, 0)
        if space == 0:
            trans_fn: MFnTransform = MFnTransform(dagPath)
            center = trans_fn.rotatePivot(MSpace.kWorld)

        while not poly_iter.isDone():
            face_center: MPoint = poly_iter.center(MSpace.kWorld)
            flag: bool = False
            if axis == 0 and direction == 1:
                flag = center.x > face_center.x

            elif axis == 1 and direction == 1:
                flag = center.y > face_center.y

            elif axis == 2 and direction == 1:
                flag = center.z > face_center.z

            elif axis == 0 and direction == 0:
                flag = center.x < face_center.x

            elif axis == 1 and direction == 0:
                flag = center.y < face_center.y

            elif axis == 2 and direction == 0:
                flag = center.z < face_center.z

            if flag:
                delete_component.add(dagPath, poly_iter.currentItem())

            poly_iter.next()
        select_iter.next()

    if delete_component.isEmpty():
        return False

    MGlobal.selectCommand(delete_component)
    MGlobal.executeCommand('delete', False, True)
    MGlobal.selectCommand(selection)
    return True


def option(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection: MSelectionList = MSelectionList()
    MGlobal.getActiveSelectionList(selection)
    if selection.isEmpty():
        _logger.error('Select polygon to remove half faces.')
        return

    settings: Settings = Settings.instance(__name__, True)
    apply(
        selection,
        settings.axis.value(),
        settings.direction.value(),
        settings.space.value(),
    )
    _logger.info('Done.')
