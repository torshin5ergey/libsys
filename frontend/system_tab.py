# frontend system_tab.py

import os
import requests
from datetime import datetime

from nicegui import ui


def create_system_tab():
    """"""
    def check_status():
        """Check services status"""
        books_status_card.clear()
        readers_status_card.clear()
        loans_status_card.clear()
        db_status_card.clear()

        # books Service
        with books_status_card:
            try:
                api_resp = requests.get(f"{os.getenv('BOOKS_SERVICE_API_URL')}/api/health", timeout=5)
                if api_resp.status_code == 200:
                    ui.label('books-service: доступен').classes('text-green-600')
                else:
                    ui.label('books-service: недоступен').classes('text-red-600')
            except:
                ui.label('books-service: недоступен').classes('text-red-600')

        # readers Service
        with readers_status_card:
            try:
                readers_resp = requests.get(f"{os.getenv('READERS_SERVICE_API_URL')}/api/health", timeout=5)
                if readers_resp.status_code == 200:
                    ui.label('readers-service: доступен').classes('text-green-600')
                else:
                    ui.label('readers-service: недоступен').classes('text-red-600')
            except:
                ui.label('readers-service: недоступен').classes('text-red-600')

        # loans Service
        with loans_status_card:
            try:
                loans_resp = requests.get(f"{os.getenv('LOANS_SERVICE_API_URL')}/api/health", timeout=5)
                if loans_resp.status_code == 200:
                    ui.label('loans-service: доступен').classes('text-green-600')
                else:
                    ui.label('loans-service: недоступен').classes('text-red-600')
            except:
                ui.label('loans-service: недоступен').classes('text-red-600')

        # database
        with db_status_card:
            try:
                db_resp = requests.get(f"{os.getenv('MONITOR_SERVICE_API_URL')}/api/db/status", timeout=5)
                if db_resp.status_code == 200:
                    data = db_resp.json()
                    if data['status'] == 'connected':
                        ui.label('База данных: подключена').classes('text-green-600')
                    else:
                        ui.label('База данных: недоступна').classes('text-red-600')
                else:
                    ui.label('База данных: недоступна').classes('text-red-600')
            except:
                ui.label('База данных: недоступна').classes('text-red-600')

        # update time
        if update_time_label:
            update_time_label.set_text(f'Обновлено: {datetime.now().strftime("%H:%M:%S")}')

    # UI

    with ui.row().classes('w-full justify-between mb-6'):
        ui.label('⚙️ Статус системы').classes('text-h5 mb-6')

        with ui.row().classes('items-center gap-4'):
            update_time_label = ui.label('Обновлено: --:--:--').classes('text-xs text-gray-500')
            ui.button('Обновить', on_click=check_status, icon='refresh')

    # autoupdate 60 sec
    ui.timer(60, check_status)
    # first manual update
    ui.timer(0.1, check_status, once=True)

    with ui.row().classes('w-full gap-4 items-center'):
        books_status_card = ui.card().classes('flex-1 min-w-48')
        readers_status_card = ui.card().classes('flex-1 min-w-48')
        loans_status_card = ui.card().classes('flex-1 min-w-48')
        db_status_card = ui.card().classes('flex-1 min-w-48')
