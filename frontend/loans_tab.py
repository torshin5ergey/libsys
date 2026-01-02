# frontend loans_tab.py

import os
import requests
from datetime import datetime, timedelta

from nicegui import ui


def create_loans_tab():
    loans = []
    available_books = []
    readers = []
    editing_loan = None

    add_dialog = None
    edit_dialog = None
    loans_container = None
    search_input = None

    def load_loans():
        """Загрузить аренды из API"""
        nonlocal loans
        try:
            search = search_input.value.strip() if search_input else ''
            status = status_filter.value if status_filter else ''

            url = f"{os.getenv('LOANS_SERVICE_API_URL')}/api/loans"
            params = []

            if search:
                params.append(f"search={search}")
            if status:
                params.append(f"status={status}")
            if params:
                url = f"{url}?{'&'.join(params)}"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                loans = data.get('loans', [])
                update_loans_list()
            else:
                ui.notify(f'Ошибка загрузки: {response.status_code}', type='negative')
                loans = []
                update_loans_list()
        except Exception as e:
            ui.notify(f'Ошибка: {str(e)}', type='negative')
            loans = []
            update_loans_list()

    def load_available_books():
        """Загрузить доступные для аренды книги"""
        try:
            response = requests.get(
                f"{os.getenv('LOANS_SERVICE_API_URL')}/api/books/available",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('books', [])
        except:
            pass
        return []

    def load_all_readers():
        """Загрузить всех читателей"""
        try:
            response = requests.get(
                f"{os.getenv('READERS_SERVICE_API_URL')}/api/readers",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('readers', [])
        except:
            pass
        return []

    def show_add_dialog():
        """Показать диалоговое окно добавления аренды"""
        nonlocal available_books, readers
        available_books = load_available_books()
        readers = load_all_readers()

        with ui.dialog() as dialog, ui.card().classes('w-full max-w-md'):
            nonlocal add_dialog
            add_dialog = dialog

            ui.label('Выдать книгу в аренду').classes('text-h6 mb-4')

            with ui.column().classes('w-full gap-3'):
                # available books list
                book_options = {None: 'Выберите книгу'}
                for book in available_books:
                    book_options[book['id']] = f"{book['title']} - {book['author']}"

                book_select = ui.select(
                    label='Книга *',
                    options=book_options,
                    value=None
                ).classes('w-full')

                # readers list
                reader_options = {None: 'Выберите читателя'}
                for reader in readers:
                    reader_options[reader['id']] = reader['full_name']

                reader_select = ui.select(
                    label='Читатель *',
                    options=reader_options,
                    value=None
                ).classes('w-full')

                # due date
                default_due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                due_date_input = ui.input('Дата возврата').classes('w-full')
                due_date_input.value = default_due_date
                due_date_input.props('type=date')

                with ui.row().classes('w-full justify-between pt-4'):
                    ui.button('Отмена', on_click=lambda: add_dialog.close()).props('flat')
                    ui.button('Выдать', on_click=lambda: create_loan(
                        book_select, reader_select, due_date_input
                    ), color='primary').props('flat')

        add_dialog.open()

    def create_loan(book_select, reader_select, due_date_input):
        """Создать новую аренду"""
        book_id = book_select.value
        reader_id = reader_select.value
        due_date = due_date_input.value

        if not book_id or book_id == 'None':
            ui.notify('Выберите книгу', type='warning')
            return

        if not reader_id or reader_id == 'None':
            ui.notify('Выберите читателя', type='warning')
            return

        try:
            data = {
                'book_id': book_id,
                'reader_id': reader_id,
                'due_date': due_date
            }

            response = requests.post(
                f"{os.getenv('LOANS_SERVICE_API_URL')}/api/loans",
                json=data,
                timeout=10
            )

            if response.status_code == 201:
                ui.notify('Книга успешно выдана в аренду', type='positive')
                add_dialog.close()
                load_loans()
            else:
                error_data = response.json()
                error_msg = error_data.get('error', 'Неизвестная ошибка')
                ui.notify(f'Ошибка: {error_msg}', type='negative')

        except requests.exceptions.ConnectionError:
            ui.notify('Не удалось подключиться к серверу', type='negative')
        except Exception as e:
            ui.notify(f'Ошибка: {str(e)}', type='negative')

    def show_edit_dialog(loan):
        """Показать диалоговое окно редактирования аренды"""
        nonlocal editing_loan, edit_dialog
        editing_loan = loan.copy()

        with ui.dialog() as dialog, ui.card().classes('w-full max-w-md'):
            edit_dialog = dialog

            ui.label('Редактировать аренду').classes('text-h6 mb-4')

            with ui.column().classes('w-full gap-3'):
                # book info
                ui.label(f"Книга: {loan.get('book_title', '—')}").classes('font-medium')
                ui.label(f"Автор: {get_book_author(loan.get('book_id'))}").classes('text-gray-600')

                # reader info
                ui.label(f"Читатель: {loan.get('reader_name', '—')}").classes('text-gray-600')

                # loan date
                ui.label(f"Дата выдачи: {loan.get('loan_date', '—')[:10]}").classes('text-gray-600')

                # due date
                due_date_input = ui.input('Дата возврата').classes('w-full')
                if loan.get('due_date'):
                    due_date_input.value = loan['due_date'][:10] if loan['due_date'] else ''
                due_date_input.props('type=date')

                # status
                status_options = {
                    'active': 'Активная',
                    'overdue': 'Просрочена',
                    'returned': 'Возвращена'
                }
                status_select = ui.select(
                    label='Статус',
                    options=status_options,
                    value=loan.get('status', 'active')
                ).classes('w-full')

                return_date_input = ui.input('Дата возврата (если книга возвращена)').classes('w-full')
                if loan.get('return_date'):
                    return_date_input.value = loan['return_date'][:10] if loan['return_date'] else ''
                return_date_input.props('type=date')

                # action buttons
                with ui.row().classes('w-full justify-between pt-4'):
                    ui.button('Удалить',
                            on_click=lambda: delete_loan(loan['id'], loan['book_title'], close_edit_dialog=True),
                            color='red').props('flat')
                    with ui.row().classes('gap-2'):
                        ui.button('Отмена', on_click=lambda: edit_dialog.close()).props('flat')
                        ui.button('Сохранить', on_click=lambda: update_loan(
                            due_date_input, status_select, return_date_input
                        ), color='primary').props('flat')

        edit_dialog.open()

    def get_book_author(book_id):
        """Получить автора книги по ID"""
        try:
            response = requests.get(
                f"{os.getenv('BOOKS_SERVICE_API_URL')}/api/books/{book_id}",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('author', 'Неизвестно')
        except:
            pass
        return 'Неизвестно'

    def update_loan(due_date_input, status_select, return_date_input):
        """Обновить информацию об аренде"""
        if not editing_loan:
            return

        due_date = due_date_input.value.strip()
        status = status_select.value
        return_date = return_date_input.value.strip() if return_date_input.value else None

        try:
            data = {
                'due_date': due_date,
                'status': status
            }

            if return_date:
                data['return_date'] = return_date
            elif status == 'returned' and not return_date:
                data['return_date'] = datetime.now().strftime('%Y-%m-%d')
            else:
                data['return_date'] = None

            response = requests.put(
                f"{os.getenv('LOANS_SERVICE_API_URL')}/api/loans/{editing_loan['id']}",
                json=data,
                timeout=10
            )

            if response.status_code == 200:
                ui.notify('Аренда успешно обновлена', type='positive')
                edit_dialog.close()
                load_loans()
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Неизвестная ошибка')
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                ui.notify(f'Ошибка: {error_msg}', type='negative')

        except requests.exceptions.ConnectionError:
            ui.notify('Не удалось подключиться к серверу', type='negative')
        except Exception as e:
            ui.notify(f'Ошибка: {str(e)}', type='negative')

    def delete_loan(loan_id, book_title, close_edit_dialog=True):
        """Удалить аренду с подтверждением"""
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-sm'):
            ui.label('Удалить запись об аренде?').classes('text-h6 mb-2')
            ui.label(f'"{book_title}"').classes('text-center mb-4 font-medium')
            ui.label('Это действие нельзя отменить').classes('text-red-500 text-sm text-center mb-4')

            with ui.row().classes('w-full justify-center gap-4'):
                ui.button('Отмена', on_click=dialog.close).props('flat')
                ui.button('Удалить',
                         on_click=lambda: confirm_delete(loan_id, book_title, dialog, close_edit_dialog),
                         color='red').props('flat')
            dialog.open()

    def confirm_delete(loan_id, book_title, dialog, close_edit_dialog=True):
        """Подтвержденное удаление аренды"""
        try:
            response = requests.delete(
                f"{os.getenv('LOANS_SERVICE_API_URL')}/api/loans/{loan_id}",
                timeout=10
            )

            if response.status_code == 200:
                ui.notify('Запись об аренде успешно удалена', type='positive')
                dialog.close()
                if close_edit_dialog and edit_dialog:
                    edit_dialog.close()
                load_loans()
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Неизвестная ошибка')
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                ui.notify(f'Ошибка: {error_msg}', type='negative')

        except requests.exceptions.ConnectionError:
            ui.notify('Не удалось подключиться к серверу', type='negative')
        except Exception as e:
            ui.notify(f'Ошибка: {str(e)}', type='negative')

    def return_book(loan_id, book_title):
        """Вернуть книгу"""
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-sm'):
            ui.label('Вернуть книгу?').classes('text-h6 mb-2')
            ui.label(f'"{book_title}"').classes('text-center mb-4 font-medium')

            with ui.row().classes('w-full justify-center gap-4'):
                ui.button('Отмена', on_click=dialog.close).props('flat')
                ui.button('Вернуть',
                         on_click=lambda: confirm_return(loan_id, book_title, dialog),
                         color='primary').props('flat')
            dialog.open()

    def confirm_return(loan_id, book_title, dialog):
        """Подтвержденный возврат книги"""
        try:
            response = requests.post(
                f"{os.getenv('LOANS_SERVICE_API_URL')}/api/loans/{loan_id}/return",
                timeout=10
            )

            if response.status_code == 200:
                ui.notify('Книга успешно возвращена', type='positive')
                dialog.close()
                load_loans()
            else:
                error_data = response.json()
                error_msg = error_data.get('error', 'Неизвестная ошибка')
                ui.notify(f'Ошибка: {error_msg}', type='negative')

        except requests.exceptions.ConnectionError:
            ui.notify('Не удалось подключиться к серверу', type='negative')
        except Exception as e:
            ui.notify(f'Ошибка: {str(e)}', type='negative')

    def edit_selected_loan(aggrid):
        """Редактировать выбранную аренду"""
        async def get_selection():
            try:
                selection = await aggrid.run_grid_method('getSelectedRows')
                if selection and len(selection) > 0:
                    selected_loan = selection[0]
                    if '_actions' in selected_loan:
                        show_edit_dialog(selected_loan['_actions'])
                    else:
                        show_edit_dialog(selected_loan)
                else:
                    ui.notify('Выберите аренду для редактирования', type='warning')
            except Exception as e:
                ui.notify(f'Ошибка: {str(e)}', type='negative')

        ui.timer(0.1, get_selection, once=True)

    def delete_selected_loan(aggrid):
        """Удалить выбранную аренду"""
        async def get_selection():
            try:
                selection = await aggrid.run_grid_method('getSelectedRows')
                if selection and len(selection) > 0:
                    selected_loan = selection[0]
                    loan_data = selected_loan.get('_actions', selected_loan)
                    delete_loan(loan_data['id'], loan_data['book_title'], close_edit_dialog=False)
                else:
                    ui.notify('Выберите аренду для удаления', type='warning')
            except Exception as e:
                ui.notify(f'Ошибка: {str(e)}', type='negative')

        ui.timer(0.1, get_selection, once=True)

    def update_loans_list():
        """Обновить отображение списка аренд"""
        if loans_container:
            loans_container.clear()

            with loans_container:
                if not loans:
                    with ui.row().classes('w-full justify-center p-8'):
                        ui.icon('book', size='xl').classes('text-gray-400')
                        ui.label('Аренды не найдены').classes('text-gray-500 text-lg')
                    return

                # create table
                try:
                    # action buttons
                    with ui.row().classes('w-full justify-end gap-2 mb-4'):
                        ui.button(
                            'Редактировать выбранное',
                            on_click=lambda: edit_selected_loan(aggrid),
                            icon='edit',
                            color='primary'
                        ).props('flat')

                        ui.button(
                            'Удалить выбранное',
                            on_click=lambda: delete_selected_loan(aggrid),
                            icon='delete',
                            color='negative'
                        ).props('flat')

                    # table columns
                    columns = [
                        {'headerName': 'Книга', 'field': 'book_title', 'sortable': True, 'filter': True},
                        {'headerName': 'Читатель', 'field': 'reader_name', 'sortable': True, 'filter': True},
                        {'headerName': 'Дата выдачи', 'field': 'loan_date', 'sortable': True, 'width': 120},
                        {'headerName': 'Срок возврата', 'field': 'due_date', 'sortable': True, 'width': 120},
                        {'headerName': 'Статус', 'field': 'status_display', 'sortable': True, 'width': 150},
                        {'headerName': 'Дата возврата', 'field': 'return_date', 'sortable': True, 'width': 120},
                    ]

                    rows = []
                    for loan in loans:
                        status_text = loan['status']
                        status_display = {
                            'active': '📚 Активная',
                            'overdue': '⚠️ Просрочена',
                            'returned': '✅ Возвращена'
                        }.get(status_text, status_text)

                        can_return = loan['status'] in ['active', 'overdue']

                        # format dates
                        loan_date = loan.get('loan_date', '—')
                        due_date = loan.get('due_date', '—')
                        return_date = loan.get('return_date', '—')

                        if loan_date and len(loan_date) >= 10:
                            loan_date = loan_date[:10]
                        if due_date and len(due_date) >= 10:
                            due_date = due_date[:10]
                        if return_date and len(return_date) >= 10:
                            return_date = return_date[:10]

                        rows.append({
                            'id': loan['id'],
                            'book_title': loan.get('book_title', '—'),
                            'reader_name': loan.get('reader_name', '—'),
                            'loan_date': loan_date,
                            'due_date': due_date,
                            'return_date': return_date if return_date != '—' else '—',
                            'status': loan.get('status', '—'),
                            'status_display': status_display,
                            'can_return': can_return,
                            '_actions': loan
                        })

                    aggrid = ui.aggrid({
                        'columnDefs': columns,
                        'rowData': rows,
                        'rowSelection': 'single',
                        'pagination': True,
                        'paginationPageSize': 10,
                    }).classes('w-full h-96')

                    def handle_row_selected(e):
                        try:
                            if not hasattr(e, 'args') or not e.args:
                                return

                            selected_rows = None
                            possible_keys = ['selection', 'selectedRows', 'selected_rows', 'rowData']

                            for key in possible_keys:
                                if key in e.args:
                                    selected_rows = e.args[key]
                                    if key == 'rowData':
                                        selected_rows = [selected_rows]
                                    break

                            if selected_rows and len(selected_rows) > 0:
                                selected_loan = selected_rows[0]
                                loan_data = selected_loan.get('_actions', selected_loan)
                                show_edit_dialog(loan_data)

                                try:
                                    aggrid.run_grid_method('deselectAll')
                                except:
                                    pass

                        except Exception as ex:
                            print(f"Ошибка в handle_row_selected: {ex}")

                    aggrid.on('rowSelected', handle_row_selected)

                except ImportError:
                    print("Ошибка импорта aggrid. Сервис возвращает ошибку.")

                    # show error message
                    with ui.row().classes('w-full justify-center p-8'):
                        ui.icon('error', size='xl').classes('text-red-400')
                        ui.label('Ошибка загрузки таблицы аренд').classes('text-red-500 text-lg')

    # UI

    with ui.row().classes('w-full justify-between mb-6'):
        ui.label('📝 Управление выдачами').classes('text-h5 flex-grow mb-6')

        with ui.row().classes('items-center gap-4'):
            ui.button('Обновить', on_click=load_loans, icon='refresh')
            ui.button('Выдать книгу', on_click=show_add_dialog, icon='bookmark_add', color='positive')

    with ui.row().classes('w-full justify-between mb-6'):
        # search bar
        search_input = ui.input('Поиск (по книге или читателю)').classes('flex-grow mr-4').on('keydown.enter', lambda: load_loans())
        # status filter
        status_filter = ui.select(
            options={'': 'Все', 'active': 'Активные', 'overdue': 'Просроченные', 'returned': 'Возвращенные'},
            value='',
            label='Статус'
        ).classes('w-48')
        status_filter.on('update:model-value', lambda: load_loans())

        with ui.row().classes('gap-2'):
            ui.button('Сбросить', on_click=lambda: (search_input.set_value(''), status_filter.set_value(''), load_loans()), icon='clear').props('outline')
            ui.button('Найти', on_click=load_loans, icon='search').props('outline')

    loans_container = ui.column().classes('w-full')

    # autoupdate 60sec
    ui.timer(60, load_loans)
    # first manual update
    ui.timer(0.2, load_loans, once=True)
