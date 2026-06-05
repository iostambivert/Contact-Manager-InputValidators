import sqlite3
from typing import List, Optional
from contact_repository import ContactRepository
from contact import Contact

CREATE_GROUPS_TABLE = """
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
"""

CREATE_CONTACTS_TABLE = """
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    group_id INTEGER NOT NULL,
    FOREIGN KEY(group_id) REFERENCES groups(id)
);
"""

class SqliteContactRepository(ContactRepository):
    def __init__(self, db_path: str = "contacts.db"):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_tables()
        # ensure meta group exists
        self.ensure_group("ungrouped")

    def _ensure_tables(self) -> None:
        with self._conn:
            self._conn.execute(CREATE_GROUPS_TABLE)
            self._conn.execute(CREATE_CONTACTS_TABLE)

    def _row_to_contact(self, row: sqlite3.Row) -> Contact:
        group_name = self._get_group_name(row["group_id"])
        return Contact(row["id"], row["first_name"], row["last_name"], row["email"], row["phone"], group_name)

    def _get_group_name(self, group_id: int) -> str:
        cur = self._conn.execute("SELECT name FROM groups WHERE id = ?", (group_id,))
        r = cur.fetchone()
        return r["name"] if r else "ungrouped"

    def list_groups(self) -> List[str]:
        cur = self._conn.execute("SELECT name FROM groups ORDER BY name COLLATE NOCASE")
        return [r["name"] for r in cur.fetchall()]

    def ensure_group(self, group: str) -> int:
        group = group.strip()
        if not group:
            group = "ungrouped"
        #try to find by case insensitive
        cur = self._conn.execute("SELECT id, name FROM groups WHERE lower(name)=lower(?)", (group,))
        row = cur.fetchone()
        if row:
            return row["id"]
        with self._conn:
            cur = self._conn.execute("INSERT INTO groups (name) VALUES (?)", (group,))
            return cur.lastrowid

    def _group_id_for(self, group: str) -> int:
        return self.ensure_group(group)

    def find_by_id(self, id: int) -> Optional[Contact]:
        cur = self._conn.execute("SELECT * FROM contacts WHERE id = ?", (id,))
        row = cur.fetchone()
        return self._row_to_contact(row) if row else None

    def find_all(self) -> List[Contact]:
        cur = self._conn.execute("SELECT * FROM contacts ORDER BY id")
        return [self._row_to_contact(r) for r in cur.fetchall()]

    def find_by_name(self, name: str) -> List[Contact]:
        pattern = f"%{name}%"
        cur = self._conn.execute(
            "SELECT c.* FROM contacts c JOIN groups g ON c.group_id=g.id "
            "WHERE lower(c.first_name || ' ' || c.last_name) LIKE lower(?) ORDER BY c.id",
            (pattern,)
        )
        return [self._row_to_contact(r) for r in cur.fetchall()]

    def find_by_phone(self, phone: str) -> List[Contact]:
        pattern = f"%{phone}%"
        cur = self._conn.execute(
            "SELECT c.* FROM contacts c WHERE lower(c.phone) LIKE lower(?) ORDER BY c.id",
            (pattern,)
        )
        return [self._row_to_contact(r) for r in cur.fetchall()]

    def find_by_group(self, group: str) -> List[Contact]:
        # case insensitive group match
        cur = self._conn.execute(
            "SELECT c.* FROM contacts c JOIN groups g ON c.group_id=g.id "
            "WHERE lower(g.name) = lower(?) ORDER BY c.id",
            (group.strip(),)
        )
        return [self._row_to_contact(r) for r in cur.fetchall()]

    def save(self, contact: Contact) -> None:
        group_id = self._group_id_for(contact.get_group() or "ungrouped")
        if contact.get_id() is None:
            with self._conn:
                cur = self._conn.execute(
                    "INSERT INTO contacts (first_name, last_name, email, phone, group_id) VALUES (?, ?, ?, ?, ?)",
                    (contact.get_first_name(), contact.get_last_name(),
                     contact.get_email(), contact.get_phone(), group_id)
                )
                contact._id = cur.lastrowid
        else:
            with self._conn:
                cur = self._conn.execute("SELECT 1 FROM contacts WHERE id = ?", (contact.get_id(),))
                if cur.fetchone():
                    self._conn.execute(
                        "UPDATE contacts SET first_name=?, last_name=?, email=?, phone=?, group_id=? WHERE id=?",
                        (contact.get_first_name(), contact.get_last_name(),
                         contact.get_email(), contact.get_phone(), group_id, contact.get_id())
                    )
                else:
                    self._conn.execute(
                        "INSERT INTO contacts (id, first_name, last_name, email, phone, group_id) VALUES (?, ?, ?, ?, ?, ?)",
                        (contact.get_id(), contact.get_first_name(), contact.get_last_name(),
                         contact.get_email(), contact.get_phone(), group_id)
                    )

    def delete(self, id: int) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM contacts WHERE id = ?", (id,))

    def close(self) -> None:
        self._conn.close()

