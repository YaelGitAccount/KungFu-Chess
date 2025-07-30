"""
This module defines the GameRoom class, which manages a game room for two players.
It includes methods for adding players, checking if the room is full, and broadcasting messages to all

מייצג חדר משחק בודד — כל חדר מכיל עד שני שחקנים (WebSocketים), ויש לו מזהה (room_id).
בנוסף, הוא יודע לשדר הודעה לכל השחקנים שבחדר.
"""
import asyncio


class GameRoom:
    def __init__(self, room_id):
        self.room_id = room_id
        self.clients = set()
        self.players = []  # רשימת WebSocket של שחקנים
        self.queue = asyncio.Queue()
        self.processing_task = asyncio.create_task(self.process_messages())

    de

    def add_player(self, ws):
        if len(self.players) < 2:
            self.players.append(ws)
            return True
        return False

    def is_full(self):
        return len(self.players) == 2

    async def broadcast(self, message: str):
        for ws in self.players:
            if ws.open:
                await ws.send(message)