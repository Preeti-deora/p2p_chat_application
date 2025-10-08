#!/usr/bin/env python3
"""
Enhanced relay server for global P2P discovery + message relay.
Supports both HTTP API (discovery) and WebSocket (messaging).
Deploy this to any hosting service (Heroku, Glitch, Railway, Render, etc.)
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import time
import threading
from typing import Dict

app = Flask(__name__)
app.config['SECRET_KEY'] = 'p2p-chat-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)

# In-memory storage (in production, use a database)
peers: Dict[str, Dict] = {}
messages: Dict[str, list] = {}  # user_id -> list of messages
message_counter = 0
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
        elif action == 'register_messaging':
            return handle_register_messaging(data)
        elif action == 'send_message':
            return handle_send_message(data)
        elif action == 'get_messages':
            return handle_get_messages(data)
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

def handle_register_messaging(data):
    """Register user for message relay"""
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    
    with lock:
        if user_id not in messages:
            messages[user_id] = []
    
    return jsonify({
        'status': 'ok',
        'message': f'Registered for messaging: {user_id}'
    })

def handle_send_message(data):
    """Send message to another user"""
    global message_counter
    
    sender = data.get('sender')
    recipient = data.get('recipient')  
    text = data.get('text')
    
    if not all([sender, recipient, text]):
        return jsonify({'error': 'Missing sender, recipient, or text'}), 400
    
    with lock:
        message_counter += 1
        
        # Add message to recipient's queue
        if recipient not in messages:
            messages[recipient] = []
        
        messages[recipient].append({
            'id': message_counter,
            'sender': sender,
            'text': text,
            'timestamp': time.time()
        })
        
        # Keep only last 100 messages per user
        if len(messages[recipient]) > 100:
            messages[recipient] = messages[recipient][-100:]
    
    return jsonify({
        'status': 'ok',
        'message_id': message_counter
    })

def handle_get_messages(data):
    """Get messages for user"""
    user_id = data.get('user_id')
    since_id = data.get('since_id', 0)
    
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    
    with lock:
        if user_id not in messages:
            messages[user_id] = []
        
        # Get messages newer than since_id
        new_messages = [msg for msg in messages[user_id] if msg['id'] > since_id]
    
    return jsonify({
        'status': 'ok',
        'messages': new_messages,
        'count': len(new_messages)
    })

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

# WebSocket Message Relay (real-time messaging)
connected_users = {}  # session_id -> user_info

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print(f"WebSocket client connected: {request.sid}")
    emit('status', {'message': 'Connected to message relay'})

@socketio.on('disconnect')  
def handle_disconnect():
    """Handle WebSocket disconnection"""
    if request.sid in connected_users:
        user_id = connected_users[request.sid]['user_id']
        leave_room(user_id)
        del connected_users[request.sid]
        print(f"User {user_id} disconnected from message relay")

@socketio.on('register')
def handle_register(data):
    """Register user for message relay"""
    user_id = data.get('user_id')
    if user_id:
        connected_users[request.sid] = {
            'user_id': user_id,
            'session_id': request.sid
        }
        join_room(user_id)  # Join room for direct messaging
        emit('registered', {'user_id': user_id})
        print(f"User {user_id} registered for message relay")

@socketio.on('send_message')
def handle_ws_message(data):
    """Handle WebSocket message sending"""
    if request.sid not in connected_users:
        emit('error', {'message': 'Not registered'})
        return
    
    sender_id = connected_users[request.sid]['user_id']
    recipient_id = data.get('recipient')
    message_text = data.get('text')
    
    if recipient_id and message_text:
        # Send message to recipient's room
        socketio.emit('message', {
            'sender': sender_id,
            'text': message_text,
            'timestamp': time.time()
        }, room=recipient_id)
        
        # Confirm delivery to sender
        emit('delivered', {'recipient': recipient_id})
        print(f"Relayed message from {sender_id} to {recipient_id}")
    else:
        emit('error', {'message': 'Missing recipient or text'})

@socketio.on('ping')
def handle_ping():
    """Handle ping for keepalive"""
    emit('pong')

if __name__ == '__main__':
    print("Starting Enhanced P2P Relay Server...")
    print("- HTTP API for peer discovery")  
    print("- HTTP API for message relay (polling)")
    print("- WebSocket for real-time messaging")
    print("Deploy this to Render for global access")
    
    # Use socketio.run for WebSocket support
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
