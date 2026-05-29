from contact import Contact
from contact_repository import ContactRepository


class InMemoryContactRepository(ContactRepository):

    def __init__(self):
        self._store: dict[int, Contact] = {}

    def find_by_id(self, id: int) -> Contact:
        contact = self._store.get(id)
        if not contact:
            raise KeyError(f"Contact with id {id} not found.")
        return contact

    def find_all(self) -> list[Contact]:
        return list(self._store.values())

    def find_by_name(self, name: str) -> list[Contact]:
        name_lower = name.lower()
        return [
            c for c in self._store.values()
            if name_lower in c.get_full_name().lower()
        ]

    def save(self, contact: Contact) -> None:
        self._store[contact.id] = contact

    def delete(self, id: int) -> None:
        if id not in self._store:
            raise KeyError(f"Contact with id {id} not found.")
        del self._store[id]
