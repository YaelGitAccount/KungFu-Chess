"""

"""
class GameRoom:
    def __init__(self, room_id):
        self.room_id = room_id
        self.players = []  # רשימת WebSocket של שחקנים

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