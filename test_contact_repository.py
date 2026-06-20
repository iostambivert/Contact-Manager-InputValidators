# test_contact_repository.py
#
# Unit tests for SqliteContactRepository, the concrete implementation of
# the ContactRepository abstract base class.
#
# These tests cover:
#   - CRUD operations (save/find_by_id/find_all/delete)
#   - search behavior (find_by_name, find_by_email, find_by_phone,
#     find_by_group, find_by_group_fuzzy)
#   - group management (ensure_group, list_groups, delete_group)
#
# Each test gets a brand-new temp SQLite file via the repo_tmp fixture,
# so tests never share state or leak into contacts.db.

import os
import tempfile
import pytest

from contact import Contact
from contact_repository import ContactRepository
from sqlite_contact_repository import SqliteContactRepository


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


# ---------------------------------------------------------------------------
# Abstraction / contract
# ---------------------------------------------------------------------------

def test_sqlite_repository_is_a_contact_repository(repo_tmp):
    # SqliteContactRepository must fulfill the ContactRepository contract
    # (Dependency Inversion Principle: ContactService depends on this
    # abstraction, not on SqliteContactRepository directly).
    assert isinstance(repo_tmp, ContactRepository)


def test_ungrouped_exists_by_default(repo_tmp):
    # constructor seeds the "ungrouped" meta group
    groups = repo_tmp.list_groups()
    assert any(g.lower() == "ungrouped" for g in groups)


# ---------------------------------------------------------------------------
# save / find_by_id / find_all
# ---------------------------------------------------------------------------

def test_save_new_contact_assigns_id(repo_tmp):
    c = Contact(None, "Alice", "Smith", "alice@example.com", "12345", "friends")
    repo_tmp.save(c)
    assert c.get_id() is not None

    fetched = repo_tmp.find_by_id(c.get_id())
    assert fetched is not None
    assert fetched.get_first_name() == "Alice"
    assert fetched.get_last_name() == "Smith"
    assert fetched.get_email() == "alice@example.com"
    assert fetched.get_group().lower() == "friends"


def test_save_existing_contact_updates_in_place(repo_tmp):
    c = Contact(None, "Bob", "Jones", "bob@example.com", "1", "work")
    repo_tmp.save(c)
    cid = c.get_id()

    c.set_first_name("Bobby")
    repo_tmp.save(c)

    updated = repo_tmp.find_by_id(cid)
    assert updated.get_first_name() == "Bobby"
    # id should not change across an update
    assert updated.get_id() == cid


def test_save_with_explicit_id_inserts_when_missing(repo_tmp):
    # Simulates an import-style insert that supplies its own id.
    c = Contact(9999, "Imp", "Ort", "i@o.com", "0", "ungrouped")
    repo_tmp.save(c)

    fetched = repo_tmp.find_by_id(9999)
    assert fetched is not None
    assert fetched.get_first_name() == "Imp"


def test_find_by_id_missing_returns_none(repo_tmp):
    assert repo_tmp.find_by_id(424242) is None


def test_find_all_returns_everything_in_id_order(repo_tmp):
    c1 = Contact(None, "Zed", "A", "z@a.com", "1", None)
    c2 = Contact(None, "Amy", "B", "a@b.com", "2", None)
    repo_tmp.save(c1)
    repo_tmp.save(c2)

    all_contacts = repo_tmp.find_all()
    ids = [c.get_id() for c in all_contacts]
    assert ids == sorted(ids)
    assert len(all_contacts) == 2


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_removes_contact(repo_tmp):
    c = Contact(None, "D", "E", "d@e.com", "2", None)
    repo_tmp.save(c)
    cid = c.get_id()

    repo_tmp.delete(cid)
    assert repo_tmp.find_by_id(cid) is None


def test_delete_nonexistent_id_does_not_raise(repo_tmp):
    # delete() is a low-level repository op; missing-id validation is the
    # service layer's job (see ContactService.delete_contact).
    repo_tmp.delete(123456)  # should simply no-op, not raise


# ---------------------------------------------------------------------------
# find_by_name (fuzzy)
# ---------------------------------------------------------------------------

def test_find_by_name_exact_match(repo_tmp):
    repo_tmp.save(Contact(None, "Jonathan", "Doe", "j@d.com", "1", None))
    results = repo_tmp.find_by_name("Jonathan Doe")
    assert any(c.get_first_name() == "Jonathan" for c in results)


def test_find_by_name_fuzzy_match(repo_tmp):
    repo_tmp.save(Contact(None, "Jonathan", "Doe", "j@d.com", "1", None))
    repo_tmp.save(Contact(None, "Jon", "Do", "jon@do.com", "2", None))

    results = repo_tmp.find_by_name("jon")
    assert len(results) >= 1
    names = [f"{c.get_first_name()} {c.get_last_name()}".lower() for c in results]
    assert any("jon" in n for n in names)


def test_find_by_name_empty_query_returns_empty(repo_tmp):
    repo_tmp.save(Contact(None, "A", "B", "a@b.com", "1", None))
    assert repo_tmp.find_by_name("") == []
    assert repo_tmp.find_by_name("   ") == []


def test_find_by_name_no_match_returns_empty(repo_tmp):
    repo_tmp.save(Contact(None, "Alice", "Smith", "a@s.com", "1", None))
    results = repo_tmp.find_by_name("zzzzzzzzzz")
    assert results == []


# ---------------------------------------------------------------------------
# find_by_email
# ---------------------------------------------------------------------------

def test_find_by_email_partial_case_insensitive(repo_tmp):
    repo_tmp.save(Contact(None, "E1", "F", "SearchMe@Example.com", "555-000", "g"))
    results = repo_tmp.find_by_email("searchme")
    assert any("searchme@example.com" in c.get_email().lower() for c in results)


def test_find_by_email_empty_query_returns_empty(repo_tmp):
    repo_tmp.save(Contact(None, "A", "B", "a@b.com", "1", None))
    assert repo_tmp.find_by_email("") == []


# ---------------------------------------------------------------------------
# find_by_phone
# ---------------------------------------------------------------------------

def test_find_by_phone_partial_match(repo_tmp):
    repo_tmp.save(Contact(None, "P1", "Q", "p@q.com", "555-1234", None))
    results = repo_tmp.find_by_phone("555")
    assert any("555-1234" in c.get_phone() for c in results)


def test_find_by_phone_no_match_returns_empty(repo_tmp):
    repo_tmp.save(Contact(None, "P2", "Q", "p2@q.com", "111-1111", None))
    assert repo_tmp.find_by_phone("999") == []


# ---------------------------------------------------------------------------
# find_by_group / find_by_group_fuzzy
# ---------------------------------------------------------------------------

def test_find_by_group_case_insensitive(repo_tmp):
    repo_tmp.save(Contact(None, "G1", "User", "g1@x.com", "9", "TeamX"))
    results = repo_tmp.find_by_group("teamx")
    assert any(c.get_first_name() == "G1" for c in results)


def test_find_by_group_fuzzy_partial_name(repo_tmp):
    repo_tmp.save(Contact(None, "G2", "User", "g2@x.com", "8", "Team Alpha"))
    results = repo_tmp.find_by_group_fuzzy("alpha")
    assert any("team alpha" in c.get_group().lower() for c in results)


# ---------------------------------------------------------------------------
# group management
# ---------------------------------------------------------------------------

def test_ensure_group_creates_group_once(repo_tmp):
    before = set(repo_tmp.list_groups())
    repo_tmp.ensure_group("Newcomers")
    after = set(repo_tmp.list_groups())
    assert "Newcomers" in (after - before) or any(g.lower() == "newcomers" for g in after)


def test_ensure_group_is_case_insensitive(repo_tmp):
    id1 = repo_tmp.ensure_group("MyGroup")
    id2 = repo_tmp.ensure_group("mygroup")
    assert id1 == id2


def test_ensure_group_blank_falls_back_to_ungrouped(repo_tmp):
    gid = repo_tmp.ensure_group("   ")
    ungrouped_id = repo_tmp.ensure_group("ungrouped")
    assert gid == ungrouped_id


def test_delete_group_moves_members_to_ungrouped(repo_tmp):
    c = Contact(None, "G3", "User", "g3@x.com", "7", "teamx")
    repo_tmp.save(c)

    repo_tmp.delete_group("teamx")

    after = repo_tmp.find_by_id(c.get_id())
    assert after.get_group().lower() == "ungrouped"
    assert not any(g.lower() == "teamx" for g in repo_tmp.list_groups())


def test_delete_group_protects_ungrouped(repo_tmp):
    # "ungrouped" is a meta group; deleting it should be a no-op.
    repo_tmp.delete_group("ungrouped")
    assert any(g.lower() == "ungrouped" for g in repo_tmp.list_groups())


def test_delete_group_unknown_group_does_not_raise(repo_tmp):
    repo_tmp.delete_group("does-not-exist")  # should simply no-op
