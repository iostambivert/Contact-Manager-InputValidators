# test_add_a_buncha_contacts.py
import random
import sqlite3
from contact_service import ContactService
from contact import Contact
from sqlite_contact_repository import SqliteContactRepository

first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
groups = ["friends", "family", "work", "gym", "school", "neighbors", None]
domains = ["example.com", "mail.com", "test.org", "demo.net"]

def rand_phone():
    formats = [
        lambda: f"+1-{random.randint(200,999)}-{random.randint(200,999)}-{random.randint(1000,9999)}",
        lambda: f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}",
        lambda: f"{random.randint(1000000000,9999999999)}",
        lambda: ""
    ]
    return random.choice(formats)()

def rand_email(first, last):
    if random.random() < 0.06:
        return "invalid-email"
    if random.random() < 0.05:
        return ""
    return f"{first.lower()}.{last.lower()}{random.randint(1,999)}@{random.choice(domains)}"

def generate_contact():
    first = random.choice(first_names)
    last = random.choice(last_names)
    return first, last, rand_email(first, last), rand_phone(), random.choice(groups)

def main(count=1000, db_path="contacts.db"):
    repo = SqliteContactRepository(db_path)
    service = ContactService(repo)

    added = 0
    skipped = 0
    for _ in range(count):
        first, last, email, phone, group = generate_contact()
        try:
            service.add_contact(first, last, email, phone, group)
            added += 1
        except ValueError:
            skipped += 1

    print(f"Requested: {count}, Added: {added}, Skipped (validation errors): {skipped}")
    print(f"Total in DB: {len(service.get_all_contacts())}")
    # sample output
    for c in service.get_contacts_sorted_by("id")[:10]:
        print(f"{c.get_id()}\t{c.get_first_name()} {c.get_last_name()}\t{c.get_email()}\t{c.get_phone()}\t{c.get_group()}")

if __name__ == "__main__":
    main(count=1000)

