# -*- coding: utf-8 -*-                                                                         # Imposta la codifica UTF-8
import re                                                                                       # Importa modulo espressioni regolari per sostituzione sicura di parole intere

LINGUA_CODICE = "en"                                                                            # Identificativo codice lingua Inglese
LINGUA_NOME = "English"                                                                         # Nome esteso della lingua

TRADUZIONI = {                                                                                  # Dizionario completo delle frasi esatte Italiano -> Inglese per tutti i 13 moduli
    # ==========================================================================
    # BARRE DEGLI STRUMENTI E TOOLTIP (13 COMANDI)
    # ==========================================================================
    "1. Setup Macchina (WCS)": "1. Machine Setup (WCS)",                                        # Comando 1 MenuText
    "Configura il sistema di coordinate macchina (WCS), l'origine Z0 e il punto di cambio utensile.": "Configure machine coordinate system (WCS), Z0 origin and tool change point.",
    "2. Grezzo & Autocentrante": "2. Stock & Chuck",                                            # Comando 2 MenuText
    "Definisce le dimensioni del cilindro/tubo grezzo e le griffe del mandrino autocentrante.": "Define stock cylinder/tube dimensions and 3-jaw chuck.",
    "3. Pezzo Finito (Target 3D)": "3. Target Part (3D Model)",                                 # Comando 3 MenuText
    "Seleziona e posiziona il solido 3D del pezzo finito dentro il grezzo.": "Select and align the 3D target part inside the stock.",
    "4. Magazzino Utensili": "4. Tool Library",                                                 # Comando 4 MenuText
    "Gestisce il magazzino utensili di tornitura, gole, filettatura e foratura.": "Manage turning, grooving, threading and drilling tool library.",
    "5. Torretta Portautensili 3D": "5. 3D Tool Turret",                                        # Comando 5 MenuText
    "Configura il disco torretta 3D e monta gli utensili nelle stazioni.": "Configure 3D turret disk and mount tools on stations.",
    "1. Sgrossatura": "1. Roughing",                                                            # Comando 6 MenuText
    "Ciclo di sgrossatura longitudinale o frontale con riconoscimento automatico del profilo 3D.": "Longitudinal or facing roughing cycle with 3D profile recognition.",
    "2. Finitura": "2. Finishing",                                                              # Comando 7 MenuText
    "Passata continua di finitura sul profilo reale del pezzo finito con compensazione raggio.": "Continuous finishing pass on target profile with nose radius compensation.",
    "3. Gola": "3. Grooving",                                                                   # Comando 8 MenuText
    "Scavo di gole radiali esterne, interne o frontali con ciclo a tuffi multipli e pulizia fondo.": "External, internal or face grooving cycle with pecking and floor finishing.",
    "4. Filettatura": "4. Threading",                                                           # Comando 9 MenuText
    "Filettatura cilindrica o conica (Metrica ISO, Gas BSP, NPT, Trapezoidale) a sezione costante.": "Cylindrical or tapered threading (ISO Metric, BSP, NPT, Acme) with constant area degression.",
    "5. Foratura Asse": "5. Center Drilling",                                                   # Comando 10 MenuText
    "Centrinatura, foratura profonda a scarico truciolo (G83/G73) e maschiatura sull'asse Z.": "Spot drilling, peck drilling (G83/G73) and tapping on spindle Z axis.",
    "6. Troncatura": "6. Parting Off",                                                          # Comando 11 MenuText
    "Taglio finale del pezzo finito dalla barra con smusso/raccordo automatico sullo spigolo.": "Parting off cycle with automatic back-edge chamfer or corner radius.",
    "1. Simulazione 3D": "1. 3D Simulation",                                                    # Comando 12 MenuText
    "Simula in 3D il movimento della torretta, l'asportazione sul grezzo e verifica le collisioni.": "Simulate 3D turret motion, dynamic stock removal and collision checking.",
    "2. Genera G-Code": "2. Post-Process G-Code",                                               # Comando 13 MenuText
    "Genera, visualizza ed esporta il programma G-Code per Fanuc/Haas, Siemens, Mach3 e LinuxCNC.": "Generate, preview and export G-Code for Fanuc/Haas, Siemens, Mach3 and LinuxCNC.",

    # ==========================================================================
    # PANNELLO 1: SETUP MACCHINA (WCS)
    # ==========================================================================
    "Configurazione Setup Macchina (WCS)": "Machine Setup Configuration (WCS)",                 # Titolo Setup WCS
    "Sistema di Coordinate Pezzo (WCS)": "Work Coordinate System (WCS)",                        # Gruppo WCS
    "Origine WCS (Z0 Pezzo)": "WCS Origin (Part Z0)",                                           # Gruppo Origine Z0
    "Origine X:": "Origin X:",                                                                  # Origine X
    "Origine Y:": "Origin Y:",                                                                  # Origine Y
    "Origine Z:": "Origin Z:",                                                                  # Origine Z
    "Origine Z (Z0):": "Z Origin (Z0):",                                                        # Origine Z0
    "Origine Z0 (mm):": "Z0 Origin (mm):",                                                      # Origine Z0 in mm
    "Quota Z0 Pezzo:": "Part Z0 Coordinate:",                                                   # Quota Z0
    "Acquisisci Z0 da Faccia/Vertice 3D": "Pick Z0 from 3D Face/Vertex",                        # Bottone acquisisci Z0
    "Acquisisci Z0 da Faccia 3D": "Pick Z0 from 3D Face",                                       # Variante bottone Z0
    "Allinea Z0 a Faccia Selezionata": "Align Z0 to Selected Face",                             # Variante allinea Z0
    "Posizione Cambio Utensile": "Tool Change Position",                                        # Gruppo cambio utensile
    "Punto Cambio Utensile (Home)": "Tool Change Point (Home)",                                 # Variante cambio utensile
    "Cambio Utensile X:": "Tool Change X:",                                                     # Quota X cambio
    "Cambio Utensile Z:": "Tool Change Z:",                                                     # Quota Z cambio
    "Cambio Utensile X (Raggio):": "Tool Change X (Radius):",                                   # Quota X raggio
    "Quota X Cambio (Raggio):": "Tool Change X (Radius):",                                      # Quota X raggio
    "Quota Z Cambio:": "Tool Change Z:",                                                        # Quota Z
    "Configurazione Torretta": "Turret Configuration",                                          # Gruppo torretta nel setup
    "Posizione Torretta:": "Turret Position:",                                                  # Posizione torretta
    "Posteriore (X+ Standard CNC)": "Rear Toolpost (X+ CNC Standard)",                          # Opzione torretta posteriore
    "Anteriore (X- Tornio Parallelo)": "Front Toolpost (X- Manual Lathe)",                      # Opzione torretta anteriore
    "Giri Max Mandrino:": "Max Spindle RPM:",                                                   # Limite giri
    "Giri Max (G50):": "Max RPM (G50):",                                                        # Limite giri G50
    "Dimensione Icona WCS:": "WCS Triad Size:",                                                 # Dimensione frecce WCS
    "Dimensione Assi WCS:": "WCS Axes Size:",                                                   # Variante dimensione assi
    "Mostra Assi WCS 3D": "Show 3D WCS Axes",                                                   # Checkbox mostra WCS

    # ==========================================================================
    # PANNELLO 2: GREZZO & AUTOCENTRANTE (TUTTE LE VOCI DELLO SCREENSHOT!)
    # ==========================================================================
    "Archivio Grezzi / Mandrini": "Stock / Chuck Presets",                                      # Gruppo archivio grezzi
    "Carica Grezzo": "Load Stock",                                                              # Bottone carica grezzo
    "Carica Stock": "Load Stock",                                                               # Correzione stringa parziale
    "Elimina": "Delete",                                                                        # Bottone elimina
    "Delete": "Delete",                                                                         # Mantiene Delete
    "Salva in Archivio Permanente all'OK": "Save to Permanent Presets on OK",                   # Checkbox salva in archivio
    "Save in Archivio Permanente all'OK": "Save to Permanent Presets on OK",                    # Correzione stringa parziale
    "1. Grezzo": "1. Stock",                                                                    # Scheda 1 grezzo
    "1. Stock": "1. Stock",                                                                     # Mantiene 1. Stock
    "2. Presa & Limiti": "2. Chuck Grip & Limits",                                              # Scheda 2 presa e limiti
    "2. Presa _Limiti": "2. Chuck Grip & Limits",                                               # Variante con underscore
    "2. Grip _Limits": "2. Chuck Grip & Limits",                                                # Correzione stringa parziale
    "Dimensioni Barra & Sovrametalli": "Bar Dimensions & Stock Allowances",                     # Gruppo dimensioni barra
    "Dimensioni Barra _Sovrametalli": "Bar Dimensions & Stock Allowances",                      # Variante con underscore
    "Dimensions Bar _Sovrametalli": "Bar Dimensions & Stock Allowances",                        # Correzione stringa parziale
    "Rileva Misure dal Pezzo 3D Selezionato": "Measure from Selected 3D Part",                  # Bottone rileva misure 3D
    "Rileva Misure dal Part 3D Selected": "Measure from Selected 3D Part",                      # Correzione stringa parziale
    "Tipo Barra:": "Stock Type:",                                                               # Etichetta tipo barra
    "Type Bar:": "Stock Type:",                                                                 # Correzione stringa parziale
    "Cilindro Pieno": "Solid Cylinder",                                                         # Voce tendina cilindro pieno
    "Tubo Forato": "Hollow Tube",                                                               # Voce tendina tubo forato
    "Diametro Base (mm):": "Base Diameter (mm):",                                               # Diametro base
    "Diameter Base (mm):": "Base Diameter (mm):",                                               # Correzione stringa parziale
    "Diametro Foro Int. (mm):": "Inner Bore Diameter (mm):",                                    # Diametro foro interno
    "Diameter Bore Int. (mm):": "Inner Bore Diameter (mm):",                                    # Correzione stringa parziale
    "Lunghezza Totale (mm):": "Total Length (mm):",                                             # Lunghezza totale
    "Total Length (mm):": "Total Length (mm):",                                                 # Mantiene Total Length
    "Sovrametallo Fronte Z+ (mm):": "Front Z+ Allowance (mm):",                                 # Sovrametallo frontale Z+
    "Allowance Fronte Z+ (mm):": "Front Z+ Allowance (mm):",                                    # Correzione stringa parziale
    "Sovrametallo Raggio X+ (mm):": "Radial X+ Allowance (mm):",                                # Sovrametallo radiale X+
    "Allowance Radius X+ (mm):": "Radial X+ Allowance (mm):",                                   # Correzione stringa parziale
    "Trasparenza Visiva (%):": "Visual Transparency (%):",                                      # Trasparenza visiva %
    "Transparency Visiva (%):": "Visual Transparency (%):",                                     # Correzione stringa parziale
    "Configurazione Grezzo e Mandrino": "Stock & Chuck Configuration",                          # Titolo Grezzo
    "Dimensioni Grezzo": "Stock Dimensions",                                                    # Gruppo dimensioni grezzo
    "Geometria Cilindro / Tubo Grezzo": "Stock Cylinder / Tube Geometry",                       # Variante gruppo grezzo
    "Adatta automaticamente al Pezzo 3D": "Auto-Fit to 3D Target Part",                         # Bottone adatta a pezzo
    "Adatta a Pezzo Finito": "Fit to Target Part",                                              # Variante bottone adatta
    "Autocentrante 3 Griffe": "3-Jaw Chuck",                                                    # Gruppo autocentrante
    "Mandrino Autocentrante a 3 Griffe": "3-Jaw Self-Centering Chuck",                          # Variante gruppo autocentrante
    "Mostra Autocentrante 3D": "Show 3D Chuck",                                                 # Checkbox mostra autocentrante
    "Visualizza Mandrino 3D": "Show 3D Chuck",                                                  # Variante mostra mandrino
    "Diametro Autocentrante:": "Chuck Diameter:",                                               # Diametro mandrino
    "Diametro Autocentrante (mm):": "Chuck Diameter (mm):",                                     # Diametro mandrino mm
    "Diametro Mandrino (mm):": "Chuck Diameter (mm):",                                          # Diametro mandrino mm
    "Presa Griffe su Grezzo:": "Jaw Grip Length:",                                              # Presa griffe
    "Presa Griffe (mm):": "Jaw Grip Length (mm):",                                              # Presa griffe mm
    "Lunghezza Presa Griffe:": "Jaw Grip Length:",                                              # Variante presa griffe
    "Sporgenza Fuori Mandrino:": "Stickout from Chuck:",                                        # Sporgenza pezzo
    "Limite Sicurezza Z Griffe (mm):": "Jaw Z Safety Limit (mm):",                              # Limite Z griffe
    "Trasparenza Grezzo:": "Stock Transparency:",                                               # Trasparenza grezzo
    "Diametro Esterno:": "Outer Diameter:",                                                     # Diametro esterno
    "Diametro Esterno (mm):": "Outer Diameter (mm):",                                           # Diametro esterno mm
    "Diametro Interno:": "Inner Diameter:",                                                     # Diametro interno
    "Diametro Interno (mm):": "Inner Diameter (mm):",                                           # Diametro interno mm
    "Diametro Foro Interno:": "Inner Bore Diameter:",                                           # Foro interno
    "Lunghezza Totale:": "Total Length:",                                                       # Lunghezza totale
    "Lunghezza Grezzo:": "Stock Length:",                                                       # Lunghezza grezzo
    "Lunghezza Grezzo (mm):": "Stock Length (mm):",                                             # Lunghezza grezzo mm
    "Sovrametallo Frontale:": "Front Stock Allowance:",                                         # Sovrametallo frontale
    "Sovrametallo Frontale (Z+):": "Front Stock Allowance (Z+):",                               # Sovrametallo Z+
    "Sovrametallo Radiale:": "Radial Stock Allowance:",                                         # Sovrametallo radiale

    # ==========================================================================
    # PANNELLO 3: PEZZO FINITO (TARGET PART 3D)
    # ==========================================================================
    "Selezione e Allineamento Pezzo Finito": "Target Part Selection & Alignment",               # Titolo Pezzo Finito
    "Modello 3D Pezzo Finito": "3D Target Part Model",                                          # Gruppo modello 3D
    "Oggetto 3D Selezionato:": "Selected 3D Object:",                                           # Oggetto 3D
    "Solido Target:": "Target Solid:",                                                          # Variante solido target
    "Usa Oggetto Selezionato nella Vista 3D": "Use Selected Object in 3D View",                 # Bottone usa selezione
    "Acquisisci Solido Selezionato": "Pick Selected Solid",                                     # Variante bottone acquisisci
    "Allinea al Centro e Fronte Grezzo": "Align to Stock Center & Front",                       # Bottone allinea
    "Centra sull'Asse Z del Tornio": "Center on Lathe Z-Axis",                                  # Variante centra
    "Inverti Orientamento Z (Ruota 180°)": "Flip Z Orientation (Rotate 180°)",                  # Bottone ruota 180
    "Ruota Pezzo 180°": "Rotate Part 180°",                                                     # Variante ruota
    "Offset Assiale Z:": "Axial Z Offset:",                                                     # Offset Z
    "Spostamento Z (mm):": "Z Shift (mm):",                                                     # Spostamento Z

    # ==========================================================================
    # PANNELLO 4 & 5: MAGAZZINO UTENSILI E TORRETTA 3D (TUTTE LE SCHEDE)
    # ==========================================================================
    "Dati Generali & Stazione Torretta": "General Data & Turret Station",                       # Gruppo dati generali utensile con &
    "Dati Generali e Stazione Torretta": "General Data & Turret Station",                       # Gruppo dati generali utensile
    "Dati Generali _Stazione Torretta": "General Data & Turret Station",                        # Con underscore
    "Dati Generali _Station Turret": "General Data & Turret Station",                           # Correzione stringa parziale
    "Dati Generali Utensile": "General Tool Data",                                              # Variante dati generali
    "Nome:": "Name:",                                                                           # Nome
    "Name:": "Name:",                                                                           # Name
    "Nome Utensile:": "Tool Name:",                                                             # Nome utensile
    "N° Posizioni Torretta:": "Turret Stations Count:",                                         # Numero posizioni torretta
    "N° Posizioni Turret:": "Turret Stations Count:",                                           # Variante numero posizioni
    "Stazione Assegnata:": "Assigned Station:",                                                 # Stazione assegnata
    "Station Axisgnata:": "Assigned Station:",                                                  # Correzione stringa precedente
    "Stazione Torretta:": "Turret Station:",                                                    # Stazione torretta
    "Numero Stazione:": "Station Number:",                                                      # Numero stazione
    "1. Geometria": "1. Geometry",                                                              # Tab 1 Utensili
    "1. Geometry": "1. Geometry",                                                               # Tab 1 Utensili
    "2. Custom 3D": "2. Custom 3D",                                                             # Tab 2 Utensili
    "2. Modello 3D Custom": "2. Custom 3D Model",                                               # Variante Tab 2
    "3. Tecnologia": "3. Technology",                                                           # Tab 3 Utensili
    "3. Technology": "3. Technology",                                                           # Tab 3 Utensili
    "Categoria Lavorazione": "Machining Category",                                              # Gruppo categoria
    "Categoria Lavorazione:": "Machining Category:",                                            # Etichetta categoria
    "Geometria Inserto / Tagliente": "Insert / Cutting Edge Geometry",                          # Gruppo geometria inserto
    "Geometry Insert / Edge": "Insert / Cutting Edge Geometry",                                 # Variante gruppo geometria inserto
    "Forma Inserto:": "Insert Shape:",                                                          # Forma inserto
    "Forma Insert:": "Insert Shape:",                                                           # Variante forma inserto
    "Raggio Punta (mm):": "Nose Radius (mm):",                                                  # Raggio punta mm
    "Radius Tip/Drill (mm):": "Nose / Drill Radius (mm):",                                      # Variante raggio punta
    "Raggio Punta (Nose R):": "Nose Radius (R):",                                               # Raggio punta
    "Raggio Inserto:": "Insert Radius:",                                                        # Raggio inserto
    "Angolo Inserto:": "Insert Angle:",                                                         # Angolo inserto
    "Verso Taglio:": "Cutting Hand:",                                                           # Verso di taglio
    "Verso Cutting:": "Cutting Hand:",                                                          # Variante verso di taglio
    "Angolo Reg. Kapr (°):": "Approach Angle Kapr (°):",                                        # Angolo registrazione Kapr
    "Angle Reg. Kapr (°):": "Approach Angle Kapr (°):",                                         # Variante angolo Kapr
    "Angolo Approccio (Kr):": "Lead Angle (Kr):",                                               # Angolo approccio Kr
    "Dimensioni Corpo / Stelo": "Shank / Body Dimensions",                                      # Gruppo dimensioni stelo
    "Dimensioni Corpo / Shank": "Shank / Body Dimensions",                                      # Variante dimensioni stelo
    "Larghezza Stelo (mm):": "Shank Width (mm):",                                               # Larghezza stelo
    "Width Shank (mm):": "Shank Width (mm):",                                                   # Variante larghezza stelo
    "Altezza Stelo (mm):": "Shank Height (mm):",                                                # Altezza stelo
    "Height Shank (mm):": "Shank Height (mm):",                                                 # Variante altezza stelo
    "Larghezza Tagliente:": "Cutting Width:",                                                   # Larghezza tagliente
    "Larghezza Lama (mm):": "Blade Width (mm):",                                                # Larghezza lama troncatura/gola
    "Diametro Utensile (mm):": "Tool Diameter (mm):",                                           # Diametro utensile
    "Sezione Stelo:": "Shank Size:",                                                            # Sezione stelo
    "Lunghezza Stelo:": "Shank Length:",                                                        # Lunghezza stelo
    "Sporgenza Utensile:": "Tool Overhang:",                                                    # Sporgenza utensile
    "Orientamento Spaziale 3D (Live)": "3D Spatial Orientation (Live)",                         # Gruppo orientamento 3D
    "Specchia X": "Mirror X",                                                                   # Checkbox Specchia X
    "Specchia Y": "Mirror Y",                                                                   # Checkbox Specchia Y
    "Specchia Z": "Mirror Z",                                                                   # Checkbox Specchia Z
    "Rotazione X (°):": "Rotation X (°):",                                                      # Rotazione X
    "Rotazione Y (°):": "Rotation Y (°):",                                                      # Rotazione Y
    "Rotazione Z (°):": "Rotation Z (°):",                                                      # Rotazione Z
    "Offset X (mm):": "Offset X (mm):",                                                         # Offset X
    "Offset Y (mm):": "Offset Y (mm):",                                                         # Offset Y
    "Offset Z (mm):": "Offset Z (mm):",                                                         # Offset Z
    "Modello 3D Personalizzato (STEP / Oggetto FreeCAD)": "Custom 3D Model (STEP / FreeCAD Object)",
    "Usa Modello 3D Personalizzato": "Use Custom 3D Model",                                     # Checkbox modello custom
    "Importa File STEP...": "Import STEP File...",                                              # Bottone importa STEP
    "Acquisisci Oggetto 3D Selezionato": "Pick Selected 3D Object",                             # Bottone acquisisci 3D
    "Posizione Punta Tagliente (TCP)": "Cutting Tip Position (TCP)",                            # Gruppo TCP
    "Acquisisci TCP da Vertice 3D": "Pick TCP from 3D Vertex",                                  # Bottone TCP
    "Parametri Tecnologici Default": "Default Cutting Parameters",                              # Gruppo tecnologia utensile
    "Velocità Taglio Default (Vc):": "Default Cutting Speed (Vc):",                             # Vc default
    "Avanzamento Default (F):": "Default Feed Rate (F):",                                       # F default
    "Profondità Max (Ap):": "Max Depth of Cut (Ap):",                                           # Ap max
    "Verso Rotazione:": "Spindle Direction:",                                                   # Verso rotazione mandrino
    "Verso Rotazione Mandrino:": "Spindle Rotation Direction:",                                 # Variante verso rotazione
    "Antiorario (M03)": "CCW / Forward (M03)",                                                  # M03
    "Orario (M04)": "CW / Reverse (M04)",                                                       # M04
    "Magazzino Utensili Tornio": "Lathe Tool Library",                                          # Titolo magazzino
    "Elenco Utensili nel Magazzino": "Tools in Library",                                        # Gruppo elenco utensili
    "➕ Nuovo Utensile": "➕ New Tool",                                                         # Bottone nuovo
    "🗑 Elimina Utensile": "🗑 Delete Tool",                                                    # Bottone elimina
    "↺ Ripristina Default": "↺ Reset Default",                                                  # Bottone ripristina
    "Proprietà Utensile Selezionato": "Selected Tool Properties",                               # Gruppo proprietà
    "Configurazione Torretta Portautensili 3D": "3D Tool Turret Configuration",                 # Titolo torretta 3D
    "Geometria Disco Torretta": "Turret Disk Geometry",                                         # Gruppo disco torretta
    "Numero Stazioni:": "Number of Stations:",                                                  # Numero stazioni
    "Stazione Attiva:": "Active Station:",                                                      # Stazione attiva
    "Ruota Torretta su Stazione:": "Index Turret to Station:",                                  # Ruota torretta
    "Diametro Disco:": "Disk Diameter:",                                                        # Diametro disco
    "Diametro Disco (mm):": "Disk Diameter (mm):",                                              # Diametro disco mm
    "Spessore Disco:": "Disk Thickness:",                                                       # Spessore disco
    "Spessore Disco (mm):": "Disk Thickness (mm):",                                             # Spessore disco mm
    "Raggio Montaggio Utensili:": "Tool Mounting Radius:",                                      # Raggio montaggio
    "Offset Centro X:": "Center X Offset:",                                                     # Offset X torretta
    "Offset Centro Z:": "Center Z Offset:",                                                     # Offset Z torretta
    "Utensili Montati sulle Stazioni": "Tools Mounted on Stations",                             # Gruppo stazioni
    "Mostra Disco Torretta 3D": "Show 3D Turret Disk",                                          # Checkbox mostra torretta

    # ==========================================================================
    # PANNELLI 6..11: LAVORAZIONI CAM (SGROSSATURA, FINITURA, GOLA, FILETTO, FORO, TRONCATURA)
    # ==========================================================================
    "1. Utensile e Modalità": "1. Tool & Cycle Mode",                                           # Gruppo 1 operazioni
    "1. Utensile & Modalità": "1. Tool & Cycle Mode",                                           # Con &
    "1. Utensile e Ciclo": "1. Tool & Cycle",                                                   # Variante Gruppo 1
    "Utensile:": "Tool:",                                                                       # Utensile
    "Utensile Assegnato:": "Assigned Tool:",                                                    # Utensile assegnato
    "Ciclo:": "Cycle:",                                                                         # Ciclo
    "Tipo Ciclo:": "Cycle Type:",                                                               # Tipo ciclo
    "Direzione:": "Direction:",                                                                 # Direzione
    "Modalità:": "Mode:",                                                                       # Modalità
    "Acquisisci da 3D (Faccia/Bordo)": "Pick from 3D (Face/Edge)",                              # Bottone acquisisci 3D
    "Acquisisci Quote da Selezione 3D": "Pick Dimensions from 3D Selection",                    # Variante bottone 3D
    "Seleziona da Modello 3D": "Select from 3D Model",                                          # Variante bottone 3D
    "2. Limiti Geometrici": "2. Geometry Limits",                                               # Gruppo 2 operazioni
    "2. Geometria e Quote": "2. Geometry & Dimensions",                                         # Variante Gruppo 2
    "Geometria e Quote": "Geometry & Dimensions",                                               # Variante Gruppo 2
    "Limiti Geometrici": "Geometry Limits",                                                     # Variante Gruppo 2
    "3. Parametri di Taglio": "3. Cutting Parameters",                                          # Gruppo 3 operazioni
    "4. Parametri di Taglio": "4. Cutting Parameters",                                          # Gruppo 4 operazioni
    "Parametri Tecnologici": "Cutting Parameters",                                              # Variante parametri
    "Parametri di Taglio": "Cutting Parameters",                                                # Variante parametri
    "Profondità Passata:": "Depth of Cut:",                                                     # Profondità passata
    "Profondità per Passata:": "Depth per Pass:",                                               # Profondità per passata
    "Profondità Passata (mm):": "Depth of Cut (mm):",                                           # Ap mm
    "Profondità Passata (Ap):": "Depth of Cut (Ap):",                                           # Ap
    "Incremento Radiale (Ap):": "Radial Stepdown (Ap):",                                        # Ap radiale
    "Sovrametallo X:": "X Stock Allowance:",                                                    # Sovrametallo X
    "Sovrametallo Z:": "Z Stock Allowance:",                                                    # Sovrametallo Z
    "Sovrametallo X (mm):": "X Stock Allowance (mm):",                                          # Sovrametallo X mm
    "Sovrametallo Z (mm):": "Z Stock Allowance (mm):",                                          # Sovrametallo Z mm
    "Sovrametallo Radiale X:": "Radial X Allowance:",                                           # Sovrametallo radiale X
    "Sovrametallo Assiale Z:": "Axial Z Allowance:",                                            # Sovrametallo assiale Z
    "Sovrametallo Diametro:": "Diameter Allowance:",                                            # Sovrametallo diametro
    "Avanzamento:": "Feed Rate:",                                                               # Avanzamento
    "Avanzamento (F):": "Feed Rate (F):",                                                       # Avanzamento F
    "Avanzamento (mm/giro):": "Feed Rate (mm/rev):",                                            # Avanzamento mm/giro
    "Avanzamento Lavoro (F):": "Cutting Feed Rate (F):",                                        # Avanzamento lavoro
    "Velocità Taglio:": "Cutting Speed:",                                                       # Velocità taglio
    "Velocità Taglio (Vc):": "Cutting Speed (Vc):",                                             # Velocità taglio Vc
    "Velocità Taglio (m/min):": "Cutting Speed (m/min):",                                       # Velocità taglio m/min
    "Giri Mandrino:": "Spindle RPM:",                                                           # Giri mandrino
    "Giri Mandrino (RPM):": "Spindle Speed (RPM):",                                             # Giri mandrino RPM
    "Raggio Sicurezza:": "Safety Radius:",                                                      # Raggio sicurezza
    "Raggio Sicurezza (mm):": "Safety Radius (mm):",                                            # Raggio sicurezza mm
    "Distacco Sicurezza:": "Safety Clearance:",                                                 # Distacco sicurezza
    "Distacco Sicurezza (mm):": "Safety Clearance (mm):",                                       # Distacco sicurezza mm
    "Rientro (Retract):": "Retract Clearance:",                                                 # Rientro
    "Quota Z Inizio:": "Start Z:",                                                              # Quota Z inizio
    "Quota Z Fine:": "End Z:",                                                                  # Quota Z fine
    "Quota Z Inizio (mm):": "Start Z (mm):",                                                    # Quota Z inizio mm
    "Quota Z Fine (mm):": "End Z (mm):",                                                        # Quota Z fine mm
    "Z Iniziale:": "Start Z:",                                                                  # Z iniziale
    "Z Finale:": "End Z:",                                                                      # Z finale
    "Z Inizio:": "Start Z:",                                                                    # Z inizio
    "Z Fine:": "End Z:",                                                                        # Z fine
    "Z Taglio:": "Parting Z:",                                                                  # Z taglio troncatura
    "Quota Z Troncatura:": "Parting Z Coordinate:",                                             # Quota Z troncatura
    "Diametro Iniziale:": "Start Diameter:",                                                    # Diametro iniziale
    "Diametro Finale:": "End Diameter:",                                                        # Diametro finale
    "Diametro Massimo:": "Max Diameter:",                                                       # Diametro massimo
    "Diametro Minimo:": "Min Diameter:",                                                        # Diametro minimo
    "Diametro Fondo:": "Root/Floor Diameter:",                                                  # Diametro fondo gola/filetto
    "Diametro Nominale:": "Nominal Diameter:",                                                  # Diametro nominale filetto
    "Larghezza Gola:": "Groove Width:",                                                         # Larghezza gola
    "Larghezza Gola (mm):": "Groove Width (mm):",                                               # Larghezza gola mm
    "Profondità Gola:": "Groove Depth:",                                                        # Profondità gola
    "Passo Filetto:": "Thread Pitch:",                                                          # Passo filetto
    "Passo Filetto (mm):": "Thread Pitch (mm):",                                                # Passo filetto mm
    "Passo (P):": "Pitch (P):",                                                                 # Passo P
    "Altezza Filetto:": "Thread Depth:",                                                        # Altezza filetto
    "Profondità Filetto:": "Thread Depth:",                                                     # Profondità filetto
    "Angolo Profilo:": "Profile Angle:",                                                        # Angolo profilo
    "Angolo Filetto (°):": "Thread Angle (°):",                                                 # Angolo filetto
    "Passate a Vuoto:": "Spring Passes:",                                                       # Passate a vuoto
    "Numero Passate:": "Number of Passes:",                                                     # Numero passate
    "Passate di Taglio:": "Cutting Passes:",                                                    # Passate di taglio
    "Standard Filettatura:": "Thread Standard:",                                                # Standard filettatura
    "Profondità Foro:": "Hole Depth:",                                                          # Profondità foro
    "Profondità Foro (mm):": "Hole Depth (mm):",                                                # Profondità foro mm
    "Profondità Totale:": "Total Depth:",                                                       # Profondità totale
    "Diametro Punta:": "Drill Diameter:",                                                       # Diametro punta
    "Diametro Punta (mm):": "Drill Diameter (mm):",                                             # Diametro punta mm
    "Incremento Scarico (Q):": "Peck Depth (Q):",                                               # Incremento Q
    "Profondità Tuffo (Q):": "Peck Depth (Q):",                                                 # Profondità tuffo Q
    "Smusso Spigolo:": "Edge Chamfer:",                                                         # Smusso spigolo
    "Raccordo / Smusso:": "Corner Radius / Chamfer:",                                           # Raccordo / Smusso
    "Compensazione Raggio Punta:": "Nose Radius Compensation:",                                 # Compensazione raggio
    "Usa Profilo 3D Pezzo Finito": "Follow 3D Target Part Profile",                             # Checkbox profilo 3D
    "Riconoscimento Automatico Profilo 3D": "Automatic 3D Profile Recognition",                 # Checkbox riconoscimento 3D
    "Ricalcola / Anteprima": "Recompute / Preview",                                             # Bottone ricalcola
    "Aggiorna Anteprima 3D": "Update 3D Preview",                                               # Bottone aggiorna

    # ==========================================================================
    # PANNELLO 12 & 13: SIMULAZIONE 3D E POST-PROCESSOR E-CAM
    # ==========================================================================
    "Selezione Operazioni e Modalità": "Operation Selection & Mode",                            # Simulazione gruppo 1
    "Simula:": "Simulate:",                                                                     # Tendina simula
    "★ Tutte le Operazioni in Sequenza": "★ All Operations in Sequence",                        # Tutte le operazioni
    "Simula asportazione materiale sul Grezzo": "Simulate 3D Stock Material Removal",           # Checkbox asportazione 3D
    "Verifica Collisioni 3D in tempo reale": "Real-time 3D Collision Check",                    # Checkbox collisioni
    "Metti in Pausa se rileva collisione": "Auto-Pause on Collision",                           # Checkbox pausa collisione
    "Controlli Riproduzione e Velocità": "Playback & Speed Controls",                           # Gruppo controlli player
    "▶ Play": "▶ Play",                                                                         # Bottone Play
    "⏸ Pausa": "⏸ Pause",                                                                       # Bottone Pausa
    "⏹ Reset": "⏹ Reset",                                                                       # Bottone Reset
    "Controllo Numerico (DRO Tempo Reale)": "Digital Readout (Real-time DRO)",                  # Gruppo DRO
    "Controllo Collisioni: Nessuna interferenza.": "Collision Check: No interference.",         # Stato collisioni OK
    "Simulazione Completata! (Premi Reset o Play per rivedere)": "Simulation Complete! (Press Reset or Play to replay)",
    "Nessuna operazione CAM trovata nel progetto!": "No CAM operations found in project!",
    "1. Controllo & Programma": "1. Controller & Program",                                      # Tab 1 Post-Processor
    "2. Configuratore e-CAM (Template & Codici)": "2. e-CAM Configurator (Templates & Codes)",  # Tab 2 Post-Processor
    "Configurazione Controllo CNC e Operazioni": "CNC Controller & Operations Setup",           # Gruppo CNC
    "Esporta:": "Export:",                                                                      # Tendina esporta
    "Controllo CNC:": "CNC Dialect:",                                                           # Tendina controllo CNC
    "Quote Asse X:": "X-Axis Mode:",                                                            # Tendina Diametro/Raggio
    "Modo Avanz.:": "Feed Mode:",                                                               # Tendina modalità avanzamento
    "Velocità Carro:": "Carriage Speed:",                                                       # Casella velocità carro
    "Millimetri al Giro (mm/giro - G95)": "Millimeters per Rev (mm/rev - G95)",                 # Opzione G95
    "Millimetri al Secondo (mm/s -> G94)": "Millimeters per Second (mm/s -> G94)",              # Opzione mm/s -> G94
    "Millimetri al Minuto (mm/min - G94)": "Millimeters per Minute (mm/min - G94)",             # Opzione mm/min G94
    "Programmazione al Diametro (X = 2*R)": "Diameter Programming (X = 2*R)",                   # Opzione Diametro
    "Programmazione al Raggio (X = R)": "Radius Programming (X = R)",                           # Opzione Raggio
    "Nome Prog.:": "Prog. Name:",                                                               # Nome programma
    "Opzioni di Formattazione G-Code": "G-Code Formatting Options",                             # Gruppo opzioni G-Code
    "Inserisci numeri di riga (N10, N20...)": "Output block numbers (N10, N20...)",             # Checkbox numeri N
    "Includi commenti descrittivi operazioni": "Include operation comments",                    # Checkbox commenti
    "Comanda Refrigerante automatico (M08 / M09)": "Automatic Coolant (M08 / M09)",             # Checkbox refrigerante
    "Usa ciclo compatto G76 per Filettatura (Mach3/Fanuc)": "Use canned G76 cycle for Threading (Mach3/Fanuc)",
    "Inverti segno X (X-) per vista Torretta Mach3": "Invert X sign (X-) for Mach3 Front Toolpost",
    "Anteprima Live Programma G-Code": "Live G-Code Program Preview",                           # Gruppo anteprima G-Code
    "📋 Copia Appunti": "📋 Copy Clipboard",                                                    # Bottone copia
    "💾 Salva File .NC": "💾 Save .NC File",                                                    # Bottone salva .NC
    "Gestione Profili Macchina e-CAM": "e-CAM Machine Profiles Management",                     # Gruppo profili e-CAM
    "Profilo Attivo:": "Active Profile:",                                                       # Profilo attivo
    "💾 Salva Profilo": "💾 Save Profile",                                                      # Bottone salva profilo
    "Parametri Formattazione e Codici M": "Formatting Parameters & M-Codes",                    # Gruppo formattazione e-CAM
    "Decimali X / Z:": "X / Z Decimals:",                                                       # Decimali X/Z
    "Inizio / Passo N:": "N Start / Step:",                                                     # Inizio/Passo N
    "Stile Commenti:": "Comment Style:",                                                        # Stile commenti
    "Codici Acqua ON/OFF:": "Coolant ON/OFF Codes:",                                            # Codici M acqua
    "Template Blocchi G-Code (Variabili: {PROG}, {DATE}, {DOC}, {TOOL}, {STATION}, {FEED_G}, {RPM}, {MAX_RPM}, {HOME_X}, {HOME_Z})": "G-Code Block Templates (Vars: {PROG}, {DATE}, {DOC}, {TOOL}, {STATION}, {FEED_G}, {RPM}, {MAX_RPM}, {HOME_X}, {HOME_Z})",
    "Attiva Template Personalizzati e-CAM": "Enable Custom e-CAM Block Templates",              # Checkbox attiva template
    "1. Blocco Inizio Programma (Header):": "1. Program Start Block (Header):",                 # Header
    "2. Blocco Cambio Utensile (Tool Change):": "2. Tool Change Block:",                        # Tool Change
    "3. Blocco Fine Programma (Footer):": "3. Program End Block (Footer):"                      # Footer
}                                                                                               # Fine dizionario frasi esatte

# Vocabolario completo di parole intere (\bparola\b) con singolari, plurali, verbi, aggettivi e abbreviazioni
TERMINI_PAROLE_INTERE = [                                                                       # Lista coppie (Termine Italiano, Termine Inglese)
    ("Archivio Permanente", "Permanent Presets"), ("Archivio Grezzi", "Stock Presets"),         # Locuzioni pannello Grezzo
    ("Cilindro Pieno", "Solid Cylinder"), ("Tubo Forato", "Hollow Tube"),                       # Locuzioni tipo barra
    ("Rileva Misure", "Measure Dimensions"), ("Ø Esterno Effettivo", "Effective Outer Ø"),      # Locuzioni pannello Grezzo
    ("con Sovra", "with Allowance"), ("Dati Generali", "General Data"),                         # Locuzioni generali
    ("Categoria Lavorazione", "Machining Category"), ("Angolo Reg", "Approach Angle"),          # Locuzioni utensili
    ("Angle Reg", "Approach Angle"), ("Velocità di Taglio", "Cutting Speed"),                   # Locuzioni taglio
    ("Velocità Taglio", "Cutting Speed"), ("Profondità per Passata", "Depth per Pass"),         # Locuzioni passata
    ("Profondità Passata", "Depth of Cut"), ("Pezzo Finito", "Target Part"),                    # Locuzioni moduli
    ("Foratura Asse", "Center Drilling"), ("Passate a Vuoto", "Spring Passes"),                 # Locuzioni cicli
    ("Scarico Truciolo", "Chip Breaking"), ("all'OK", "on OK"),                                 # Locuzioni UI
    ("Archivio", "Presets"), ("Permanente", "Permanent"), ("Misure", "Dimensions"),             # Parole singole Grezzo
    ("Rileva", "Detect/Measure"), ("Carica", "Load"), ("Applica", "Apply"), ("Azzera", "Reset"),
    ("Grezzi", "Stocks"), ("Grezzo", "Stock"), ("Mandrini", "Chucks"), ("Mandrino", "Chuck"),   # Singolari e plurali
    ("Sovrametalli", "Allowances"), ("Sovrametallo", "Allowance"), ("Sovra", "Allow."),         # Singolari, plurali e abbrev.
    ("Pieno", "Solid"), ("Forato", "Hollow"), ("Visiva", "Visual"), ("Visivo", "Visual"),       # Aggettivi Grezzo
    ("Effettivo", "Effective"), ("Effettiva", "Effective"), ("Reale", "Actual"),                # Aggettivi misure
    ("Fronte", "Front"), ("Frontale", "Front"), ("Base", "Base"),                               # Riferimenti geometrici
    ("Configurazione", "Configuration"), ("Impostazioni", "Settings"), ("Proprietà", "Properties"),
    ("Sgrossatura", "Roughing"), ("Finitura", "Finishing"), ("Filettatura", "Threading"),       # Lavorazioni
    ("Foratura", "Drilling"), ("Troncatura", "Parting Off"), ("Gola", "Grooving"),              # Lavorazioni
    ("Sfacciatura", "Facing"), ("Centrinatura", "Spot Drilling"), ("Maschiatura", "Tapping"),   # Lavorazioni
    ("Barenatura", "Boring"), ("Tornitura", "Turning"), ("Lavorazione", "Machining"),           # Lavorazioni
    ("Longitudinale", "Longitudinal"), ("Radiale", "Radial"), ("Assiale", "Axial"),             # Direzioni
    ("Cilindrica", "Cylindrical"), ("Conica", "Tapered"),                                       # Geometrie ciclo
    ("Esterna", "External"), ("Esterno", "Outer"), ("Interna", "Internal"), ("Interno", "Inner"),
    ("Destro", "Right-Hand"), ("Sinistro", "Left-Hand"), ("Neutro", "Neutral"),                 # Verso utensile
    ("Posteriore", "Rear"), ("Anteriore", "Front"), ("Superiore", "Upper"), ("Inferiore", "Lower"),
    ("Diametro", "Diameter"), ("Raggio", "Radius"), ("Lunghezza", "Length"),                    # Geometria
    ("Profondità", "Depth"), ("Profondita", "Depth"), ("Larghezza", "Width"), ("Altezza", "Height"),
    ("Spessore", "Thickness"), ("Sezione", "Section"), ("Angolo", "Angle"), ("Passo", "Pitch"), # Geometria
    ("Dimensioni", "Dimensions"), ("Dimensione", "Size"), ("Forma", "Shape"), ("Corpo", "Body"),
    ("Orientamento", "Orientation"), ("Spaziale", "Spatial"), ("Rotazione", "Rotation"),        # 3D Live
    ("Specchia", "Mirror"), ("Ribalta", "Flip"), ("Inclinazione", "Tilt"),                      # 3D Live
    ("Passata", "Pass"), ("Passate", "Passes"), ("Avanzamento", "Feed"),                        # Taglio
    ("Velocità", "Speed"), ("Velocita", "Speed"), ("Taglio", "Cutting"),                        # Taglio
    ("Tecnologia", "Technology"), ("Tecnologici", "Cutting"), ("Geometrici", "Geometry"),       # Schede/Gruppi
    ("Geometria", "Geometry"), ("Parametri", "Parameters"), ("Limiti", "Limits"),               # Schede/Gruppi
    ("Giri", "RPM"), ("Costante", "Constant"), ("Fissi", "Fixed"),                              # Mandrino
    ("Utensile", "Tool"), ("Utensili", "Tools"), ("Magazzino", "Library"), ("Libreria", "Library"),
    ("Torretta", "Turret"), ("Stazione", "Station"), ("Stazioni", "Stations"), ("Disco", "Disk"),
    ("Posizioni", "Positions"), ("Posizione", "Position"), ("Assegnata", "Assigned"), ("Assegnato", "Assigned"),
    ("Attiva", "Active"), ("Attivo", "Active"), ("Montati", "Mounted"), ("Montato", "Mounted"), # Stazioni
    ("Stelo", "Shank"), ("Inserto", "Insert"), ("Punta", "Tip"), ("Tagliente", "Edge"),         # Componenti utensile
    ("Lama", "Blade"), ("Collare", "Collar"), ("Sporgenza", "Overhang"),                        # Componenti utensile
    ("Pezzo", "Part"), ("Finito", "Target"), ("Modello", "Model"),                              # Pezzo/Grezzo
    ("Solido", "Solid"), ("Oggetto", "Object"), ("Barra", "Bar"), ("Tubo", "Tube"), ("Cilindro", "Cylinder"),
    ("Autocentrante", "Chuck"), ("Griffe", "Jaws"), ("Presa", "Grip"), ("Foro", "Bore"),        # Mandrino
    ("Origine", "Origin"), ("Punto", "Point"), ("Quota", "Coord"), ("Quote", "Coords"),         # WCS
    ("Inizio", "Start"), ("Iniziale", "Start"), ("Fine", "End"), ("Finale", "End"),             # Limiti
    ("Massimo", "Max"), ("Minimo", "Min"), ("Totale", "Total"), ("Sicurezza", "Safety"),        # Limiti
    ("Distacco", "Clearance"), ("Rientro", "Retract"), ("Uscita", "Exit"), ("Ingresso", "Entry"),
    ("Scarico", "Peck"), ("Truciolo", "Chip"), ("Vuoto", "Spring"), ("Pulizia", "Clean"),       # Cicli
    ("Tuffo", "Plunge"), ("Tuffi", "Pecks"), ("Incremento", "Step"), ("Sosta", "Dwell"),        # Cicli
    ("Smusso", "Chamfer"), ("Raccordo", "Corner R"), ("Spigolo", "Edge"), ("Fondo", "Root"),    # Finitura/Gola
    ("Filetto", "Thread"), ("Cresta", "Crest"), ("Fianco", "Flank"), ("Conicità", "Taper"),     # Filettatura
    ("Modalità", "Mode"), ("Modalita", "Mode"), ("Categoria", "Category"), ("Verso", "Direction"),
    ("Direzione", "Direction"), ("Tipo", "Type"), ("Ciclo", "Cycle"), ("Profilo", "Profile"), ("Asse", "Axis"),
    ("Seleziona", "Select"), ("Selezionato", "Selected"), ("Selezionata", "Selected"),          # Azioni
    ("Acquisisci", "Pick"), ("Faccia", "Face"), ("Bordo", "Edge"), ("Vertice", "Vertex"), ("Centro", "Center"),
    ("Allinea", "Align"), ("Adatta", "Fit"), ("Mostra", "Show"), ("Visualizza", "Display"),     # Azioni
    ("Inverti", "Invert"), ("Usa", "Use"), ("Calcola", "Calculate"), ("Ricalcola", "Recompute"),
    ("Aggiorna", "Update"), ("Anteprima", "Preview"), ("Nuovo", "New"), ("Elimina", "Delete"),  # Bottoni
    ("Salva", "Save"), ("Ripristina", "Reset"), ("Importa", "Import"), ("Esporta", "Export"),   # Bottoni
    ("Copia", "Copy"), ("Appunti", "Clipboard"), ("Chiudi", "Close"), ("Annulla", "Cancel"),    # Bottoni
    ("Cambio", "Change"), ("Macchina", "Machine"), ("Stile", "Style"), ("Numero", "Number"),    # Vari
    ("Nome", "Name"), ("Colore", "Color"), ("Trasparenza", "Transparency"), ("Nessuno", "None"),
    ("Automatico", "Automatic"), ("Automatica", "Automatic"), ("Manuale", "Manual"),            # Vari
    ("dal", "from"), ("dalla", "from"), ("del", "of"), ("della", "of"), ("delle", "of"),        # Preposizioni
    ("dei", "of"), ("degli", "of"), ("di", "of"), ("per", "per"), ("su", "on"), ("sul", "on"),  # Preposizioni
    ("sulla", "on"), ("da", "from"), ("al", "to"), ("alla", "to"), ("con", "with"), ("e", "&")  # Preposizioni
]                                                                                               # Fine vocabolario parole intere


def traduci(testo):                                                                             # Funzione principale di traduzione verso l'Inglese
    if not testo:                                                                               # Se la stringa è vuota
        return testo                                                                            # Ritorna subito
    s_orig = str(testo)                                                                         # Converte in stringa
    s_norm = re.sub(r"\s*_\s*", " & ", s_orig).strip()                                          # Ripristina eventuali '_' (generati da '&' in Qt) in ' & '

    if s_orig.strip() in TRADUZIONI:                                                            # 1A. Controllo frase esatta originale
        return TRADUZIONI[s_orig.strip()]                                                       # Restituisce traduzione esatta
    if s_norm in TRADUZIONI:                                                                    # 1B. Controllo frase normalizzata (senza underscore)
        return TRADUZIONI[s_norm]                                                               # Restituisce traduzione esatta

    if s_norm.startswith("Velocità ("):                                                         # Etichetta dinamica velocità simulatore
        return s_norm.replace("Velocità (", "Speed (")                                          # Traduce in Speed (...)
    if s_norm.startswith("Statistiche:"):                                                       # Etichetta dinamica statistiche post-processor
        return s_norm.replace("Statistiche:", "Stats:").replace("righe generate", "lines").replace("utensili impiegati", "tools")

    risultato = s_norm                                                                          # 2. Traduzione intelligente di tutte le parole intere (\b...\b)
    for it_word, en_word in TERMINI_PAROLE_INTERE:                                              # Scorre il vocabolario completo
        pattern = r"\b" + re.escape(it_word.strip()) + r"\b"                                    # Confine rigoroso di parola intera
        if re.search(pattern, risultato, flags=re.IGNORECASE):                                  # Se il termine intero è presente
            risultato = re.sub(pattern, en_word.strip(), risultato, flags=re.IGNORECASE)        # Sostituisce il termine con l'equivalente inglese
    return risultato                                                                            # Restituisce la stringa completamente in Inglese