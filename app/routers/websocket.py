"""
WebSocket endpoint for real-time signal push.
Clients connect to /ws/signals and receive JSON signal objects
whenever new signals are generated.
"""
import asyncio
import json
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# In-process connection registry
_connected: Set[WebSocket] = set()


async def broadcast_signal(signal: dict):
    """
    Broadcast a signal dict to all connected WebSocket clients.
    Called from signal_service after inserting a new signal.
    Dead connections are pruned automatically.
    """
    dead = set()
    message = json.dumps({"type": "NEW_SIGNAL", "data": signal})

    for ws in list(_connected):
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)

    _connected.difference_update(dead)


@router.websocket("/signals")
async def ws_signals(websocket: WebSocket):
    """
    WebSocket endpoint: ws://<host>/ws/signals
    Sends a heartbeat every 30 s and broadcasts new signals in real time.
    """
    await websocket.accept()
    _connected.add(websocket)

    try:
        while True:
            # Heartbeat to keep connection alive through proxies / load balancers
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "PING"}))
    except WebSocketDisconnect:
        pass
    finally:
        _connected.discard(websocket)
