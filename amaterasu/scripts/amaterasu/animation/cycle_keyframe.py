# ==============================================================================
#
# Cycle Keyframe
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget, QCheckBox, QComboBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QWidget, QCheckBox, QComboBox
from maya import cmds
from ..lib import parser, utility, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Cycle Keyframe'
__version__: str = '1.20'
__doc__ = 'Change an animation of selected node to a cycle.'
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
    method: parser.Variant[int] = parser.Variant(0)
    target: parser.Variant[int] = parser.Variant(0)
    tangent: parser.Variant[int] = parser.Variant(1)
    display_infinities: parser.Variant[bool] = parser.Variant(True)
    pre_infinity: parser.Variant[int] = parser.Variant(2)
    post_infinity: parser.Variant[int] = parser.Variant(2)


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
            widgets.FrameWidget('Cycle Options', False, False, self)
        )

        self.__target: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__target.set_labels(('Selected Node', 'Selected Curve'))
        main_layout.addRow(widgets.FormLabel('Target'), self.__target)

        self.__method: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__method.set_labels(('None', 'Start -> End', 'End -> Start'))
        self.__method.button_group().buttonClicked.connect(
            self.update_ui_enabled
        )
        main_layout.addRow(widgets.FormLabel('Method'), self.__method)

        self.__tangent: QCheckBox = QCheckBox('Copy Tangent', self)
        main_layout.addRow('', self.__tangent)

        main_layout.addRow(
            widgets.FrameWidget('Infinities Options', False, False, self)
        )

        self.__display_infinities: QCheckBox = QCheckBox(
            'Display Infinities', self
        )
        main_layout.addRow('', self.__display_infinities)

        self.__pre_infinity: QComboBox = QComboBox(self)
        self.__pre_infinity.addItem('Constant')
        self.__pre_infinity.addItem('Linear')
        self.__pre_infinity.addItem('Cycle')
        self.__pre_infinity.addItem('Cycle with Offset')
        self.__pre_infinity.addItem('Oscillate')
        main_layout.addRow(
            widgets.FormLabel('Pre Infinity'), self.__pre_infinity
        )

        self.__post_infinity: QComboBox = QComboBox(self)
        self.__post_infinity.addItem('Constant')
        self.__post_infinity.addItem('Linear')
        self.__post_infinity.addItem('Cycle')
        self.__post_infinity.addItem('Cycle with Offset')
        self.__post_infinity.addItem('Oscillate')
        main_layout.addRow(
            widgets.FormLabel('Post Infinity'), self.__post_infinity
        )

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__method.set_check_id(settings.method.value())
        self.__target.set_check_id(settings.target.value())
        self.__tangent.setChecked(settings.tangent.value())
        self.__display_infinities.setChecked(
            settings.display_infinities.value()
        )
        self.__pre_infinity.setCurrentIndex(settings.pre_infinity.value())
        self.__post_infinity.setCurrentIndex(settings.post_infinity.value())
        self.update_ui_enabled()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.method.set_value(self.__method.check_id())
        settings.target.set_value(self.__target.check_id())
        settings.tangent.set_value(self.__tangent.isChecked())
        settings.display_infinities.set_value(
            self.__display_infinities.isChecked()
        )
        settings.pre_infinity.set_value(self.__pre_infinity.currentIndex())
        settings.post_infinity.set_value(self.__post_infinity.currentIndex())
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

    def update_ui_enabled(self) -> None:
        '''Update ui enabled'''
        if self.__method.check_id() == 0:
            self.__tangent.setEnabled(False)
        else:
            self.__tangent.setEnabled(True)

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
    method: int = 0,
    tangent: bool = True,
    display_infinities: bool = True,
    pre_infinity: int = 2,
    post_infinity: int = 2,
) -> bool:
    '''Change an animation to a cycle.'''
    cmds.animCurveEditor(
        'graphEditor1GraphEd',
        edit=True,
        displayInfinities='on' if display_infinities else 'off',
    )
    if pre_infinity >= 2:
        pre_infinity += 1

    if post_infinity >= 2:
        post_infinity += 1

    connected_curves: list[str] = []
    for node in nodes:
        if cmds.objectType(node) not in utility.ANIM_CURVE_TYPES:
            connected_curves.extend(utility.get_anim_curves(node))
        else:
            connected_curves.append(node)

    for curve in connected_curves:
        if method != 0:
            indexes: list[int] = cmds.keyframe(
                curve, query=True, indexValue=True
            )
            values: list[Any] = cmds.keyframe(
                curve, query=True, valueChange=True
            )
            tangents: list[float] = cmds.keyTangent(
                curve, query=True, outAngle=True
            )
            src_seek: int = 0 if method == 1 else -1
            dst_seek: int = -1 if method == 1 else 0
            index: tuple[int, int] = (indexes[dst_seek], indexes[dst_seek])

            cmds.keyframe(
                curve, edit=True, index=index, valueChange=values[src_seek]
            )
            if tangent:
                cmds.keyTangent(
                    curve, edit=True, index=index, outAngle=tangents[src_seek]
                )

        cmds.setAttr(f'{curve}.preInfinity', pre_infinity)
        cmds.setAttr(f'{curve}.postInfinity', post_infinity)

    return True


def option(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection: list[str] = []
    settings: Settings = Settings.instance(__name__, True)
    if settings.target.value() == 0:
        selection = cmds.ls(selection=True)
        if not selection:
            _logger.error('Select node to cycle key.')
            return
    else:
        selection = cmds.keyframe(query=True, selected=True, name=True)
        if not selection:
            _logger.error('Select curve to cycle key.')
            return

    result: bool = apply(
        selection,
        settings.method.value(),
        settings.tangent.value(),
        settings.display_infinities.value(),
        settings.pre_infinity.value(),
        settings.post_infinity.value(),
    )
    if result:
        _logger.info('Done.')
