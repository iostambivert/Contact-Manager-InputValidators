"""
test_contact_service.py - Unit tests for ContactService
Person 4: Tests & project setup
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from sqlite_contact_repository import SqliteContactRepository
from contact_service import ContactService


class TestContactService(unittest.TestCase):

    def setUp(self):
        """Create a fresh service with an in-memory repo before each test."""
        self.repo = SqliteContactRepository()
        self.service = ContactService(self.repo)

    # ------------------------------------------------------------------ #
    #  add_contact
    # ------------------------------------------------------------------ #

    def test_add_contact_success(self):
        c = self.service.add_contact("Alice", "Smith", "alice@example.com", "555123456")
        self.assertEqual(c.get_full_name(), "Alice Smith")
        self.assertEqual(c.get_email(), "alice@example.com")
        self.assertIsNotNone(c.get_id())   # id assigned by repo, not fixed to 1

    def test_add_contact_increments_id(self):
        c1 = self.service.add_contact("Alice", "Smith", "alice@example.com", "555123456")
        c2 = self.service.add_contact("Bob", "Jones", "bob@example.com", "555123457")
        self.assertNotEqual(c1.get_id(), c2.get_id())

    def test_add_contact_empty_first_name_raises(self):
        with self.assertRaises(ValueError):
            self.service.add_contact("", "Smith", "alice@example.com", "555123456")

    def test_add_contact_empty_email_raises(self):
        # empty string is not a valid email — service should raise
        with self.assertRaises(ValueError):
            self.service.add_contact("Alice", "Smith", "", "555123456")

    def test_add_contact_none_email_stored_as_unset(self):
        # None email is normalised to "unset" — no error raised
        c = self.service.add_contact("Alice", "Smith", None, "555123456")
        self.assertEqual(c.get_email(), "unset")

    def test_add_contact_none_phone_stored_as_unset(self):
        c = self.service.add_contact("Alice", "Smith", "alice@example.com", None)
        self.assertEqual(c.get_phone(), "unset")

    def test_add_contact_invalid_email_raises(self):
        with self.assertRaises(ValueError):
            self.service.add_contact("Alice", "Smith", "not-an-email", "555123456")

    def test_add_contact_valid_email_formats(self):
        c = self.service.add_contact("A", "B", "a.b+tag@sub.domain.org", "500000123")
        self.assertIsNotNone(c)

    def test_add_contact_default_group_is_ungrouped(self):
        c = self.service.add_contact("Alice", "Smith", "alice@example.com", "555123456")
        self.assertEqual(c.get_group(), "ungrouped")

    def test_add_contact_custom_group(self):
        c = self.service.add_contact("Alice", "Smith", "alice@example.com", "555123456", "Friends")
        self.assertEqual(c.get_group(), "Friends")

    def test_add_contact_blank_group_defaults_to_ungrouped(self):
        c = self.service.add_contact("Alice", "Smith", "alice@example.com", "555123456", "   ")
        self.assertEqual(c.get_group(), "ungrouped")

    # ------------------------------------------------------------------ #
    #  update_contact
    # ------------------------------------------------------------------ #

    def test_update_contact_success(self):
        c = self.service.add_contact("Alice", "Smith", "alice@example.com", "555123456")
        c.set_email("new@example.com")
        self.service.update_contact(c)
        fetched = self.service.get_contact_by_id(c.get_id())
        self.assertEqual(fetched.get_email(), "new@example.com")

    def test_update_nonexistent_contact_raises(self):
        from contact import Contact
        ghost = Contact(999, "Ghost", "User", "g@g.com", "500000000")
        with self.assertRaises(ValueError):
            self.service.update_contact(ghost)

    # ------------------------------------------------------------------ #
    #  delete_contact
    # ------------------------------------------------------------------ #

    def test_delete_contact_success(self):
        c = self.service.add_contact("Alice", "Smith", "alice@example.com", "555123456")
        self.service.delete_contact(c.get_id())
        self.assertEqual(len(self.service.get_all_contacts()), 0)

    def test_delete_nonexistent_raises(self):
        with self.assertRaises(ValueError):
            self.service.delete_contact(999)

    # ------------------------------------------------------------------ #
    #  search_by_name
    # ------------------------------------------------------------------ #

    def test_search_by_name_found(self):
        self.service.add_contact("Alice", "Smith", "alice@example.com", "500000001")
        self.service.add_contact("Bob", "Jones", "bob@example.com", "500000002")
        results = self.service.search_by_name("alice")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].get_first_name(), "Alice")

    def test_search_by_name_case_insensitive(self):
        self.service.add_contact("Alice", "Smith", "alice@example.com", "500000001")
        results = self.service.search_by_name("ALICE")
        self.assertEqual(len(results), 1)

    def test_search_by_name_no_results(self):
        self.service.add_contact("Alice", "Smith", "alice@example.com", "500000001")
        results = self.service.search_by_name("zzz")
        self.assertEqual(len(results), 0)

    def test_search_empty_query_raises(self):
        with self.assertRaises(ValueError):
            self.service.search_by_name("")
    
    # ------------------------------------------------------------------ #
    # search_by_phone
    # ------------------------------------------------------------------ #

    def test_search_by_phone_found(self):
        self.service.add_contact("Alice", "Smith", "alice@example.com", "500000001")
        results = self.service.search_by_phone("500000001")
        self.assertEqual(len(results), 1)

    def test_search_by_phone_empty_raises(self):
        with self.assertRaises(ValueError):
            self.service.search_by_phone("")
    
    # ------------------------------------------------------------------ #
    # search_by_group
    # ------------------------------------------------------------------ #

    def test_search_by_group_found(self):
        self.service.add_contact("Alice", "Smith", "alice@example.com", "500000001", "Friends")
        results = self.service.search_by_group("Friends")
        self.assertEqual(len(results), 1)

    def test_search_by_group_empty_raises(self):
        with self.assertRaises(ValueError):
            self.service.search_by_group("")

    def test_search_by_group_no_match(self):
        self.service.add_contact("Alice", "Smith", "alice@example.com", "500000001", "Friends")
        results = self.service.search_by_group("Work")
        self.assertEqual(len(results), 0)

    # ------------------------------------------------------------------ #
    #  get_all_contacts
    # ------------------------------------------------------------------ #

    def test_get_all_contacts_empty(self):
        self.assertEqual(self.service.get_all_contacts(), [])

    def test_get_all_contacts_returns_all(self):
        self.service.add_contact("A", "A", "a@a.com", "500000001")
        self.service.add_contact("B", "B", "b@b.com", "500000002")
        self.assertEqual(len(self.service.get_all_contacts()), 2)

    # ------------------------------------------------------------------ #
    # list_groups
    # ------------------------------------------------------------------ #

    def test_list_groups_returns_existing_groups(self):
        self.service.add_contact("Alice", "Smith", "alice@example.com", "500000001", "Friends")
        self.service.add_contact("Bob",   "Jones", "bob@example.com",   "500000002", "Work")
        groups = self.service.list_groups()
        self.assertIn("Friends", groups)
        self.assertIn("Work", groups)


if __name__ == "__main__":
    unittest.main(verbosity=2)