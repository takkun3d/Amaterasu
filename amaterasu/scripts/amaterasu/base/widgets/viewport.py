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
"""Provides viewport capture functionality for the Amaterasu toolset."""

from __future__ import annotations
import os
from maya import OpenMaya, OpenMayaUI, cmds, mel
from amaterasu.base.qt import QtCore, QtWidgets


class Viewport(QtWidgets.QWidget):
    """Widget for rendering and capturing the Maya viewport or shader ball.

    This widget embeds a Maya model editor into a Qt layout to provide
    either a standard perspective view or a specialized material viewer
    (shader ball). It also provides functionality to capture the view to
    an image file.

    Attributes:
        viewport_offset_width (int): Global offset for viewport width.
        viewport_offset_height (int): Global offset for viewport height.
    """

    viewport_offset_width: int = 0
    viewport_offset_height: int = 0

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        width: int = 512,
        height: int = 512,
        is_shader_ball: bool = False,
    ) -> None:
        """Initializes the ViewportCapture widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to QtCore.Qt.WindowType.Widget.
            width (int, optional): The initial width of the viewport.
                Defaults to 512.
            height (int, optional): The initial height of the viewport.
                Defaults to 512.
            is_shader_ball (bool, optional): Whether to initialize as a
                shader ball viewer. Defaults to False.
        """
        self.__width: int = width
        self.__height: int = height
        self.__is_shader_ball: bool = is_shader_ball
        self.__ibl_path: str = os.path.join(
            os.getenv("MAYA_LOCATION") or "",
            "presets",
            "Assets",
            "IBL",
            "Interior1_Color.exr",
        )
        self.__scriptjob: int = -1
        self.__renderer: str = ""

        super().__init__(parent, flag)
        self.setObjectName("Widget" + str(id(self)))
        self.set_image_size(width, height)
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setObjectName("Layout" + str(id(main_layout)))

        cmds.setParent(main_layout.objectName())
        self.__model_editor: str = cmds.modelEditor()  # type: ignore
        if not self.__is_shader_ball:
            cmds.modelEditor(
                self.__model_editor,
                edit=True,
                camera="persp",
                polymeshes=True,
                nurbsSurfaces=True,
                subdivSurfaces=True,
                displayTextures=True,
                displayAppearance="smoothShaded",
                allObjects=False,
                grid=False,
                dynamics=False,
                activeOnly=False,
                manipulators=False,
                headsUpDisplay=False,
                selectionHiliteDisplay=False,
            )
        else:
            # If Hypershade is not open, Maya will crash.
            mel.eval("HypershadeWindow;")
            # mel.eval("HypershadeOpenMaterialViewerWindow;")
            self.__scriptjob = cmds.scriptJob(
                event=("SelectionChanged", self.update_shading_graph)
            )  # type: ignore
            cmds.modelEditor(
                self.__model_editor,
                edit=True,
                sceneRenderFilter="shaderBallSceneFilter",
            )
            cmds.modelEditor(
                self.__model_editor,
                edit=True,
                activeCustomGeometry="meshShaderball",
            )
            cmds.modelEditor(
                self.__model_editor,
                edit=True,
                activeCustomEnvironment=self.__ibl_path,
            )
            self.update_shading_graph()

        # It is easier to use cmds.parent instead of Qt.
        # self.__model_panel_qt = maya_control_to_qt(self.__model_panel)
        # main_layout.addWidget(self.__model_panel_qt)

    def cleanup(self) -> None:
        """Cleans up Maya resources created by the widget.

        This method must be called before the widget is destroyed to ensure
        that script jobs and UI elements are properly removed from Maya.
        """
        if self.__is_shader_ball:
            cmds.scriptJob(kill=self.__scriptjob)
            cmds.modelEditor(
                self.__model_editor, edit=True, sceneRenderFilter=""
            )
        cmds.deleteUI(self.__model_editor)

    def set_image_size(self, width: int, height: int) -> None:
        """Sets the rendering size of the viewport.

        Args:
            width (int): The new width in pixels.
            height (int): The new height in pixels.
        """
        self.__width = width
        self.__height = height
        self.setMinimumSize(self.__width, self.__height)
        self.setMaximumSize(self.__width, self.__height)
        self.resize(self.__width, self.__height)

    def update_shading_graph(self) -> None:
        """Updates the active shading graph for the shader ball viewer.

        This method evaluates the current selection to determine the
        appropriate shading engine and material to display in the
        shader ball, and updates the model editor accordingly.
        """
        selection: list[str] = cmds.ls(selection=True)
        a: str = ""
        b: str = ""
        c: str = ""
        self.__renderer = ""
        for node in selection:
            c = node
            node_type: str = cmds.nodeType(node)  # type: ignore
            if cmds.getClassification(node_type, satisfies="shader/surface"):
                b = node
                connections: list[str] = cmds.listConnections(
                    node,
                    source=False,
                    destination=True,
                    skipConversionNodes=True,
                )
                for connection in connections:
                    if cmds.nodeType(connection) == "shadingEngine":
                        a = connection
                        break

            elif node_type == "shadingEngine":
                a = node
                connections = cmds.listConnections(
                    f"{node}.surfaceShader",
                    source=True,
                    destination=False,
                    skipConversionNodes=True,
                )
                if connections:
                    a = connections[0]

                connections = cmds.listConnections(
                    f"{node}.aiSurfaceShader",
                    source=True,
                    destination=False,
                    skipConversionNodes=True,
                )
                if connections:
                    a = connections[0]

            else:
                b = node

            if cmds.nodeType(node, api=True) == "kPluginDependNode":  # type: ignore
                self.__renderer = "Arnold"

        cmds.modelEditor(
            self.__model_editor,
            edit=True,
            activeShadingGraph=f"{a},{b},{c}",
        )
        cmds.modelEditor(
            self.__model_editor,
            edit=True,
            activeCustomRenderer=self.__renderer,
        )

    def capture(self, output: str) -> bool:
        """Captures the current viewport view and saves it to an image file.

        Args:
            output (str): The absolute file path to save the captured image.

        Returns:
            bool: True if the capture was successful, False otherwise.
        """
        window: str = cmds.window(width=self.__width, height=self.__height)  # type: ignore
        layout: str = cmds.formLayout()  # type: ignore
        editor: str = cmds.modelEditor(parent=layout)  # type: ignore
        if not self.__is_shader_ball:
            cmds.modelEditor(
                editor,
                edit=True,
                camera="persp",
                polymeshes=True,
                nurbsSurfaces=True,
                subdivSurfaces=True,
                displayTextures=True,
                displayAppearance="smoothShaded",
                allObjects=False,
                grid=False,
                dynamics=False,
                activeOnly=False,
                manipulators=False,
                headsUpDisplay=False,
                selectionHiliteDisplay=False,
            )
        else:
            # If Hypershade is not open, Maya will crash.
            mel.eval("HypershadeWindow;")
            # mel.eval("HypershadeOpenMaterialViewerWindow;")
            cmds.modelEditor(
                editor,
                edit=True,
                sceneRenderFilter="shaderBallSceneFilter",
            )
            cmds.modelEditor(
                editor,
                edit=True,
                activeCustomGeometry="meshShaderball",
            )
            cmds.modelEditor(
                editor,
                edit=True,
                activeCustomEnvironment=self.__ibl_path,
            )
            cmds.modelEditor(
                editor,
                edit=True,
                activeShadingGraph=cmds.modelEditor(
                    self.__model_editor, query=True, activeShadingGraph=True
                ),  # type: ignore
            )
            cmds.modelEditor(
                editor,
                edit=True,
                activeCustomRenderer=self.__renderer,
            )
        cmds.formLayout(
            layout,
            edit=True,
            attachForm=[
                (editor, "top", 0),
                (editor, "left", 0),
                (editor, "right", 0),
                (editor, "bottom", 0),
            ],
        )
        cmds.showWindow(window)

        # Note: OpenMaya 2.0 (maya.api.OpenMaya) requires a slightly different
        # approach for reading color buffers compared to the older API.
        image: OpenMaya.MImage = OpenMaya.MImage()
        view: OpenMayaUI.M3dView = OpenMayaUI.M3dView()
        OpenMayaUI.M3dView.getM3dViewFromModelEditor(editor, view)
        view.beginGL()
        view.readColorBuffer(image, 1)
        view.endGL()
        image.writeToFile(output)

        cmds.deleteUI(window)
        return True
