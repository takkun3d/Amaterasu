# ==============================================================================
#
# Attribute Reorder
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from venv import logger

try:
    from PySide2.QtCore import Qt, QItemSelectionModel
    from PySide2.QtGui import QStandardItemModel, QStandardItem
    from PySide2.QtWidgets import (
        QWidget,
        QGridLayout,
        QListView,
        QLineEdit,
        QPushButton,
        QMessageBox,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, QItemSelectionModel
        from PySide6.QtGui import QStandardItemModel, QLineEdit, QStandardItem
        from PySide6.QtWidgets import (
            QWidget,
            QGridLayout,
            QListView,
            QPushButton,
            QMessageBox,
        )
from maya import cmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Attribute Reorder'
__version__: str = '1.00'
__doc__ = 'Reorders the user-defined attributes on the selected node.'
__copyright__ = 'Copyright(c) 2019-2025 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')


class MainWindow(widgets.ToolWidget):
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

        main_layout: QGridLayout = QGridLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__node: QLineEdit = QLineEdit(self)
        self.__node.setEnabled(False)
        main_layout.addWidget(self.__node, 0, 0, 1, 2)

        self.__model = QStandardItemModel(0, 1, self)
        self.__selection_model = QItemSelectionModel(self.__model)

        self.__view = QListView(self)
        self.__view.setModel(self.__model)
        self.__view.setSelectionModel(self.__selection_model)
        self.__view.setFocusPolicy(Qt.NoFocus)
        self.__view.setSelectionMode(QListView.SingleSelection)
        self.__view.setDragEnabled(True)
        self.__view.setAcceptDrops(True)
        self.__view.setDragDropMode(QListView.InternalMove)
        self.__view.setDefaultDropAction(Qt.MoveAction)
        main_layout.addWidget(self.__view, 1, 0, 1, 2)

        analyze_btn: QPushButton = QPushButton('Analyze', self)
        analyze_btn.clicked.connect(self.analyze)
        main_layout.addWidget(analyze_btn, 2, 0)

        apply_btn: QPushButton = QPushButton('Apply', self)
        apply_btn.clicked.connect(self.apply)
        main_layout.addWidget(apply_btn, 2, 1)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
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
    def analyze(self) -> None:
        '''Analyze attribute from selection.'''
        self.__node.setText('')
        self.__model.removeRows(0, self.__model.rowCount())

        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            logging.error('Select a node to reorder attributes.')
            return

        if len(selection) > 1:
            logging.error('Select a node to reorder attributes.')
            return

        attributes: list[str] = cmds.listAttr(selection[0], userDefined=True)
        if not attributes:
            logging.error('The selected node has no user-defined attributes.')
            return

        self.__node.setText(selection[0])
        for attribute in attributes:
            item: QStandardItem = QStandardItem(attribute)
            item.setEditable(False)
            item.setDropEnabled(False)
            self.__model.appendRow(item)

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()
        order: list[str] = []
        for i in range(self.__model.rowCount()):
            item: QStandardItem = self.__model.item(i, 0)
            order.append(item.text())

        anser: QMessageBox.StandardButton = QMessageBox.warning(
            self,
            __product__,
            'This action cannot be undo.\nDo you want to continue?',
            QMessageBox.Yes,
            QMessageBox.No,
        )
        if anser == QMessageBox.No:
            return

        apply(self.__node.text(), order)


# ==============================================================================
#
# Functions
#
# ==============================================================================
def apply(node: str = '', attr_orders: list[str] | None = None) -> bool:
    '''Reorder attributes.'''
    if not attr_orders:
        return False

    attr_orders.reverse()
    for attr in attr_orders:
        cmds.deleteAttr(f'{node}.{attr}')

    for i in range(len(attr_orders)):
        cmds.undo()

    cmds.flushUndo()
    logger.info('Done.')
    return True


def main() -> None:
    '''Show window.'''
    window: MainWindow = MainWindow()
    window.show()
