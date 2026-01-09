# ==============================================================================
#
# Anim Library
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
        QHBoxLayout,
        QGridLayout,
        QScrollArea,
        QStackedWidget,
        QLabel,
        QLineEdit,
        QTextEdit,
        QCheckBox,
        QSpinBox,
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
            QHBoxLayout,
            QGridLayout,
            QScrollArea,
            QStackedWidget,
            QLabel,
            QLineEdit,
            QTextEdit,
            QCheckBox,
            QSpinBox,
            QPushButton,
            QDialog,
            QMessageBox,
        )

from maya import cmds
from ..lib import parser, utility, widgets
import amaterasu

# atomImport時に、ループの設定が消えるバグの対応(2022.3では治ってる？)

# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Anim Library'
__version__: str = '1.20'
__doc__ = 'This tool manage poses and animation.'
__copyright__ = 'Copyright(c) 2014-2024 @takkun3d. All Rights Reserved.'
_logger: logging.Logger = logging.getLogger(__product__)

ROOT_DIR: str = os.path.join(amaterasu.USER_DATA_DIR, 'anim_library')
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
]  # TODO: utity.getAnimCurves or utity.getAnimCurveに変更可能?


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

    pose_method: parser.Variant[int] = parser.Variant(0)
    pose_keyframe: parser.Variant[bool] = parser.Variant(True)

    anim_method: parser.Variant[int] = parser.Variant(0)
    remove_animation: parser.Variant[bool] = parser.Variant(True)
    override_animation: parser.Variant[bool] = parser.Variant(False)
    is_time_range: parser.Variant[bool] = parser.Variant(False)
    start_frame: parser.Variant[int] = parser.Variant(1)
    end_frame: parser.Variant[int] = parser.Variant(120)


class Pose:
    '''Pose Data'''

    version: float = 1.0
    folder_extension: str = 'pose'
    meta_file_name: str = 'meta.json'
    data_file_name: str = 'data.json'

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
        self.__pose_file_name: str = os.path.join(
            self.__root_path, self.data_file_name
        )

    @classmethod
    def fromPath(cls, path: str) -> Pose:
        '''Retrun instance from path.'''
        basename, extension = os.path.splitext(path)
        data_path = os.path.dirname(basename)
        basename = os.path.basename(basename)
        return cls(data_path, basename)

    def apply(self, method: int = 0, keyframe: bool = False) -> bool:
        '''Apply pose.'''
        self.__data = self.read_json(self.__pose_file_name)
        if method == 0:
            return self.apply_from_selection(keyframe)

        else:
            return self.apply_from_file(keyframe)

    def apply_from_selection(self, keyframe: bool = False) -> bool:
        '''Apply pose data from selection.'''
        selection = cmds.ls(selection=True)
        if not selection:
            _logger.error('Select node to apply pose data.')
            return False

        for node in selection:
            dst_namespace: str = utility.extract_namespace(node)
            for src_node, attrs in self.__data.items():
                src_namespace: str = utility.extract_namespace(src_node)

                search: str = ''
                replace: str = ''
                prefix: str = ''
                suffix: str = ''
                if not src_namespace and not dst_namespace:
                    # Has not Namespace > Has not Namespace
                    pass

                elif not src_namespace and dst_namespace:
                    # Has not Namespace > Has Namespace
                    prefix = dst_namespace

                elif src_namespace and not dst_namespace:
                    # Has Namespace > Has not Namespace
                    search = src_namespace
                    replace = ''

                elif src_namespace and dst_namespace:
                    # Has Namespace > Has Namespace
                    search = src_namespace
                    replace = dst_namespace

                for attr, value in attrs.items():
                    result: int = Pose.set_value(
                        src_node,
                        attr,
                        value,
                        keyframe,
                        search,
                        replace,
                        prefix,
                        suffix,
                        node,
                    )
                    if result == -1:
                        _logger.warning(
                            '%s Does not exists node. skipped.', src_node
                        )
                        break

                    elif result == -2:
                        _logger.warning('Field to set value. %s.%s', node, attr)
        return True

    def apply_from_file(self, keyframe: bool = False) -> bool:
        '''Appy pose data from file.'''

        # Make namespace table from selection
        selection: list[str] = cmds.ls(selection=True)
        dst_namespaces: list[str] = utility.extract_namespaces(selection)

        for node, attrs in self.__data.items():
            result: int = 1
            for attr, value in attrs.items():
                src_namespace: str = utility.extract_namespace(node)

                if not src_namespace and not dst_namespaces:
                    # Has not Namespace > Has not Namespace
                    result = Pose.set_value(node, attr, value, keyframe)
                    if result == -1:
                        _logger.error(
                            '%s does not exists. Try the Selection Mode.',
                            node,
                        )
                        break

                    elif result == -2:
                        _logger.warning('Field to set value. %s.%s', node, attr)

                elif not src_namespace and dst_namespaces:
                    # Has not Namespace > Has Namespace
                    for dst_namespace in dst_namespaces:
                        result = Pose.set_value(
                            node, attr, value, keyframe, '', '', dst_namespace
                        )
                        if result == -1:
                            _logger.error(
                                '%s does not exists. Try the Selection Mode.',
                                node,
                            )
                            break

                        elif result == -2:
                            _logger.warning(
                                'Field to set value. %s.%s', node, attr
                            )
                    else:
                        continue
                    break

                elif src_namespace and not dst_namespaces:
                    # Has Namespace > Has not Namespace
                    dst_namespace = '' if selection else src_namespace
                    result = Pose.set_value(
                        node,
                        attr,
                        value,
                        keyframe,
                        src_namespace,
                        dst_namespace,
                    )
                    if result == -1:
                        _logger.error(
                            '%s does not exists. Try the Selection Mode.',
                            node,
                        )
                        break

                    elif result == -2:
                        _logger.warning('Field to set value. %s.%s', node, attr)

                elif src_namespace and dst_namespaces:
                    # Has Namespace > Has Namespace
                    for dst_namespace in dst_namespaces:
                        result = Pose.set_value(
                            node,
                            attr,
                            value,
                            keyframe,
                            src_namespace,
                            dst_namespace,
                        )
                        if result == -1:
                            _logger.error(
                                '%s does not exists. Try the Selection Mode.',
                                node,
                            )
                            break

                        elif result == -2:
                            _logger.warning(
                                'Field to set value. %s.%s', node, attr
                            )
                    else:
                        continue
                    break

        return True

    @staticmethod
    def set_value(
        node: str,
        attr: str,
        value: Any,
        keyframe: bool,
        search: str = '',
        replace: str = '',
        prefix: str = '',
        suffix: str = '',
        filter: str = '',
    ) -> int:
        ''' '
        Set value.

        Return
        -1 : Does not exists object.
        -2 : Does not exists attribute at object.[RuntimeError]
        0 : Filtered
        1 : Success
        '''
        node = prefix + node.replace(search, replace) + suffix
        if not cmds.objExists(node):
            return -1

        if filter and node != filter:
            return 0

        try:
            plug: str = f'{node}.{attr}'
            cmds.setAttr(plug, value)
            if keyframe:
                cmds.setKeyframe(plug)

        except RuntimeError:
            return -2

        return 1

    def read(self) -> None:
        '''Read pose from file.'''
        self.__metadata = self.read_json(self.__metadata_file_name)

    def write(self, nodes: list[str]) -> bool:
        '''Write pose data from objects.'''
        if not nodes:
            _logger.error('Specify the node where the pose is to be saved.')
            return False

        if not os.path.exists(self.__root_path):
            try:
                os.makedirs(self.__root_path)
            except IOError as e:
                _logger.error('Failed to make folder. %s', e)

        # Save data.
        result = self.write_json(
            self.__pose_file_name,
            self.read_from_nodes(nodes),
        )
        if not result:
            return False

        # Save metadata.
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

    def read_from_nodes(self, nodes: list[str]) -> dict[str, dict[str, Any]]:
        '''Return pose data from selection.'''

        # Replace namespace to save metadata.
        self.__metadata['namespace'] = utility.extract_namespace(nodes[0])
        if self.__replace_namespace != '':
            self.__metadata['namespace'] = self.__replace_namespace

        self.__data = {}
        self.__metadata['nodes'] = []
        for node in nodes:
            attributes: list[str] = (
                cmds.listAttr(node, keyable=True, unlocked=True) or []
            )

            # Replace namespace to save data.
            namespace: str = utility.extract_namespace(node)
            save_node_name: str = node
            if self.__replace_namespace != '':
                save_node_name = node.replace(
                    namespace, self.__replace_namespace
                )

            self.__data[save_node_name] = {}
            self.__metadata['nodes'].append(save_node_name)
            for attribute in attributes:
                plug: str = f'{node}.{attribute}'
                try:
                    attribute_type: str = cmds.getAttr(plug, type=True)
                except ValueError:
                    continue

                if attribute_type not in ATTRIBUTE_TYPE_FILTER:
                    continue

                value: Any = cmds.getAttr(plug)
                self.__data[save_node_name][attribute] = value

        return self.__data

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


class Animation:
    '''Animation Data'''

    version: float = 1.0
    folder_extension: str = 'anim'
    meta_file_name: str = 'meta.json'
    data_file_name: str = 'data.atom'

    def __init__(
        self,
        base_path: str,
        basename: str,
        comment: str = '',
        replace_namespace: str = '',
        # start_frame: int | None = None,
        # end_frame: int | None = None,
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
        # self.__start_frame: int | None = start_frame
        # self.__end_frame: int | None = end_frame

        self.__folder_name: str = f'{basename}.{self.folder_extension}'
        self.__root_path: str = os.path.join(base_path, self.__folder_name)
        self.__thumbnail_file_name: str = os.path.join(
            self.__root_path, widgets.FileBrowserItem.thumbnail_filename
        )
        self.__metadata_file_name: str = os.path.join(
            self.__root_path, self.meta_file_name
        )
        self.__anim_file_name: str = os.path.join(
            self.__root_path, self.data_file_name
        )

    @classmethod
    def fromPath(cls, path: str) -> Animation:
        '''Retrun instance from path.'''
        basename, extension = os.path.splitext(path)
        data_path = os.path.dirname(basename)
        basename = os.path.basename(basename)
        return cls(data_path, basename)

    def apply(
        self,
        method: int = 0,
        remove_animation: bool = True,
        override_animation: bool = False,
        start_frame: int | None = None,
        end_frame: int | None = None,
    ) -> bool:
        '''Apply pose.'''
        if method == 0:
            return self.apply_from_selection(
                remove_animation, override_animation, start_frame, end_frame
            )

        else:
            return self.apply_from_file(
                remove_animation, override_animation, start_frame, end_frame
            )

    def remove_animation(self, nodes: list[str]) -> None:
        '''Remove animation'''
        for node in nodes:
            connections: list[str] = cmds.listConnections(
                node, source=True, destination=False
            )
            if not connections:
                continue

            for connection in connections:
                if cmds.nodeType(connection) in ANIM_CURVE_TYPE:
                    cmds.delete(connection)

    def apply_from_selection(
        self,
        remove_animation: bool = True,
        override_animation: bool = False,
        start_frame: int | None = None,
        end_frame: int | None = None,
    ) -> bool:
        '''Apply pose data from selection.'''
        selection = cmds.ls(selection=True)
        if not selection:
            _logger.error('Select node to apply animation data.')
            return False

        if remove_animation:
            self.remove_animation(selection)

        namespaces: dict[str, list[str]] = utility.list_to_per_namespace(
            selection
        )
        for dst_namespace, nodes in namespaces.items():
            src_namespace: str = self.__metadata["namespace"]

            search: str = ''
            replace: str = ''
            prefix: str = ''
            suffix: str = ''
            if not src_namespace and not dst_namespace:
                # Has not Namespace > Has not Namespace
                pass

            elif not src_namespace and dst_namespace:
                # Has not Namespace > Has Namespace
                prefix = dst_namespace

            elif src_namespace and not dst_namespace:
                # Has Namespace > Has not Namespace
                search = src_namespace
                replace = ''

            elif src_namespace and dst_namespace:
                # Has Namespace > Has Namespace
                search = src_namespace
                replace = dst_namespace

            result: bool = Animation.import_atom(
                self.__anim_file_name,
                nodes,
                search,
                replace,
                prefix,
                suffix,
                override_animation,
                start_frame,
                end_frame,
                selection,
            )
            if not result:
                _logger.error('Failed to import file.')

        return True

    def apply_from_file(
        self,
        remove_animation: bool = True,
        override_animation: bool = False,
        start_frame: int | None = None,
        end_frame: int | None = None,
    ) -> bool:
        '''Appy pose data from file.'''
        selection = cmds.ls(selection=True)
        namespaces: list[str] = utility.extract_namespaces(selection)
        if not namespaces:
            namespaces.append('')  # No namespace.

        if remove_animation:
            self.remove_animation(selection)

        for dst_namespace in namespaces:
            src_namespace: str = self.__metadata['namespace']

            search: str = ''
            replace: str = ''
            prefix: str = ''
            suffix: str = ''
            if not src_namespace and not dst_namespace:
                # Has not Namespace > Has not Namespace
                pass

            elif not src_namespace and dst_namespace:
                # Has not Namespace > Has Namespace
                prefix = dst_namespace

            elif src_namespace and not dst_namespace:
                # Has Namespace > Has not Namespace
                search = src_namespace
                replace = ''

            elif src_namespace and dst_namespace:
                # Has Namespace > Has Namespace
                search = src_namespace
                replace = dst_namespace

            result: bool = Animation.import_atom(
                self.__anim_file_name,
                self.__metadata['nodes'],
                search,
                replace,
                prefix,
                suffix,
                override_animation,
                start_frame,
                end_frame,
            )
            if not result:
                _logger.error('Failed to import file.')

        return True

    @staticmethod
    def import_atom(
        anim_file: str,
        nodes: list[str],
        search: str = '',
        replace: str = '',
        prefix: str = '',
        suffix: str = '',
        replace_anim: bool = False,
        start_frame: int | None = None,
        end_frame: int | None = None,
        filter: list[str] | None = None,
    ) -> bool:
        'Import animation by atom.'
        if filter is None:
            filter = []

        nodes: list[str] = [
            prefix + n.replace(search, replace) + suffix for n in nodes
        ]
        if filter:
            nodes = [n for n in nodes if n in filter]

        try:
            cmds.select(*nodes)
        except ValueError:
            _logger.error('Does not exists node. %s', nodes)
            return False

        target_time: int = 3
        time_flag: str = ''
        option: str = 'insert'
        if start_frame is not None and end_frame is not None:
            option = 'scaleReplace'
            time_flag = f'srcTime={start_frame}:{end_frame};dstTime={start_frame}:{end_frame};'
            target_time = 1

        if replace_anim:
            option = 'scaleReplace'

        options: str = (
            ';'
            + ';'
            + f'targetTime={target_time};'
            + time_flag
            + f'option={option};'
            + 'match=string;'
            + ';'
            + 'selected=selectedOnly;'
            + f'search={search};'
            + f'replace={replace};'
            + f'prefix={prefix};'
            + f'suffix={suffix};'
            + 'mapFile=;'
        )
        cmds.file(
            anim_file,
            i=True,
            type='atomImport',
            renameAll=True,
            namespace='AnimLibraryAnimImport',
            options=options,
        )
        return True

    def read(self) -> None:
        '''Read animation from file.'''
        self.__metadata = self.read_json(self.__metadata_file_name)

    def write(
        self,
        nodes: list[str],
        start_frame: int | None = None,
        end_frame: int | None = None,
    ) -> bool:
        '''Write animation data from objects.'''
        if not nodes:
            _logger.error(
                'Specify the node where the animation is to be saved.'
            )
            return False

        self.__metadata['nodes'] = []
        filtered_node: list[str] = []
        for node in nodes:
            # Check animation.
            if not utility.has_animation(node):
                continue

            # Replace namespace.
            namespace: str = utility.extract_namespace(node)
            node_name: str = node
            if self.__replace_namespace != '':
                node_name = node.replace(namespace, self.__replace_namespace)

            self.__metadata['nodes'].append(node_name)
            filtered_node.append(node)

        if not filtered_node:
            _logger.error(
                'Specify the node where the animation is to be saved.'
            )
            return False

        self.__metadata['namespace'] = utility.extract_namespace(
            self.__metadata['nodes'][0]
        )
        namespace = utility.extract_namespace(filtered_node[0])

        if not os.path.exists(self.__root_path):
            try:
                os.makedirs(self.__root_path)
            except IOError as e:
                _logger.error('Failed to make folder. %s', e)

        cmds.select(*filtered_node)

        # Make atom option.
        which_range: int = 1
        copy_key_cmd_time_rage: str = ''
        if start_frame is not None and end_frame is not None:
            which_range = 2
            copy_key_cmd_time_rage = f'-time >{start_frame}:{end_frame}> -float >{start_frame}:{end_frame}>'
        else:
            start_frame = 1
            end_frame = 120

        options: str = (
            'precision=8;'
            + 'statics=1;'
            + 'baked=0;'
            + 'sdk=0;'
            + 'constraint=0;'
            + 'animLayers=0;'
            + 'selected=selectedOnly;'
            + f'whichRange={which_range};'
            + f'range={start_frame}:{end_frame};'
            + 'hierarchy=none;'
            + 'controlPoints=0;'
            + 'useChannelBox=1;'
            + 'options=keys;'
            + f'copyKeyCmd=-animation objects {copy_key_cmd_time_rage} -option keys -hierarchy none -controlPoints 0 '
        )

        # Save atom.
        try:
            cmds.file(
                self.__anim_file_name,
                force=True,
                options=options,
                constructionHistory=True,
                type='atomExport',
                exportSelected=True,
            )

            # Modify atom file.
            if self.__replace_namespace != '':
                with open(self.__anim_file_name, 'r', encoding='utf-8') as f:
                    all_lines: list[str] = f.readlines()

                for i, line in enumerate(all_lines):
                    all_lines[i] = line.replace(
                        namespace, self.__replace_namespace
                    )

                with open(
                    self.__anim_file_name, 'w', encoding='utf-8', newline='\n'
                ) as fw:
                    fw.writelines(all_lines)

        except RuntimeError as e:
            _logger.error('Failed to export animation data. %s', e)
            return False

        # Save metadata.
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


class SavePoseOption(QDialog):
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

        self.setObjectName('SavePoseOption' + str(id(self)))
        self.setWindowTitle('Save Pose Options')
        self.resize(512, 256)

        main_layout: QGridLayout = QGridLayout(self)
        main_layout.setObjectName('Layout' + str(id(main_layout)))
        self.setLayout(main_layout)

        viewport_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setObjectName('Layout' + str(id(viewport_layout)))
        main_layout.addLayout(viewport_layout, 0, 0)

        label = QLabel('Thumbnail :', self)
        viewport_layout.addWidget(label)

        self.__viewport = widgets.ViewportCapture(self)
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
        '''Save pose data.'''
        name: str = self.__name.text()
        comment: str = self.__comment.toPlainText()
        replace_namespace: str = self.__replace_namespace.text()
        if replace_namespace != '' and replace_namespace[-1] != ':':
            replace_namespace += ':'

        if name == '':
            QMessageBox.critical(
                self,
                'Save Pose Option',
                'A name must be entered to save a pose.',
            )
            return

        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            QMessageBox.critical(
                self, 'Save Pose Option', 'Select node(s) to save a pose.'
            )
            return

        namespaces: list[str] = utility.extract_namespaces(selection)
        if len(namespaces) >= 2:
            QMessageBox.critical(
                self,
                'Save Pose Option',
                f'You must select only one asset.\nFound name spaces {namespaces}',
            )
            return

        pose = Pose(self.__output_path, name, comment, replace_namespace)
        if pose.isExists():
            result = QMessageBox.question(
                self,
                'Save Pose Option',
                'Pose is already exists.\nDo you want to override?',
            )
            if result != QMessageBox.Yes:
                return

        if not pose.write(selection):
            return

        if not self.__viewport.capture(pose.thumbnail()):
            return

        self.finished_save.emit(pose.root_path())
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        '''Close Event[override]'''
        self.__viewport.cleanup()
        super().closeEvent(event)


class SaveAnimationOption(QDialog):
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

        self.setObjectName('SaveAnimationOption' + str(id(self)))
        self.setWindowTitle('Save Animation Options')
        self.resize(512, 256)

        main_layout: QGridLayout = QGridLayout(self)
        main_layout.setObjectName('Layout' + str(id(main_layout)))
        self.setLayout(main_layout)

        viewport_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setObjectName('Layout' + str(id(viewport_layout)))
        main_layout.addLayout(viewport_layout, 0, 0)

        label = QLabel('Thumbnail :', self)
        viewport_layout.addWidget(label)

        self.__viewport = widgets.ViewportCapture(self)
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

        option_layout.addWidget(widgets.HorizontalLine(self))

        self.__is_time_range: QCheckBox = QCheckBox('Time Range', self)
        self.__is_time_range.clicked.connect(self.update_ui_enabled)
        option_layout.addWidget(self.__is_time_range)

        self.__time_range_layout: QHBoxLayout = QHBoxLayout(self)

        self.__start_frame: QSpinBox = QSpinBox(self)
        self.__start_frame.setRange(-999999, 999999)
        self.__start_frame.setValue(1)
        self.__start_frame.setButtonSymbols(QSpinBox.NoButtons)
        self.__time_range_layout.addWidget(self.__start_frame, True)

        self.__time_range_layout.addWidget(QLabel('-', self))

        self.__end_frame: QSpinBox = QSpinBox(self)
        self.__end_frame.setRange(-999999, 999999)
        self.__end_frame.setValue(120)
        self.__end_frame.setButtonSymbols(QSpinBox.NoButtons)
        self.__time_range_layout.addWidget(self.__end_frame, True)

        button: QPushButton = QPushButton('Get', self)
        button.clicked.connect(self.set_time_rage_from_current)
        self.__time_range_layout.addWidget(button)
        option_layout.addLayout(self.__time_range_layout)
        option_layout.addStretch(True)

        button = QPushButton('Save', self)
        button.clicked.connect(self.save)
        main_layout.addWidget(button, 1, 0, 1, 2)
        self.update_ui_enabled()

    def update_ui_enabled(self) -> None:
        '''Update ui enabled'''
        for i in range(self.__time_range_layout.count()):
            widget = self.__time_range_layout.itemAt(i).widget()
            widget.setEnabled(self.__is_time_range.isChecked())

    def set_time_rage_from_current(self) -> None:
        '''Set time range from current.'''
        self.__start_frame.setValue(
            cmds.playbackOptions(query=True, animationStartTime=True)
        )
        self.__end_frame.setValue(
            cmds.playbackOptions(query=True, animationEndTime=True)
        )

    def save(self) -> None:
        '''Save animation data.'''
        name: str = self.__name.text()
        comment: str = self.__comment.toPlainText()
        replace_namespace: str = self.__replace_namespace.text()
        if replace_namespace != '' and replace_namespace[-1] != ':':
            replace_namespace += ':'

        is_time_range: bool = self.__is_time_range.isChecked()
        start_frame: int | None = None
        end_frame: int | None = None
        if is_time_range:
            start_frame = self.__start_frame.value()
            end_frame = self.__end_frame.value()

        if name == '':
            QMessageBox.critical(
                self,
                'Save Animation Option',
                'A name must be entered to save a animation.',
            )
            return

        selection: list[str] = cmds.ls(selection=True)
        if not selection:
            QMessageBox.critical(
                self,
                'Save Animation Option',
                'Select node(s) to save a animation.',
            )
            return

        namespaces: list[str] = utility.extract_namespaces(selection)
        if len(namespaces) >= 2:
            QMessageBox.critical(
                self,
                'Save Pose Option',
                f'You must select only one asset.\nFound name spaces {namespaces}',
            )
            return

        animation = Animation(
            self.__output_path,
            name,
            comment,
            replace_namespace,
        )
        if animation.isExists():
            result = QMessageBox.question(
                self,
                'Save Animation Option',
                'Animation is already exists.\nDo you want to override?',
            )
            if result != QMessageBox.Yes:
                return

        if not animation.write(selection, start_frame, end_frame):
            return

        if not self.__viewport.capture(animation.thumbnail()):
            return

        self.finished_save.emit(animation.root_path())
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        '''Close Event[override]'''
        self.__viewport.cleanup()
        super().closeEvent(event)


class PoseOption(QWidget):
    '''Pose option widget'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize'''
        super().__init__(parent, flag)
        self.__pose: Pose = Pose('', '')
        self.__no_image: QPixmap = widgets.pixmap_from_file_name(NO_IMAGE)

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.addWidget(QLabel('<h2>Pose</h2>'))

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

        inner_layout.addWidget(widgets.HorizontalLine(self))

        option_layout: widgets.QFormLayout = widgets.FormLayout(self)
        option_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.addLayout(option_layout)

        self.__method: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__method.set_labels(('Selection', 'From File'))
        option_layout.addRow(widgets.FormLabel('Method'), self.__method)

        self.__keyframe: QCheckBox = QCheckBox('Keyframe')
        option_layout.addRow('', self.__keyframe)
        inner_layout.addStretch(True)

        button_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.addLayout(button_layout)

        button: QPushButton = QPushButton('Apply', self)
        button.clicked.connect(self.apply)
        button_layout.addWidget(button)

        button: QPushButton = QPushButton('Select', self)
        button.clicked.connect(self.select)
        button_layout.addWidget(button)

    def set_file(self, pose: Pose) -> None:
        '''Set file'''
        self.__pose = pose
        self.__pose.read()

        if self.__pose.thumbnail() != '':
            pixmap: QPixmap = QPixmap(self.__pose.thumbnail())
            if pixmap.width() > pixmap.height():
                pixmap = pixmap.scaledToWidth(ICON_SIZE_RANGE[1])
            else:
                pixmap = pixmap.scaledToHeight(ICON_SIZE_RANGE[1])
            self.__image.setPixmap(pixmap)
        else:
            self.__image.setPixmap(self.__no_image)

        self.__file_name.setText(self.__pose.title())
        self.__owner.setText(self.__pose.owner())
        self.__date.setText(self.__pose.date())
        self.__nodes.setText(f'{self.__pose.node_number()} Object(s)')
        self.__comment.setText(self.__pose.comment())

    def method(self) -> widgets.RadioButtons:
        '''Return method widget.'''
        return self.__method

    def keyframe(self) -> QCheckBox:
        '''Return keyframe widget.'''
        return self.__keyframe

    @widgets.undo
    def apply(self) -> None:
        '''Apply pose data.'''
        self.__pose.apply(self.__method.check_id(), self.__keyframe.isChecked())

    @widgets.undo
    def select(self) -> None:
        try:
            cmds.select(*self.__pose.nodes())
        except ValueError:
            QMessageBox.critical(
                self, 'Import Pose Option', 'Does not exists node.'
            )


class AnimationOption(QWidget):
    '''Anim option widget'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize'''
        super().__init__(parent, flag)
        self.__anim: Animation = Animation('', '')
        self.__no_image: QPixmap = widgets.pixmap_from_file_name(NO_IMAGE)

        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.addWidget(QLabel('<h2>Animation</h2>'))

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

        inner_layout.addWidget(widgets.HorizontalLine(self))

        self.__option_layout: widgets.QFormLayout = widgets.FormLayout(self)
        self.__option_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.addLayout(self.__option_layout)

        self.__method: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__method.set_labels(('Selection', 'From File'))
        self.__option_layout.addRow(widgets.FormLabel('Method'), self.__method)

        self.__remove_anim: QCheckBox = QCheckBox(
            'Remove current animation.', self
        )
        self.__remove_anim.clicked.connect(self.update_ui_enabled)
        self.__option_layout.addRow('', self.__remove_anim)

        self.__override: QCheckBox = QCheckBox('Override animation.', self)
        self.__option_layout.addRow('', self.__override)
        self.__override_id: int = self.__option_layout.row_id()

        self.__is_time_range: QCheckBox = QCheckBox('Time Range', self)
        self.__is_time_range.clicked.connect(self.update_ui_enabled)
        self.__option_layout.addRow('', self.__is_time_range)

        time_range_layout: QHBoxLayout = QHBoxLayout(self)

        self.__start_frame: QSpinBox = QSpinBox(self)
        self.__start_frame.setRange(-999999, 999999)
        self.__start_frame.setValue(1)
        self.__start_frame.setButtonSymbols(QSpinBox.NoButtons)
        time_range_layout.addWidget(self.__start_frame, True)

        time_range_layout.addWidget(QLabel('-', self))

        self.__end_frame: QSpinBox = QSpinBox(self)
        self.__end_frame.setRange(-999999, 999999)
        self.__end_frame.setValue(120)
        self.__end_frame.setButtonSymbols(QSpinBox.NoButtons)
        time_range_layout.addWidget(self.__end_frame, True)

        button: QPushButton = QPushButton('Get', self)
        button.clicked.connect(self.set_time_rage_from_current)
        time_range_layout.addWidget(button)

        self.__option_layout.addRow('Time Range', time_range_layout)
        self.__time_range_id: int = self.__option_layout.row_id()
        inner_layout.addStretch(True)

        button_layout: QHBoxLayout = QHBoxLayout(self)
        main_layout.addLayout(button_layout)

        button: QPushButton = QPushButton('Apply', self)
        button.clicked.connect(self.apply)
        button_layout.addWidget(button)

        button: QPushButton = QPushButton('Select', self)
        button.clicked.connect(self.select)
        button_layout.addWidget(button)

        self.update_ui_enabled()

    def update_ui_enabled(self) -> None:
        '''Update ui enabled.'''
        self.__option_layout.set_row_enabled(
            self.__override_id, not self.__remove_anim.isChecked()
        )
        self.__option_layout.set_row_enabled(
            self.__time_range_id, self.__is_time_range.isChecked()
        )

    def set_time_rage_from_current(self) -> None:
        '''Set time range from current.'''
        self.__start_frame.setValue(
            cmds.playbackOptions(query=True, animationStartTime=True)
        )
        self.__end_frame.setValue(
            cmds.playbackOptions(query=True, animationEndTime=True)
        )

    def set_file(self, anim: Animation) -> None:
        '''Set file'''
        self.__anim = anim
        self.__anim.read()

        if self.__anim.thumbnail() != '':
            pixmap: QPixmap = QPixmap(self.__anim.thumbnail())
            if pixmap.width() > pixmap.height():
                pixmap = pixmap.scaledToWidth(ICON_SIZE_RANGE[1])
            else:
                pixmap = pixmap.scaledToHeight(ICON_SIZE_RANGE[1])
            self.__image.setPixmap(pixmap)
        else:
            self.__image.setPixmap(self.__no_image)

        self.__file_name.setText(self.__anim.title())
        self.__owner.setText(self.__anim.owner())
        self.__date.setText(self.__anim.date())
        self.__nodes.setText(f'{self.__anim.node_number()} Object(s)')
        self.__comment.setText(self.__anim.comment())

    def method(self) -> widgets.RadioButtons:
        '''Return method widget.'''
        return self.__method

    def remove_animation(self) -> QCheckBox:
        '''Return remove animation widget'''
        return self.__remove_anim

    def override_animation(self) -> QCheckBox:
        '''Return override animation widget'''
        return self.__override

    def is_time_range(self) -> QCheckBox:
        '''Return is time range widget'''
        return self.__is_time_range

    def start_frame(self) -> QSpinBox:
        '''Return start frame widget'''
        return self.__start_frame

    def end_frame(self) -> QSpinBox:
        '''Return end frame widget'''
        return self.__end_frame

    @widgets.undo
    def apply(self) -> None:
        '''Apply anim data.'''
        start_frame: int | None = None
        end_frame: int | None = None
        if self.__is_time_range.isChecked():
            start_frame = self.__start_frame.value()
            end_frame = self.__end_frame.value()

        self.__anim.apply(
            self.__method.check_id(),
            self.__remove_anim.isChecked(),
            self.__override.isChecked(),
            start_frame,
            end_frame,
        )

    @widgets.undo
    def select(self) -> None:
        '''Select node from save data.'''
        try:
            cmds.select(*self.__anim.nodes())
        except ValueError:
            QMessageBox.critical(
                self, 'Import Anim Option', 'Does not exists node.'
            )


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
            'New Pose',
            'a_add_pose.png',
            self.show_new_pose_option,
        )
        self.__file_browser.add_file_view_button(
            2,
            'New Animation',
            'a_add_motion.png',
            self.show_new_animation_option,
        )
        layout.addWidget(self.__file_browser)

        # Option Widget
        self.__stack_option: QStackedWidget = QStackedWidget(self)
        self.__file_browser.add_option_widget(self.__stack_option)

        self.__pose_option: PoseOption = PoseOption(self)
        self.__anim_option: AnimationOption = AnimationOption(self)
        self.__stack_option.addWidget(QWidget(self))
        self.__stack_option.addWidget(self.__pose_option)
        self.__stack_option.addWidget(self.__anim_option)

        # Menu
        # menu_bar = self.menu_bar()
        # view_menu = menu_bar.addMenu('View')
        # menu_bar.insertMenu(self.help_menu().menuAction(), view_menu)

        # action = view_menu.addAction('Update')
        # action.triggered.connect(self.update_view)

    def item_select_callback(self, file_item: widgets.FileBrowserItem) -> None:
        '''Item selected callback.'''
        extension = file_item.extension()
        if extension == 'pose':
            self.__stack_option.setCurrentIndex(1)
            pose = Pose.fromPath(file_item.data_path())
            pose.set_thumbnail(file_item.icon_path())
            self.__pose_option.set_file(pose)

        elif extension == 'anim':
            self.__stack_option.setCurrentIndex(2)
            anim = Animation.fromPath(file_item.data_path())
            anim.set_thumbnail(file_item.icon_path())
            self.__anim_option.set_file(anim)

        else:
            self.__stack_option.setCurrentIndex(0)

    def show_new_pose_option(self, path: str) -> None:
        '''Show new pose option'''
        option = SavePoseOption(output_path=path)
        option.finished_save.connect(self.save_item_callback)
        option.show()

    def show_new_animation_option(self, path: str) -> None:
        '''Show new animation option'''
        option = SaveAnimationOption(output_path=path)
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

        # Pose
        self.__pose_option.method().set_check_id(settings.pose_method.value())
        self.__pose_option.keyframe().setChecked(settings.pose_keyframe.value())

        # Anim
        self.__anim_option.method().set_check_id(settings.anim_method.value())
        self.__anim_option.remove_animation().setChecked(
            settings.remove_animation.value()
        )
        self.__anim_option.override_animation().setChecked(
            settings.override_animation.value()
        )
        self.__anim_option.is_time_range().setChecked(
            settings.is_time_range.value()
        )
        self.__anim_option.start_frame().setValue(settings.start_frame.value())
        self.__anim_option.end_frame().setValue(settings.end_frame.value())

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

        # Pose
        settings.pose_method.set_value(self.__pose_option.method().check_id())
        settings.pose_keyframe.set_value(
            self.__pose_option.keyframe().isChecked()
        )

        # Anim
        settings.anim_method.set_value(self.__anim_option.method().check_id())
        settings.remove_animation.set_value(
            self.__anim_option.remove_animation().isChecked()
        )
        settings.override_animation.set_value(
            self.__anim_option.override_animation().isChecked()
        )
        settings.is_time_range.set_value(
            self.__anim_option.is_time_range().isChecked()
        )
        settings.start_frame.set_value(self.__anim_option.start_frame().value())
        settings.end_frame.set_value(self.__anim_option.end_frame().value())
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
    # Load atom.
    atom = cmds.pluginInfo('atomImportExport.mll', query=True, loaded=True)
    if not atom:
        cmds.loadPlugin('atomImportExport.mll')

    if not os.path.exists(ROOT_DIR):
        try:
            os.makedirs(ROOT_DIR)
        except IOError as e:
            _logger.error('Failed to make folder. %s', e)

    window: MainWindow = MainWindow()
    window.show()
