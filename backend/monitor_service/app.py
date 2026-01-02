# monitor service app.py

import os
from datetime import datetime
import logging

from flask import Flask, jsonify
import psycopg2

from common.env_checker import check_env

# ==============================================================================
vars_to_check = [
    'BOOKS_SERVICE_API_URL',
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

def check_db_connection():
    config = get_db_config()
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            connect_timeout=5
        )

        # get db basic info
        cursor = conn.cursor()
        cursor.execute("SELECT version(), current_database(), current_user")
        db_info = cursor.fetchone()

        cursor.execute("SELECT count(*) FROM pg_database")
        db_count = cursor.fetchone()[0]

        cursor.execute("SELECT count(*) FROM pg_tables WHERE schemaname = 'public'")
        table_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            'status': 'connected',
            'message': 'Successfully connected to database',
            'database_info': {
                'version': db_info[0],
                'database_name': db_info[1],
                'current_user': db_info[2],
                'total_databases': db_count,
                'tables_in_public': table_count
            },
            'config': {k: v for k, v in config.items() if k != 'password'},
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'config': {k: v for k, v in config.items() if k != 'password'},
            'timestamp': datetime.now().isoformat()
        }


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.route('/api/db/status', methods=['GET'])
def get_db_status():
    status = check_db_connection()
    return jsonify(status)


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'service': 'System Monitor API',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("Starting System Monitor...")
    check_env(vars_to_check)

    print(f"System Monitor service is listening on {os.getenv('API_HOST')}:{os.getenv('API_PORT')}")
    app.run(host=os.getenv('API_HOST'), port=os.getenv('API_PORT'), debug=True)
