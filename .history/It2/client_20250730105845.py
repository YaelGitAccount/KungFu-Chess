# file: client.py
import asyncio
import websockets

async def hello():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello from client!")
        response = await websocket.recv()
        print(f"Server replied: {response}")

asyncio.run(hello())
