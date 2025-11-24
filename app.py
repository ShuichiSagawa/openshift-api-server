from flask import Flask, jsonify, request
import os
import socket
from datetime import datetime

app = Flask(__name__)

   # シンプルなインメモリデータストア
items = [
   {"id": 1, "name": "Item 1", "description": "First item"},
   {"id": 2, "name": "Item 2", "description": "Second item"},
]

@app.route('/')
def info():
    return jsonify({
        'service': 'API Server',
        'hostname': socket.gethostname(),
        'version': os.getenv('APP_VERSION', 'v1.0'),
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/items', methods=['GET'])
def get_items():
    return jsonify({'items': items, 'count': len(items)})

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = next((i for i in items if i['id'] == item_id), None)
    if item:
        return jsonify(item)
    return jsonify({'error': 'Item not found'}), 404

@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.get_json()
    new_id = max(i['id'] for i in items) + 1 if items else 1
    new_item = {
        'id': new_id,
        'name': data.get('name', 'New Item'),
        'description': data.get('description', '')
    }
    items.append(new_item)
    return jsonify(new_item), 201

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
