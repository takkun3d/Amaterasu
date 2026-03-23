# ==============================================================================
#
# Mirror Polygon
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
from maya import cmds

try:
    from PySide2.QtCore import Qt, Slot
    from PySide2.QtWidgets import QWidget, QLineEdit, QCheckBox, QComboBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Slot
        from PySide6.QtWidgets import QWidget, QLineEdit, QCheckBox, QComboBox
from ..lib import logger, parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Mirror Polygon'
__version__: str = '1.30'
__doc__ = 'Mirror polygon easily generates inverted meshes.'
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
    axis: parser.Variant[int] = parser.Variant(0)
    flip_uvs: parser.Variant[bool] = parser.Variant(True)
    uv_direction: parser.Variant[int] = parser.Variant(2)
    search: parser.Variant[str] = parser.Variant('_L_')
    replace: parser.Variant[str] = parser.Variant('_R_')


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
        self.resize(400, 300)

        option_widget: QWidget = self.option_widget()
        main_layout: widgets.FormLayout = widgets.FormLayout(option_widget)

        main_layout.addRow(
            widgets.FrameWidget('Mirror Options', False, False, self)
        )

        self.__axis: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__axis.set_labels(('X', 'Y', 'Z'))
        main_layout.addRow(widgets.FormLabel('Axis'), self.__axis)

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

        main_layout.addRow(
            widgets.FrameWidget('Rename Options', False, False, self)
        )

        self.__search: QLineEdit = QLineEdit(self)
        main_layout.addRow(widgets.FormLabel('Search'), self.__search)

        self.__replace: QLineEdit = QLineEdit(self)
        main_layout.addRow(widgets.FormLabel('Replace'), self.__replace)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.__axis.set_check_id(settings.axis.value())
        self.__flip_uvs.setChecked(settings.flip_uvs.value())
        self.__uv_direction.setCurrentIndex(settings.uv_direction.value())
        self.__search.setText(settings.search.value())
        self.__replace.setText(settings.replace.value())
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.set_valid_options()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.axis.set_value(self.__axis.check_id())
        settings.flip_uvs.set_value(self.__flip_uvs.isChecked())
        settings.uv_direction.set_value(self.__uv_direction.currentIndex())
        settings.search.set_value(self.__search.text())
        settings.replace.set_value(self.__replace.text())
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

    @Slot()
    def set_valid_options(self) -> None:
        '''Synchronize with valid options.'''
        layout: widgets.FormLayout = self.option_widget().layout()
        layout.set_row_enabled(
            self.__uv_direction_id, self.__flip_uvs.isChecked()
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
def apply(
    nodes: list[str],
    axis: int = 0,  # x=0, y=1, z=2
    flip_uvs: bool = False,
    uv_direction: int = 0,  # 0=Local U, 1=Local V, 2=World U, 3=World V
    search: str = '',
    replace: str = '',
) -> list[str]:
    '''Invert selected polygons.'''
    mirror_args: list[list[int]] = [[-1, 1, 1], [1, -1, 1], [1, 1, -1]]
    new_nodes: list[str] = []
    for node in nodes:
        shapes: list[str] = (
            cmds.listRelatives(node, shapes=True, path=True) or []
        )
        if not shapes:
            continue

        shape: str = shapes[0]
        if cmds.objectType(shape) != 'mesh':
            continue

        new_node: str = cmds.duplicate(node, returnRootsOnly=True)[0]
        cmds.scale(
            mirror_args[axis][0],
            mirror_args[axis][1],
            mirror_args[axis][2],
            new_node,
            relative=True,
        )
        try:
            cmds.makeIdentity(
                new_node,
                apply=True,
                translate=True,
                rotate=True,
                scale=True,
                normal=False,
            )
        except RuntimeError:
            _logger.error('Failed to freeze transform : %s', new_node)
            cmds.delete(new_node)
            continue

        cmds.polyNormal(
            new_node,
            normalMode=0,
            userNormalMode=False,
            constructionHistory=False,
        )
        cmds.setAttr(f'{new_node}.opposite', False)
        cmds.setAttr(f'{new_node}.doubleSided', True)

        if flip_uvs:
            kwargs: dict[str, Any] = {
                'flipType': uv_direction % 2,
                'local': True,
            }
            if uv_direction in (2, 3):
                kwargs['usePivot'] = True
                kwargs['pivotU'] = 0
                kwargs['pivotV'] = 0
            cmds.polyFlipUV(new_node, **kwargs)

        if search:
            try:
                base_name: str = node.split('|')[-1]
                new_name: str = base_name.replace(search, replace)
                new_node = cmds.rename(new_node, new_name)
            except RuntimeError:
                _logger.warning(
                    'New name has no legal characters. : %s', new_name
                )
        new_nodes.append(new_node)

    if new_nodes:
        cmds.select(*new_nodes)

    return new_nodes


def option(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection = cmds.ls(selection=True, type='transform')
    if not selection:
        _logger.error('Select polygon to mirror it.')
        return

    settings: Settings = Settings.instance(__name__, True)
    apply(
        selection,
        settings.axis.value(),
        settings.flip_uvs.value(),
        settings.uv_direction.value(),
        settings.search.value(),
        settings.replace.value(),
    )
    _logger.info('Done.')
