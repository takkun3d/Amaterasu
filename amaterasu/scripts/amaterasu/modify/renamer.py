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
"""A powerful, artist-friendly batch renaming tool.

Built for creators who want to keep their Outliner perfectly organized
without the headache of manual renaming. Whether you are prepping a massive
environment, finalizing a complex character rig, or just cleaning up after
a long modeling session, Renamer streamlines your workflow so you can focus
on what matters: creating.
"""

from __future__ import annotations
from typing import Any
import re
import json
from maya import cmds
from maya.api import OpenMaya
from maya.app.renderSetup.model import utils as rs_utils
from maya.app.renderSetup.views import viewCmds
from amaterasu.base.qt import QtCore, QtWidgets, QtGui
from amaterasu.base import dcc, framework, utils, widgets

__product__: str = "Renamer"
__version__: str = "1.40"
_logger: utils.Logger = utils.get_logger(__product__)


class Settings(framework.ToolSettings):
    """Settings for the Renamer tool.

    Attributes:
        window_geo (framework.Variant[str]): Saved window geometry data.
        base_name (framework.Variant[str]): The base string for renaming.
        start_number (framework.Variant[str]): The starting number or
            character sequence.
        padding (framework.Variant[int]): Padding for numbers or characters.
        suffix (framework.Variant[str]): The suffix string.
        insert_str (framework.Variant[str]): The string to insert.
        insert_to (framework.Variant[int]): Insertion position index
            (0 for First, 1 for Last).
        find_replace_rules (framework.Variant[str]): JSON string representing
            multiple find/replace rules.
    """

    window_geo: framework.Variant[str] = framework.Variant("")
    base_name: framework.Variant[str] = framework.Variant("")
    start_number: framework.Variant[str] = framework.Variant("0")
    padding: framework.Variant[int] = framework.Variant(1)
    suffix: framework.Variant[str] = framework.Variant("")
    insert_str: framework.Variant[str] = framework.Variant("")
    insert_to: framework.Variant[int] = framework.Variant(0)
    find_replace_rules: framework.Variant[str] = framework.Variant('[["", ""]]')


class PreviewDialog(QtWidgets.QDialog):
    """Dialog to show a before/after preview of renamed nodes."""

    def __init__(
        self,
        changes: list[tuple[str, str]],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        """Initializes the preview dialog.

        Args:
            changes (list[tuple[str, str]]): A list containing tuples of
                (old_name, new_name).
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Rename Preview")
        self.resize(500, 400)

        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        tree: widgets.TreeWidget = widgets.TreeWidget(self)
        tree.setHeaderLabels(["Current Name", "New Name"])
        tree.setAlternatingRowColors(True)
        tree.setRootIsDecorated(False)
        tree.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.NoSelection
        )
        layout.addWidget(tree)

        for old_name, new_name in changes:
            item: QtWidgets.QTreeWidgetItem = QtWidgets.QTreeWidgetItem(
                [old_name, new_name]
            )
            item.setForeground(1, QtGui.QColor("#73d216"))
            tree.addTopLevelItem(item)

        tree.resizeColumnToContents(0)

        btn_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        layout.addLayout(btn_layout)
        btn_layout.addStretch()

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Apply", self)
        button.clicked.connect(self.accept)
        btn_layout.addWidget(button)

        button = QtWidgets.QPushButton("Cancel", self)
        button.clicked.connect(self.reject)
        btn_layout.addWidget(button)


class StringAndNumber(QtWidgets.QWidget):
    """String and number option tab."""

    applied = QtCore.Signal(bool)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the String and Number tab.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to Widget.
        """
        super().__init__(parent, flag)
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 0)

        form_layout: widgets.FormLayout = widgets.FormLayout()
        main_layout.addLayout(form_layout)

        self.base_name: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        form_layout.addRow(widgets.FormLabel("Base Name"), self.base_name)

        self.start_number: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self.start_number.setToolTip("Can be input string : [A-Z][a-z][0-9]")
        form_layout.addRow(widgets.FormLabel("Start"), self.start_number)

        self.padding: QtWidgets.QSpinBox = QtWidgets.QSpinBox(self)
        self.padding.setRange(1, 256)
        self.padding.setMinimumWidth(70)
        form_layout.addRow(widgets.FormLabel("Padding"), self.padding)

        self.suffix: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        form_layout.addRow(widgets.FormLabel("Suffix"), self.suffix)

        btn_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(btn_layout)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Preview", self)
        button.clicked.connect(lambda: self.applied.emit(True))
        btn_layout.addWidget(button)

        button = QtWidgets.QPushButton("Apply", self)
        button.clicked.connect(lambda: self.applied.emit(False))
        btn_layout.addWidget(button)


class InsertStringTo(QtWidgets.QWidget):
    """Insert string to fist/last option tab."""

    applied = QtCore.Signal(bool)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the Insert String tab.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to Widget.
        """
        super().__init__(parent, flag)
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 0)

        form_layout: widgets.FormLayout = widgets.FormLayout()
        main_layout.addLayout(form_layout)

        self.insert: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        form_layout.addRow(widgets.FormLabel("String"), self.insert)

        self.insert_to: QtWidgets.QComboBox = QtWidgets.QComboBox(self)
        self.insert_to.addItems(["First", "Last"])
        form_layout.addRow(widgets.FormLabel("Insert to"), self.insert_to)

        btn_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(btn_layout)

        button: QtWidgets.QPushButton = QtWidgets.QPushButton("Preview", self)
        button.clicked.connect(lambda: self.applied.emit(True))
        btn_layout.addWidget(button)

        button = QtWidgets.QPushButton("Apply", self)
        button.clicked.connect(lambda: self.applied.emit(False))
        btn_layout.addWidget(button)


class FindReplaceRuleWidget(QtWidgets.QWidget):
    """A single row widget for a find and replace rule."""

    removed = QtCore.Signal(QtWidgets.QWidget)

    def __init__(
        self,
        find_str: str = "",
        replace_str: str = "",
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes a rule widget.

        Args:
            find_str (str, optional): The initial find string. Defaults to "".
            replace_str (str, optional): The initial replace string.
                Defaults to "".
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to Widget.
        """
        super().__init__(parent, flag)
        layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.search: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self.search.setPlaceholderText("Find")
        self.search.setText(find_str)
        layout.addWidget(self.search)

        layout.addWidget(QtWidgets.QLabel("->", self))

        self.replace: QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
        self.replace.setPlaceholderText("Replace")
        self.replace.setText(replace_str)
        layout.addWidget(self.replace)

        button = widgets.IconButton(self)
        button.set_icon(dcc.get_icon_path("a_close.png"))
        button.setToolTip("Remove Rule")
        button.clicked.connect(lambda: self.removed.emit(self))
        layout.addWidget(button)

    def rule(self) -> tuple[str, str]:
        """Gets the rule from this widget.

        Returns:
            tuple[str, str]: A tuple containing the find and replace strings.
        """
        return self.search.text(), self.replace.text()


class FindAndReplace(QtWidgets.QWidget):
    """Find and replace option tab with dynamic rows."""

    applied = QtCore.Signal(bool)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
    ) -> None:
        """Initializes the Find and Replace tab.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to Widget.
        """
        super().__init__(parent, flag)
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 10, 4, 4)

        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        main_layout.addWidget(scroll_area)

        self.rules_container: QtWidgets.QWidget = QtWidgets.QWidget(self)
        scroll_area.setWidget(self.rules_container)

        self.rules_layout = QtWidgets.QVBoxLayout(self.rules_container)
        self.rules_layout.setContentsMargins(0, 0, 0, 0)
        self.rules_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        ctrl_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(ctrl_layout)

        ctrl_layout.addStretch()

        button: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "+ Add Rules", self
        )
        button.clicked.connect(lambda: self.add_rule())
        ctrl_layout.addWidget(button)

        btn_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(btn_layout)

        button = QtWidgets.QPushButton("Preview", self)
        button.clicked.connect(lambda: self.applied.emit(True))
        btn_layout.addWidget(button)

        button = QtWidgets.QPushButton("Apply", self)
        button.clicked.connect(lambda: self.applied.emit(False))
        btn_layout.addWidget(button)

    @QtCore.Slot()
    def add_rule(self, find: str = "", replace: str = "") -> None:
        """Adds a new dynamic rule row.

        Args:
            find (str, optional): The initial find string. Defaults to "".
            replace (str, optional): The initial replace string. Defaults to "".
        """
        rule_widget: FindReplaceRuleWidget = FindReplaceRuleWidget(
            find, replace, self.rules_container
        )
        rule_widget.removed.connect(self.remove_rule)
        self.rules_layout.addWidget(rule_widget)

    @QtCore.Slot(QtWidgets.QWidget)
    def remove_rule(self, widget: QtWidgets.QWidget) -> None:
        """Removes a dynamic rule row widget.

        Args:
            widget (QtWidgets.QWidget): The rule widget to be removed.
        """
        self.rules_layout.removeWidget(widget)
        widget.deleteLater()
        if self.rules_layout.count() == 0:
            self.add_rule()

    def rules(self) -> list[tuple[str, str]]:
        """Collects the find and replace data from all dynamic rows.

        Returns:
            list[tuple[str, str]]: A list of (find, replace) tuples.
        """
        rules: list[tuple[str, str]] = []
        for i in range(self.rules_layout.count()):
            item: QtWidgets.QLayoutItem = self.rules_layout.itemAt(i)
            if item and item.widget():
                widget: QtWidgets.QWidget = item.widget()
                if isinstance(widget, FindReplaceRuleWidget):
                    rules.append(widget.rule())

        return rules

    def set_rules(self, rules: list[list[str]]) -> None:
        """Populates the dynamic rows from a list of rules.

        Args:
            rules (list[list[str]]): A list of rule pairs
                (e.g., [["find1", "replace1"], ...]).
        """
        while self.rules_layout.count():
            item: QtWidgets.QLayoutItem = self.rules_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        for rule in rules:
            if len(rule) == 2:
                self.add_rule(rule[0], rule[1])

        if self.rules_layout.count() == 0:
            self.add_rule()


class MainWindow(framework.ToolWindow[Settings]):
    """Tool main window acting as the controller."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        flag: QtCore.Qt.WindowType = QtCore.Qt.WindowType.Widget,
        unique_id: str = "",
    ) -> None:
        """Initializes the main window.

        Args:
            parent (QtWidgets.QWidget | None, optional): The parent widget.
                Defaults to None.
            flag (QtCore.Qt.WindowType, optional): The window flags.
                Defaults to Widget.
            unique_id (str, optional): The unique identifier for this window.
                Defaults to "".
        """
        super().__init__(parent, flag, unique_id)
        self.setWindowTitle(__product__)
        self.resize(400, 300)
        self.__tab: QtWidgets.QTabWidget
        self.__find_and_replace: FindAndReplace

    def create_ui(self, parent: QtWidgets.QWidget) -> None:
        """Creates the user interface.

        Args:
            parent (QtWidgets.QWidget): The parent widget to contain the UI.
        """
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.__tab = QtWidgets.QTabWidget(self)
        self.__tab.setDocumentMode(True)
        main_layout.addWidget(self.__tab)

        string_and_number: StringAndNumber = StringAndNumber(self)
        string_and_number.applied.connect(self.string_and_number)
        self.__tab.addTab(string_and_number, "String && Number")

        insert_string_to: InsertStringTo = InsertStringTo(self)
        insert_string_to.applied.connect(self.insert_string)
        self.__tab.addTab(insert_string_to, "Insert String To")

        self.__find_and_replace = FindAndReplace(self)
        self.__find_and_replace.applied.connect(self.find_replace)
        self.__tab.addTab(self.__find_and_replace, "Find && Replace")

        settings: Settings = self.tool_settings()
        settings.window_geo.bind(
            setter=self.restoreGeometry,
            getter=self.saveGeometry,
            encoder=utils.qt_to_ascii,
            decoder=utils.ascii_to_qt,
        )
        settings.base_name.bind(
            setter=string_and_number.base_name.setText,
            getter=string_and_number.base_name.text,
        )
        settings.start_number.bind(
            setter=string_and_number.start_number.setText,
            getter=string_and_number.start_number.text,
        )
        settings.padding.bind(
            setter=string_and_number.padding.setValue,
            getter=string_and_number.padding.value,
        )
        settings.suffix.bind(
            setter=string_and_number.suffix.setText,
            getter=string_and_number.suffix.text,
        )
        settings.insert_str.bind(
            setter=insert_string_to.insert.setText,
            getter=insert_string_to.insert.text,
        )
        settings.insert_to.bind(
            setter=insert_string_to.insert_to.setCurrentIndex,
            getter=insert_string_to.insert_to.currentIndex,
        )

        def get_rules_json() -> str:
            """Helper to encode rules to JSON string."""
            return json.dumps(self.__find_and_replace.rules())

        def set_rules_json(val: str) -> None:
            """Helper to decode rules from JSON string."""
            try:
                rules: Any = json.loads(val)
                if not rules:
                    rules = [["", ""]]

                self.__find_and_replace.set_rules(rules)

            except json.JSONDecodeError:
                self.__find_and_replace.set_rules([["", ""]])

        settings.find_replace_rules.bind(
            setter=set_rules_json,
            getter=get_rules_json,
        )

    def string_and_number(self, preview: bool) -> None:
        """Executes the string and number logic.

        Args:
            preview (bool): If True, runs in preview mode without modifying
                the scene.
        """
        self.save_settings()
        settings: Settings = self.tool_settings()
        start: str = settings.start_number.value()

        find: str = ""
        replace: str = ""
        number: int = 0
        if re.search("^[0-9]*$", start):
            find = "^.*$"
            replace = f"{settings.base_name.value()}@i<{settings.padding.value()}>{settings.suffix.value()}"
            number = int(start)

        elif re.search("^[a-zA-Z]*$", start):
            tag: str = "J" if re.search("^[A-Z]*$", start) else "j"
            find = "^.*$"
            replace = f"{settings.base_name.value()}@{tag}<{settings.padding.value()}>{settings.suffix.value()}"
            number = char_to_num(start.upper())

        else:
            _logger.error("Start has no legal characters.")
            return

        self.rename([(find, replace)], number, preview)

    def insert_string(self, preview: bool) -> None:
        """Executes the insert string logic.

        Args:
            preview (bool): If True, runs in preview mode without modifying
                the scene.
        """
        self.save_settings()
        settings: Settings = self.tool_settings()
        find: str = "^.*$"
        if settings.insert_to.value() == 0:
            replace: str = f"{settings.insert_str.value()}@g<0>"
        else:
            replace = f"@g<0>{settings.insert_str.value()}"

        self.rename([(find, replace)], preview=preview)

    def find_replace(self, preview: bool) -> None:
        """Executes the multiple find and replace logic.

        Args:
            preview (bool): If True, runs in preview mode without modifying
                the scene.
        """
        self.save_settings()
        raw_rules: list[tuple[str, str]] = self.__find_and_replace.rules()
        rules: list[tuple[str, str]] = []
        for find, replace in raw_rules:
            rules.append((find.replace("*", ".*"), replace))

        self.rename(rules, preview=preview)

    @dcc.undo
    def rename(
        self,
        rules: list[tuple[str, str]],
        number: int = 0,
        preview: bool = False,
    ) -> None:
        """A wrapper for the core renaming logic to handle UI updates and
        undo grouping.

        Args:
            rules (list[tuple[str, str]]): A list of (find, replace) tuples.
            number (int, optional): The initial number for sequential renaming.
                Defaults to 0.
            preview (bool, optional): If True, opens the preview dialog
                instead of applying directly. Defaults to False.
        """
        if preview:
            changes: list[tuple[str, str]] = rename(rules, number, preview=True)
            if not changes:
                _logger.warning("No nodes will be renamed.")
                return

            dialog: PreviewDialog = PreviewDialog(changes, self)
            result: int = dialog.exec_()
            if result == QtWidgets.QDialog.DialogCode.Accepted:
                rename(rules, number, preview=False)

        else:
            rename(rules, number, preview=False)


def num_to_char(v: int, padding: int, is_lower: bool = False) -> str:
    """Converts an integer to an alphabetical sequence (e.g., 1 -> A, 27 -> AA).

    Args:
        v (int): The integer to convert.
        padding (int): The minimum character padding (e.g., padding=3 -> AAB).
        is_lower (bool, optional): If True, returns lowercase characters.
            Defaults to False.

    Returns:
        str: The alphabetical sequence.
    """
    result: str = ""
    abc: list[str] = [chr(x) for x in range(65, 91)]
    while v > 0:
        result = abc[(v % len(abc)) - 1] + result
        v = int((v - 1) / len(abc))

    if len(result) < padding:
        d: int = padding - len(result)
        result = ("A" * d) + result

    if is_lower:
        result = result.lower()

    return result


def char_to_num(chars: str) -> int:
    """Converts an alphabetical sequence back to an integer.

    Args:
        chars (str): The string of characters to convert (e.g., 'A', 'AA').

    Returns:
        int: The resulting integer.
    """
    num: int = 0
    for c in chars:
        num = num * 26 + (ord(c) - 64)
    return num


def apply_rule(string: str, find: str, replace: str, number: int) -> str:
    """Applies a single find/replace rule resolving special formatting tokens.

    Supports advanced replacement tokens such as:
    @g<X> for Regex Groups
    @u<X> for Uppercase
    @l<X> for Lowercase
    @ul<X> for Swapcase
    @i<X> for Incrementing Integer
    @J<X> for Uppercase Alphabetical
    @j<X> for Lowercase Alphabetical

    Args:
        string (str): The input string to modify.
        find (str): The regex pattern to find.
        replace (str): The replacement string potentially containing special tokens.
        number (int): The sequence number for incremental replacement.

    Returns:
        str: The modified string.
    """
    base_string: str = string
    temp: str = string

    # @g<*>
    for i in range(9):
        u2: re.Match[str] | None = re.search(rf"@g<[{i}]>", replace)
        if u2:
            myid = int(re.sub(r"@g<|>", "", u2.group(0)))
            match_value: re.Match[str] | None = re.search(find, base_string)
            if match_value:
                try:
                    value: str = match_value.group(myid)
                    replace = re.sub(rf"@g<{i}>", value, replace)
                except IndexError:
                    replace = re.sub(rf"@g<{i}>", "", replace)
            else:
                replace = re.sub(rf"@g<{i}>", "", replace)

    temp = re.sub(find, replace, temp)

    # @u<*>
    for i in range(9):
        upper_cmd: re.Match[str] | None = re.search(rf"@u<[{i}]>", temp)
        if upper_cmd:
            myid = int(re.sub(r"@u<|>", "", upper_cmd.group(0)))
            match_value = re.search(find, base_string)
            if match_value:
                try:
                    value = match_value.group(myid).upper()
                    temp = re.sub(rf"@u<{i}>", value, temp)
                except IndexError:
                    pass

    # @l<*>
    for i in range(9):
        lower_cmd: re.Match[str] | None = re.search(rf"@l<[{i}]>", temp)
        if lower_cmd:
            myid = int(re.sub(r"@l<|>", "", lower_cmd.group(0)))
            match_value = re.search(find, base_string)
            if match_value:
                try:
                    value = match_value.group(myid).lower()
                    temp = re.sub(rf"@l<{i}>", value, temp)
                except IndexError:
                    pass

    # @ul<*>
    for i in range(9):
        swap_cmd: re.Match[str] | None = re.search(rf"@ul<[{i}]>", temp)
        if swap_cmd:
            myid = int(re.sub(r"@ul<|>", "", swap_cmd.group(0)))
            match_value = re.search(find, base_string)
            if match_value:
                try:
                    value = match_value.group(myid).swapcase()
                    temp = re.sub(rf"@ul<{i}>", value, temp)
                except IndexError:
                    pass

    # @i<*>
    number_cmd: re.Match[str] | None = re.search(r"@i<[0-9]*>", temp)
    if number_cmd:
        padding_str: str = re.sub(r"@i<|>", "", number_cmd.group(0))
        if padding_str:
            padding: int = int(padding_str)
            number_format: str = f"%.{padding}i"
            replace_str: str = number_format % number
            temp = re.sub(rf"@i<{padding}>", replace_str, temp)

    # @J<*>
    number_cmd = re.search(r"@J<[0-9]*>", temp)
    if number_cmd:
        padding_str = re.sub(r"@J<|>", "", number_cmd.group(0))
        if padding_str:
            padding_num: int = int(padding_str)
            replace_str = num_to_char(number, padding_num)
            temp = re.sub(rf"@J<{padding_num}>", replace_str, temp)

    # @j<*>
    number_cmd = re.search(r"@j<[0-9]*>", temp)
    if number_cmd:
        padding_str = re.sub(r"@j<|>", "", number_cmd.group(0))
        if padding_str:
            padding_num = int(padding_str)
            replace_str = num_to_char(number, padding_num, True)
            temp = re.sub(rf"@j<{padding_num}>", replace_str, temp)

    return temp


def apply_rules(
    string: str, rules: list[tuple[str, str]], number: int = 0
) -> str:
    """Iterates through all rules to process sequential replacements.

    Args:
        string (str): The initial string to modify.
        rules (list[tuple[str, str]]): A list of (find, replace) tuples.
        number (int, optional): The sequence number. Defaults to 0.

    Returns:
        str: The final modified string after applying all rules.
    """
    temp: str = string
    for find, replace in rules:
        temp = apply_rule(temp, find, replace, number)

    return temp


def rename(
    rules: list[tuple[str, str]], number: int = 0, preview: bool = False
) -> list[tuple[str, str]]:
    """Core renaming logic handling sequential rules across selected objects.

    Iterates over currently selected nodes in Maya (including Render Setup layers)
    and applies the renaming rules. It returns a list of the modifications made.

    Args:
        rules (list[tuple[str, str]]): A list of (find, replace) tuples.
        number (int, optional): The initial sequence number. Defaults to 0.
        preview (bool, optional): If True, performs calculations but
            avoids renaming nodes. Defaults to False.

    Returns:
        list[tuple[str, str]]: A list of (old_name, new_name) tuples for
            UI updates or previewing.
    """
    default_number: int = number
    has_error: bool = False
    changes: list[tuple[str, str]] = []

    selection: OpenMaya.MSelectionList = (
        OpenMaya.MGlobal.getActiveSelectionList(True)
    )
    rs_selection: list[str] = viewCmds.getSelection(False, False, False, False)
    if not selection and not rs_selection:
        _logger.error("Select nodes or render layer to rename.")
        return changes

    # From Selection
    for i in range(selection.length()):
        try:
            full_path: str = selection.getDagPath(i).fullPathName()
            short_name: str = full_path.split("|")[-1]

        except TypeError:
            mobject: OpenMaya.MObject = selection.getDependNode(i)
            full_path = OpenMaya.MFnDependencyNode(mobject).name()
            short_name = full_path

        new_name: str = apply_rules(short_name, rules, number)
        number += 1

        if short_name == new_name:
            continue

        changes.append((short_name, new_name))
        if not preview:
            try:
                cmds.rename(full_path, new_name)

            except RuntimeError as error:
                _logger.error("Failed to rename : %s", error)
                has_error = True

    # From Render Setup Nodes
    number = default_number
    for rs_node in rs_selection:
        new_name = apply_rules(rs_node, rules, number)
        number += 1

        if rs_node == new_name:
            continue

        changes.append((rs_node, new_name))

        if not preview:
            try:
                layer: Any | None = rs_utils.nameToUserNode(rs_node)
                layer.setName(new_name)  # type: ignore

            except RuntimeError as error:
                _logger.error("Failed to rename : %s", error)
                has_error = True

    if not has_error and not preview and changes:
        _logger.info("Done")

    return changes


def main(unique_id: str = "") -> None:
    """Entry point to launch the Renamer tool window.

    Args:
        unique_id (str, optional): The unique identifier for the tool window instance.
            Defaults to "".
    """
    window: MainWindow = MainWindow(unique_id=unique_id)
    window.show()
