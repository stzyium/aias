import cv2
import os
import base64
import asyncio
import random
import datetime
import json
from utils import *
import sys
from pathlib import Path
parent_folder = r"Data/TrainingImages/"
tracker = True
manage_subfolders_with_sections_windows(parent_folder)
def rcd():
    global tracker
    tracker = False
if getattr(sys, 'frozen', False):
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path(__file__).parent
config = base_path / "Configs"
web = base_path / "web"
hascade = config / "haarcascade_frontalface_default.xml"

def getRandomImage(path):
    images = [f for f in os.listdir(path) if f.endswith(".jpg")]
    imagepath = os.path.join(path, random.choice(images))
    _, ff = cv2.imencode('.jpg', cv2.imread(imagepath))
    image = base64.b64encode(ff).decode('utf-8')
    return image
class Attendance:
    def save(frames: list, name, roll, clas, section):
        for sample_num, frame in enumerate(frames):
            folder_path = f"Data/TrainingImages/Class#{clas}/Section#{section}/Roll#{roll}"
            os.makedirs(folder_path, exist_ok=True)
            face_image_path = os.path.join(folder_path, f"{name}.{roll}.{sample_num}.jpg")
            cv2.imwrite(face_image_path, frame)

    async def capture(websocket, name, roll, clas, section):
        if not os.path.exists('Data/Details'):
            os.makedirs('Data/Details')
        frames = []
        cam = cv2.VideoCapture(0)
        harcascade_path = hascade
        detector = cv2.CascadeClassifier(harcascade_path)
        sample_num = 0
        folder_path = f"Data/TrainingImages/Class#{clas}/Section#{section}/Roll#{roll}"
        try:
            while sample_num <= 50:
                ret, img = cam.read()
                if ret is False:
                    print("Failed to capture image from camera.")
                    break
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = detector.detectMultiScale(gray, 1.1, 3)
                sideframe = 0
                for (x, y, w, h) in faces:
                    cv2.rectangle(gray, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    grayimageframe = gray[y:y + h, x:x + w]
                    frames.append(grayimageframe)
                    sideframe = 1
                    sample_num += 1
                    if sample_num > 50:
                        break
                if sideframe != 0:
                    _, jpeg_frame = cv2.imencode('.jpg', grayimageframe)
                else:
                    _, jpeg_frame = cv2.imencode('.jpg', cv2.imread(web / "kai.png"))
                sidecm = base64.b64encode(jpeg_frame).decode('utf-8')
                fgray = cv2.flip(gray, 2)
                _, jpeg_frame = cv2.imencode('.jpg', fgray)
                key1 = 'sidecamera'
                key = 'camera'
                frame0 = base64.b64encode(jpeg_frame).decode('utf-8')
                await websocket.send(json.dumps({ key: frame0, key1: sidecm, 'text': f'Capturing... {sample_num-1}/50' }))
            _, ff = cv2.imencode('.jpg', cv2.imread(web / "kai.png"))
            fim = base64.b64encode(ff).decode('utf-8')
            await websocket.send(json.dumps({ key: fim, key1: fim, 'text': f'Captured and saving required frames.' }))
        except Exception as e:
            print(f"Error in capture: {e}")
        finally:
            cam.release()
            Attendance.save(frames, name, roll, clas, section)
            frames.clear()
            data = {
                clas: {
                    section: {
                        roll: {
                            'name': name,
                            'captured': True,
                            'path': folder_path,
                            'days_attended': 0,
                            'id': f'{roll}00{clas}00{section}'
                        }
                    }
                }
            }

            try:
                with open('Data/Details/registered.json', 'r') as file:
                    registered_data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                registered_data = {}
            if clas not in registered_data:
                registered_data[clas] = {}

            if section not in registered_data[clas]:
                registered_data[clas][section] = {}

            registered_data[clas][section][roll] = {
                'name': name,
                'captured': True,
                'path': folder_path,
                'days_attended': 0,
                'id': f'{roll}00{clas}00{section}'
            }
            with open('Data/Details/registered.json', 'w') as file:
                json.dump(registered_data, file, indent=4)

    async def trackImage(websocket):
        global tracker
        tracker = True
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read("Data/Trained.yml")
        faceCascade = cv2.CascadeClassifier(hascade)

        with open('Data/Details/registered.json', 'r') as file:
            student_data = json.load(file)

        def initDate():
            date = datetime.datetime.now().strftime('%d-%m-%Y')
            if not os.path.exists('Data/At'):
                os.makedirs('Data/At')
            filepath = f'Data/At/{date}.json'
            if not os.path.exists(filepath):
                with open(filepath, 'w') as file:
                    json.dump([], file)
            return filepath

        def readAttendance(filepath):
            with open(filepath, 'r') as file:
                return json.load(file)

        def writeAttendance(filepath, data):
            with open(filepath, 'w') as file:
                json.dump(data, file, indent=4)

        font = cv2.FONT_HERSHEY_COMPLEX_SMALL
        cam = cv2.VideoCapture(0)
        attendance_filepath = initDate()

        attendance = readAttendance(attendance_filepath)
        marked_ids = {entry['ID'] for entry in attendance}

        while True:
            ret, img = cam.read()
            if not ret:
                continue
            if not tracker:
                break
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            name, roll = 'Unknown', '0'
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                Id, conf = recognizer.predict(gray[y:y + h, x:x + w])

                if conf < 60:
                    student_id = inttoid(Id)
                    if not student_id.count('0') >= 4:
                        continue
                    roll, clss, sec = student_id.split('00')
                    ids = [roll["id"] for class_key in student_data.values() for section_key in class_key.values() for roll in section_key.values()]
                    if student_id in ids:
                        student_info = student_data
                        
                        name = student_info[clss][sec][roll]['name']
                        if student_id not in marked_ids:
                            timeStamp = datetime.datetime.now().strftime('%H:%M')
                            attendance_entry = {
                                "NAME": name,
                                "ROLL": roll,
                                "CLASS": clss,
                                "ID": student_id,
                                "SECTION": sec,
                                "TIME": timeStamp
                            }
                            attendance.append(attendance_entry)
                            writeAttendance(attendance_filepath, attendance)
                            marked_ids.add(student_id)
                            status = f"Attendance marked for {name} (ID: {Id})"
                            with open('Data/Details/registered.json', 'r') as file:
                                student_data = json.load(file)
                            with open('Data/Details/registered.json', 'w') as file:
                                student_data[clss][sec][roll]['days_attended'] += 1
                                json.dump(student_data, file, indent=4)
                        else:
                            status = f"Attendance already marked for ID: {Id}"
                    else:
                        status = f"ID: {Id} not found in the database."
                else:
                    status = "Face not recognizable"

                cv2.putText(img, status, (x, y - 10), font, 0.6, (255, 255, 255), 1)
                cv2.putText(img, str(roll) + '; ' + name, (x, y + h + 12 ), font, 0.8, (255, 255, 255), 1)
            _, jpeg_frame = cv2.imencode('.jpg', img)
            frame_data = base64.b64encode(jpeg_frame).decode('utf-8')
            try:
                await websocket.send(json.dumps({"camera": frame_data, "text": status}))
            except:
                await websocket.send(json.dumps({"camera": frame_data, "text": "working on it.."}))

            await asyncio.sleep(0.01)

    async def trainImage():
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        faces, Id = getImagesAndLabels()
        Id = [idtoint(id) for id in Id]
        recognizer.train(faces, np.array(Id))
        recognizer.save("Data/Trained.yml")
        return {'trained': True}
