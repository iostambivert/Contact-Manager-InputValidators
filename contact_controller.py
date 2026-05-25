from contact_service import ContactService


class ContactController:
    """
    Translates raw user input into ContactService calls and formats output.
    """

    def __init__(self, service: ContactService):
        self._service = service

    #display helpers
    @staticmethod
    def _print_header(title: str) -> None:
        print(f"\n{'=' * 50}")
        print(f"  {title}")
        print('=' * 50)

    @staticmethod
    def _print_contact(contact) -> None:
        print(f"  [{contact.get_id()}] {contact.get_full_name()}")
        print(f"      Email : {contact.get_email()}")
        print(f"      Phone : {contact.get_phone()}")

    #actions

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
            contact = self._service.add_contact(first_name, last_name, email, phone)
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

    def search(self, query: str) -> None:
        self._print_header(f"Search Results for '{query}'")
        try:
            results = self._service.search_by_name(query)
            if not results:
                print("  No contacts matched.")
            else:
                for c in results:
                    self._print_contact(c)
                    print()
        except ValueError as e:
            print(f"\nError: {e}")
