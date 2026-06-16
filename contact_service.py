import re
from typing import List, Optional
from contact import Contact
from contact_repository import ContactRepository

class ContactService:
    def __init__(self, repository: ContactRepository):
        self._repository = repository

    def _validate(self, first_name: str, last_name: str, email: Optional[str], phone: Optional[str]):
        if not self._validate_not_empty(first_name):
            raise ValueError("First Name cannot be empty.")
        if not self._validate_not_empty(last_name):
            raise ValueError("Last Name cannot be empty.")

        email_norm = email.strip() if email and email.strip() else "unset"
        phone_norm = phone.strip() if phone and phone.strip() else "unset"

        if email_norm != "unset" and not re.match(r"[^@]+@[^@]+\.[^@]+", email_norm):
            raise ValueError(f"Invalid email address: {email_norm}")

        return email_norm, phone_norm

    @staticmethod
    def _validate_not_empty(value: Optional[str]) -> bool:
        if value is None:
            return False
        if not value or not value.strip():
            return False
        return True

    def add_contact(self, first_name: str, last_name: str, email: Optional[str], phone: Optional[str], group: Optional[str] = None) -> Contact:
        email_norm, phone_norm = self._validate(first_name, last_name, email, phone)
        grp = group.strip() if group and group.strip() else "ungrouped"
        contact = Contact(None, first_name.strip(), last_name.strip(), email_norm, phone_norm, grp)
        self._repository.save(contact)
        return contact

    def update_contact(self, contact: Contact) -> None:
        existing = self._repository.find_by_id(contact.get_id())
        if existing is None:
            raise ValueError(f"Contact with id={contact.get_id()} not found.")
        self._repository.save(contact)

    def delete_contact(self, id: int) -> None:
        existing = self._repository.find_by_id(id)
        if existing is None:
            raise ValueError(f"Contact with id={id} not found.")
        self._repository.delete(id)

    def search_by_name(self, name: str) -> List[Contact]:
        if not self._validate_not_empty(name):
            raise ValueError("Search query cannot be empty")
        return self._repository.find_by_name(name)

    def search_by_phone(self, phone: str) -> List[Contact]:
        if not self._validate_not_empty(phone):
            raise ValueError("Search query cannot be empty")
        return self._repository.find_by_phone(phone)

    def search_by_group(self, group: str) -> List[Contact]:
        if not self._validate_not_empty(group):
            raise ValueError("Search query cannot be empty")
        return self._repository.find_by_group(group)

    def get_all_contacts(self) -> List[Contact]:
        return self._repository.find_all()

    def get_contact_by_id(self, id: int) -> Contact:
        contact = self._repository.find_by_id(id)
        if contact is None:
            raise ValueError(f"Contact with id={id} not found.")
        return contact

    def query_contacts(self, query_mode: str, text: str) -> List[Contact]:
        q = text.strip()
        if not self._validate_not_empty(q):
            return []

        mode = query_mode or "name"
        mode = mode.lower()
        if mode == "name":
            return self._repository.find_by_name(q)
        if mode == "first":
            # repository has no find_by_first; filter in-memory
            return [c for c in self._repository.find_all() if q.lower() in c.get_first_name().lower()]
        if mode == "last":
            return [c for c in self._repository.find_all() if q.lower() in c.get_last_name().lower()]
        if mode == "email":
            return [c for c in self._repository.find_all() if q.lower() in c.get_email().lower()]
        if mode == "number" or mode == "phone":
            return self._repository.find_by_phone(q)
        if mode == "group":
            return self._repository.find_by_group(q)

        # fallback: full name search
        return self._repository.find_by_name(q)


    def get_contacts_sorted_by(self, category_key: str) -> List[Contact]:
        key = (category_key or "id").lower()
        allc = list(self._repository.find_all())
        if key in ("id",):
            return sorted(allc, key=lambda c: (c.get_id() or 0))
        if key in ("first", "first_name"):
            return sorted(allc, key=lambda c: (c.get_first_name() or "").lower())
        if key in ("last", "last_name"):
            return sorted(allc, key=lambda c: (c.get_last_name() or "").lower())
        if key in ("email",):
            return sorted(allc, key=lambda c: (c.get_email() or "").lower())
        if key in ("phone", "number"):
            return sorted(allc, key=lambda c: (c.get_phone() or "").lower())
        if key in ("group",):
            return sorted(allc, key=lambda c: (c.get_group() or "").lower())
        return allc

    def list_groups(self) -> List[str]:
        return self._repository.list_groups()

