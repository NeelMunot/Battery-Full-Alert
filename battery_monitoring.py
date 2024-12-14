import os
import sys
import json
import time
import psutil
import pygame
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from win10toast import ToastNotifier
import winsound
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import shutil
import uuid

class BatteryMonitor:
    def __init__(self):
        # Initialize pygame mixer first
        pygame.mixer.init()
        
        self.root = tk.Tk()
        self.root.title("Battery Monitor")
        self.root.geometry("400x300")
        
        # Set up directory paths
        if getattr(sys, 'frozen', False):
            self.app_dir = os.path.dirname(sys.executable)
        else:
            self.app_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.resources_dir = os.path.join(self.app_dir, 'resources')
        self.audio_dir = os.path.join(self.resources_dir, 'audio')
        
        # Create directories if not frozen
        if not getattr(sys, 'frozen', False):
            os.makedirs(self.audio_dir, exist_ok=True)
        
        # Initialize all instance variables first
        self.alert_percentage = tk.IntVar(value=90)
        self.sound_file = tk.StringVar(value="default")
        self.monitoring = False
        self.monitor_thread = None
        self.toaster = ToastNotifier()
        self.threshold_slider = None
        self.threshold_spinbox = None
        self.sound_label = None  # Initialize sound_label reference
        self.playing_audio = False  # Add after other initializations
        self.last_valid_sound = None  # Store last working custom sound
        self.icon = None  # Add after other initializations
        
        self.create_ui()  # Create UI first
        self.load_settings()  # Load settings after UI is created
        
        # Configure window close button
        self.root.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)

    def get_resource_path(self):
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable))
        return os.path.dirname(os.path.abspath(__file__))

    def create_ui(self):
        # Battery threshold setting
        ttk.Label(self.root, text="Alert when battery reaches:").pack(pady=10)
        threshold_frame = ttk.Frame(self.root)
        threshold_frame.pack()
        
        # Create slider first
        self.threshold_slider = ttk.Scale(
            threshold_frame,
            from_=10,
            to=100,
            orient='horizontal',
            length=200
        )
        self.threshold_slider.set(self.alert_percentage.get())
        self.threshold_slider.pack(side='left')
        
        # Create spinbox with modified configuration
        self.threshold_spinbox = ttk.Spinbox(
            threshold_frame,
            from_=10,
            to=100,
            width=5,
            validate='key',
            validatecommand=(self.root.register(self.validate_spinbox_input), '%P'),
            command=lambda: self.on_spinbox_change(None)  # For up/down buttons
        )
        self.threshold_spinbox.set(self.alert_percentage.get())
        self.threshold_spinbox.pack(side='left', padx=5)
        
        # Bind events for manual input
        self.threshold_spinbox.bind('<FocusOut>', self.on_spinbox_change)
        self.threshold_spinbox.bind('<Return>', self.on_spinbox_change)
        
        # Bind slider change
        self.threshold_slider.configure(command=self.on_slider_change)
        
        ttk.Label(threshold_frame, text="%").pack(side='left')
        
        # Sound selection
        ttk.Label(self.root, text="Alert Sound:").pack(pady=10)
        sound_frame = ttk.Frame(self.root)
        sound_frame.pack()
        
        # Add radio buttons with command to update label
        ttk.Radiobutton(
            sound_frame, 
            text="Default Beep", 
            variable=self.sound_file,
            value="default",
            command=self.update_sound_label
        ).pack(side='left', padx=5)
        
        ttk.Radiobutton(
            sound_frame, 
            text="Custom Sound", 
            variable=self.sound_file,
            value="custom",
            command=self.update_sound_label
        ).pack(side='left', padx=5)
        
        ttk.Button(sound_frame, text="Browse", command=self.browse_sound).pack(side='left', padx=5)
        
        # Add audio file info label
        self.sound_label = ttk.Label(self.root, text="Current Sound: Default Beep")
        self.sound_label.pack(pady=5)
        
        # Start/Stop button
        self.toggle_button = ttk.Button(self.root, text="Start Monitoring",
                                      command=self.toggle_monitoring)
        self.toggle_button.pack(pady=20)
        
        # Status label
        self.status_label = ttk.Label(self.root, text="Status: Not monitoring")
        self.status_label.pack(pady=10)
        
    def update_sound_label(self):
        if self.sound_file.get() == "default":
            self.sound_label.config(text="Current Sound: Default Beep")
        elif self.last_valid_sound and os.path.exists(self.last_valid_sound):
            filename = os.path.basename(self.last_valid_sound)
            self.sound_label.config(text=f"Current Sound: {filename}")
        else:
            self.sound_label.config(text="Current Sound: No file selected")
            self.sound_file.set("default")  # Fallback to default if file not found
        
    def on_slider_change(self, value):
        try:
            value = int(float(value))
            self.alert_percentage.set(value)
            self.threshold_spinbox.set(value)
        except ValueError:
            pass

    def on_spinbox_change(self, event):
        try:
            value = int(self.threshold_spinbox.get())
            value = max(10, min(100, value))  # Clamp between 10-100
            self.alert_percentage.set(value)
            self.threshold_slider.set(value)
            if event:  # Only reset spinbox on actual changes
                self.threshold_spinbox.set(value)
        except ValueError:
            self.threshold_spinbox.set(self.alert_percentage.get())

    def validate_spinbox_input(self, value):
        if value == "":
            return True
        try:
            val = int(value)
            return len(value) <= 3  # Allow typing up to 3 digits
        except ValueError:
            return False
        
    def validate_final_value(self):
        try:
            value = int(self.threshold_spinbox.get())
            if value < 10:
                self.alert_percentage.set(10)
            elif value > 100:
                self.alert_percentage.set(100)
        except ValueError:
            self.alert_percentage.set(90)
            return False
    
    def browse_sound(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Audio files", "*.mp3;*.wav;*.ogg"),
                ("MP3 files", "*.mp3"),
                ("WAV files", "*.wav"),
                ("OGG files", "*.ogg"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            # Generate unique filename
            ext = os.path.splitext(file_path)[1]
            new_filename = f"custom_sound_{uuid.uuid4()}{ext}"
            new_path = os.path.join(self.audio_dir, new_filename)
            
            # Remove old custom sound if exists
            if self.last_valid_sound and os.path.exists(self.last_valid_sound):
                try:
                    os.remove(self.last_valid_sound)
                except OSError:
                    pass
            
            # Copy new file
            shutil.copy2(file_path, new_path)
            self.last_valid_sound = new_path
            self.sound_file.set("custom")
            self.update_sound_label()
            self.save_settings()
            
    def play_alarm(self):
        try:
            self.playing_audio = True
            if self.sound_file.get() == "custom" and self.last_valid_sound and os.path.exists(self.last_valid_sound):
                pygame.mixer.music.load(self.last_valid_sound)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and self.playing_audio:
                    if not self.monitoring or not psutil.sensors_battery().power_plugged:
                        pygame.mixer.music.stop()
                        break
                    time.sleep(0.1)
            else:
                winsound.Beep(2500, 1000)
                
            if self.playing_audio:
                time.sleep(1)
        except Exception as e:
            print(f"Error playing sound: {e}")
            winsound.Beep(2500, 1000)

    def stop_alarm(self):
        self.playing_audio = False
        pygame.mixer.music.stop()

    def monitor_battery(self):
        while self.monitoring:
            battery = psutil.sensors_battery()
            if battery:
                current_percentage = battery.percent
                if battery.power_plugged and current_percentage >= self.alert_percentage.get():
                    self.toaster.show_toast(
                        "Battery Monitor",
                        f"Battery at {current_percentage}%! Please unplug.",
                        duration=5,
                        threaded=True
                    )
                    # Start alarm in separate thread to prevent UI blocking
                    if not hasattr(self, 'alarm_thread') or not self.alarm_thread.is_alive():
                        self.alarm_thread = threading.Thread(target=self.play_alarm)
                        self.alarm_thread.daemon = True
                        self.alarm_thread.start()
            time.sleep(5)
            
    def toggle_controls(self, state):
        """Enable or disable UI controls based on monitoring state"""
        self.threshold_slider.configure(state=state)
        self.threshold_spinbox.configure(state=state)

    def toggle_monitoring(self):
        if not self.monitoring:
            self.monitoring = True
            self.playing_audio = False
            self.toggle_button.config(text="Stop Monitoring")
            self.status_label.config(text="Status: Monitoring")
            self.toggle_controls('disabled')  # Disable controls when monitoring
            self.monitor_thread = threading.Thread(target=self.monitor_battery)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
        else:
            self.monitoring = False
            self.stop_alarm()
            self.toggle_button.config(text="Start Monitoring")
            self.status_label.config(text="Status: Not monitoring")
            self.toggle_controls('normal')
            
    def load_settings(self):
        settings_path = os.path.join(self.app_dir, 'settings.json')
        try:
            with open(settings_path, 'r') as f:
                settings = json.load(f)
                self.alert_percentage.set(settings.get('threshold', 90))
                self.sound_file.set(settings.get('sound_mode', 'default'))
                
                # Convert relative path to absolute
                relative_path = settings.get('custom_sound_path')
                if relative_path:
                    self.last_valid_sound = os.path.join(self.app_dir, relative_path)
                    if not os.path.exists(self.last_valid_sound):
                        self.last_valid_sound = None
                        self.sound_file.set('default')
                else:
                    self.last_valid_sound = None
                
                self.update_sound_label()
        except FileNotFoundError:
            self.alert_percentage.set(90)
            self.sound_file.set('default')
            self.last_valid_sound = None
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        # Convert absolute path to relative
        relative_path = None
        if self.last_valid_sound and os.path.exists(self.last_valid_sound):
            relative_path = os.path.relpath(self.last_valid_sound, self.app_dir)
        
        settings = {
            'threshold': self.alert_percentage.get(),
            'sound_mode': self.sound_file.get(),
            'custom_sound_path': relative_path
        }
        
        settings_path = os.path.join(self.app_dir, 'settings.json')
        try:
            with open(settings_path, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def run(self):
        self.root.mainloop()
        
    def minimize_to_tray(self):
        """Hide window instead of destroying"""
        self.root.withdraw()
        
    def show_window(self):
        """Restore window from tray"""
        self.root.deiconify()

    def quit_app(self):
        self.monitoring = False
        self.stop_alarm()
        self.icon.stop()
        self.root.destroy()

    def create_tray_icon(self):
        # Create tray icon image (16x16 black square with white B)
        image = Image.new('RGB', (16, 16), color='black')
        d = ImageDraw.Draw(image)
        d.text((4, 2), "B", fill='white')
        
        # Create menu
        menu = (
            item('Open', self.show_window),
            item('Quit', self.quit_app)
        )
        
        # Create tray icon
        self.icon = pystray.Icon(
            "battery_monitor",
            image,
            "Battery Monitor",
            menu
        )

def resource_path(relative_path):
    """Get absolute path to resource for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = BatteryMonitor()
    app.run()