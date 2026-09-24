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
"""Rotoscope tool for layout and animation in Maya.

This module provides various contextual tools, camera management,
and image plane layering to assist with scene layout and animation.
"""

from __future__ import annotations
from typing import Any
import os
from functools import partial
from maya import cmds, mel
from amaterasu.base.qt import QtCore, QtGui, QtWidgets
from amaterasu.base import dcc, framework, utils, widgets, system
from amaterasu.animation import shift_lens, dolly_zoom, camera_rig

__product__: str = "Rotoscope"
__version__: str = "1.62"
_logger: utils.Logger = utils.get_logger(__product__)

DEFAULT_MAIN_PANEL_SIZE: list[tuple[int, int, int]] = [
    (1, 80, 100),
    (2, 20, 100),
]
DEFAULT_LEFT_PANEL_SIZE: list[tuple[int, int, int]] = [
    (1, 100, 99),
    (2, 100, 1),
]
DEFAULT_RIGHT_PANEL_SIZE: list[tuple[int, int, int]] = [
    (1, 100, 1),
    (2, 100, 29),
    (3, 100, 70),
]


class Settings(framework.ToolSettings):
    """Settings for the Rotoscope tool.

    Note:
        Attribute names match Maya's `modelEditor` kwargs (camelCase) to allow
        dynamic iteration, rather than standard Python snake_case.

    Attributes:
        window_geo (framework.Variant[str]): Geometry of the window.
        main_panel (framework.Variant[list[tuple[int, int, int]]]): Size of main.
        left_panel (framework.Variant[list[tuple[int, int, int]]]): Size of left.
        right_panel (framework.Variant[list[tuple[int, int, int]]]): Size of right.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    main_panel: framework.Variant[list[tuple[int, int, int]]] = (
        framework.Variant(DEFAULT_MAIN_PANEL_SIZE)
    )
    left_panel: framework.Variant[list[tuple[int, int, int]]] = (
        framework.Variant(DEFAULT_LEFT_PANEL_SIZE)
    )
    right_panel: framework.Variant[list[tuple[int, int, int]]] = (
        framework.Variant(DEFAULT_RIGHT_PANEL_SIZE)
    )

    camera: framework.Variant[str] = framework.Variant("persp")
    displayLights: framework.Variant[str] = framework.Variant("default")
    bufferMode: framework.Variant[str] = framework.Variant("double")
    activeOnly: framework.Variant[bool] = framework.Variant(False)
    twoSidedLighting: framework.Variant[bool] = framework.Variant(False)
    displayAppearance: framework.Variant[str] = framework.Variant(
        "smoothShaded"
    )
    wireframeOnShaded: framework.Variant[bool] = framework.Variant(False)
    useDefaultMaterial: framework.Variant[bool] = framework.Variant(False)
    wireframeBackingStore: framework.Variant[bool] = framework.Variant(False)
    backfaceCulling: framework.Variant[bool] = framework.Variant(True)
    xray: framework.Variant[bool] = framework.Variant(False)
    jointXray: framework.Variant[bool] = framework.Variant(False)
    activeComponentsXray: framework.Variant[bool] = framework.Variant(False)
    maxConstantTransparency: framework.Variant[float] = framework.Variant(1.0)
    displayTextures: framework.Variant[bool] = framework.Variant(True)
    smoothWireframe: framework.Variant[bool] = framework.Variant(False)
    lineWidth: framework.Variant[float] = framework.Variant(1.0)
    textureAnisotropic: framework.Variant[bool] = framework.Variant(False)
    textureSampling: framework.Variant[int] = framework.Variant(2)
    textureDisplay: framework.Variant[str] = framework.Variant("modulate")
    textureHilight: framework.Variant[bool] = framework.Variant(True)
    fogging: framework.Variant[bool] = framework.Variant(False)
    fogSource: framework.Variant[str] = framework.Variant("fragment")
    fogMode: framework.Variant[str] = framework.Variant("linear")
    fogDensity: framework.Variant[float] = framework.Variant(0.1)
    fogEnd: framework.Variant[float] = framework.Variant(100.0)
    fogStart: framework.Variant[float] = framework.Variant(0.0)
    fogColor: framework.Variant[list[float]] = framework.Variant(
        [0.5, 0.5, 0.5, 1]
    )
    shadows: framework.Variant[bool] = framework.Variant(False)
    colorResolution: framework.Variant[list[int]] = framework.Variant(
        [256, 156]
    )
    bumpResolution: framework.Variant[list[int]] = framework.Variant([512, 512])
    transparencyAlgorithm: framework.Variant[str] = framework.Variant(
        "frontAndBackCull"
    )
    transpInShadows: framework.Variant[bool] = framework.Variant(False)
    cullingOverride: framework.Variant[str] = framework.Variant("none")
    lowQualityLighting: framework.Variant[bool] = framework.Variant(False)
    occlusionCulling: framework.Variant[bool] = framework.Variant(False)
    useBaseRenderer: framework.Variant[bool] = framework.Variant(False)
    useInteractiveMode: framework.Variant[bool] = framework.Variant(False)
    sortTransparent: framework.Variant[bool] = framework.Variant(True)
    viewSelected: framework.Variant[bool] = framework.Variant(False)

    controllers: framework.Variant[bool] = framework.Variant(False)
    nurbsCurves: framework.Variant[bool] = framework.Variant(True)
    nurbsSurfaces: framework.Variant[bool] = framework.Variant(False)
    controlVertices: framework.Variant[bool] = framework.Variant(False)
    hulls: framework.Variant[bool] = framework.Variant(False)
    polymeshes: framework.Variant[bool] = framework.Variant(True)
    subdivSurfaces: framework.Variant[bool] = framework.Variant(True)
    planes: framework.Variant[bool] = framework.Variant(False)
    lights: framework.Variant[bool] = framework.Variant(False)
    cameras: framework.Variant[bool] = framework.Variant(False)
    imagePlane: framework.Variant[bool] = framework.Variant(True)
    joints: framework.Variant[bool] = framework.Variant(False)
    ikHandles: framework.Variant[bool] = framework.Variant(False)
    deformers: framework.Variant[bool] = framework.Variant(False)
    dynamics: framework.Variant[bool] = framework.Variant(True)
    particleInstancers: framework.Variant[bool] = framework.Variant(True)
    fluids: framework.Variant[bool] = framework.Variant(False)
    hairSystems: framework.Variant[bool] = framework.Variant(False)
    follicles: framework.Variant[bool] = framework.Variant(False)
    nCloths: framework.Variant[bool] = framework.Variant(False)
    nParticles: framework.Variant[bool] = framework.Variant(True)
    nRigids: framework.Variant[bool] = framework.Variant(False)
    dynamicConstraints: framework.Variant[bool] = framework.Variant(False)
    locators: framework.Variant[bool] = framework.Variant(False)
    dimensions: framework.Variant[bool] = framework.Variant(False)
    pivots: framework.Variant[bool] = framework.Variant(False)
    handles: framework.Variant[bool] = framework.Variant(False)
    textures: framework.Variant[bool] = framework.Variant(False)
    strokes: framework.Variant[bool] = framework.Variant(True)
    motionTrails: framework.Variant[bool] = framework.Variant(True)
    pluginShapes: framework.Variant[bool] = framework.Variant(True)
    clipGhosts: framework.Variant[bool] = framework.Variant(True)
    greasePencils: framework.Variant[bool] = framework.Variant(True)
    manipulators: framework.Variant[bool] = framework.Variant(True)
    headsUpDisplay: framework.Variant[bool] = framework.Variant(True)
    grid: framework.Variant[bool] = framework.Variant(False)
    selectionHiliteDisplay: framework.Variant[bool] = framework.Variant(True)

    def read_from_model_panel(self, model_panel: str) -> None:
        """Reads flag values from the specified model panel.

        Args:
            model_panel (str): The name of the target model panel.
        """
        self.read_from_model_editor(
            cmds.modelPanel(model_panel, query=True, modelEditor=True)  # type: ignore
        )

    def read_from_model_editor(self, model_editor: str) -> None:
        """Reads flag values from the specified model editor.

        Args:
            model_editor (str): The name of the target model editor.
        """
        for element in self:
            try:
                if element.name() in [
                    "window_geo",
                    "main_panel",
                    "left_panel",
                    "right_panel",
                ]:
                    continue

                kwargs: dict[str, Any] = {
                    "query": True,
                    element.name(): True,
                }
                element.set_value(cmds.modelEditor(model_editor, **kwargs))

            except RuntimeError:
                _logger.warning("Unsupported flag: %s", element.name())

    def write_from_model_panel(self, model_panel: str) -> None:
        """Writes flag values to the specified model panel.

        Args:
            model_panel (str): The name of the target model panel.
        """
        self.write_from_model_editor(
            cmds.modelPanel(model_panel, query=True, modelEditor=True)  # type: ignore
        )

    def write_from_model_editor(self, model_editor: str) -> None:
        """Writes flag values to the specified model editor.

        Args:
            model_editor (str): The name of the target model editor.
        """
        for element in self:
            try:
                if element.name() in [
                    "window_geo",
                    "main_panel",
                    "left_panel",
                    "right_panel",
                ]:
                    continue

                if element.name() == "camera":
                    if not cmds.objExists(element.value()):
                        element.set_value("persp")

                kwargs: dict[str, Any] = {
                    "edit": True,
                    element.name(): element.value(),
                }
                cmds.modelEditor(model_editor, **kwargs)

            except RuntimeError:
                _logger.warning("Unsupported flag: %s", element.name())


class BaseCameraDraggerContext:
    """Base class for camera dragging contexts."""

    def __init__(
        self,
        tool_name: str,
        cursor: str = "crossHair",
        tool_image: str = "",
        help_string: str = "",
        camera: str = "",
    ) -> None:
        """Initializes the context.

        Args:
            tool_name (str): Name of the dragger context tool.
            cursor (str, optional): Cursor icon string. Defaults to 'crossHair'.
            tool_image (str, optional): Tool image path. Defaults to ''.
            help_string (str, optional): Tool help text. Defaults to ''.
            camera (str, optional): Target camera name. Defaults to ''.
        """
        self.__tool_name: str = tool_name
        self.__cursor: str = cursor
        self.__tool_image: str = tool_image
        self.__help: str = help_string
        self.__camera: str = camera
        self.__start_x: float = 0.0
        self.__start_y: float = 0.0
        self.__start_z: float = 0.0

    def cursor(self) -> str:
        """Returns the current cursor string.

        Returns:
            str: The cursor string.
        """
        return self.__cursor

    def set_cursor(self, cursor: str) -> None:
        """Sets a new cursor string.

        Args:
            cursor (str): The cursor string to apply.
        """
        self.__cursor = cursor

    def camera(self) -> str:
        """Returns the current target camera.

        Returns:
            str: The camera name.
        """
        return self.__camera

    def set_camera(self, camera: str) -> None:
        """Sets the target camera.

        Args:
            camera (str): The camera name.
        """
        self.__camera = camera

    def press_event(self) -> None:
        """Handles the mouse press event during drag."""
        x: float
        y: float
        z: float
        x, y, z = cmds.draggerContext(
            self.__tool_name, query=True, anchorPoint=True
        )  # type: ignore
        self.__start_x = x
        self.__start_y = y
        self.__start_z = z

        self.__camera = self.camera()
        self.setup_drag()

    def drag_event(self) -> None:
        """Handles the mouse drag event."""
        pos: tuple[float, float, float] = cmds.draggerContext(
            self.__tool_name, query=True, dragPoint=True
        )  # type: ignore
        mods: int = cmds.getModifiers()
        self.execute_drag(
            (self.__start_x, self.__start_y, self.__start_z),
            pos,
            (mods & 1) > 0,
            (mods & 4) > 0,
        )
        cmds.refresh()

    def setup_drag(self) -> None:
        """Initializes values before drag execution."""

    def execute_drag(
        self,
        start_pos: tuple[float, float, float],
        pos: tuple[float, float, float],
        is_shift: bool,
        is_ctrl: bool,
    ) -> None:
        """Executes the specific drag logic.

        Args:
            start_pos (tuple[float, float, float]): The anchor position.
            pos (tuple[float, float, float]): The current drag position.
            is_shift (bool): True if Shift is held.
            is_ctrl (bool): True if Ctrl is held.
        """

    def set_tool(self) -> None:
        """Registers and activates the context tool in Maya."""
        if cmds.draggerContext(self.__tool_name, exists=True):
            cmds.deleteUI(self.__tool_name)

        cmds.draggerContext(
            self.__tool_name,
            pressCommand=self.press_event,
            dragCommand=self.drag_event,
            cursor=self.__cursor,
            undoMode="step",
            image1=self.__tool_image,
            helpString=self.__help,
        )
        cmds.setToolTo(self.__tool_name)

    def zoom_2d(self) -> float:
        """Retrieves the 2D zoom scale factor for the current camera.

        Returns:
            float: The 2D zoom scale if pan/zoom is enabled, otherwise 1.0.
        """
        zoom_scale: float = 1.0
        camera_node: str = self.camera()
        shapes: list[str] = cmds.listRelatives(camera_node, shapes=True) or []
        cam_shape: str = shapes[0] if shapes else camera_node
        if cmds.objExists(f"{cam_shape}.panZoomEnabled"):
            if cmds.getAttr(f"{cam_shape}.panZoomEnabled"):
                zoom_scale = cmds.getAttr(f"{cam_shape}.zoom")

        return zoom_scale


class FilmOffsetContext(BaseCameraDraggerContext):
    """Context for modifying the film offset of a camera."""

    def __init__(self, camera: str = "") -> None:
        """Initializes the film offset context.

        Args:
            camera (str, optional): Target camera name. Defaults to ''.
        """
        super().__init__(
            "FilmOffsetTool",
            "track",
            "a_move.png",
            "Film Offset Tool: Drag in viewport to adjust. (Shift: Lock Axis)",
            camera,
        )
        self.__start_offset_x: float = 0.0
        self.__start_offset_y: float = 0.0
        self.__horizontal_plug: str = ""
        self.__vertical_plug: str = ""
        self.__lock_axis: str = ""

    def setup_drag(self) -> None:
        """Initializes the offset plugs before drag begins."""
        self.__horizontal_plug = find_target_plug(
            self.camera(),
            "horizontalFilmOffset",
            "filmOffsetSlider_C_ctrl",
            "translateX",
        )
        self.__start_offset_x = cmds.getAttr(self.__horizontal_plug)

        self.__vertical_plug = find_target_plug(
            self.camera(),
            "verticalFilmOffset",
            "filmOffsetSlider_C_ctrl",
            "translateY",
        )
        self.__start_offset_y = cmds.getAttr(self.__vertical_plug)

        self.__lock_axis = ""

    def execute_drag(
        self,
        start_pos: tuple[float, float, float],
        pos: tuple[float, float, float],
        is_shift: bool,
        is_ctrl: bool,
    ) -> None:
        """Executes the film offset adjust based on mouse drag.

        Args:
            start_pos (tuple[float, float, float]): Anchor position.
            pos (tuple[float, float, float]): Current position.
            is_shift (bool): True if Shift is held.
            is_ctrl (bool): True if Ctrl is held.
        """
        sensitivity: float = -0.001 * self.zoom_2d()
        delta_x: float = (pos[0] - start_pos[0]) * sensitivity
        delta_y: float = (pos[1] - start_pos[1]) * sensitivity
        if is_shift:
            abs_x: float = abs(pos[0] - start_pos[0])
            abs_y: float = abs(pos[1] - start_pos[1])
            if not self.__lock_axis and (abs_x > 5 or abs_y > 5):
                if abs_x > abs_y:
                    self.__lock_axis = "x"
                else:
                    self.__lock_axis = "y"

            if self.__lock_axis == "x":
                delta_y = 0.0
            elif self.__lock_axis == "y":
                delta_x = 0.0

        else:
            self.__lock_axis = ""

        cmds.setAttr(self.__horizontal_plug, self.__start_offset_x + delta_x)
        cmds.setAttr(self.__vertical_plug, self.__start_offset_y + delta_y)


class PostScaleContext(BaseCameraDraggerContext):
    """Context for modifying the post scale of a camera."""

    def __init__(self, camera: str = "") -> None:
        """Initializes the post scale context.

        Args:
            camera (str, optional): Target camera name. Defaults to ''.
        """
        super().__init__(
            "PostScaleTool",
            "dolly",
            "a_zoom.png",
            "Post Scale Tool: Drag in the viewport to adjust.",
            camera,
        )
        self.__start_post_scale: float = 1.0
        self.__scale_plug: str = ""

    def setup_drag(self) -> None:
        """Initializes the post scale plug before drag begins."""
        self.__scale_plug = find_target_plug(
            self.camera(),
            "postScale",
            "camera_C_ctrl",
            "postScale",
        )
        self.__start_post_scale = cmds.getAttr(self.__scale_plug)

    def execute_drag(
        self,
        start_pos: tuple[float, float, float],
        pos: tuple[float, float, float],
        is_shift: bool,
        is_ctrl: bool,
    ) -> None:
        """Executes the post scale adjust based on mouse drag.

        Args:
            start_pos (tuple[float, float, float]): Anchor position.
            pos (tuple[float, float, float]): Current position.
            is_shift (bool): True if Shift is held.
            is_ctrl (bool): True if Ctrl is held.
        """
        sensitivity: float = 0.001 * self.zoom_2d()
        delta: float = (
            (pos[0] - start_pos[0]) + (pos[1] - start_pos[1])
        ) * sensitivity
        new_scale: float = max(0.001, self.__start_post_scale + delta)
        cmds.setAttr(self.__scale_plug, new_scale)


class LayerItemWidget(QtWidgets.QWidget):
    """Widget representing a single layer item in the list."""

    visibility_toggled: QtCore.Signal = QtCore.Signal(str, bool)
    name_changed = QtCore.Signal(str, str)
    update_requested: QtCore.Signal = QtCore.Signal()
    request_attribute_editor = QtCore.Signal(str)

    def __init__(
        self, node: str, parent: QtWidgets.QWidget | None = None
    ) -> None:
        """Initializes the layer widget.

        Args:
            node (str): The node name.
            parent (QtWidgets.QWidget | None, optional): Parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.__node: str = node

        self.__main_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout(self)
        self.__main_layout.setContentsMargins(4, 4, 4, 4)

        self.__visible: widgets.IconButton = widgets.IconButton(self)
        self.update_visible_state()
        self.__visible.clicked.connect(self.on_visible_clicked)
        self.__main_layout.addWidget(self.__visible)

        self.__thumbnail: QtWidgets.QLabel = QtWidgets.QLabel()
        self.__thumbnail.setFixedSize(30, 30)
        self.__thumbnail.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.update_thumbnail()
        self.__main_layout.addWidget(self.__thumbnail)

        self.__name: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self.__node)
        self.__name.setFrame(False)
        self.__name.setReadOnly(True)
        self.__name.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )
        self.__name.setStyleSheet("background: transparent;")
        self.__name.editingFinished.connect(self.rename_node)
        self.__main_layout.addWidget(self.__name)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handles mouse double click events on the layer item.

        Args:
            event (QtGui.QMouseEvent): The triggered mouse event.
        """
        if self.__name.geometry().contains(event.pos()):
            self.start_editing()
            event.accept()

        else:
            self.request_attribute_editor.emit(self.__node)
            event.accept()

    def on_visible_clicked(self) -> None:
        """Toggles the visibility state of the node."""
        if not cmds.objExists(self.__node):
            _logger.error("Image plane does not exist: %s", self.__node)
            self.update_requested.emit()
            return None

        visible: bool = cmds.getAttr(f"{self.__node}.visibility")
        if cmds.getAttr(f"{self.__node}.displayMode") != 3:
            visible = False

        self.visibility_toggled.emit(self.__node, not visible)

    def update_visible_state(self) -> None:
        """Updates the eye icon based on current node visibility."""
        visible: bool = cmds.getAttr(f"{self.__node}.visibility")
        if cmds.getAttr(f"{self.__node}.displayMode") != 3:
            visible = False

        icon: str = "view/a_show.png" if visible else "view/a_hide.png"
        self.__visible.set_icon(icon)

    def update_thumbnail(self) -> None:
        """Updates the thumbnail pixmap from the image plane path."""
        filepath: str = cmds.getAttr(f"{self.__node}.imageName")
        pixmap: QtGui.QPixmap = QtGui.QPixmap(filepath)
        if not pixmap.isNull():
            self.__thumbnail.setPixmap(
                pixmap.scaled(
                    self.__thumbnail.width(),
                    self.__thumbnail.height(),
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
            )

    def start_editing(self) -> None:
        """Activates edit mode for the layer name line edit."""
        self.__name.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            False,
        )
        self.__name.setReadOnly(False)
        self.__name.setFrame(True)
        self.__name.setStyleSheet("")
        self.__name.setFocus()
        self.__name.selectAll()

    def rename_node(self) -> None:
        """Renames the target image plane in Maya."""
        self.__name.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )
        self.__name.setReadOnly(True)
        self.__name.setFrame(False)
        self.__name.setStyleSheet("background: transparent;")

        new_name: str = self.__name.text()
        if new_name and new_name != self.__node:
            try:
                old_name: str = self.__node
                self.__node = cmds.rename(self.__node, new_name)
                self.__node = self.__node.split("->")[-1]
                self.__name.setText(self.__node)
                self.name_changed.emit(old_name, new_name)

            except RuntimeError:
                self.__name.setText(self.__node)

        else:
            self.__name.setText(self.__node)


class ImagePlaneListWidget(QtWidgets.QListWidget):
    """Custom list widget with drag-and-drop support for image planes."""

    order_changed: QtCore.Signal = QtCore.Signal()
    files_dropped: QtCore.Signal = QtCore.Signal(list)
    wheel_scrolled: QtCore.Signal = QtCore.Signal(int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initializes the image plane list.

        Args:
            parent (QtWidgets.QWidget | None, optional): Parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.setDragDropMode(QtWidgets.QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.setSelectionMode(
            QtWidgets.QListWidget.SelectionMode.ExtendedSelection
        )
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Handles items entering the widget bounds during drag.

        Args:
            event (QtGui.QDragEnterEvent): The drag enter event.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        """Handles items moving within the widget bounds during drag.

        Args:
            event (QtGui.QDragMoveEvent): The drag move event.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Handles dropped items containing URLs.

        Args:
            event (QtGui.QDropEvent): The drop event.
        """
        if event.mimeData().hasUrls():
            filepaths: list[str] = [
                url.toLocalFile()
                for url in event.mimeData().urls()
                if url.isLocalFile()
            ]
            if filepaths:
                self.files_dropped.emit(filepaths)

            event.acceptProposedAction()

        else:
            super().dropEvent(event)
            QtCore.QTimer.singleShot(0, self.order_changed.emit)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """Handles mouse wheel scrolls for opacity adjustments.

        Args:
            event (QtGui.QWheelEvent): The wheel event.
        """
        delta: int = event.angleDelta().y()
        step: int = 5 if delta > 0 else -5
        self.wheel_scrolled.emit(step)
        event.accept()
        # super().wheelEvent(event)


class SubToolManager(QtWidgets.QWidget):
    """Manages secondary contextual camera tools and operations."""

    update_requested: QtCore.Signal = QtCore.Signal()

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the sub-tool manager widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): Parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flag type.
                Defaults to Widget.
        """
        super().__init__(parent)
        self.setWindowFlags(flag)
        self.setObjectName(f"SubToolManager{str(id(self))}")

        self.__camera: str = ""

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(layout)

        button: widgets.IconButton = widgets.IconButton(self)
        button.set_icon("a_move.png")
        button.setToolTip("Film Offset Tool")
        button.clicked.connect(self.film_offset_context)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon("a_zoom.png")
        button.setToolTip("Post Scale Tool")
        button.clicked.connect(self.post_scale_context)
        layout.addWidget(button)

        layout.addWidget(widgets.VerticalLine(self))

        button = widgets.IconButton(self)
        button.set_icon("a_shift_lens.png")
        button.setToolTip("Show Shift Lens")
        button.clicked.connect(self.show_shift_lens)
        layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon("a_zoom_out.png")
        button.setToolTip("Show Dolly Zoom")
        button.clicked.connect(self.show_dolly_zoom)
        layout.addWidget(button)

        layout.addStretch(True)

        button = widgets.IconButton(self)
        button.set_icon("a_update.png")
        button.setToolTip("Update window")
        button.clicked.connect(self.update_ui)
        layout.addWidget(button)

        main_layout.addStretch(True)

    def set_camera(self, camera: str) -> None:
        """Sets the active camera.

        Args:
            camera (str): Camera node name.
        """
        self.__camera = camera

    def camera(self) -> str:
        """Returns the active camera.

        Returns:
            str: Camera node name.
        """
        return self.__camera

    def show_shift_lens(self) -> None:
        """Triggers the shift lens main process."""
        shift_lens.main(camera=self.camera())

    def show_dolly_zoom(self) -> None:
        """Triggers the dolly zoom main process."""
        dolly_zoom.main(camera=self.camera())

    def update_ui(self) -> None:
        """Requests a UI refresh via signals."""
        self.update_requested.emit()

    def film_offset_context(self) -> None:
        """Activates the film offset context tool."""
        context: FilmOffsetContext = FilmOffsetContext(self.camera())
        context.set_tool()

    def post_scale_context(self) -> None:
        """Activates the post scale context tool."""
        context: PostScaleContext = PostScaleContext(self.camera())
        context.set_tool()


class CameraInfoManager(QtWidgets.QWidget):
    """Manages the UI controls for camera properties (Focal Length, Offset)."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the camera information manager widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): Parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flag type.
                Defaults to Widget.
        """
        super().__init__(parent)
        self.setWindowFlags(flag)
        self.setObjectName(f"CameraInfoManager{str(id(self))}")

        self.__camera: str = ""
        self.__model_editor: str = ""
        current_parent: str = cmds.setParent(query=True)  # type: ignore

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        main_layout.setObjectName(f"Layout{str(id(self))}")
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        layout.setObjectName(f"Layout{str(id(layout))}")
        main_layout.addLayout(layout)

        self.__dummy_window: str = cmds.window()  # type: ignore
        self.__dummy_layout: str = cmds.columnLayout()  # type: ignore

        self.__focal_length: str = cmds.attrFieldSliderGrp(
            label="Lens",
            columnWidth=[(1, 40), (2, 60)],
            adjustableColumn=0,
            parent=self.__dummy_layout,
        )  # type: ignore
        focal_length_qt: QtWidgets.QWidget | None = dcc.find_control(
            self.__focal_length,
            QtWidgets.QWidget,
        )
        if focal_length_qt:
            focal_length_qt.setMaximumWidth(100)
            self.__focal_length = focal_length_qt.objectName()
            layout.addWidget(focal_length_qt, True)

        button = widgets.IconButton(self)
        button.set_icon("a_reset.png")
        button.clicked.connect(
            partial(self.reset_value, self.__focal_length, 35)
        )
        layout.addWidget(button)

        layout.addWidget(widgets.VerticalLine(self))

        self.__offset_x: str = cmds.attrFieldSliderGrp(
            label="Film X",
            columnWidth=[(1, 40), (2, 60)],
            adjustableColumn=0,
            parent=self.__dummy_layout,
        )  # type: ignore
        offset_x_qt: QtWidgets.QWidget | None = dcc.find_control(
            self.__offset_x,
            QtWidgets.QWidget,
        )
        if offset_x_qt:
            offset_x_qt.setMaximumWidth(100)
            self.__offset_x = offset_x_qt.objectName()
            layout.addWidget(offset_x_qt, True)

        button = widgets.IconButton(self)
        button.set_icon("a_reset.png")
        button.clicked.connect(partial(self.reset_value, self.__offset_x, 0.0))
        layout.addWidget(button)

        self.__offset_y: str = cmds.attrFieldSliderGrp(
            label="Film Y",
            columnWidth=[(1, 40), (2, 60)],
            adjustableColumn=0,
            parent=self.__dummy_layout,
        )  # type: ignore
        offset_y_qt: QtWidgets.QWidget | None = dcc.find_control(
            self.__offset_y,
            QtWidgets.QWidget,
        )
        if offset_y_qt:
            offset_y_qt.setMaximumWidth(100)
            self.__offset_y = offset_y_qt.objectName()
            layout.addWidget(offset_y_qt, True)

        button = widgets.IconButton(self)
        button.set_icon("a_reset.png")
        button.clicked.connect(partial(self.reset_value, self.__offset_y, 0.0))
        layout.addWidget(button)

        layout.addWidget(widgets.VerticalLine(self))

        self.__post_scale: str = cmds.attrFieldSliderGrp(
            label="Scale",
            columnWidth=[(1, 40), (2, 60)],
            adjustableColumn=0,
            parent=self.__dummy_layout,
        )  # type: ignore
        post_scale_qt: QtWidgets.QWidget | None = dcc.find_control(
            self.__post_scale,
            QtWidgets.QWidget,
        )
        if post_scale_qt:
            post_scale_qt.setMaximumWidth(100)
            self.__post_scale = post_scale_qt.objectName()
            layout.addWidget(post_scale_qt, True)

        button = widgets.IconButton(self)
        button.set_icon("a_reset.png")
        button.clicked.connect(
            partial(self.reset_value, self.__post_scale, 1.0)
        )
        layout.addWidget(button)

        layout.addStretch(True)

        self.__curve: widgets.IconButton = widgets.IconButton(self)
        self.__curve.set_icon("a_curve.png")
        self.__curve.setCheckable(True)
        self.__curve.clicked.connect(self.set_displayed_filter)
        layout.addWidget(self.__curve)

        self.__polygon: widgets.IconButton = widgets.IconButton(self)
        self.__polygon.set_icon("a_polygon.png")
        self.__polygon.setCheckable(True)
        self.__polygon.clicked.connect(self.set_displayed_filter)
        layout.addWidget(self.__polygon)

        self.__image_plane: widgets.IconButton = widgets.IconButton(self)
        self.__image_plane.set_icon("a_image_plane.png")
        self.__image_plane.setCheckable(True)
        self.__image_plane.clicked.connect(self.set_displayed_filter)
        layout.addWidget(self.__image_plane)

        cmds.setParent(current_parent)

    def set_camera(self, camera: str) -> None:
        """Sets the target camera and updates associated UI elements.

        Args:
            camera (str): The target camera name.
        """
        self.__camera = camera
        self.update_controllers()

    def camera(self) -> str:
        """Returns the currently bound camera.

        Returns:
            str: Camera node name.
        """
        return self.__camera

    def set_model_editor(self, model_editor: str) -> None:
        """Binds the model editor to synchronize display states.

        Args:
            model_editor (str): The model editor panel name.
        """
        self.__model_editor = model_editor
        self.__curve.setChecked(
            cmds.modelEditor(self.__model_editor, query=True, nurbsCurves=True)  # type: ignore
        )
        self.__polygon.setChecked(
            cmds.modelEditor(self.__model_editor, query=True, polymeshes=True)  # type: ignore
        )
        self.__image_plane.setChecked(
            cmds.modelEditor(self.__model_editor, query=True, imagePlane=True)  # type: ignore
        )

    def set_displayed_filter(self) -> None:
        """Applies checkbox states back to the model editor."""
        cmds.modelEditor(
            self.__model_editor,
            edit=True,
            nurbsCurves=self.__curve.isChecked(),
            polymeshes=self.__polygon.isChecked(),
            imagePlane=self.__image_plane.isChecked(),
        )

    def reset_value(self, widget: str, value: float) -> None:
        """Resets the slider values for a given UI element.

        Args:
            widget (str): The Maya UI control name.
            value (float): The default value to restore.
        """
        plug: str = cmds.attrFieldSliderGrp(widget, query=True, attribute=True)  # type: ignore
        if plug:
            cmds.setAttr(plug, value)

    def update_controllers(self) -> None:
        """Updates internal mapping between sliders and node plugs."""
        plug: str = find_target_plug(
            self.camera(),
            "focalLength",
            "camera_C_ctrl",
            "focalLength",
        )
        cmds.attrFieldSliderGrp(self.__focal_length, edit=True, attribute=plug)

        plug = find_target_plug(
            self.camera(),
            "horizontalFilmOffset",
            "filmOffsetSlider_C_ctrl",
            "translateX",
        )
        cmds.attrFieldSliderGrp(self.__offset_x, edit=True, attribute=plug)

        plug = find_target_plug(
            self.camera(),
            "verticalFilmOffset",
            "filmOffsetSlider_C_ctrl",
            "translateY",
        )
        cmds.attrFieldSliderGrp(self.__offset_y, edit=True, attribute=plug)

        plug = find_target_plug(
            self.camera(),
            "postScale",
            "camera_C_ctrl",
            "postScale",
        )
        cmds.attrFieldSliderGrp(self.__post_scale, edit=True, attribute=plug)

    def cleanup(self) -> None:
        """Cleans up dummy layout and window created for slider groups."""
        cmds.deleteUI(self.__focal_length)
        cmds.deleteUI(self.__offset_x)
        cmds.deleteUI(self.__offset_y)
        cmds.deleteUI(self.__post_scale)
        cmds.deleteUI(self.__dummy_layout)
        cmds.deleteUI(self.__dummy_window)


class CameraManager(QtWidgets.QWidget):
    """Manages scene cameras and camera switching logic."""

    camera_changed: QtCore.Signal = QtCore.Signal(str)
    update_requested: QtCore.Signal = QtCore.Signal()

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the camera manager widget.

        Args:
            parent (QtWidgets.QWidget | None, optional): Parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flag type.
                Defaults to Widget.
        """
        super().__init__(parent)
        self.setWindowFlags(flag)
        self.setObjectName(f"CameraManager{str(id(self))}")

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        header_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(header_layout)

        label: QtWidgets.QLabel = QtWidgets.QLabel("Camera")
        header_layout.addWidget(label)
        header_layout.addStretch(True)

        button: widgets.IconButton = widgets.IconButton(self)
        button.set_icon("a_add.png")
        button.setToolTip("Create Camera")
        button.clicked.connect(self.create_camera)
        header_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon("a_trash.png")
        button.setToolTip("Delete Camera")
        button.clicked.connect(self.delete_camera)
        header_layout.addWidget(button)

        self.__camera_list: QtWidgets.QListWidget = QtWidgets.QListWidget(self)
        self.__camera_list.setSelectionMode(
            QtWidgets.QListWidget.SelectionMode.SingleSelection
        )
        self.__camera_list.itemSelectionChanged.connect(self.switched_camera)
        self.__camera_list.itemDoubleClicked.connect(self.show_attribute_editor)
        main_layout.addWidget(self.__camera_list)

        self.update_cameras()

    def set_camera(self, camera: str) -> None:
        """Selects a camera from the list widget.

        Args:
            camera (str): Target camera name.
        """
        items: list[QtWidgets.QListWidgetItem] = self.__camera_list.findItems(
            camera,
            QtCore.Qt.MatchFlag.MatchExactly,
        )
        if items:
            self.__camera_list.setCurrentItem(items[0])
        else:
            self.__camera_list.setCurrentRow(0)

        self.switched_camera()

    def current_camera(self) -> str:
        """Returns the currently selected camera.

        Returns:
            str: Target camera name.
        """
        items: list[QtWidgets.QListWidgetItem] = (
            self.__camera_list.selectedItems()
        )
        if items:
            return items[0].text()

        return ""

    def switched_camera(self) -> None:
        """Fires camera changed event and performs node validation."""
        current_camera: str = self.current_camera()
        if current_camera:
            if not cmds.objExists(current_camera):
                _logger.error("Camera does not exist: %s", current_camera)
                self.update_requested.emit()
                return

            self.camera_changed.emit(current_camera)

    def update_cameras(self, current_camera: str = "") -> None:
        """Repopulates the camera list from scene data.

        Args:
            current_camera (str, optional): Target camera name. Defaults to ''.
        """

        def sort_camera(camera: str) -> tuple[int, str]:
            """Sort helper for ordering default cameras to the top."""
            default_order: dict[str, str] = {
                "persp": "1",
                "top": "2",
                "front": "3",
                "side": "4",
            }
            if camera in default_order:
                return (1, default_order[camera])

            return (0, camera)

        self.__camera_list.blockSignals(True)

        if not current_camera:
            current_camera = self.current_camera()

        self.__camera_list.clear()

        cameras: list[str] = []
        camera_shapes: list[str] = cmds.ls(type="camera")
        for camera_shape in camera_shapes:
            parent: str = cmds.listRelatives(
                camera_shape, parent=True, fullPath=True
            )[0]
            parent = cmds.ls(parent)[0]
            cameras.append(parent)

        cameras.sort(key=sort_camera)
        for camera in cameras:
            item: QtWidgets.QListWidgetItem = QtWidgets.QListWidgetItem(camera)
            self.__camera_list.addItem(item)

        self.__camera_list.blockSignals(False)

        items: list[QtWidgets.QListWidgetItem] = self.__camera_list.findItems(
            current_camera,
            QtCore.Qt.MatchFlag.MatchExactly,
        )
        if items:
            self.__camera_list.setCurrentItem(items[0])
        else:
            self.__camera_list.setCurrentRow(0)

    def show_attribute_editor(
        self,
        item: QtWidgets.QListWidgetItem | None = None,
    ) -> None:
        """Opens Maya's attribute editor for the selected item.

        Args:
            item (QtWidgets.QListWidgetItem | None, optional): The target item.
                Defaults to None.
        """
        camera: str = self.current_camera()
        if item:
            camera = item.text()

        cmds.select(camera)
        mel.eval("ShowAttributeEditorOrChannelBox;")

    @dcc.undo
    def create_camera(self) -> None:
        """Creates a new default camera or an Amaterasu Rig camera."""
        camera: str = "render_cam"
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("Create Camera")
        msg_box.setText("Which type of camera would you like to create?")
        msg_box.setIcon(QtWidgets.QMessageBox.Icon.Question)

        amaterasu_camera_rig: QtWidgets.QPushButton = msg_box.addButton(
            "Camera Rig",
            QtWidgets.QMessageBox.ButtonRole.ActionRole,
        )
        default_camera: QtWidgets.QPushButton = msg_box.addButton(
            "Default Camera",
            QtWidgets.QMessageBox.ButtonRole.ActionRole,
        )
        msg_box.addButton("Cancel", QtWidgets.QMessageBox.ButtonRole.RejectRole)

        msg_box.exec_()

        if msg_box.clickedButton() == amaterasu_camera_rig:
            if cmds.objExists("render_cam"):
                QtWidgets.QMessageBox.critical(
                    self,
                    "Duplicate Camera Rig",
                    "An Amaterasu camera rig already exists in the scene.",
                )
                return

            camera = camera_rig.main()
            camera = cmds.ls(camera)[0]

        elif msg_box.clickedButton() == default_camera:
            created_camera: str = cmds.camera(
                name=camera,
                centerOfInterest=5,
                focalLength=35,
                lensSqueezeRatio=1,
                cameraScale=1,
                horizontalFilmAperture=1.41732,
                horizontalFilmOffset=0,
                verticalFilmAperture=0.94488,
                verticalFilmOffset=0,
                filmFit="horizontal",
                overscan=1.3,
                motionBlur=False,
                shutterAngle=144,
                nearClipPlane=0.1,
                farClipPlane=10000,
                orthographic=False,
                orthographicWidth=30,
                panZoomEnabled=False,
                horizontalPan=0,
                verticalPan=0,
                zoom=1,
                displayResolution=True,
            )  # type: ignore
            camera = cmds.rename(created_camera[0], camera)
            cmds.setAttr(f"{camera}.displayGateMaskOpacity", 0.9)
            cmds.setAttr(
                f"{camera}.displayGateMaskColor", 0, 0, 0, type="double3"
            )
            cmds.setAttr(f"{camera}.locatorScale", 10)

        else:
            return

        cmds.select(clear=True)
        item: QtWidgets.QListWidgetItem = QtWidgets.QListWidgetItem(camera)
        self.__camera_list.addItem(item)
        self.__camera_list.setCurrentItem(item)
        self.update_cameras()

    @dcc.undo
    def delete_camera(self) -> None:
        """Deletes the actively selected camera (excluding default ones)."""
        camera: str = self.current_camera()
        if camera in ["persp", "top", "front", "side"]:
            return

        full_path: str = cmds.ls(camera, long=True)[0]
        parts: list[str] = full_path.split("|")
        if len(parts) > 2:
            cmds.delete(parts[1])
        else:
            cmds.delete(camera)

        self.update_cameras()
        items: list[QtWidgets.QListWidgetItem] = self.__camera_list.findItems(
            "persp",
            QtCore.Qt.MatchFlag.MatchExactly,
        )
        if items:
            self.__camera_list.setCurrentItem(items[0])
        else:
            self.__camera_list.setCurrentRow(0)


class ImagePlaneManager(QtWidgets.QWidget):
    """Manages creation, deletion, and property updates for image planes."""

    update_requested: QtCore.Signal = QtCore.Signal()

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the Image Plane Manager.

        Args:
            parent (QtWidgets.QWidget | None, optional): Parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Window flag type.
                Defaults to Widget.
        """
        super().__init__(parent)
        self.setWindowFlags(flag)
        self.setObjectName(f"CameraManager{str(id(self))}")

        self.__camera: str = ""

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        header_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(header_layout)

        label: QtWidgets.QLabel = QtWidgets.QLabel("Image Plane")
        header_layout.addWidget(label)
        header_layout.addStretch(True)

        button: widgets.IconButton = widgets.IconButton(self)
        button.set_icon("a_add.png")
        button.setToolTip("Create Image Plane")
        button.clicked.connect(self.import_images)
        header_layout.addWidget(button)

        button = widgets.IconButton(self)
        button.set_icon("a_trash.png")
        button.setToolTip("Delete Image Plane")
        button.clicked.connect(self.delete_image_planes)
        header_layout.addWidget(button)

        slider_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        slider_layout.setContentsMargins(30, 2, 2, 2)
        main_layout.addLayout(slider_layout)

        label = QtWidgets.QLabel("Opacity :", self)
        slider_layout.addWidget(label)

        self.__slider: widgets.DragSlider = widgets.DragSlider(
            self, auto_reset=False
        )
        self.__slider.setRange(0, 100)
        self.__slider.setValue(100)
        self.__slider.setEnabled(False)
        self.__slider.valueChanged.connect(self.on_slider_changed)
        slider_layout.addWidget(self.__slider)

        self.__image_list: ImagePlaneListWidget = ImagePlaneListWidget(self)
        self.__image_list.itemSelectionChanged.connect(
            self.on_selection_changed
        )
        self.__image_list.order_changed.connect(self.rebuild_after_drop)
        self.__image_list.files_dropped.connect(self.create_image_planes)
        self.__image_list.wheel_scrolled.connect(self.on_wheel_scrolled)
        self.__image_list.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.__image_list.customContextMenuRequested.connect(
            self.show_context_menu
        )
        main_layout.addWidget(self.__image_list)

        self.__delete_act = QtGui.QAction("Delete", self)
        self.__delete_act.setShortcut(QtGui.QKeySequence("Delete"))
        self.__delete_act.setShortcutContext(
            QtCore.Qt.ShortcutContext.WidgetShortcut
        )
        self.__delete_act.triggered.connect(self.delete_image_planes)
        self.__image_list.addAction(self.__delete_act)

        self.__ae_act = QtGui.QAction("Attribute Editor ...", self)
        self.__ae_act.setShortcut(QtGui.QKeySequence("Ctrl+A"))
        self.__ae_act.setShortcutContext(
            QtCore.Qt.ShortcutContext.WidgetShortcut
        )
        self.__ae_act.triggered.connect(self.show_attribute_editor)
        self.__image_list.addAction(self.__ae_act)

    def show_context_menu(self, pos: QtCore.QPoint) -> None:
        """Constructs and displays the contextual menu for the image list.

        Args:
            pos (QtCore.QPoint): Location coordinates for the menu.
        """
        items: list[QtWidgets.QListWidgetItem] = (
            self.__image_list.selectedItems()
        )
        if not items:
            return

        nodes: list[str] = []
        for item in items:
            widget: LayerItemWidget = self.__image_list.itemWidget(item)  # type: ignore
            if widget:
                nodes.append(item.data(QtCore.Qt.ItemDataRole.UserRole))

        if not nodes:
            return

        node: str = nodes[0]
        current_state: bool = cmds.getAttr(f"{node}.useFrameExtension")

        menu = QtWidgets.QMenu(self)

        action: QtGui.QAction = QtGui.QAction("Use Image Sequence", self)
        action.setCheckable(True)
        action.setChecked(current_state)
        action.toggled.connect(self.set_use_image_sequence)
        menu.addAction(action)

        action = QtGui.QAction("Reload Image", self)
        action.triggered.connect(self.reload_image_planes)
        menu.addAction(action)

        menu.addSeparator()

        action = QtGui.QAction("Create Image Plane ...", self)
        action.triggered.connect(self.import_images)
        menu.addAction(action)
        menu.addAction(self.__delete_act)

        menu.addSeparator()

        action = QtGui.QAction("Reveal in Explorer", self)
        action.triggered.connect(self.open_file_location)
        menu.addAction(action)
        menu.addAction(self.__ae_act)

        menu.exec_(self.__image_list.mapToGlobal(pos))

    def set_camera(self, camera: str) -> None:
        """Sets the active camera.

        Args:
            camera (str): Camera node name.
        """
        self.__camera = camera
        self.update_image_planes()

    def camera(self) -> str:
        """Returns the active camera name.

        Returns:
            str: Camera node name.
        """
        return self.__camera

    def current_items(self) -> list[str]:
        """Returns nodes linked to currently selected list items.

        Returns:
            list[str]: Node names of the selected image planes.
        """
        items: list[QtWidgets.QListWidgetItem] = (
            self.__image_list.selectedItems()
        )
        return [item.data(QtCore.Qt.ItemDataRole.UserRole) for item in items]

    @dcc.undo
    def on_slider_changed(self, value: int) -> None:
        """Applies slider value to image plane opacity.

        Args:
            value (int): The updated slider value.
        """
        nodes: list[str] = self.current_items()
        for node in nodes:
            if not cmds.objExists(node):
                _logger.error("Image plane does not exist: %s", node)
                self.update_image_planes()
                return

            cmds.setAttr(f"{node}.alphaGain", value / 100.0)

    def on_selection_changed(self) -> None:
        """Updates slider settings when selection changes."""
        items: list[QtWidgets.QListWidgetItem] = (
            self.__image_list.selectedItems()
        )
        if items:
            node: str = items[0].data(QtCore.Qt.ItemDataRole.UserRole)
            if not cmds.objExists(node):
                _logger.error("Image plane does not exist: %s", node)
                self.update_image_planes()
                return

            alpha: float = cmds.getAttr(f"{node}.alphaGain")
            self.__slider.setEnabled(True)
            self.__slider.blockSignals(True)
            self.__slider.setValue(int(alpha * 100))
            self.__slider.blockSignals(False)

        else:
            self.__slider.setEnabled(False)

    @dcc.undo
    def on_wheel_scrolled(self, step: int) -> None:
        """Adjusts slider based on scroll step.

        Args:
            step (int): Positive or negative step offset.
        """
        if self.__slider.isEnabled():
            new_value: int = max(0, min(100, self.__slider.value() + step))
            self.__slider.setValue(new_value)

    @dcc.undo
    def rebuild_after_drop(self) -> None:
        """Re-evaluates image depth when item order changes."""
        nodes: list[str] = []
        for i in range(self.__image_list.count()):
            item: QtWidgets.QListWidgetItem = self.__image_list.item(i)
            nodes.append(item.data(QtCore.Qt.ItemDataRole.UserRole))

        if not cmds.objExists(self.camera()):
            self.update_image_planes()
            return

        base_depth: float = cmds.getAttr(f"{self.camera()}.nearClipPlane")
        for i, node in enumerate(nodes):
            if not cmds.objExists(node):
                _logger.error("Image plane does not exist: %s", node)
                self.update_image_planes()
                return

            cmds.setAttr(
                f"{node}.depth",
                base_depth + (i + 1) * base_depth / 10.0,
            )

        self.update_image_planes()

    @dcc.undo
    def on_visibility_toggled(self, trigger_node: str, new_vis: bool) -> None:
        """Toggles visibility based on user input.

        Args:
            trigger_node (str): The node whose visibility was toggled.
            new_vis (bool): Expected boolean state of the target plane.
        """
        selected_items: list[QtWidgets.QListWidgetItem] = (
            self.__image_list.selectedItems()
        )
        selected_nodes: list[str] = [
            item.data(QtCore.Qt.ItemDataRole.UserRole)
            for item in selected_items
        ]
        selected_nodes.append(trigger_node)
        for node in selected_nodes:
            cmds.setAttr(f"{node}.visibility", new_vis)
            cmds.setAttr(f"{node}.displayMode", 3 if new_vis else 0)

        for i in range(self.__image_list.count()):
            widget: LayerItemWidget = self.__image_list.itemWidget(
                self.__image_list.item(i)
            )  # type: ignore
            if widget:
                widget.update_visible_state()

    def on_layer_name_changed(self, old_name: str, new_name: str) -> None:
        """Synchronizes node name changes back to UI data role.

        Args:
            old_name (str): Original data entry.
            new_name (str): New data entry.
        """
        for i in range(self.__image_list.count()):
            item: QtWidgets.QListWidgetItem = self.__image_list.item(i)
            if item.data(QtCore.Qt.ItemDataRole.UserRole) == old_name:
                item.setData(QtCore.Qt.ItemDataRole.UserRole, new_name)
                break

    def update_image_planes(self) -> None:
        """Synchronizes the list view with available scene image planes."""
        selected_nodes: list[str] = [
            item.data(QtCore.Qt.ItemDataRole.UserRole)
            for item in self.__image_list.selectedItems()
        ]
        self.__image_list.clear()

        target_cam: str = self.camera()
        image_planes: list[str] = []

        if target_cam:
            if not cmds.objExists(self.camera()):
                _logger.error("Camera does not exist: %s", self.camera())
                self.update_requested.emit()
                return

            cam_shapes: list[str] = (
                cmds.listRelatives(target_cam, shapes=True, type="camera") or []
            )
            if cam_shapes:
                image_planes = (
                    cmds.listConnections(
                        f"{cam_shapes[0]}.imagePlane", type="imagePlane"
                    )
                    or []
                )

        image_planes.sort(key=lambda node: cmds.getAttr(f"{node}.depth"))
        for image_plane in image_planes:
            node: str = image_plane.split("->")[-1]

            item = QtWidgets.QListWidgetItem(self.__image_list)
            item.setSizeHint(QtCore.QSize(0, 35))
            item.setData(QtCore.Qt.ItemDataRole.UserRole, node)

            row_widget = LayerItemWidget(node)
            row_widget.visibility_toggled.connect(self.on_visibility_toggled)
            row_widget.name_changed.connect(self.on_layer_name_changed)
            row_widget.update_requested.connect(self.update_image_planes)
            row_widget.request_attribute_editor.connect(
                self.show_attribute_editor
            )
            self.__image_list.setItemWidget(item, row_widget)

            if image_plane in selected_nodes:
                item.setSelected(True)

    @dcc.undo
    def create_image_plane(self, filepath: str) -> None:
        """Instantiates an image plane from an input path.

        Args:
            filepath (str): Source path of the image.
        """
        camera: str = self.camera()
        width: float = cmds.optionVar(query="freeImageWidth")  # type: ignore
        height: float = cmds.optionVar(query="freeImageHeight")  # type: ignore
        maintain_ratio: bool = cmds.optionVar(query="freeImageMR")  # type: ignore

        if not cmds.objExists(self.camera()):
            self.update_image_planes()
            return

        image_plane: list[str] = cmds.imagePlane(
            camera=camera,
            width=width,
            height=height,
            maintainRatio=maintain_ratio,
        )  # type: ignore
        cmds.imagePlane(image_plane[1], edit=True, lookThrough=camera)
        cmds.setAttr(f"{image_plane[1]}.displayOnlyIfCurrent", 1)
        cmds.setAttr(f"{image_plane[1]}.type", 0)
        cmds.setAttr(f"{image_plane[1]}.imageName", filepath, type="string")

        pixmap_size: list[int] = cmds.imagePlane(
            image_plane[1],
            query=True,
            imageSize=True,
        )  # type: ignore
        cmds.imagePlane(image_plane[1], edit=True, width=pixmap_size[0] / 100.0)
        cmds.imagePlane(
            image_plane[1],
            edit=True,
            height=pixmap_size[1] / 100.0,
        )
        cmds.connectAttr(f"{camera}.filmOffset", f"{image_plane[1]}.offset")

        render_width: int = cmds.getAttr("defaultResolution.width")
        render_height: int = cmds.getAttr("defaultResolution.height")
        device_aspect: float = float(pixmap_size[0]) / float(pixmap_size[1])
        if pixmap_size[0] != render_width or pixmap_size[1] != render_height:
            result = QtWidgets.QMessageBox.question(
                self,
                "Question",
                (
                    "Image size and render image size do not match.\n"
                    + "Do you want to set the render image size?\n\n"
                    + f"{render_width} x {render_height} -> "
                    + f"{pixmap_size[0]} x {pixmap_size[1]}"
                ),
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No,
            )

            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                cmds.setAttr("defaultResolution.width", pixmap_size[0])
                cmds.setAttr("defaultResolution.height", pixmap_size[1])
                cmds.setAttr(
                    "defaultResolution.deviceAspectRatio", device_aspect
                )
                cmds.setAttr("defaultResolution.pixelAspect", 1.00)

        camera_x: float = cmds.getAttr(f"{camera}.horizontalFilmAperture")
        camera_y: float = cmds.getAttr(f"{camera}.verticalFilmAperture")
        fit_type: int = cmds.getAttr(f"{camera}.filmFit")
        camera_aspect: float = camera_x / camera_y

        if fit_type == 0:  # FILL
            if device_aspect < camera_aspect:
                cmds.setAttr(
                    f"{image_plane[1]}.sizeX",
                    camera_y * device_aspect,
                )
                cmds.setAttr(f"{image_plane[1]}.sizeY", camera_y)
            else:
                cmds.setAttr(f"{image_plane[1]}.sizeX", camera_x)
                cmds.setAttr(
                    f"{image_plane[1]}.sizeY",
                    camera_x * device_aspect,
                )

        elif fit_type == 1:  # Horizontal
            cmds.setAttr(f"{image_plane[1]}.sizeX", camera_x)
            cmds.setAttr(f"{image_plane[1]}.sizeY", camera_x / device_aspect)

        elif fit_type == 2:  # Vertical
            cmds.setAttr(f"{image_plane[1]}.sizeX", camera_y)
            cmds.setAttr(f"{image_plane[1]}.sizeY", camera_y * device_aspect)

        elif fit_type == 3:  # Overscan
            if device_aspect < camera_aspect:
                cmds.setAttr(f"{image_plane[1]}.sizeX", camera_x)
                cmds.setAttr(
                    f"{image_plane[1]}.sizeY",
                    camera_x / device_aspect,
                )
            else:
                cmds.setAttr(
                    f"{image_plane[1]}.sizeX",
                    camera_y * device_aspect,
                )
                cmds.setAttr(f"{image_plane[1]}.sizeY", camera_y)

        self.update_image_planes()
        self.rebuild_after_drop()

    @dcc.undo
    def create_image_planes(self, filepaths: list[str]) -> None:
        """Batch instantiates multiple image planes.

        Args:
            filepaths (list[str]): List of absolute image paths.
        """
        for filepath in filepaths:
            self.create_image_plane(filepath)

    @dcc.undo
    def import_images(self) -> None:
        """Opens a file dialog to import images manually."""
        workspace: str = cmds.workspace(query=True, fullName=True)  # type: ignore
        start_dir: str = os.path.join(workspace, "sourceImages")
        if not os.path.exists(start_dir):
            start_dir = workspace

        filepaths: list[str] = []
        filepaths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Import images",
            start_dir,
            "Images (*.png *.jpg *.jpeg *.tif *.tiff *.tga *.bmp)",
        )
        if filepaths:
            self.create_image_planes(filepaths)

    @dcc.undo
    def delete_image_planes(self) -> None:
        """Deletes the selected image planes from the scene and view."""
        items: list[QtWidgets.QListWidgetItem] = (
            self.__image_list.selectedItems()
        )
        if not items:
            return

        delete_nodes: list[str] = [
            item.data(QtCore.Qt.ItemDataRole.UserRole) for item in items
        ]
        cmds.delete(*delete_nodes)
        self.update_image_planes()

    def show_attribute_editor(self, node: str = "") -> None:
        """Displays Maya's Attribute Editor for target image planes.

        Args:
            node (str, optional): Overriding node string. Defaults to ''.
        """
        nodes: list[str] = [node]
        if not node:
            items: list[QtWidgets.QListWidgetItem] = (
                self.__image_list.selectedItems()
            )
            if not items:
                return

            nodes = [
                item.data(QtCore.Qt.ItemDataRole.UserRole) for item in items
            ]

        cmds.select(*nodes)
        mel.eval("ShowAttributeEditorOrChannelBox;")

    @dcc.undo
    def set_use_image_sequence(self, state: bool) -> None:
        """Toggles the 'useFrameExtension' state for selected items.

        Args:
            state (bool): Extension flag requirement.
        """
        items: list[QtWidgets.QListWidgetItem] = (
            self.__image_list.selectedItems()
        )
        if not items:
            return

        nodes: list[str] = [
            item.data(QtCore.Qt.ItemDataRole.UserRole) for item in items
        ]
        for node in nodes:
            cmds.setAttr(f"{node}.useFrameExtension", state)

    def reload_image_planes(self) -> None:
        """Forces Maya to refresh image file paths from disk."""
        items: list[QtWidgets.QListWidgetItem] = (
            self.__image_list.selectedItems()
        )
        if not items:
            return

        nodes: list[str] = [
            item.data(QtCore.Qt.ItemDataRole.UserRole) for item in items
        ]
        for node in nodes:
            path: str = cmds.getAttr(f"{node}.imageName")
            cmds.setAttr(f"{node}.imageName", path, type="string")

    def open_file_location(self) -> None:
        """Reveals the directory path mapped to the currently selected file."""
        items: list[QtWidgets.QListWidgetItem] = (
            self.__image_list.selectedItems()
        )
        if not items:
            return

        nodes: list[str] = [
            item.data(QtCore.Qt.ItemDataRole.UserRole) for item in items
        ]
        for node in nodes:
            file_path: str = cmds.getAttr(f"{node}.imageName")
            if not file_path:
                continue

            dir_path: str = os.path.dirname(file_path)
            if not os.path.exists(dir_path):
                _logger.error("Directory does not exist: %s", dir_path)
                continue

            result: utils.Result = system.open_directory(dir_path)
            if result.status() != utils.ResultStatus.SUCCESS:
                result.log(_logger)


class MainWindow(framework.WorkspaceControlWindow):
    """Main window coordinating all Rotoscoping elements."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Window,
        unique_id: str = "",
    ) -> None:
        """Initializes the main Rotoscope window interface.

        Args:
            parent (QtWidgets.QWidget | None, optional): Parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): Main window flag type.
                Defaults to Window.
            unique_id (str, optional): Unique ID. Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(1280, 720)

        self.__main_panel: str = ""
        self.__left_panel: str = ""
        self.__right_panel: str = ""
        self.__model_panel_name: str = ""
        self.__model_editor_name: str = ""

        self.__subtool_mgr: SubToolManager = SubToolManager(self)
        self.__camera_info_mgr: CameraInfoManager = CameraInfoManager(self)
        self.__camera_mgr: CameraManager = CameraManager(self)
        self.__image_plane_mgr: ImagePlaneManager = ImagePlaneManager(self)

        self.__toggle_shortcut: QtGui.QShortcut = QtGui.QShortcut(
            QtGui.QKeySequence("Ctrl+Space"),
            self.__subtool_mgr,
        )
        self.__toggle_shortcut.setContext(
            QtCore.Qt.ShortcutContext.WindowShortcut
        )
        self.__main_panel_size: list[tuple[int, int, int]] = []
        self.__left_panel_size: list[tuple[int, int, int]] = []
        self.__is_toggle: bool = False

    def show(self) -> None:
        """Initializes and integrates the tool's workspace layout into Maya's UI."""
        self.initialize_workspace()
        parent_path: str | None = self.workspace_window()
        if not parent_path:
            _logger.error("Failed to get workspace window.")
            return

        # Maya's Panel Layout --------------------------------------------------
        self.__main_panel = cmds.paneLayout(
            configuration="vertical2",
            parent=parent_path,
        )  # type: ignore

        self.__left_panel = cmds.paneLayout(
            configuration="horizontal2",
            parent=self.__main_panel,
        )  # type: ignore

        self.__right_panel = cmds.paneLayout(
            configuration="horizontal3",
            parent=self.__main_panel,
        )  # type: ignore

        # ----------------------------------------------------------------------
        # Model Panel
        self.__model_panel_name = cmds.modelPanel(
            unParent=True,
            menuBarVisible=True,
        )  # type: ignore
        cmds.modelPanel(
            self.__model_panel_name,
            edit=True,
            parent=self.__left_panel,
        )
        self.__model_editor_name = cmds.modelPanel(
            self.__model_panel_name,
            query=True,
            modelEditor=True,
        )  # type: ignore

        # ----------------------------------------------------------------------
        # Event
        self.__camera_mgr.camera_changed.connect(self.__subtool_mgr.set_camera)
        self.__camera_mgr.camera_changed.connect(
            self.__camera_info_mgr.set_camera
        )
        self.__camera_mgr.camera_changed.connect(
            self.__image_plane_mgr.set_camera
        )
        self.__camera_mgr.camera_changed.connect(self.set_camera)
        self.__camera_mgr.update_requested.connect(self.update_ui)
        self.__subtool_mgr.update_requested.connect(self.update_ui)
        self.__image_plane_mgr.update_requested.connect(self.update_ui)
        self.__toggle_shortcut.activated.connect(self.toggle_ui_visibility)

        # ----------------------------------------------------------------------
        # Move PySide Widget to Maya's UI
        dcc.add_widget_to_maya(self.__camera_info_mgr, self.__left_panel)
        dcc.add_widget_to_maya(self.__subtool_mgr, self.__right_panel)
        dcc.add_widget_to_maya(self.__camera_mgr, self.__right_panel)
        dcc.add_widget_to_maya(self.__image_plane_mgr, self.__right_panel)

        # ----------------------------------------------------------------------
        self.load_settings()
        self.update_ui()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Cleans up widgets and applies window saving state on close.

        Args:
            event (QtGui.QCloseEvent): Closing event.
        """
        self.save_settings()
        self.__camera_info_mgr.cleanup()
        super().closeEvent(event)

    def load_settings(self) -> None:
        """Retrieves and applies the tool settings bound on the instance."""
        settings: Settings = Settings.instance(__name__, True)
        self.restoreGeometry(utils.ascii_to_qt(settings.window_geo.value()))
        cmds.paneLayout(
            self.__main_panel,
            edit=True,
            paneSize=settings.main_panel.value(),
        )
        cmds.paneLayout(
            self.__left_panel,
            edit=True,
            paneSize=settings.left_panel.value(),
        )
        cmds.paneLayout(
            self.__right_panel,
            edit=True,
            paneSize=settings.right_panel.value(),
        )
        settings.write_from_model_panel(self.__model_panel_name)

    def save_settings(self) -> None:
        """Flushes the tool's current internal properties to generic settings."""
        settings: Settings = Settings.instance(__name__, True)
        settings.window_geo.set_value(utils.qt_to_ascii(self.saveGeometry()))
        settings.main_panel.set_value(
            self.convert_panel_size(self.__main_panel)
        )
        settings.left_panel.set_value(
            self.convert_panel_size(self.__left_panel)
        )
        settings.right_panel.set_value(
            self.convert_panel_size(self.__right_panel)
        )
        settings.read_from_model_panel(self.__model_panel_name)
        settings.write()

    def convert_panel_size(self, panel: str) -> list[tuple[int, int, int]]:
        """Converts raw Maya pane layout variables into strict tuples.

        Args:
            panel (str): The target Maya UI panel format.

        Returns:
            list[tuple[int, int, int]]: Configured sizes format.
        """
        data: list[int] = cmds.paneLayout(panel, query=True, paneSize=True)  # type: ignore
        return [
            (index, data[i], data[i + 1])
            for index, i in enumerate(range(0, len(data), 2), 1)
        ]

    def set_camera(self, camera: str) -> None:
        """Applies internal camera bindings directly into Maya models.

        Args:
            camera (str): Name of the target camera.
        """
        cmds.modelPanel(
            self.__model_panel_name,
            edit=True,
            camera=camera,
        )

    def current_camera(self) -> str:
        """Returns string representations of the bound Maya model panel context.

        Returns:
            str: Currently embedded camera node name.
        """
        camera: str = cmds.modelPanel(
            self.__model_panel_name, query=True, camera=True
        )  # type: ignore
        return camera

    def toggle_ui_visibility(self) -> None:
        """Adjusts the layout widths temporarily for focused view modes."""
        if not self.__is_toggle:
            self.__main_panel_size = self.convert_panel_size(self.__main_panel)
            self.__left_panel_size = self.convert_panel_size(self.__left_panel)
            cmds.paneLayout(
                self.__main_panel,
                edit=True,
                paneSize=[(1, 100, 100), (2, 0, 100)],
            )
            cmds.paneLayout(
                self.__left_panel,
                edit=True,
                paneSize=[(1, 100, 100), (2, 100, 0)],
            )

        else:
            # Prevent saving width as 0 when the UI is collapsed.
            if not self.__main_panel_size or self.__main_panel_size[1][1] == 0:
                self.__main_panel_size = DEFAULT_MAIN_PANEL_SIZE

            if not self.__left_panel_size or self.__left_panel_size[1][2] == 0:
                self.__left_panel_size = DEFAULT_LEFT_PANEL_SIZE

            cmds.paneLayout(
                self.__main_panel,
                edit=True,
                paneSize=self.__main_panel_size,
            )
            cmds.paneLayout(
                self.__left_panel,
                edit=True,
                paneSize=self.__left_panel_size,
            )

        self.__is_toggle = not self.__is_toggle

    def update_ui(self) -> None:
        """Resynchronizes generic components dynamically."""
        self.__camera_mgr.update_cameras(self.current_camera())
        self.__camera_info_mgr.set_model_editor(self.__model_editor_name)


def find_target_plug(
    start_node: str,
    attr_name: str,
    target_name: str,
    target_attr: str,
) -> str:
    """Traverses connections to find an origin plug associated with inputs.

    Args:
        start_node (str): Starting evaluation node segment.
        attr_name (str): Target generic attribute name property.
        target_name (str): The desired search substring context.
        target_attr (str): Filter matching element on matched connections.

    Returns:
        str: Fully formatted node attribute connection.
    """
    start_plug: str = f"{start_node}.{attr_name}"
    connections: list[str] = (
        cmds.listConnections(
            start_plug, source=True, destination=False, plugs=True
        )
        or []
    )
    if not connections:
        return start_plug

    plugs_to_check: list[str] = list(connections)
    visited_plugs: set[str] = set()
    while plugs_to_check:
        current_plug: str = plugs_to_check.pop(0)
        if current_plug in visited_plugs:
            continue

        visited_plugs.add(current_plug)

        node_name: str = current_plug.split(".")[0]
        if target_name in node_name:
            return f"{node_name}.{target_attr}"

        upstreams: list[str] = (
            cmds.listConnections(
                node_name, source=True, destination=False, plugs=True
            )
            or []
        )
        plugs_to_check.extend(upstreams)

    return start_plug


def main(unique_id: str = "") -> None:
    """Launches window.

    Args:
        unique_id (str, optional): A unique ID identifier. Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
