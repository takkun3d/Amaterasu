# ==============================================================================
#
# Delete Unused Animation
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QWidget, QCheckBox

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QWidget, QCheckBox
from maya import cmds
from ..lib import parser, widgets, utility


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Delete Unused Animation'
__version__: str = '1.20'
__doc__ = 'Delete unused animation from selected nodes.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

TRANSFORM_ATTR: list[str] = [
    'tx',
    'ty',
    'tz',
    'rx',
    'ry',
    'rz',
    'sx',
    'sy',
    'sz',
    'translateX',
    'translateY',
    'translateZ',
    'rotateX',
    'rotateY',
    'rotateZ',
    'scaleX',
    'scaleY',
    'scaleZ',
]


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    keep_multi_attr: parser.Variant[bool] = parser.Variant(True)
    ignore_transformation: parser.Variant[bool] = parser.Variant(True)


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

        self.__keep_multi_attr: QCheckBox = QCheckBox(
            "Don't remove compound attribute animations.", self
        )
        main_layout.addRow(widgets.FormLabel(''), self.__keep_multi_attr)

        self.__ignore_transformation: QCheckBox = QCheckBox(
            'Ignore Transform && Rotate && Scale.', self
        )
        main_layout.addRow(widgets.FormLabel(''), self.__ignore_transformation)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__keep_multi_attr.setChecked(settings.keep_multi_attr.value())
        self.__ignore_transformation.setChecked(
            settings.ignore_transformation.value()
        )

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.keep_multi_attr.set_value(self.__keep_multi_attr.isChecked())
        settings.ignore_transformation.set_value(
            self.__ignore_transformation.isChecked()
        )
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
    nodes: list[str],
    keep_multi_attr: bool = True,
    ignore_transformation: bool = True,
) -> bool:
    '''Delete unused animation.'''
    delete_nodes: list[str] = []
    for node in nodes:
        connections: list[str] = cmds.listConnections(
            node,
            type='animCurve',
            source=True,
            destination=False,
            plugs=True,
            connections=True,
        )
        if not connections:
            continue

        compound_attr: dict[str, dict[str, str]] = {}
        for i in range(0, len(connections), 2):
            src_plug: str = connections[i]
            dst_plug: str = connections[i + 1]
            src_node: str = src_plug.split('.')[0]
            src_attr: str = '.'.join(src_plug.split('.')[1:])
            anim_curve: str = dst_plug.split('.')[0]

            # Ignore Transformation
            if ignore_transformation and src_attr in TRANSFORM_ATTR:
                continue

            values: set[float] = set(
                cmds.keyframe(anim_curve, query=True, valueChange=True)  # type: ignore
            )
            is_static_value: set[bool] = set()
            for value in values:
                is_static_value.add(
                    utility.is_static_value(src_node, src_attr, True, value)
                )

            # compound attribute
            parent_attr: list[str] = cmds.attributeQuery(
                src_attr, node=src_node, listParent=True
            )  # type: ignore
            if keep_multi_attr and parent_attr:
                children_attr: list[str] = cmds.attributeQuery(
                    parent_attr[0], node=src_node, listChildren=True
                )  # type: ignore

                # Initialize compound_attr
                if parent_attr[0] not in compound_attr:
                    compound_attr[parent_attr[0]] = {}
                    for child_attr in children_attr:
                        compound_attr[parent_attr[0]][child_attr] = ''

                if False not in is_static_value:
                    compound_attr[parent_attr[0]][src_attr] = anim_curve

            else:
                if False not in is_static_value:
                    delete_nodes.append(anim_curve)

        # Check unused animation from compound_attr.
        if keep_multi_attr:
            for _parent_attr in compound_attr:
                if '' in compound_attr[_parent_attr].values():
                    continue

                delete_nodes += compound_attr[_parent_attr].values()

        if delete_nodes:
            cmds.delete(*delete_nodes)

    return True


def option() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()


def main() -> None:
    '''Apply according to the setting.'''
    selection: list[str] = cmds.ls(selection=True)
    if not selection:
        _logger.error('Select node to delete unused animation.')
        return

    settings: Settings = Settings.instance(__name__, True)
    result: bool = apply(
        selection,
        settings.keep_multi_attr.value(),
        settings.ignore_transformation.value(),
    )
    if result:
        _logger.info('Done.')
