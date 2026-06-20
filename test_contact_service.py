# test_contact_service.py
#
# Unit tests for ContactService, the business-logic layer.
#
# ContactService depends only on the ContactRepository abstraction
# (Dependency Inversion Principle), so most tests here exercise it
# against a lightweight FakeContactRepository instead of SQLite.
# This keeps the tests fast and focused purely on ContactService's
# own behavior: validation, normalization, and delegation.
#
# A few tests at the bottom wire ContactService up to the real
# SqliteContactRepository to confirm the two layers integrate correctly.

import os
import tempfile
import pytest

from contact import Contact
from contact_repository import ContactRepository
from contact_service import ContactService, InvalidEmailError, InvalidPhoneError
from sqlite_contact_repository import SqliteContactRepository


# ---------------------------------------------------------------------------
# Fake repository: an in-memory ContactRepository implementation used only
# for testing. Standing in for the abstraction lets us unit-test
# ContactService without touching SQLite at all.
# ---------------------------------------------------------------------------

class FakeContactRepository(ContactRepository):
    def __init__(self):
        self._contacts = {}
        self._next_id = 1
        self._groups = {"ungrouped"}

    def find_by_id(self, id):
        return self._contacts.get(id)

    def find_all(self):
        return list(self._contacts.values())

    def find_by_name(self, name):
        q = name.lower()
        return [c for c in self._contacts.values() if q in c.get_full_name().lower()]

    def find_by_phone(self, phone):
        return [c for c in self._contacts.values() if phone in (c.get_phone() or "")]

    def find_by_group(self, group):
        g = group.lower()
        return [c for c in self._contacts.values() if (c.get_group() or "").lower() == g]

    def save(self, contact):
        if contact.get_id() is None:
            contact._id = self._next_id
            self._next_id += 1
        self._groups.add((contact.get_group() or "ungrouped"))
        self._contacts[contact.get_id()] = contact

    def delete(self, id):
        self._contacts.pop(id, None)

    def list_groups(self):
        return sorted(self._groups)

    def ensure_group(self, group):
        g = group.strip() or "ungrouped"
        self._groups.add(g)
        return hash(g)

    def delete_group(self, group):
        g = group.strip()
        if not g or g.lower() == "ungrouped":
            return
        self._groups.discard(g)
        for c in self._contacts.values():
            if (c.get_group() or "").lower() == g.lower():
                c.set_group("ungrouped")


@pytest.fixture
def fake_repo():
    return FakeContactRepository()


@pytest.fixture
def service(fake_repo):
    return ContactService(fake_repo)


# ---------------------------------------------------------------------------
# Abstraction check (Dependency Inversion Principle)
# ---------------------------------------------------------------------------

def test_service_accepts_any_contact_repository(fake_repo):
    # ContactService should work with ANY ContactRepository implementation,
    # not just SqliteContactRepository, since it depends on the abstraction.
    service = ContactService(fake_repo)
    contact = service.add_contact("Dip", "Inv", "dip@inv.com", "1", None)
    assert contact.get_id() is not None


# ---------------------------------------------------------------------------
# add_contact: validation
# ---------------------------------------------------------------------------

def test_add_contact_valid(service, fake_repo):
    c = service.add_contact("Alice", "Smith", "alice@example.com", "12345", "friends")
    assert c.get_id() is not None
    fetched = fake_repo.find_by_id(c.get_id())
    assert fetched.get_first_name() == "Alice"
    assert fetched.get_group().lower() == "friends"


def test_add_contact_strips_whitespace(service):
    c = service.add_contact("  Alice  ", "  Smith  ", "alice@example.com", "1", "  friends  ")
    assert c.get_first_name() == "Alice"
    assert c.get_last_name() == "Smith"
    assert c.get_group() == "friends"


def test_add_contact_empty_first_name_raises(service):
    with pytest.raises(ValueError):
        service.add_contact("", "Smith", "a@b.com", "1", None)


def test_add_contact_whitespace_first_name_raises(service):
    with pytest.raises(ValueError):
        service.add_contact("   ", "Smith", "a@b.com", "1", None)


def test_add_contact_none_first_name_raises(service):
    with pytest.raises(ValueError):
        service.add_contact(None, "Smith", "a@b.com", "1", None)


def test_add_contact_empty_last_name_raises(service):
    with pytest.raises(ValueError):
        service.add_contact("Alice", "", "a@b.com", "1", None)


def test_add_contact_normalizes_empty_email_and_phone(service):
    c = service.add_contact("Bob", "Jones", "", "", None)
    assert c.get_email() == "unset"
    assert c.get_phone() == "unset"


def test_add_contact_none_email_and_phone_normalize_to_unset(service):
    c = service.add_contact("Bob", "Jones", None, None, None)
    assert c.get_email() == "unset"
    assert c.get_phone() == "unset"


def test_add_contact_invalid_email_raises(service):
    with pytest.raises(InvalidEmailError):
        service.add_contact("T", "U", "not-an-email", "123", None)


def test_add_contact_invalid_phone_raises(service):
    with pytest.raises(InvalidPhoneError):
        service.add_contact("T", "U", "t@u.com", "phone-with-letters", None)


def test_add_contact_valid_email_formats_accepted(service):
    # Should not raise
    service.add_contact("A", "B", "simple@example.com", None, None)
    service.add_contact("C", "D", "first.last@sub.example.co", None, None)


def test_add_contact_phone_must_be_digits_only(service):
    # Up to 15 digits is valid per the service's phone regex
    c = service.add_contact("A", "B", None, "123456789012345", None)
    assert c.get_phone() == "123456789012345"


def test_add_contact_default_group_is_ungrouped_when_blank(service):
    c = service.add_contact("A", "B", "a@b.com", "1", "   ")
    assert c.get_group() == "ungrouped"


def test_add_contact_default_group_is_ungrouped_when_none(service):
    c = service.add_contact("A", "B", "a@b.com", "1", None)
    assert c.get_group() == "ungrouped"


# ---------------------------------------------------------------------------
# update_contact
# ---------------------------------------------------------------------------

def test_update_contact_existing(service, fake_repo):
    c = service.add_contact("Carl", "B", "c@b.com", "1", "g")
    c.set_first_name("Carlton")
    service.update_contact(c)
    updated = fake_repo.find_by_id(c.get_id())
    assert updated.get_first_name() == "Carlton"


def test_update_contact_missing_raises(service):
    ghost = Contact(999, "Ghost", "User", "g@u.com", "0", None)
    with pytest.raises(ValueError):
        service.update_contact(ghost)


# ---------------------------------------------------------------------------
# delete_contact
# ---------------------------------------------------------------------------

def test_delete_contact_existing(service, fake_repo):
    c = service.add_contact("D", "E", "d@e.com", "2", None)
    cid = c.get_id()
    service.delete_contact(cid)
    assert fake_repo.find_by_id(cid) is None


def test_delete_contact_missing_raises(service):
    with pytest.raises(ValueError):
        service.delete_contact(424242)


# ---------------------------------------------------------------------------
# get_contact_by_id / get_all_contacts
# ---------------------------------------------------------------------------

def test_get_contact_by_id_existing(service):
    c = service.add_contact("A", "B", "a@b.com", "1", None)
    fetched = service.get_contact_by_id(c.get_id())
    assert fetched.get_id() == c.get_id()


def test_get_contact_by_id_missing_raises(service):
    with pytest.raises(ValueError):
        service.get_contact_by_id(123456)


def test_get_all_contacts(service):
    service.add_contact("A", "B", "a@b.com", "1", None)
    service.add_contact("C", "D", "c@d.com", "2", None)
    assert len(service.get_all_contacts()) == 2


# ---------------------------------------------------------------------------
# query_contacts
# ---------------------------------------------------------------------------

def test_query_contacts_blank_text_returns_empty(service):
    service.add_contact("A", "B", "a@b.com", "1", None)
    assert service.query_contacts("name", "") == []
    assert service.query_contacts("name", "   ") == []


def test_query_contacts_by_name_mode(service):
    service.add_contact("Jonathan", "Doe", "j@d.com", "1", None)
    results = service.query_contacts("name", "Jonathan")
    assert any(c.get_first_name() == "Jonathan" for c in results)


def test_query_contacts_unknown_mode_falls_back_to_name(service):
    service.add_contact("Jonathan", "Doe", "j@d.com", "1", None)
    results = service.query_contacts("nonsense_mode", "Jonathan")
    assert any(c.get_first_name() == "Jonathan" for c in results)


def test_query_contacts_number_and_phone_modes_are_equivalent(service):
    # phone validation only accepts digits, so no hyphens here
    service.add_contact("P", "Q", "p@q.com", "5551234", None)
    by_number = service.query_contacts("number", "555")
    by_phone = service.query_contacts("phone", "555")
    assert len(by_number) == len(by_phone) == 1


# ---------------------------------------------------------------------------
# get_contacts_sorted_by
# ---------------------------------------------------------------------------

def test_sorted_by_first_name(service):
    service.add_contact("Zed", "A", "z@a.com", "1", None)
    service.add_contact("Amy", "B", "a@b.com", "2", None)
    sorted_by_first = service.get_contacts_sorted_by("first")
    assert [c.get_first_name() for c in sorted_by_first] == ["Amy", "Zed"]


def test_sorted_by_last_name(service):
    service.add_contact("A", "Zed", "a@z.com", "1", None)
    service.add_contact("B", "Amy", "b@a.com", "2", None)
    sorted_by_last = service.get_contacts_sorted_by("last_name")
    assert [c.get_last_name() for c in sorted_by_last] == ["Amy", "Zed"]


def test_sorted_by_unknown_key_returns_unsorted(service):
    service.add_contact("Z", "Z", "z@z.com", "1", None)
    service.add_contact("A", "A", "a@a.com", "2", None)
    result = service.get_contacts_sorted_by("not_a_real_key")
    assert len(result) == 2  # no filtering, just no sorting guarantee


# ---------------------------------------------------------------------------
# delete_group
# ---------------------------------------------------------------------------

def test_delete_group_blank_raises(service):
    with pytest.raises(ValueError):
        service.delete_group("")


def test_delete_group_delegates_to_repository(service, fake_repo):
    service.add_contact("G1", "User", "g1@x.com", "9", "teamx")
    service.delete_group("teamx")
    after = fake_repo.find_all()[0]
    assert after.get_group().lower() == "ungrouped"


# ---------------------------------------------------------------------------
# list_groups
# ---------------------------------------------------------------------------

def test_list_groups_includes_ungrouped_by_default(service):
    assert any(g.lower() == "ungrouped" for g in service.list_groups())


# ---------------------------------------------------------------------------
# Integration: ContactService + real SqliteContactRepository
# ---------------------------------------------------------------------------

@pytest.fixture
def sqlite_repo_tmp():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        r = SqliteContactRepository(path)
        yield r
    finally:
        try:
            r.close()
        except Exception:
            pass
        if os.path.exists(path):
            os.remove(path)


def test_service_with_real_sqlite_repository(sqlite_repo_tmp):
    service = ContactService(sqlite_repo_tmp)
    c = service.add_contact("Real", "Repo", "real@repo.com", "1", "qa")
    assert c.get_id() is not None

    fetched = sqlite_repo_tmp.find_by_id(c.get_id())
    assert fetched.get_first_name() == "Real"
    assert fetched.get_group().lower() == "qa"

    service.delete_contact(c.get_id())
    assert sqlite_repo_tmp.find_by_id(c.get_id()) is None
