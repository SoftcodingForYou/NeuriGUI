# Neuri GUI

1. Setup

The GUI is distributed as a Python program. The GUI should work with **Python versions 3.10 or higher**.

You can set up the environment (Python **libraries**) by running:
`pip install - requirements.txt`

Please note that the GUI is also using the **tkinter** framework which is not installable via `pip`. You have to install this during installation of the Python language. On GNU/Linux-based systems, it can be installed via the package manager (apt for Ubuntu):
`apt-get install python3-tk`

2. Compilation

The compiled version the the Neuri GUI runs way faster and has more stable  execution speed of iteration loops inside the backend of the GUI. You can **compile the GUI with Nuitka**:
- Windows: `nuitka ./neuri_gui.py --onefile --enable-plugin=tk-inter --standalone --enable-plugin=pyqt5 --include-data-dir=./frontend/=data --windows-icon-from-ico=frontend/Isotipo-Helment-color.ico --windows-disable-console`
- GNU/Linux: `nuitka3 ./neuri_gui.py --onefile --enable-plugin=tk-inter --standalone --enable-plugin=pyqt5 --include-data-dir=./frontend/=data --windows-icon-from-ico=frontend/Isotipo-Helment-color.ico --windows-disable-console` (note the 3 in nuitka3 compared to Windows)
