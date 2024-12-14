# Battery Monitor

A Windows application developed through AI pair programming with GitHub Copilot to prevent battery overcharging.

## Project Background

This project was born from a personal need to protect my laptop's battery life by preventing overcharging. The entire application was developed through conversational programming with GitHub Copilot, demonstrating the power of AI-assisted development.

### Development Journey
1. Initial concept discussion with Copilot
2. Step-by-step feature implementation through prompts
3. Iterative improvements and bug fixes
4. Final packaging into executable

## Features

- 🔋 Customizable battery threshold alerts (10-100%)
- 🔊 Custom sound alerts with file persistence
- 🔔 Windows system notifications
- 💻 System tray integration
- ⚙️ Persistent settings across sessions
- 🎯 User-friendly interface

## Requirements

- Windows 10/11
- Python 3.x
- Required packages (automatically installed through requirements.txt):
  - psutil
  - win10toast
  - pygame
  - pystray
  - Pillow
  - pyinstaller (for creating executable)

## Installation

### Method 1: Windows Installer
1. Download the latest `.msi` installer from the releases page
2. Run the installer and follow the setup wizard
3. The application will be installed in Program Files
4. A desktop shortcut will be created automatically

### Method 2: Manual Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run `python battery_monitoring.py`

### From Source
1. Clone the repository:
```bash
git clone https://github.com/yourusername/battery-monitor.git
cd battery-monitor
```

2. Create virtual environment (recommended):
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install requirements:
```bash
pip install -r requirements.txt
```

### Creating Executable
1. Install PyInstaller if not already installed:
```bash
pip install pyinstaller
```

2. Create executable:
```bash
pyinstaller --onefile --noconsole --icon=icon.ico battery_monitoring.py
```

3. Find the executable in the dist folder

## Usage

### Running from Source
```bash
python battery_monitoring.py
```

### Running Executable
1. Navigate to dist folder
2. Run `battery_monitoring.exe`

### Features Usage
1. Set desired battery threshold using slider or input box
2. Choose between default or custom alert sound
3. Click "Start Monitoring"
4. Application minimizes to system tray
5. Receive alerts when battery reaches threshold

## Development with GitHub Copilot

This project showcases how modern development can be accelerated using AI pair programming. Every feature was implemented through natural language prompts to GitHub Copilot:

1. Basic UI implementation
2. Battery monitoring logic
3. Sound alert system
4. System tray integration
5. Settings persistence
6. Executable creation

## Project Structure

```
battery-monitor/
│
├── battery_monitoring.py    # Main application file
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
└── .gitignore            # Git ignore rules
```

## Contributing

This project was developed as a personal tool, but contributions are welcome! Feel free to:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - Feel free to use and modify for your needs.

## Acknowledgments

- GitHub Copilot for pair programming assistance
- Python community for excellent libraries
- Open source contributors

