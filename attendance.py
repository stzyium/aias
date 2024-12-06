import cv2
import os
import base64
import asyncio
import datetime
import json
from utils import *
parent_folder = r"Data/TrainingImages/"

manage_subfolders_with_sections_windows(parent_folder)

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
        harcascade_path = "Data/Configs/haarcascade_frontalface_default.xml"
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
                    _, jpeg_frame = cv2.imencode('.jpg', cv2.imread('Data/web/kai.png'))
                sidecm = base64.b64encode(jpeg_frame).decode('utf-8')
                fgray = cv2.flip(gray, 2)
                _, jpeg_frame = cv2.imencode('.jpg', fgray)
                key1 = 'sidecamera'
                key = 'camera'
                frame0 = base64.b64encode(jpeg_frame).decode('utf-8')
                await websocket.send(json.dumps({ key: frame0, key1: sidecm, 'text': f' Capturing... {sample_num}/50' }))
        except Exception as e:
            print(f"Error in capture: {e}")
        finally:
            cam.release()
            Attendance.save(frames, name, roll, clas, section)
            frames.clear()
            data = {
                "name": name,
                "roll": roll,
                "class": clas,
                "section": section,
                "path": folder_path
            }
            try:
                with open('Data/Details/registered.json', 'r') as file:
                    registered_data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                registered_data = {}

            registered_data[f"{roll}{clas}{section}"] = data

            with open('Data/Details/registered.json', 'w') as file:
                json.dump(registered_data, file, indent=4)

    async def trackImage(websocket):
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read("Data/Trained.yml")
        faceCascade = cv2.CascadeClassifier("Data/Configs/haarcascade_frontalface_default.xml")

        with open('Data/Details/registered.json', 'r') as file:
            student_data = json.load(file)

        def initDate():
            date = datetime.datetime.now().strftime('%d-%m-%Y')
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

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            name, roll = 'Unknown', '0'
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                Id, conf = recognizer.predict(gray[y:y + h, x:x + w])

                if conf < 60:
                    student_id = inttoid(Id)
                    if student_id in student_data:
                        student_info = student_data[student_id]
                        name = student_info['name']
                        roll = student_info['roll']
                        if student_id not in marked_ids:
                            # Add attendance entry
                            timeStamp = datetime.datetime.now().strftime('%H:%M')
                            attendance_entry = {
                                "NAME": student_info['name'],
                                "ROLL": student_info['roll'],
                                "CLASS": student_info['class'],
                                "ID": student_id,
                                "SECTION": student_info['section'],
                                "TIME": timeStamp
                            }
                            attendance.append(attendance_entry)
                            writeAttendance(attendance_filepath, attendance)
                            marked_ids.add(student_id)
                            status = f"Attendance marked for {student_info['name']} (ID: {Id})"
                        else:
                            status = f"Attendance already marked for ID: {Id}"
                    else:
                        status = f"ID: {Id} not found in the database."
                else:
                    status = "Face not recognizable"

                cv2.flip(img, 2)
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
        return 1
