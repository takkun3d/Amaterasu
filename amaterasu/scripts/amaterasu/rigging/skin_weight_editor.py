# ==============================================================================
#
# Skin Weight Editor
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING, Any
import os
import json

try:
    from PySide2.QtCore import Qt, QSize
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QCheckBox,
        QDoubleSpinBox,
        QButtonGroup,
        QPushButton,
        QMessageBox,
        QFileDialog,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt, QSize
        from PySide6.QtWidgets import (
            QWidget,
            QVBoxLayout,
            QHBoxLayout,
            QCheckBox,
            QDoubleSpinBox,
            QButtonGroup,
            QPushButton,
            QMessageBox,
            QFileDialog,
        )
from maya import cmds, mel
from ..lib import logger, parser, utility, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Skin Weight Editor'
__version__: str = '1.4'
__doc__ = 'This tool helps to edit skin weights.'
__copyright__ = (
    'Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.'
)
_logger: logger.Logger = logger.get_logger(__product__)
ICON_SIZE: QSize = QSize(24, 24)


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Settings(parser.ToolSettings):
    '''Settings for tool.'''

    window_geo: parser.Variant[str] = parser.Variant('')
    transfer_method: parser.Variant[int] = parser.Variant(0)
    threshold: parser.Variant[float] = parser.Variant(0.1)
    across: parser.Variant[int] = parser.Variant(1)
    direction: parser.Variant[bool] = parser.Variant(True)


class TransferSkinWeight(QWidget):
    '''Transfer Skin Weight Widget'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__layout = widgets.FormLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(self.__layout)

        self.__method: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__method.set_labels(('Default', 'Proximity'))
        button_group: QButtonGroup = self.__method.button_group()
        button_group.buttonClicked.connect(self.update_ui)
        self.__layout.addRow(widgets.FormLabel('Method'), self.__method)

        self.__threshold: QDoubleSpinBox = QDoubleSpinBox(self)
        self.__threshold.setRange(0, 1000)
        self.__threshold.setDecimals(3)
        self.__threshold.setSingleStep(0.05)
        self.__layout.addRow(widgets.FormLabel('Threshold'), self.__threshold)
        self.__threshold_idx: int = self.__layout.row_id()

        button = QPushButton('Transfer Skin Weight', self)
        button.clicked.connect(self.apply)
        main_layout.addWidget(button)

    def load_settings(self) -> None:
        '''Load Settings.'''
        settings: Settings = Settings.instance(__name__, True)
        self.__method.set_check_id(settings.transfer_method.value())
        self.__threshold.setValue(settings.threshold.value())
        self.update_ui()

    def save_settings(self) -> None:
        '''Save Settings.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.transfer_method.set_value(self.__method.check_id())
        settings.threshold.set_value(self.__threshold.value())

    def reset_settings(self) -> None:
        '''Reset Settings.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()

    def update_ui(self) -> None:
        '''Update UI'''
        self.__layout.set_row_enabled(
            self.__threshold_idx, self.__method.check_id() == 1
        )

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()

        selection: list[str] = cmds.ls(selection=True, exactType='transform')
        if not selection or len(selection) <= 1:
            QMessageBox.critical(
                self, 'Error', 'Must select a source and a destination skin.'
            )
            return

        if self.__method.check_id() == 0:
            transfer_skin_weight(selection[0], selection[1:])

        else:
            masked_transfer_skin_weight(
                selection[:-1], selection[-1], self.__threshold.value()
            )


class MirrorSkinWeight(QWidget):
    '''Mirror Skin Weight Widget'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        layout = widgets.FormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(layout)

        self.__across: widgets.RadioButtons = widgets.RadioButtons(self)
        self.__across.set_labels(('XY', 'YZ', 'XZ'))
        layout.addRow(widgets.FormLabel('Across'), self.__across)

        self.__direction = QCheckBox('Positive to negative', self)
        layout.addRow('', self.__direction)

        button = QPushButton('Mirror Skin Weight', self)
        button.clicked.connect(self.apply)
        main_layout.addWidget(button)

    def load_settings(self) -> None:
        '''Load Settings.'''
        settings: Settings = Settings.instance(__name__, True)
        self.__across.set_check_id(settings.across.value())
        self.__direction.setChecked(settings.direction.value())

    def save_settings(self) -> None:
        '''Save Settings.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.across.set_value(self.__across.check_id())
        settings.direction.set_value(self.__direction.isChecked())

    def reset_settings(self) -> None:
        '''Reset Settings.'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.load_settings()

    @widgets.undo
    def apply(self) -> None:
        '''Apply'''
        self.save_settings()

        seleciton: list[str] = cmds.ls(selection=True, exactType='transform')
        if not seleciton:
            QMessageBox.critical(
                self, 'Error', 'Must select a source and a destination skin.'
            )
            return

        if len(seleciton) != 1:
            src: str = seleciton[0]
            dst: str = seleciton[1]
        else:
            src = seleciton[0]
            dst = seleciton[0]

        settings: Settings = Settings.instance(__name__, True)
        mirror_skin_weight(
            src, dst, settings.across.value(), settings.direction.value()
        )


class Utilities(QWidget):
    '''Utilities Widget'''

    def __init__(
        self,
        parent: QWidget | None = None,
        flag: Qt.WindowFlags = Qt.WindowFlags(),
    ) -> None:
        '''Initialize widget.'''
        super().__init__(parent, flag)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1 --------------------------------------------------------------------
        icon_layout = QHBoxLayout(self)
        layout.addLayout(icon_layout)

        button = widgets.IconButton(self)
        button.set_icon('a_paint.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Paint Skin Weights Tool')
        button.clicked.connect(self.paint_skin_weights_tool)
        icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_lock_weight.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Lock Influences')
        button.clicked.connect(self.lock_influences)
        icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_unlock_weight.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Unlock Influences')
        button.clicked.connect(self.unlock_influences)
        icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_add_influence.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Add Influence / Right-click to open options.')
        button.clicked.connect(self.add_influence)
        button.right_clicked.connect(self.add_influence_option)
        icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_remove_influence.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Remove Influence')
        button.clicked.connect(self.remove_influence)
        icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_hammer.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Hammer Skin Weights')
        button.clicked.connect(self.hammer_skin_weights)
        icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_prune_small_weights.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Prune Small Weights / Right-click to open options.')
        button.clicked.connect(self.prune_small_weights)
        button.right_clicked.connect(self.prune_small_weights_options)
        icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_remove_unused_influences.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Remove Unused Influences')
        button.clicked.connect(self.remove_unused_influences)
        icon_layout.addWidget(button)
        icon_layout.addStretch(True)

        # 2 --------------------------------------------------------------------
        icon_layout = QHBoxLayout(self)
        layout.addLayout(icon_layout)

        # button = widgets.IconButton(self)
        # button.set_icon('a_transfer.png')
        # button.setIconSize(ICON_SIZE)
        # button.setToolTip('Transfer Skin Weights')
        # button.clicked.connect(self.transfer_skin_weights)
        # icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_copy.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Copy Vertex Weights')
        button.clicked.connect(self.copy_vertex_weights)
        icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_paste.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Paste Vertex Weights')
        button.clicked.connect(self.paste_vertex_weights)
        icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_import.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Import Skin Weights')
        button.clicked.connect(self.import_skin_weights)
        icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_batch_import.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Batch Import Skin Weights')
        button.clicked.connect(self.batch_import_skin_weights)
        icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_export.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Export Skin Weights')
        button.clicked.connect(self.export_skin_weights)
        icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_batch_export.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Batch Export Skin Weights')
        button.clicked.connect(self.batch_export_skin_weights)
        icon_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon('a_component_editor.png')
        button.setIconSize(ICON_SIZE)
        button.setToolTip('Component Editor')
        button.clicked.connect(self.component_editor)
        icon_layout.addWidget(button)
        icon_layout.addStretch(True)

    @widgets.undo
    def paint_skin_weights_tool(self) -> None:
        '''Paint Skin Weights Tool'''
        mel.eval('ArtPaintSkinWeightsToolOptions;')

    @widgets.undo
    def lock_influences(self) -> None:
        '''Lock influences'''
        selection: list[str] = cmds.ls(selection=True)
        joints: list[str] = cmds.ls(type='joint')
        for joint in joints:
            cmds.select(joint)
            cmds.setAttr(f'{joint}.lockInfluenceWeights', True)

        if selection:
            cmds.select(*selection)

    @widgets.undo
    def unlock_influences(self) -> None:
        '''Unlock influences'''
        selection: list[str] = cmds.ls(selection=True)
        joints: list[str] = cmds.ls(type='joint')
        for joint in joints:
            cmds.select(joint)
            cmds.setAttr(f'{joint}.lockInfluenceWeights', False)

        if selection:
            cmds.select(*selection)

    @widgets.undo
    def add_influence(self) -> None:
        '''Add influence'''
        # skinCluster -e -dr 4 -ug -ps 0 -ns 10 -lw true -wt 0 -ai joint3 skinCluster1;
        mel.eval('AddInfluence;')

    @widgets.undo
    def add_influence_option(self) -> None:
        '''Add influence Option'''
        mel.eval('AddInfluenceOptions;')

    @widgets.undo
    def remove_influence(self) -> None:
        '''Remove influence'''
        # skinCluster -e  -ri joint3 skinCluster1;
        mel.eval('RemoveInfluence;')

    @widgets.undo
    def hammer_skin_weights(self) -> None:
        '''Hammer Skin Weights'''
        mel.eval('WeightHammer;')

    @widgets.undo
    def prune_small_weights(self) -> None:
        '''Prune Small Weights Options'''
        mel.eval('PruneSmallWeights;')

    @widgets.undo
    def prune_small_weights_options(self) -> None:
        '''PruneSmallWeights'''
        mel.eval('PruneSmallWeightsOptions;')

    @widgets.undo
    def remove_unused_influences(self) -> None:
        '''Remove Unused Influences'''
        selection: list[str] = cmds.ls(selection=True, exactType='transform')
        if not selection:
            QMessageBox.critical(self, 'Error', 'No skins are selected.')
            return

        button = QMessageBox.warning(
            self,
            __product__,
            'You can not undo this action.',
            QMessageBox.Ok,
            QMessageBox.Cancel,
        )
        if button != QMessageBox.Ok:
            return

        remove_unused_influences(selection)

    # @widgets.undo
    # def transfer_skin_weights(self) -> None:
    #     '''Apply'''
    #     selection: list[str] = cmds.ls(selection=True, exactType='transform')
    #     if not selection or len(selection) <= 1:
    #         QMessageBox.critical(
    #             self, 'Error', 'Must select a source and a destination skin.'
    #         )
    #         return

    #     transfer_skin_weight(selection[0], selection[1:])

    @widgets.undo
    def copy_vertex_weights(self) -> None:
        '''Copy vertex weights'''
        mel.eval('artAttrSkinWeightCopy;')

    @widgets.undo
    def paste_vertex_weights(self) -> None:
        '''Paste vertex weights'''
        mel.eval('artAttrSkinWeightPaste;')

    @widgets.undo
    def import_skin_weights(self) -> None:
        '''Apply'''
        selection: list[str] = cmds.ls(selection=True, type='transform')
        if not selection:
            QMessageBox.critical(
                self, 'Error', 'Select polygon to import skin weight.'
            )
            return

        filename = QFileDialog.getOpenFileName(
            self, 'Import', import_export_dir(), 'swd (*.swd)'
        )
        if filename[0] == '':
            return  # Canceled

        result = import_file(selection[0], filename[0])
        if result:
            _logger.info('Done.')

    @widgets.undo
    def batch_import_skin_weights(self) -> None:
        '''Apply'''
        selection: list[str] = cmds.ls(selection=True, type='transform')
        if not selection:
            QMessageBox.critical(
                self, 'Error', 'Select polygon to import skin weight.'
            )
            return

        dirname = QFileDialog.getExistingDirectory(
            self, 'Import', import_export_dir()
        )
        if dirname == '':
            return  # Canceled

        for node in selection:
            filename = os.path.join(dirname, f'{node}.swd')

            if not os.path.exists(filename):
                _logger.warning('Could not find weight data : %s', node)
                continue

            import_file(node, filename)

        _logger.info('Done')

    @widgets.undo
    def export_skin_weights(self) -> None:
        '''Apply'''
        selection: list[str] = cmds.ls(selection=True, type='transform')
        if not selection:
            QMessageBox.critical(
                self, 'Error', 'Select polygon to export skin weight.'
            )
            return

        filename = QFileDialog.getSaveFileName(
            self, 'Export', import_export_dir(), 'swd (*.swd)'
        )
        if filename[0] == '':
            return  # Canceled

        result = export_file(selection[0], filename[0])
        if result:
            _logger.info('Done.')

    @widgets.undo
    def batch_export_skin_weights(self) -> None:
        '''Multiple Apply'''
        selection: list[str] = cmds.ls(selection=True, type='transform')
        if not selection:
            QMessageBox.critical(
                self, 'Error', 'Select polygons to export skin weight.'
            )
            return

        dirname = QFileDialog.getExistingDirectory(
            self, 'Export', import_export_dir()
        )
        if dirname == '':
            return  # Canceled

        for node in selection:
            filename = os.path.join(dirname, f'{node}.swd')
            export_file(node, filename)

        _logger.info('Done')

    @widgets.undo
    def component_editor(self) -> None:
        '''Show Component Editor'''
        mel.eval('ComponentEditor;')


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

        layout = QVBoxLayout(self.option_widget())
        layout.setContentsMargins(0, 0, 0, 0)

        self.__utilities = Utilities(self)
        layout.addWidget(self.__utilities)

        layout.addWidget(widgets.HorizontalLine())

        self.__transfer_weight: TransferSkinWeight = TransferSkinWeight(self)
        layout.addWidget(self.__transfer_weight)

        layout.addWidget(widgets.HorizontalLine())

        self.__mirror_skin_weight = MirrorSkinWeight(self)
        layout.addWidget(self.__mirror_skin_weight)
        layout.addStretch()

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__transfer_weight.load_settings()
        self.__mirror_skin_weight.load_settings()

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        self.__transfer_weight.save_settings()
        self.__mirror_skin_weight.save_settings()
        settings.write()

    # override
    def reset_settings(self) -> None:
        '''Reset ui settings.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.reset()
        self.__transfer_weight.reset_settings()
        self.__mirror_skin_weight.reset_settings()
        self.load_settings()

    # override
    def about(self) -> None:
        '''Show a about dialog.[override]'''
        widgets.AboutDialog.info(
            self, __product__, __version__, __copyright__, __doc__
        )


# ==============================================================================
#
# Functions
#
# ==============================================================================
def import_export_dir() -> str:
    '''Return import and export directry.'''
    project_dir: str = cmds.workspace(query=True, rootDirectory=True)
    directory: str = os.path.abspath(os.path.join(project_dir, 'data'))
    return directory


def transfer_skin_weight(src: str, dsts: list[str]) -> bool:
    '''Transfer skin weight'''
    shapes: list[str] = cmds.listRelatives(src, shapes=True, path=True) or []
    if not shapes:
        return False

    src_skin_cluster: str = utility.find_related_skin_cluster(shapes[0])
    if not src_skin_cluster:
        _logger.error('Must select a destination surface with a skin.')
        return False

    skinning_method: int = cmds.getAttr(f'{src_skin_cluster}.skm')
    dropoff_rate: float = cmds.getAttr(f'{src_skin_cluster}.dr')
    maintain_max_influences: int = cmds.getAttr(f'{src_skin_cluster}.mmi')
    max_influences: int = cmds.getAttr(f'{src_skin_cluster}.mi')
    normalize_weights: bool = cmds.getAttr(f'{src_skin_cluster}.nw')
    src_influences: list[str] = cmds.skinCluster(
        src_skin_cluster, query=True, influence=True
    )

    for dst in dsts:
        shapes = cmds.listRelatives(dst, shapes=True, path=True) or []
        if not shapes:
            continue

        dst_skin_cluster: str = utility.find_related_skin_cluster(shapes[0])
        if not dst_skin_cluster:
            temp: list[str] = cmds.skinCluster(
                dst,
                src_influences,
                obeyMaxInfluences=maintain_max_influences,
                maximumInfluences=max_influences,
                dropoffRate=dropoff_rate,
                skinMethod=skinning_method,
                normalizeWeights=normalize_weights,
                toSelectedBones=True,
            )
            dst_skin_cluster = temp[0]

        dst_influences: list[str] = cmds.skinCluster(
            dst_skin_cluster, query=True, influence=True
        )
        src_influences = cmds.ls(src_influences, long=True)
        dst_influences = cmds.ls(dst_influences, long=True)
        diff_influences: list[str] = list(
            set(src_influences) - set(dst_influences)
        )
        if diff_influences:
            cmds.skinCluster(
                dst_skin_cluster,
                edit=True,
                dropoffRate=4.0,
                useGeometry=True,
                polySmoothness=0,
                nurbsSamples=10,
                lockWeights=True,
                weight=0.0,
                addInfluence=diff_influences,
            )

        cmds.copySkinWeights(
            sourceSkin=src_skin_cluster,
            destinationSkin=dst_skin_cluster,
            surfaceAssociation='closestPoint',
            influenceAssociation=['name', 'closestJoint', 'oneToOne'],
            normalize=True,
            noMirror=True,
        )

        _logger.info('Transfer skin weight : %s > %s', src, dst)

    return True


def masked_transfer_skin_weight(
    srcs: list[str], dst: str, threshold: float
) -> bool:
    '''Masked Transfer skin weight'''
    selection: list[str] = cmds.ls(selection=True)
    result: list[str] = []

    shapes: list[str] = cmds.listRelatives(dst, shapes=True, path=True) or []
    if not shapes:
        return False

    dst_skin_cluster: str = utility.find_related_skin_cluster(shapes[0])

    cmds.select(clear=True)
    for src in srcs:
        shapes = cmds.listRelatives(src, shapes=True, path=True) or []
        if not shapes:
            continue

        src_skin_cluster: str = utility.find_related_skin_cluster(shapes[0])
        skinning_method: int = cmds.getAttr(f'{src_skin_cluster}.skm')
        dropoff_rate: float = cmds.getAttr(f'{src_skin_cluster}.dr')
        maintain_max_influences: int = cmds.getAttr(f'{src_skin_cluster}.mmi')
        max_influences: int = cmds.getAttr(f'{src_skin_cluster}.mi')
        normalize_weights: bool = cmds.getAttr(f'{src_skin_cluster}.nw')
        src_influences: list[str] = cmds.skinCluster(
            src_skin_cluster, query=True, influence=True
        )
        if not dst_skin_cluster:
            temp: list[str] = cmds.skinCluster(
                dst,
                src_influences,
                obeyMaxInfluences=maintain_max_influences,
                maximumInfluences=max_influences,
                dropoffRate=dropoff_rate,
                skinMethod=skinning_method,
                normalizeWeights=normalize_weights,
                toSelectedBones=True,
            )
            dst_skin_cluster = temp[0]

        dst_influences: list[str] = cmds.skinCluster(
            dst_skin_cluster, query=True, influence=True
        )
        src_influences = cmds.ls(src_influences, long=True)
        dst_influences = cmds.ls(dst_influences, long=True)
        diff_influences: list[str] = list(
            set(src_influences) - set(dst_influences)
        )
        if diff_influences:
            cmds.skinCluster(
                dst_skin_cluster,
                edit=True,
                dropoffRate=4.0,
                useGeometry=True,
                polySmoothness=0,
                nurbsSamples=10,
                lockWeights=True,
                weight=0.0,
                addInfluence=diff_influences,
            )

        masked_vertices: list[str] = utility.closest_vertex_ids(
            src, dst, threshold
        )
        if masked_vertices:
            cmds.select(*masked_vertices, replace=True)
            result.extend(masked_vertices)

        cmds.copySkinWeights(
            sourceSkin=src_skin_cluster,
            destinationSkin=dst_skin_cluster,
            surfaceAssociation='closestPoint',
            influenceAssociation=['name', 'closestJoint', 'oneToOne'],
            normalize=True,
            noMirror=True,
        )

        _logger.info('Masked transfer skin weight : %s > %s', src, dst)

    if selection:
        cmds.select(*selection)

    if result:
        cmds.select(*result)

    return True


def mirror_skin_weight(
    src: str, dst: str, across: int, direction: bool
) -> bool:
    '''Mirror Skin Weight'''
    shapes: list[str] = cmds.listRelatives(src, shapes=True, path=True) or []
    if not shapes:
        return False

    src_skin_cluster: str = utility.find_related_skin_cluster(shapes[0])
    if not src_skin_cluster:
        _logger.error('Must select a destination surface with a skin.')
        return False

    shapes = cmds.listRelatives(dst, shapes=True, path=True) or []
    if not shapes:
        return False

    dst_skin_cluster: str = utility.find_related_skin_cluster(shapes[0])
    if not dst_skin_cluster:
        _logger.error('Must select a destination surface with a skin.')
        return False

    cmds.copySkinWeights(
        sourceSkin=src_skin_cluster,
        destinationSkin=dst_skin_cluster,
        mirrorMode=('XY', 'YZ', 'XZ')[across],
        mirrorInverse=(not direction),
        influenceAssociation='oneToOne',
        normalize=True,
        noMirror=False,
    )

    _logger.info('Mirror skin weight %s > %s', src, dst)
    return True


def remove_unused_influences(nodes: list[str]) -> None:
    '''Remove Unused Influences'''
    for node in nodes:
        skin_cluster: str = utility.find_related_skin_cluster(node)
        if not skin_cluster:
            continue

        remove_infls: list[str] = utility.unused_influences(skin_cluster)
        if not remove_infls:
            continue

        cmds.skinCluster(skin_cluster, edit=True, removeInfluence=remove_infls)
        cmds.flushUndo()
        _logger.info('Remove unused influences : %s / %s', skin_cluster, node)


def import_file(node: str, filename: str) -> bool:
    '''Import skin weight data.'''
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

    except IOError:
        _logger.error('Failed to read file : %s', filename)
        return False

    skin_cluster_data: dict[str, Any] = data['skinCluster']
    joints: list[str] = data['joints']
    weight_data: list[float] = data['weight']

    shapes: list[str] = cmds.listRelatives(node, shapes=True, path=True) or []
    if not shapes:
        _logger.error('Failed to get shape node.')
        return False

    points: list[str] = []
    object_type: str = cmds.objectType(shapes[0])
    if object_type == 'mesh':
        points = cmds.ls(f'{shapes[0]}.vtx[*]', flatten=True)

    elif object_type == 'nurbsSurface':
        points = cmds.ls(f'{shapes[0]}.cv[*][*]', flatten=True)

    elif object_type == 'nurbsCurve':
        points = cmds.ls(f'{shapes[0]}.cv[*]', flatten=True)

    elif object_type == 'lattice':
        points = cmds.ls(f'{shapes[0]}.pt[*][*][*]', flatten=True)

    if not points:
        _logger.error('This node is not supported : %s', node)
        return False

    for joint in joints:
        if not cmds.objExists(joint):
            _logger.error('Joint does not exists : %s', joint)
            return False

    skin_cluster: str = utility.find_related_skin_cluster(shapes[0])
    if not skin_cluster:
        temp: list[str] = cmds.skinCluster(
            node,
            joints,
            obeyMaxInfluences=skin_cluster_data['maintainMaxInfluences'],
            maximumInfluences=skin_cluster_data['maxInfluences'],
            dropoffRate=skin_cluster_data['dropoffRate'],
            skinMethod=skin_cluster_data['skinningMethod'],
            normalizeWeights=skin_cluster_data['normalizeWeights'],
            toSelectedBones=True,
        )
        skin_cluster = temp[0]

    cmds.setAttr(f'{skin_cluster}.nw', 0)
    cmds.setAttr(f'{skin_cluster}.envelope', 0)
    for i, point in enumerate(points):
        cmds.skinPercent(
            skin_cluster,
            point,
            relative=False,
            transformValue=zip(joints, weight_data[i]),
        )

    cmds.setAttr(f'{skin_cluster}.envelope', 1)
    cmds.setAttr(f'{skin_cluster}.nw', skin_cluster_data['normalizeWeights'])
    return True


def export_file(node: str, filename: str) -> bool:
    '''Export skin weight data.'''
    shapes: list[str] = cmds.listRelatives(node, shapes=True, path=True) or []
    if not shapes:
        _logger.error('Failed to get shape node : %s', node)
        return False

    skin_cluster: str = utility.find_related_skin_cluster(shapes[0])
    if not skin_cluster:
        _logger.error('Could not find skin cluster : %s', node)
        return False

    skin_cluster_data: dict[str, Any] = {}
    skin_cluster_data['skinningMethod'] = cmds.getAttr(f'{skin_cluster}.skm')
    skin_cluster_data['dropoffRate'] = cmds.getAttr(f'{skin_cluster}.dr')
    skin_cluster_data['maintainMaxInfluences'] = cmds.getAttr(
        f'{skin_cluster}.mmi'
    )
    skin_cluster_data['maxInfluences'] = cmds.getAttr(f'{skin_cluster}.mi')
    skin_cluster_data['bindMethod'] = cmds.getAttr(f'{skin_cluster}.bm')
    skin_cluster_data['normalizeWeights'] = cmds.getAttr(f'{skin_cluster}.nw')

    joints: list[str] = cmds.skinCluster(
        skin_cluster, query=True, influence=True
    )
    points: list[str] = []
    object_type: str = cmds.objectType(shapes[0])
    if object_type == 'mesh':
        points = cmds.ls(f'{shapes[0]}.vtx[*]', flatten=True)

    elif object_type == 'nurbsSurface':
        points = cmds.ls(f'{shapes[0]}.cv[*][*]', flatten=True)

    elif object_type == 'nurbsCurve':
        points = cmds.ls(f'{shapes[0]}.cv[*]', flatten=True)

    elif object_type == 'lattice':
        points = cmds.ls(f'{shapes[0]}.pt[*][*][*]', flatten=True)

    if not points:
        _logger.error('This node can not export file : %s', node)
        return False

    weight_data: list[float] = []
    position_data: list[float] = []
    for point in points:
        weight_data.append(
            cmds.skinPercent(skin_cluster, point, query=True, value=True)
        )
        position_data.append(cmds.pointPosition(point, world=True))

    write_data: dict[str, Any] = {}
    write_data['skinCluster'] = skin_cluster_data
    write_data['joints'] = joints
    write_data['weight'] = weight_data
    write_data['position'] = position_data

    try:
        with open(filename, 'w', encoding='utf-8') as fw:
            json.dump(write_data, fw, indent=4)

    except IOError:
        _logger.error('Failed to write file : %s', filename)
        return False

    return True


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
