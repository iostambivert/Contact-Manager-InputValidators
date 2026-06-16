# main.py
import sys
from PyQt6 import QtWidgets
from sqlite_contact_repository import SqliteContactRepository
from contact_service import ContactService
from ui import UiWindow
from gui_controller import GuiController

def build_app(db_path: str = "contacts.db"):
    repo = SqliteContactRepository(db_path)
    service = ContactService(repo)
    return repo, service

def main():
    app = QtWidgets.QApplication(sys.argv)
    repo, service = build_app("contacts.db")

    view = UiWindow()
    controller = GuiController(service=service, view=view)

    controller.refresh_list()    # initial population
    view.show()
    exit_code = app.exec()
    repo.close()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
