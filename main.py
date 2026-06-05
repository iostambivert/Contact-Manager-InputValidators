from sqlite_contact_repository import SqliteContactRepository
from contact_service import ContactService
from contact_controller import ContactController


def print_menu() -> None:
    print("\n_____________________________")
    print("|     CONTACT MANAGER v1.0    |")
    print("|_____________________________|")
    print("|  1. Show all contacts       |")
    print("|  2. Add new contact         |")
    print("|  3. Edit contact            |")
    print("|  4. Delete contact          |")
    print("|  5. Query by...             |")
    print("|  0. Exit                    |")
    print("|_____________________________|")

def main() -> None:
    repository = SqliteContactRepository("contacts.db")
    service    = ContactService(repository)
    controller = ContactController(service)

    print("\n  Welcome to Contact Manager")

    while True:
        print_menu()
        choice = input("Choose an option: ").strip()

        if choice == '1':
            controller.show_all()
        elif choice == '2':
            controller.create()
        elif choice == '3':
            try:
                id = int(input("Enter contact ID to edit: ").strip())
                controller.edit(id)
            except ValueError:
                print("Please enter a valid numeric ID.")
        elif choice == '4':
            try:
                id = int(input("Enter contact ID to delete: ").strip())
                controller.delete(id)
            except ValueError:
                print("Please enter a valid numeric ID.")
        elif choice == '5':
            controller.query_by_prompt()
        elif choice == '0':
            print("\n  Goodbye!\n")
            repository.close()
            break
        else:
            print("Invalid option. Please choose 0–5.")

if __name__ == "__main__":
    main()

