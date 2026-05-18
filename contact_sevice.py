"""
contact_service.py - Business logic layer
"""
import re
from typing import List
from contact import Contact
from contact_repository import ContactRepository


class ContactService:

    def __init__(self, repository: ContactRepository):
        # Dependency Injection
        self._repository = repository
        self._next_id = 1

    #  Internal helpers
    
    def _generate_id(self) -> int:
        id = self._next_id
        self._next_id += 1
        return id

    @staticmethod
    def _validate_not_empty(value: str, field_name: str) -> None:
        if not value or not value.strip():
            raise ValueError(f"{field_name} cannot be empty.")

    #  Public API
    def add_contact(self, first_name: str, last_name: str, email: str, phone: str) -> Contact:
        self._validate_not_empty(first_name, "First name")
        self._validate_not_empty(last_name, "Last name")
        self._validate_not_empty(email, "Email")
        self._validate_not_empty(phone, "Phone")

        contact = Contact(self._generate_id(), first_name.strip(), last_name.strip(),
                          email.strip(), phone.strip())
        self._repository.save(contact)
        return contact

    def update_contact(self, contact: Contact) -> None:
        if self._repository.find_by_id(contact.get_id()) is None:
            raise ValueError(f"Contact with id={contact.get_id()} not found.")
        self._repository.save(contact)

    def delete_contact(self, id: int) -> None:
        if self._repository.find_by_id(id) is None:
            raise ValueError(f"Contact with id={id} not found.")
        self._repository.delete(id)

    def search_by_name(self, name: str) -> List[Contact]:
        self._validate_not_empty(name, "Search query")
        return self._repository.find_by_name(name)

    def get_all_contacts(self) -> List[Contact]:
        return self._repository.find_all()

    def get_contact_by_id(self, id: int) -> Contact:
        contact = self._repository.find_by_id(id)
        if contact is None:
            raise ValueError(f"Contact with id={id} not found.")
        return contact
