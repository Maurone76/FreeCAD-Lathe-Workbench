import os                                                                                       # Importa il modulo per gestire percorsi e cartelle su disco
import FreeCAD                                                                                  # Importa il modulo base di FreeCAD


def get_workbench_dir():                                                                        # Restituisce la cartella principale del Workbench
    return os.path.dirname(os.path.abspath(__file__))                                           # Percorso assoluto della cartella corrente


def get_icons_dir():                                                                            # Restituisce il percorso della sottocartella icons
    icons_dir = os.path.join(get_workbench_dir(), "icons")                                      # Combina il percorso base con "icons"
    os.makedirs(icons_dir, exist_ok=True)                                                       # Crea la cartella icons se non esiste ancora
    return icons_dir                                                                            # Restituisce il percorso completo


def ensure_workbench_folders():                                                                 # Crea tutte le sottocartelle di archivio del Workbench
    base = get_workbench_dir()                                                                  # Ottiene la cartella radice del Workbench
    folders = [                                                                                 # Elenco delle sottocartelle necessarie al sistema
        "icons",                                                                                # Cartella per le icone SVG/PNG della toolbar e dell'albero
        "MachineLibrary",                                                                       # Archivio configurazioni Setup Macchina (machines_db.json)
        "StockLibrary",                                                                         # Archivio configurazioni Grezzo e Mandrino (stocks_db.json)
        "ToolLibrary",                                                                          # Archivio Utensili e geometrie STEP/BREP (tools_db.json)
        "TurretLibrary"                                                                         # Archivio Torrette e saldature utensili (turrets_db.json)
    ]                                                                                           # Fine elenco cartelle
    for folder in folders:                                                                      # Cicla su ogni nome cartella
        os.makedirs(os.path.join(base, folder), exist_ok=True)                                  # Crea la cartella su disco se assente
    generate_default_svg_icons()                                                                # Genera le icone SVG predefinite se non sono ancora presenti


def get_icon_path(icon_filename, fallback="Std_Tool1"):                                         # Restituisce il percorso dell'icona SVG o il fallback di FreeCAD
    ensure_workbench_folders()                                                                  # Assicura che la cartella e le icone base esistano
    full_path = os.path.join(get_icons_dir(), icon_filename)                                    # Costruisce il percorso completo del file .svg
    if os.path.exists(full_path):                                                               # Verifica se il file esiste su disco
        return full_path.replace("\\", "/")                                                     # Restituisce il percorso normalizzato per Qt/FreeCAD
    return fallback                                                                             # Restituisce l'icona interna di FreeCAD come sicurezza


def _wrap_svg(inner_elements):                                                                  # Racchiude gli elementi grafici in un'intestazione SVG 64x64
    return (                                                                                    # Restituisce la stringa XML SVG completa
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'                              # Dichiarazione XML standard
        '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">\n' # Area di disegno 64x64 pixel
        f'{inner_elements}\n'                                                                   # Contenuto vettoriale specifico dell'icona
        '</svg>\n'                                                                              # Chiusura tag SVG
    )                                                                                           # Fine wrapper SVG


def generate_default_svg_icons():                                                               # Genera su disco i file .svg se non esistono già
    icons_dir = get_icons_dir()                                                                 # Ottiene la cartella icons

    svg_defs = {                                                                                # Dizionario {nome_file.svg: contenuto_vettoriale}
        "lathe_workbench.svg": _wrap_svg(                                                       # Icona generale del Workbench Tornio CAM
            '<rect x="6" y="14" width="16" height="36" rx="2" fill="#3B4252" stroke="#D8DEE9" stroke-width="2"/>'
            '<rect x="22" y="24" width="28" height="16" fill="#D08770" stroke="#2E3440" stroke-width="2"/>'
            '<polygon points="42,52 50,36 56,52" fill="#EBCB8B" stroke="#2E3440" stroke-width="2"/>'
            '<circle cx="14" cy="32" r="4" fill="#88C0D0"/>'
        ),
        "lathe_setup.svg": _wrap_svg(                                                           # Icona 1: Setup Macchina e Terna WCS
            '<circle cx="20" cy="44" r="10" fill="none" stroke="#EBCB8B" stroke-width="2.5"/>'
            '<path d="M20,34 L20,44 L30,44 Z" fill="#EBCB8B"/>'
            '<line x1="20" y1="44" x2="20" y2="10" stroke="#BF616A" stroke-width="4" stroke-linecap="round"/>'
            '<polygon points="20,4 14,14 26,14" fill="#BF616A"/>'
            '<line x1="20" y1="44" x2="54" y2="44" stroke="#5E81AC" stroke-width="4" stroke-linecap="round"/>'
            '<polygon points="60,44 50,38 50,50" fill="#5E81AC"/>'
        ),
        "lathe_stock.svg": _wrap_svg(                                                           # Icona 2: Grezzo e Autocentrante a Griffe
            '<rect x="6" y="10" width="14" height="44" rx="2" fill="#4C566A" stroke="#2E3440" stroke-width="2"/>'
            '<rect x="20" y="14" width="8" height="10" fill="#81A1C1" stroke="#2E3440" stroke-width="1.5"/>'
            '<rect x="20" y="40" width="8" height="10" fill="#81A1C1" stroke="#2E3440" stroke-width="1.5"/>'
            '<rect x="20" y="22" width="36" height="20" fill="#EBCB8B" fill-opacity="0.8" stroke="#D08770" stroke-width="2"/>'
            '<line x1="16" y1="32" x2="60" y2="32" stroke="#BF616A" stroke-width="1.5" stroke-dasharray="4,3"/>'
        ),
        "lathe_tool.svg": _wrap_svg(                                                            # Icona 3: Magazzino Utensili (Stelo + Inserto Oro)
            '<polygon points="30,10 48,10 48,56 30,56 30,28 18,20" fill="#434C5E" stroke="#2E3440" stroke-width="2"/>'
            '<polygon points="14,16 32,12 28,28 14,24" fill="#EBCB8B" stroke="#2E3440" stroke-width="2"/>'
            '<circle cx="23" cy="20" r="2.5" fill="#2E3440"/>'
        ),
        "lathe_turret.svg": _wrap_svg(                                                          # Icona 4: Torretta Ottagonale Porta-Utensili
            '<polygon points="24,8 40,8 56,24 56,40 40,56 24,56 8,40 8,24" fill="#4C566A" stroke="#D8DEE9" stroke-width="2"/>'
            '<circle cx="32" cy="32" r="10" fill="#2E3440" stroke="#88C0D0" stroke-width="2"/>'
            '<line x1="32" y1="8" x2="32" y2="18" stroke="#EBCB8B" stroke-width="3"/>'
            '<line x1="32" y1="46" x2="32" y2="56" stroke="#EBCB8B" stroke-width="3"/>'
            '<line x1="8" y1="32" x2="18" y2="32" stroke="#EBCB8B" stroke-width="3"/>'
            '<line x1="46" y1="32" x2="56" y2="32" stroke="#EBCB8B" stroke-width="3"/>'
        ),
        "lathe_roughing.svg": _wrap_svg(                                                        # Icona Operazione: Sgrossatura a passate
            '<polygon points="8,48 8,24 28,24 28,34 46,34 46,48" fill="#D08770" stroke="#2E3440" stroke-width="2"/>'
            '<line x1="10" y1="18" x2="56" y2="18" stroke="#A3BE8C" stroke-width="2.5" stroke-dasharray="4,2"/>'
            '<line x1="30" y1="26" x2="56" y2="26" stroke="#A3BE8C" stroke-width="2.5" stroke-dasharray="4,2"/>'
            '<polygon points="46,10 56,10 50,22" fill="#EBCB8B" stroke="#2E3440" stroke-width="1.5"/>'
        ),
        "lathe_finishing.svg": _wrap_svg(                                                       # Icona Operazione: Finitura continua profilo
            '<path d="M8,50 L8,22 L24,22 L36,34 L54,34 L54,50 Z" fill="#81A1C1" stroke="#2E3440" stroke-width="2"/>'
            '<path d="M8,16 L26,16 L38,28 L56,28" fill="none" stroke="#EBCB8B" stroke-width="3.5"/>'
            '<polygon points="36,12 46,12 40,24" fill="#EBCB8B" stroke="#2E3440" stroke-width="1.5"/>'
        ),
        "lathe_grooving.svg": _wrap_svg(                                                        # Icona Operazione: Gola / Scarico
            '<path d="M6,50 L6,24 L22,24 L22,40 L42,40 L42,24 L58,24 L58,50 Z" fill="#D08770" stroke="#2E3440" stroke-width="2"/>'
            '<rect x="27" y="8" width="10" height="20" fill="#434C5E" stroke="#2E3440" stroke-width="1.5"/>'
            '<rect x="26" y="26" width="12" height="8" fill="#EBCB8B" stroke="#2E3440" stroke-width="1.5"/>'
        ),
        "lathe_threading.svg": _wrap_svg(                                                       # Icona Operazione: Filettatura
            '<polygon points="6,50 6,28 14,38 22,28 30,38 38,28 46,38 54,28 58,34 58,50" fill="#88C0D0" stroke="#2E3440" stroke-width="2"/>'
            '<polygon points="24,10 36,10 30,24" fill="#EBCB8B" stroke="#2E3440" stroke-width="2"/>'
        ),
        "lathe_drilling.svg": _wrap_svg(                                                        # Icona Operazione: Foratura Assiale
            '<rect x="6" y="14" width="24" height="12" fill="#D08770" stroke="#2E3440" stroke-width="1.5"/>'
            '<rect x="6" y="38" width="24" height="12" fill="#D08770" stroke="#2E3440" stroke-width="1.5"/>'
            '<polygon points="22,32 34,24 58,24 58,40 34,40" fill="#EBCB8B" stroke="#2E3440" stroke-width="2"/>'
            '<line x1="36" y1="24" x2="44" y2="40" stroke="#2E3440" stroke-width="2"/>'
            '<line x1="46" y1="24" x2="54" y2="40" stroke="#2E3440" stroke-width="2"/>'
        ),
        "lathe_parting.svg": _wrap_svg(                                                         # Icona Operazione: Troncatura Pezzo
            '<rect x="6" y="20" width="20" height="32" fill="#D08770" stroke="#2E3440" stroke-width="2"/>'
            '<rect x="38" y="24" width="20" height="28" fill="#81A1C1" stroke="#2E3440" stroke-width="2"/>'
            '<rect x="29" y="6" width="6" height="32" fill="#434C5E" stroke="#2E3440" stroke-width="1.5"/>'
            '<rect x="28" y="36" width="8" height="8" fill="#EBCB8B" stroke="#2E3440" stroke-width="1.5"/>'
        ),
        "lathe_simulation.svg": _wrap_svg(                                                      # Icona Verifica: Simulazione 3D (Play)
            '<circle cx="32" cy="32" r="24" fill="#2E5A27" stroke="#A3BE8C" stroke-width="3"/>'
            '<polygon points="24,18 48,32 24,46" fill="#ECEFF4"/>'
        ),
        "lathe_post.svg": _wrap_svg(                                                            # Icona Output: Esporta G-Code
            '<rect x="12" y="8" width="40" height="48" rx="3" fill="#3B4252" stroke="#88C0D0" stroke-width="2"/>'
            '<line x1="20" y1="20" x2="44" y2="20" stroke="#EBCB8B" stroke-width="3"/>'
            '<line x1="20" y1="30" x2="44" y2="30" stroke="#A3BE8C" stroke-width="3"/>'
            '<line x1="20" y1="40" x2="36" y2="40" stroke="#88C0D0" stroke-width="3"/>'
        )
    }                                                                                           # Fine dizionario icone SVG

    for filename, svg_content in svg_defs.items():                                              # Cicla su ogni icona definita
        path = os.path.join(icons_dir, filename)                                                # Percorso completo del file .svg
        if not os.path.exists(path):                                                            # Crea il file solo se non esiste (non sovrascrive icone custom dell'utente)
            try:                                                                                # Tenta la scrittura del file SVG su disco
                with open(path, "w", encoding="utf-8") as f:                                    # Apre il file in scrittura UTF-8
                    f.write(svg_content)                                                        # Scrive il codice XML vettoriale
            except Exception as e:                                                              # Cattura eventuali errori di permessi
                FreeCAD.Console.PrintError(f"Errore creazione icona {filename}: {e}\n")         # Stampa l'errore in console