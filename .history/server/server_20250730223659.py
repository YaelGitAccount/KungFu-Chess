# server.py
import asyncio
import websockets
import json
from room_manager import RoomManager

room_manager = RoomManager()

async def handle_client(ws):#(ws, path)

    print("New client connected")
    room = None

    try:
        async for msg in ws:
            data = json.loads(msg)
            msg_type = data.get("type")
            room_id = data.get("room_id")

            if not room and room_id:
                room = room_manager.get_or_create_room(room_id)
                room.add_player(ws)

            if room:
                await room.enqueue_message(data, ws)

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        if room:
            room.remove_player(ws)
            print("Client removed from room")
            # אם זה השחקן האחרון בחדר - בטל את המשימה


        #old for players
        # if current_room and ws in current_room.players:
        #     current_room.players.remove(ws)

async def main():
    async with websockets.serve(handle_client, "localhost", 8765):
        print("Server started at ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
