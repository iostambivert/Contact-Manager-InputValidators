import os
import sqlite3
import tempfile
import pytest

from contact import Contact
from sqlite_contact_repository import SqliteContactRepository, FUZZY_THRESHOLD
from gui_controller import InvalidEmailError, InvalidPhoneError, ContactService

# Small helper to create a repo with a temp DB
@pytest.fixture
def repo_tmp():
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

@pytest.fixture
def service(repo_tmp):
    return ContactService(repo_tmp)

def test_add_contact_valid(service, repo_tmp):
    c = service.add_contact("Alice", "Smith", "alice@example.com", "12345", "friends")
    assert c.get_id() is not None
    fetched = repo_tmp.find_by_id(c.get_id())
    assert fetched is not None
    assert fetched.get_first_name() == "Alice"
    assert fetched.get_group().lower() == "friends"

def test_add_contact_normalizes_empty_email_phone(service):
    c = service.add_contact("Bob", "Jones", "", "", None)
    assert c.get_email() == "unset"
    assert c.get_phone() == "unset"

def test_add_contact_invalid_email(service):
    with pytest.raises(InvalidEmailError):
        service.add_contact("T", "U", "not-an-email", "123", None)

def test_add_contact_invalid_phone(service):
    with pytest.raises(InvalidPhoneError):
        service.add_contact("T", "U", "t@u.com", "phone-with-letters", None)

def test_update_contact(service, repo_tmp):
    c = service.add_contact("Carl", "B", "c@b.com", "1", "g")
    c.set_first_name("Carlton")
    service.update_contact(c)
    updated = repo_tmp.find_by_id(c.get_id())
    assert updated.get_first_name() == "Carlton"

def test_delete_contact(service, repo_tmp):
    c = service.add_contact("D", "E", "d@e.com", "2", None)
    cid = c.get_id()
    service.delete_contact(cid)
    assert repo_tmp.find_by_id(cid) is None

def test_list_and_sort(service):
    # add in non-sorted order
    service.add_contact("Zed", "A", "z@a.com", "1", None)
    service.add_contact("Amy", "B", "a@b.com", "2", None)
    sorted_by_first = service.get_contacts_sorted_by("first")
    assert [c.get_first_name() for c in sorted_by_first][:2] == ["Amy", "Zed"]

def test_group_management(service, repo_tmp):
    # ensure group created on add
    c = service.add_contact("G1", "User", "g1@x.com", "9", "teamx")
    groups = repo_tmp.list_groups()
    assert any(g.lower() == "teamx" for g in groups)

    # delete group moves members to ungrouped
    service.delete_group("teamx")
    after = repo_tmp.find_by_id(c.get_id())
    assert after.get_group().lower() == "ungrouped"

def test_ensure_group_case_insensitive(repo_tmp):
    id1 = repo_tmp.ensure_group("MyGroup")
    id2 = repo_tmp.ensure_group("mygroup")
    assert id1 == id2

def test_find_by_email_and_phone(repo_tmp, service):
    service.add_contact("E1", "F", "searchme@example.com", "555-000", "g")
    res_email = repo_tmp.find_by_email("searchme")
    assert any("searchme@example.com" in c.get_email() for c in res_email)

    res_phone = repo_tmp.find_by_phone("555")
    assert any("555-000" in c.get_phone() for c in res_phone)

def test_find_by_name_fuzzy(repo_tmp, service):
    # Use names that will fuzzy-match
    service.add_contact("Jonathan", "Doe", "j@d.com", "1", None)
    service.add_contact("Jon", "Do", "jon@do.com", "2", None)

    results = repo_tmp.find_by_name("jon")
    # Expect at least one result and we expect fuzzy matching to include Jon/Jonathan
    assert len(results) >= 1
    names = [f"{c.get_first_name()} {c.get_last_name()}" for c in results]
    assert any("jon" in n.lower() or "jonathan" in n.lower() for n in names)

def test_find_by_group_fuzzy(repo_tmp, service):
    service.add_contact("G2", "User", "g2@x.com", "8", "Team Alpha")
    results = repo_tmp.find_by_group_fuzzy("alpha")
    assert any("team alpha" in c.get_group().lower() for c in results)

def test_save_with_explicit_id(repo_tmp):
    # create contact with explicit id (simulate import)
    c = Contact(9999, "Imp", "Ort", "i@o.com", "0", "ungrouped")
    repo_tmp.save(c)
    fetched = repo_tmp.find_by_id(9999)
    assert fetched is not None
    assert fetched.get_first_name() == "Imp"
    # cleanup
    repo_tmp.delete(9999)
    assert repo_tmp.find_by_id(9999) is None
