# loans service app.py

import os
import logging
from datetime import datetime, timedelta

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
        'service': 'Loans Service API',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/loans', methods=['GET'])
def get_loans():
    """Получить все аренды"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        status_filter = request.args.get('status', '').strip()
        search_query = request.args.get('search', '').strip()

        base_sql = """
            SELECT r.id, r.book_id, b.title as book_title,
                   r.reader_id, rd.full_name as reader_name,
                   r.loan_date, r.due_date, r.return_date, r.status,
                   r.created_at
            FROM loans r
            JOIN books b ON r.book_id = b.id
            JOIN readers rd ON r.reader_id = rd.id
        """

        conditions = []
        params = []

        if status_filter:
            conditions.append("r.status = %s")
            params.append(status_filter)

        if search_query:
            conditions.append("(b.title ILIKE %s OR rd.full_name ILIKE %s)")
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        if conditions:
            base_sql += " WHERE " + " AND ".join(conditions)

        base_sql += " ORDER BY r.loan_date DESC"

        cursor.execute(base_sql, params)
        loans = cursor.fetchall()

        cursor.close()
        conn.close()

        loans_list = []
        for loan in loans:
            loans_list.append({
                'id': loan[0],
                'book_id': loan[1],
                'book_title': loan[2],
                'reader_id': loan[3],
                'reader_name': loan[4],
                'loan_date': loan[5].isoformat() if loan[5] else None,
                'due_date': loan[6].isoformat() if loan[6] else None,
                'return_date': loan[7].isoformat() if loan[7] else None,
                'status': loan[8],
                'created_at': loan[9].isoformat() if loan[9] else None
            })

        return jsonify({
            'loans': loans_list,
            'count': len(loans_list)
        })

    except Exception as e:
        logging.error(f"Error getting loans: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/loans/<int:loan_id>', methods=['GET'])
def get_loan(loan_id):
    """Получить аренду по ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.id, r.book_id, b.title as book_title,
                   r.reader_id, rd.full_name as reader_name,
                   r.loan_date, r.due_date, r.return_date, r.status,
                   r.created_at
            FROM loans r
            JOIN books b ON r.book_id = b.id
            JOIN readers rd ON r.reader_id = rd.id
            WHERE r.id = %s
        """, (loan_id,))
        loan = cursor.fetchone()

        cursor.close()
        conn.close()

        if loan is None:
            return jsonify({'error': 'Loan not found'}), 404

        return jsonify({
            'id': loan[0],
            'book_id': loan[1],
            'book_title': loan[2],
            'reader_id': loan[3],
            'reader_name': loan[4],
            'loan_date': loan[5].isoformat() if loan[5] else None,
            'due_date': loan[6].isoformat() if loan[6] else None,
            'return_date': loan[7].isoformat() if loan[7] else None,
            'status': loan[8],
            'created_at': loan[9].isoformat() if loan[9] else None
        })

    except Exception as e:
        logging.error(f"Error getting loan: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/loans', methods=['POST'])
def create_loan():
    """Создать новую аренду"""
    try:
        data = request.json

        if not data or 'book_id' not in data or 'reader_id' not in data:
            return jsonify({'error': 'Book ID and Reader ID are required'}), 400

        book_id = data['book_id']
        reader_id = data['reader_id']
        due_date = data.get('due_date')

        if due_date:
            try:
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        else:
            # by default 30 days
            due_date = (datetime.now() + timedelta(days=30)).date()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM books WHERE id = %s
        """, (book_id,))
        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Book not found'}), 404

        cursor.execute("""
            SELECT id FROM loans
            WHERE book_id = %s AND status = 'active'
        """, (book_id,))
        if cursor.fetchone() is not None:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Book is already loaned'}), 400

        cursor.execute("SELECT id FROM readers WHERE id = %s", (reader_id,))
        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Reader not found'}), 404

        cursor.execute(
            """INSERT INTO loans (book_id, reader_id, loan_date, due_date, status)
               VALUES (%s, %s, CURRENT_DATE, %s, 'active') RETURNING id""",
            (book_id, reader_id, due_date)
        )

        loan_id = cursor.fetchone()[0]
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Loan created successfully',
            'id': loan_id
        }), 201

    except Exception as e:
        logging.error(f"Error creating loan: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/loans/<int:loan_id>', methods=['PUT'])
def update_loan(loan_id):
    """Обновить аренду"""
    try:
        data = request.json

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM loans WHERE id = %s", (loan_id,))
        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Loan not found'}), 404

        updates = []
        params = []

        if 'due_date' in data and data['due_date']:
            updates.append("due_date = %s")
            try:
                due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
                params.append(due_date)
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        if 'status' in data:
            updates.append("status = %s")
            params.append(data['status'])

        if 'return_date' in data:
            if data['return_date']:
                updates.append("return_date = %s")
                try:
                    return_date = datetime.strptime(data['return_date'], '%Y-%m-%d').date()
                    params.append(return_date)
                except ValueError:
                    return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
            else:
                updates.append("return_date = NULL")

        if not updates:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No fields to update'}), 400

        params.append(loan_id)

        query = f"UPDATE loans SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, params)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Loan updated successfully'})

    except Exception as e:
        logging.error(f"Error updating loan: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/loans/<int:loan_id>', methods=['DELETE'])
def delete_loan(loan_id):
    """Удалить аренду"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM loans WHERE id = %s", (loan_id,))
        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Loan not found'}), 404

        cursor.execute("DELETE FROM loans WHERE id = %s", (loan_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Loan deleted successfully'})

    except Exception as e:
        logging.error(f"Error deleting loan: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/loans/<int:loan_id>/return', methods=['POST'])
def return_book(loan_id):
    """Вернуть книгу"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, status FROM loans WHERE id = %s
        """, (loan_id,))
        loan = cursor.fetchone()

        if loan is None:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Loan not found'}), 404

        if loan[1] == 'returned':
            cursor.close()
            conn.close()
            return jsonify({'error': 'Book already returned'}), 400

        cursor.execute("""
            UPDATE loans
            SET return_date = CURRENT_DATE, status = 'returned'
            WHERE id = %s
        """, (loan_id,))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Book returned successfully'})

    except Exception as e:
        logging.error(f"Error returning book: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/books/available', methods=['GET'])
def get_available_books():
    """Получить список доступных для аренды книг"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT b.id, b.title, b.author, b.year, g.name as genre
            FROM books b
            LEFT JOIN genres g ON b.genre_id = g.id
            WHERE b.id NOT IN (
                SELECT book_id FROM loans WHERE status = 'active'
            )
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
                'genre': book[4]
            })

        return jsonify({
            'books': books_list,
            'count': len(books_list)
        })

    except Exception as e:
        logging.error(f"Error getting available books: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Loans Service...")
    check_env(vars_to_check)

    print(f"Loans Service is listening on {os.getenv('API_HOST')}:{os.getenv('API_PORT')}")
    app.run(host=os.getenv('API_HOST'), port=os.getenv('API_PORT'), debug=True)
