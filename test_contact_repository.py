"""
test_contact_repository.py - Unit tests for InMemoryContactRepository
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from contact import Contact
from in_memory_contact_repository import InMemoryContactRepository


def make_contact(id=1, first="Alice", last="Smith",
                 email="alice@example.com", phone="555-0001") -> Contact:
    return Contact(id, first, last, email, phone)


class TestInMemoryContactRepository(unittest.TestCase):

    def setUp(self):
        self.repo = InMemoryContactRepository()

    # ------------------------------------------------------------------ #
    #  save / find_by_id
    # ------------------------------------------------------------------ #

    def test_save_and_find_by_id(self):
        c = make_contact(id=1)
        self.repo.save(c)
        found = self.repo.find_by_id(1)
        self.assertIsNotNone(found)
        self.assertEqual(found.get_id(), 1)

    def test_find_by_id_not_found_returns_none(self):
        result = self.repo.find_by_id(999)
        self.assertIsNone(result)

    def test_save_updates_existing(self):
        c = make_contact(id=1)
        self.repo.save(c)
        c.set_email("updated@example.com")
        self.repo.save(c)
        self.assertEqual(self.repo.find_by_id(1).get_email(), "updated@example.com")

    # ------------------------------------------------------------------ #
    #  find_all
    # ------------------------------------------------------------------ #

    def test_find_all_empty(self):
        self.assertEqual(self.repo.find_all(), [])

    def test_find_all_returns_all(self):
        self.repo.save(make_contact(id=1, first="Alice"))
        self.repo.save(make_contact(id=2, first="Bob", email="bob@b.com"))
        self.assertEqual(len(self.repo.find_all()), 2)

    # ------------------------------------------------------------------ #
    #  find_by_name
    # ------------------------------------------------------------------ #

    def test_find_by_name_match(self):
        self.repo.save(make_contact(id=1, first="Alice", last="Smith"))
        results = self.repo.find_by_name("alice")
        self.assertEqual(len(results), 1)

    def test_find_by_name_partial_match(self):
        self.repo.save(make_contact(id=1, first="Alice", last="Smith"))
        results = self.repo.find_by_name("Smi")
        self.assertEqual(len(results), 1)

    def test_find_by_name_no_match(self):
        self.repo.save(make_contact(id=1, first="Alice", last="Smith"))
        results = self.repo.find_by_name("xyz")
        self.assertEqual(len(results), 0)

    def test_find_by_name_case_insensitive(self):
        self.repo.save(make_contact(id=1, first="Alice", last="Smith"))
        results = self.repo.find_by_name("SMITH")
        self.assertEqual(len(results), 1)

    # ------------------------------------------------------------------ #
    #  delete
    # ------------------------------------------------------------------ #

    def test_delete_existing(self):
        self.repo.save(make_contact(id=1))
        self.repo.delete(1)
        self.assertIsNone(self.repo.find_by_id(1))

    def test_delete_nonexistent_is_noop(self):
        """Deleting a missing id should not raise any error."""
        try:
            self.repo.delete(999)
        except Exception as e:
            self.fail(f"delete raised unexpectedly: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
