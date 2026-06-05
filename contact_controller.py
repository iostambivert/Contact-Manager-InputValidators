from contact_service import ContactService

class ContactController:
    def __init__(self, service: ContactService):
        self._service = service

    @staticmethod
    def _print_header(title: str) -> None:
        print(f"\n{'=' * 50}")
        print(f"  {title}")
        print('=' * 50)

    @staticmethod
    def _print_contact(contact) -> None:
        print(f"  [{contact.get_id()}] {contact.get_full_name()}  (Group: {contact.get_group()})")
        print(f"      Email : {contact.get_email()}")
        print(f"      Phone : {contact.get_phone()}")

    def show_all(self) -> None:
        self._print_header("All Contacts")
        contacts = self._service.get_all_contacts()
        if not contacts:
            print("No contacts found.")
        else:
            for c in contacts:
                self._print_contact(c)
                print()

    def create(self) -> None:
        self._print_header("Add New Contact")
        try:
            first_name = input("  First name : ").strip()
            last_name  = input("  Last name  : ").strip()
            email      = input("  Email      : ").strip()
            phone      = input("  Phone      : ").strip()

            # group selection
            groups = self._service.list_groups()
            print("\nExisting groups:")
            for i, g in enumerate(groups, start=1):
                print(f"  {i}. {g}")
            print(f"  {len(groups)+1}. Create new group")

            choice = input(f"Choose group [1-{len(groups)+1}] (default 1): ").strip()
            group = None
            try:
                idx = int(choice) if choice else 1
                if idx == len(groups) + 1:
                    newg = input("  New group name: ").strip()
                    group = newg if newg else "ungrouped"
                else:
                    group = groups[max(0, idx-1)]
            except Exception:
                group = "ungrouped"

            contact = self._service.add_contact(first_name, last_name, email, phone, group)
            print(f"\nContact added: {contact.get_full_name()} (id={contact.get_id()})")
        except ValueError as e:
            print(f"\nError: {e}")

    def edit(self, id: int) -> None:
        self._print_header(f"Edit Contact (id={id})")
        try:
            contact = self._service.get_contact_by_id(id)
            print(f"Editing: {contact.get_full_name()}")
            print("(Press Enter to keep current value)\n")

            first = input(f"  First name [{contact.get_first_name()}]: ").strip()
            last  = input(f"  Last name  [{contact.get_last_name()}]: ").strip()
            email = input(f"  Email      [{contact.get_email()}]: ").strip()
            phone = input(f"  Phone      [{contact.get_phone()}]: ").strip()

            # group editing
            groups = self._service.list_groups()
            print("\nExisting groups:")
            for i, g in enumerate(groups, start=1):
                print(f"  {i}. {g}")
            print(f"  {len(groups)+1}. Create new group")
            grp_choice = input(f"Choose group [1-{len(groups)+1}] (current '{contact.get_group()}'): ").strip()
            try:
                if grp_choice:
                    idx = int(grp_choice)
                    if idx == len(groups) + 1:
                        newg = input("  New group name: ").strip()
                        contact.set_group(newg if newg else contact.get_group())
                    else:
                        contact.set_group(groups[max(0, idx-1)])
            except Exception:
                pass

            if first:
                contact.set_first_name(first)
            if last:
                contact.set_last_name(last)
            if email:
                contact.set_email(email)
            if phone:
                contact.set_phone(phone)

            self._service.update_contact(contact)
            print(f"\nContact updated: {contact.get_full_name()}")
        except ValueError as e:
            print(f"\nError: {e}")

    def delete(self, id: int) -> None:
        self._print_header(f"Delete Contact (id={id})")
        try:
            contact = self._service.get_contact_by_id(id)
            confirm = input(f"  Delete '{contact.get_full_name()}'? (y/n): ").strip().lower()
            if confirm == 'y':
                self._service.delete_contact(id)
                print(f"\nContact deleted.")
            else:
                print("Cancelled.")
        except ValueError as e:
            print(f"\nError: {e}")

    def search(self, mode: str, query: str) -> None:
        try:
            q = query.strip().lower()
            # fetch all and filter in-memory so we can search any attribute
            all_contacts = self._service.get_all_contacts()

            if mode == "name":
                results = [c for c in all_contacts if q in c.get_full_name().lower()]
            elif mode == "first":
                results = [c for c in all_contacts if q in c.get_first_name().lower()]
            elif mode == "last":
                results = [c for c in all_contacts if q in c.get_last_name().lower()]
            elif mode == "email":
                results = [c for c in all_contacts if q in c.get_email().lower()]
            elif mode == "number":
                results = [c for c in all_contacts if q in c.get_phone().lower()]
            elif mode == "group":
                results = [c for c in all_contacts if q in c.get_group().lower()]
            else:
                print("Unknown search mode.")
                return

            self._print_header(f"Search Results for '{query}' by {mode}")
            if not results:
                print("  No contacts matched.")
            else:
                for c in results:
                    self._print_contact(c)
                    print()
        except ValueError as e:
            print(f"\nError: {e}")

    def query_by_prompt(self) -> None:
        self._print_header("Query By...")
        options = [
            ("name", "Full name"),
            ("first", "First name"),
            ("last", "Last name"),
            ("email", "Email"),
            ("number", "Phone number"),
            ("group", "Group"),
        ]
        for i, (_, label) in enumerate(options, start=1):
            print(f"  {i}. {label}")
        choice = input(f"Choose option [1-{len(options)}]: ").strip()
        try:
            idx = int(choice) if choice else 1
            mode = options[max(0, idx-1)][0]
            term = input("Enter query term: ").strip()
            if term:
                self.search(mode, term)
            else:
                print("Query term cannot be empty.")
        except Exception:
            print("Invalid selection.")

