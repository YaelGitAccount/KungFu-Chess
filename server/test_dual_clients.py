import asyncio
import websockets
import json

SERVER_URL = "ws://localhost:8765"
ROOM_ID = "room123"

async def player(name, messages_to_send):
    async with websockets.connect(SERVER_URL) as ws:
        print(f"[{name}] connected")

        # Send join message
        join_msg = {
            "type": "join",
            "room_id": ROOM_ID,
            "player_name": name
        }
        await ws.send(json.dumps(join_msg))

        async def receiver():
            try:
                async for msg in ws:
                    data = json.loads(msg)
                    print(f"[{name} received]: {data}")
            except websockets.exceptions.ConnectionClosed:
                print(f"[{name}] disconnected")

        async def sender():
            for msg in messages_to_send:
                await asyncio.sleep(1)
                await ws.send(json.dumps({
                    "type": "chat",
                    "room_id": ROOM_ID,
                    "player_name": name,
                    "message": msg
                }))
            await asyncio.sleep(2)
            await ws.close()

        await asyncio.gather(receiver(), sender())

async def main():
    await asyncio.gather(
        player("Alice", ["Hello!", "How are you?", "I'm ready"]),
        player("Bob", ["Hi!", "All good.", "Let's play"])
    )

if __name__ == "__main__":
    asyncio.run(main())
