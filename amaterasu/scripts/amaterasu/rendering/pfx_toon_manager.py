# ==============================================================================
#
# PfxToon Manager
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import (
        Qt,
        Signal,
        QEvent,
        QAbstractItemModel,
        QItemSelectionModel,
        QModelIndex,
        QSize,
        QPoint,
        QRect,
    )
    from PySide2.QtGui import (
        QPainter,
        QColor,
        QBrush,
        QPixmap,
        QStandardItemModel,
    )
    from PySide2.QtWidgets import (
        QApplication,
        QStyle,
        QWidget,
        QItemDelegate,
        QStyleOptionViewItem,
        QVBoxLayout,
        QLineEdit,
        QLabel,
        QAbstractItemView,
        QTreeView,
        QHeaderView,
        QPushButton,
        QMenuBar,
        QMenu,
        QAction,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import (
            Qt,
            Signal,
            QEvent,
            QAbstractItemModel,
            QItemSelectionModel,
            QModelIndex,
            QSize,
            QPoint,
            QRect,
        )
        from PySide6.QtGui import (
            QPainter,
            QColor,
            QBrush,
            QPixmap,
            QStandardItemModel,
        )
        from PySide6.QtWidgets import (
            QApplication,
            QStyle,
            QWidget,
            QItemDelegate,
            QStyleOptionViewItem,
            QVBoxLayout,
            QLineEdit,
            QLabel,
            QAbstractItemView,
            QTreeView,
            QHeaderView,
            QPushButton,
            QMenuBar,
            QMenu,
            QAction,
        )
from maya import cmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'PfxToon Manager'
__version__: str = '1.20'
__doc__ = 'Manages multiple pfxToon nodes and controls geometry assignments.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

DEFAULT_NAME: str = 'outline'
LINE_COLOR: tuple[float, float, float] = (0.0472, 0.0472, 0.0472)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')


class PfxToonViewDelegate(QItemDelegate):
    '''pfxToon view delegate'''

    CELL_SIZE: int = 20
    ACTION_ICON_LIST: tuple[QPixmap, ...] = (
        widgets.pixmap_from_file_name('view/a_add.png'),
        widgets.pixmap_from_file_name('view/a_remove.png'),
        widgets.pixmap_from_file_name('view/a_trash.png'),
    )

    clicked_cursor: Signal = Signal(str, Qt.KeyboardModifiers)
    clicked_add: Signal = Signal(str)
    ckicked_remove: Signal = Signal(str)
    clicked_delete: Signal = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        '''Initilize widget'''
        super().__init__(parent)

    # override
    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QWidget:
        '''createEditor[override]'''
        if index.column() == 0:
            return QLineEdit(parent)

        return QWidget(parent)

    # override
    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        '''setEditorData[override]'''
        value: str = index.model().data(index, Qt.EditRole)
        if index.column() == 0:
            editor.setText(value)

    # override
    def setModelData(
        self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex
    ) -> None:
        '''setModelData[override]'''
        if index.column() == 0:
            value: str = editor.text()
            if index.data() == value:
                return

            try:
                value = cmds.rename(index.data(), value)
                model.setData(index, value, Qt.EditRole)

            except RuntimeError:
                _logger.error('Failed rename : %s -> %s', index.data(), value)
                return

            # TODO: Rename geometry, material and shading group.

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
                modifiers = QApplication.keyboardModifiers()
                index = model.index(index.row(), 0)
                self.clicked_cursor.emit(index.data(), modifiers)
                status = True

            elif index.column() == 1:
                action_index: int = -1
                for i in range(len(self.ACTION_ICON_LIST)):
                    actionRect = QRect(
                        option.rect.left() + self.CELL_SIZE * i,
                        option.rect.top(),
                        self.CELL_SIZE,
                        self.CELL_SIZE,
                    )
                    if actionRect.contains(event.pos()):
                        action_index = i
                        break

                if action_index == 0:
                    _index = model.index(index.row(), 0)
                    self.clicked_add.emit(_index.data())

                elif action_index == 1:
                    _index = model.index(index.row(), 0)
                    self.ckicked_remove.emit(_index.data())

                elif action_index == 2:
                    _index = model.index(index.row(), 0)
                    result = self.clicked_delete.emit(_index.data())
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
            if option.state & QStyle.State_MouseOver:
                painter.fillRect(option.rect, option.palette.highlight())
            painter.drawText(
                option.rect,
                int(Qt.AlignLeft | Qt.AlignVCenter),
                data,
            )

        elif index.column() == 1:
            for i, icon in enumerate(self.ACTION_ICON_LIST):
                pos: QPoint = QPoint(
                    option.rect.x()
                    + (icon.width() / 2.0)
                    + (self.CELL_SIZE * i),
                    option.rect.y()
                    + (option.rect.height() / 2.0)
                    - (icon.height() / 2.0),
                )
                painter.drawPixmap(pos, icon)

            if not option.state & QStyle.State_MouseOver:
                background_brush: QBrush = option.palette.base()
                over_color: QColor = background_brush.color()
                over_color.setAlphaF(0.8)
                background_brush.setColor(over_color)
                painter.fillRect(option.rect, background_brush)

    def sizeHint(
        self, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QSize:
        '''sizeHint[override]'''
        if index.column() == 0:
            return QSize(option.rect.width(), option.rect.height())

        return QSize(
            self.CELL_SIZE * len(self.ACTION_ICON_LIST) + 10,
            self.CELL_SIZE,
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
        main_layout: QVBoxLayout = QVBoxLayout(option_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        label: QLabel = QLabel('== Support only Polygon ==', self)
        label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(label)

        self.__model: QStandardItemModel = QStandardItemModel(0, 2, self)
        self.__sel_model: QItemSelectionModel = QItemSelectionModel(
            self.__model
        )
        self.__delegater: PfxToonViewDelegate = PfxToonViewDelegate(self)
        self.__delegater.clicked_cursor.connect(select_pfx_toon)
        self.__delegater.clicked_add.connect(add_object_to_pfx_toon)
        self.__delegater.ckicked_remove.connect(remove_object_from_pfx_toon)
        self.__delegater.clicked_delete.connect(delete_pfx_toon)

        self.__view: QTreeView = QTreeView(self)
        self.__view.setModel(self.__model)
        self.__view.setSelectionModel(self.__sel_model)
        self.__view.setItemDelegate(self.__delegater)
        self.__view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.__view.setRootIsDecorated(False)
        self.__setup_view_header(self.__view)
        main_layout.addWidget(self.__view)

        button: QPushButton = QPushButton('New Outline')
        button.clicked.connect(self.create_pfx_toon_callback)
        main_layout.addWidget(button)

        # ======================================================================
        # Event
        # ======================================================================
        self.__view.setMouseTracking(True)
        self.__view.viewportEntered.connect(self.__view.viewport().update)

        # ======================================================================
        # Menu
        # ======================================================================
        menu_bar: QMenuBar = self.menu_bar()
        view_menu: QMenu = menu_bar.addMenu('View')
        menu_bar.insertMenu(self.help_menu().menuAction(), view_menu)

        action: QAction = view_menu.addAction('Update')
        action.triggered.connect(self.update_model)

    def __setup_view_header(self, view: QWidget) -> None:
        '''Setup view header'''
        view.header().hide()
        view.header().setStretchLastSection(False)
        view.header().setSectionResizeMode(0, QHeaderView.Stretch)
        view.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)

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
    def create_pfx_toon_callback(self) -> None:
        '''Create pfxToon callback.'''
        pfx_toon: str = create_pfx_toon()
        self.add_item(pfx_toon)

    def add_item(self, pfx_toon: str) -> None:
        '''Aadd sets to model.'''
        row: int = self.__model.rowCount()
        self.__model.setRowCount(row + 1)

        index = self.__model.index(row, 0, QModelIndex())
        self.__model.setData(index, pfx_toon)

        index = self.__model.index(row, 1, QModelIndex())
        self.__model.setData(index, None)

    def add_item_list(self, pfx_toons: list[str]) -> None:
        '''Add sets list to model.'''
        for pfx_toon in pfx_toons:
            self.add_item(pfx_toon)

    def update_model(self) -> None:
        '''Update UI.'''
        while self.__model.rowCount():
            self.__model.removeRow(0)

        self.add_item_list(get_pfx_toon())


# ==============================================================================
#
# Functions
#
# ==============================================================================
def __get_pfx_toon_surface_index(pfx_toon_shape: str, start: int) -> int:
    '''Return surface index from specific pfxToon.'''

    # TODO: Change the logic.
    for i in range(start, 10000000):
        connections_a: list[str] = cmds.connectionInfo(
            f'{pfx_toon_shape}.ins[{i}].srf', sourceFromDestination=True
        )
        connections_b: list[str] = cmds.connectionInfo(
            f'{pfx_toon_shape}.ins[{i}].iwm', sourceFromDestination=True
        )
        if len(connections_a) == 0 and len(connections_b) == 0:
            return i

    return i


def get_pfx_toon() -> list[str]:
    '''Return pfxToons in current scene.'''
    result: list[str] = []
    for pfx_toon in cmds.ls(type='pfxToon'):
        parent: list[str] = (
            cmds.listRelatives(pfx_toon, parent=True, path=True) or []
        )
        if not parent:
            continue

        result.append(cmds.ls(parent[0])[0])

    return result


@widgets.undo
def select_pfx_toon(pfx_toon: str, modifiers: Qt) -> None:
    '''Select pfxToon.'''
    kwargs = {}
    if modifiers == Qt.ShiftModifier:
        kwargs['tgl'] = True

    elif modifiers == Qt.ControlModifier:
        kwargs['d'] = True

    elif modifiers & Qt.ShiftModifier and modifiers & Qt.ControlModifier:
        kwargs['add'] = True

    cmds.select(pfx_toon, **kwargs)


@widgets.undo
def add_object_to_pfx_toon(pfx_toon: str) -> None:
    '''Add geometry to specific pfxToon.'''
    pfx_toon_shapes: list[str] = (
        cmds.listRelatives(pfx_toon, shapes=True, path=True) or []
    )
    if not pfx_toon_shapes:
        _logger.error('Failed to get pfxToon shape : %s', pfx_toon)
        return

    pfx_toon_shape: str = pfx_toon_shapes[0]

    org_selection: list[str] = cmds.ls(selection=True)
    selected: list[str] = cmds.ls(
        selection=True, dagObjects=True, noIntermediate=True, type=['mesh']
    )
    for node in selected:
        transforms: list[str] = (
            cmds.listRelatives(node, parent=True, path=True) or []
        )
        if not transforms:
            _logger.error('Failed to get transform: %s', node)
            continue

        transform: str = transforms[0]
        connectionList: list[str] = cmds.listConnections(
            f'{node}.outMesh', source=True, shapes=True
        )
        if connectionList and pfx_toon_shape in connectionList:
            continue

        choice: str = cmds.createNode('choice', name=f'{node}_choice')
        cmds.connectAttr(f'{node}.outMesh', f'{choice}.input[1]')
        cmds.connectAttr(f'{transform}.visibility', f'{choice}.selector')

        multi_index: int = __get_pfx_toon_surface_index(pfx_toon_shape, 0)
        cmds.connectAttr(
            f'{choice}.output', f'{pfx_toon_shape}.ins[{multi_index}].srf'
        )
        cmds.connectAttr(
            f'{node}.worldMatrix[0]', f'{pfx_toon_shape}.ins[{multi_index}].iwm'
        )

    if org_selection:
        cmds.select(*org_selection)


@widgets.undo
def remove_object_from_pfx_toon(pfx_toon: str) -> None:
    '''Remove geometry from specific pfxToon.'''
    pfx_toon_shapes: list[str] = (
        cmds.listRelatives(pfx_toon, shapes=True, path=True) or []
    )
    if not pfx_toon_shapes:
        _logger.error('Failed to get pfxToon shape : %s', pfx_toon)
        return

    pfx_toon_shape: str = pfx_toon_shapes[0]
    selected: list[str] = cmds.ls(
        selection=True, dagObjects=True, noIntermediate=True, type=['mesh']
    )
    for node in selected:
        output_plugs: list[str] = cmds.connectionInfo(
            f'{node}.outMesh', destinationFromSource=True
        )
        for output_plug in output_plugs:
            connected_node: str = output_plug.split('.')[0]
            if connected_node == pfx_toon_shape:
                cmds.disconnectAttr(f'{node}.outMesh', output_plug)

            elif cmds.nodeType(connected_node) == 'choice':
                is_delete: bool = False
                for _output_plug in cmds.connectionInfo(
                    f'{connected_node}.output', destinationFromSource=True
                ):
                    _connected_node: str = _output_plug.split('.')[0]
                    if _connected_node == pfx_toon_shape:
                        is_delete = True
                        cmds.disconnectAttr(
                            f'{connected_node}.output', _output_plug
                        )

                if is_delete:
                    cmds.delete(connected_node)

        world_mtx_plug: str = f'{node}.worldMatrix[0]'
        output_plugs = cmds.connectionInfo(
            world_mtx_plug, destinationFromSource=True
        )
        for output_plug in output_plugs:
            connected_node: str = output_plug.split('.')[0]
            if connected_node == pfx_toon_shape:
                cmds.disconnectAttr(world_mtx_plug, output_plug)


@widgets.undo
def delete_pfx_toon(pfx_toon: str) -> None:
    '''Delete pfxToon.'''
    cmds.delete(pfx_toon)

    # TODO: Find connected geometry from pfxToon.
    if cmds.objExists(f'{pfx_toon}_geo'):
        cmds.delete(f'{pfx_toon}_geo')

    # TODO: Find assigned material from geometry.
    if cmds.objExists(f'{pfx_toon}_MT'):
        cmds.delete(f'{pfx_toon}_MT')

    # TODO: Find connected shading group from material.
    if cmds.objExists(f'{pfx_toon}_MTSG'):
        cmds.delete(f'{pfx_toon}_MTSG')


@widgets.undo
def create_pfx_toon(camera: str = 'persp') -> str:
    '''Create pfxToon.'''

    selection: list[str] = cmds.ls(selection=True)

    # Create pfxToon transform
    pfx_toon: str = cmds.createNode('transform', name=f'{DEFAULT_NAME}_pfxToon')
    cmds.setAttr(f'{pfx_toon}.visibility', False)

    # Create pfxToon
    pfx_toon_shape: str = cmds.createNode(
        'pfxToon', name=f'{DEFAULT_NAME}Shape_pfxToon', parent=pfx_toon
    )
    cmds.setAttr(f'{pfx_toon_shape}.displayPercent', 100)
    cmds.setAttr(f'{pfx_toon_shape}.borderLines', 3)
    cmds.setAttr(f'{pfx_toon_shape}.intersectionLines', 1)
    cmds.setAttr(f'{pfx_toon_shape}.smoothProfile', 0)
    cmds.setAttr(f'{pfx_toon_shape}.creaseAngleMax', 25)
    cmds.setAttr(f'{pfx_toon_shape}.tighterProfile', 1)
    cmds.setAttr(f'{pfx_toon_shape}.selfIntersect', 1)
    cmds.setAttr(f'{pfx_toon_shape}.curvatureModulation', 1)
    cmds.setAttr(
        f'{pfx_toon_shape}.curvatureWidth[1].curvatureWidth_FloatValue', 0.8
    )
    cmds.setAttr(f'{pfx_toon_shape}.screenspaceWidth', 1)
    cmds.setAttr(f'{pfx_toon_shape}.distanceScaling', 1)
    cmds.setAttr(f'{pfx_toon_shape}.minPixelWidth', 1)
    cmds.setAttr(f'{pfx_toon_shape}.maxPixelWidth', 10)
    cmds.setAttr(f'{pfx_toon_shape}.meshHardEdges', 1)
    cmds.setAttr(f'{pfx_toon_shape}.meshQuadOutput', 1)
    cmds.setAttr(f'{pfx_toon_shape}.meshPolyLimit', 10000000)

    # Connect camera world position to cameraPoint.
    camera_decompose_mtx: str = cmds.createNode(
        'decomposeMatrix', name=f'{camera}_decomposeMtx'
    )
    cmds.connectAttr(
        f'{camera}.worldMatrix[0]', f'{camera_decompose_mtx}.inputMatrix'
    )
    cmds.connectAttr(
        f'{camera_decompose_mtx}.outputTranslate',
        f'{pfx_toon_shape}.cameraPoint',
        force=True,
    )

    # Assign selected nodes to pfxToon.
    if selection:
        cmds.select(*selection)
        add_object_to_pfx_toon(pfx_toon)

    # Create Mesh
    geo_trans: str = cmds.createNode('transform', name=f'{DEFAULT_NAME}_geo')
    geo_shape: str = cmds.createNode(
        'mesh', name=f'{DEFAULT_NAME}Shape_geo', parent=geo_trans
    )
    cmds.setAttr(f'{geo_shape}.castsShadows', 0)
    cmds.setAttr(f'{geo_shape}.receiveShadows', 0)
    cmds.setAttr(f'{geo_shape}.visibleInReflections', 0)
    cmds.setAttr(f'{geo_shape}.visibleInRefractions', 0)
    cmds.connectAttr(
        f'{pfx_toon_shape}.worldMainMesh[0]', f'{geo_shape}.inMesh'
    )

    # Material
    material: str = cmds.shadingNode(
        'surfaceShader', name=f'{DEFAULT_NAME}_MT', asShader=True
    )
    cmds.setAttr(f'{material}.outColor', *LINE_COLOR, type='double3')

    # Shading Group
    shading_group: str = cmds.sets(
        renderable=True,
        noSurfaceShader=True,
        empty=True,
        name=f'{DEFAULT_NAME}_MTSG',
    )
    cmds.connectAttr(f'{material}.outColor', f'{shading_group}.surfaceShader')

    # Assign material
    cmds.select(geo_trans)
    cmds.hyperShade(assign=shading_group)

    cmds.select(pfx_toon)
    return pfx_toon


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.update_model()
    window.show()
