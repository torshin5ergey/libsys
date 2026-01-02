# frontend readers_tab.py

import os
import requests

from nicegui import ui


def create_readers_tab():
    """Вкладка управления читателями"""
    readers = []
    editing_reader = None

    add_dialog = None
    edit_dialog = None
    readers_container = None
    search_input = None

    def load_readers():
        """Загрузить читателей из API"""
        nonlocal readers
        try:
            search = search_input.value.strip() if search_input else ''
            url = f"{os.getenv('READERS_SERVICE_API_URL')}/api/readers"

            if search:
                url = f"{url}?search={search}"

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                readers = data.get('readers', [])
                update_readers_list()
                if search:
                    ui.notify(f'Найдено {len(readers)} читателей', type='info')
            else:
                ui.notify(f'Ошибка загрузки: {response.status_code}', type='negative')
                readers = []
                update_readers_list()
        except Exception as e:
            ui.notify(f'Ошибка: {str(e)}', type='negative')
            readers = []
            update_readers_list()

    def show_add_dialog():
        """Показать диалоговое окно добавления читателя"""
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-md'):
            nonlocal add_dialog
            add_dialog = dialog

            ui.label('Добавить нового читателя').classes('text-h6 mb-4')

            with ui.column().classes('w-full gap-3'):
                name_input = ui.input('ФИО *').classes('w-full')
                email_input = ui.input('Email').classes('w-full')
                phone_input = ui.input('Телефон').classes('w-full')
                address_input = ui.input('Адрес').classes('w-full')

                with ui.row().classes('w-full justify-between pt-4'):
                    ui.button('Отмена', on_click=lambda: add_dialog.close()).props('flat')
                    ui.button('Добавить', on_click=lambda: create_reader(
                        name_input, email_input, phone_input, address_input
                    ), color='primary').props('flat')

        add_dialog.open()

    def create_reader(name_input, email_input, phone_input, address_input):
        """Создать нового читателя"""
        name = name_input.value.strip()
        email = email_input.value.strip()
        phone = phone_input.value.strip()
        address = address_input.value.strip()

        if not name:
            ui.notify('ФИО обязательно для заполнения', type='warning')
            name_input.classes('border-red-500', remove='border-gray-300')
            return

        try:
            data = {
                'full_name': name,
                'email': email if email else None,
                'phone': phone if phone else None,
                'address': address if address else None
            }

            response = requests.post(
                f"{os.getenv('READERS_SERVICE_API_URL')}/api/readers",
                json=data,
                timeout=10
            )

            if response.status_code == 201:
                ui.notify('Читатель успешно добавлен', type='positive')
                add_dialog.close()
                load_readers()
            else:
                error_data = response.json()
                error_msg = error_data.get('error', 'Неизвестная ошибка')
                ui.notify(f'Ошибка: {error_msg}', type='negative')

        except requests.exceptions.ConnectionError:
            ui.notify('Не удалось подключиться к серверу', type='negative')
        except Exception as e:
            ui.notify(f'Ошибка: {str(e)}', type='negative')

    def show_edit_dialog(reader):
        """Показать диалоговое окно редактирования читателя"""
        nonlocal editing_reader, edit_dialog
        editing_reader = reader.copy()

        with ui.dialog() as dialog, ui.card().classes('w-full max-w-md'):
            edit_dialog = dialog

            ui.label('Редактировать читателя').classes('text-h6 mb-4')

            with ui.column().classes('w-full gap-3'):
                edit_name_input = ui.input('ФИО *').classes('w-full')
                edit_name_input.value = reader.get('full_name', '')

                edit_email_input = ui.input('Email').classes('w-full')
                edit_email_input.value = reader.get('email', '')

                edit_phone_input = ui.input('Телефон').classes('w-full')
                edit_phone_input.value = reader.get('phone', '')

                edit_address_input = ui.input('Адрес').classes('w-full')
                edit_address_input.value = reader.get('address', '')

                with ui.row().classes('w-full justify-between pt-4'):
                    ui.button('Удалить',
                            on_click=lambda: delete_reader(reader['id'], reader['full_name'], close_edit_dialog=True),
                            color='red').props('flat')
                    with ui.row().classes('gap-2'):
                        ui.button('Отмена', on_click=lambda: edit_dialog.close()).props('flat')
                        ui.button('Сохранить', on_click=lambda: update_reader(
                            edit_name_input, edit_email_input, edit_phone_input, edit_address_input
                        ), color='primary').props('flat')

        edit_dialog.open()

    def update_reader(name_input, email_input, phone_input, address_input):
        """Обновить информацию о читателе"""
        if not editing_reader:
            return

        name = name_input.value.strip()
        email = email_input.value.strip()
        phone = phone_input.value.strip()
        address = address_input.value.strip()

        if not name:
            ui.notify('ФИО обязательно для заполнения', type='warning')
            name_input.classes('border-red-500', remove='border-gray-300')
            return

        try:
            data = {
                'full_name': name,
                'email': email,
                'phone': phone,
                'address': address
            }

            response = requests.put(
                f"{os.getenv('READERS_SERVICE_API_URL')}/api/readers/{editing_reader['id']}",
                json=data,
                timeout=10
            )

            if response.status_code == 200:
                ui.notify('Читатель успешно обновлен', type='positive')
                edit_dialog.close()
                load_readers()
            else:
                error_data = response.json()
                error_msg = error_data.get('error', 'Неизвестная ошибка')
                ui.notify(f'Ошибка: {error_msg}', type='negative')

        except requests.exceptions.ConnectionError:
            ui.notify('Не удалось подключиться к серверу', type='negative')
        except Exception as e:
            ui.notify(f'Ошибка: {str(e)}', type='negative')

    def delete_reader(reader_id, reader_name, close_edit_dialog=True):
        """Удалить читателя с подтверждением"""
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-sm'):
            ui.label('Удалить читателя?').classes('text-h6 mb-2')
            ui.label(f'"{reader_name}"').classes('text-center mb-4 font-medium')

            with ui.row().classes('w-full justify-center gap-4'):
                ui.button('Отмена', on_click=dialog.close).props('flat')
                ui.button('Удалить',
                         on_click=lambda: confirm_delete(reader_id, reader_name, dialog, close_edit_dialog),
                         color='red').props('flat')
            dialog.open()

    def confirm_delete(reader_id, reader_name, dialog, close_edit_dialog=True):
        """Подтвержденное удаление читателя"""
        try:
            response = requests.delete(
                f"{os.getenv('READERS_SERVICE_API_URL')}/api/readers/{reader_id}",
                timeout=10
            )

            if response.status_code == 200:
                ui.notify('Читатель успешно удален', type='positive')
                dialog.close()
                if close_edit_dialog and edit_dialog:
                    edit_dialog.close()
                load_readers()
            else:
                error_data = response.json()
                error_msg = error_data.get('error', 'Неизвестная ошибка')
                ui.notify(f'Ошибка удаления: {error_msg}', type='negative')

        except requests.exceptions.ConnectionError:
            ui.notify('Не удалось подключиться к серверу', type='negative')
        except Exception as e:
            ui.notify(f'Ошибка: {str(e)}', type='negative')

    def update_readers_list():
        """Обновить отображение списка читателей"""
        if readers_container:
            readers_container.clear()

            with readers_container:
                if not readers:
                    with ui.row().classes('w-full justify-center p-8'):
                        ui.icon('people', size='xl').classes('text-gray-400')
                        ui.label('Читатели не найдены').classes('text-gray-500 text-lg')
                    return

                # create table
                try:
                    # action buttons
                    with ui.row().classes('w-full justify-end gap-2 mb-4'):
                        ui.button(
                            'Редактировать выбранное',
                            on_click=lambda: edit_selected_reader(aggrid),
                            icon='edit',
                            color='primary'
                        ).props('flat')

                        ui.button(
                            'Удалить выбранное',
                            on_click=lambda: delete_selected_reader(aggrid),
                            icon='delete',
                            color='negative'
                        ).props('flat')

                    # table columns
                    columns = [
                        {'headerName': 'ФИО', 'field': 'full_name', 'sortable': True, 'filter': True},
                        {'headerName': 'Email', 'field': 'email', 'sortable': True, 'filter': True},
                        {'headerName': 'Телефон', 'field': 'phone', 'sortable': True, 'filter': True},
                        {'headerName': 'Дата регистрации', 'field': 'registration_date', 'sortable': True, 'width': 150},
                    ]

                    rows = []
                    for reader in readers:
                        rows.append({
                            'id': reader['id'],
                            'full_name': reader.get('full_name', '—'),
                            'email': reader.get('email', '—'),
                            'phone': reader.get('phone', '—'),
                            'registration_date': reader.get('registration_date', '—')[:10] if reader.get('registration_date') else '—',
                            '_actions': reader
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
                                selected_reader = selected_rows[0]
                                reader_data = selected_reader.get('_actions', selected_reader)
                                show_edit_dialog(reader_data)

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
                        ui.label('Ошибка загрузки таблицы читателей').classes('text-red-500 text-lg')

    def edit_selected_reader(aggrid):
        """Редактировать выбранного читателя"""
        async def get_selection():
            try:
                selection = await aggrid.run_grid_method('getSelectedRows')
                if selection and len(selection) > 0:
                    selected_reader = selection[0]
                    if '_actions' in selected_reader:
                        show_edit_dialog(selected_reader['_actions'])
                    else:
                        show_edit_dialog(selected_reader)
                else:
                    ui.notify('Выберите читателя для редактирования', type='warning')
            except Exception as e:
                ui.notify(f'Ошибка: {str(e)}', type='negative')

        ui.timer(0.1, get_selection, once=True)

    def delete_selected_reader(aggrid):
        """Удалить выбранного читателя"""
        async def get_selection():
            try:
                selection = await aggrid.run_grid_method('getSelectedRows')
                if selection and len(selection) > 0:
                    selected_reader = selection[0]
                    reader_data = selected_reader.get('_actions', selected_reader)
                    delete_reader(reader_data['id'], reader_data['full_name'], close_edit_dialog=False)
                else:
                    ui.notify('Выберите читателя для удаления', type='warning')
            except Exception as e:
                ui.notify(f'Ошибка: {str(e)}', type='negative')

        ui.timer(0.1, get_selection, once=True)

    # UI

    with ui.row().classes('w-full justify-between mb-6'):
        ui.label('👥 Управление читателями').classes('text-h5 flex-grow mb-6')

        with ui.row().classes('items-center gap-4'):
            ui.button('Обновить', on_click=load_readers, icon='refresh')
            ui.button('Добавить читателя', on_click=show_add_dialog, icon='person_add', color='positive')

    # search row
    with ui.row().classes('w-full justify-between mb-6'):
        search_input = ui.input('Поиск (по ФИО, email или телефону)').classes('flex-grow mr-4').on('keydown.enter', lambda: load_readers())

        with ui.row().classes('gap-2'):
            ui.button('Сбросить', on_click=lambda: search_input.set_value('') or load_readers(), icon='clear').props('outline')
            ui.button('Найти', on_click=load_readers, icon='search').props('outline')

    readers_container = ui.column().classes('w-full')

    # autoupdate 60sec
    ui.timer(60, load_readers)
    # first manual update
    ui.timer(0.1, load_readers, once=True)
