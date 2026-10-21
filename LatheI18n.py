import FreeCAD                                                                                  # Importa il modulo base di FreeCAD
import FreeCADGui                                                                               # Importa il modulo interfaccia grafica di FreeCAD


TRANSLATIONS = {                                                                                # Dizionario principale delle traduzioni IT / EN
    "it": {                                                                                     # Sezione lingua Italiana
        "WB_NAME": "Tornio CAM",                                                                # Nome del Workbench
        "WB_TOOLTIP": "Ambiente CAM per Tornitura CNC, Torretta 3D e Simulazione",              # Descrizione del Workbench
        "TOOLBAR_SETUP": "Tornio CAM - Setup Macchina",                                         # Nome barra strumenti Setup
        "TOOLBAR_OPS": "Tornio CAM - Lavorazioni",                                              # Nome barra strumenti Lavorazioni
        "TOOLBAR_SIM": "Tornio CAM - Verifica e G-Code",                                        # Nome barra strumenti Simulazione
        "MENU_MAIN": "Tornio CAM",                                                              # Voce di menu principale

        "SETUP_TITLE": "1. Setup Macchina (WCS)",                                               # Titolo comando Setup
        "SETUP_TOOLTIP": "Configura origine Zero Pezzo (G54..G59), piani di sicurezza e CNC",   # Tooltip comando Setup
        "STOCK_TITLE": "2. Grezzo e Autocentrante",                                             # Titolo comando Grezzo
        "STOCK_TOOLTIP": "Definisci barra grezza (tonda, tubo, quadra, esagonale), griffe e contropunta", # Tooltip Grezzo
        "TOOL_TITLE": "3. Magazzino Utensili",                                                  # Titolo comando Utensili
        "TOOL_TOOLTIP": "Crea, modifica e archivia utensili da tornio parametrici o STEP 3D",   # Tooltip Utensili
        "TURRET_TITLE": "4. Torretta Porta-Utensili",                                           # Titolo comando Torretta
        "TURRET_TOOLTIP": "Configura il plateau torretta, monta gli utensili e verifica le collisioni", # Tooltip Torretta

        "ROUGH_TITLE": "Sgrossatura / Sfacciatura",                                             # Titolo comando Sgrossatura
        "ROUGH_TOOLTIP": "Ciclo di sgrossatura longitudinale o sfacciatura frontale",           # Tooltip Sgrossatura
        "FINISH_TITLE": "Finitura Profilo",                                                     # Titolo comando Finitura
        "FINISH_TOOLTIP": "Ciclo di finitura continua sul profilo del pezzo",                   # Tooltip Finitura
        "GROOVE_TITLE": "Gola / Scarico",                                                       # Titolo comando Gola
        "GROOVE_TOOLTIP": "Ciclo di esecuzione gole esterne, interne o frontali",               # Tooltip Gola
        "THREAD_TITLE": "Filettatura",                                                          # Titolo comando Filettatura
        "THREAD_TOOLTIP": "Ciclo di filettatura cilindrica o conica (ISO, GAS, Trapezoidale)",  # Tooltip Filettatura
        "DRILL_TITLE": "Foratura / Maschiatura",                                                # Titolo comando Foratura
        "DRILL_TOOLTIP": "Ciclo di foratura assiale, scarico truciolo (G83) o maschiatura",     # Tooltip Foratura
        "PART_TITLE": "Troncatura Pezzo",                                                       # Titolo comando Troncatura
        "PART_TOOLTIP": "Ciclo di taglio e distacco finale del pezzo finito dalla barra",       # Tooltip Troncatura

        "SIM_TITLE": "Simulazione 3D",                                                          # Titolo comando Simulazione
        "SIM_TOOLTIP": "Simula il movimento della torretta armata e verifica le collisioni",    # Tooltip Simulazione
        "POST_TITLE": "Esporta G-Code",                                                         # Titolo comando Post-Processor
        "POST_TOOLTIP": "Genera ed esporta il programma ISO G-Code per il controllo CNC",       # Tooltip Post-Processor

        "MSG_NO_DOC": "Attenzione: Apri o crea prima un documento FreeCAD!",                    # Messaggio nessun documento
        "MSG_NEED_SETUP": "Attenzione: Definisci prima il '1. Setup Macchina (WCS)'!",          # Messaggio richiede Setup
        "MSG_NEED_STOCK": "Attenzione: Definisci prima il '2. Grezzo e Autocentrante'!",        # Messaggio richiede Grezzo
        "MSG_NEED_TOOLS": "Attenzione: Crea almeno un utensile nel '3. Magazzino Utensili'!"    # Messaggio richiede Utensili
    },                                                                                          # Fine dizionario Italiano
    "en": {                                                                                     # Sezione lingua Inglese (Fallback internazionale)
        "WB_NAME": "Lathe CAM",                                                                 # Nome del Workbench EN
        "WB_TOOLTIP": "CNC Turning CAM Workbench, 3D Turret and Simulation",                    # Descrizione EN
        "TOOLBAR_SETUP": "Lathe CAM - Machine Setup",                                           # Barra Setup EN
        "TOOLBAR_OPS": "Lathe CAM - Operations",                                                # Barra Lavorazioni EN
        "TOOLBAR_SIM": "Lathe CAM - Verify & G-Code",                                           # Barra Simulazione EN
        "MENU_MAIN": "Lathe CAM",                                                               # Menu principale EN

        "SETUP_TITLE": "1. Machine Setup (WCS)",                                                # Titolo Setup EN
        "SETUP_TOOLTIP": "Configure Work Coordinate System (G54..G59), clearance planes and CNC",
        "STOCK_TITLE": "2. Stock & Chuck Jaws",                                                 # Titolo Grezzo EN
        "STOCK_TOOLTIP": "Define stock bar (round, tube, square, hex), chuck jaws and tailstock",
        "TOOL_TITLE": "3. Tool Library Manager",                                                # Titolo Utensili EN
        "TOOL_TOOLTIP": "Create, edit and store parametric or 3D STEP turning tools",
        "TURRET_TITLE": "4. Tool Turret 3D",                                                    # Titolo Torretta EN
        "TURRET_TOOLTIP": "Configure turret disc, mount tools onto stations and check collisions",

        "ROUGH_TITLE": "Roughing / Facing",                                                     # Titolo Sgrossatura EN
        "ROUGH_TOOLTIP": "Longitudinal roughing or front facing cycle",
        "FINISH_TITLE": "Profile Finishing",                                                    # Titolo Finitura EN
        "FINISH_TOOLTIP": "Continuous finishing cycle along part profile",
        "GROOVE_TITLE": "Grooving",                                                             # Titolo Gola EN
        "GROOVE_TOOLTIP": "External, internal or face grooving cycle",
        "THREAD_TITLE": "Threading",                                                            # Titolo Filettatura EN
        "THREAD_TOOLTIP": "Single-point threading cycle (Metric, BSP, Acme)",
        "DRILL_TITLE": "Center Drilling / Tapping",                                             # Titolo Foratura EN
        "DRILL_TOOLTIP": "Axial drilling, peck drilling (G83) or tapping cycle",
        "PART_TITLE": "Parting Off",                                                            # Titolo Troncatura EN
        "PART_TOOLTIP": "Cut-off cycle to separate finished part from bar stock",

        "SIM_TITLE": "3D Simulation",                                                           # Titolo Simulazione EN
        "SIM_TOOLTIP": "Simulate full 3D turret kinematics and check collisions",
        "POST_TITLE": "Post-Process G-Code",                                                    # Titolo G-Code EN
        "POST_TOOLTIP": "Generate and export CNC G-Code program",

        "MSG_NO_DOC": "Warning: Please open or create a FreeCAD document first!",               # Avviso documento EN
        "MSG_NEED_SETUP": "Warning: Please define '1. Machine Setup (WCS)' first!",             # Avviso Setup EN
        "MSG_NEED_STOCK": "Warning: Please define '2. Stock & Chuck Jaws' first!",              # Avviso Grezzo EN
        "MSG_NEED_TOOLS": "Warning: Please create at least one tool in '3. Tool Library'!"      # Avviso Utensili EN
    }                                                                                           # Fine dizionario Inglese
}                                                                                               # Fine dizionario TRANSLATIONS


def get_current_lang():                                                                         # Rileva la lingua impostata nelle preferenze di FreeCAD
    try:                                                                                        # Tenta la lettura dei parametri lingua di FreeCAD
        p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/General")                      # Accede alle preferenze generali
        lang = p.GetString("Language", "Italian").lower()                                       # Legge la stringa della lingua
        if "ital" in lang or lang.startswith("it"):                                             # Se è impostato Italiano
            return "it"                                                                         # Restituisce codice "it"
        if "eng" in lang or lang.startswith("en"):                                              # Se è impostato Inglese
            return "en"                                                                         # Restituisce codice "en"
    except Exception:                                                                           # In caso di errore di lettura preferenze
        pass                                                                                    # Passa al valore predefinito
    return "it"                                                                                 # Lingua predefinita: Italiano


def tr(key, default=None):                                                                      # Traduce una chiave nella lingua corrente senza mai dare errore
    lang = get_current_lang()                                                                   # Ottiene il codice lingua corrente ("it" o "en")
    diz_lang = TRANSLATIONS.get(lang, TRANSLATIONS["it"])                                       # Prende il dizionario della lingua scelta
    if key in diz_lang:                                                                         # Se la chiave esiste nel dizionario corrente
        return diz_lang[key]                                                                    # Restituisce il testo tradotto
    if key in TRANSLATIONS["it"]:                                                               # Fallback sul dizionario Italiano
        return TRANSLATIONS["it"][key]                                                          # Restituisce il testo Italiano
    return default if default is not None else key                                              # Restituisce il default o la chiave stessa