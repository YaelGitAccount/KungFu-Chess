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
        self.players = set()
        # self.players = []  # רשימת WebSocket של שחקנים
        self.queue = asyncio.Queue()
        self.processing_task = asyncio.create_task(self.process_messages())
#############
#לבטל אחד מן השניים הבאים
    # def add_client(self, ws):
    #     self.clients.add(ws)

     #old for players       
    def add_player(self, ws):
        if len(self.players) < 2:
            self.players.add(ws)
            return True
        return False

    def is_full(self):
        return len(self.players) == 2

    def remove_player(self, ws):
        self.players.discard(ws)
     
     #old for players       
    # def remove_player(self, ws):
    #     if ws in self.players:
    #         self.players.remove(ws)

    async def enqueue_message(self, message, player):
        await self.queue.put((message, client))
    async def process_messages(self):
        while True:
            message, client = await self.queue.get()
            msg_type=message.get("type")

            if msg_type == "move":
                # דוגמה: טיפול בהזזת חייל
                await self.broadcast({
                    "type": "move",
                    "from": message["from"],
                    "to": message["to"]
                }, exclude=client)

            elif msg_type == "resign":
                await self.broadcast({"type": "game_over", "reason": "resign"}, exclude=client)

            # תוכל להוסיף כאן טיפול לעוד סוגי הודעות כמו: chat, promotion, etc.

            self.queue.task_done()
     
     #old for players       
    async def broadcast(self, message: str):
        for ws in self.players:
            if ws.open:
                await ws.send(message)

    async def broadcast(self, message: dict, exclude=None):
        for client in self.clients:
            if client != exclude:
                await client.send(json.dumps(message))