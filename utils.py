import os
from PIL import Image
import json
import numpy as np
import time

def manage_subfolders_with_sections_windows(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    required_classes = {f"Class#{i}" for i in range(1, 13)}
    required_sections = {f"Section#{chr(c)}" for c in range(ord('A'), ord('H') + 1)}

    current_folders = {f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))}

    unwanted_classes = current_folders - required_classes
    for folder in unwanted_classes:
        folder_to_delete = os.path.join(folder_path, folder)
        try:
            for root, dirs, files in os.walk(folder_to_delete, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(folder_to_delete)
        except Exception as e:
            print(f"Failed to delete {folder_to_delete}: {e}")
    missing_classes = required_classes - current_folders
    for folder in missing_classes:
        folder_to_create = os.path.join(folder_path, folder)
        os.makedirs(folder_to_create, exist_ok=True)
    for class_folder in required_classes:
        class_path = os.path.join(folder_path, class_folder)
        os.makedirs(class_path, exist_ok=True)
        current_sections = {f for f in os.listdir(class_path) if os.path.isdir(os.path.join(class_path, f))}

        unwanted_sections = current_sections - required_sections
        for section in unwanted_sections:
            section_to_delete = os.path.join(class_path, section)
            try:
                for root, dirs, files in os.walk(section_to_delete, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(section_to_delete)
            except Exception as e:
                print(f"Failed to delete section {section_to_delete}: {e}")
        missing_sections = required_sections - current_sections
        for section in missing_sections:
            section_to_create = os.path.join(class_path, section)
            os.makedirs(section_to_create, exist_ok=True)
    return 200

def idtoint(id):
    return int(id[:-1]+str(ord(id[-1])))

def inttoid(id):
    return str(id)[:-2]+chr(int(str(id)[-2:]))

def getImagesAndLabels():
    with open('Data/Details/registered.json', 'r') as file:
        data = json.load(file)
    faces = []
    Ids = []
    for dat in data:
        for sec in data[dat]:
            for roll in data[dat][sec]:
                imagePath = data[dat][sec][roll]['path']
                for path in os.listdir(imagePath):
                    pilImage = Image.open(os.path.join(imagePath, path)).convert('L')
                    imageNp = np.array(pilImage, 'uint8')
                    Id = data[dat][sec][roll]['id']
                    faces.append(imageNp)
                    Ids.append(Id)
    return faces, Ids
