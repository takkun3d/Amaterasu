# ==============================================================================
#
# Material Library
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging
import os
import json
import datetime

try:
    from PySide2.QtCore import Qt, Signal
    from PySide2.QtGui import QCloseEvent, QPixmap
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QGridLayout,
        QScrollArea,
        QStackedWidget,
        QLabel,
        QLineEdit,
        QTextEdit,
        QPushButton,
        QDialog,
        QMessageBox,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, Signal
        from PySide6.QtGui import QCloseEvent, QPixmap
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QGridLayout,
            QScrollArea,
            QStackedWidget,
            QLabel,
            QLineEdit,
            QTextEdit,
            QPushButton,
            QDialog,
            QMessageBox,
        )

from maya import cmds
from ..lib import parser, utility, widgets
from . import matcap
import amaterasu

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Material Library'
__version__: str = '1.00'
__doc__ = 'This tool manage material and matcap.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logging.Logger = logging.getLogger(__product__)

ROOT_DIR: str = os.path.join(amaterasu.USER_DATA_DIR, 'material_library')
ICON_SIZE_RANGE: tuple[int, int] = (64, 256)
NO_IMAGE: str = widgets.FileBrowserItem.no_image
DATE_FORMAT: str = '%Y/%m/%d/ %H:%M:%S'

ATTRIBUTE_TYPE_FILTER: list[str] = [
    'double',
    'doubleAngle',
    'doubleLinear',
    'int',
    'short',
    'long',
    'float',
    'bool',
    'string',
    'enum',
]
ANIM_CURVE_TYPE: list[str] = [
    'animCurveTL',
    'animCurveTA',
    'animCurveTU',
    'animCurveTT',
]


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    splitter_state: parser.Variant[str] = parser.Variant('')
    root_dir: parser.Variant[str] = parser.Variant(ROOT_DIR)
    filter: parser.Variant[str] = parser.Variant('')
    icon_size: parser.Variant[int] = parser.Variant(128)

    # pose_method: parser.Variant[int] = parser.Variant(0)
    # pose_keyframe: parser.Variant[bool] = parser.Variant(True)

    anim_method: parser.Variant[int] = parser.Variant(0)
    remove_animation: parser.Variant[bool] = parser.Variant(True)
    override_animation: parser.Variant[bool] = parser.Variant(False)
    is_time_range: parser.Variant[bool] = parser.Variant(False)
    start_frame: parser.Variant[int] = parser.Variant(1)
    end_frame: parser.Variant[int] = parser.Variant(120)


class Material:
    '''Material Data'''

    version: float = 1.0
    folder_extension: str = 'material'
    meta_file_name: str = 'meta.json'
    data_file_name: str = 'data.ma'

    def __init__(
        self,
        base_path: str,
        basename: str,
        comment: str = '',
        replace_namespace: str = '',
    ) -> None:
        '''Initialize'''
        self.__title: str = basename
        self.__metadata: dict[str, Any] = {
            'owner': utility.user_name(),
            'date': '',
            'version': self.version,
            'maya_version': cmds.about(apiVersion=True),
            'comment': comment,
        }
        self.__replace_namespace: str = replace_namespace
        self.__data: dict[str, dict[str, Any]] = {}

        self.__folder_name: str = f'{basename}.{self.folder_extension}'
        self.__root_path: str = os.path.join(base_path, self.__folder_name)
        self.__thumbnail_file_name: str = os.path.join(
            self.__root_path, widgets.FileBrowserItem.thumbnail_filename
        )
        self.__metadata_file_name: str = os.path.join(
            self.__root_path, self.meta_file_name
        )
        self.__material_file_name: str = os.path.join(
            self.__root_path, self.data_file_name
        )

    @classmethod
    def fromPath(cls, path: str) -> Material:
        '''Retrun instance from path.'''
        basename, extension = os.path.splitext(path)
        data_path = os.path.dirname(basename)
        basename = os.path.basename(basename)
        return cls(data_path, basename)

    def apply(self) -> bool:
        '''Apply material.'''
        cmds.file(
            self.__material_file_name,
            i=True,
            type='mayaAscii',
            ignoreVersion=True,
            mergeNamespacesOnClash=False,
            renamingPrefix=self.__title,
            options='v=0;',
            preserveReferences=True,
        )

        return True

    def read(self) -> None:
        '''Read material from file.'''
        self.__metadata = self.read_json(self.__metadata_file_name)

    def write(self, nodes: list[str]) -> bool:
        '''Write material data from objects.'''
        if not nodes:
            _logger.error('Specify the node where the material is to be saved.')
            return False

        if not os.path.exists(self.__root_path):
            try:
                os.makedirs(self.__root_path)
            except IOError as e:
                _logger.error('Failed to make folder. %s', e)

        temp: list[str] = []
        for node in nodes:
            if utility.is_surface_shader(node):
                temp.extend(utility.surface_shader(node))

        nodes.extend(temp)

        try:
            cmds.select(*nodes)
            cmds.file(
                self.__material_file_name,
                force=True,
                options='v=0;',
                type='mayaAscii',
                preserveReferences=True,
                exportSelected=True,
            )
        except ValueError as e:
            _logger.error('Failed to export file. %s', e)
            return False

        except RuntimeError as e:
            _logger.error('Failed to export file. %s', e)
            return False

        # Save metadata.
        self.__metadata['nodes'] = nodes
        self.__metadata['date'] = datetime.datetime.now().strftime(DATE_FORMAT)
        result = self.write_json(self.__metadata_file_name, self.__metadata)
        if not result:
            return False

        return True

    def title(self) -> str:
        '''Return title.'''
        return self.__title

    def owner(self) -> str:
        '''return owner in metadata.'''
        if 'owner' not in self.__metadata:
            return 'Unknown'

        return str(self.__metadata['owner'])

    def data_version(self) -> float:
        '''return version in metadata.'''
        if 'version' not in self.__metadata:
            return 0.0
        return float(self.__metadata['version'])

    def maya_version(self) -> int:
        '''return maya version in metadata.'''
        if 'maya_version' not in self.__metadata:
            return 0
        return int(self.__metadata['maya_version'])

    def comment(self) -> str:
        '''return comment in metadata.'''
        if 'comment' not in self.__metadata:
            return 'Unknown'
        return str(self.__metadata['comment'])

    def nodes(self) -> list[str]:
        '''return nodes'''
        return self.__metadata['nodes']

    def node_number(self) -> int:
        '''return object number of data.'''
        return len(self.__metadata['nodes'])

    def date(self) -> str:
        '''Return date in metadata.'''
        if 'date' not in self.__metadata:
            return 'Unknown'
        return str(self.__metadata['date'])

    def thumbnail(self) -> str:
        '''return thumbnail file name.''' ''
        return self.__thumbnail_file_name

    def set_thumbnail(self, path: str) -> None:
        '''Set thumbnail file path.'''
        self.__thumbnail_file_name = path

    def root_path(self) -> str:
        '''return root path.'''
        return self.__root_path

    def isExists(self) -> bool:
        '''return is exists.'''
        return os.path.exists(self.__root_path)

    def read_json(self, file_name: str) -> dict[str, Any]:
        '''Read data from json file.'''
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                datas: dict[str, Any] = json.load(f)
            return datas

        except IOError:
            _logger.error('Failed to write : %s', file_name)
            return {}

    def write_json(self, file_name: str, data: Any) -> bool:
        '''Write data to json file.'''
        try:
            with open(file_name, 'w', encoding='utf-8') as fw:
                json.dump(data, fw, sort_keys=True, indent=4)
            return True

        except IOError:
            _logger.error('Failed to write : %s', file_name)
            return False


class Matcap:
    '''Matcap Data'''

    version: float = 1.0
    folder_extension: str = 'matcap'
    meta_file_name: str = 'meta.json'
    data_file_name: str = 'data.png'

    def __init__(
        self,
        base_path: str,
        basename: str,
        comment: str = '',
        replace_namespace: str = '',
    ) -> None:
        '''Initialize'''
        self.__title: str = basename
        self.__metadata: dict[str, Any] = {
            'owner': utility.user_name(),
            'date': '',
            'version': self.version,
            'maya_version': cmds.about(apiVersion=True),
            'comment': comment,
        }
        self.__replace_namespace: str = replace_namespace

        self.__folder_name: str = f'{basename}.{self.folder_extension}'
        self.__root_path: str = os.path.join(base_path, self.__folder_name)
        self.__thumbnail_file_name: str = os.path.join(
            self.__root_path, widgets.FileBrowserItem.thumbnail_filename
        )
        self.__metadata_file_name: str = os.path.join(
            self.__root_path, self.meta_file_name
        )
        self.__matcap_file_name: str = os.path.join(
            self.__root_path, self.data_file_name
        )

    @classmethod
    def fromPath(cls, path: str) -> Matcap:
        '''Retrun instance from path.'''
        basename, extension = os.path.splitext(path)
        data_path = os.path.dirname(basename)
        basename = os.path.basename(basename)
        return cls(data_path, basename)

    def apply(self) -> bool:
        '''Apply matcap.'''
        matcap.apply(self.__title, self.__matcap_file_name, '', 0, False)
        return True

    def read(self) -> None:
        '''Read matcap from file.'''
        self.__metadata = self.read_json(self.__metadata_file_name)

    def write(self, matcap_map: str) -> bool:
        '''Write matcap data from objects.'''
        if not os.path.exists(self.__root_path):
            try:
                os.makedirs(self.__root_path)
            except IOError as e:
                _logger.error('Failed to make folder. %s', e)

        image = QPixmap(matcap_map)
        if not image.save(self.__matcap_file_name):
            return False

        # Save metadata.
        self.__metadata['date'] = datetime.datetime.now().strftime(DATE_FORMAT)
        result = self.write_json(self.__metadata_file_name, self.__metadata)
        return result

    def title(self) -> str:
        '''Return title.'''
        return self.__title

    def owner(self) -> str:
        '''return owner in metadata.'''
        if 'owner' not in self.__metadata:
            return 'Unknown'

        return str(self.__metadata['owner'])

    def data_version(self) -> float:
        '''return version in metadata.'''
        if 'version' not in self.__metadata:
            return 0.0
        return float(self.__metadata['version'])

    def maya_version(self) -> int:
        '''return maya version in metadata.'''
        if 'maya_version' not in self.__metadata:
            return 0
        return int(self.__metadata['maya_version'])

    def comment(self) -> str:
        '''return comment in metadata.'''
        if 'comment' not in self.__metadata:
            return 'Unknown'
        return str(self.__metadata['comment'])

    def nodes(self) -> list[str]:
        '''return nodes'''
        return ''  # self.__metadata['nodes']

    def node_number(self) -> int:
        '''return object number of data.'''
        return 0  # len(self.__metadata['nodes'])

    def date(self) -> str:
        '''Return date in metadata.'''
        if 'date' not in self.__metadata:
            return 'Unknown'
        return str(self.__metadata['date'])

    def thumbnail(self) -> str:
        '''return thumbnail file name.'''
        return self.__thumbnail_file_name

    def set_thumbnail(self, path: str) -> None:
        '''Set thumbnail file path.'''
        self.__thumbnail_file_name = path

    def root_path(self) -> str:
        '''return root path.'''
        return self.__root_path

    def isExists(self) -> bool:
        '''return is exists.'''
        return os.path.exists(self.__root_path)

    def read_json(self, file_name: str) -> dict[str, Any]:
        '''Read data from json file.'''
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                datas: dict[str, Any] = json.load(f)
            return datas

        except IOError:
            _logger.error('Failed to write : %s', file_name)
            return {}

    def write_json(self, file_name: str, data: Any) -> bool:
        '''Write data to json file.'''
        try:
            with open(file_name, 'w', encoding='utf-8') as fw:
                json.dump(data, fw, sort_keys=True, indent=4)
            return True

        except IOError:
            _logger.error('Failed to write : %s', file_name)
            return False


class SaveMaterialOption(QDialog):
    finished_save = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
        output_path: str = '',
    ) -> None:
        '''Initialize'''
        if not parent:
            parent = widgets.maya_window_to_qt()

        super().__init__(parent, flag)
        self.__output_path: str = output_path

        self.setObjectName('SaveMaterialOption' + str(id(self)))
        self.setWindowTitle('Save Material Options')
        self.resize(512, 256)

        main_layout: QGridLayout = QGridLayout(self)
        main_layout.setObjectName('Layout' + str(id(main_layout)))
        self.setLayout(main_layout)

        viewport_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setObjectName('Layout' + str(id(viewport_layout)))
        main_layout.addLayout(viewport_layout, 0, 0)

        label = QLabel('Thumbnail :', self)
        viewport_layout.addWidget(label)

        self.__viewport = widgets.ViewportCapture(self, is_shader_ball=True)
        self.__viewport.set_image_size(256, 256)
        viewport_layout.addWidget(self.__viewport)
        viewport_layout.addStretch(True)

        option_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.addLayout(option_layout, 0, 1)

        label = QLabel('Name :', self)
        option_layout.addWidget(label)

        self.__name = QLineEdit(self)
        option_layout.addWidget(self.__name)

        label = QLabel('Comment :', self)
        option_layout.addWidget(label)

        self.__comment = QTextEdit(self)
        self.__comment.setMaximumHeight(50)
        option_layout.addWidget(self.__comment)

        option_layout.addWidget(widgets.HorizontalLine(self))

        label = QLabel('Replace Namespace : ', self)
        option_layout.addWidget(label)

        self.__replace_namespace = QLineEdit(self)
        option_layout.addWidget(self.__replace_namespace)
        option_layout.addStretch(True)

        button = QPushButton('Save', self)
        button.clicked.connect(self.save)
        main_layout.addWidget(button, 1, 0, 1, 2)

    def save(self) -> None:
        '''Save material data.'''
        name: str = self.__name.text()
        comment: str = self.__comment.toPlainText()
        replace_namespace: str = self.__replace_namespace.text()
        if replace_namespace != '' and replace_namespace[-1] != ':':
            replace_namespace += ':'

        if name == '':
            QMessageBox.critical(
                self,
                'Save Material Option',
                'A name must be entered to save a material.',
            )
            return

        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            QMessageBox.critical(
                self,
                'Save Material Option',
                'Select node(s) to save a material.',
            )
            return

        namespaces: list[str] = utility.extract_namespaces(selection)
        if len(namespaces) >= 2:
            QMessageBox.critical(
                self,
                'Save Material Option',
                f'You must select only one asset.\nFound name spaces {namespaces}',
            )
            return

        material = Material(
            self.__output_path, name, comment, replace_namespace
        )
        if material.isExists():
            result = QMessageBox.question(
                self,
                'Save Material Option',
                'Material is already exists.\nDo you want to override?',
            )
            if result != QMessageBox.Yes:
                return

        if not material.write(selection):
            return

        if not self.__viewport.capture(material.thumbnail()):
            return

        self.finished_save.emit(material.root_path())
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        '''Close Event[override]'''
        self.__viewport.cleanup()
        super().closeEvent(event)


class SaveMatcapOption(QDialog):
    finished_save = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
        output_path: str = '',
    ) -> None:
        '''Initialize'''
        if not parent:
            parent = widgets.maya_window_to_qt()

        super().__init__(parent, flag)
        self.__output_path: str = output_path

        self.setObjectName('SaveMatcapOption' + str(id(self)))
        self.setWindowTitle('Save Matcap Options')
        self.resize(512, 256)

        main_layout: QGridLayout = QGridLayout(self)
        main_layout.setObjectName('Layout' + str(id(main_layout)))
        self.setLayout(main_layout)

        viewport_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setObjectName('Layout' + str(id(viewport_layout)))
        main_layout.addLayout(viewport_layout, 0, 0)

        label = QLabel('Matcap Map :', self)
        viewport_layout.addWidget(label)

        self.__image = widgets.DropImage(self, 256, 256)
        viewport_layout.addWidget(self.__image)
        viewport_layout.addStretch(True)

        option_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.addLayout(option_layout, 0, 1)

        label = QLabel('Name :', self)
        option_layout.addWidget(label)

        self.__name = QLineEdit(self)
        option_layout.addWidget(self.__name)

        label = QLabel('Comment :', self)
        option_layout.addWidget(label)

        self.__comment = QTextEdit(self)
        self.__comment.setMaximumHeight(50)
        option_layout.addWidget(self.__comment)
        option_layout.addStretch(True)

        button = QPushButton('Save', self)
        button.clicked.connect(self.save)
        main_layout.addWidget(button, 1, 0, 1, 2)

    def save(self) -> None:
        '''Save matcap data.'''
        name: str = self.__name.text()
        comment: str = self.__comment.toPlainText()

        if name == '':
            QMessageBox.critical(
                self,
                'Save Matcap Option',
                'A name must be entered to save a matcap.',
            )
            return

        image_path: str = self.__image.file_path()
        if not os.path.exists(image_path):
            QMessageBox.critical(
                self,
                'Save Matcap Option',
                'A image must be entered to save a matcap.',
            )
            return

        matcap = Matcap(
            self.__output_path,
            name,
            comment,
            '',
        )
        if matcap.isExists():
            result = QMessageBox.question(
                self,
                'Save Matcap Option',
                'Matcap is already exists.\nDo you want to override?',
            )
            if result != QMessageBox.Yes:
                return

        if not matcap.write(image_path):
            QMessageBox.critical(
                self, 'Save Matcap Option', 'Failed to save matcap map.'
            )
            return

        image = QPixmap(image_path)
        image.scaled(256, 256)
        if not image.save(matcap.thumbnail()):
            QMessageBox.critical(
                self, 'Save Matcap Option', 'Failed to save thumbnail.'
            )
            return

        self.finished_save.emit(matcap.root_path())
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        '''Close Event[override]'''
        super().closeEvent(event)


class MaterialOption(QWidget):
    '''Material option widget'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize'''
        super().__init__(parent, flag)
        self.__material: Material = Material('', '')
        self.__no_image: QPixmap = widgets.pixmap_from_file_name(NO_IMAGE)

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.addWidget(QLabel('<h2>Material</h2>'))

        scroll_area: QScrollArea = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFocusPolicy(Qt.NoFocus)
        scroll_area.setMinimumWidth(ICON_SIZE_RANGE[1] + 40)
        scroll_area.setMinimumHeight(1)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        main_layout.addWidget(scroll_area)

        inner_widget: QWidget = QWidget(self)
        scroll_area.setWidget(inner_widget)

        inner_layout: QVBoxLayout = QVBoxLayout(self)
        inner_widget.setLayout(inner_layout)

        self.__image: QLabel = QLabel(self)
        self.__image.setAlignment(Qt.AlignCenter)
        self.__image.setMinimumSize(ICON_SIZE_RANGE[1], ICON_SIZE_RANGE[1])
        self.__image.setPixmap(self.__no_image)
        inner_layout.addWidget(self.__image)

        inner_layout.addWidget(widgets.HorizontalLine(self))

        fileinfo_layout: widgets.QFormLayout = widgets.FormLayout(self)
        fileinfo_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.addLayout(fileinfo_layout)

        self.__file_name: QLabel = QLabel(self)
        fileinfo_layout.addRow('File Name : ', self.__file_name)

        self.__owner: QLabel = QLabel(self)
        fileinfo_layout.addRow('Owner : ', self.__owner)

        self.__date: QLabel = QLabel(self)
        fileinfo_layout.addRow('Date : ', self.__date)

        self.__nodes: QLabel = QLabel(self)
        fileinfo_layout.addRow('Nodes : ', self.__nodes)

        self.__comment: QTextEdit = QTextEdit(self)
        self.__comment.setReadOnly(True)
        self.__comment.setFixedHeight(45)
        fileinfo_layout.addRow('Comment : ', self.__comment)
        inner_layout.addStretch(True)

        button: QPushButton = QPushButton('Import', self)
        button.clicked.connect(self.apply)
        main_layout.addWidget(button)

    def set_file(self, material: Material) -> None:
        '''Set file'''
        self.__material = material
        self.__material.read()

        if self.__material.thumbnail() != '':
            pixmap: QPixmap = QPixmap(self.__material.thumbnail())
            if pixmap.width() > pixmap.height():
                pixmap = pixmap.scaledToWidth(ICON_SIZE_RANGE[1])
            else:
                pixmap = pixmap.scaledToHeight(ICON_SIZE_RANGE[1])
            self.__image.setPixmap(pixmap)
        else:
            self.__image.setPixmap(self.__no_image)

        self.__file_name.setText(self.__material.title())
        self.__owner.setText(self.__material.owner())
        self.__date.setText(self.__material.date())
        self.__nodes.setText(f'{self.__material.node_number()} Object(s)')
        self.__comment.setText(self.__material.comment())

    @widgets.undo
    def apply(self) -> None:
        '''Apply pose data.'''
        self.__material.apply()


class MatcapOption(QWidget):
    '''Anim option widget'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize'''
        super().__init__(parent, flag)
        self.__matcap: Matcap = Matcap('', '')
        self.__no_image: QPixmap = widgets.pixmap_from_file_name(NO_IMAGE)

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.addWidget(QLabel('<h2>Matcap</h2>'))

        scroll_area: QScrollArea = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFocusPolicy(Qt.NoFocus)
        scroll_area.setMinimumWidth(ICON_SIZE_RANGE[1] + 40)
        scroll_area.setMinimumHeight(1)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        main_layout.addWidget(scroll_area)

        inner_widget: QWidget = QWidget(self)
        scroll_area.setWidget(inner_widget)

        inner_layout: QVBoxLayout = QVBoxLayout(self)
        inner_widget.setLayout(inner_layout)

        self.__image: QLabel = QLabel(self)
        self.__image.setAlignment(Qt.AlignCenter)
        self.__image.setMinimumSize(ICON_SIZE_RANGE[1], ICON_SIZE_RANGE[1])
        self.__image.setPixmap(self.__no_image)
        inner_layout.addWidget(self.__image)

        inner_layout.addWidget(widgets.HorizontalLine(self))

        fileinfo_layout: widgets.QFormLayout = widgets.FormLayout(self)
        fileinfo_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.addLayout(fileinfo_layout)

        self.__file_name: QLabel = QLabel(self)
        fileinfo_layout.addRow('File Name : ', self.__file_name)

        self.__owner: QLabel = QLabel(self)
        fileinfo_layout.addRow('Owner : ', self.__owner)

        self.__date: QLabel = QLabel(self)
        fileinfo_layout.addRow('Date : ', self.__date)

        self.__nodes: QLabel = QLabel(self)
        fileinfo_layout.addRow('Nodes : ', self.__nodes)

        self.__comment: QTextEdit = QTextEdit(self)
        self.__comment.setReadOnly(True)
        self.__comment.setFixedHeight(45)
        fileinfo_layout.addRow('Comment : ', self.__comment)
        inner_layout.addStretch(True)

        button: QPushButton = QPushButton('Import', self)
        button.clicked.connect(self.apply)
        main_layout.addWidget(button)

        self.update_ui_enabled()

    def update_ui_enabled(self) -> None:
        '''Update ui enabled.'''

    def set_file(self, matcap: Matcap) -> None:
        '''Set file'''
        self.__matcap = matcap
        self.__matcap.read()

        if self.__matcap.thumbnail() != '':
            pixmap: QPixmap = QPixmap(self.__matcap.thumbnail())
            if pixmap.width() > pixmap.height():
                pixmap = pixmap.scaledToWidth(ICON_SIZE_RANGE[1])
            else:
                pixmap = pixmap.scaledToHeight(ICON_SIZE_RANGE[1])
            self.__image.setPixmap(pixmap)
        else:
            self.__image.setPixmap(self.__no_image)

        self.__file_name.setText(self.__matcap.title())
        self.__owner.setText(self.__matcap.owner())
        self.__date.setText(self.__matcap.date())
        self.__nodes.setText(f'{self.__matcap.node_number()} Object(s)')
        self.__comment.setText(self.__matcap.comment())

    @widgets.undo
    def apply(self) -> None:
        '''Apply matcap data.'''
        self.__matcap.apply()


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

        layout = QVBoxLayout(self.option_widget())
        layout.setContentsMargins(0, 0, 0, 0)

        # File Brower
        self.__file_browser = widgets.FileBrowser(self)
        self.__file_browser.item_selected.connect(self.item_select_callback)

        self.__file_browser.add_file_view_button(
            1,
            'New Material',
            'a_add_material.png',
            self.show_new_material_option,
        )
        self.__file_browser.add_file_view_button(
            2,
            'New Matcap',
            'a_add_texture.png',
            self.show_new_matcap_option,
        )
        layout.addWidget(self.__file_browser)

        # Option Widget
        self.__stack_option: QStackedWidget = QStackedWidget(self)
        self.__file_browser.add_option_widget(self.__stack_option)

        self.__material_option: MaterialOption = MaterialOption(self)
        self.__matcap_option: Matcap = MatcapOption(self)
        self.__stack_option.addWidget(QWidget(self))
        self.__stack_option.addWidget(self.__material_option)
        self.__stack_option.addWidget(self.__matcap_option)

        # Menu
        # menu_bar = self.menu_bar()
        # view_menu = menu_bar.addMenu('View')
        # menu_bar.insertMenu(self.help_menu().menuAction(), view_menu)

        # action = view_menu.addAction('Update')
        # action.triggered.connect(self.update_view)

    def item_select_callback(self, file_item: widgets.FileBrowserItem) -> None:
        '''Item selected callback.'''
        extension = file_item.extension()
        if extension == 'material':
            self.__stack_option.setCurrentIndex(1)
            material = Material.fromPath(file_item.data_path())
            material.set_thumbnail(file_item.icon_path())
            self.__material_option.set_file(material)

        elif extension == 'matcap':
            self.__stack_option.setCurrentIndex(2)
            matcap = Matcap.fromPath(file_item.data_path())
            matcap.set_thumbnail(file_item.icon_path())
            self.__matcap_option.set_file(matcap)

        else:
            self.__stack_option.setCurrentIndex(0)

    def show_new_material_option(self, path: str) -> None:
        '''Show new material option'''
        option = SaveMaterialOption(output_path=path)
        option.finished_save.connect(self.save_item_callback)
        option.show()

    def show_new_matcap_option(self, path: str) -> None:
        '''Show new matcap option'''
        option = SaveMatcapOption(output_path=path)
        option.finished_save.connect(self.save_item_callback)
        option.show()

    def save_item_callback(self, path: str) -> None:
        '''Callback after save item.'''
        self.__file_browser.add_item(path)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__file_browser.splitter_widget().restoreState(
            widgets.to_qt(settings.splitter_state.value())
        )
        self.__file_browser.set_root_path(settings.root_dir.value())
        self.__file_browser.set_filter_text(settings.filter.value())
        self.__file_browser.set_icon_range(
            settings.icon_size.value(), ICON_SIZE_RANGE[0], ICON_SIZE_RANGE[1]
        )

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        # Window
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.splitter_state.set_value(
            widgets.to_ascii(self.__file_browser.splitter_widget().saveState())
        )
        settings.root_dir.set_value(self.__file_browser.root_path())
        settings.filter.set_value(self.__file_browser.filter())
        settings.icon_size.set_value(self.__file_browser.icon_size())
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
def main() -> None:
    '''Show window.'''
    if not os.path.exists(ROOT_DIR):
        try:
            os.makedirs(ROOT_DIR)
        except IOError as e:
            _logger.error('Failed to make folder. %s', e)

    window: MainWindow = MainWindow()
    window.show()
