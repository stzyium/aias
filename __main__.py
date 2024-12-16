import asyncio
import json
import websockets
from aiohttp import web
from pathlib import Path
from attendance import Attendance, getRandomImage, rcd
import webbrowser
import sys
import os
import time
import datetime
import base64

HTTP_PORT = 8000
WS_PORT = 5000
WEB_DIRECTORY = Path("web")
__version__ = '1.24'

if getattr(sys, 'frozen', False):
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path(__file__).parent

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
async def dash(request):
    file_path = WEB_DIRECTORY / "settings.html"
    if file_path.exists():
        return web.FileResponse(file_path)
    else:
        return web.Response(status=404, text="File not found")
async def fec(request):
    file_path = WEB_DIRECTORY / "fevicon.ico"
    if file_path.exists():
        return web.FileResponse(file_path)
    else:
        return web.Response(status=404, text="File not found")
async def api(request):
    endpoint = request.match_info["endpoint"]
    if endpoint == 'trainmodel':
        trained = await Attendance.trainImage()
        if trained:
            print("\033[93m[DEBUG]\033[0m", "Trained model")
        return web.Response(status=200, text="Trained Succesfully...") 
    elif endpoint == 'stoptracking':
        rcd()
        return web.Response(status=200, text="Tracking stopped...")
    else:
        if not os.path.exists('Data/Details/registered.json'):
            return web.Response(status=404, text="File not found")
        with open('Data/Details/registered.json', 'r') as f:
            data = json.load(f)
        if endpoint == 'classes':
            keys = [keys for keys in data]
            return web.json_response(json.dumps(keys))
        elif endpoint == 'sections':
            cl = request.query.get('class', None)
            keys = [keys for keys in data[str(cl)]]
            return web.json_response(json.dumps(keys))
        elif endpoint == 'students':
            cl = request.query.get('class', None)
            sec = request.query.get('section', None)
            students = data[cl][sec]
            return web.json_response(students)
        elif endpoint == 'pfp':
            cl = request.query.get('class', None)
            sec = request.query.get('section', None)
            roll = request.query.get('roll', None)
            image = getRandomImage(data[cl][sec][roll]['path'])
            return web.json_response(json.dumps({ "image": image, "path": os.path.join(os.getcwd(), data[cl][sec][roll]['path'])}))
        elif endpoint == 'getimages':
            cls = request.query.get("cls", None)
            sec = request.query.get("sec", None)
            roll = request.query.get("roll", None)
            IMAGE_FOLDER = f"Data/TrainingImages/Class#{cls}/Section#{sec}/Roll#{roll}"
            try:
                image_files = os.listdir(IMAGE_FOLDER)
                images_base64 = []
                image_files = [f for f in image_files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                for image_filename in image_files:
                    image_path = os.path.join(IMAGE_FOLDER, image_filename)
                    with open(image_path, "rb") as img_file:
                        image_bytes = img_file.read()
                    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
                    images_base64.append(f"data:image/jpeg;base64,{encoded_image}")
                return web.json_response({"images": images_base64})
            except Exception as e:
                return web.json_response({'error': str(e)}, status=500) 
    return web.Response(status=404, text="File not found")
async def pllimages(request):
    file_path = WEB_DIRECTORY / "imageview.html"
    if file_path.exists():
        return web.FileResponse(file_path)
    else:
        return web.Response(status=404, text="File not found")
async def attendance(request):
    endpoint = request.match_info["date"]
    if endpoint == 'get':
        files = os.listdir('Data/At')
        json_files = [file[:-5] for file in files if file.endswith(".json")]
        return web.json_response(json.dumps({ "dates": json_files}))
    if endpoint+'.json' not in os.listdir('Data/At'):
        return web.Response(status=404, text="Record not Found")
    return web.FileResponse(WEB_DIRECTORY / "attendancelog.html")
async def attendancedata(request):
    end = request.match_info["date"]
    if end+'.json' not in os.listdir('Data/At'):
        return web.Response(status=404, text="Record not Found")
    with open(f"Data/At/{end}.json") as e:
        data = json.load(e)
    return web.json_response(data)
async def tests(requests):
    file_path = WEB_DIRECTORY / "ts.html"
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
            print("\033[93m[DEBUG]\033[0m", str(data)[1:-1])
            if data['type'] == 'capture':
                name = data['name']
                roll = data['roll']
                clas = data['class']
                section = data['section']
                await Attendance.capture(websocket, name, roll, clas, section)
            elif data['type'] == 'track':
                await Attendance.trackImage(websocket)
    except Exception as e:
        print(f"\033[93m[SOCKET]\033[0m {e}")


RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
WHITE = "\033[1m"
GRAY = "\033[90m"

async def start_http_server():
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/script', script)
    app.router.add_get('/style', style)
    app.router.add_get('/kvs', image)
    app.router.add_get('/api/{endpoint}', api)
    app.router.add_get('/attendance/{date}', attendance)
    app.router.add_get('/dash', dash)
    app.router.add_get('/attendance/{date}/api/data', attendancedata)
    app.router.add_get('/images/view', pllimages)
    app.router.add_get('/test', tests)
    app.router.add_get('/favicon.ico', fec)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", HTTP_PORT)
    await site.start()
    print(f"{GRAY}[{datetime.datetime.now().strftime('%d-%m-%Y')}]{RESET} :: HTTP server running on \033[4;94mhttp://127.0.0.1:{HTTP_PORT}\033[0m")
    webbrowser.open(f'http://127.0.0.1:{HTTP_PORT}')


async def start_websocket_server():
    server = await websockets.serve(socket, "127.0.0.1", WS_PORT)  
    print(f"{GRAY}[{datetime.datetime.now().strftime('%d-%m-%Y')}]{RESET} :: WebSocket server started at \033[92mws://127.0.0.1:{WS_PORT}\033[0m")
    print()
    print("\033[1;90m> Send Ctrl+C to stop\033[0m")
    print()
    await server.wait_closed()


async def main():
    http_server = asyncio.create_task(start_http_server())
    websocket_server = asyncio.create_task(start_websocket_server())
    await asyncio.gather(http_server, websocket_server)


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
    sys.stdout.write(f"{GRAY}[PYTHON {sys.version.partition('(')[0].strip()}]{RESET} {WHITE}AiBAS Beta Build v{__version__} (windows) [Compiled using PyInstaller==6.11.1]{RESET}\n")
    sys.stdout.write(f"{WHITE}This is an Alpha version. It lacks many features, may contain bugs, and is under active development.{RESET}\n")
    sys.stdout.write(f"{YELLOW}[Known limitations include incomplete functionality and potential instability.]{RESET}\n\n")
    sys.stdout.write(f"{GRAY}[{datetime.datetime.now().strftime('%d-%m-%Y')}]{RESET} Setting up data directories and configurations [...]{RESET}\r")
    sys.stdout.flush()
    time.sleep(1)
    createdata()
    sys.stdout.write(f"{GRAY}[{datetime.datetime.now().strftime('%d-%m-%Y')}]{RESET} Setting up data directories and configurations {GREEN}[DONE]{RESET}\n")
    time.sleep(1)
    sys.stdout.write(f"{GRAY}[{datetime.datetime.now().strftime('%d-%m-%Y')}]{RESET} Initializing Servers {CYAN}[ws/WebSockets] [http/AioHttp]{RESET}\n")
    sys.stdout.flush()
    print()
    time.sleep(1)
    asyncio.run(main())

except KeyboardInterrupt:
    text = "> Stopping servers..."
    sys.stdout.write(f"{get_color(text)}{text}{RESET}\n")
