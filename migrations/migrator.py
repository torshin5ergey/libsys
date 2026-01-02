# migrator.py

import os
import sys
import re

import psycopg2
from psycopg2 import sql


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

def execute_sql_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        conn = get_db_connection()
        cursor = conn.cursor()

        statements = []
        current_statement = ""
        in_string = False
        string_char = None

        for char in sql_content:
            if char in "'\"" and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                in_string = False
                string_char = None

            current_statement += char

            if char == ';' and not in_string:
                statements.append(current_statement.strip())
                current_statement = ""

        if current_statement.strip():
            statements.append(current_statement.strip())

        for statement in statements:
            if statement:
                cursor.execute(statement)

        conn.commit()
        cursor.close()
        conn.close()

        print(f"[INFO] Успешно выполнен файл: {filename}")
        return True

    except Exception as e:
        print(f"[ERROR] Ошибка при выполнении файла {filename}: {e}")
        return False

def get_sql_files_sorted():
    script_files = []
    scripts_dir = 'scripts'

    if not os.path.exists(scripts_dir):
        print(f"[ERROR] Директория '{scripts_dir}' не существует")
        return []

    pattern = re.compile(r'^(\d+)-.*\.sql$')

    for filename in os.listdir(scripts_dir):
        if filename.endswith('.sql'):
            match = pattern.match(filename)
            if match:
                # get script number
                file_number = int(match.group(1))
                full_path = os.path.join(scripts_dir, filename)
                script_files.append((file_number, filename, full_path))
    # sort by number
    script_files.sort(key=lambda x: x[0])
    # return full path
    return [file_info[2] for file_info in script_files]


def main():
    print("=== Запуск мигратора базы данных ===")

    script_files = get_sql_files_sorted()
    if not script_files:
        print("[ERROR] Не найдено SQL файлов в директории 'scripts'")
        print("[ERROR] неверный формат имени скриптов")
        sys.exit(1)

    print(f"[INFO] Найдено {len(script_files)} файлов для выполнения:")
    for i, script_file in enumerate(script_files, 1):
        print(f"  {i}. {os.path.basename(script_file)}")

    all_success = True
    for script_file in script_files:
        success = execute_sql_file(script_file)
        if not success:
            all_success = False

    if all_success:
        print("[INFO] Все миграции успешно выполнены!")
        sys.exit(0)
    else:
        print("[ERROR] Произошли ошибки при выполнении миграций")
        sys.exit(1)


if __name__ == '__main__':
    main()
