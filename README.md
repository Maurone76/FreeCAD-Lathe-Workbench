# Lathe Workbench for FreeCAD

![Status](https://img.shields.io/badge/status-in%20development-orange)
![FreeCAD](https://img.shields.io/badge/FreeCAD-%3E%3D%200.21-blue)
![License: LGPL v2.0](https://img.shields.io/badge/License-LGPL%20v2.0-blue.svg)

## Screenshots & Simulation
![Main Interface](docs/screenshot.png)
*Figure 1: Lathe Workbench main interface and toolpaths.*

https://github.com/Maurone76/FreeCAD-Lathe-Workbench/blob/main/docs/simulation.mp4
*Figure 2: Real-time 3D simulation of turning operations.*

The **Lathe Workbench** is a specialized external CAM environment for [FreeCAD](https://www.freecad.org) built to handle complex CNC turning workflows. Unlike standard milling workbenches, this workbench is tailored specifically for lathe operations—including roughing, finishing, grooving, parting, drilling, threading, turret indexing, and custom G-code post-processing.

---

## Features

- **Turning Operations**: Dedicated tools for roughing, finishing, grooving, parting, drilling, and threading.
- **Tool & Turret Management**: Comprehensive interface to define cutting tools, inserts, holders, and turret stations.
- **Simulation & Verification**: Integrated simulation tools to preview toolpaths and check against stock geometry.
- **Stock & Setup Definition**: Fast definition of raw material stock and machine coordinate setups.
- **Custom Post-Processing**: Converts internal toolpaths into machine-ready G-code using customizable JSON post profiles.
- **Multi-language Support**: Built-in internationalization framework for localized UI and messages.

---

## Installation

### Manual Installation
1. Locate your FreeCAD `Mod` directory:
   - **Linux**: `~/.local/share/FreeCAD/Mod/`
   - **Windows**: `%APPDATA%\FreeCAD\Mod\`
   - **macOS**: `~/Library/Preferences/FreeCAD/Mod/`
2. Clone or extract this repository's folder (named `LatheCAM`) inside your `Mod` directory.
3. Restart FreeCAD. The **Lathe** workbench will appear in the workbench dropdown selector.

---

## Command Reference

| Icon | Tool | Module | Description |
| :---: | :--- | :--- | :--- |
| ![Setup](icons/lathe_setup.svg) | **Setup** | `LatheSetup.py` | Sets up job boundaries, safety clearances, and spindle speed limits. |
| ![Stock](icons/lathe_stock.svg) | **Stock** | `LatheStock.py` | Defines raw stock dimensions, allowances, and material properties. |
| ![Tool Manager](icons/Lathe_Tools.svg) | **Tool Manager** | `LatheToolManager.py` | Interface for creating and modifying cutting tools and inserts. |
| ![Turret](icons/lathe_turret.svg) | **Turret** | `LatheTurret.py` | Assigns tools to specific turret slots for multi-step operations. |
| ![Roughing](icons/lathe_roughing.svg) | **Roughing** | `LatheRoughing.py` | Executes rough turning cycles for rapid bulk material removal. |
| ![Finishing](icons/lathe_finishing.svg) | **Finishing** | `LatheFinishing.py` | Performs final profile passes for precise dimensional tolerances. |
| ![Grooving](icons/lathe_grooving.svg) | **Grooving** | `LatheGrooving.py` | Cuts internal, external, or face grooves. |
| ![Parting](icons/lathe_parting.svg) | **Parting** | `LatheParting.py` | Specialized cut-off toolpath with feed reduction near the center line. |
| ![Drilling](icons/lathe_drilling.svg) | **Drilling** | `LatheDrilling.py` | Manages axial drilling, pecking, and boring cycles. |
| ![Threading](icons/lathe_threading.svg) | **Threading** | `LatheThreading.py` | Generates metric, imperial, or custom thread profiles. |
| ![Simulation](icons/lathe_simulation.svg) | **Simulation** | `LatheSimulation.py` | Runs graphical simulation of toolpaths against stock geometry. |
| ![PostProcess](icons/Lathe_PostProcess.svg) | **Post-Process** | `LathePostProcessor.py` | Exports operations to machine-ready G-code. |

---

## Project Structure

The workbench uses a clean, modular structure following FreeCAD Addon standards:

```text
LatheCAM/
├── docs/                    # Documentation assets (screenshots and Simulation.mp4)
├── icons/                   # SVG toolbar icons
├── MachineLibrary/          # Machine definition profiles
├── StockLibrary/            # Stock material profiles
├── ToolLibrary/             # Tool and insert databases
├── TurretLibrary/           # Turret configuration files
├── translations/            # I18n localization files (EN, IT, ES, DE)
├── post_profiles_ecam.json  # G-code post-processor configurations
├── InitGui.py               # Workbench initialization for FreeCAD
├── Lathe*.py                # Main operation modules
├── README.md                # This documentation
└── LICENSE                  # LGPL License file
