# room_manager.py
from GameRoom import GameRoom

class RoomManager:
    def __init__(self):
        self.rooms = {}  # room_id -> GameRoom

    def get_or_create_room(self, room_id):
        if room_id not in self.rooms:
            self.rooms[room_id] = GameRoom(room_id)
        return self.rooms[room_id]
    
    def cleanup_empty_room(self, room_id):
        """Clean up the room if it is empty."""
        if room_id in self.rooms:
            room = self.rooms[room_id]
            if len(room.players) == 0:
                if hasattr(room, 'processing_task'):
                    room.processing_task.cancel()
                del self.rooms[room_id]
                print(f"Room {room_id} cleaned up")