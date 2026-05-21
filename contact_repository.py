"""
contact_repository.py - Abstract repository interface (Repository Pattern)
"""

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
    def save(self, contact: Contact) -> None:
        pass

    @abstractmethod
    def delete(self, id: int) -> None:
        pass
