import tkinter as tk
from tkinter import ttk, filedialog
import psutil
import winsound
import threading
import json
import time
from win10toast import ToastNotifier
import os
import pygame
from pygame import mixer
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

class BatteryMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Battery Monitor")
        self.root.geometry("400x300")
        
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
        pygame.mixer.init()
        
        # Configure window close button
        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)

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
            self.sound_label.config(text="Current Sound: Default")
        elif self.last_valid_sound:
            filename = os.path.basename(self.last_valid_sound)
            self.sound_label.config(text=f"Current Sound: {filename}")
        else:
            self.sound_label.config(text="Current Sound: No file selected")
        
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
            self.sound_file.set("custom")  # Switch to custom mode
            self.last_valid_sound = file_path
            filename = os.path.basename(file_path)
            self.sound_label.config(text=f"Current Sound: {filename}")
            self.save_settings()
            
    def play_alarm(self):
        self.playing_audio = True
        while self.monitoring and psutil.sensors_battery().power_plugged and self.playing_audio:
            try:
                if self.sound_file.get() == "default":
                    winsound.Beep(2500, 1000)
                else:
                    # Try to use stored custom sound
                    sound_to_play = self.last_valid_sound if self.last_valid_sound else self.sound_file.get()
                    
                    # Check if file exists and is accessible
                    if sound_to_play and os.path.exists(sound_to_play):
                        pygame.mixer.music.load(sound_to_play)
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy() and self.playing_audio:
                            if not self.monitoring or not psutil.sensors_battery().power_plugged:
                                pygame.mixer.music.stop()
                                break
                            time.sleep(0.1)
                    else:
                        # Fallback to default beep
                        print("Custom sound file not found, using default beep")
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
                if current_percentage >= self.alert_percentage.get() and battery.power_plugged:
                    self.toaster.show_toast("Battery Alert",
                                          f"Battery at {current_percentage}%! Please unplug.",
                                          duration=5,
                                          threaded=True)
                    threading.Thread(target=self.play_alarm).start()
                elif not battery.power_plugged:
                    self.stop_alarm()
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
        settings_path = resource_path('battery_monitor_settings.json')
        try:
            with open(settings_path, 'r') as f:
                settings = json.load(f)
                # Load threshold
                self.alert_percentage.set(settings.get('threshold', 90))
                
                # Load sound settings
                self.last_valid_sound = settings.get('last_valid_sound')
                sound_file = settings.get('sound_file', 'default')
                self.sound_file.set(sound_file)
                
                # Update sound label
                if hasattr(self, 'sound_label'):
                    if sound_file == 'default':
                        self.sound_label.config(text="Current Sound: Default Beep")
                    elif self.last_valid_sound:
                        filename = os.path.basename(self.last_valid_sound)
                        self.sound_label.config(text=f"Current Sound: {filename}")
        except FileNotFoundError:
            # Set defaults if no settings file
            self.alert_percentage.set(90)
            self.sound_file.set('default')
            self.last_valid_sound = None
            
    def save_settings(self):
        settings = {
            'threshold': self.alert_percentage.get(),
            'sound_file': self.sound_file.get(),
            'last_valid_sound': self.last_valid_sound  # Save last valid sound path
        }
        settings_path = resource_path('battery_monitor_settings.json')
        try:
            with open(settings_path, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def run(self):
        self.root.mainloop()
        
    def hide_window(self):
        self.root.withdraw()
        self.create_tray_icon()
        self.icon.run()

    def show_window(self):
        self.icon.stop()
        self.root.after(0, self.root.deiconify)
        
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