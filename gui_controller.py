# gui_controller.py
from typing import Optional
from PyQt6 import QtWidgets, QtCore
from contact import Contact
from contact_service import ContactService, InvalidEmailError, InvalidPhoneError
from ui import UiWindow, ContactDialog, GroupDialog, QueryMode

class GuiController:
    def __init__(self, service: ContactService, view: UiWindow):
        self.service = service
        self.view = view
        self._wire_view_handlers()

    def _wire_view_handlers(self) -> None:
        self.view.register_handlers(
            on_add=self.add_contact,
            on_groups_manage=self.manage_groups,
            on_edit=self.edit_selected,
            on_delete=self.delete_selected,
            on_refresh=self.refresh_list,
            on_query=self.query,
            on_request_sorted=self.request_sorted
        )

    def refresh_list(self) -> None:
        self.view.clear_list()
        for c in self.service.get_all_contacts():
            self.view.add_contact_item(c)

    def add_contact(self) -> None:
        dlg = ContactDialog(parent=self.view.window, title="Add Contact", groups=self.service.list_groups())
        if dlg.exec():
            first, last, email, phone, group = dlg.values()
            try:
                c = self.service.add_contact(first, last, email, phone, group)
            except InvalidEmailError:
                QtWidgets.QMessageBox.warning(None, "Validation", "Please enter a valid email address.")
                return
            except InvalidPhoneError:
                QtWidgets.QMessageBox.warning(None, "Validation", "Please enter a valid Phone number.")
                return
            self.view.add_contact_item(c)

    def manage_groups(self) -> None:
        groups = self.service.list_groups()
        if not groups:
            QtWidgets.QMessageBox.information(self.view.window, "No groups", "There are no groups to delete.")
            return

        dlg = GroupDialog(parent=self.view.window, groups=groups)
        # initial contacts for selected group
        current = dlg.selected_group()
        if current:
            contacts = self.service.query_contacts("group", current)
            dlg._update_contacts_display(contacts)
        # update contacts when selection changes
        dlg.group_combo.currentTextChanged.connect(lambda grp: dlg.set_contacts(self.service.query_contacts("group", grp)))

        if dlg.exec():
            group_to_delete = dlg.selected_group()
            if not group_to_delete:
                return
            # confirm already shown in dialog then delete via service
            try:
                self.service.delete_group(group_to_delete)
                QtWidgets.QMessageBox.information(self.view.window, "Group deleted", f"Group '{group_to_delete}' deleted. Contacts moved to 'ungrouped'.")
                self.refresh_list()
            except Exception as e:
                QtWidgets.QMessageBox.warning(self.view.window, "Error", str(e))

    def edit_selected(self) -> None:
        item = self.view.current_item()
        if not item:
            return
        contact: Contact = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        dlg = ContactDialog(parent=self.view.window, title="Edit Contact", contact=contact,
                            groups=self.service.list_groups())
        if dlg.exec():
            first, last, email, phone, group = dlg.values()
            contact.set_first_name(first)
            contact.set_last_name(last)
            contact.set_email(email)
            contact.set_phone(phone)
            contact.set_group(group)
            self.service.update_contact(contact)
            self.refresh_list()

    def delete_selected(self) -> None:
        item = self.view.current_item()
        if not item:
            return
        contact: Contact = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        reply = QtWidgets.QMessageBox.question(
            self.view.window,
            "Delete contact",
            f"Delete '{contact.get_full_name()}'?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.service.delete_contact(contact.get_id())
            self.refresh_list()

    def query(self, query_mode: str, text: str) -> None:
        if not text or not text.strip():
            # empty search > show all
            self.refresh_list()
            return
        results = self.service.query_contacts(query_mode, text)
        self.view.clear_list()
        for c in results:
            self.view.add_contact_item(c)

    def request_sorted(self, category_key: str) -> None:
        results = self.service.get_contacts_sorted_by(category_key)
        self.view.clear_list()
        for c in results:
            self.view.add_contact_item(c)