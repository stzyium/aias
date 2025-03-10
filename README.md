# Aias
 Ai based Smart adn Automated Attendance System
### PyInstaller build command
 ```bash
 pyinstaller --onefile --add-data "web;web/" --add-data "Configs;Configs/"--icon=icon.ico --name=aias-build  __main__.py --optimize=2 --clean
 ```
 The build can be found at `dist/aias-build.exe`.
## Run the appilcation and visit http://127.0.0.1:8000/
 Version v1.24 beta
## [Features]
- Automated system
- Attendance tracking
- Detailed camera frame
## [ADDED] (v1.24-beta)
- Dashboard
- Image viewer
- Attendance viewer
- Tracker stop button
- Settings
- Asynchronous API server
- and more
## [CHANGED] (v1.24-beta)
- Improved UI/UX
- Now using Api for some tasks instead of websocket
- Improved performance
- Default HTTP port to 8000
- Students registration in JSON format
- and more
