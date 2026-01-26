# ==============================================================================
#
# Amaterasu Menus
#
# Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.
#
# ==============================================================================
from __future__ import annotations
from typing import Any
from maya import cmds, mel

# ==============================================================================
#
# Variables
#
# ==============================================================================
__doc__ = '''Build amaterasu menu at a main window.'''
MAIN_MENU_NAME: str = 'AmaterasuMenu'
MAIN_MENU_LABEL: str = 'Amaterasu'
CB_MENU_NAME: str = 'AmaterasuChannelBoxMenu'
CB_MENU_LABEL: str = 'A'
SHELF_ICON: str = 'a_shelf.png'


# ==============================================================================
#
# Classes
#
# ==============================================================================
class Menu:
    '''This class creates menu in with statements.'''

    def __init__(self, object_name: str, **kwargs: Any) -> None:
        '''Get arguments for menu.'''
        self.__object_name: str = object_name
        self.__kwargs: dict[str, Any] = kwargs
        if 'tearOff' not in self.__kwargs:
            self.__kwargs['tearOff'] = True

    def __enter__(self) -> Menu:
        '''Create a menu.'''
        if self.__object_name:
            if cmds.menu(self.__object_name, exists=True):
                cmds.deleteUI(self.__object_name)

        cmds.menu(self.__object_name, **self.__kwargs)
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        '''Set to one level up in the menu hierarchy.'''
        cmds.setParent('..', menu=True)

    @staticmethod
    def create_python_command(module_path: str, func_name: str) -> str:
        '''Create a python command to run the tool.'''
        return f'import {module_path}\n{module_path}.{func_name}'

    def add_item(
        self,
        label: str,
        module: str,
        main_func: str = 'main()',
        option_func: str | None = None,
        is_window_only: bool = False,
        **kwargs: Any,
    ) -> None:
        '''Add a menu item with optional settings.'''

        if is_window_only and not label.endswith('...'):
            label += '...'

        command: str = self.create_python_command(module, main_func)
        cmds.menuItem(
            label=label, command=command, sourceType='python', **kwargs
        )
        if option_func:
            command = self.create_python_command(module, option_func)
            base_label: str = label[:-3] if label.endswith('...') else label
            option_label: str = f'{base_label} Option'
            cmds.menuItem(
                label=option_label,
                command=command,
                sourceType='python',
                optionBox=True,
            )

    def add_divider(self, label: str | None = None) -> None:
        '''Add a divider.'''
        if label:
            cmds.menuItem(divider=True, dividerLabel=label)
        else:
            cmds.menuItem(divider=True)


class SubMenu(Menu):
    '''This class creates submenu in with statements.'''

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        '''Get arguments for menuItem.'''
        self.__args: tuple[Any, ...] = args
        self.__kwargs: dict[str, Any] = kwargs
        if 'tearOff' not in self.__kwargs:
            self.__kwargs['tearOff'] = True

        if 'subMenu' not in self.__kwargs:
            self.__kwargs['subMenu'] = True

        if 'allowOptionBoxes' not in self.__kwargs:
            self.__kwargs['allowOptionBoxes'] = True

    def __enter__(self) -> SubMenu:
        '''Create a submenu.'''
        cmds.menuItem(*self.__args, **self.__kwargs)
        return self


# ==============================================================================
#
# Functions
#
# ==============================================================================
def create_main_menu() -> None:
    '''Create an Amaterasu menu in main window.'''
    cmds.setParent(mel.eval('$gMainWindow=$gMainWindow'))
    with Menu(
        MAIN_MENU_NAME, label=MAIN_MENU_LABEL, familyImage=SHELF_ICON
    ) as mm:

        with SubMenu(label='File') as m:
            m.add_divider('IO')
            m.add_item(
                'Auto Set Project',
                'amaterasu.file.auto_set_project',
                is_window_only=True,
            )
            m.add_item(
                'Open Project Directory', 'amaterasu.file.open_work_directory'
            )

            m.add_divider('Reference')
            m.add_item(
                'Replace Reference',
                'amaterasu.file.replace_reference',
                is_window_only=True,
            )
            m.add_item(
                'Rename Reference from Filename',
                'amaterasu.file.rename_reference',
            )
            m.add_item(
                'Rename Namespace from Filename',
                'amaterasu.file.rename_namespace',
            )

            m.add_divider('Utility')
            m.add_item(
                'Remove Unknown Nodes', 'amaterasu.file.remove_unknown_nodes'
            )
            m.add_item(
                'Remove Unknown Plugins',
                'amaterasu.file.remove_unknown_plugins',
            )
            m.add_item(
                'Remove Node Editor Info',
                'amaterasu.file.remove_node_editor_info',
            )

        with SubMenu(label='Edit') as m:
            m.add_divider('Shape')
            m.add_item('Combine Shapes', 'amaterasu.edit.combine_shapes')
            m.add_item('Separate Shapes', 'amaterasu.edit.separate_shapes')
            m.add_item('Replace Shapes', 'amaterasu.edit.replace_shapes')

            m.add_divider('Outliner')
            m.add_item(
                'Sort Nodes',
                'amaterasu.edit.sort_nodes',
                option_func='option()',
            )

        with SubMenu(label='Select') as m:
            m.add_divider('Polygons')
            m.add_item('Select Hard Edges', 'amaterasu.select.hard_edges')
            m.add_item(
                'Select Hard Edges Shell', 'amaterasu.select.hard_edges_shell'
            )
            m.add_item(
                'Select Each Nth Edges',
                'amaterasu.select.each_nth_edges',
                option_func='option()',
            )
            m.add_item('Select Crease Edges', 'amaterasu.select.crease_edges')
            m.add_item('Select Inverted UV', 'amaterasu.select.inverted_uv')

            m.add_divider('Node')
            m.add_item(
                'Select Animated Nodes', 'amaterasu.select.animated_nodes'
            )
            m.add_item(
                'Select Displayed Nodes', 'amaterasu.select.displayed_nodes'
            )
            m.add_item(
                'Select Stacked Nodes',
                'amaterasu.select.stacked_nodes',
                option_func='option()',
            )

        with SubMenu(label='Modify') as m:
            m.add_divider('Transform')
            m.add_item(
                'Lock & Hide Transform',
                'amaterasu.modify.lock_hide_transform',
                main_func='main(True)',
            )
            m.add_item(
                'Unlock & Show Transform',
                'amaterasu.modify.lock_hide_transform',
                main_func='main(False)',
            )
            m.add_item(
                'Unfreeze Transformations',
                'amaterasu.modify.unfreeze_transformations',
                is_window_only=True,
            )

            m.add_divider('Naming')
            m.add_item(
                'Renamer', 'amaterasu.modify.renamer', is_window_only=True
            )

            m.add_divider('Attribute')
            m.add_item(
                'Add Attribute',
                'amaterasu.modify.add_attribute',
                option_func='option()',
            )
            m.add_item('Reset Value', 'amaterasu.modify.reset_value')
            m.add_item(
                'Random Value',
                'amaterasu.modify.random_value',
                option_func='option()',
            )
            m.add_item(
                'Stocker', 'amaterasu.modify.stocker', is_window_only=True
            )
            m.add_item('Refresh', 'amaterasu.modify.refresh')

            m.add_divider('User Defined Attribute')
            m.add_item(
                'Attribute Reorder',
                'amaterasu.modify.attribute_reorder',
                is_window_only=True,
            )
            m.add_item(
                'Transfer User Defined Attr',
                'amaterasu.modify.transfer_user_defined_attr',
                is_window_only=True,
            )

            m.add_divider('Connection')
            m.add_item(
                'Show Node History',
                'amaterasu.modify.history_visibility',
                main_func='show()',
            )
            m.add_item(
                'Hide Node History',
                'amaterasu.modify.history_visibility',
                main_func='hide()',
            )

            m.add_divider('Utility')
            m.add_item(
                'Lock Node', 'amaterasu.modify.lock_node', main_func='lock()'
            )
            m.add_item(
                'Unlock Node',
                'amaterasu.modify.lock_node',
                main_func='unlock()',
            )

        with SubMenu(label='Display') as m:
            m.add_divider('Colors')
            m.add_item(
                'Outliner Color',
                'amaterasu.display.outliner_color',
                is_window_only=True,
            )
            m.add_item(
                'Drawing Color',
                'amaterasu.display.drawing_color',
                is_window_only=True,
            )

            m.add_divider('Viewport')
            m.add_item(
                'Perspective Guide',
                'amaterasu.display.perspective_guide',
                option_func='option()',
            )
            m.add_item(
                'XRay Geometry',
                'amaterasu.display.xray_geometry',
                is_window_only=True,
            )
            m.add_item(
                'Local Axis',
                'amaterasu.display.local_axis',
                is_window_only=True,
            )

        with SubMenu(label='Window') as m:
            m.add_divider('Manager')
            m.add_item(
                'Sets Manager',
                'amaterasu.window.sets_manager',
                is_window_only=True,
            )
            m.add_item(
                'Instance Manager',
                'amaterasu.window.instance_manager',
                is_window_only=True,
            )
            m.add_item(
                'File Manager',
                'amaterasu.window.file_manager',
                is_window_only=True,
            )

            m.add_divider('UI Element')
            m.add_item(
                'Shelf Stocker',
                'amaterasu.window.shelf_stocker',
                is_window_only=True,
            )

        mm.add_divider()

        with SubMenu(label='Modeling') as m:
            m.add_divider('Edge')
            m.add_item(
                'Apply Crease Edge',
                'amaterasu.modeling.apply_crease_edge',
                option_func='option()',
            )
            m.add_item(
                'Recovery Edge Type', 'amaterasu.modeling.recovery_edge_type'
            )

            m.add_divider('Face')
            m.add_item('Duplicate Face', 'amaterasu.modeling.duplicate_face')
            m.add_item('Extract Face', 'amaterasu.modeling.extract_face')
            m.add_item(
                'Extract Face Each Material',
                'amaterasu.modeling.extract_face_each_material',
            )
            m.add_item('Flatten Faces', 'amaterasu.modeling.flatten_faces')

            m.add_divider('Mirror')
            m.add_item(
                'Remove Half',
                'amaterasu.modeling.remove_half',
                option_func='option()',
            )
            m.add_item(
                'Mirror Geometry',
                'amaterasu.modeling.mirror_geometry',
                option_func='option()',
            )
            m.add_item(
                'Mirror Polygon',
                'amaterasu.modeling.mirror_polygon',
                option_func='option()',
            )
            m.add_item(
                'Symmetry', 'amaterasu.modeling.symmetry', is_window_only=True
            )

            m.add_divider('Combine')
            m.add_item(
                'Combine', 'amaterasu.modeling.combine', option_func='option()'
            )
            m.add_item(
                'Separate',
                'amaterasu.modeling.separate',
                option_func='option()',
            )

            m.add_divider('UV')
            m.add_item(
                'Camera Projection', 'amaterasu.modeling.camera_projection'
            )
            m.add_item(
                'UV Linker', 'amaterasu.modeling.uv_linker', is_window_only=True
            )

            m.add_divider('Utility')
            m.add_item(
                'Expand Mesh From UV', 'amaterasu.modeling.expand_mesh_from_uv'
            )
            m.add_item(
                'Smooth Mesh Preview',
                'amaterasu.modeling.smooth_mesh_preview',
                option_func='option()',
            )
            m.add_item(
                'Poly Cleaner',
                'amaterasu.modeling.poly_cleaner',
                option_func='option()',
            )

        with SubMenu(label='Animation') as m:
            m.add_divider('Create')
            m.add_item('Create Camera Rig', 'amaterasu.animation.camera_rig')
            m.add_item(
                'Create Motion Trail Curve[plug-ins]',
                'amaterasu.animation.create_motion_trail_curve',
                enable=False,
            )
            m.add_item(
                'Create Motion Curve',
                'amaterasu.animation.create_motion_curve',
                option_func='option()',
            )

            m.add_divider('Camera')
            m.add_item(
                'Shift Lens',
                'amaterasu.animation.shift_lens',
                is_window_only=True,
            )
            m.add_item(
                'Dolly Zoom',
                'amaterasu.animation.dolly_zoom',
                is_window_only=True,
            )
            m.add_item(
                'Perspective Inspector',
                'amaterasu.animation.perspective_inspector',
                is_window_only=True,
            )
            m.add_item(
                'Rotoscope',
                'amaterasu.animation.rotoscope',
                is_window_only=True,
            )

            m.add_divider('Keyframe')
            m.add_item(
                'Insert Keyframe',
                'amaterasu.animation.insert_keyframe',
                option_func='option()',
            )
            m.add_item(
                'Round Off Time',
                'amaterasu.animation.round_off_time',
                option_func='option()',
            )
            m.add_item(
                'Cycle Keyframe',
                'amaterasu.animation.cycle_keyframe',
                option_func='option()',
            )
            m.add_item(
                'Offset Keyframe',
                'amaterasu.animation.offset_keyframe',
                is_window_only=True,
            )
            m.add_item(
                'Between Keyframe',
                'amaterasu.animation.between_keyframe',
                is_window_only=True,
            )

            m.add_divider('Animation')
            m.add_item(
                'Copy Animation',
                'amaterasu.animation.copy_animation',
                option_func='option()',
            )
            m.add_item(
                'Delete Unused Animation',
                'amaterasu.animation.delete_unused_animation',
                option_func='option()',
            )
            m.add_item(
                'Motion Denoiser',
                'amaterasu.animation.motion_denoiser',
                option_func='option()',
            )
            m.add_item(
                'Time Warp',
                'amaterasu.animation.time_warp',
                is_window_only=True,
            )

            m.add_divider('Utility')
            m.add_item(
                'Playblast',
                'amaterasu.animation.playblast',
                is_window_only=True,
            )
            m.add_item(
                'Anim Library',
                'amaterasu.animation.anim_library',
                is_window_only=True,
            )

        with SubMenu(label='Rigging') as m:
            m.add_divider('Skeleton & Skin')
            m.add_item(
                'Joint Editor',
                'amaterasu.rigging.joint_editor',
                is_window_only=True,
            )
            m.add_item(
                'Skin Weight Editor',
                'amaterasu.rigging.skin_weight_editor',
                is_window_only=True,
            )

            m.add_divider('Controllers')
            m.add_item(
                'Create Controller',
                'amaterasu.rigging.create_controller',
                is_window_only=True,
            )
            m.add_item(
                'Insert Space',
                'amaterasu.rigging.insert_space',
            )
            m.add_item(
                'Pivot Shifter',
                'amaterasu.rigging.pivot_shifter',
                is_window_only=True,
            )
            m.add_item(
                'Curve Rivet',
                'amaterasu.rigging.curve_rivet',
                option_func='option()',
            )
            m.add_item('Curve Linker', 'amaterasu.rigging.curve_linker')

            m.add_divider('Deformation')
            m.add_item(
                'Soft Tweak',
                'amaterasu.rigging.soft_tweak',
                is_window_only=True,
            )
            m.add_item(
                'Cluster Tweak',
                'amaterasu.rigging.cluster_tweak',
                is_window_only=True,
            )

            m.add_divider('Constraint')
            m.add_item(
                'Matrix Constraint',
                'amaterasu.rigging.matrix_constraint',
                is_window_only=True,
            )
            m.add_item(
                'Geometry Constraint', 'amaterasu.rigging.geometry_constraint'
            )
            m.add_item(
                'Bend Constraint',
                'amaterasu.rigging.bend_constraint',
                option_func='option()',
            )
            m.add_item(
                'Roll Constraint',
                'amaterasu.rigging.roll_constraint',
                option_func='option()',
            )

            m.add_divider('Utilities')
            m.add_item('Decompose Rotate', 'amaterasu.rigging.decompose_rotate')
            m.add_item(
                'Animation To Driven Key',
                'amaterasu.rigging.convert_animation_to_driven_key',
                is_window_only=True,
            )

        with SubMenu(label='Rendering') as m:
            m.add_divider('Look Dev')
            m.add_item('Reload Texture', 'amaterasu.rendering.reload_texture')
            m.add_item(
                'Generate All UDIM Preview',
                'amaterasu.rendering.generate_all_udim_preview',
            )
            m.add_item(
                'Matcap', 'amaterasu.rendering.matcap', is_window_only=True
            )
            m.add_item(
                'Material Library',
                'amaterasu.rendering.material_library',
                is_window_only=True,
            )

            m.add_divider('Render Setup')
            m.add_item(
                'Make Overrides',
                'amaterasu.rendering.make_overrides',
                is_window_only=True,
            )
            m.add_item(
                'Register Geometry',
                'amaterasu.rendering.register_geometry',
                is_window_only=True,
            )

            m.add_divider('Camera')
            m.add_item(
                'Overscan',
                'amaterasu.rendering.overscan',
                is_window_only=True,
            )
            m.add_item(
                'Bake Film Offset',
                'amaterasu.rendering.bake_film_offset',
                is_window_only=True,
            )

            m.add_divider('Toon')
            m.add_item(
                'PfxToon Manager',
                'amaterasu.rendering.pfx_toon_manager',
                is_window_only=True,
            )

            m.add_divider('Settings')
            m.add_item(
                'Disable anti-aliasing(SW)',
                'amaterasu.rendering.disable_anti_aliasing',
            )

        with SubMenu(label='Development') as m:
            m.add_divider('Python')
            m.add_item(
                'Package Installer',
                'amaterasu.development.package_installer',
                is_window_only=True,
            )

        mm.add_divider()

        with SubMenu(label='Web Site') as m:
            m.add_divider('Amaterasu')
            m.add_item('Home', 'amaterasu', main_func='show_home()')
            m.add_item('Patch Note', 'amaterasu', main_func='show_patch_note()')
            m.add_item('Manual', 'amaterasu', main_func='show_manual()')

            m.add_divider('Other')
            m.add_item(
                'Digital Craft Nodes', 'amaterasu', main_func='show_dcn()'
            )

        mm.add_divider()

        mm.add_item('About', 'amaterasu', main_func='show_about()')


def create_channelbox_menu() -> None:
    '''Create an Amaterasu menu in channel box.'''
    channel_box = mel.eval('$gChannelBoxForm=$gChannelBoxForm')
    cmds.setParent(f'{channel_box}|menuBarLayout1')
    with Menu(CB_MENU_NAME, label=CB_MENU_LABEL) as mm:
        mm.add_divider('Transform')
        mm.add_item(
            'Lock && Hide Transform',
            'amaterasu.modify.lock_hide_transform',
            main_func='main(True)',
        )
        mm.add_item(
            'Unlock && Show Transform',
            'amaterasu.modify.lock_hide_transform',
            main_func='main(False)',
        )
        mm.add_item(
            'Unfreeze Transformations',
            'amaterasu.modify.unfreeze_transformations',
            is_window_only=True,
        )

        mm.add_divider('Attribute')
        mm.add_item(
            'Add Attribute',
            'amaterasu.modify.add_attribute',
            option_func='option()',
        )
        mm.add_item(
            'Reset Value',
            'amaterasu.modify.reset_value',
        )
        mm.add_item(
            'Random Value',
            'amaterasu.modify.random_value',
            option_func='option()',
        )
        mm.add_item(
            'Stocker',
            'amaterasu.modify.stocker',
            is_window_only=True,
        )
        mm.add_item('Refresh', 'amaterasu.modify.refresh')

        mm.add_divider('User Defined Attribute')
        mm.add_item(
            'Attribute Reorder',
            'amaterasu.modify.attribute_reorder',
            is_window_only=True,
        )
        mm.add_item(
            'Transfer User Defined Attr',
            'amaterasu.modify.transfer_user_defined_attr',
            is_window_only=True,
        )

        mm.add_divider('Keyframe')
        mm.add_item(
            'Insert Keyframe',
            'amaterasu.animation.insert_keyframe',
            option_func='option()',
        )
        mm.add_item(
            'Round Off Time',
            'amaterasu.animation.round_off_time',
            option_func='option()',
        )
        mm.add_item(
            'Cycle Keyframe',
            'amaterasu.animation.cycle_keyframe',
            option_func='option()',
        )
        mm.add_item(
            'Offset Keyframe',
            'amaterasu.animation.offset_keyframe',
            is_window_only=True,
        )

        mm.add_divider('Animation')
        mm.add_item(
            'Copy Animation',
            'amaterasu.animation.copy_animation',
            option_func='option()',
        )
        mm.add_item(
            'Delete Unused Animation',
            'amaterasu.animation.delete_unused_animation',
            option_func='option()',
        )
