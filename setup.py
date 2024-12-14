import sys
import os
from cx_Freeze import setup, Executable

APP_NAME = "Battery Monitor"
VERSION = "1.0.0"
DESCRIPTION = "Battery Monitoring Application"

# Ensure resources exist
resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
audio_dir = os.path.join(resources_dir, 'audio')
os.makedirs(audio_dir, exist_ok=True)

build_exe_options = {
    "packages": ["os", "sys", "json", "psutil", "pygame", "win10toast", "threading"],
    "includes": ["tkinter"],
    "include_files": [
        ("resources", "resources"),
        ("settings.json", "settings.json")
    ],
    "include_msvcr": True,
    "excludes": []
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable(
        script="battery_monitoring.py",
        base=base,
        target_name="BatteryMonitor.exe",
        shortcut_name=APP_NAME,
        shortcut_dir="DesktopFolder",
        icon="resources/icon.ico" if os.path.exists("resources/icon.ico") else None
    )
]

setup(
    name=APP_NAME,
    version=VERSION,
    description=DESCRIPTION,
    options={
        "build_exe": build_exe_options,
        "bdist_msi": {
            "initial_target_dir": fr"[ProgramFilesFolder]\{APP_NAME}",
            "add_to_path": True
        }
    },
    executables=executables
)