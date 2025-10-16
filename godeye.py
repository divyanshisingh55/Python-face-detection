import cv2
import face_recognition
import sqlite3
import numpy as np
import threading
import time
import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import requests
import socket
from urllib.parse import urlparse

class GodsEyeRecognition:
    def __init__(self):
        self.conn = sqlite3.connect("gods_eye_faces.db", check_same_thread=False)
        self.c = self.conn.cursor()
        self.setup_database()
        
        self.cameras = {}
        self.active_cameras = []
        self.recognition_active = False

        self.known_names = []
        self.known_regnos = []
        self.known_encodings = []
        self.load_known_faces()
        
        self.detections = {}
        self.detection_history = []
        
        self.setup_gui()
        
    def setup_database(self):
        """Initialize database tables"""
        self.c.execute("""CREATE TABLE IF NOT EXISTS faces(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            regno TEXT NOT NULL UNIQUE,
                            encoding BLOB NOT NULL,
                            registered_date TEXT,
                            photo_path TEXT
                        )""")
        
        self.c.execute("""CREATE TABLE IF NOT EXISTS detections(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT,
                            regno TEXT,
                            camera_id TEXT,
                            timestamp TEXT,
                            confidence REAL
                        )""")
        self.conn.commit()
    
    def setup_gui(self):
        """Create futuristic GUI interface"""
        self.root = tk.Tk()
        self.root.title(" GOD'S EYE - Face Recognition System")
        self.root.configure(bg='#0a0a0a')
        self.root.geometry("1400x900")
        
        # Styling
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Futuristic.TButton', 
                       background='#00ffff', 
                       foreground='black',
                       font=('Arial', 10, 'bold'))
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#0a0a0a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, 
                              text="GOD'S EYE SURVEILLANCE SYSTEM", 
                              bg='#0a0a0a', 
                              fg='#00ffff', 
                              font=('Arial', 20, 'bold'))
        title_label.pack(pady=10)
        
        # Control Panel
        control_frame = tk.Frame(main_frame, bg='#1a1a1a', relief='raised', bd=2)
        control_frame.pack(fill=tk.X, pady=10)
        
        # Buttons
        btn_frame = tk.Frame(control_frame, bg='#1a1a1a')
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Add Phone Camera", 
                  command=self.add_phone_camera, 
                  style='Futuristic.TButton').grid(row=0, column=0, padx=5)
        
        ttk.Button(btn_frame, text="Add Laptop Camera", 
                  command=self.add_laptop_camera, 
                  style='Futuristic.TButton').grid(row=0, column=1, padx=5)
        
        ttk.Button(btn_frame, text="Register Person", 
                  command=self.register_person_gui, 
                  style='Futuristic.TButton').grid(row=0, column=2, padx=5)
        
        ttk.Button(btn_frame, text="Start Recognition", 
                  command=self.start_recognition, 
                  style='Futuristic.TButton').grid(row=0, column=3, padx=5)
        
        ttk.Button(btn_frame, text="Stop Recognition", 
                  command=self.stop_recognition, 
                  style='Futuristic.TButton').grid(row=0, column=4, padx=5)
        
        self.feeds_frame = tk.Frame(main_frame, bg='#0a0a0a')
        self.feeds_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        info_frame = tk.Frame(main_frame, bg='#1a1a1a', relief='raised', bd=2)
        info_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(info_frame, text="ACTIVE DETECTIONS", 
                bg='#1a1a1a', fg='#00ffff', 
                font=('Arial', 14, 'bold')).pack(pady=5)
        
        self.detection_text = tk.Text(info_frame, height=8, bg='black', 
                                     fg='#00ff00', font=('Courier', 10))
        self.detection_text.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_var = tk.StringVar()
        self.status_var.set("System Ready - Add cameras to begin")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, 
                             bg='#333333', fg='white', 
                             font=('Arial', 10), relief='sunken', bd=1)
        status_bar.pack(fill=tk.X, pady=5)
    
    def add_phone_camera(self):
        """Add phone camera via IP with optimization"""
        dialog = PhoneCameraDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            camera_url = dialog.result
            try:
                cap = cv2.VideoCapture(camera_url)
                
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimum buffer
                    cap.set(cv2.CAP_PROP_FPS, 10)  # Lower FPS
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # Lower resolution
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    
                    ret, test_frame = cap.read()
                    if ret:
                        camera_id = f"phone_{len(self.cameras)}"
                        self.cameras[camera_id] = {
                            'cap': cap,
                            'url': camera_url,
                            'type': 'phone',
                            'active': True
                        }
                        self.status_var.set(f"Phone camera optimized and added: {camera_id}")
                        messagebox.showinfo("Success", 
                                          f"Phone camera connected with optimizations: {camera_id}\n\n" + 
                                          "Optimizations applied:\n" +
                                          "• Reduced buffer size\n" +
                                          "• Frame skipping enabled\n" +
                                          "• Fast HOG detection model\n" +
                                          "• Lower resolution processing")
                    else:
                        cap.release()
                        messagebox.showerror("Error", "Could not read frames from phone camera")
                else:
                    messagebox.showerror("Error", "Could not connect to phone camera")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add phone camera: {str(e)}")
    
    def add_laptop_camera(self):
        """Add laptop/webcam camera"""
        camera_index = simpledialog.askinteger("Camera Index", 
                                               "Enter camera index (usually 0):", 
                                               initialvalue=0)
        if camera_index is not None:
            try:
                cap = cv2.VideoCapture(camera_index)
                if cap.isOpened():
                    camera_id = f"laptop_{camera_index}"
                    self.cameras[camera_id] = {
                        'cap': cap,
                        'index': camera_index,
                        'type': 'laptop',
                        'active': True
                    }
                    self.status_var.set(f"Laptop camera added: {camera_id}")
                    messagebox.showinfo("Success", f"Laptop camera connected: {camera_id}")
                else:
                    messagebox.showerror("Error", f"Could not access camera {camera_index}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add laptop camera: {str(e)}")
    
    def register_person_gui(self):
        """Register a new person with GUI"""
        dialog = RegistrationDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            name, regno = dialog.result
            self.register_person(name, regno)
    
    def register_person(self, name, regno):
        """Register person from camera feed"""
        if not self.cameras:
            messagebox.showerror("Error", "No cameras available! Add a camera first.")
            return
        
        camera_id = list(self.cameras.keys())[0]
        cap = self.cameras[camera_id]['cap']
        
        self.status_var.set(f"📷 Registration mode - Show face to camera...")
        
        registered = False
        start_time = time.time()
        
        while not registered and time.time() - start_time < 30:  # 30 second timeout
            ret, frame = cap.read()
            if not ret:
                continue
                
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if face_locations:
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                if face_encodings:
                    encoding = face_encodings[0]
                    
                    self.save_face_to_db(name, regno, encoding)
                    self.load_known_faces()  # Reload known faces
                    
                    for (top, right, bottom, left) in face_locations:
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 3)
                        cv2.putText(frame, f"REGISTERED: {name}", 
                                  (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 
                                  0.8, (0, 255, 0), 2)
                    
                    registered = True
                    self.status_var.set(f"Successfully registered: {name} ({regno})")
                    messagebox.showinfo("Success", f"Successfully registered {name}!")
            
            cv2.imshow(f"Registration - {camera_id}", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cv2.destroyAllWindows()
        
        if not registered:
            self.status_var.set("Registration timeout - Please try again")
            messagebox.showwarning("Timeout", "Registration failed - no face detected in time")
    
    def save_face_to_db(self, name, regno, encoding):
        """Save face encoding to database"""
        try:
            self.c.execute("""INSERT INTO faces 
                            (name, regno, encoding, registered_date) 
                            VALUES (?, ?, ?, ?)""", 
                          (name, regno, encoding.tobytes(), 
                           datetime.now().isoformat()))
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"Registration number {regno} already exists!")
    
    def load_known_faces(self):
        """Load all known faces from database"""
        self.c.execute("SELECT name, regno, encoding FROM faces")
        data = self.c.fetchall()
        
        self.known_names = []
        self.known_regnos = []
        self.known_encodings = []
        
        for name, regno, encoding_blob in data:
            self.known_names.append(name)
            self.known_regnos.append(regno)
            encoding = np.frombuffer(encoding_blob, dtype=np.float64)
            self.known_encodings.append(encoding)
    
    def start_recognition(self):
        """Start face recognition on all cameras"""
        if not self.cameras:
            messagebox.showerror("Error", "No cameras available! Add cameras first.")
            return
        
        if not self.known_encodings:
            messagebox.showerror("Error", "No registered faces! Register people first.")
            return
        
        self.recognition_active = True
        self.status_var.set("GOD'S EYE ACTIVE - Scanning all feeds...")
        
        for camera_id in self.cameras.keys():
            thread = threading.Thread(target=self.recognition_loop, 
                                     args=(camera_id,), daemon=True)
            thread.start()
    
    def stop_recognition(self):
        """Stop face recognition"""
        self.recognition_active = False
        self.status_var.set("Recognition stopped")
        cv2.destroyAllWindows()
    
    def recognition_loop(self, camera_id):
        """Optimized recognition loop for a camera with lag reduction"""
        cap = self.cameras[camera_id]['cap']
        camera_type = self.cameras[camera_id]['type']
        
        if camera_type == 'phone':
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimum
            cap.set(cv2.CAP_PROP_FPS, 15)  # Lower FPS for stability
            process_every_n_frames = 3  # Process every 3rd frame only
            resize_factor = 0.3  # Smaller resize for faster processing
        else:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
            process_every_n_frames = 2
            resize_factor = 0.4
        
        frame_count = 0
        last_detections = []  # Cache last detections for skipped frames
        
        while self.recognition_active and camera_id in self.cameras:
            ret, frame = cap.read()
            if not ret:
                if camera_type == 'phone':
                    for _ in range(5):  # Clear up to 5 buffered frames
                        cap.read()
                time.sleep(0.01)  # Reduced sleep time
                continue
            
            frame_count += 1
            
            if frame_count % process_every_n_frames != 0:
                # Use cached detections for skipped frames
                for detection in last_detections:
                    self.draw_futuristic_box(frame, detection['bbox'], 
                                           detection['name'], detection['regno'], 
                                           detection['confidence'], detection['color'])
                
                cv2.imshow(f"GOD'S EYE - {camera_id.upper()}", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue
            
            if camera_type == 'phone' and frame_count % 10 == 0:
                for _ in range(3):
                    cap.grab()  # Skip buffered frames
            
            small_frame = cv2.resize(frame, (0, 0), fx=resize_factor, fy=resize_factor)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_small_frame, 
                                                           number_of_times_to_upsample=0,
                                                           model="hog")  # Faster HOG model
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            scale_factor = 1 / resize_factor
            face_locations = [(int(top*scale_factor), int(right*scale_factor), 
                             int(bottom*scale_factor), int(left*scale_factor)) 
                            for (top, right, bottom, left) in face_locations]
            
            last_detections = []
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(self.known_encodings, face_encoding, tolerance=0.6)
                face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                
                name = "UNKNOWN PERSON"
                regno = "UNREGISTERED"
                confidence = 0
                color = (0, 0, 255)  # Red for unknown
                
                if True in matches:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.known_names[best_match_index]
                        regno = self.known_regnos[best_match_index]
                        confidence = (1 - face_distances[best_match_index]) * 100
                        color = (0, 255, 0)  # Green for known
                        
                        # Log detection (less frequently for performance)
                        if frame_count % 30 == 0:  # Log every 30 processed frames
                            self.log_detection(name, regno, camera_id, confidence)
                
                # Cache detection for skipped frames
                last_detections.append({
                    'bbox': (left, top, right, bottom),
                    'name': name,
                    'regno': regno,
                    'confidence': confidence,
                    'color': color
                })
                
                # Draw futuristic detection box
                self.draw_futuristic_box(frame, (left, top, right, bottom), 
                                       name, regno, confidence, color)
            
            # Show frame with detections
            cv2.imshow(f"GOD'S EYE - {camera_id.upper()}", frame)
            
            # Reduced waitKey time for better responsiveness
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Cleanup
        if camera_id in self.cameras:
            self.cameras[camera_id]['cap'].release()
    
    def draw_futuristic_box(self, frame, bbox, name, regno, confidence, color):
        """Draw futuristic-style detection box"""
        left, top, right, bottom = bbox
        
        # Main rectangle
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        
        # Corner brackets (futuristic style)
        corner_length = 20
        corner_thickness = 3
        
        # Top-left corner
        cv2.line(frame, (left, top), (left + corner_length, top), color, corner_thickness)
        cv2.line(frame, (left, top), (left, top + corner_length), color, corner_thickness)
        
        # Top-right corner
        cv2.line(frame, (right, top), (right - corner_length, top), color, corner_thickness)
        cv2.line(frame, (right, top), (right, top + corner_length), color, corner_thickness)
        
        # Bottom-left corner
        cv2.line(frame, (left, bottom), (left + corner_length, bottom), color, corner_thickness)
        cv2.line(frame, (left, bottom), (left, bottom - corner_length), color, corner_thickness)
        
        # Bottom-right corner
        cv2.line(frame, (right, bottom), (right - corner_length, bottom), color, corner_thickness)
        cv2.line(frame, (right, bottom), (right, bottom - corner_length), color, corner_thickness)
        
        # Text background
        label = f"{name} ({regno})"
        if confidence > 0:
            label += f" - {confidence:.1f}%"
        
        (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (left, top - text_height - 10), 
                     (left + text_width, top), color, -1)
        cv2.putText(frame, label, (left, top - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Add scanning line effect (optional)
        cv2.line(frame, (left, top + (bottom - top) // 2), 
                (right, top + (bottom - top) // 2), (0, 255, 255), 1)
    
    def log_detection(self, name, regno, camera_id, confidence):
        """Log detection to database and update display"""
        timestamp = datetime.now().isoformat()
        
        # Save to database
        self.c.execute("""INSERT INTO detections 
                        (name, regno, camera_id, timestamp, confidence) 
                        VALUES (?, ?, ?, ?, ?)""",
                      (name, regno, camera_id, timestamp, confidence))
        self.conn.commit()
        
        # Update detection display
        detection_info = f"[{datetime.now().strftime('%H:%M:%S')}] {name} ({regno}) detected on {camera_id} - {confidence:.1f}%\n"
        
        self.detection_text.insert(tk.END, detection_info)
        self.detection_text.see(tk.END)
        
        # Keep only last 50 entries
        lines = self.detection_text.get(1.0, tk.END).split('\n')
        if len(lines) > 50:
            self.detection_text.delete(1.0, f"{len(lines)-50}.0")
    
    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.recognition_active = False
        for camera_data in self.cameras.values():
            camera_data['cap'].release()
        cv2.destroyAllWindows()
        self.conn.close()

class PhoneCameraDialog:
    def __init__(self, parent):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Phone Camera")
        self.dialog.geometry("550x400")
        self.dialog.configure(bg='#1a1a1a')
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx()+50, parent.winfo_rooty()+50))
        
        # Instructions
        instructions = """
📱 CONNECT PHONE CAMERA (OPTIMIZED FOR LOW LAG):

FOR BEST PERFORMANCE:
1. Install "IP Webcam" app on your phone
2. In app settings, set:
   • Video Resolution: 640x480 (Lower = Faster)
   • Quality: 50% (Lower = Less lag)
   • FPS limit: 10 (Lower = Smoother)
   • Video encoder: H.264
3. Start server and note IP address

ALTERNATIVE APPS (Try if IP Webcam is laggy):
• DroidCam (often faster)
• EpocCam
• iVCam

CONNECTION TIPS:
• Use the same WiFi network
• Keep phone close to router
• Close other apps on phone
• Use /video endpoint for mjpeg (fastest)
        """
        
        tk.Label(self.dialog, text=instructions, bg='#1a1a1a', fg='white', 
                font=('Arial', 9), justify=tk.LEFT).pack(pady=10, padx=10)
        
        # URL entry with presets
        tk.Label(self.dialog, text="Phone Camera URL:", bg='#1a1a1a', fg='#00ffff',
                font=('Arial', 12, 'bold')).pack()
        
        # Preset buttons frame
        preset_frame = tk.Frame(self.dialog, bg='#1a1a1a')
        preset_frame.pack(pady=5)
        
        # Quick preset buttons
        tk.Button(preset_frame, text="IP Webcam", 
                 command=lambda: self.url_var.set("http://192.168.1.100:8080/video"),
                 bg='#444444', fg='white', font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(preset_frame, text="DroidCam", 
                 command=lambda: self.url_var.set("http://192.168.1.100:4747/mjpegfeed?640x480"),
                 bg='#444444', fg='white', font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(preset_frame, text="Low Quality", 
                 command=lambda: self.url_var.set("http://192.168.1.100:8080/video?320x240"),
                 bg='#444444', fg='white', font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
        
        self.url_var = tk.StringVar(value="http://192.168.1.100:8080/video")
        url_entry = tk.Entry(self.dialog, textvariable=self.url_var, width=60,
                           font=('Arial', 10))
        url_entry.pack(pady=10)
        url_entry.focus()
        
        # Performance note
        perf_note = tk.Label(self.dialog, 
                           text="⚡ System will automatically optimize phone camera for best performance",
                           bg='#1a1a1a', fg='#ffff00', font=('Arial', 9))
        perf_note.pack(pady=5)
        
        # Buttons
        btn_frame = tk.Frame(self.dialog, bg='#1a1a1a')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Connect & Optimize", command=self.ok_clicked,
                 bg='#00ffff', fg='black', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancel", command=self.cancel_clicked,
                 bg='#ff4444', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
    
    def ok_clicked(self):
        url = self.url_var.get().strip()
        if url:
            self.result = url
        self.dialog.destroy()
    
    def cancel_clicked(self):
        self.dialog.destroy()

class RegistrationDialog:
    def __init__(self, parent):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Register New Person")
        self.dialog.geometry("400x250")
        self.dialog.configure(bg='#1a1a1a')
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx()+100, parent.winfo_rooty()+100))
        
        # Title
        tk.Label(self.dialog, text="👤 REGISTER NEW PERSON", 
                bg='#1a1a1a', fg='#00ffff', font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Name entry
        tk.Label(self.dialog, text="Full Name:", bg='#1a1a1a', fg='white',
                font=('Arial', 10)).pack()
        self.name_var = tk.StringVar()
        name_entry = tk.Entry(self.dialog, textvariable=self.name_var, width=30,
                            font=('Arial', 10))
        name_entry.pack(pady=5)
        name_entry.focus()
        
        # Registration number entry
        tk.Label(self.dialog, text="Registration Number:", bg='#1a1a1a', fg='white',
                font=('Arial', 10)).pack(pady=(10, 0))
        self.regno_var = tk.StringVar()
        regno_entry = tk.Entry(self.dialog, textvariable=self.regno_var, width=30,
                             font=('Arial', 10))
        regno_entry.pack(pady=5)
        
        # Instructions
        tk.Label(self.dialog, text="After clicking Register, show your face to the camera",
                bg='#1a1a1a', fg='#ffff00', font=('Arial', 9)).pack(pady=10)
        
        # Buttons
        btn_frame = tk.Frame(self.dialog, bg='#1a1a1a')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Register", command=self.ok_clicked,
                 bg='#00ffff', fg='black', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancel", command=self.cancel_clicked,
                 bg='#ff4444', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
    
    def ok_clicked(self):
        name = self.name_var.get().strip()
        regno = self.regno_var.get().strip()
        if name and regno:
            self.result = (name, regno)
        self.dialog.destroy()
    
    def cancel_clicked(self):
        self.dialog.destroy()

# Main execution
if __name__ == "__main__":
    print("🎯 Starting God's Eye Recognition System...")
    print("=" * 50)
    
    try:
        app = GodsEyeRecognition()
        app.run()
    except KeyboardInterrupt:
        print("\n⏹️ System shutdown by user")
    except Exception as e:
        print(f"❌ System error: {e}")
    finally:
        print("🔚 God's Eye system terminated")