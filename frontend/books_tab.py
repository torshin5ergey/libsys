# frontend books_tab.py

import os
import requests
from datetime import datetime

from nicegui import ui


def create_books_tab():
    books = []
    genres = []
    editing_book = None

    add_dialog = None
    edit_dialog = None

    books_container = None
    search_input = None

    def load_genres():
        """Загрузить список жанров"""
        nonlocal genres
        try:
            response = requests.get(
                f"{os.getenv('BOOKS_SERVICE_API_URL')}/api/genres",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                genres = data.get('genres', [])
            else:
                genres = []
        except:
            genres = []

    def get_book_status(book_id):
        """Получить статус книги"""
        try:
            response = requests.get(
                f"{os.getenv('LOANS_SERVICE_API_URL')}/api/loans",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                loans = data.get('loans', [])

                for loan in loans:
                    if loan.get('book_id') == book_id and loan.get('status') in ['active', 'overdue']:
                        return {
                            'status': 'loaned',
                            'reader_name': loan.get('reader_name'),
                            'due_date': loan.get('due_date'),
                            'loan_status': loan.get('status')
                        }

            return {'status': 'available'}
        except:
            return {'status': 'unknown'}

    def reset_search():
        """Сбросить поиск и загрузить все книги"""
        if search_input:
            search_input.value = ''
        load_books()

    def load_books():
        """Загрузить книги из API"""
        nonlocal books
        try:
            search = search_input.value.strip()
            url = f"{os.getenv('BOOKS_SERVICE_API_URL')}/api/books"

            if search:
                # add search parameter to request
                url = f"{url}?search={search}"

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                books_data = data.get('books', [])

                # add book status
                books = []
                for book in books_data:
                    status_info = get_book_status(book['id'])
                    book_with_status = {**book, 'status_info': status_info}
                    books.append(book_with_status)

                update_books_list()
                if search:
                    ui.notify(f'Найдено {len(books)} книг по запросу "{search}"', type='info')
            else:
                ui.notify(f'Ошибка загрузки: {response.status_code}', type='negative')
                books = []
                update_books_list()
        except requests.exceptions.ConnectionError:
            ui.notify('Не удалось подключиться к серверу книг', type='negative')
        except requests.exceptions.Timeout:
            ui.notify('Превышено время ожидания ответа', type='negative')
        except Exception as e:
            ui.notify(f'Ошибка: {str(e)}', type='negative')
            books = []
            update_books_list()

    def show_add_dialog():
        """Показать диалоговое окно добавления книги"""
        load_genres()

        with ui.dialog() as dialog, ui.card().classes('w-full max-w-md'):
            nonlocal add_dialog
            add_dialog = dialog

            ui.label('Добавить новую книгу').classes('text-h6 mb-4')

            with ui.column().classes('w-full gap-3'):
                title_input = ui.input('Название книги *').classes('w-full')
                author_input = ui.input('Автор *').classes('w-full')
                year_input = ui.input('Год издания').classes('w-full')

                genre_options = {}
                genre_options[None] = 'Не выбран'

                for genre in genres:
                    genre_options[genre['id']] = genre['name']

                genre_select = ui.select(
                    label='Жанр',
                    options=genre_options,
                    value=None
                ).classes('w-full')

                with ui.row().classes('w-full justify-between pt-4'):
                    ui.button('Отмена', on_click=lambda: add_dialog.close()).props('flat')
                    ui.button('Добавить', on_click=lambda: create_book(
                        title_input, author_input, year_input, genre_select
                    ), color='primary').props('flat')

            title_input.on('blur', lambda: highlight_required(title_input))
            author_input.on('blur', lambda: highlight_required(author_input))

        add_dialog.open()

    def highlight_required(input_field):
        """Подсветить обязательное поле если оно пустое"""
        if not input_field.value.strip():
            input_field.classes('border-red-500', remove='border-gray-300')
        else:
            input_field.classes('border-gray-300', remove='border-red-500')

    def create_book(title_input, author_input, year_input, genre_select):
        """Создать новую книгу"""
        title = title_input.value.strip()
        author = author_input.value.strip()
        year = year_input.value.strip()
        genre_id = genre_select.value if genre_select.value else None

        errors = []
        if not title:
            errors.append('Название книги обязательно')
            title_input.classes('border-red-500', remove='border-gray-300')
        if not author:
            errors.append('Автор обязателен')
            author_input.classes('border-red-500', remove='border-gray-300')

        if errors:
            for error in errors:
                ui.notify(error, type='warning')
            return

        try:
            data = {'title': title, 'author': author}
            if year:
                try:
                    data['year'] = int(year)
                    if data['year'] < 0 or data['year'] > datetime.now().year + 1:
                        ui.notify('Некорректный год', type='warning')
                        year_input.classes('border-red-500', remove='border-gray-300')
                        return
                except ValueError:
                    ui.notify('Год должен быть числом', type='warning')
                    year_input.classes('border-red-500', remove='border-gray-300')
                    return
            if genre_id:
                data['genre_id'] = genre_id

            response = requests.post(
                f"{os.getenv('BOOKS_SERVICE_API_URL')}/api/books",
                json=data,
                timeout=10
            )

            if response.status_code == 201:
                ui.notify('Книга успешно добавлена', type='positive')
                add_dialog.close()
                load_books()
            else:
                error_data = response.json()
                error_msg = error_data.get('error', 'Неизвестная ошибка')
                ui.notify(f'Ошибка: {error_msg}', type='negative')

        except requests.exceptions.ConnectionError:
            ui.notify('Не удалось подключиться к серверу', type='negative')
        except Exception as e:
            ui.notify(f'Ошибка: {str(e)}', type='negative')

    def show_edit_dialog(book):
        """Показать диалоговое окно редактирования книги"""
        load_genres()

        nonlocal editing_book, edit_dialog
        editing_book = book.copy()

        with ui.dialog() as dialog, ui.card().classes('w-full max-w-md'):
            edit_dialog = dialog

            ui.label('Редактировать книгу').classes('text-h6 mb-4')

            with ui.column().classes('w-full gap-3'):
                edit_title_input = ui.input('Название книги *').classes('w-full')
                edit_title_input.value = book.get('title', '')

                edit_author_input = ui.input('Автор *').classes('w-full')
                edit_author_input.value = book.get('author', '')

                edit_year_input = ui.input('Год издания').classes('w-full')
                if book.get('year'):
                    edit_year_input.value = str(book['year'])

                genre_options = {}
                genre_options[None] = 'Не выбран'

                for genre in genres:
                    genre_options[genre['id']] = genre['name']

                edit_genre_select = ui.select(
                    label='Жанр',
                    options=genre_options,
                    value=book.get('genre_id')
                ).classes('w-full')

                # action buttons
                with ui.row().classes('w-full justify-between pt-4'):
                    ui.button('Удалить',
                            on_click=lambda: delete_book(book['id'], book['title'], close_edit_dialog=True),
                            color='red').props('flat')
                    with ui.row().classes('gap-2'):
                        ui.button('Отмена', on_click=lambda: edit_dialog.close()).props('flat')
                        ui.button('Сохранить', on_click=lambda: update_book(
                            edit_title_input, edit_author_input, edit_year_input, edit_genre_select
                        ), color='primary').props('flat')

            edit_title_input.on('blur', lambda: highlight_required(edit_title_input))
            edit_author_input.on('blur', lambda: highlight_required(edit_author_input))

        edit_dialog.open()

    def update_book(title_input, author_input, year_input, genre_select):
        """Обновить информацию о книге"""
        if not editing_book:
            return

        title = title_input.value.strip()
        author = author_input.value.strip()
        year = year_input.value.strip()
        genre_id = genre_select.value if genre_select.value else None

        errors = []
        if not title:
            errors.append('Название книги обязательно')
            title_input.classes('border-red-500', remove='border-gray-300')
        if not author:
            errors.append('Автор обязателен')
            author_input.classes('border-red-500', remove='border-gray-300')

        if errors:
            for error in errors:
                ui.notify(error, type='warning')
            return

        try:
            data = {'title': title, 'author': author}
            if year:
                try:
                    data['year'] = int(year)
                    if data['year'] < 0 or data['year'] > datetime.now().year + 1:
                        ui.notify('Некорректный год', type='warning')
                        year_input.classes('border-red-500', remove='border-gray-300')
                        return
                except ValueError:
                    ui.notify('Год должен быть числом', type='warning')
                    year_input.classes('border-red-500', remove='border-gray-300')
                    return
            else:
                data['year'] = None

            data['genre_id'] = genre_id

            response = requests.put(
                f"{os.getenv('BOOKS_SERVICE_API_URL')}/api/books/{editing_book['id']}",
                json=data,
                timeout=10
            )

            if response.status_code == 200:
                ui.notify('Книга успешно обновлена', type='positive')
                edit_dialog.close()
                load_books()
            else:
                error_data = response.json()
                error_msg = error_data.get('error', 'Неизвестная ошибка')
                ui.notify(f'Ошибка: {error_msg}', type='negative')

        except requests.exceptions.ConnectionError:
            ui.notify('Не удалось подключиться к серверу', type='negative')
        except Exception as e:
            ui.notify(f'Ошибка: {str(e)}', type='negative')

    def delete_book(book_id, book_title, close_edit_dialog=True):
        """Удалить книгу с подтверждением"""
        status_info = get_book_status(book_id)
        if status_info.get('status') == 'loaned':
            ui.notify('Нельзя удалить книгу, которая находится в аренде', type='warning')
            return

        with ui.dialog() as dialog, ui.card().classes('w-full max-w-sm'):
            ui.label('Удалить книгу?').classes('text-h6 mb-2')
            ui.label(f'"{book_title}"').classes('text-center mb-4 font-medium')

            with ui.row().classes('w-full justify-center gap-4'):
                ui.button('Отмена', on_click=dialog.close).props('flat')
                ui.button('Удалить',
                         on_click=lambda: confirm_delete(book_id, book_title, dialog, close_edit_dialog),
                         color='red').props('flat')
            dialog.open()

    def confirm_delete(book_id, book_title, dialog, close_edit_dialog=True):
        """Подтверждение удаления книги"""
        try:
            response = requests.delete(
                f"{os.getenv('BOOKS_SERVICE_API_URL')}/api/books/{book_id}",
                timeout=10
            )

            if response.status_code == 200:
                ui.notify('Книга успешно удалена', type='positive')
                dialog.close()
                if close_edit_dialog and edit_dialog:
                    edit_dialog.close()
                load_books()
            else:
                error_data = response.json()
                error_msg = error_data.get('error', 'Неизвестная ошибка')
                ui.notify(f'Ошибка удаления: {error_msg}', type='negative')

        except requests.exceptions.ConnectionError:
            ui.notify('Не удалось подключиться к серверу', type='negative')
        except Exception as e:
            ui.notify(f'Ошибка: {str(e)}', type='negative')

    def edit_selected_book(aggrid):
        """Редактировать выбранную книгу"""
        async def get_selection():
            try:
                selection = await aggrid.run_grid_method('getSelectedRows')
                if selection and len(selection) > 0:
                    selected_book = selection[0]
                    if '_actions' in selected_book:
                        show_edit_dialog(selected_book['_actions'])
                    else:
                        show_edit_dialog(selected_book)
                else:
                    ui.notify('Выберите книгу для редактирования', type='warning')
            except Exception as e:
                ui.notify(f'Ошибка: {str(e)}', type='negative')

        ui.timer(0.1, get_selection, once=True)

    def delete_selected_book(aggrid):
        """Удалить выбранную книгу"""
        async def get_selection():
            try:
                selection = await aggrid.run_grid_method('getSelectedRows')
                if selection and len(selection) > 0:
                    selected_book = selection[0]
                    book_data = selected_book.get('_actions', selected_book)

                    # check if loaned
                    status_info = get_book_status(book_data['id'])
                    if status_info.get('status') == 'loaned':
                        ui.notify('Нельзя удалить книгу, которая находится в аренде', type='warning')
                        return

                    delete_book(book_data['id'], book_data['title'], close_edit_dialog=False)
                else:
                    ui.notify('Выберите книгу для удаления', type='warning')
            except Exception as e:
                ui.notify(f'Ошибка: {str(e)}', type='negative')

        ui.timer(0.1, get_selection, once=True)

    def update_books_list():
        """Обновить отображение списка книг"""
        if books_container:
            books_container.clear()

            with books_container:
                if not books:
                    with ui.row().classes('w-full justify-center p-8'):
                        ui.icon('search_off', size='xl').classes('text-gray-400')
                        ui.label('Книги не найдены').classes('text-gray-500 text-lg')
                    return

                # create table
                try:
                    with ui.row().classes('w-full justify-end gap-2 mb-4'):
                        ui.button(
                            'Редактировать выбранное',
                            on_click=lambda: edit_selected_book(aggrid),
                            icon='edit',
                            color='primary'
                        ).props('flat')

                        ui.button(
                            'Удалить выбранное',
                            on_click=lambda: delete_selected_book(aggrid),
                            icon='delete',
                            color='negative'
                        ).props('flat')

                    # table columns
                    columns = [
                        {'headerName': 'Название', 'field': 'title', 'sortable': True, 'filter': True},
                        {'headerName': 'Автор', 'field': 'author', 'sortable': True, 'filter': True},
                        {'headerName': 'Год', 'field': 'year', 'sortable': True, 'filter': True, 'width': 100},
                        {'headerName': 'Жанр', 'field': 'genre', 'sortable': True, 'filter': True, 'width': 150},
                        {'headerName': 'Статус', 'field': 'status', 'sortable': True, 'width': 150},
                    ]

                    rows = []
                    for book in books:
                        status_info = book.get('status_info', {})
                        status_text = '✅ Доступна'

                        if status_info.get('status') == 'loaned':
                            if status_info.get('loan_status') == 'overdue':
                                status_text = '⚠️ Просрочена'
                            else:
                                status_text = '📚 Арендована'
                        elif status_info.get('status') == 'unknown':
                            status_text = '❓ Неизвестно'

                        rows.append({
                            'id': book['id'],
                            'title': book['title'],
                            'author': book['author'],
                            'year': book.get('year', '—'),
                            'genre': book.get('genre', '—'),
                            'status': status_text,
                            '_actions': book
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
                                selected_book = selected_rows[0]
                                book_data = selected_book.get('_actions', selected_book)
                                show_edit_dialog(book_data)

                                try:
                                    aggrid.run_grid_method('deselectAll')
                                except:
                                    pass

                        except Exception as ex:
                            print(f"Ошибка в handle_row_selected: {ex}")
                            ui.notify('Ошибка при выборе строки', type='negative')

                    aggrid.on('rowSelected', handle_row_selected)

                except ImportError:
                    print("Ошибка импорта aggrid. Сервис возвращает ошибку.")

                    # show error message
                    with ui.row().classes('w-full justify-center p-8'):
                        ui.icon('error', size='xl').classes('text-red-400')
                        ui.label('Ошибка загрузки таблицы книг').classes('text-red-500 text-lg')

    # UI

    with ui.row().classes('w-full justify-between mb-6'):
        ui.label('📚 Управление книгами').classes('text-h5 flex-grow mb-6')

        with ui.row().classes('items-center gap-4'):
            ui.button('Обновить', on_click=load_books, icon='refresh')
            ui.button('Добавить книгу', on_click=show_add_dialog, icon='add', color='positive')

    # search row
    with ui.row().classes('w-full justify-between mb-6'):
        search_input = ui.input('Поиск (по названию или автору)').classes('flex-grow mr-4').on('keydown.enter', lambda: load_books())

        with ui.row().classes('gap-2'):
            ui.button('Сбросить', on_click=reset_search, icon='clear').props('outline')
            ui.button('Найти', on_click=load_books, icon='search').props('outline')

    books_container = ui.column().classes('w-full')

    # first manual load genres
    ui.timer(0.1, load_genres, once=True)
    # autoupdate 60sec
    ui.timer(60, load_books)
    # first manual update
    ui.timer(0.2, load_books, once=True)
