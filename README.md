# LibSys

Система для управления библиотечныйм фондом: книги, читатели и аренды с веб-интерфейсом и микросервисной архитектурой.

**Table of contents:**
- [Requirements](#requirements)
- [Quickstart](#quickstart)
- [Микросервисы](#микросервисы)
  - [books-service](#books-service)
    - [Назначение](#назначение)
    - [API endpoints](#api-endpoints)
  - [loans-service](#loans-service)
    - [Назначение](#назначение-1)
    - [API endpoints](#api-endpoints-1)
  - [readers-service](#readers-service)
    - [Назначение](#назначение-2)
    - [API endpoints](#api-endpoints-2)
  - [monitor-service](#monitor-service)
    - [Назначение](#назначение-3)
    - [API endpoints](#api-endpoints-3)
- [Возможные улучшения](#возможные-улучшения)
- [Стек](#стек)
- [Author](#author)

## Requirements

- Docker, Docker Compose

## Quickstart

- Запуск проекта
```bash
git clone https://github.com/torshin5ergey/libsys.git
cd libsys

docker compose up -d --build
```
- Доступ на `http://localhost:8080/`

## Микросервисы

### books-service

#### Назначение

Микросервис для управления каталогом книг библиотеки. Обеспечивает полный CRUD-функционал для работы с книгами.

#### API endpoints

**API URL: `http://localhost:5001`**

<details>
<summary><code>GET	/api/health</code> проверка работоспособности сервиса</summary>

**Responses:**
- `200 OK` сервис работает нормально
  ```json
  {
    "status": "ok",
    "service": "Book Service API",
    "timestamp": "2025-01-01T00:00:00"
  }
  ```
</details>

<details>
<summary><code>GET	/api/books</code> получить список всех книг</summary>

**Request parameters:**
- `search` (opt, string): текст для поиска
- `field` (opt, string): поле для поиска: `title`, `author`, `both` (default)

**Responses:**
- `200 OK` успешное получение списка книг
  ```json
  {
    "books": [
      {
        "id": 1,
        "title": "Война и мир",
        "author": "Лев Толстой",
        "year": 1869,
        "genre_id": 1,
        "genre": "Роман",
        "created_at": "2025-01-01T00:00:00"
      }
    ],
    "search_query": "война",
    "count": 1
  }
  ```
</details>

<details>
<summary><code>GET	/api/books/{id}</code> получить книгу по ID</summary>

**Request parameters:**
- `id` (req, int): ID книги

**Responses:**
- `200 OK` книга найдена
  ```json
  {
    "id": 1,
    "title": "Война и мир",
    "author": "Лев Толстой",
    "year": 1869,
    "genre_id": 1,
    "genre": "Роман",
    "created_at": "2023-01-01T00:00:00"
  }
  ```
- `404 Not Found` книга с указанным ID не найдена
  ```json
  {
    "error": "Book not found"
  }
  ```
</details>

<details>
<summary><code>POST	/api/books</code> создать новую книгу</summary>

**Request body:**
  ```json
  {
    "title": "string (req, not empty)",
    "author": "string (req, not empty)",
    "year": "integer (opt)",
    "genre_id": "integer (opt)"
  }
  ```

**Responses:**
- `201 Created` книга успешно создана
  ```json
  {
    "message": "Book created successfully",
    "id": 1
  }
  ```
- `400 Bad Request` ошибки валидации
  - Не указаны обязательные поля:
    ```json
    {
      "error": "Title and author are required"
    }
    ```
  - Пустые обязательные поля:
    ```json
    {
      "error": "Title and author cannot be empty"
    }
    ```
</details>

<details>
<summary><code>PUT	/api/books/{id}</code> обновить информацию о книге</summary>

**Requets parameters:**
- `id` (req, int): ID книги

**Request body:**
```json
{
  "title": "string (opt)",
  "author": "string (opt)",
  "year": "integer/null (opt)",
  "genre_id": "integer/null (opt)"
}
```

**Responses:**
- `200 OK` книга успешно обновлена
  ```json
  {
    "message": "Book updated successfully"
  }
  ```
- `400 Bad Request` ошибки валидации
  - Не переданы данные для обновления:
    ```json
    {
      "error": "No data provided"
    }
    ```
  - Не передано ни одного поля:
    ```json
    {
      "error": "No fields to update"
    }
    ```
  - Пустые строки в `title` или `author`:
    ```json
    {
      "error": "Title cannot be empty"
    }
    ```
- `404 Not Found` книга не найдена
  ```json
  {
    "error": "Book not found"
  }
  ```
</details>

<details>
<summary><code>DELETE	/api/books/{id}</code> удалить книгу</summary>

**Request parameters:**
- `id` (req, int): ID книги

**Responses:**
- `200 OK` книга успешно удалена
  ```json
  {
    "message": "Book deleted successfully"
  }
  ```
- `404 Not Found` книга не найдена
  ```json
  {
    "error": "Book not found"
  }
  ```
</details>

<details>
<summary><code>GET	/api/genres</code> получить список всех жанров</summary>

**Responses:**
- `200 OK` список жанров
  ```json
  {
    "genres": [
      {
        "id": 1,
        "name": "Роман",
        "description": "Крупное повествовательное произведение"
      }
    ],
    "count": 1
  }
  ```
</details>

### loans-service

#### Назначение

Микросервис для управления выдачей книг в библиотеке: выдача, возврат, отслеживание сроков и статусов.

#### API endpoints

**API URL: `http://localhost:5004`**

<details>
<summary><code>GET	/api/health</code> проверка работоспособности сервиса</summary>

**Responses:**
- `200 OK` cервис работает нормально
  ```json
  {
    "status": "ok",
    "service": "Loans Service API",
    "timestamp": "2023-01-01T00:00:00"
  }
  ```
</details>

<details>
<summary><code>GET	/api/loans</code> получить список всех аренд</summary>

**Request parameters:**
- `status` (opt, string): фильтр по статусу: `active`, `overdue`, `returned`
- `search` (opt, string): поиск по названию книги или имени читателя

**Responses:**
- `200 OK` успешное получение списка аренд
  ```json
  {
    "loans": [
      {
        "id": 1,
        "book_id": 1,
        "book_title": "Война и мир",
        "reader_id": 1,
        "reader_name": "Иванов Иван Иванович",
        "loan_date": "2023-01-01",
        "due_date": "2023-01-31",
        "return_date": null,
        "status": "active",
        "created_at": "2023-01-01T00:00:00"
      }
    ],
    "count": 1
  }
  ```
</details>

<details>
<summary><code>GET	/api/loans/{id}</code> получить аренду по ID</summary>

**Request parameters:**
- `id` (req, int): ID выдачи

**Responses:**
- `200 OK` выдача найдена
  ```json
  {
    "id": 1,
    "book_id": 1,
    "book_title": "Война и мир",
    "reader_id": 1,
    "reader_name": "Иванов Иван Иванович",
    "loan_date": "2023-01-01",
    "due_date": "2023-01-31",
    "return_date": null,
    "status": "active",
    "created_at": "2023-01-01T00:00:00"
  }
  ```
- `404 Not Found` аренда с указанным ID не найдена
  ```json
  {
    "error": "Loan not found"
  }
  ```
</details>

<details>
<summary><code>POST	/api/loans</code> создать новую выдачу книги</summary>

**Request body:**
```json
{
  "book_id": "integer (обязательно)",
  "reader_id": "integer (обязательно)",
  "due_date": "string (опционально, формат YYYY-MM-DD)"
}
```
**Responses:**
- `201 Created` книга успешно выдана
  ```json
  {
    "message": "Loan created successfully",
    "id": 1
  }
  ```
- `400 Bad Request` ошибки валидации
  - Не указаны обязательные поля:
    ```json
    {
      "error": "Book ID and Reader ID are required"
    }
    ```
  - Книга не найдена:
    ```json
    {
      "error": "Book not found"
    }
    ```
  - Читатель не найден:
    ```json
    {
      "error": "Reader not found"
    }
    ```
  - Книга уже выдана:
    ```json
    {
      "error": "Book is already loaned"
    }
    ```
  - Некорректный формат даты:
    ```json
    {
      "error": "Invalid date format. Use YYYY-MM-DD"
    }
    ```
</details>

<details>
<summary><code>PUT	/api/loans/{id}</code> обновить информацию о выдаче</summary>

**Request parameters:**
- `id` (req, int): ID выдачи
**Request body:**
```json
{
  "due_date": "string (опционально, формат YYYY-MM-DD)",
  "status": "string (опционально: active, overdue, returned)",
  "return_date": "string/null (опционально, формат YYYY-MM-DD)"
}
```
**Responses:**
- `200 OK` выдача успешно обновлена
  ```json
  {
    "message": "Loan updated successfully"
  }
  ```
- `400 Bad Request` ошибки валидации
  - Не переданы данные для обновления:
    ```json
    {
      "error": "No data provided"
    }
    ```
  - Не передано ни одного поля:
    ```json
    {
      "error": "No fields to update"
    }
    ```
  - Некорректный формат даты:
    ```json
    {
      "error": "Invalid date format. Use YYYY-MM-DD"
    }
    ```
  - Некорректный статус:
    ```json
    {
      "error": "Invalid status value"
    }
    ```
- `404 Not Found` выдача не найдена
  ```json
  {
    "error": "Loan not found"
  }
  ```
</details>

<details>
<summary><code>DELETE	/api/loans/{id}</code> удалить запись об аренде</summary>

**Request parameters:**
- `id` (req, int): ID выдачи

**Responses:**
- `200 OK` книга успешно возвращена
  ```json
  {
    "message": "Book returned successfully"
  }
  ```
- `400 Bad Request` книга уже возвращена
  ```json
  {
    "error": "Book already returned"
  }
  ```
- `404 Not Found` выдача  не найдена
  ```json
  {
    "error": "Loan not found"
  }
  ```
</details>


<details>
<summary><code>POST	/api/loans/{id}/return</code> вернуть книгу (пометить как возвращенную)</summary>

**Request parameters:**
- `id` (req, int): идентификатор выдачи

**Responses:**
- `200 OK` книга успешно возвращена
    ```json
    {
      "message": "Book returned successfully"
    }
    ```
- `400 Bad Request` книга уже возвращена
  ```json
    {
      "error": "Book already returned"
    }
  ```
`404 Not Found` выдача не найдена
```json
{
  "error": "Loan not found"
}
```
</details>

<details>
<summary><code>GET	/api/books/available</code> получить список доступных для аренды книг</summary>

**Responses:**
- `200 OK` список доступных книг
  ```json
  {
    "books": [
      {
        "id": 1,
        "title": "Война и мир",
        "author": "Лев Толстой",
        "year": 1869,
        "genre": "Роман"
      }
    ],
    "count": 1
  }
  ```

</details>

### readers-service

#### Назначение

Микросервис для управления данными читателей библиотеки. Обеспечивает регистрацию, обновление и удаление информации о читателях.

#### API endpoints

**API URL: `http://localhost:5002`**

<details>
<summary><code>GET	/api/health</code> проверка работоспособности сервиса</summary>

**Responses:**
- `200 OK` сервис работает нормально
  ```json
  {
    "status": "ok",
    "service": "Readers Service API",
    "timestamp": "2025-01-01T00:00:00"
  }
  ```
</details>

<details>
<summary><code>GET	/api/readers</code> получить список читателей</summary>

**Request parameters:**
- `search` (opt, string): текст для поиска по ФИО, email, или телефону

**Responses:**
- `200 OK` успешное получение списка читателей
  `GET /api/readers?search=Иванов`
  ```json
  {
    "readers": [
      {
        "id": 1,
        "full_name": "Иванов Иван Иванович",
        "email": "ivanov@example.com",
        "phone": "+79161234567",
        "address": "ул. Ленина, д. 1",
        "registration_date": "2023-01-01",
        "created_at": "2023-01-01T00:00:00"
      }
    ],
    "count": 1
  }
  ```
</details>

<details>
<summary><code>GET	/api/readers/{id}</code> получить читателя по ID</summary>

**Request parameters:**
- `id` (req, int): идентификатор читателя

**Responses:**
- `200 OK` читатель найден
`GET	/api/readers/1`
  ```json
  {
    "id": 1,
    "full_name": "Иванов Иван Иванович",
    "email": "ivanov@example.com",
    "phone": "+79161234567",
    "address": "ул. Ленина, д. 1",
    "registration_date": "2023-01-01",
    "created_at": "2023-01-01T00:00:00"
  }
  ```
- `404 Not Found` читатель с указанным ID не найден
  ```json
  {
    "error": "Reader not found"
  }
  ```
</details>

<details>
<summary><code>POST	/api/readers</code> создать нового читателя</summary>

**Request body:**
```json
{
  "full_name": "string (req)",
  "email": "string (opt unique)",
  "phone": "string (opt)",
  "address": "string (opt)"
}
```
**Responses:**
- `201 Created` читатель успешно создан
  ```json
  {
    "message": "Reader created successfully",
    "id": 1
  }
  ```
- `400 Bad Request` ошибка валидации входных данных
  - Не указано обязательное поле
    ```json
    {
      "error": "Full name is required"
    }
    ```
  - Пустое обязательное поле
    ```json
    {
      "error": "Full name cannot be empty"
    }
    ```
  - Email уже существует
    ```json
    {
      "error": "Email already exists"
    }
    ```
</details>

<details>
<summary><code>PUT	/api/readers/{id}</code> обновить информацию о читателе</summary>

**Request parameters:**
- `id` (req, int): идентификатор читателя

**Request body:**
```json
{
  "full_name": "string (опционально)",
  "email": "string (опционально, уникальный)",
  "phone": "string (опционально)",
  "address": "string (опционально)"
}
```
**Responses:**
- `200 OK` читатель успешно обновлен
  ```json
  {
    "message": "Reader updated successfully"
  }
  ```
- `400 Bad Request` ошибки валидации
  - Не переданы данные для обновления:
    ```json
    {
      "error": "No data provided"
    }
    ```
  - Не передано ни одного поля:
    ```json
    {
      "error": "No fields to update"
    }
    ```
  - Email уже существует у другого читателя:
    ```json
    {
      "error": "Email already exists"
    }
    ```
- `404 Not Found` читатель не найден
  ```json
  {
    "error": "Reader not found"
  }
  ```
</details>

<details>
<summary><code>DELETE	/api/readers/{id}</code> удалить читателя</summary>

**Request parameters:**
- `id` (req, int): идентификатор читателя

**Responses:**
  - `200 OK` читатель успешно удален
    ```json
    {
      "message": "Reader deleted successfully"
    }
    ```
  - `404 Not Found` читатель не найден
    ```json
    {
      "error": "Reader not found"
    }
    ```
</details>

### monitor-service

#### Назначение

Микросервис для мониторинга состояния всей системы. Отвечает за проверку доступности базы данных и предоставление информации о состоянии системы.

#### API endpoints

**API URL: `http://localhost:5000`**

<details>
<summary><code>GET	/api/health</code> проверка работоспособности сервиса мониторинга</summary>

**Responses:**
- `200 OK` сервис мониторинга работает нормально
  ```json
  {
    "status": "ok",
    "service": "System Monitor API",
    "timestamp": "2023-01-01T00:00:00"
  }
  ```
</details>

<details>
<summary><code>GET	/api/db/status</code> проверка состояния подключения к базе данных</summary>

**Responses:**
- `200 OK` успешное подключение к базе данных
  ```json
  {
    "status": "connected",
    "message": "Successfully connected to database",
    "database_info": {
      "version": "PostgreSQL 13.10 (Debian 13.10-1.pgdg110+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 10.2.1-6) 10.2.1 20210110, 64-bit",
      "database_name": "libsys",
      "current_user": "postgres",
      "total_databases": 5,
      "tables_in_public": 10
    },
    "config": {
      "host": "postgres",
      "port": 5432,
      "database": "libsys",
      "user": "postgres"
    },
    "timestamp": "2023-01-01T00:00:00"
  }
  ```
- `200 OK` ошибка подключения к базе данных
  ```json
  {
    "status": "error",
    "message": "connection to server at 'postgres' (172.18.0.2), port 5432 failed: Connection refused\n\tIs the server running on that host and accepting TCP/IP connections?",
    "config": {
      "host": "postgres",
      "port": 5432,
      "database": "libsys",
      "user": "postgres"
    },
    "timestamp": "2023-01-01T00:00:00"
  }
  ```
</details>

## Возможные улучшения

- `auth-service` для JWT аутентификации пользователя/читателя и RBAC
- `user-service` для управления пользователями
- `notifications-service` для увемодлений (о просроченных книгах и т.д)

- Расширение схемы данных для сущностей: книги, авторы, выдачи, читатели
- Панель администратора
- Возможность сохранения обложки книги с применением объектной БД MongoDB
- Расширенная история выдачи
- Возможность добавления/удаления/редактирования жанров
- Возможность добавления/удаления/редактирования авторов
- Отображение выданных книг в таблице читателей
- Логирование 4ХХ, 5ХХ ответов в сервисах
- Мониторинг и логирование Prometheus/Grafana
- Кэширование для часто запрашиваемых данных с применением Redis
- Индексация БД
- Написание манифестов Kubernetes
- Балансировщик нагрузки и reverse proxy (Nginx, HAProxy)

## Стек

**Бэкенд:**
- Python 3.10
- Flask
- psycopg2

**Фронтенд:**
- nicegui

**Инфраструктура:**
- Docker Compose
- PostgreSQL

*Проект создан для практики с использованием AI для генерации кода.*

## Author

Sergey Torshin [@torshin5ergey](https://github.com/torshin5ergey)
