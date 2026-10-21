LatheCAM Workbench for FreeCAD


(Placeholder: Insert a nice, wide screenshot of FreeCAD with the LatheCAM workbench open, showing a complex turned part and the toolpaths.)

LatheCAM is a powerful and dedicated FreeCAD workbench designed to streamline CNC lathe operations. It provides a comprehensive suite of tools for turning, facing, drilling, grooving, and threading, complete with tool management, stock definition, and post-processing capabilities.

📸 Screenshots & Workflow

(Placeholder: Add 2-3 screenshots here showing the Tool Manager, the Setup Dialog, and the 3D Simulation in action.)

Tool Manager Interface:


Toolpath Simulation:


Generated G-Code:


🛠️ Features & Tool Reference

LatheCAM organizes the turning workflow logically, from machine setup to G-code generation. Below are the main tools available in the toolbar:

Setup & Configuration

 Lathe Setup: Define your machine parameters, coordinate systems, and safety clearances (LatheSetup.py).

 Lathe Stock: Define the raw material dimensions (cylinder, tube, etc.) for accurate simulation and machining (LatheStock.py).

 Lathe Part: Select the final target shape/body to be machined.

Tool Management

 Tool Library: Open the Tool Manager GUI to create, edit, and manage turning inserts, holders, and drills (LatheToolManager.py).

 Turret Setup: Configure your Automatic Tool Changer (ATC) or turret stations (LatheTurret.py).

Machining Operations

 Roughing: Generate roughing toolpaths for external and internal turning profiles (LatheRoughing.py).

 Finishing: Generate fine finishing passes to achieve the final part dimensions (LatheFinishing.py).

 Grooving: Create plunging toolpaths for external or internal grooves (LatheGrooving.py).

 Parting: Generate the cut-off operation to separate the finished part from the raw stock (LatheParting.py).

 Threading: Create constant or variable pitch threads (LatheThreading.py).

 Drilling: Generate axial drilling, pecking, and tapping cycles (LatheDrilling.py).

Output & Verification

 Simulation: Run a visual check of the programmed toolpaths directly within the FreeCAD 3D view (LatheSimulation.py).

 Post-Process: Output the final NC/G-code file tailored for your specific CNC controller (LathePostProcessor.py).

🌍 Multi-Language Support

LatheCAM is designed to be accessible globally. It currently supports:

🇬🇧 English

🇮🇹 Italian

🇪🇸 Spanish

🇩🇪 German

📥 Installation

Manual Installation

Download the repository as a ZIP file or clone it using Git:

git clone https://github.com/yourusername/LatheCAM.git


Place the LatheCAM folder into your FreeCAD Mod directory:

Windows: %APPDATA%\FreeCAD\Mod\

Linux: ~/.local/share/FreeCAD/Mod/ or ~/.FreeCAD/Mod/

macOS: ~/Library/Application Support/FreeCAD/Mod/

Restart FreeCAD. You should now see "LatheCAM" in the Workbench dropdown menu.

📁 Directory Structure

The workbench strictly follows FreeCAD's external workbench guidelines:

LatheCAM/
├── InitGui.py                  # FreeCAD Workbench initialization
├── LatheATC.py                 # Automatic Tool Changer logic
├── LatheCommands.py            # Core workbench commands registration
├── LatheDrilling.py            # Drilling operation
├── LatheFinishing.py           # Finishing operation
├── LatheGrooving.py            # Grooving operation
├── LatheI18n.py                # Internationalization handling
├── LatheParting.py             # Parting operation
├── LathePostProcessor.py       # G-Code generation logic
├── LatheRoughing.py            # Roughing operation
├── LatheSetup.py               # Job/Machine setup logic
├── LatheSimulation.py          # Toolpath simulation
├── LatheStock.py               # Stock definition
├── LatheThreading.py           # Threading operation
├── LatheToolManager.py         # Tool library management GUI
├── LatheTurret.py              # Turret setup logic
├── MachineLibrary/             # DB: machine configurations
├── StockLibrary/               # DB: standard stock sizes
├── ToolLibrary/                # DB: cutting tools
├── TurretLibrary/              # DB: turret configurations
├── icons/                      # SVG icons for the toolbar
└── translations/               # Language dictionaries (.py files)


📜 License

This project is licensed under the terms of the GNU LGPL v2.1 (or compatible) license, matching FreeCAD's licensing model. See the LICENSE file for more details.
