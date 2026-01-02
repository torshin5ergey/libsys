# frontend app.py

from nicegui import ui

from common.env_checker import check_env
from books_tab import create_books_tab
from readers_tab import create_readers_tab
from loans_tab import create_loans_tab
from system_tab import create_system_tab

# ==============================================================================
vars_to_check = [
    "BOOKS_SERVICE_API_URL",
    "MONITOR_SERVICE_API_URL",
    "READERS_SERVICE_API_URL",
    "LOANS_SERVICE_API_URL"
]
# ==============================================================================


def main():
    # tabs
    tabs = ui.tabs().classes("w-full")

    with tabs:
        ui.tab("Книги")
        ui.tab("Читатели")
        ui.tab("Выдачи")
        ui.tab("Система")

    with ui.tab_panels(tabs, value="Система").classes("flex-grow w-full"):
        # books
        with ui.tab_panel("Книги"):
            create_books_tab()

        # readers
        with ui.tab_panel("Читатели"):
            create_readers_tab()

        # loans
        with ui.tab_panel("Выдачи"):
            create_loans_tab()

        # system
        with ui.tab_panel("Система"):
            create_system_tab()

    ui.query(".nicegui-content").classes("flex")

if __name__ in {"__main__", "__mp_main__"}:
    check_env(vars_to_check)
    ui.run(main, title="ИС Библиотека", port=8080, host="0.0.0.0")
