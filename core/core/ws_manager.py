from typing import Dict, List, Optional
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        if user_id not in self.active_connections.keys():
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_connections.keys():
            self.active_connections[user_id].remove(websocket)
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int):
        try:
            if user_id in self.active_connections:
                for conn in self.active_connections[user_id]:
                    await conn.send_text(message)
        except Exception as e:
            self.active_connections[user_id] = []

    def is_connected(self, user_id: int):
        return user_id in self.active_connections.keys()

    async def broadcast(self, message: str):
        for connections in self.active_connections.values():
            for conn in connections:
                await conn.send_text(message)
        print(self.active_connections)


manager = ConnectionManager()
