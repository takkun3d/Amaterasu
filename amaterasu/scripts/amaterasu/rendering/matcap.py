# ==============================================================================
#
# Matcap
#
# ==============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import logging

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QWidget,
        QGridLayout,
        QLineEdit,
        QCheckBox,
        QLabel,
    )

except ImportError:
    if not TYPE_CHECKING:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QWidget,
            QGridLayout,
            QLineEdit,
            QCheckBox,
            QLabel,
        )
from maya import cmds
from ..lib import parser, widgets


# ==============================================================================
#
# Variables
#
# ==============================================================================
__product__: str = 'Matcap'
__version__: str = '1.10'
__doc__ = 'Matcap for Maya.'
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
    material_name: parser.Variant[str] = parser.Variant('matcap')
    blend_normal: parser.Variant[int] = parser.Variant(0)
    assign_material: parser.Variant[bool] = parser.Variant(True)


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

        self.__name = QLineEdit(self)
        main_layout.addRow(widgets.FormLabel('Material Name'), self.__name)

        self.__blend_normal = widgets.RadioButtons(self)
        self.__blend_normal.set_labels(['Reoriented', 'Simple'])
        main_layout.addRow(
            widgets.FormLabel('Blend Normal'), self.__blend_normal
        )

        main_layout.addRow(widgets.HorizontalLine(self))

        file_layout = QGridLayout(self)
        file_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addRow('', file_layout)

        self.__matcap_file = widgets.DropImage(self)
        file_layout.addWidget(QLabel('Matcap Map'), 0, 0)
        file_layout.addWidget(self.__matcap_file, 1, 0)

        self.__normal_file = widgets.DropImage(self)
        file_layout.addWidget(QLabel('Normal Map'), 0, 1)
        file_layout.addWidget(self.__normal_file, 1, 1)

        main_layout.addRow(widgets.HorizontalLine(self))

        self.__assign_material = QCheckBox('Assign Material', self)
        main_layout.addRow('', self.__assign_material)

    # override
    def load_settings(self) -> None:
        '''Load ui settings from file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(widgets.to_qt(settings.window_geo.value()))
        self.__name.setText(settings.material_name.value())
        self.__blend_normal.set_check_id(settings.blend_normal.value())
        self.__assign_material.setChecked(settings.assign_material.value())

    # override
    def save_settings(self) -> None:
        '''Save ui settings to file.[override]'''
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(widgets.to_ascii(self.saveGeometry()))
        settings.material_name.set_value(self.__name.text())
        settings.blend_normal.set_value(self.__blend_normal.check_id())
        settings.assign_material.set_value(self.__assign_material.isChecked())
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

        settings: Settings = Settings.instance(__name__, True)
        apply(
            settings.material_name.value(),
            self.__matcap_file.file_path(),
            self.__normal_file.file_path(),
            settings.blend_normal.value(),
            settings.assign_material.value(),
        )


# ==============================================================================
#
# Functions
#
# ==============================================================================
def create_file(base_name: str = '') -> tuple[str, str]:
    '''Create file node.'''
    p2d: str = cmds.shadingNode(
        'place2dTexture', name=f'{base_name}_p2d', asUtility=True
    )
    file_: str = cmds.shadingNode(
        'file', name=f'{base_name}_tex', asTexture=True, isColorManaged=True
    )
    for plug in (
        'coverage',
        'translateFrame',
        'rotateFrame',
        'mirrorU',
        'mirrorV',
        'stagger',
        'wrapU',
        'wrapV',
        'repeatUV',
        'offset',
        'rotateUV',
        'noiseUV',
        'vertexUvOne',
        'vertexUvTwo',
        'vertexUvThree',
        'vertexCameraOne',
    ):
        cmds.connectAttr(f'{p2d}.{plug}', f'{file_}.{plug}')

    cmds.connectAttr(f'{p2d}.outUV', f'{file_}.uv')
    cmds.connectAttr(f'{p2d}.outUvFilterSize', f'{file_}.uvFilterSize')
    return (p2d, file_)


def create_simple_blend_normal(sampler_info: str) -> str:
    '''Create blend normal network.'''
    vectorB_mult: str = 'matcapVectorB_mul'
    if not cmds.objExists(vectorB_mult):
        vectorB_mult = cmds.shadingNode(
            'multiplyDivide', name=vectorB_mult, asUtility=True
        )
        cmds.setAttr(f'{vectorB_mult}.input2', 1.0, 1.0, 1.25, type='double3')
        cmds.connectAttr(
            f'{sampler_info}.rayDirection', f'{vectorB_mult}.input1'
        )

    blend_x: str = 'matcapBlendX_add'
    if not cmds.objExists(blend_x):
        blend_x = cmds.shadingNode(
            'plusMinusAverage', name=blend_x, asUtility=True
        )
        cmds.connectAttr(
            f'{sampler_info}.normalCameraX', f'{blend_x}.input1D[0]'
        )
        cmds.connectAttr(f'{vectorB_mult}.outputX', f'{blend_x}.input1D[1]')

    blend_y: str = 'matpcapBlendY_add'
    if not cmds.objExists(blend_y):
        blend_y = cmds.shadingNode(
            'plusMinusAverage', name=blend_y, asUtility=True
        )
        cmds.connectAttr(
            f'{sampler_info}.normalCameraY', f'{blend_y}.input1D[0]'
        )
        cmds.connectAttr(f'{vectorB_mult}.outputY', f'{blend_y}.input1D[1]')

    blend_z: str = 'matpcapBlendZ_mult'
    if not cmds.objExists(blend_z):
        blend_z = cmds.shadingNode(
            'multiplyDivide', name=blend_z, asUtility=True
        )
        cmds.connectAttr(f'{sampler_info}.normalCameraZ', f'{blend_z}.input1Z')
        cmds.connectAttr(f'{vectorB_mult}.outputZ', f'{blend_z}.input2Z')

    normalize: str = 'matcapSimpleBlendNormal_normalize'
    if not cmds.objExists(normalize):
        normalize = cmds.shadingNode(
            'aiNormalize', name=normalize, asUtility=True
        )
        cmds.connectAttr(f'{blend_x}.output1D', f'{normalize}.inputX')
        cmds.connectAttr(f'{blend_y}.output1D', f'{normalize}.inputY')
        cmds.connectAttr(f'{blend_z}.outputZ', f'{normalize}.inputZ')

    return normalize


def create_reoriented_normal(sampler_info: str) -> str:
    '''Create reoriented normal network.'''
    vector_u: str = 'matcapVectorU_mul'
    if not cmds.objExists(vector_u):
        vector_u = cmds.shadingNode(
            'multiplyDivide', name=vector_u, asUtility=True
        )
        cmds.setAttr(f'{vector_u}.input2', 1.0, 1.0, 1.25, type='double3')
        cmds.connectAttr(f'{sampler_info}.rayDirection', f'{vector_u}.input1')

    vector_t: str = 'matcapVectorT_add'
    if not cmds.objExists(vector_t):
        vector_t = cmds.shadingNode(
            'plusMinusAverage', name=vector_t, asUtility=True
        )
        cmds.setAttr(f'{vector_t}.input3D[1]', 0.0, 0.0, 1.0, type='double3')
        cmds.connectAttr(
            f'{sampler_info}.normalCamera', f'{vector_t}.input3D[0]'
        )

    vector_dot: str = 'matcapVectorTU_dot'
    if not cmds.objExists(vector_dot):
        vector_dot = cmds.shadingNode('aiDot', name=vector_dot, asUtility=True)
        cmds.connectAttr(f'{vector_t}.output3D', f'{vector_dot}.input1')
        cmds.connectAttr(f'{vector_u}.output', f'{vector_dot}.input2')

    dot_sub: str = 'matcapDotVectorU_sub'
    if not cmds.objExists(dot_sub):
        dot_sub = cmds.shadingNode(
            'plusMinusAverage', name=dot_sub, asUtility=True
        )
        cmds.setAttr(f'{dot_sub}.operation', 2)
        cmds.connectAttr(
            f'{vector_dot}.outValue', f'{dot_sub}.input3D[0].input3Dx'
        )
        cmds.connectAttr(
            f'{vector_dot}.outValue', f'{dot_sub}.input3D[0].input3Dy'
        )
        cmds.connectAttr(
            f'{vector_dot}.outValue', f'{dot_sub}.input3D[0].input3Dz'
        )
        cmds.connectAttr(f'{vector_u}.output', f'{dot_sub}.input3D[1]')

    vector_div: str = 'matcapVecTvecUz_div'
    if not cmds.objExists(vector_div):
        vector_div = cmds.shadingNode(
            'multiplyDivide', name=vector_div, asUtility=True
        )
        cmds.setAttr(f'{vector_div}.operation', 2)
        cmds.connectAttr(f'{vector_t}.output3D', f'{vector_div}.input1')
        cmds.connectAttr(f'{vector_u}.outputZ', f'{vector_div}.input2X')
        cmds.connectAttr(f'{vector_u}.outputZ', f'{vector_div}.input2Y')
        cmds.connectAttr(f'{vector_u}.outputZ', f'{vector_div}.input2Z')

    vector_mul: str = 'matcapVecTU_mul'
    if not cmds.objExists(vector_mul):
        vector_mul = cmds.shadingNode(
            'multiplyDivide', name=vector_mul, asUtility=True
        )
        cmds.connectAttr(f'{vector_div}.output', f'{vector_mul}.input1')
        cmds.connectAttr(f'{dot_sub}.output3D', f'{vector_mul}.input2')

    normalize: str = 'matcapReoriented_normalize'
    if not cmds.objExists(normalize):
        normalize = cmds.shadingNode(
            'aiNormalize', name=normalize, asUtility=True
        )
        cmds.connectAttr(f'{vector_mul}.output', f'{normalize}.input')

    return normalize


def apply(
    base_name: str,
    matcap_texture_path: str,
    matcap_normalmap_path: str,
    normal_mode: int = 0,
    assign_material: bool = False,
) -> tuple[str, str]:
    '''
    Create matcap network.
    normal_mode = 0: reoriented_normal, else: simple_blend_normal
    '''
    selection: list[str] = cmds.ls(selection=True)

    sampler_info: str = 'matcap_samplerInfo'
    if not cmds.objExists(sampler_info):
        cmds.shadingNode('samplerInfo', name=sampler_info, asUtility=True)

    simple_blend_normal: str = create_simple_blend_normal(sampler_info)
    reoriented_normal: str = create_reoriented_normal(sampler_info)
    blend_switch = cmds.shadingNode(
        'condition', name='matcapBlendNormal_condition', asUtility=True
    )
    cmds.setAttr(f'{blend_switch}.firstTerm', normal_mode)
    cmds.connectAttr(
        f'{reoriented_normal}.outValue', f'{blend_switch}.colorIfTrue'
    )
    cmds.connectAttr(
        f'{simple_blend_normal}.outValue', f'{blend_switch}.colorIfFalse'
    )

    (_, normalmap_file) = create_file('matcapNormalmap')
    cmds.setAttr(f'{normalmap_file}.colorSpace', 'Raw', type='string')
    cmds.setAttr(f'{normalmap_file}.ignoreColorSpaceFileRules', True)
    cmds.setAttr(
        f'{normalmap_file}.fileTextureName',
        matcap_normalmap_path,
        type='string',
    )

    normalmap_setRange: str = cmds.shadingNode(
        'setRange', name='normalMapToVector_setRange', asUtility=True
    )
    cmds.setAttr(f'{normalmap_setRange}.min', -1.0, -1.0, -1.0, type='double3')
    cmds.setAttr(f'{normalmap_setRange}.max', 1.0, 1.0, 1.0, type='double3')
    cmds.setAttr(f'{normalmap_setRange}.oldMin', 0.0, 0.0, 0.0, type='double3')
    cmds.setAttr(f'{normalmap_setRange}.oldMax', 1.0, 1.0, 1.0, type='double3')
    cmds.connectAttr(
        f'{normalmap_file}.outColor', f'{normalmap_setRange}.value'
    )

    blend_normalmap: str = cmds.shadingNode(
        'colorComposite', name='matcapBlendNormalmap_cc', asUtility=True
    )
    cmds.connectAttr(f'{blend_switch}.outColor', f'{blend_normalmap}.colorA')
    cmds.connectAttr(
        f'{normalmap_setRange}.outValue', f'{blend_normalmap}.colorB'
    )

    matcap_uv: str = cmds.shadingNode(
        'setRange', name='matcapUV_setRange', asUtility=True
    )
    cmds.setAttr(f'{matcap_uv}.min', 0.0, 0.0, 0.0, type='double3')
    cmds.setAttr(f'{matcap_uv}.max', 1.0, 1.0, 1.0, type='double3')
    cmds.setAttr(f'{matcap_uv}.oldMin', -1.0, -1.0, -1.0, type='double3')
    cmds.setAttr(f'{matcap_uv}.oldMax', 1.0, 1.0, 1.0, type='double3')
    cmds.connectAttr(f'{blend_normalmap}.outColor', f'{matcap_uv}.value')

    # FileノードだとUV Coordが反応しないので、aiImageを使う。
    matcap_file: str = cmds.shadingNode(
        'aiImage', name=f'{base_name}_aiImage', asUtility=True
    )
    cmds.setAttr(f'{matcap_file}.filename', matcap_texture_path, type='string')
    cmds.connectAttr(f'{matcap_uv}.outValueX', f'{matcap_file}.uvcoordsX')
    cmds.connectAttr(f'{matcap_uv}.outValueY', f'{matcap_file}.uvcoordsY')

    material: str = cmds.shadingNode(
        'aiStandardSurface', name=f'{base_name}_MT', asShader=True
    )
    cmds.setAttr(f'{material}.base', 0)
    cmds.setAttr(f'{material}.specular', 0)
    cmds.setAttr(f'{material}.emission', 1)
    cmds.connectAttr(f'{matcap_file}.outColor', f'{material}.emissionColor')

    sg: str = cmds.sets(
        name=f'{base_name}_MTSG',
        renderable=True,
        noSurfaceShader=True,
        empty=True,
    )
    cmds.connectAttr(f'{material}.outColor', f'{sg}.surfaceShader')

    if cmds.objExists('defaultArnoldRenderOptions'):
        cmds.setAttr('defaultArnoldRenderOptions.enable_swatch_render', 1)

    if selection:
        cmds.select(*selection)
    else:
        cmds.select(clear=True)

    if assign_material and selection:
        cmds.sets(edit=True, forceElement=sg)

    return (material, sg)


def main(unique_id: str = '') -> None:
    '''Show window.'''
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
