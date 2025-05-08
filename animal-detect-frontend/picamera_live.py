import asyncio
import websockets
import base64

from picamera2 import Picamera2
from io import BytesIO
from PIL import Image

picam = Picamera2()
print(picam.is_open)
picam.configure(picam.create_preview_configuration(main={"size": (640,480)}))
picam.start()


def get_frames():
    while True:
        arr = picam.capture_array()           # RGBA
        img = Image.fromarray(arr).convert("RGB")   # ➜ RGB
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=80)
        yield b"data:image/jpeg;base64," + base64.b64encode(buf.getvalue())

async def handle_connection(connection):
    print("Client connected")
    try:
        # connection.recv() / connection.send() instead of websocket.recv()/send()
        for frame in get_frames():
            await connection.send(frame.decode("utf-8"))
            await asyncio.sleep(0.03)
    except Exception as e:
        print("Connection error:", e)

async def main():
    async with websockets.serve(handle_connection, "0.0.0.0", 8000):
        print("WebSocket server started at ws://0.0.0.0:8000")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
