# Lathe Workbench for FreeCAD

![Status](https://img.shields.io/badge/status-in%20development-orange)
![FreeCAD](https://img.shields.io/badge/FreeCAD-%3E%3D%200.21-blue)
![License: LGPL v2.0](https://img.shields.io/badge/License-LGPL%20v2.0-blue.svg)

<img width="2539" height="1253" alt="image" src="https://github.com/user-attachments/assets/b9e57f93-c0b9-4447-8464-adc9594d4cb3" />


The **Lathe Workbench** is a specialized external CAM environment for [FreeCAD](https://www.freecad.org) built to handle complex CNC turning workflows. Unlike standard milling workbenches, this workbench is tailored specifically for lathe operations—including roughing, finishing, grooving, parting, drilling, threading, turret indexing, and custom G-code post-processing.

---

## Features

- **Turning Operations**: Dedicated tools for roughing, finishing, grooving, parting, and threading.
- **Tool & Turret Management**: Comprehensive interface (`LatheToolManager`, `LatheTurret`) to define cutting tools, inserts, holders, and turret stations.
- **Simulation & Verification**: Integrated simulation tools (`LatheSimulation`) to preview toolpaths and check against stock geometry.
- **Stock & Setup Definition**: Fast definition of raw material stock (`LatheStock`) and machine coordinate setups (`LatheSetup`).
- **Custom Post-Processing**: Converts internal toolpaths into machine-ready G-code using customizable JSON post profiles (`post_profiles_ecam.json`).
- **Multi-language Support**: Built-in internationalization framework (`LatheI18n`) for localized UI and messages.

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

| Icon / Tool | Module File | Description |
| :--- | :--- | :--- |
| **Setup** | `LatheSetup.py` | Sets up job boundaries, safety clearances, and spindle speed limits. |
| **Stock** | `LatheStock.py` | Defines raw stock dimensions, allowances, and material properties. |
| **Tool Manager** | `LatheToolManager.py` | Interface for creating and modifying cutting tools and inserts. |
| **Turret** | `LatheTurret.py` | Assigns tools to specific turret slots for multi-step operations. |
| **Roughing** | `LatheRoughing.py` | Executes rough turning cycles for rapid bulk material removal. |
| **Finishing** | `LatheFinishing.py` | Performs final profile passes for precise dimensional tolerances. |
| **Grooving** | `LatheGrooving.py` | Cuts internal, external, or face grooves. |
| **Parting** | `LatheParting.py` | Specialized cut-off toolpath with feed reduction near the center line. |
| **Drilling** | `LatheDrilling.py` | Manages axial drilling, pecking, and boring cycles. |
| **Threading** | `LatheThreading.py` | Generates metric, imperial, or custom thread profiles. |
| **Simulation** | `LatheSimulation.py` | Runs graphical simulation of toolpaths against stock geometry. |

---

## License

This project is licensed under the **GNU Lesser General Public License v2.0 or later (LGPL-2.0-or-later)**. See the `LICENSE` file for details.
