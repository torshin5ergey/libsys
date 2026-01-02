# readers service app.py

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
        'service': 'Readers Service API',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/readers', methods=['GET'])
def get_readers():
    """Получить всех читателей"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        search_query = request.args.get('search', '').strip()

        if search_query:
            sql = """
                SELECT id, full_name, email, phone, address, registration_date, created_at
                FROM readers
                WHERE full_name ILIKE %s OR email ILIKE %s OR phone ILIKE %s
                ORDER BY full_name
            """
            params = (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%")
            cursor.execute(sql, params)
        else:
            cursor.execute("""
                SELECT id, full_name, email, phone, address, registration_date, created_at
                FROM readers
                ORDER BY full_name
            """)

        readers = cursor.fetchall()

        cursor.close()
        conn.close()

        readers_list = []
        for reader in readers:
            readers_list.append({
                'id': reader[0],
                'full_name': reader[1],
                'email': reader[2],
                'phone': reader[3],
                'address': reader[4],
                'registration_date': reader[5].isoformat() if reader[5] else None,
                'created_at': reader[6].isoformat() if reader[6] else None
            })

        return jsonify({
            'readers': readers_list,
            'count': len(readers_list)
        })

    except Exception as e:
        logging.error(f"Error getting readers: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/readers/<int:reader_id>', methods=['GET'])
def get_reader(reader_id):
    """Получить читателя по ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, full_name, email, phone, address, registration_date, created_at
            FROM readers
            WHERE id = %s
        """, (reader_id,))
        reader = cursor.fetchone()

        cursor.close()
        conn.close()

        if reader is None:
            return jsonify({'error': 'Reader not found'}), 404

        return jsonify({
            'id': reader[0],
            'full_name': reader[1],
            'email': reader[2],
            'phone': reader[3],
            'address': reader[4],
            'registration_date': reader[5].isoformat() if reader[5] else None,
            'created_at': reader[6].isoformat() if reader[6] else None
        })

    except Exception as e:
        logging.error(f"Error getting reader: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/readers', methods=['POST'])
def create_reader():
    """Создать нового читателя"""
    try:
        data = request.json

        if not data or 'full_name' not in data:
            return jsonify({'error': 'Full name is required'}), 400

        full_name = data['full_name'].strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        address = data.get('address', '').strip()

        if not full_name:
            return jsonify({'error': 'Full name cannot be empty'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO readers (full_name, email, phone, address)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (full_name, email, phone, address)
        )

        reader_id = cursor.fetchone()[0]
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Reader created successfully',
            'id': reader_id
        }), 201

    except psycopg2.IntegrityError as e:
        if 'unique constraint' in str(e).lower():
            return jsonify({'error': 'Email already exists'}), 400
        logging.error(f"Integrity error creating reader: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logging.error(f"Error creating reader: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/readers/<int:reader_id>', methods=['PUT'])
def update_reader(reader_id):
    """Обновить читателя"""
    try:
        data = request.json

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM readers WHERE id = %s", (reader_id,))
        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Reader not found'}), 404

        updates = []
        params = []

        if 'full_name' in data and data['full_name']:
            updates.append("full_name = %s")
            params.append(data['full_name'].strip())
        if 'email' in data:
            updates.append("email = %s")
            params.append(data['email'].strip())
        if 'phone' in data:
            updates.append("phone = %s")
            params.append(data['phone'].strip())
        if 'address' in data:
            updates.append("address = %s")
            params.append(data['address'].strip())

        if not updates:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No fields to update'}), 400

        params.append(reader_id)

        query = f"UPDATE readers SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, params)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Reader updated successfully'})

    except psycopg2.IntegrityError as e:
        if 'unique constraint' in str(e).lower():
            return jsonify({'error': 'Email already exists'}), 400
        logging.error(f"Integrity error updating reader: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logging.error(f"Error updating reader: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/readers/<int:reader_id>', methods=['DELETE'])
def delete_reader(reader_id):
    """Удалить читателя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM readers WHERE id = %s", (reader_id,))
        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Reader not found'}), 404

        cursor.execute("DELETE FROM readers WHERE id = %s", (reader_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Reader deleted successfully'})

    except Exception as e:
        logging.error(f"Error deleting reader: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Readers Service...")
    check_env(vars_to_check)

    print(f"Readers Service is listening on {os.getenv('API_HOST')}:{os.getenv('API_PORT')}")
    app.run(host=os.getenv('API_HOST'), port=os.getenv('API_PORT'), debug=True)
