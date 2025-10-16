GOD’S EYE — AI Face Recognition Surveillance System

God’s Eye is an advanced, AI-powered face recognition surveillance system built using Python, OpenCV, and face_recognition.
It supports multi-camera monitoring (laptop + phone), real-time face logging, and SQLite-based storage — all wrapped in a sleek Tkinter GUI.

🚀 Features

🔥 Real-time Face Recognition using OpenCV + face_recognition

📱 Add Cameras Dynamically — Supports both laptop and phone IP cameras

⚙️ Optimized for Low-Lag Performance on phone cameras

🧠 Local Database (SQLite) for face encodings and detections

👤 Face Registration with name + reg number + live capture

📜 Detection Logging with timestamp, confidence, and camera ID

💾 Auto Reloading Known Faces after registration

💻 Modern Tkinter GUI — dark themed with futuristic buttons and real-time logs

⚡ Multi-threaded Recognition across cameras for speed

🧩 HOG-based fast recognition (configurable)

🧠 Confidence-based matching and real-time label overlays

🧱 Tech Stack
Component	Technology
Language	Python 3.8+
Face Detection	face_recognition (dlib)
GUI	Tkinter
Database	SQLite3
Image Processing	OpenCV, Pillow
Networking	IP/Webcam streams
Threading	Python threading module
🏗️ Project Structure
gods_eye/
│
├── gods_eye.py                # Main application file
├── gods_eye_faces.db          # SQLite database (auto-created)
├── requirements.txt           # Dependencies
└── README.md                  # Documentation

⚙️ Installation
1️⃣ Clone the repo
git clone https://github.com/<your-username>/gods-eye.git
cd gods-eye

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Run the app
python gods_eye.py

🧩 requirements.txt
opencv-python
face-recognition
numpy
Pillow
requests

🧠 How It Works

Register Faces:

Add a person via GUI → enter name & registration number

Face captured from any connected camera

Encoded and stored in SQLite (faces table)

Add Cameras:

Add laptop camera (index 0 or others)

Add phone camera using IP (e.g., http://192.168.x.x:8080/video)

Start Recognition:

God’s Eye begins scanning all active feeds

Matches faces in real-time with stored encodings

Logs each detection (name, regno, camera, confidence, timestamp)

View Detections:

Live detection log appears at the bottom of GUI

Stored permanently in detections table

🧾 Database Schema
Table: faces
Column	Type	Description
id	INTEGER	Auto increment
name	TEXT	Person’s name
regno	TEXT	Unique registration ID
encoding	BLOB	Numpy-encoded face
registered_date	TEXT	Date & time registered
photo_path	TEXT	(optional) image path
Table: detections
Column	Type	Description
id	INTEGER	Auto increment
name	TEXT	Detected person’s name
regno	TEXT	Registration ID
camera_id	TEXT	Camera source
timestamp	TEXT	Detection time
confidence	REAL	Match confidence %
⚡ Performance Tips

Use 640x480 resolution or lower for smoother phone streams

Set FPS = 10 in IP Webcam settings

Use H.264 encoder for better compression

Keep phone close to router

Close other background apps on phone

🛠️ Future Plans

🔗 Blockchain logging for tamper-proof detections

🌐 Remote access via web dashboard

🧠 Face recognition with deep CNNs for better accuracy

🪪 Integration with KYC & security systems
