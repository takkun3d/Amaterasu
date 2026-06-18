# Copyright (c) 2014-2026 takkun (takkun3d). Released under the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Amaterasu Parallax Interior Mapping Tool.

This module provides a tool to automatically generate a hybrid shading network
for parallax interior mapping. It seamlessly bridges real-time viewport shaders
(GLSL/HLSL) with Arnold's offline OSL shaders, linking their attributes to
provide a unified and intuitive artist experience.
"""

from __future__ import annotations
import pathlib
from maya import cmds
from mtoa import osl
from amaterasu.base.qt import QtCore, QtWidgets
from amaterasu.base import utils, framework, dcc, widgets
from amaterasu import env

__product__: str = "Parallax Interior Mapping"
__version__: str = "1.00"
__copyright__: str = f"""
{env.DEFAULT_LICENSE}
<hr />
Parallax Interior Mapping (GLSL / HLSL / OSL)<br />
Based on "jiWindowBox" by Autodesk Inc., licensed under the Apache License, Version 2.0.<br />
See the respective source files for detailed copyright and license notices.<br />
https://github.com/ADN-DevTech/3dsMax-OSL-Shaders/blob/master/LICENSE.txt
"""
_logger: utils.Logger = utils.get_logger(__product__)

NEED_PLUGINS: list[str] = ["glslShader.mll", "dx11Shader.mll", "mtoa.mll"]
SHADER_DIR: pathlib.Path = env.RESOURCE_PATH / "shader"
SOURCE_FILES: dict[str, pathlib.Path] = {
    "glsl": SHADER_DIR / "parallax_interior_mapping_v1_0.ogsfx",
    "hlsl": SHADER_DIR / "parallax_interior_mapping_v1_0.fx",
    "osl": SHADER_DIR / "parallax_interior_mapping_v1_0.osl",
}

ATTRIBUTE_LINK: list[str] = [
    "MainDepth",
    "EnableLayer0",
    "DepthLayer0",
    "EnableLayer1",
    "DepthLayer1",
    "EnableLayer2",
    "DepthLayer2",
    "EnableLayer3",
    "DepthLayer3",
]


class Settings(framework.ToolSettings):
    """Tool settings for the Parallax Interior Mapping tool.

    Attributes:
        window_geo (framework.Variant[str]): The serialized window geometry for
            restoring the UI layout.
        base_name (framework.Variant[str]): The default base name prefix applied
            to all generated Maya nodes.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    base_name: framework.Variant[str] = framework.Variant("Parallax")


class MainWindow(framework.StandardToolWindow[Settings]):
    """The main user interface for the Parallax Interior Mapping tool.

    Inherits from `StandardToolWindow` to provide a consistent Amaterasu UI
    with standard execution buttons. Manages user inputs for the base name,
    viewport engine preference, and interior texture assignment.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        unique_id: str = "",
    ) -> None:
        """Initializes the MainWindow widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
            unique_id (str, optional): A unique identifier for the widget.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 280)
        self.__base_name: QtWidgets.QLineEdit
        self.__engine: QtWidgets.QComboBox
        self.__image: widgets.ImageDropImage

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the tool-specific user interface and binds settings.

        Args:
            parent (QtWidgets.QWidget): The central container widget where the
                custom UI elements should be added.
        """
        main_layout: widgets.FormLayout = widgets.FormLayout(parent)

        self.__base_name = QtWidgets.QLineEdit(self)
        main_layout.addRow(widgets.FormLabel("Base Name"), self.__base_name)

        self.__engine = QtWidgets.QComboBox(parent)
        self.__engine.addItems(["GLSL (OpenGL)", "HLSL (DirectX 11)"])
        if dcc.viewport.get_current_viewport_engine() == "HLSL":
            self.__engine.setCurrentIndex(1)
        else:
            self.__engine.setCurrentIndex(0)
        main_layout.addRow(widgets.FormLabel("Viewport Engine"), self.__engine)

        self.__image = widgets.ImageDropImage(128, 128, self)
        main_layout.addRow(widgets.FormLabel("Texture"), self.__image)

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.base_name.bind(
            setter=self.__base_name.setText,
            getter=self.__base_name.text,
        )

    @QtCore.Slot()
    @dcc.undo
    def apply(self) -> None:
        """Executes the main tool logic to build the parallax network.

        This slot is triggered by the Apply button. It saves the UI settings,
        copies the shader files to the project, and initializes the network
        creation process based on user inputs. Wrapped with an undo chunk.
        """
        self.save_settings()
        texture_path: str = self.__image.file_path()
        engine_choice: str = (
            "HLSL" if self.__engine.currentIndex() == 1 else "GLSL"
        )

        shader_paths: dict[str, pathlib.Path] = dcc.project.deploy_resources(
            source_files=SOURCE_FILES,
            sub_dir="data/shader",
        )
        result: utils.Result = create_network(
            self.__base_name.text(),
            shader_paths,
            texture_path,
            engine_choice,
        )
        result.log(_logger)


def create_network(
    base_name: str,
    shader_paths: dict[str, pathlib.Path],
    texture_path: str,
    engine_choice: str,
) -> utils.Result:
    """Builds the shading network and links attributes.

    Constructs the complete node graph including 2D placement, texture file,
    real-time viewport shader (GLSL/HLSL), Arnold OSL shader, and shading engine.
    It forcefully compiles the OSL code and connects shared attributes.

    Args:
        base_name (str): The prefix used for naming generated nodes.
        shader_paths (dict[str, pathlib.Path]): The dictionary of copied shader
            paths returned by `setup_project_shaders`.
        texture_path (str): The absolute path to the assigned texture image.
        engine_choice (str): The selected rendering engine ("GLSL" or "HLSL").
    """
    result: utils.Result = utils.Result()
    selection: list[str] = cmds.ls(selection=True)

    if "glsl" not in shader_paths or not shader_paths["glsl"].exists():
        path_info: pathlib.Path = shader_paths.get("glsl", pathlib.Path())
        result.set_error(f"GLSL shader file not found.: {path_info}")
        return result

    if "hlsl" not in shader_paths or not shader_paths["hlsl"].exists():
        path_info = shader_paths.get("hlsl", pathlib.Path())
        result.set_error(f"HLSL shader file not found.: {path_info}")
        return result

    if "osl" not in shader_paths or not shader_paths["osl"].exists():
        path_info = shader_paths.get("osl", pathlib.Path())
        result.set_error(f"OSL shader file not found.: {path_info}")
        return result

    if not texture_path or not pathlib.Path(texture_path).exists():
        result.set_error(f"Texture image not found.: {texture_path}")
        return result

    for plugin in NEED_PLUGINS:
        r: utils.Result = dcc.plugin.load(plugin)
        if r.status() != utils.ResultStatus.SUCCESS:
            result.merge(r)
            return result

    # --------------------------------------------------------------------------
    # Placement 2D
    place2d: str = cmds.shadingNode(
        'place2dTexture',
        name=f"{base_name}_p2d",
        asUtility=True,
    )

    # --------------------------------------------------------------------------
    # File Node
    file_node: str = cmds.shadingNode(
        'file',
        name=f"{base_name}_Tex",
        asTexture=True,
        isColorManaged=True,
    )
    cmds.setAttr(f"{file_node}.fileTextureName", texture_path, type="string")
    cmds.connectAttr(f"{place2d}.outUV", f"{file_node}.uvCoord")
    cmds.connectAttr(f"{place2d}.outUvFilterSize", f"{file_node}.uvFilterSize")

    # --------------------------------------------------------------------------
    # Viewport Shader
    if engine_choice == "GLSL":
        viewport_node: str = cmds.shadingNode(
            "GLSLShader",
            name=f"{base_name}GLSL_MT",
            asShader=True,
        )
        cmds.setAttr(
            f"{viewport_node}.shader",
            str(shader_paths["glsl"]),
            type="string",
        )

    else:
        viewport_node = cmds.shadingNode(
            "dx11Shader",
            name=f"{base_name}HLSL_MT",
            asShader=True,
        )
        cmds.setAttr(
            f"{viewport_node}.shader",
            str(shader_paths["hlsl"]),
            type="string",
        )

    cmds.connectAttr(f"{file_node}.outColor", f"{viewport_node}.MainTexture")

    # --------------------------------------------------------------------------
    # OSL Shader
    osl_node: str = cmds.shadingNode(
        'aiOslShader',
        name=f"{base_name}OSL_MT",
        asShader=True,
    )
    osl_code: str = shader_paths["osl"].read_text(encoding="utf-8")
    cmds.setAttr(f"{osl_node}.codeCache", osl_code, type="string")
    cmds.setAttr(f"{osl_node}.code", osl_code, type="string")
    osl.OSLSceneModel(osl_code, osl_node)
    cmds.connectAttr(f"{file_node}.fileTextureName", f"{osl_node}.filename")
    for attr in ATTRIBUTE_LINK:
        cmds.connectAttr(f"{viewport_node}.{attr}", f"{osl_node}.{attr}")

    # --------------------------------------------------------------------------
    # Arnold Shader
    ai_flat: str = cmds.shadingNode(
        "aiFlat", asShader=True, name=f"{base_name}Ai_MT"
    )

    cmds.connectAttr(f"{osl_node}.outColor", f"{ai_flat}.color")

    # --------------------------------------------------------------------------
    # Shading Engine
    sg_node: str = cmds.sets(
        name=f"{base_name}_MTSG",
        renderable=True,
        noSurfaceShader=True,
        empty=True,
    )  # type: ignore
    cmds.connectAttr(f"{viewport_node}.outColor", f"{sg_node}.surfaceShader")
    cmds.connectAttr(f"{ai_flat}.outColor", f"{sg_node}.aiSurfaceShader")

    if selection:
        cmds.sets(*selection, edit=True, forceElement=sg_node)
        cmds.select(*selection)

    else:
        cmds.select(viewport_node)

    return result


def main(unique_id: str = "") -> None:
    """Entry point for launching the Parallax Interior Mapping tool.

    Instantiates and displays the tool's main window.

    Args:
        unique_id (str, optional): A unique string identifier for the tool window.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
