# 🌍 Cross-Network P2P Chat Deployment Guide

## Overview

This P2P Desktop App now supports **cross-network communication** using a hybrid approach:

1. **Local Network**: Direct UDP broadcasting (fast, no internet required)
2. **Global Network**: Relay server for cross-network discovery (requires internet)

## 🚀 Quick Start

### For Users (No Setup Required)
```bash
python main.py
```

The app automatically tries to connect to the default relay server for global discovery.

### For Developers (Custom Relay Server)

## 🔧 Setting Up Your Own Relay Server

### Option 1: Deploy to Free Hosting Services

#### Heroku
```bash
# Install Heroku CLI, then:
heroku create your-p2p-relay
git init
git add relay_server.py requirements.txt
git commit -m "Initial relay server"
git push heroku main
```

#### Glitch
1. Go to [glitch.com](https://glitch.com)
2. Create new project
3. Upload `relay_server.py` and `requirements.txt`
4. Deploy automatically

#### Railway
```bash
# Install Railway CLI, then:
railway login
railway init
railway add
railway deploy
```

### Option 2: Run Locally
```bash
pip install flask
python relay_server.py
```

### Option 3: VPS/Cloud Server
```bash
# On your server:
pip install flask
python relay_server.py
# Access via your server's IP:5000
```

## ⚙️ Configuration

### Update Relay Server URL
Edit `net/global_discovery.py`:
```python
DEFAULT_RELAY_HOST = "your-server.com"  # Your server
DEFAULT_RELAY_PORT = 443  # or 5000 for local
DEFAULT_RELAY_URL = f"https://{DEFAULT_RELAY_HOST}"
```

## 🌐 How It Works

### Local Network (Same WiFi/LAN)
- Uses UDP broadcasting on port `54545`
- No internet required
- Fast discovery and messaging

### Global Network (Different Networks)
- Uses relay server for peer discovery
- Direct P2P connections when possible
- Fallback to relay for NAT traversal

### Network Architecture
```
┌─────────────────┐    Internet     ┌─────────────────┐
│   User A        │◄──────────────►│  Relay Server   │
│ (Network A)     │                 │                 │
│                 │                 │                 │
│ TCP Server:12345│◄──────────────►│  Discovery API  │
└─────────────────┘                 └─────────────────┘
         ▲                                    │
         │                                    ▼
┌─────────────────┐                 ┌─────────────────┐
│   User B        │◄──────────────►│   User C        │
│ (Network B)     │    Internet     │ (Network C)     │
│                 │   Direct P2P    │                 │
│ TCP Server:54321│◄──────────────►│ TCP Server:98765│
└─────────────────┘                 └─────────────────┘
```

## 🔒 Security Considerations

### For Relay Server
- The relay server only handles discovery, not messages
- Messages are sent directly P2P when possible
- No message content is stored on relay server
- Consider adding authentication for production use

### For Users
- All messages are encrypted end-to-end (if implemented)
- No central server stores your messages
- Peer discovery is public but messaging is private

## 🚀 Advanced Features

### Custom Relay Server Features
You can extend `relay_server.py` with:
- User authentication
- Message persistence
- File sharing
- Group chats
- Push notifications

### NAT Traversal
For better P2P connectivity:
- Implement STUN/TURN servers
- Use UPnP for port forwarding
- Consider WebRTC for web clients

## 📱 Mobile Support
To support mobile devices:
- Create web version using WebRTC
- Use same relay server architecture
- Implement responsive UI

## 🔧 Troubleshooting

### Common Issues
1. **Can't connect to relay server**
   - Check internet connection
   - Verify relay server is running
   - Check firewall settings

2. **Can't connect to peers globally**
   - NAT/firewall blocking direct connections
   - Try different network
   - Use relay server for message forwarding

3. **Local discovery not working**
   - Check if on same network
   - Verify UDP port 54545 is not blocked
   - Try different network interface

### Debug Mode
Add debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Monitoring

### Relay Server Health
Visit your relay server URL to see:
- Number of active peers
- Server uptime
- Recent activity

### Client Logs
The app prints connection status and errors to console.

## 🎯 Production Deployment

For production use:
1. Use HTTPS for relay server
2. Implement rate limiting
3. Add user authentication
4. Use database for persistence
5. Set up monitoring and alerts
6. Consider load balancing

## 💡 Future Enhancements

- **WebRTC Integration**: Better NAT traversal
- **Mobile Apps**: iOS/Android versions
- **File Sharing**: Send files between peers
- **Voice/Video**: Real-time communication
- **Group Chats**: Multi-user conversations
- **Message Encryption**: End-to-end encryption
- **Offline Support**: Message queuing
- **Push Notifications**: Mobile notifications

---

**Ready to deploy?** Choose your hosting platform and follow the setup guide above! 🚀