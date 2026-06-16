# gui_controller.py
from typing import Optional
from PyQt6 import QtWidgets, QtCore
from contact import Contact
from contact_service import ContactService
from ui import UiWindow, ContactDialog, QueryMode

class GuiController:
    def __init__(self, service: ContactService, view: UiWindow):
        self.service = service
        self.view = view
        self._wire_view_handlers()

    def _wire_view_handlers(self) -> None:
        self.view.register_handlers(
            on_add=self.add_contact,
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
            c = self.service.add_contact(first, last, email, phone, group)
            self.view.add_contact_item(c)

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
