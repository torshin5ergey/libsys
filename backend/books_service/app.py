# books service app.py

import os
import logging
from datetime import datetime

from flask import Flask, jsonify, request
import psycopg2

from common.env_checker import check_env

# ==============================================================================
vars_to_check = [
    'API_HOST',
    'API_PORT',
    'DB_HOST',
    'DB_PORT',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD'
]
# ==============================================================================

def get_db_config():
    return {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }

def get_db_connection():
    config = get_db_config()
    return psycopg2.connect(**config)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'service': 'Book Service API',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/books', methods=['GET'])
def get_books():
    """Получить все книги с поддержкой поиска"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # get params from request
        search_query = request.args.get('search', '').strip()
        search_field = request.args.get('field', 'both')  # 'title', 'author', 'both'

        if search_query:
            if search_field == 'title':
                sql = """
                    SELECT b.id, b.title, b.author, b.year, b.genre_id, g.name as genre_name, b.created_at
                    FROM books b
                    LEFT JOIN genres g ON b.genre_id = g.id
                    WHERE b.title ILIKE %s
                    ORDER BY b.title
                """
                params = (f"%{search_query}%",)
            elif search_field == 'author':
                sql = """
                    SELECT b.id, b.title, b.author, b.year, b.genre_id, g.name as genre_name, b.created_at
                    FROM books b
                    LEFT JOIN genres g ON b.genre_id = g.id
                    WHERE b.author ILIKE %s
                    ORDER BY b.title
                """
                params = (f"%{search_query}%",)
            else:  # both
                sql = """
                    SELECT b.id, b.title, b.author, b.year, b.genre_id, g.name as genre_name, b.created_at
                    FROM books b
                    LEFT JOIN genres g ON b.genre_id = g.id
                    WHERE b.title ILIKE %s OR b.author ILIKE %s
                    ORDER BY b.title
                """
                params = (f"%{search_query}%", f"%{search_query}%")

            cursor.execute(sql, params)
        else:
            cursor.execute("""
                SELECT b.id, b.title, b.author, b.year, b.genre_id, g.name as genre_name, b.created_at
                FROM books b
                LEFT JOIN genres g ON b.genre_id = g.id
                ORDER BY b.title
            """)

        books = cursor.fetchall()

        cursor.close()
        conn.close()

        books_list = []
        for book in books:
            books_list.append({
                'id': book[0],
                'title': book[1],
                'author': book[2],
                'year': book[3],
                'genre_id': book[4],
                'genre': book[5],
                'created_at': book[6].isoformat() if book[6] else None
            })

        return jsonify({
            'books': books_list,
            'search_query': search_query,
            'count': len(books_list)
        })

    except Exception as e:
        logging.error(f"Error getting books: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """Получить книгу по ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT b.id, b.title, b.author, b.year, b.genre_id, g.name as genre_name, b.created_at
            FROM books b
            LEFT JOIN genres g ON b.genre_id = g.id
            WHERE b.id = %s
        """, (book_id,))
        book = cursor.fetchone()

        cursor.close()
        conn.close()

        if book is None:
            return jsonify({'error': 'Book not found'}), 404

        return jsonify({
            'id': book[0],
            'title': book[1],
            'author': book[2],
            'year': book[3],
            'genre_id': book[4],
            'genre': book[5],
            'created_at': book[6].isoformat() if book[6] else None
        })

    except Exception as e:
        logging.error(f"Error getting book: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/books', methods=['POST'])
def create_book():
    """Создать новую книгу"""
    try:
        data = request.json

        if not data or 'title' not in data or 'author' not in data:
            return jsonify({'error': 'Title and author are required'}), 400

        title = data['title'].strip()
        author = data['author'].strip()
        year = data.get('year')
        genre_id = data.get('genre_id')

        if not title or not author:
            return jsonify({'error': 'Title and author cannot be empty'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO books (title, author, year, genre_id) VALUES (%s, %s, %s, %s) RETURNING id",
            (title, author, year, genre_id)
        )

        book_id = cursor.fetchone()[0]
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Book created successfully',
            'id': book_id
        }), 201

    except Exception as e:
        logging.error(f"Error creating book: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """Обновить книгу"""
    try:
        data = request.json

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM books WHERE id = %s", (book_id,))
        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Book not found'}), 404

        updates = []
        params = []

        if 'title' in data and data['title']:
            updates.append("title = %s")
            params.append(data['title'].strip())
        if 'author' in data and data['author']:
            updates.append("author = %s")
            params.append(data['author'].strip())
        if 'year' in data:
            updates.append("year = %s")
            params.append(data['year'])
        if 'genre_id' in data:
            updates.append("genre_id = %s")
            params.append(data['genre_id'])
        if not updates:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No fields to update'}), 400

        params.append(book_id)

        query = f"UPDATE books SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, params)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Book updated successfully'})

    except Exception as e:
        logging.error(f"Error updating book: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Удалить книгу"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM books WHERE id = %s", (book_id,))
        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Book not found'}), 404

        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Book deleted successfully'})

    except Exception as e:
        logging.error(f"Error deleting book: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/genres', methods=['GET'])
def get_genres():
    """Получить список всех жанров"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, description
            FROM genres
            ORDER BY name
        """)

        genres = cursor.fetchall()

        cursor.close()
        conn.close()

        genres_list = []
        for genre in genres:
            genres_list.append({
                'id': genre[0],
                'name': genre[1],
                'description': genre[2]
            })

        return jsonify({
            'genres': genres_list,
            'count': len(genres_list)
        })

    except Exception as e:
        logging.error(f"Error getting genres: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Books Service...")
    check_env(vars_to_check)

    print(f"Book Service is listening on {os.getenv('API_HOST')}:{os.getenv('API_PORT')}")
    app.run(host=os.getenv('API_HOST'), port=os.getenv('API_PORT'), debug=True)
