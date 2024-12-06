import asyncio
import json
import websockets
from aiohttp import web
from pathlib import Path
from attendance import Attendance
import webbrowser
import sys
import os
import time

HTTP_PORT = 3000
WS_PORT = 5000
WEB_DIRECTORY = Path("web")

if getattr(sys, 'frozen', False):
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path(__file__).parent
    print(base_path)

WEB_DIRECTORY = base_path / "web"
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
    try:
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
    except Exception as e:
        print(f"Error in socket communication: {e}")


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
    print(f":: HTTP server running on \033[4;94mhttp://127.0.0.1:{HTTP_PORT}\033[0m")
    webbrowser.open(f'http://127.0.0.1:{HTTP_PORT}')


async def start_websocket_server():
    server = await websockets.serve(socket, "127.0.0.1", WS_PORT)  
    print(f":: WebSocket server started at \033[92mws://127.0.0.1:{WS_PORT}\033[0m")
    print()
    print("\033[1;90m> Send Ctrl+C to stop\033[0m")
    print()
    await server.wait_closed()


async def main():
    http_server = asyncio.create_task(start_http_server())
    websocket_server = asyncio.create_task(start_websocket_server())
    await asyncio.gather(http_server, websocket_server)

RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
WHITE = "\033[1m"
GRAY = "\033[90m"

def get_color(text):
    if "error" in text.lower() or "fail" in text.lower():
        return RED
    elif "done" in text.lower() or "success" in text.lower():
        return GREEN
    elif "setting up" in text.lower() or "initializing" in text.lower():
        return CYAN
    else:
        return WHITE
def exception(exc_type, exc_value, exc_tb):
    print(f"{RED}[Exception <{str(exc_type)[7:]}]{RESET} {exc_value}")
try:
    sys.excepthook = exception
    sys.stdout.write(f"{WHITE}AiBAS Alpha Build v0.1.24a (windows) [Compiled using PyInstaller==6.11.1]{RESET}\n")
    sys.stdout.write(f"{WHITE}This is an Alpha version. It lacks many features, may contain bugs, and is under active development.{RESET}\n")
    sys.stdout.write(f"{YELLOW}[Known limitations include incomplete functionality and potential instability.]{RESET}\n\n")
    sys.stdout.write(f"+ Setting up data directories and configurations [...]{RESET}\r")
    sys.stdout.flush()
    time.sleep(1)
    createdata()
    sys.stdout.write(f"+ Setting up data directories and configurations {GREEN}[DONE]{RESET}\n")
    time.sleep(1)
    sys.stdout.write(f"+ Initializing Servers {CYAN}[ws/WebSockets] [http/AioHttp]{RESET}\n")
    sys.stdout.flush()
    print()
    time.sleep(1)
    asyncio.run(main())

except KeyboardInterrupt:
    text = "> Stopping servers..."
    sys.stdout.write(f"{get_color(text)}{text}{RESET}\n")
