# P2P Chat Relay Server

A simple relay server for P2P chat discovery across different networks.

## Features

- Peer discovery across different networks
- RESTful API for peer management
- Automatic peer cleanup (TTL-based)
- Health monitoring

## API Endpoints

- `POST /api` - Main API endpoint for peer operations
- `GET /health` - Health check endpoint
- `GET /` - Status page showing active peers

## Deployment

This server can be deployed to any Python hosting service that supports Flask.

## Usage

The server automatically handles:
- Peer registration and updates
- Peer list retrieval
- Peer removal
- Automatic cleanup of expired peers