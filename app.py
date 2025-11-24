from flask import Flask, jsonify, request
import os
import socket
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# カスタムメトリクス
metrics.info('app_info', 'Application info', version='2.0', service='api-server')

DB_HOST = os.getenv('DB_HOST', 'postgresql')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'appdb')
DB_USER = os.getenv('DB_USER', 'appuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'apppassword')

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized")
    except Exception as e:
        print(f"Database init error: {e}")

init_db()

@app.route('/')
def info():
    return jsonify({
        'service': 'API Server',
        'hostname': socket.gethostname(),
        'version': os.getenv('APP_VERSION', 'v2.0-db'),
        'database': f'{DB_HOST}:{DB_PORT}/{DB_NAME}',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/metrics')
def prometheus_metrics():
    # prometheus_flask_exporterが自動的に/metricsを提供
    pass

@app.route('/api/items', methods=['GET'])
def get_items():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM items ORDER BY id')
        items = cur.fetchall()
        cur.close()
        conn.close()
        # datetime を文字列に変換
        for item in items:
            if item.get('created_at'):
                item['created_at'] = item['created_at'].isoformat()
        return jsonify({'items': items, 'count': len(items)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM items WHERE id = %s', (item_id,))
        item = cur.fetchone()
        cur.close()
        conn.close()
        if item:
            if item.get('created_at'):
                item['created_at'] = item['created_at'].isoformat()
            return jsonify(dict(item))
        return jsonify({'error': 'Item not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items', methods=['POST'])
def create_item():
    try:
        data = request.get_json()
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            'INSERT INTO items (name, description) VALUES (%s, %s) RETURNING *',
            (data.get('name', 'New Item'), data.get('description', ''))
        )
        new_item = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if new_item.get('created_at'):
            new_item['created_at'] = new_item['created_at'].isoformat()
        return jsonify(dict(new_item)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/ready')
def ready():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({'status': 'ready'}), 200
    except:
        return jsonify({'status': 'not ready'}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
