"""
contact.py - Contact model class
"""


class Contact:

    def __init__(self, id: int, first_name: str, last_name: str, email: str, phone: str):
        self._id = id
        self._first_name = first_name
        self._last_name = last_name
        self._email = email
        self._phone = phone

    #getter
    def get_id(self) -> int:
        return self._id
    def get_full_name(self) -> str:
        return f"{self._first_name} {self._last_name}"
    def get_first_name(self) -> str:
        return self._first_name
    def get_last_name(self) -> str:
        return self._last_name
    def get_email(self) -> str:
        return self._email
    def get_phone(self) -> str:
        return self._phone

    #setters
    def set_first_name(self, first_name: str) -> None:
        self._first_name = first_name
    def set_last_name(self, last_name: str) -> None:
        self._last_name = last_name
    def set_email(self, email: str) -> None:
        self._email = email
    def set_phone(self, phone: str) -> None:
        self._phone = phone

    def __repr__(self) -> str:
        return (
            f"Contact(id={self._id}, name={self.get_full_name()}, "
            f"email={self._email}, phone={self._phone})"
        )
