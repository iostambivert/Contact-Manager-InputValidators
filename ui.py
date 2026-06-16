#ui.py
from enum import Enum
from typing import Callable, List, Optional, Tuple
from PyQt6 import QtCore, QtGui, QtWidgets

class QueryMode(str, Enum):
    NAME = "name"
    FIRST = "first"
    LAST = "last"
    EMAIL = "email"
    NUMBER = "number"
    GROUP = "group"

class UiWindow:
    def __init__(self):
        self.window = QtWidgets.QMainWindow()
        self.window.setWindowTitle("Simple Contact Manager")
        self.window.resize(1200, 800)
        self._apply_dark_theme()

        central = QtWidgets.QWidget()
        self.window.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # toolbar
        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(18, 18))
        self.window.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.add_action = QtGui.QAction(QtGui.QIcon.fromTheme("list-add"), "Add", self.window)
        self.edit_action = QtGui.QAction(QtGui.QIcon.fromTheme("document-edit"), "Edit", self.window)
        self.delete_action = QtGui.QAction(QtGui.QIcon.fromTheme("user-trash"), "Delete", self.window)
        self.refresh_action = QtGui.QAction(QtGui.QIcon.fromTheme("view-refresh"), "Refresh", self.window)
        for a in (self.add_action, self.edit_action, self.delete_action, self.refresh_action):
            self.toolbar.addAction(a)

        # header: title, search type dropdown , and search line
        header = QtWidgets.QHBoxLayout()
        main_layout.addLayout(header)
        self.title_label = QtWidgets.QLabel("Contacts")
        self.title_label.setObjectName("titleLabel")
        header.addWidget(self.title_label, stretch=0)
        header.addStretch(1)

        self.search_mode = QtWidgets.QComboBox()
        self.search_mode.setMinimumWidth(80)
        self.search_mode.setMaximumWidth(120)
        self.search_mode.addItem("Name", QueryMode.NAME.value)
        self.search_mode.addItem("Email", QueryMode.EMAIL.value)
        self.search_mode.addItem("Phone", QueryMode.NUMBER.value)
        self.search_mode.addItem("Group", QueryMode.GROUP.value)
        header.addWidget(self.search_mode)

        self.search_line = QtWidgets.QLineEdit()
        self.search_line.setPlaceholderText("Search...")
        self.search_line.setClearButtonEnabled(True)
        header.addWidget(self.search_line, stretch=1)

        # main splitter: left table and right detail
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # contacts table
        self.table = QtWidgets.QTreeWidget()
        self.table.setColumnCount(6)
        self.table.setHeaderLabels(["ID", "First Name", "Last Name", "Email", "Phone", "Group"])
        self.table.setRootIsDecorated(False)
        self.table.setAllColumnsShowFocus(True)
        self.table.header().setSectionsMovable(True)
        self.table.header().setStretchLastSection(True)
        self.table.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.table.setUniformRowHeights(False)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        # set default column widths
        self.table.setColumnWidth(0, 10) #id
        self.table.setColumnWidth(1, 180) #name
        self.table.setColumnWidth(2, 180) #last name
        self.table.setColumnWidth(3, 220) #email
        self.table.setColumnWidth(4, 100) #phone
        self.table.setColumnWidth(5, 80) #group
        splitter.addWidget(self.table)

        # right: detail preview
        self.detail_panel = QtWidgets.QFrame()
        dp_layout = QtWidgets.QFormLayout(self.detail_panel)
        dp_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        dp_layout.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.detail_name = QtWidgets.QLabel("—")
        self.detail_group = QtWidgets.QLabel("—")
        self.detail_email = QtWidgets.QLabel("—")
        self.detail_phone = QtWidgets.QLabel("—")
        dp_layout.addRow("<b>Name:</b>", self.detail_name)
        dp_layout.addRow("<b>Group:</b>", self.detail_group)
        dp_layout.addRow("<b>Email:</b>", self.detail_email)
        dp_layout.addRow("<b>Phone:</b>", self.detail_phone)
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        self.window.statusBar().showMessage("Ready")

        # handlers (register_handlers)
        self._handlers = {
            "add": lambda: None, "edit": lambda: None, "delete": lambda: None,
            "refresh": lambda: None, "query": lambda mode, text: None, "request_sorted": lambda k: None
        }

        # wire toolbar
        self.add_action.triggered.connect(lambda: self._handlers["add"]())
        self.edit_action.triggered.connect(lambda: self._handlers["edit"]())
        self.delete_action.triggered.connect(lambda: self._handlers["delete"]())
        self.refresh_action.triggered.connect(lambda: self._handlers["refresh"]())

        # search enters -> delegate to app
        self.search_line.returnPressed.connect(lambda: self._handlers["query"](self.search_mode.currentData(), self.search_line.text().strip()))

        # selection -> preview
        self.table.currentItemChanged.connect(self._on_selection_changed)

        # header clicks request sorting from app
        self.table.header().sectionClicked.connect(lambda idx: self._on_header_clicked(idx))

        try:
            with open("styles.qss", "r", encoding="utf-8") as f:
                self.window.setStyleSheet(f.read())
        except Exception:
            pass

    def register_handlers(self,
                          on_add: Callable[[], None],
                          on_edit: Callable[[], None],
                          on_delete: Callable[[], None],
                          on_refresh: Callable[[], None],
                          on_query: Callable[[str, str], None],
                          on_request_sorted: Callable[[str], None]) -> None:
        self._handlers.update({
            "add": on_add, "edit": on_edit, "delete": on_delete,
            "refresh": on_refresh, "query": on_query, "request_sorted": on_request_sorted
        })

    def show(self) -> None:
        self.window.show()

    def add_contact_item(self, contact) -> None:
        # single row per contact, store Contact in UserRole
        row = [
            str(contact.get_id()),
            contact.get_first_name(),
            contact.get_last_name(),
            contact.get_email(),
            contact.get_phone(),
            contact.get_group(),
        ]
        it = QtWidgets.QTreeWidgetItem(row)
        it.setData(0, QtCore.Qt.ItemDataRole.UserRole, contact)
        self.table.addTopLevelItem(it)

    def clear_list(self) -> None:
        self.table.clear()

    def current_item(self) -> Optional[QtWidgets.QTreeWidgetItem]:
        return self.table.currentItem()

    def _on_selection_changed(self, current: Optional[QtWidgets.QTreeWidgetItem], prev: Optional[QtWidgets.QTreeWidgetItem]) -> None:
        if not current:
            self._clear_preview(); return
        contact = current.data(0, QtCore.Qt.ItemDataRole.UserRole)
        self.detail_name.setText(contact.get_full_name())
        self.detail_group.setText(contact.get_group())
        self.detail_email.setText(contact.get_email())
        self.detail_phone.setText(contact.get_phone())

    def _clear_preview(self) -> None:
        self.detail_name.setText("—")
        self.detail_group.setText("—")
        self.detail_email.setText("—")
        self.detail_phone.setText("—")

    def _on_header_clicked(self, section_index: int) -> None:
        # map column index > category key and delegate request to application
        mapping = {
            0: "id",
            1: "first",
            2: "last",
            3: "email",
            4: "phone",
            5: "group"
        }
        key = mapping.get(section_index, "id")
        self._handlers.get("request_sorted", lambda k: None)(key)

    def _apply_dark_theme(self) -> None:
        palette = QtGui.QPalette()
        base = QtGui.QColor(18, 20, 23)
        alt_base = QtGui.QColor(26, 28, 33)
        text = QtGui.QColor(230, 230, 235)
        muted = QtGui.QColor(160, 166, 178)
        palette.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Window, base)
        palette.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Base, alt_base)
        palette.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.Text, text)
        palette.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.ButtonText, text)
        palette.setColor(QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorRole.PlaceholderText, muted)
        self.window.setPalette(palette)


# ContactDialog for adding new contacts
class ContactDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, title: str = "Contact", contact: Optional[object] = None,
                 groups: Optional[List[str]] = None):
        super().__init__(parent)
        self.setWindowTitle(title); self.resize(520, 280)
        self._contact = contact; self._groups = groups or ["ungrouped"]
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout(); layout.addLayout(form)
        self.first = QtWidgets.QLineEdit(contact.get_first_name() if contact else "")
        self.last = QtWidgets.QLineEdit(contact.get_last_name() if contact else "")
        self.email = QtWidgets.QLineEdit(contact.get_email() if contact else "")
        self.phone = QtWidgets.QLineEdit(contact.get_phone() if contact else "")
        self.group_combo = QtWidgets.QComboBox()
        self.group_combo.addItems(self._groups + ["<Create new>"])
        if contact:
            try:
                idx = self._groups.index(contact.get_group())
            except ValueError:
                idx = 0
            self.group_combo.setCurrentIndex(idx)
        form.addRow("First name:", self.first)
        form.addRow("Last name:", self.last)
        form.addRow("Email:", self.email)
        form.addRow("Phone:", self.phone)
        form.addRow("Group:", self.group_combo)
        btns = QtWidgets.QDialogButtonBox()
        ok = QtWidgets.QPushButton("Save"); ok.setObjectName("primary")
        cancel = QtWidgets.QPushButton("Cancel")
        btns.addButton(ok, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        btns.addButton(cancel, QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(btns)
        btns.accepted.connect(self._on_accept); btns.rejected.connect(self.reject)
        self._chosen_group = None

    def _on_accept(self) -> None:
        if not self.first.text().strip() or not self.last.text().strip():
            QtWidgets.QMessageBox.warning(self, "Validation", "First and last name required"); return
        if self.group_combo.currentText() == "<Create new>":
            text, ok = QtWidgets.QInputDialog.getText(self, "New Group", "Group name:")
            self._chosen_group = text.strip() if ok and text.strip() else "ungrouped"
        else:
            self._chosen_group = self.group_combo.currentText()
        self.accept()

    def values(self) -> Tuple[str, str, str, str, str]:
        email = self.email.text().strip() or "unset"
        phone = self.phone.text().strip() or "unset"
        group = getattr(self, "_chosen_group", self.group_combo.currentText())
        return (self.first.text().strip(), self.last.text().strip(), email, phone, group)
