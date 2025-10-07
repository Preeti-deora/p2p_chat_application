#!/usr/bin/env python3
"""
Global network discovery via relay server.
Handles cross-network peer discovery when local network discovery isn't sufficient.
"""

from __future__ import annotations
import json
import socket
import threading
import time
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Optional, Callable

# Default relay server (you can change this to your own server)
DEFAULT_RELAY_HOST = "p2p-relay.glitch.me"  # Free hosting service
DEFAULT_RELAY_PORT = 443
DEFAULT_RELAY_URL = f"https://{DEFAULT_RELAY_HOST}"

class GlobalDiscovery:
    """
    Manages global peer discovery through a relay server.
    Works alongside local discovery for cross-network communication.
    """
    
    def __init__(self, name: str, tcp_port: int, on_peer_update: Optional[Callable] = None):
        self.name = name
        self.tcp_port = tcp_port
        self.on_peer_update = on_peer_update or (lambda: None)
        
        # Configuration
        self.relay_url = DEFAULT_RELAY_URL
        self.update_interval = 10.0  # seconds between updates
        self.peer_ttl = 30.0  # seconds until peer considered offline
        
        # State
        self._running = threading.Event()
        self._peers: Dict[str, Dict] = {}  # peer_id -> peer_info
        self._lock = threading.Lock()
        self._update_thread: Optional[threading.Thread] = None
        
        # Public IP detection
        self.public_ip: Optional[str] = None
        self._detect_public_ip()
    
    def start(self):
        """Start global discovery service."""
        if not self.public_ip:
            print("Warning: Could not detect public IP, global discovery disabled")
            return
        
        self._running.set()
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()
        
        # Initial update
        self._update_presence()
    
    def stop(self):
        """Stop global discovery service."""
        self._running.clear()
        if self._update_thread:
            self._update_thread.join(timeout=2.0)
        
        # Remove our presence from relay
        try:
            self._remove_presence()
        except Exception:
            pass
    
    def get_global_peers(self) -> List[Dict]:
        """Get list of peers discovered globally."""
        with self._lock:
            now = time.time()
            # Filter expired peers
            expired = [peer_id for peer_id, peer_info in self._peers.items() 
                      if now - peer_info.get('last_seen', 0) > self.peer_ttl]
            for peer_id in expired:
                del self._peers[peer_id]
            
            return list(self._peers.values())
    
    def _detect_public_ip(self):
        """Detect our public IP address."""
        try:
            # Try multiple services for reliability
            services = [
                "https://api.ipify.org",
                "https://ipv4.icanhazip.com",
                "https://checkip.amazonaws.com"
            ]
            
            for service in services:
                try:
                    with urllib.request.urlopen(service, timeout=5) as response:
                        self.public_ip = response.read().decode('utf-8').strip()
                        if self.public_ip:
                            break
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Failed to detect public IP: {e}")
            self.public_ip = None
    
    def _update_loop(self):
        """Main update loop - runs in background thread."""
        while self._running.is_set():
            try:
                self._update_presence()
                self._fetch_peers()
                self.on_peer_update()
            except Exception as e:
                print(f"Global discovery error: {e}")
            
            # Wait for next update
            for _ in range(int(self.update_interval * 10)):
                if not self._running.is_set():
                    break
                time.sleep(0.1)
    
    def _update_presence(self):
        """Update our presence on the relay server."""
        if not self.public_ip:
            return
            
        data = {
            'action': 'update',
            'peer_id': self._get_peer_id(),
            'name': self.name,
            'public_ip': self.public_ip,
            'tcp_port': self.tcp_port,
            'timestamp': time.time()
        }
        
        try:
            self._send_to_relay(data)
        except Exception as e:
            print(f"Failed to update presence: {e}")
    
    def _fetch_peers(self):
        """Fetch list of peers from relay server."""
        data = {
            'action': 'list',
            'exclude': self._get_peer_id()
        }
        
        try:
            response = self._send_to_relay(data)
            if response and 'peers' in response:
                with self._lock:
                    for peer_info in response['peers']:
                        peer_id = peer_info.get('peer_id')
                        if peer_id:
                            self._peers[peer_id] = peer_info
        except Exception as e:
            print(f"Failed to fetch peers: {e}")
    
    def _remove_presence(self):
        """Remove our presence from relay server."""
        data = {
            'action': 'remove',
            'peer_id': self._get_peer_id()
        }
        
        try:
            self._send_to_relay(data)
        except Exception as e:
            print(f"Failed to remove presence: {e}")
    
    def _send_to_relay(self, data: Dict) -> Optional[Dict]:
        """Send data to relay server and get response."""
        try:
            # Prepare request
            json_data = json.dumps(data).encode('utf-8')
            
            req = urllib.request.Request(
                f"{self.relay_url}/api",
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except urllib.error.URLError as e:
            print(f"Network error communicating with relay: {e}")
            return None
        except Exception as e:
            print(f"Error communicating with relay: {e}")
            return None
    
    def _get_peer_id(self) -> str:
        """Generate unique peer ID."""
        return f"{self.name}@{self.public_ip}:{self.tcp_port}"


class RelayServer:
    """
    Simple relay server implementation.
    Can be deployed to any hosting service for global discovery.
    """
    
    def __init__(self):
        self.peers: Dict[str, Dict] = {}
        self.lock = threading.Lock()
    
    def handle_request(self, data: Dict) -> Dict:
        """Handle incoming request from peer."""
        action = data.get('action')
        
        if action == 'update':
            return self._handle_update(data)
        elif action == 'list':
            return self._handle_list(data)
        elif action == 'remove':
            return self._handle_remove(data)
        else:
            return {'error': 'Unknown action'}
    
    def _handle_update(self, data: Dict) -> Dict:
        """Handle peer presence update."""
        peer_id = data.get('peer_id')
        if not peer_id:
            return {'error': 'Missing peer_id'}
        
        with self.lock:
            self.peers[peer_id] = {
                'peer_id': peer_id,
                'name': data.get('name', 'Unknown'),
                'public_ip': data.get('public_ip'),
                'tcp_port': data.get('tcp_port'),
                'last_seen': time.time()
            }
        
        return {'status': 'updated'}
    
    def _handle_list(self, data: Dict) -> Dict:
        """Handle peer list request."""
        exclude = data.get('exclude')
        ttl = 30.0  # 30 seconds TTL
        
        with self.lock:
            now = time.time()
            # Clean expired peers
            expired = [peer_id for peer_id, peer_info in self.peers.items()
                      if now - peer_info.get('last_seen', 0) > ttl]
            for peer_id in expired:
                del self.peers[peer_id]
            
            # Get active peers
            active_peers = []
            for peer_id, peer_info in self.peers.items():
                if peer_id != exclude:
                    active_peers.append(peer_info.copy())
        
        return {'peers': active_peers}
    
    def _handle_remove(self, data: Dict) -> Dict:
        """Handle peer removal."""
        peer_id = data.get('peer_id')
        if peer_id:
            with self.lock:
                self.peers.pop(peer_id, None)
        
        return {'status': 'removed'}


# Example Flask server for deployment
def create_flask_server():
    """Create Flask server for relay deployment."""
    try:
        from flask import Flask, request, jsonify
        import threading
        
        app = Flask(__name__)
        relay = RelayServer()
        
        @app.route('/api', methods=['POST'])
        def api():
            try:
                data = request.get_json()
                response = relay.handle_request(data)
                return jsonify(response)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @app.route('/health', methods=['GET'])
        def health():
            return jsonify({'status': 'ok', 'peers': len(relay.peers)})
        
        return app
        
    except ImportError:
        print("Flask not available. Install with: pip install flask")
        return None


if __name__ == "__main__":
    # Test the global discovery
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Run as relay server
        app = create_flask_server()
        if app:
            print("Starting relay server...")
            app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        # Test client
        def on_update():
            print("Peer list updated")
        
        discovery = GlobalDiscovery("TestUser", 12345, on_update)
        discovery.start()
        
        try:
            while True:
                peers = discovery.get_global_peers()
                print(f"Global peers: {len(peers)}")
                for peer in peers:
                    print(f"  - {peer['name']} ({peer['public_ip']}:{peer['tcp_port']})")
                time.sleep(5)
        except KeyboardInterrupt:
            discovery.stop()
            print("Stopped")