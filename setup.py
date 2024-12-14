import sys
import os
from cx_Freeze import setup, Executable
import pygame

# Get pygame directory with DLLs
pygame_dir = os.path.dirname(pygame.__file__)

APP_NAME = "Battery Monitor"
VERSION = "1.0.1"
DESCRIPTION = "Battery Monitoring Application"

# Include pygame DLLs and dependencies
build_exe_options = {
    "packages": [
        "os", "sys", "json", "psutil", "pygame", "win10toast", 
        "threading", "PIL", "pystray"
    ],
    "includes": ["tkinter"],
    "include_files": [
        ("resources", "resources"),
        ("settings.json", "settings.json"),
        (pygame_dir, os.path.join("lib", "pygame")),  # Include pygame files
    ],
    "include_msvcr": True,
    "excludes": [],
    "zip_include_packages": "*",
    "zip_exclude_packages": "pygame"  # Exclude pygame from zip to avoid DLL issues
}

base = "Win32GUI" if sys.platform == "win32" else None

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