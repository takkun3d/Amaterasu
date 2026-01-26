# ==============================================================================
#
# Replace Reference
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import os

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QWidget,
        QHBoxLayout,
        QLineEdit,
        QCheckBox,
        QFileDialog,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QWidget,
            QHBoxLayout,
            QLineEdit,
            QCheckBox,
            QFileDialog,
        )
from maya import cmds, mel
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Replace Reference'
__version__: str = '1.00'
__doc__ = 'Replaces the reference from selected node.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

FILE_FORMAT: dict[str, str] = {'.ma': 'mayaAscii', '.mb': 'mayaBinary'}


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    file_path: parser.Variant[str] = parser.Variant('')
    update_namespace: parser.Variant[bool] = parser.Variant(True)
    update_node_name: parser.Variant[bool] = parser.Variant(True)


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

        filepath_layout: QHBoxLayout = QHBoxLayout(self)
        self.__file_path: QLineEdit = QLineEdit(self)
        filepath_layout.addWidget(self.__file_path)

        file_dialog_button: widgets.IconButton = widgets.IconButton()
        file_dialog_button.set_icon(widgets.image_file_path('a_folder.png'))
        file_dialog_button.clicked.connect(self.__open_file_dialog)
        filepath_layout.addWidget(file_dialog_button)
        main_layout.addRow(widgets.FormLabel('file'), filepath_layout)

        self.__update_namespace: QCheckBox = QCheckBox('Update Namespace', self)
        main_layout.addRow('', self.__update_namespace)

        self.__update_reference_name: QCheckBox = QCheckBox(
            'Update Reference Name', self
        )
        main_layout.addRow('', self.__update_reference_name)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__file_path.setText(settings.file_path.value())
        self.__update_namespace.setChecked(settings.update_namespace.value())
        self.__update_reference_name.setChecked(
            settings.update_node_name.value()
        )

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.file_path.set_value(self.__file_path.text())
        settings.update_namespace.set_value(self.__update_namespace.isChecked())
        settings.update_node_name.set_value(
            self.__update_reference_name.isChecked()
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

    def __open_file_dialog(self) -> None:
        '''Open File Dialog'''
        current_dir: str = os.path.dirname(self.__file_path.text())
        result: tuple(str, str) = QFileDialog.getOpenFileName(
            self,
            'Specific Maya Scene File',
            current_dir,
            'Maya Files (*.ma *.mb)',
        )
        if result[0] != '':
            self.__file_path.setText(result[0])

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()
        settings: Settings = Settings.instance(__name__, True)
        apply(
            settings.file_path.value(),
            settings.update_namespace.value(),
            settings.update_node_name.value(),
        )


# ==============================================================================
#
# Functions
#
# ==============================================================================
def get_reference_nodes(nodes: list[str]) -> list[str]:
    '''Return reference nodes form selected nodes.'''
    references: list[str] = [
        cmds.referenceQuery(node, referenceNode=True) for node in nodes
    ]
    references = list(set(references))
    return references


def get_selected_references() -> list[str]:
    '''Return selected in the Reference Editor.'''
    try:
        reference_editor: str = mel.eval('$temp = $gReferenceEditorPanel;')
        references: list[str] = cmds.sceneEditor(
            reference_editor, query=True, selectReference=True
        )
    except RuntimeError:
        return []

    return references


def replace_reference_file(reference: str, file_path: str) -> bool:
    '''Replace file of reference.'''
    format: str = FILE_FORMAT[os.path.splitext(file_path)[-1]]
    cmds.file(file_path, loadReference=reference, type=format, options='v=0;')
    return True


def set_namespace_from_filename(reference: str) -> bool:
    '''Set namespace from filename'''
    file_path: str = cmds.referenceQuery(reference, filename=True)
    basename: str = os.path.splitext(os.path.basename(file_path))[0]
    cmds.file(file_path, edit=True, namespace=basename)
    return True


def set_reference_name_from_filename(reference: str) -> bool:
    '''Set reference name from filename.'''
    file_path: str = cmds.referenceQuery(reference, filename=True)
    basename: str = os.path.splitext(os.path.basename(file_path))[0]

    cmds.lockNode(reference, lock=False)
    reference = cmds.rename(reference, f'{basename}RN')
    cmds.lockNode(reference, lock=True)
    return True


def apply(
    file_path: str,
    update_namespace: bool = True,
    update_node_name: bool = True,
) -> bool:
    '''Replaces the reference from selected node.'''
    if not os.path.exists(file_path):
        _logger.error('Does not exists file : %s', file_path)
        return False

    references: list[str] = get_selected_references()
    if not references:
        references = get_reference_nodes(cmds.ls(selection=True))

    if not references:
        _logger.error(
            'Select node or Reference Editor item to replace reference file.'
        )
        return False

    for reference in references:
        replace_reference_file(reference, file_path)
        if update_namespace:
            set_namespace_from_filename(reference)

        if update_node_name:
            set_reference_name_from_filename(reference)

    return True


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
