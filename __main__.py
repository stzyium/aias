import asyncio
import json
import websockets
from aiohttp import web
from pathlib import Path
from attendance import Attendance
import webbrowser
import sys
import os

HTTP_PORT = 3000
WS_PORT = 5000
WEB_DIRECTORY = Path("web")

if getattr(sys, 'frozen', False):
    base_path = Path(sys._MEIPASS)
    print(base_path)
else:
    base_path = Path(__file__).parent
    print(base_path)

print(base_path)
WEB_DIRECTORY = base_path / "web"
print(WEB_DIRECTORY)
async def index(request):
    file_path = WEB_DIRECTORY / "index.html"
    if file_path.exists():
        return web.FileResponse(file_path)
    else:
        return web.Response(status=404, text="File not found")

async def style(request):
    file_path = WEB_DIRECTORY / "styles.css"
    if file_path.exists():
        return web.FileResponse(file_path)
    else:
        return web.Response(status=404, text="File not found")

async def script(request):
    file_path = WEB_DIRECTORY / "scripts.js"
    if file_path.exists():
        return web.FileResponse(file_path)
    else:
        return web.Response(status=404, text="File not found")

async def image(request):
    file_path = WEB_DIRECTORY / "kai.png"
    if file_path.exists():
        return web.FileResponse(file_path)
    else:
        return web.Response(status=404, text="File not found")

def createdata():
    if not os.path.exists("Data"):
        os.makedirs("data")
async def socket(websocket):
    #try:
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == 'capture':
                print(data)
                name = data['name']
                roll = data['roll']
                clas = data['class']
                section = data['section']
                await Attendance.capture(websocket, name, roll, clas, section)
            elif data['type'] == 'track':
                await Attendance.trackImage(websocket)
            else:
                await Attendance.trackImage()
    # except Exception as e:
    #     print(f"Error in socket communication: {e}")


async def start_http_server():
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/script', script)
    app.router.add_get('/style', style)
    app.router.add_get('/kvs', image)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", HTTP_PORT)
    await site.start()
    print(f"HTTP server running on http://127.0.0.1:{HTTP_PORT}")
    webbrowser.open(f'http://127.0.0.1:{HTTP_PORT}')


async def start_websocket_server():
    server = await websockets.serve(socket, "127.0.0.1", WS_PORT)  
    print(f"WebSocket server started at ws://127.0.0.1:{WS_PORT}")
    await server.wait_closed()


async def main():
    http_server = asyncio.create_task(start_http_server())
    websocket_server = asyncio.create_task(start_websocket_server())
    await asyncio.gather(http_server, websocket_server)

try:
    createdata()
    asyncio.run(main())
except KeyboardInterrupt:
    print("Stopping servers...")
