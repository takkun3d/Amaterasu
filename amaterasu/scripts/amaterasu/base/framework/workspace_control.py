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
"""Maya workspace control module for Amaterasu.

This module provides the core UI foundation for all Amaterasu tools by
wrapping PySide widgets into Maya's native workspace controls. It ensures
that tools can be docked, floated, and seamlessly integrated into Maya's
UI layout while maintaining their state across sessions and workspace changes.

Attributes:
    WORKSPACE_WIDGETS (dict[str, QtWidgets.QWidget]): A global registry mapping
        workspace control names to their corresponding WorkspaceControlWindow instances.
        Used for tracking, managing, and safely closing active tool windows.
"""
from __future__ import annotations
import abc
import sys
import types
import uuid
from maya import OpenMayaUI, cmds
from amaterasu.base.qt import QtCore, QtWidgets


WORKSPACE_WIDGETS: dict[str, QtWidgets.QWidget] = {}


class QWidgetMeta(type(QtWidgets.QWidget)):  # type: ignore
    """Metaclass for PySide QWidget.

    This acts as a base metaclass to resolve conflicts when multiple
    inheritance involves both a Qt class and a standard Python metaclass.

    Reference:
        https://stackoverflow.com/questions/66591752/metaclass-conflict-when-trying-to-create-a-python-abstract-class-that-also-subcl
    """


class QWidgetABCMeta(QWidgetMeta, abc.ABCMeta):
    """Metaclass resolving conflicts between QWidget and abc.ABCMeta.

    This metaclass allows a class to inherit from both a PySide QWidget
    and Python's abstract base class (`abc.ABC`), preventing the
    'metaclass conflict' error.
    """


class WorkspaceControlWindow(QtWidgets.QWidget):
    """Initializes the WorkspaceControlWindow.

    Args:
        parent (QtWidgets.QWidget | None, optional): The parent widget.
            Defaults to None.
        flag (QtCore.Qt.WindowType, optional): The Qt window flags.
            Defaults to Widget.
        unique_id (str, optional): A unique identifier for the widget.
            If not provided,
            a random UUID will be generated automatically. Defaults to ''.
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        unique_id: str = "",
    ) -> None:
        """Initializes the BaseToolWidget.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The Qt window flags.
                Defaults to Widget.
            unique_id (str, optional): A unique identifier for the widget.
                If not provided,
                a random UUID will be generated automatically. Defaults to ''.
        """
        super(WorkspaceControlWindow, self).__init__(parent)
        self.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_DontCreateNativeAncestors
        )
        if flag:
            self.setWindowFlags(flag)

        if unique_id:
            self.setObjectName(unique_id)

        else:
            module_name: str = self.__module__
            class_name: str = self.__class__.__name__
            uuid4: str = uuid.uuid4().hex
            self.setObjectName(f"{module_name}_{class_name}_{uuid4}")

        self.__workspace_name: str = f"{self.objectName()}WorkspaceControl"
        self.__workspace_ptr: int | None = None

    def show(self) -> None:
        """Shows the widget within a Maya workspace control.

        This overrides the standard QWidget.show() to initialize the Maya
        workspace and attach the PySide widget directly to Maya's internal
        layout.
        """
        self.initialize_workspace()

        parent_ptr: int | None = self.workspace_pointer()
        self_ptr: int = int(OpenMayaUI.MQtUtil.findControl(self.objectName()))
        OpenMayaUI.MQtUtil.addWidgetToMayaLayout(self_ptr, parent_ptr)
        QtWidgets.QWidget.setVisible(self, True)

    def close(self) -> bool:
        """Closes the widget and deletes its associated Maya workspace control.

        Returns:
            bool: True if the workspace control was successfully deleted and
                the widget was closed, False otherwise.
        """
        parent: QtCore.QObject = self.parent()
        if parent:
            workspace: str = parent.objectName()
            if cmds.workspaceControl(workspace, query=True, exists=True):
                cmds.deleteUI(workspace)
                if workspace in WORKSPACE_WIDGETS:
                    del WORKSPACE_WIDGETS[workspace]
                return True

        return QtWidgets.QWidget.close(self)

    def workspace_name(self) -> str:
        """Gets the name of the Maya workspace control.

        Returns:
            str: The unique name of the workspace control.
        """
        return self.__workspace_name

    def workspace_pointer(self) -> int | None:
        """Gets the memory pointer to the Maya workspace control.

        Returns:
            int | None: The memory address (pointer) of the workspace,
                or None if the workspace has not been initialized.
        """
        return self.__workspace_ptr

    def workspace_window(self) -> str | None:
        """Gets the full UI path name of the Maya workspace window.

        Returns:
            str | None: The full UI path string, or None if the workspace
                pointer is invalid.
        """
        ptr: int | None = self.workspace_pointer()
        if ptr is None:
            return None

        name: str = OpenMayaUI.MQtUtil.fullName(self.workspace_pointer())
        return name

    def initialize_workspace(self) -> bool:
        """Initializes the Maya workspace control for this widget.

        If the workspace control does not already exist, it creates a new one
        with the appropriate settings (dockable, floating, size properties).

        Returns:
            bool: True if a new workspace was created,
                False if it already existed.
        """
        result: bool = False
        workspace: str = self.workspace_name()
        if not cmds.workspaceControl(workspace, query=True, exists=True):
            workspace = cmds.workspaceControl(
                workspace,
                label=self.windowTitle(),
                retain=False,
                loadImmediately=True,
                floating=True,
                initialWidth=self.size().width(),
                widthProperty="free",
                initialHeight=self.size().height(),
                heightProperty="free",
                requiredPlugin=[],
                requiredControl=[],
            )  # type: ignore

            cmds.workspaceControl(
                workspace,
                edit=True,
                uiScript=self.ui_script_command(),  # type: ignore
                closeCommand=self.close_command(),  # type: ignore
            )

            self.__workspace_name = workspace
            result = True

        else:
            # Update command
            cmds.workspaceControl(
                workspace,
                edit=True,
                uiScript=self.ui_script_command(),  # type: ignore
                closeCommand=self.close_command(),  # type: ignore
            )

        self.__workspace_ptr = int(OpenMayaUI.MQtUtil.getCurrentParent())
        WORKSPACE_WIDGETS[self.workspace_name()] = self
        return result

    def ui_script_command(self) -> str:
        """Generates the Python script command to rebuild the UI.

        This command is stored in Maya's workspace control to automatically
        restore the tool when the user switches workspaces or restarts Maya.

        Returns:
            str: The Python execution string to launch the tool.
        """
        entry_func: str = "main"
        module: types.ModuleType | None = sys.modules.get(self.__module__)
        if module and hasattr(module, "option"):
            entry_func = "option"

        command: str = (
            f"import {self.__module__};"
            f"{self.__module__}.{entry_func}(\"{self.objectName()}\")"
        )
        return command

    def close_command(self) -> str:
        """Generates the Python script command to close the tool.

        Returns:
            str: The Python execution string for closing the workspace control.
        """
        entry_func: str = "WorkspaceControlWindow.close_workspace"
        command: str = (
            f"import {__name__};"
            f"{__name__}.{entry_func}(\"{self.workspace_name()}\")"
        )
        return command

    @staticmethod
    def close_workspace(workspace: str) -> None:
        """Closes a specific workspace control by its name.

        Args:
            workspace (str): The name of the workspace control to close.
        """
        if workspace in WORKSPACE_WIDGETS:
            WORKSPACE_WIDGETS[workspace].close()
