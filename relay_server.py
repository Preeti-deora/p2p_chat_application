#!/usr/bin/env python3
"""
Simple relay server for global P2P discovery.
Deploy this to any hosting service (Heroku, Glitch, Railway, etc.)
"""

from flask import Flask, request, jsonify
import json
import time
import threading
from typing import Dict

app = Flask(__name__)

# In-memory storage (in production, use a database)
peers: Dict[str, Dict] = {}
lock = threading.Lock()
PEER_TTL = 30.0  # 30 seconds TTL

@app.route('/api', methods=['POST'])
def api():
    """Handle peer discovery requests."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data'}), 400
        
        action = data.get('action')
        
        if action == 'update':
            return handle_update(data)
        elif action == 'list':
            return handle_list(data)
        elif action == 'remove':
            return handle_remove(data)
        else:
            return jsonify({'error': 'Unknown action'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def handle_update(data):
    """Handle peer presence update."""
    peer_id = data.get('peer_id')
    if not peer_id:
        return jsonify({'error': 'Missing peer_id'}), 400
    
    with lock:
        peers[peer_id] = {
            'peer_id': peer_id,
            'name': data.get('name', 'Unknown'),
            'public_ip': data.get('public_ip'),
            'tcp_port': data.get('tcp_port'),
            'last_seen': time.time()
        }
    
    return jsonify({'status': 'updated'})

def handle_list(data):
    """Handle peer list request."""
    exclude = data.get('exclude')
    
    with lock:
        now = time.time()
        # Clean expired peers
        expired = [peer_id for peer_id, peer_info in peers.items()
                  if now - peer_info.get('last_seen', 0) > PEER_TTL]
        for peer_id in expired:
            del peers[peer_id]
        
        # Get active peers
        active_peers = []
        for peer_id, peer_info in peers.items():
            if peer_id != exclude:
                active_peers.append(peer_info.copy())
    
    return jsonify({'peers': active_peers})

def handle_remove(data):
    """Handle peer removal."""
    peer_id = data.get('peer_id')
    if peer_id:
        with lock:
            peers.pop(peer_id, None)
    
    return jsonify({'status': 'removed'})

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    with lock:
        return jsonify({
            'status': 'ok', 
            'peers': len(peers),
            'timestamp': time.time()
        })

@app.route('/', methods=['GET'])
def index():
    """Simple status page."""
    with lock:
        return f"""
        <h1>P2P Relay Server</h1>
        <p>Status: Running</p>
        <p>Active Peers: {len(peers)}</p>
        <p>Time: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <h3>Active Peers:</h3>
        <ul>
        {''.join(f'<li>{peer["name"]} ({peer["public_ip"]}:{peer["tcp_port"]})</li>' 
                for peer in peers.values())}
        </ul>
        """

if __name__ == '__main__':
    print("Starting P2P Relay Server...")
    print("Deploy this to any hosting service for global discovery")
    app.run(host='0.0.0.0', port=5000, debug=False)