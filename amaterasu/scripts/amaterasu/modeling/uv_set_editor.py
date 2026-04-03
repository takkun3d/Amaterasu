# ==============================================================================
#
# UV Set Editor
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any

try:
    from PySide2.QtCore import Qt, QSize
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLineEdit,
        QTableWidget,
        QHeaderView,
        QTableWidgetItem,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, QSize
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QLineEdit,
            QTableWidget,
            QHeaderView,
            QTableWidgetItem,
        )
from maya import cmds
from ..lib import logger, parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'UV Set Editor'
__version__: str = '1.00'
__doc__ = 'A matrix-based UI tool for managing UV sets across multiple nodes.'
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


class MainWindow(widgets.ToolWidget):
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

        main_layout: QVBoxLayout = QVBoxLayout(self.option_widget())
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        header_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.addLayout(header_layout)

        self.__filter: QLineEdit = QLineEdit(self)
        self.__filter.setPlaceholderText('Search ...')
        header_layout.addWidget(self.__filter)

        button: widgets.IconButton = widgets.IconButton(self)
        button.set_icon(widgets.icon_from_file_name('a_update.png'))
        button.clicked.connect(self.update_ui)
        header_layout.addWidget(button)

        self.__table: QTableWidget = QTableWidget(self)
        self.__table.setSelectionBehavior(QTableWidget.SelectItems)
        self.__table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.__table.setIconSize(QSize(24, 24))

        header_h: QHeaderView = self.__table.horizontalHeader()
        header_h.setSectionResizeMode(QHeaderView.Interactive)
        header_h.setDefaultSectionSize(80)

        header_v: QHeaderView = self.__table.verticalHeader()

        main_layout.addWidget(self.__table)

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

    def update_ui(self) -> None:
        '''Update UI'''
        self.__table.blockSignals(True)
        self.__table.clear()

        selection: list[str] = cmds.ls(selection=True, type='transform')
        if not selection:
            return

        all_uvsets: set[str] = set()
        mesh_data: dict[str, Any] = {}
        for node in selection:
            shapes: list[str] = (
                cmds.listRelatives(
                    node, shapes=True, type='mesh', noIntermediate=True
                )
                or []
            )
            if not shapes:
                continue

            shape: str = shapes[0]
            uv_sets: list[str] = (
                cmds.polyUVSet(shape, query=True, allUVSets=True) or []
            )  # type: ignore
            uv_indices: list[int] = (
                cmds.polyUVSet(shape, query=True, allUVSetsIndices=True) or []
            )  # type: ignore
            current_uv_sets: list[str] = cmds.polyUVSet(
                shape, query=True, currentUVSet=True
            )  # type: ignore
            current_uv_set: str = current_uv_sets[0] if current_uv_sets else ''

            all_uvsets.update(uv_sets)
            mesh_data[node] = {'current': current_uv_set}

        geometrys: list[str] = [geo for geo in mesh_data]
        self.__table.setRowCount(len(geometrys) + 1)

        unique_uvsets: list[str] = sorted(list(all_uvsets))
        self.__table.setColumnCount(len(unique_uvsets) + 1)

        for row, geo in enumerate(geometrys):
            item: QTableWidgetItem = QTableWidgetItem(geo)
            self.__table.setVerticalHeaderItem(row, item)

            for col, uvset in enumerate(unique_uvsets):
                item = QTableWidgetItem(uvset)
                self.__table.setHorizontalHeaderItem(col, item)

                item = QTableWidgetItem()
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.__table.setItem(row, col, item)

        item = QTableWidgetItem('+')
        self.__table.setVerticalHeaderItem(len(geometrys), item)

        item = QTableWidgetItem('+')
        self.__table.setHorizontalHeaderItem(len(unique_uvsets), item)

        self.__table.blockSignals(False)


# ==============================================================================
#
# Functions
#
# ==============================================================================
def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
