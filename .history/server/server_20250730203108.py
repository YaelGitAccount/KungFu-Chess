# server.py
import asyncio
import websockets
import json
from room_manager import RoomManager

room_manager = RoomManager()

async def handle_client(ws, path):

    print("New client connected")
    current_room = None

    try:
        async for msg in ws:
            data = json.loads(msg)
            msg_type = data.get("type")
            room_id = data.get("room_id")

            if not room and room_id:
                room = room_manager.get_or_create_room(room_id)
                room.add_client(ws)

            if room:
                await room.enqueue_message(data, ws)

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
            if msg_type == "join":
                room_id = data["room_id"]
                room = room_manager.get_or_create_room(room_id)
                if not room.add_player(ws):
                    await ws.send(json.dumps({"type": "error", "message": "Room full"}))
                    return
                current_room = room
                await room.broadcast(json.dumps({
                    "type": "status",
                    "message": f"Player joined room {room_id}"
                }))

            elif msg_type == "move":
                if current_room:
                    await current_room.broadcast(json.dumps({
                        "type": "move",
                        "from": data["from"],
                        "to": data["to"]
                    }))

    except websockets.ConnectionClosed:
        print("Client disconnected")
        if current_room and ws in current_room.players:
            current_room.players.remove(ws)

async def main():
    async with websockets.serve(handle_client, "localhost", 8765):
        print("Server started at ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
