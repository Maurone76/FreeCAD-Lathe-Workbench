# Lathe Workbench for FreeCAD <!-- Titolo principale del repository -->

![Status](https://img.shields.io/badge/status-in%20development-orange) <!-- Badge dello stato di sviluppo -->
![FreeCAD](https://img.shields.io/badge/FreeCAD-%3E%3D%200.21-blue) <!-- Badge della versione di FreeCAD -->
![License: LGPL v2.0](https://img.shields.io/badge/License-LGPL%20v2.0-blue.svg) <!-- Badge della licenza -->

## Screenshots & Simulation <!-- Sezione immagini e video -->
![Main Interface](docs/screenshot.png) <!-- Mostra lo screenshot della cartella docs -->
*Figure 1: Lathe Workbench main interface and toolpaths.* <!-- Didascalia screenshot -->

<video src="docs/Simulations_2_compressed.mp4" width="100%" controls></video> <!-- Mostra il video integrato. ATTENZIONE: verifica che il nome "Simulations_2_compressed.mp4" sia esattamente quello caricato su GitHub -->
*Figure 2: Real-time 3D simulation of turning operations.* <!-- Didascalia video -->

The **Lathe Workbench** is a specialized external CAM environment for [FreeCAD](https://www.freecad.org) built to handle complex CNC turning workflows. Unlike standard milling workbenches, this workbench is tailored specifically for lathe operations—including roughing, finishing, grooving, parting, drilling, threading, turret indexing, and custom G-code post-processing. <!-- Descrizione del progetto -->

---

## Features <!-- Sezione funzionalità -->

- **Turning Operations**: Dedicated tools for roughing, finishing, grooving, parting, drilling, and threading. <!-- Punto elenco -->
- **Tool & Turret Management**: Comprehensive interface to define cutting tools, inserts, holders, and turret stations. <!-- Punto elenco -->
- **Simulation & Verification**: Integrated simulation tools to preview toolpaths and check against stock geometry. <!-- Punto elenco -->
- **Stock & Setup Definition**: Fast definition of raw material stock and machine coordinate setups. <!-- Punto elenco -->
- **Custom Post-Processing**: Converts internal toolpaths into machine-ready G-code using customizable JSON post profiles. <!-- Punto elenco -->
- **Multi-language Support**: Built-in internationalization framework for localized UI and messages. <!-- Punto elenco -->

---

## Installation <!-- Sezione installazione -->

### Manual Installation <!-- Sotto-sezione installazione manuale -->
1. Locate your FreeCAD `Mod` directory: <!-- Istruzione 1 -->
   - **Linux**: `~/.local/share/FreeCAD/Mod/` <!-- Percorso Linux -->
   - **Windows**: `%APPDATA%\FreeCAD\Mod\` <!-- Percorso Windows -->
   - **macOS**: `~/Library/Preferences/FreeCAD/Mod/` <!-- Percorso macOS -->
2. Clone or extract this repository's folder (named `LatheCAM`) inside your `Mod` directory. <!-- Istruzione 2 -->
3. Restart FreeCAD. The **Lathe** workbench will appear in the workbench dropdown selector. <!-- Istruzione 3 -->

---

## Command Reference <!-- Sezione comandi -->

| Icon | Tool | Module | Description | <!-- Intestazione tabella -->
| :---: | :--- | :--- | :--- | <!-- Formattazione colonne tabella -->
| ![Setup](icons/lathe_setup.svg) | **Setup** | `LatheSetup.py` | Sets up job boundaries, safety clearances, and spindle speed limits. | <!-- Riga tabella -->
| ![Stock](icons/lathe_stock.svg) | **Stock** | `LatheStock.py` | Defines raw stock dimensions, allowances, and material properties. | <!-- Riga tabella -->
| ![Tool Manager](icons/Lathe_Tools.svg) | **Tool Manager** | `LatheToolManager.py` | Interface for creating and modifying cutting tools and inserts. | <!-- Riga tabella -->
| ![Turret](icons/lathe_turret.svg) | **Turret** | `LatheTurret.py` | Assigns tools to specific turret slots for multi-step operations. | <!-- Riga tabella -->
| ![Roughing](icons/lathe_roughing.svg) | **Roughing** | `LatheRoughing.py` | Executes rough turning cycles for rapid bulk material removal. | <!-- Riga tabella -->
| ![Finishing](icons/lathe_finishing.svg) | **Finishing** | `LatheFinishing.py` | Performs final profile passes for precise dimensional tolerances. | <!-- Riga tabella -->
| ![Grooving](icons/lathe_grooving.svg) | **Grooving** | `LatheGrooving.py` | Cuts internal, external, or face grooves. | <!-- Riga tabella -->
| ![Parting](icons/lathe_parting.svg) | **Parting** | `LatheParting.py` | Specialized cut-off toolpath with feed reduction near the center line. | <!-- Riga tabella -->
| ![Drilling](icons/lathe_drilling.svg) | **Drilling** | `LatheDrilling.py` | Manages axial drilling, pecking, and boring cycles. | <!-- Riga tabella -->
| ![Threading](icons/lathe_threading.svg) | **Threading** | `LatheThreading.py` | Generates metric, imperial, or custom thread profiles. | <!-- Riga tabella -->
| ![Simulation](icons/lathe_simulation.svg) | **Simulation** | `LatheSimulation.py` | Runs graphical simulation of toolpaths against stock geometry. | <!-- Riga tabella -->
| ![PostProcess](icons/Lathe_PostProcess.svg) | **Post-Process** | `LathePostProcessor.py` | Exports operations to machine-ready G-code. | <!-- Riga tabella -->

---

## Project Structure <!-- Sezione struttura cartelle -->

The workbench uses a clean, modular structure following FreeCAD Addon standards: <!-- Testo introduttivo struttura -->

```text
LatheCAM/
├── docs/                    # Documentation assets (screenshots and Simulations_2_compressed.mp4)
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
``` <!-- Fine blocco di testo -->

---

## Feedback and Contributions <!-- Sezione feedback -->

This is a brand new software project in active development. If you encounter bugs, have suggestions, or want to propose improvements, please do not hesitate to share them! <!-- Testo incoraggiamento -->

*Please note: I develop this project in my free time and I am not at the computer every day. My response times may vary from very quick to a few days. Thank you for your patience!* <!-- Avviso sui tempi di risposta personalizzato -->

To keep everything organized and avoid direct private messages, please use the following official channels: <!-- Regole di contatto -->
- Open an **[Issue](https://github.com/Maurone76/FreeCAD-Lathe-Workbench/issues)** on GitHub for bug reports or specific errors. <!-- Link alle Issues corretto col tuo utente -->
- Start or join a conversation in the **[GitHub Discussions](https://github.com/Maurone76/FreeCAD-Lathe-Workbench/discussions)** section for ideas and general feedback. <!-- Link alle Discussions corretto col tuo utente -->
- Join the community discussion on the official **[FreeCAD Forum](https://forum.freecad.org/)**. <!-- Link al forum -->

---

## License <!-- Sezione licenza -->

This project is open-source and released under the **GNU Lesser General Public License v2.0 or later (LGPL-2.0-or-later)**. See the `LICENSE` file for details. Textual documentation is provided under CC-BY-3.0. <!-- Testo della licenza -->
