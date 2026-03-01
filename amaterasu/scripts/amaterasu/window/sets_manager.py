# ==============================================================================
#
# Sets Manager
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging

try:
    from PySide2.QtCore import (
        Qt,
        Signal,
        QModelIndex,
        QAbstractItemModel,
        QEvent,
        QRect,
        QPoint,
        QSize,
        QItemSelectionModel,
        QSortFilterProxyModel,
    )
    from PySide2.QtGui import QPixmap, QColor, QPainter, QStandardItemModel
    from PySide2.QtWidgets import (
        QWidget,
        QItemDelegate,
        QStyleOptionViewItem,
        QLineEdit,
        QApplication,
        QStyle,
        QGridLayout,
        QPushButton,
        QTabWidget,
        QTreeView,
        QHeaderView,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import (
            Qt,
            Signal,
            QModelIndex,
            QAbstractItemModel,
            QEvent,
            QRect,
            QPoint,
            QSize,
            QItemSelectionModel,
            QSortFilterProxyModel,
        )
        from PySide6.QtGui import QPixmap, QColor, QPainter, QStandardItemModel
        from PySide6.QtWidgets import (
            QWidget,
            QItemDelegate,
            QStyleOptionViewItem,
            QLineEdit,
            QApplication,
            QStyle,
            QGridLayout,
            QPushButton,
            QTabWidget,
            QTreeView,
            QHeaderView,
        )
from maya import cmds
from ..lib import parser, widgets

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Sets Manager'
__version__: str = '1.30'
__doc__ = 'Sets manager.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

FAVORITE_ATTR_NAME: str = 'amaterasu_sets_favorite'
IGNORE_SETS: tuple[str, ...] = (
    'defaultLightSet',
    'defaultObjectSet',
    'initialParticleSE',
    'initialShadingGroup',
    'TurtleDefaultBakeLayer',
)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    ignore_referencce: parser.Variant[bool] = parser.Variant(False)


class SetsViewDelegate(QItemDelegate):
    '''Sets view delegate'''

    CELL_SIZE: int = 20
    FAVORITE_ICON_LIST: tuple[QPixmap, ...] = (
        widgets.pixmap_from_file_name('view/a_star_off.png'),
        widgets.pixmap_from_file_name('view/a_star_on.png'),
    )
    ACTION_ICON_LIST: tuple[QPixmap, ...] = (
        widgets.pixmap_from_file_name('view/a_add.png'),
        widgets.pixmap_from_file_name('view/a_remove.png'),
        widgets.pixmap_from_file_name('view/a_show.png'),
        widgets.pixmap_from_file_name('view/a_hide.png'),
        widgets.pixmap_from_file_name('view/a_trash.png'),
    )

    clicked_cursor = Signal(str, Qt.KeyboardModifiers)
    clicked_add = Signal(str)
    clicked_remove = Signal(str)
    clicked_show = Signal(str)
    clicked_hide = Signal(str)
    clicked_delete = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initilize widget'''
        super().__init__(parent)

    # override
    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        '''createEditor[override]'''
        if index.column() == 1:
            return QLineEdit(parent)

        return QWidget(parent)

    # override
    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        '''setEditorData[override]'''
        value: str = index.model().data(index, Qt.EditRole)
        if index.column() == 1:
            editor.setText(value)

    # override
    def setModelData(
        self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex
    ) -> None:
        '''setModelData[override]'''

        value: str = ''
        if index.column() == 1:
            value = editor.text()
            if index.data() == value:
                return

            try:
                value = cmds.rename(index.data(), value)
                model.setData(index, value, Qt.EditRole)
            except RuntimeError:
                _logger.error('Failed rename : %s -> %s', index.data(), value)
                return

    # override
    def updateEditorGeometry(
        self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        '''updateEditorGeometry[override]'''
        editor.setGeometry(option.rect)

    # override
    def editorEvent(
        self,
        event: QEvent,
        model: QAbstractItemModel,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> bool:
        '''editorEvent[override]'''
        status: bool = False
        if event.type() == QEvent.MouseButtonPress:
            if index.column() == 0:
                value = not index.model().data(index, Qt.EditRole)
                model.setData(index, value, Qt.EditRole)

                index = model.index(index.row(), 1)
                save_favorite_state(index.data(), value)
                status = True

            elif index.column() == 1:
                modifiers = QApplication.keyboardModifiers()
                index = model.index(index.row(), 1)
                self.clicked_cursor.emit(index.data(), modifiers)
                status = True

            elif index.column() == 2:
                action_index: int = -1
                for i in range(len(self.ACTION_ICON_LIST)):
                    action_rect: QRect = QRect(
                        option.rect.left() + self.CELL_SIZE * i,
                        option.rect.top(),
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    )
                    if action_rect.contains(event.pos()):
                        action_index = i
                        break

                if action_index == 0:
                    index = model.index(index.row(), 1)
                    self.clicked_add.emit(index.data())

                elif action_index == 1:
                    index = model.index(index.row(), 1)
                    self.clicked_remove.emit(index.data())

                elif action_index == 2:
                    index = model.index(index.row(), 1)
                    self.clicked_show.emit(index.data())

                elif action_index == 3:
                    index = model.index(index.row(), 1)
                    self.clicked_hide.emit(index.data())

                elif action_index == 4:
                    index = model.index(index.row(), 1)
                    result = self.clicked_delete.emit(index.data())
                    if result:
                        model.removeRow(index.row())

                status = True

        return status

    # override
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        '''paint[override]'''
        data = index.data()

        painter.fillRect(option.rect, QColor(Qt.transparent))
        if index.column() == 0:
            pos = QPoint(
                option.rect.x()
                + (option.rect.width() / 2.0)
                - (self.FAVORITE_ICON_LIST[int(data)].width() / 2.0),
                option.rect.y()
                + (option.rect.height() / 2.0)
                - (self.FAVORITE_ICON_LIST[int(data)].height() / 2.0),
            )
            painter.drawPixmap(pos, self.FAVORITE_ICON_LIST[int(data)])

        elif index.column() == 1:
            if option.state & QStyle.State_MouseOver:
                painter.fillRect(option.rect, option.palette.highlight())
            painter.drawText(
                option.rect,
                int(Qt.AlignLeft | Qt.AlignVCenter),
                data,
            )

        elif index.column() == 2:
            for i, icon in enumerate(self.ACTION_ICON_LIST):
                pos = QPoint(
                    option.rect.x()
                    + (icon.width() / 2.0)
                    + (self.CELL_SIZE * i),
                    option.rect.y()
                    + (option.rect.height() / 2.0)
                    - (icon.height() / 2.0),
                )
                painter.drawPixmap(pos, icon)

            if not option.state & QStyle.State_MouseOver:
                background_brush = option.palette.base()
                over_color = background_brush.color()
                over_color.setAlphaF(0.8)
                background_brush.setColor(over_color)
                painter.fillRect(option.rect, background_brush)

    def sizeHint(
        self, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QSize:
        '''sizeHint[override]'''
        if index.column() == 0:
            return QSize(self.CELL_SIZE, self.CELL_SIZE)

        elif index.column() == 1:
            return QSize(option.rect.width(), option.rect.height())

        else:
            return QSize(
                self.CELL_SIZE * len(self.ACTION_ICON_LIST) + 10, self.CELL_SIZE
            )


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

        option_widget: QWidget = self.option_widget()
        main_layout: QGridLayout = QGridLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__sets_name: QLineEdit = QLineEdit(self)
        main_layout.addWidget(self.__sets_name, 0, 0)

        button: QPushButton = QPushButton('Create', self)
        button.clicked.connect(self.create_sets_callback)
        main_layout.addWidget(button, 0, 1)

        self.__tab: QTabWidget = QTabWidget(self)
        self.__tab.setDocumentMode(True)
        main_layout.addWidget(self.__tab, 1, 0, 1, 2)

        # ======================================================================
        # View
        # ======================================================================
        self.__model: QStandardItemModel = QStandardItemModel(0, 3, self)
        self.__selection_model: QItemSelectionModel = QItemSelectionModel(
            self.__model
        )
        self.__delegater: SetsViewDelegate = SetsViewDelegate(self)
        self.__delegater.clicked_cursor.connect(select_sets)
        self.__delegater.clicked_add.connect(add_member)
        self.__delegater.clicked_remove.connect(remove_member)
        self.__delegater.clicked_show.connect(show_member)
        self.__delegater.clicked_hide.connect(hide_member)
        self.__delegater.clicked_delete.connect(delete_sets)

        self.__view: QTreeView = QTreeView(self)
        self.__view.setModel(self.__model)
        self.__view.setSelectionModel(self.__selection_model)
        self.__view.setItemDelegate(self.__delegater)
        self.__view.setSelectionBehavior(QTreeView.SelectRows)
        self.__view.setSelectionMode(QTreeView.ExtendedSelection)
        self.__view.setRootIsDecorated(False)
        self.__setupViewHeader(self.__view)
        self.__tab.addTab(self.__view, 'Sets')

        # ======================================================================
        # Proxy View
        # ======================================================================
        self.__proxy_model: QSortFilterProxyModel = QSortFilterProxyModel(self)
        self.__proxy_model.setDynamicSortFilter(True)
        self.__proxy_model.setSourceModel(self.__model)
        self.__proxy_model.setFilterKeyColumn(0)
        self.__proxy_model.setFilterCaseSensitivity(Qt.CaseSensitive)
        self.__proxy_model.setFilterWildcard('true')
        self.__proxy_model.setSortCaseSensitivity(Qt.CaseSensitive)
        self.__proxy_model.setFilterRole(Qt.EditRole)

        self.__proxy_sel_model: QItemSelectionModel = QItemSelectionModel(
            self.__proxy_model
        )

        self.__proxy_view: QTreeView = QTreeView(self)
        self.__proxy_view.setModel(self.__proxy_model)
        self.__proxy_view.setSelectionModel(self.__proxy_sel_model)
        self.__proxy_view.setItemDelegate(self.__delegater)
        self.__proxy_view.setSelectionBehavior(QTreeView.SelectRows)
        self.__proxy_view.setSelectionMode(QTreeView.ExtendedSelection)
        self.__proxy_view.setRootIsDecorated(False)
        self.__setupViewHeader(self.__proxy_view)
        self.__tab.addTab(self.__proxy_view, 'Favorite')

        # ======================================================================
        # Event
        # ======================================================================
        self.__view.setMouseTracking(True)
        self.__view.viewportEntered.connect(self.__view.viewport().update)
        self.__proxy_view.setMouseTracking(True)
        self.__proxy_view.viewportEntered.connect(
            self.__proxy_view.viewport().update
        )

        # ======================================================================
        # Menu
        # ======================================================================
        menu_bar = self.menu_bar()
        view_menu = menu_bar.addMenu('View')
        menu_bar.insertMenu(self.help_menu().menuAction(), view_menu)

        self.__ignore_reference_sets = view_menu.addAction(
            'Ignore Referenced sets'
        )
        self.__ignore_reference_sets.setCheckable(True)
        self.__ignore_reference_sets.triggered.connect(
            self.ignore_referenced_sets
        )

        action = view_menu.addAction('Update')
        action.triggered.connect(self.update_model)

    def __setupViewHeader(self, view: QWidget) -> None:
        '''Setup view header'''
        view.header().hide()
        view.header().setStretchLastSection(False)
        view.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        view.header().setSectionResizeMode(1, QHeaderView.Stretch)
        view.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__ignore_reference_sets.setChecked(
            settings.ignore_referencce.value()
        )

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.ignore_referencce.set_value(
            self.__ignore_reference_sets.isChecked()
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
    def create_sets_callback(self) -> None:
        '''Create sets callback.'''
        sets: str = create_sets(self.__sets_name.text())
        self.add_item(sets)
        self.__sets_name.setText('')

    def add_item(self, sets: str) -> None:
        '''Aadd sets to model.'''
        row: int = self.__model.rowCount()
        self.__model.setRowCount(row + 1)

        index: QModelIndex = self.__model.index(row, 0, QModelIndex())
        self.__model.setData(index, favorite_state(sets))

        index = self.__model.index(row, 1, QModelIndex())
        self.__model.setData(index, sets)

        index = self.__model.index(row, 2, QModelIndex())
        self.__model.setData(index, None)

    def add_item_list(self, sets_list: list[str]) -> None:
        '''Add sets list to model.'''
        for sets in sets_list:
            self.add_item(sets)

    def ignore_referenced_sets(self) -> None:
        '''Ignore reference sets'''
        self.save_settings()
        self.update_model()

    def update_model(self) -> None:
        '''Update UI.'''
        while self.__model.rowCount():
            self.__model.removeRow(0)

        result: list[str] = []
        sets_list: list[str] = cmds.ls(sets=True)

        settings: Settings = Settings.instance(__name__, True)
        if settings.ignore_referencce.value():
            sets_list = cmds.ls('*', sets=True)

        for sets in sets_list:
            if sets in IGNORE_SETS:
                continue
            if cmds.sets(sets, query=True, renderable=True):
                continue
            if cmds.sets(sets, query=True, edges=True):
                continue
            if cmds.sets(sets, query=True, editPoints=True):
                continue
            if cmds.sets(sets, query=True, facets=True):
                continue
            if cmds.sets(sets, query=True, vertices=True):
                continue
            result.append(sets)
        self.add_item_list(result)


# ==============================================================================
#
# Functions
#
# ==============================================================================
@widgets.undo
def select_sets(sets: str, modifiers: Qt.KeyboardModifiers) -> None:
    '''Select sets member.'''
    kwargs: dict[str, Any] = {}
    if modifiers == Qt.ShiftModifier:
        kwargs['tgl'] = True
    elif modifiers == Qt.ControlModifier:
        kwargs['d'] = True
    elif modifiers & Qt.ShiftModifier and modifiers & Qt.ControlModifier:
        kwargs['add'] = True
    cmds.select(sets, **kwargs)


@widgets.undo
def create_sets(sets_name: str) -> str:
    '''Create sets.'''
    selection: list[str] = cmds.ls(selection=True)
    sets: str = ''
    if not selection:
        sets = cmds.sets(name=sets_name)
    else:
        sets = cmds.sets(*selection, name=sets_name)
    return sets


@widgets.undo
def add_member(sets: str) -> None:
    '''Add member to sets.'''
    if not cmds.objExists(sets):
        _logger.warning(
            'The requested node was not found on this scene : %s', sets
        )
        return
    selection: list[str] = cmds.ls(selection=True)
    if selection:
        cmds.sets(*selection, edit=True, addElement=sets)


@widgets.undo
def remove_member(sets: str) -> None:
    '''Remove member from sets.'''
    if not cmds.objExists(sets):
        _logger.warning(
            'The requested node was not found on this scene : %s', sets
        )
        return
    selection: list[str] = cmds.ls(selection=True)
    if selection:
        cmds.sets(*selection, edit=True, remove=sets)


@widgets.undo
def show_member(sets: str) -> None:
    '''Show node from sets member.'''
    if not cmds.objExists(sets):
        _logger.warning(
            'The requested node was not found on this scene : %s', sets
        )
        return
    cmds.showHidden(sets)


@widgets.undo
def hide_member(sets: str) -> None:
    '''Show node from sets member.'''
    if not cmds.objExists(sets):
        _logger.warning(
            'The requested node was not found on this scene : %s', sets
        )
        return
    cmds.hide(sets)


@widgets.undo
def delete_sets(sets: str) -> None:
    '''Delete sets.'''
    try:
        cmds.delete(sets)

    except RuntimeError:
        _logger.error('Failed to delete sets : %s', sets)


def favorite_state(sets: str) -> bool:
    '''Return favorite state'''
    if not cmds.attributeQuery(FAVORITE_ATTR_NAME, node=sets, exists=True):
        cmds.addAttr(sets, longName=FAVORITE_ATTR_NAME, attributeType='bool')

    return cmds.getAttr(f'{sets}.{FAVORITE_ATTR_NAME}')


def save_favorite_state(sets: str, value: bool) -> None:
    '''save favorite state'''
    if not cmds.attributeQuery(FAVORITE_ATTR_NAME, node=sets, exists=True):
        cmds.addAttr(sets, longName=FAVORITE_ATTR_NAME, attributeType='bool')

    cmds.setAttr(f'{sets}.{FAVORITE_ATTR_NAME}', value)


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.update_model()
    window.show()
