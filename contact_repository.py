from abc import ABC, abstractmethod
from typing import List, Optional
from contact import Contact

class ContactRepository(ABC):
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[Contact]:
        pass

    @abstractmethod
    def find_all(self) -> List[Contact]:
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> List[Contact]:
        pass

    @abstractmethod
    def find_by_phone(self, phone: str) -> List[Contact]:
        pass

    @abstractmethod
    def find_by_group(self, group: str) -> List[Contact]:
        pass

    @abstractmethod
    def save(self, contact: Contact) -> None:
        pass

    @abstractmethod
    def delete(self, id: int) -> None:
        pass

    # group management
    @abstractmethod
    def list_groups(self) -> List[str]:
        pass

    @abstractmethod
    def ensure_group(self, group: str) -> int:
        pass

