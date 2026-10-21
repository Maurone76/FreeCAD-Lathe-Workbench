import os                                                                                       # Importa il modulo os per gestire i percorsi delle icone e delle cartelle
import sys                                                                                      # Importa sys per registrare i moduli caricati dalla sottocartella translations
import inspect                                                                                  # Importa inspect per rilevare automaticamente le classi e funzioni nei moduli CAM
import importlib                                                                                # Importa importlib per ricaricare i moduli senza riavviare FreeCAD
import importlib.util                                                                           # Importa importlib.util per caricare i file di traduzione dalla cartella dedicata
import FreeCAD                                                                                  # Importa il modulo base di FreeCAD
import FreeCADGui                                                                               # Importa il modulo interfaccia grafica di FreeCAD
from PySide import QtCore, QtGui                                                                # Importa i moduli grafici PySide
try:                                                                                            # Tenta di importare QtWidgets per compatibilità Qt5/Qt6
    from PySide import QtWidgets                                                                # Assegna QtWidgets
except ImportError:                                                                             # Fallback per versioni meno recenti
    QtWidgets = QtGui                                                                           # Usa QtGui come alias di QtWidgets

MOD_DIR = os.path.dirname(__file__)                                                             # Cartella radice del Workbench (es. LatheCAM_2)
ICON_DIR = os.path.join(MOD_DIR, "icons")                                                       # Sottocartella predefinita per le icone SVG
TRANS_DIR = os.path.join(MOD_DIR, "translations")                                               # Sottocartella dedicata per i file delle traduzioni (traduzione_IT/EN/DE/ES.py)

try:                                                                                            # Assicura che la cartella translations/ esista già sul disco
    if not os.path.exists(TRANS_DIR):                                                           # Se la cartella translations/ non esiste ancora
        os.makedirs(TRANS_DIR, exist_ok=True)                                                   # La crea automaticamente dentro LatheCAM_2
except Exception:                                                                               # Ignora errori di permessi
    pass                                                                                        # Continua

SVG_ICONS_DATA = {                                                                              # Dizionario con il codice vettoriale SVG delle 13 icone del Workbench
    "Lathe_Setup.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <circle cx="20" cy="44" r="7" fill="#FFCC00" stroke="#222" stroke-width="2"/>
        <line x1="20" y1="44" x2="56" y2="44" stroke="#3388FF" stroke-width="5" stroke-linecap="round"/>
        <polygon points="58,44 46,38 46,50" fill="#3388FF"/>
        <line x1="20" y1="44" x2="20" y2="8" stroke="#FF4444" stroke-width="5" stroke-linecap="round"/>
        <polygon points="20,6 14,18 26,18" fill="#FF4444"/>
        <text x="48" y="35" font-family="Arial" font-size="14" font-weight="bold" fill="#3388FF">Z</text>
        <text x="28" y="18" font-family="Arial" font-size="14" font-weight="bold" fill="#FF4444">X</text>
    </svg>""",                                                                                  # Icona 1: Assi WCS X/Z
    "Lathe_Stock.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <rect x="6" y="10" width="14" height="44" rx="2" fill="#667788" stroke="#222" stroke-width="2"/>
        <rect x="16" y="14" width="8" height="10" fill="#445566" stroke="#222" stroke-width="1.5"/>
        <rect x="16" y="40" width="8" height="10" fill="#445566" stroke="#222" stroke-width="1.5"/>
        <rect x="20" y="18" width="38" height="28" rx="3" fill="#D49A45" stroke="#222" stroke-width="2"/>
        <ellipse cx="58" cy="32" rx="3" ry="14" fill="#E6B86A" stroke="#222" stroke-width="1.5"/>
    </svg>""",                                                                                  # Icona 2: Grezzo e Mandrino Autocentrante
    "Lathe_Part.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <polygon points="8,16 26,16 36,24 56,24 56,40 36,40 26,48 8,48" fill="#44AAEE" stroke="#113355" stroke-width="2.5" stroke-linejoin="round"/>
        <line x1="4" y1="32" x2="60" y2="32" stroke="#FFCC00" stroke-width="2" stroke-dasharray="6,4"/>
    </svg>""",                                                                                  # Icona 3: Pezzo Finito 3D
    "Lathe_Tools.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <rect x="24" y="6" width="18" height="34" fill="#556677" stroke="#222" stroke-width="2"/>
        <polygon points="24,40 42,40 30,56 18,52" fill="#FFCC00" stroke="#222" stroke-width="2" stroke-linejoin="round"/>
        <circle cx="28" cy="46" r="3.5" fill="#444"/>
    </svg>""",                                                                                  # Icona 4: Magazzino Utensili
    "Lathe_Turret.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <polygon points="22,8 42,8 56,22 56,42 42,56 22,56 8,42 8,22" fill="#4A5568" stroke="#1A202C" stroke-width="2.5"/>
        <circle cx="32" cy="32" r="10" fill="#A0AEC0" stroke="#1A202C" stroke-width="2"/>
        <polygon points="32,56 26,63 38,63" fill="#FFCC00" stroke="#222" stroke-width="1.5"/>
        <polygon points="8,32 1,26 1,38" fill="#FFCC00" stroke="#222" stroke-width="1.5"/>
        <polygon points="56,32 63,26 63,38" fill="#FFCC00" stroke="#222" stroke-width="1.5"/>
    </svg>""",                                                                                  # Icona 5: Torretta Portautensili 3D
    "Lathe_Roughing.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <polygon points="8,54 8,28 24,28 40,42 56,42 56,54" fill="#8899AA" stroke="#222" stroke-width="2"/>
        <line x1="12" y1="14" x2="58" y2="14" stroke="#22DD44" stroke-width="3"/>
        <line x1="16" y1="21" x2="58" y2="21" stroke="#22DD44" stroke-width="3"/>
        <line x1="28" y1="28" x2="58" y2="28" stroke="#22DD44" stroke-width="3"/>
        <line x1="38" y1="35" x2="58" y2="35" stroke="#22DD44" stroke-width="3"/>
    </svg>""",                                                                                  # Icona 6: Sgrossatura
    "Lathe_Finishing.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <polygon points="8,54 8,24 26,24 42,40 56,40 56,54" fill="#5599DD" stroke="#222" stroke-width="2"/>
        <polyline points="8,18 28,18 44,34 58,34" fill="none" stroke="#FFAA00" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>""",                                                                                  # Icona 7: Finitura
    "Lathe_Grooving.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <polygon points="6,54 6,26 24,26 24,44 40,44 40,26 58,26 58,54" fill="#99AABB" stroke="#222" stroke-width="2"/>
        <rect x="28" y="6" width="8" height="34" fill="#FFCC00" stroke="#222" stroke-width="2"/>
    </svg>""",                                                                                  # Icona 8: Gola
    "Lathe_Threading.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <polygon points="6,54 6,28 12,38 18,28 24,38 30,28 36,38 42,28 48,38 54,28 58,35 58,54" fill="#77AA99" stroke="#222" stroke-width="2" stroke-linejoin="round"/>
        <polygon points="26,8 34,8 30,24" fill="#FFCC00" stroke="#222" stroke-width="2"/>
    </svg>""",                                                                                  # Icona 9: Filettatura
    "Lathe_Drilling.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <rect x="6" y="14" width="26" height="36" fill="#8899AA" stroke="#222" stroke-width="2"/>
        <polygon points="6,24 22,24 28,32 22,40 6,40" fill="#2B303B"/>
        <polygon points="58,26 34,26 26,32 34,38 58,38" fill="#FFCC00" stroke="#222" stroke-width="2"/>
    </svg>""",                                                                                  # Icona 10: Foratura Asse
    "Lathe_Parting.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <rect x="6" y="22" width="20" height="32" fill="#8899AA" stroke="#222" stroke-width="2"/>
        <rect x="38" y="22" width="20" height="32" fill="#5599DD" stroke="#222" stroke-width="2"/>
        <rect x="29" y="6" width="6" height="48" fill="#FF4444" stroke="#222" stroke-width="1.5"/>
    </svg>""",                                                                                  # Icona 11: Troncatura
    "Lathe_Simulation.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r="26" fill="#2E6B27" stroke="#1B4317" stroke-width="3"/>
        <polygon points="24,18 24,46 48,32" fill="#FFFFFF"/>
    </svg>""",                                                                                  # Icona 12: Simulazione 3D
    "Lathe_PostProcess.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
        <rect x="10" y="6" width="44" height="52" rx="4" fill="#1E222A" stroke="#88C0D0" stroke-width="2.5"/>
        <text x="16" y="26" font-family="Consolas,monospace" font-size="13" font-weight="bold" fill="#A3BE8C">G01</text>
        <text x="16" y="42" font-family="Consolas,monospace" font-size="13" font-weight="bold" fill="#EBCB8B">X20</text>
        <text x="16" y="54" font-family="Consolas,monospace" font-size="12" font-weight="bold" fill="#88C0D0">M30</text>
    </svg>"""                                                                                   # Icona 13: Post-Processor G-Code
}                                                                                               # Fine dizionario icone SVG


def get_icon_file(filename):                                                                    # Restituisce il percorso dell'icona (cercandola o rigenerandola automaticamente)
    percorsi_possibili = [                                                                      # Elenco delle cartelle in cui cercare l'icona esistente
        os.path.join(MOD_DIR, "icons", filename),                                               # 1. Cartella icons/
        os.path.join(MOD_DIR, "Resources", "icons", filename),                                  # 2. Cartella Resources/icons/
        os.path.join(MOD_DIR, "Icons", filename),                                               # 3. Cartella Icons/
        os.path.join(MOD_DIR, filename)                                                         # 4. Cartella radice del modulo
    ]                                                                                           # Fine lista percorsi
    for p in percorsi_possibili:                                                                # Controlla se il file esiste già in una delle cartelle
        if os.path.exists(p):                                                                   # Se trovato
            return p                                                                            # Restituisce il percorso esistente

    try:                                                                                        # Creazione automatica icona SVG se non presente sul disco
        if not os.path.exists(ICON_DIR):                                                        # Se la cartella icons/ non esiste
            os.makedirs(ICON_DIR, exist_ok=True)                                                # La crea
        target_path = os.path.join(ICON_DIR, filename)                                          # Percorso file da salvare
        svg_content = SVG_ICONS_DATA.get(filename, SVG_ICONS_DATA["Lathe_Setup.svg"])           # Prende il contenuto SVG corrispondente
        with open(target_path, "w", encoding="utf-8") as f:                                     # Apre il file in scrittura
            f.write(svg_content.strip())                                                        # Scrive l'SVG
        return target_path                                                                      # Restituisce il percorso valido appena creato
    except Exception:                                                                           # In caso di permessi negati
        return ""                                                                               # Fallback vuoto


# ==============================================================================
# GESTIONE FILE DI TRADUZIONE DALLA CARTELLA DEDICATA "translations/"
# ==============================================================================
def rileva_codice_lingua():                                                                     # Rileva il codice lingua impostato nelle preferenze di FreeCAD ("it", "en", "de", "es")
    raw_lang = ""                                                                               # Stringa lingua grezza
    try:                                                                                        # 1. Legge la preferenza salvata nel registro interno di FreeCAD
        raw_lang = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/General").GetString("Language", "").strip().lower()
    except Exception:                                                                           # Se non disponibile
        pass                                                                                    # Continua
    if not raw_lang:                                                                            # 2. Se vuoto, controlla FreeCADGui.getLocale()
        try:                                                                                    # Tenta la lettura del locale GUI
            raw_lang = str(FreeCADGui.getLocale()).strip().lower()                              # Esempio: "english", "italian", "german", "spanish"
        except Exception:                                                                       # Fallback
            raw_lang = "it"                                                                     # Default Italiano

    if "ital" in raw_lang or raw_lang.startswith("it"):                                         # Se la lingua è Italiano
        return "it"                                                                             # Codice IT
    if "germ" in raw_lang or "deut" in raw_lang or raw_lang.startswith("de"):                   # Se la lingua è Tedesco
        return "de"                                                                             # Codice DE
    if "span" in raw_lang or "espa" in raw_lang or raw_lang.startswith("es"):                   # Se la lingua è Spagnolo
        return "es"                                                                             # Codice ES
    return "en"                                                                                 # Per English o qualsiasi altra lingua internazionale carica EN


def carica_modulo_traduzione():                                                                 # Carica il file traduzione_XX.py dalla cartella dedicata "translations/"
    codice = rileva_codice_lingua()                                                             # Ottiene "it", "en", "de" oppure "es"
    mappa_file = {                                                                              # Mappa codice lingua -> nome file modulo Python
        "it": "traduzione_IT",                                                                  # File dedicato Italiano
        "en": "traduzione_EN",                                                                  # File dedicato Inglese
        "de": "traduzione_DE",                                                                  # File dedicato Tedesco
        "es": "traduzione_ES"                                                                   # File dedicato Spagnolo
    }                                                                                           # Fine mappa
    nome_mod = mappa_file.get(codice, "traduzione_EN")                                          # Sceglie il nome del modulo di traduzione

    percorsi_ricerca = [                                                                        # Cerca prima nella cartella dedicata translations/, poi nella radice come fallback
        os.path.join(TRANS_DIR, f"{nome_mod}.py"),                                              # 1. Percorso principale: LatheCAM_2/translations/traduzione_XX.py
        os.path.join(MOD_DIR, f"{nome_mod}.py")                                                 # 2. Fallback se il file fosse ancora nella radice LatheCAM_2/
    ]                                                                                           # Fine lista percorsi

    for file_path in percorsi_ricerca:                                                          # Scorre i percorsi
        if os.path.exists(file_path):                                                           # Se il file .py esiste sul disco
            try:                                                                                # Carica direttamente il file dal suo percorso esatto
                spec = importlib.util.spec_from_file_location(nome_mod, file_path)              # Crea la specifica del modulo dal file
                if spec and spec.loader:                                                        # Se il loader è valido
                    mod_tr = importlib.util.module_from_spec(spec)                              # Crea il modulo
                    sys.modules[nome_mod] = mod_tr                                              # Registra in sys.modules
                    spec.loader.exec_module(mod_tr)                                             # Esegue e carica il dizionario aggiornato
                    return mod_tr                                                               # Restituisce il modulo di traduzione pronto
            except Exception:                                                                   # In caso di errore di sintassi nel file traduzione
                continue                                                                        # Prova il percorso successivo
    return None                                                                                 # Restituisce None se il file non esiste ancora


def tr_str(testo_it):                                                                           # Traduce una stringa richiamando il file nella cartella translations/
    if not testo_it or rileva_codice_lingua() == "it":                                          # Se siamo in Italiano o il testo è vuoto
        return testo_it                                                                         # Restituisce l'originale in Italiano
    mod_tr = carica_modulo_traduzione()                                                         # Ottiene il modulo della lingua corrente da translations/
    if mod_tr and hasattr(mod_tr, "traduci"):                                                   # Se il modulo possiede la funzione traduci()
        return mod_tr.traduci(testo_it)                                                         # Richiama la traduzione dal file dedicato!
    return testo_it                                                                             # Fallback testo originale


def _traduci_solo_etichette_dinamiche(root_widget):                                             # Traduce solo i QLabel (es. scritta gialla diametro effettivo) senza toccare gli input!
    if not root_widget or rileva_codice_lingua() == "it":                                       # Se siamo in Italiano non fa nulla
        return                                                                                  # Esce
    mod_tr = carica_modulo_traduzione()                                                         # Carica modulo traduzione
    if not mod_tr or not hasattr(mod_tr, "traduci"):                                            # Controllo sicurezza
        return                                                                                  # Esce
    for lbl in root_widget.findChildren(QtWidgets.QLabel):                                      # Scorre solo ed esclusivamente le etichette di testo QLabel
        try:                                                                                    # Protezione widget
            t_old = lbl.text()                                                                  # Legge testo attuale
            if t_old:                                                                           # Se non vuoto
                t_new = mod_tr.traduci(t_old)                                                   # Traduce
                if t_new != t_old: lbl.setText(t_new)                                           # Aggiorna scritta
        except Exception:                                                                       # Ignora errori
            continue                                                                            # Continua


def _traduci_albero_widget(root_widget):                                                        # Traduce tutti i widget visivi del pannello (senza disturbare gli spinbox di calcolo!)
    if not root_widget or rileva_codice_lingua() == "it":                                       # Se siamo in Italiano non tocca nulla
        return                                                                                  # Esce subito
    mod_tr = carica_modulo_traduzione()                                                         # Carica il modulo lingua dedicato da translations/
    if not mod_tr or not hasattr(mod_tr, "traduci"):                                            # Se non disponibile
        return                                                                                  # Esce

    for w in root_widget.findChildren(QtWidgets.QWidget):                                       # Scorre tutti i widget figli del pannello
        try:                                                                                    # Protezione per singolo widget
            if w.toolTip():                                                                     # Se il widget ha un suggerimento (ToolTip)
                tt_new = mod_tr.traduci(w.toolTip())                                            # Traduce il ToolTip
                if tt_new != w.toolTip(): w.setToolTip(tt_new)                                  # Aggiorna il ToolTip

            if isinstance(w, QtWidgets.QGroupBox):                                              # Titoli dei riquadri QGroupBox
                t_old = w.title()                                                               # Legge il titolo
                t_new = mod_tr.traduci(t_old)                                                   # Lo traduce tramite il file dedicato
                if t_new != t_old: w.setTitle(t_new)                                            # Aggiorna il titolo
            elif isinstance(w, QtWidgets.QTabWidget):                                           # Schede QTabWidget (es. 1. Stock, 2. Grip & Limits)
                for i in range(w.count()):                                                      # Scorre tutte le schede
                    t_old = w.tabText(i)                                                        # Legge il titolo della scheda
                    t_new = mod_tr.traduci(t_old)                                               # Lo traduce tramite il file dedicato
                    if t_new != t_old: w.setTabText(i, t_new)                                   # Imposta il nuovo titolo scheda
                if not getattr(w, "_lathe_tab_hooked", False):                                  # Aggancia il cambio scheda per tradurre anche le schede appena mostrate
                    w._lathe_tab_hooked = True                                                  # Segna come agganciato
                    w.currentChanged.connect(lambda idx, rw=root_widget: QtCore.QTimer.singleShot(20, lambda: _traduci_albero_widget(rw)))
            elif isinstance(w, (QtWidgets.QLabel, QtWidgets.QPushButton, QtWidgets.QCheckBox, QtWidgets.QRadioButton)):
                t_old = w.text()                                                                # Legge il testo dell'etichetta, bottone o checkbox
                if not t_old: continue                                                          # Salta se vuoto
                t_new = mod_tr.traduci(t_old)                                                   # Traduce usando il file dedicato in translations/
                if t_new != t_old: w.setText(t_new)                                             # Aggiorna il testo
            elif isinstance(w, QtWidgets.QLineEdit):                                            # Caselle di testo con placeholder
                ph_old = w.placeholderText()                                                    # Legge eventuale testo guida (placeholder)
                if ph_old:                                                                      # Se presente
                    ph_new = mod_tr.traduci(ph_old)                                             # Traduce il placeholder
                    if ph_new != ph_old: w.setPlaceholderText(ph_new)                           # Aggiorna il placeholder
            elif isinstance(w, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):                 # Quando cambi un numero, ritraduce eventuale scritta gialla dinamica!
                if not getattr(w, "_lathe_lbl_hooked", False):                                  # Aggancia una sola volta senza bloccare i segnali
                    w._lathe_lbl_hooked = True                                                  # Segna come agganciato
                    w.valueChanged.connect(lambda val, rw=root_widget: QtCore.QTimer.singleShot(15, lambda: _traduci_solo_etichette_dinamiche(rw)))
        except Exception:                                                                       # Ignora eventuali widget speciali
            continue                                                                            # Continua


def traduci_pannello_qt(panel_obj=None):                                                        # Traduce il pannello specificato all'apertura
    if rileva_codice_lingua() == "it":                                                          # Se FreeCAD è in Italiano non fa nulla
        return                                                                                  # Esce subito
    if panel_obj is not None and hasattr(panel_obj, "form") and panel_obj.form:                 # Se il pannello ha l'attributo .form
        _traduci_albero_widget(panel_obj.form)                                                  # Traduce direttamente il form del pannello
    try:                                                                                        # Traduce anche il dock laterale in cui FreeCAD inserisce il pannello
        mw = FreeCADGui.getMainWindow()                                                         # Finestra principale di FreeCAD
        if mw:                                                                                  # Se presente
            for dock in mw.findChildren(QtWidgets.QDockWidget):                                 # Scorre i QDockWidget laterali
                _traduci_albero_widget(dock)                                                    # Traduce le etichette del pannello aperto
    except Exception:                                                                           # Ignora errori GUI
        pass                                                                                    # Continua


def pianifica_traduzione_apertura():                                                            # Esegue la traduzione all'apertura della finestra (SENZA TIMER CONTINUI!)
    if rileva_codice_lingua() != "it":                                                          # Solo se la lingua non è Italiano
        QtCore.QTimer.singleShot(40, traduci_pannello_qt)                                       # Primo passaggio a 40ms dall'apertura
        QtCore.QTimer.singleShot(160, traduci_pannello_qt)                                      # Secondo passaggio a 160ms per eventuali etichette popolate subito dopo l'init


def apri_pannello_task(panel_instance):                                                         # Apre in modo sicuro un pannello Task in FreeCAD
    if FreeCADGui.Control.activeDialog():                                                       # Se c'era già un pannello aperto a destra
        FreeCADGui.Control.closeDialog()                                                        # Lo chiude prima di aprire il nuovo
    traduci_pannello_qt(panel_instance)                                                         # Traduce i widget del pannello prima di mostrarlo
    FreeCADGui.Control.showDialog(panel_instance)                                               # Mostra la finestra dei controlli a destra
    pianifica_traduzione_apertura()                                                             # Completa la traduzione delle etichette appena mostrate


def verifica_setup_attivo():                                                                    # Controlla che ci sia un documento attivo in FreeCAD
    if FreeCAD.ActiveDocument is None:                                                          # Se non c'è nessun documento aperto
        FreeCAD.newDocument("Tornio_CAM")                                                       # Crea automaticamente un documento nuovo
    return True                                                                                 # Documento pronto


def aggiungi_a_setup_se_gruppo(doc, child_obj):                                                 # Aggiunge child_obj a Setup_Macchina SOLO se Setup_Macchina è un Gruppo!
    if not doc or not child_obj:                                                                # Controllo sicurezza
        return                                                                                  # Esce
    setup_obj = doc.getObject("Setup_Macchina")                                                 # Cerca Setup_Macchina
    if setup_obj and hasattr(setup_obj, "addObject"):                                           # Verifica che possieda il metodo addObject
        try:                                                                                    # Tenta l'inserimento
            setup_obj.addObject(child_obj)                                                      # Inserisce nel gruppo
        except Exception:                                                                       # Se Setup_Macchina è un FeaturePython senza estensione gruppo
            pass                                                                                # Lascia l'oggetto nella radice del documento senza errori


def _carica_modulo_sicuro(lista_nomi_moduli):                                                   # Carica e ricarica il primo modulo esistente nella cartella del Workbench
    for m_name in lista_nomi_moduli:                                                            # Scorre i possibili nomi del file .py
        try:                                                                                    # Tenta di importare il modulo
            mod = importlib.import_module(m_name)                                               # Importa il modulo
            importlib.reload(mod)                                                               # Ricarica sempre l'ultima versione dal disco
            return mod                                                                          # Restituisce il modulo trovato
        except ImportError:                                                                     # Se quel nome file non esiste
            continue                                                                            # Prova il nome successivo nella lista
    raise ImportError(f"Nessuno dei moduli {lista_nomi_moduli} è stato trovato in {MOD_DIR}")   # Errore solo se non esiste nessuno dei nomi


def _individua_classi_modulo_cam(mod, nome_modulo):                                             # Trova automaticamente le classi (Proxy, ViewProvider, Panel) nel modulo!
    cls_proxy = None                                                                            # Classe principale dell'operazione/oggetto (FeaturePython Proxy)
    cls_vp = None                                                                               # Classe ViewProvider
    cls_panel = None                                                                            # Classe TaskPanel

    for cand_p in [nome_modulo, f"{nome_modulo}Op", f"{nome_modulo}Obj", f"{nome_modulo}Proxy", "LatheTurretObj", "TurretProxy", "LatheOp"]:
        if hasattr(mod, cand_p) and inspect.isclass(getattr(mod, cand_p)):                      # Se esiste ed è una classe
            cls_proxy = getattr(mod, cand_p)                                                    # Assegna Proxy
            break                                                                               # Trovata
    for cand_v in [f"ViewProvider{nome_modulo}", f"ViewProvider{nome_modulo}Op", f"{nome_modulo}ViewProvider", "ViewProviderTurret", "ViewProviderLatheOp"]:
        if hasattr(mod, cand_v) and inspect.isclass(getattr(mod, cand_v)):                      # Se esiste ed è una classe
            cls_vp = getattr(mod, cand_v)                                                       # Assegna ViewProvider
            break                                                                               # Trovata
    for cand_pnl in [f"{nome_modulo}Panel", f"{nome_modulo}TaskPanel", f"Task{nome_modulo}Panel", "TurretTaskPanel", "LatheTurretTaskPanel"]:
        if hasattr(mod, cand_pnl) and inspect.isclass(getattr(mod, cand_pnl)):                  # Se esiste ed è una classe
            cls_panel = getattr(mod, cand_pnl)                                                  # Assegna Panel
            break                                                                               # Trovata

    for name, obj in inspect.getmembers(mod, inspect.isclass):                                  # Ispeziona tutte le classi definite nel modulo se qualcuna ha nome diverso
        if obj.__module__ != mod.__name__:                                                      # Ignora classi importate dall'esterno
            continue                                                                            # Passa oltre
        if cls_panel is None and ("Panel" in name or hasattr(obj, "getStandardButtons") or hasattr(obj, "accept")):
            cls_panel = obj                                                                     # Riconosciuta come classe TaskPanel
        elif cls_vp is None and ("ViewProvider" in name or "VP" in name or hasattr(obj, "setEdit") or hasattr(obj, "claimChildren")):
            cls_vp = obj                                                                        # Riconosciuta come classe ViewProvider
        elif cls_proxy is None and (hasattr(obj, "execute") and "Panel" not in name and "View" not in name):
            cls_proxy = obj                                                                     # Riconosciuta come classe Proxy dell'oggetto/operazione

    return cls_proxy, cls_vp, cls_panel                                                         # Restituisce le 3 classi trovate


def _esegui_funzione_avvio_se_presente(mod, lista_nomi_funzioni):                               # Cerca ed esegue una funzione helper di avvio se presente nel modulo
    for fn in lista_nomi_funzioni:                                                              # Scorre i nomi candidati
        if hasattr(mod, fn) and inspect.isfunction(getattr(mod, fn)):                           # Se esiste ed è una funzione
            sig = inspect.signature(getattr(mod, fn))                                           # Ispeziona i parametri richiesti
            req = [p for p in sig.parameters.values() if p.default == inspect.Parameter.empty]  # Parametri obbligatori
            if len(req) == 0:                                                                   # Se può essere chiamata senza argomenti
                getattr(mod, fn)()                                                              # La esegue
                pianifica_traduzione_apertura()                                                 # Traduce il pannello appena aperto
                return True                                                                     # Avviato con successo
            elif len(req) == 1 and FreeCAD.ActiveDocument is not None:                          # Se richiede il documento attivo (doc)
                getattr(mod, fn)(FreeCAD.ActiveDocument)                                        # La esegue passando ActiveDocument
                pianifica_traduzione_apertura()                                                 # Traduce il pannello appena aperto
                return True                                                                     # Avviato con successo
    return False                                                                                # Nessuna funzione helper trovata


# ==============================================================================
# BARRA 1: SETUP MACCHINA, GREZZO, PEZZO FINITO, UTENSILI E TORRETTA
# ==============================================================================
class Lathe_Setup_Cmd:                                                                          # Comando 1: Setup Macchina (WCS)
    def GetResources(self):                                                                     # Risorse grafiche e testi del pulsante
        return {
            "Pixmap": get_icon_file("Lathe_Setup.svg"),                                         # Icona SVG garantita
            "MenuText": tr_str("1. Setup Macchina (WCS)"),                                      # Testo menu tradotto dal file in translations/
            "ToolTip": tr_str("Configura il sistema di coordinate macchina (WCS), l'origine Z0 e il punto di cambio utensile.")
        }

    def IsActive(self):                                                                         # Sempre cliccabile
        return True

    def Activated(self):                                                                        # Azione al click sul pulsante
        verifica_setup_attivo()                                                                 # Assicura documento attivo
        mod = _carica_modulo_sicuro(["LatheSetup"])                                             # Carica LatheSetup.py
        if _esegui_funzione_avvio_se_presente(mod, ["attiva_setup", "crea_o_modifica_setup", "open_setup", "apri_setup"]):
            return                                                                              # Avviato tramite funzione helper
        _, _, cls_panel = _individua_classi_modulo_cam(mod, "LatheSetup")                       # Individua il pannello
        obj = mod.get_or_create_setup() if hasattr(mod, "get_or_create_setup") else FreeCAD.ActiveDocument.getObject("Setup_Macchina")
        if cls_panel:                                                                           # Se ha trovato la classe Panel
            apri_pannello_task(cls_panel(obj) if obj else cls_panel())                          # Apre e traduce il pannello


class Lathe_Stock_Cmd:                                                                          # Comando 2: Grezzo & Autocentrante
    def GetResources(self):                                                                     # Risorse grafiche e testi del pulsante
        return {
            "Pixmap": get_icon_file("Lathe_Stock.svg"),                                         # Icona SVG
            "MenuText": tr_str("2. Grezzo & Autocentrante"),                                    # Testo menu
            "ToolTip": tr_str("Definisce le dimensioni del cilindro/tubo grezzo e le griffe del mandrino autocentrante.")
        }

    def IsActive(self):                                                                         # Attivo con documento aperto
        return FreeCAD.ActiveDocument is not None

    def Activated(self):                                                                        # Azione al click
        mod = _carica_modulo_sicuro(["LatheStock"])                                             # Carica LatheStock.py
        if _esegui_funzione_avvio_se_presente(mod, ["attiva_grezzo", "crea_o_modifica_grezzo", "open_stock", "apri_grezzo"]):
            return                                                                              # Avviato tramite funzione helper
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        obj = doc.getObject("Grezzo_Macchina")                                                  # Cerca oggetto grezzo
        if not obj and hasattr(mod, "create_stock_object"):                                     # Se non esiste lo crea
            obj = mod.create_stock_object(doc)                                                  # Crea oggetto
        _, _, cls_panel = _individua_classi_modulo_cam(mod, "LatheStock")                       # Individua il pannello
        if cls_panel:                                                                           # Se ha trovato la classe Panel
            apri_pannello_task(cls_panel(obj) if obj else cls_panel())                          # Apre e traduce il pannello


class Lathe_Part_Cmd:                                                                           # Comando 3: Pezzo Finito (Target 3D)
    def GetResources(self):                                                                     # Risorse grafiche e testi del pulsante
        return {
            "Pixmap": get_icon_file("Lathe_Part.svg"),                                          # Icona SVG
            "MenuText": tr_str("3. Pezzo Finito (Target 3D)"),                                  # Testo menu
            "ToolTip": tr_str("Seleziona e posiziona il solido 3D del pezzo finito dentro il grezzo.")
        }

    def IsActive(self):                                                                         # Attivo con documento aperto
        return FreeCAD.ActiveDocument is not None

    def Activated(self):                                                                        # Azione al click
        mod = _carica_modulo_sicuro(["LathePart"])                                              # Carica LathePart.py
        if _esegui_funzione_avvio_se_presente(mod, ["attiva_pezzo_finito", "crea_o_modifica_pezzo", "open_part", "apri_pezzo"]):
            return                                                                              # Avviato tramite funzione helper
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        obj = doc.getObject("Pezzo_Finito")                                                     # Cerca oggetto Pezzo_Finito
        if not obj and hasattr(mod, "create_part_wrapper"):                                     # Se non esiste lo crea
            obj = mod.create_part_wrapper(doc)                                                  # Crea wrapper
        _, _, cls_panel = _individua_classi_modulo_cam(mod, "LathePart")                        # Individua il pannello
        if cls_panel:                                                                           # Se ha trovato la classe Panel
            apri_pannello_task(cls_panel(obj) if obj else cls_panel())                          # Apre e traduce il pannello


class Lathe_ToolLibrary_Cmd:                                                                    # Comando 4: Magazzino Utensili (compatibile con LatheToolManager.py!)
    def GetResources(self):                                                                     # Risorse grafiche e testi del pulsante
        return {
            "Pixmap": get_icon_file("Lathe_Tools.svg"),                                         # Icona SVG
            "MenuText": tr_str("4. Magazzino Utensili"),                                        # Testo menu
            "ToolTip": tr_str("Gestisce il magazzino utensili di tornitura, gole, filettatura e foratura.")
        }

    def IsActive(self):                                                                         # Attivo con documento aperto
        return FreeCAD.ActiveDocument is not None

    def Activated(self):                                                                        # Azione al click
        mod = _carica_modulo_sicuro(["LatheToolManager", "LatheTools", "LatheToolLibrary", "LatheTool"])
        if _esegui_funzione_avvio_se_presente(mod, [                                            # Cerca qualsiasi funzione di avvio nel modulo utensili
            "apri_magazzino_utensili", "attiva_magazzino_utensili", "apri_libreria_utensili",
            "attiva_libreria_utensili", "open_tool_manager", "open_tool_library", "gestisci_utensili"
        ]):
            return                                                                              # Avviato con successo

        _, _, cls_panel = _individua_classi_modulo_cam(mod, mod.__name__)                       # Individua la classe TaskPanel in LatheToolManager
        if cls_panel:                                                                           # Se trovata
            sig_p = inspect.signature(cls_panel.__init__)                                       # Controlla gli argomenti del costruttore
            params_req = [p for name, p in sig_p.parameters.items() if name != "self" and p.default == inspect.Parameter.empty]
            if len(params_req) == 0:                                                            # Se non richiede argomenti (carica i default in autonomia)
                apri_pannello_task(cls_panel())                                                 # Apre il pannello
            else:                                                                               # Se richiede l'oggetto libreria o utensile
                doc = FreeCAD.ActiveDocument                                                    # Documento attivo
                lib = doc.getObject("Libreria_Utensili") or doc.getObject("Magazzino_Utensili") # Cerca il gruppo libreria
                if not lib:                                                                     # Se non esiste ancora
                    lib = doc.addObject("App::DocumentObjectGroup", "Libreria_Utensili")        # Crea gruppo
                    lib.Label = "Magazzino Utensili"                                            # Etichetta
                target_obj = lib.Group[0] if (hasattr(lib, "Group") and lib.Group) else lib     # Primo utensile o gruppo
                apri_pannello_task(cls_panel(target_obj))                                       # Apre il pannello


class Lathe_Turret_Cmd:                                                                         # Comando 5: Torretta Portautensili 3D
    def GetResources(self):                                                                     # Risorse grafiche e testi del pulsante
        return {
            "Pixmap": get_icon_file("Lathe_Turret.svg"),                                        # Icona SVG
            "MenuText": tr_str("5. Torretta Portautensili 3D"),                                 # Testo menu
            "ToolTip": tr_str("Configura il disco torretta 3D e monta gli utensili nelle stazioni.")
        }

    def IsActive(self):                                                                         # Attivo con documento aperto
        return FreeCAD.ActiveDocument is not None

    def Activated(self):                                                                        # Azione al click
        mod = _carica_modulo_sicuro(["LatheTurret", "LatheTurret3D", "LatheToolTurret"])        # Carica il modulo della Torretta 3D
        if _esegui_funzione_avvio_se_presente(mod, [                                            # Tutte le possibili funzioni di attivazione torretta
            "attiva_torretta", "apri_torretta", "crea_o_modifica_torretta", "crea_torretta",
            "gestisci_torretta", "open_turret", "create_or_edit_turret", "create_turret",
            "show_turret_panel", "avvia_torretta"
        ]):
            return                                                                              # Avviato con successo!

        cls_proxy, cls_vp, cls_panel = _individua_classi_modulo_cam(mod, "LatheTurret")         # Individua Proxy, ViewProvider e Panel reali!
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo

        obj = doc.getObject("Torretta_Macchina") or doc.getObject("Torretta_3D") or doc.getObject("Turret")
        if not obj:                                                                             # Se non esiste ancora
            for o in doc.Objects:                                                               # Cerca tra gli oggetti del documento
                if "Torretta" in o.Name or "Turret" in o.Name or "Torretta" in o.Label:         # Se trova un oggetto Torretta
                    obj = o                                                                     # Lo usa
                    break                                                                       # Trovato

        if cls_panel:                                                                           # Se abbiamo trovato la classe Panel
            sig_p = inspect.signature(cls_panel.__init__)                                       # Ispeziona il costruttore del Panel
            params_req = [p for name, p in sig_p.parameters.items() if name != "self" and p.default == inspect.Parameter.empty]
            if len(params_req) == 0:                                                            # Se il Panel si apre senza argomenti (cls_panel())
                apri_pannello_task(cls_panel())                                                 # Lo apre direttamente!
                return                                                                          # Termina

        if not obj:                                                                             # Se l'oggetto Torretta va creato
            obj = doc.addObject("Part::FeaturePython", "Torretta_Macchina")                     # Crea FeaturePython
            obj.Label = tr_str("5. Torretta Portautensili 3D").replace("5. ", "")               # Etichetta
            if cls_proxy:                                                                       # Usa la vera classe Proxy trovata nel modulo!
                cls_proxy(obj)                                                                  # Inizializza proprietà
            if FreeCAD.GuiUp and cls_vp:                                                        # Usa il vero ViewProvider trovato nel modulo!
                cls_vp(obj.ViewObject)                                                          # Inizializza ViewProvider
            aggiungi_a_setup_se_gruppo(doc, obj)                                                # Aggiunge a Setup se gruppo

        if cls_panel:                                                                           # Apre il pannello passando l'oggetto Torretta
            apri_pannello_task(cls_panel(obj))                                                  # Apre e traduce il pannello
        elif hasattr(obj, "ViewObject") and hasattr(obj.ViewObject, "Proxy") and hasattr(obj.ViewObject.Proxy, "setEdit"):
            obj.ViewObject.Proxy.setEdit(obj.ViewObject, 0)                                     # Fallback su setEdit
            pianifica_traduzione_apertura()                                                     # Traduce il pannello


# ==============================================================================
# BARRA 2: OPERAZIONI DI LAVORAZIONE CAM (TORNIO)
# ==============================================================================
def _avvia_operazione_cam(nome_modulo, base_name, label_it):                                    # Avvia o modifica un'operazione CAM rilevando automaticamente classi o funzioni!
    doc = FreeCAD.ActiveDocument                                                                # Documento attivo
    if not doc: return                                                                          # Controllo sicurezza
    mod = _carica_modulo_sicuro([nome_modulo])                                                  # Carica e ricarica il modulo dell'operazione

    if _esegui_funzione_avvio_se_presente(mod, [                                                # Controlla se il modulo ha una funzione di avvio propria
        "attiva_operazione", "crea_operazione", "avvia_operazione",
        "attiva_sgrossatura", "crea_sgrossatura", "attiva_finitura", "crea_finitura",
        "attiva_gola", "crea_gola", "attiva_filettatura", "crea_filettatura",
        "attiva_foratura", "crea_foratura", "attiva_troncatura", "crea_troncatura"
    ]):
        return                                                                                  # Termina

    cls_proxy, cls_vp, cls_panel = _individua_classi_modulo_cam(mod, nome_modulo)               # Individua automaticamente Proxy, ViewProvider e Panel

    ops_grp = doc.getObject("Operazioni_CAM")                                                   # Cerca il gruppo Operazioni_CAM
    if not ops_grp:                                                                             # Se non esiste ancora
        ops_grp = doc.addObject("App::DocumentObjectGroup", "Operazioni_CAM")                   # Lo crea nella radice del documento
        ops_grp.Label = "Operazioni CAM"                                                        # Etichetta gruppo
        aggiungi_a_setup_se_gruppo(doc, ops_grp)                                                # Inserisce in Setup_Macchina solo se è un gruppo

    sel = FreeCADGui.Selection.getSelection()                                                   # Legge la selezione corrente nell'albero
    for s_obj in sel:                                                                           # Scorre gli oggetti selezionati
        if s_obj.Name.startswith(base_name) and hasattr(s_obj, "PercorsoJSON"):                 # Se è già selezionata un'operazione dello stesso tipo
            if cls_panel:                                                                       # Se abbiamo la classe del pannello
                apri_pannello_task(cls_panel(s_obj))                                            # Apre il pannello sull'operazione esistente
            return                                                                              # Termina

    op_obj = doc.addObject("Part::FeaturePython", base_name)                                    # Crea il FeaturePython della nuova operazione
    op_obj.Label = f"{tr_str(label_it)} {len(ops_grp.Group) + 1}"                               # Assegna etichetta progressiva
    ops_grp.addObject(op_obj)                                                                   # Aggiunge al gruppo Operazioni_CAM

    if cls_proxy:                                                                               # Se ha trovato la classe Proxy
        cls_proxy(op_obj)                                                                       # Inizializza le proprietà parametriche
    if FreeCAD.GuiUp:                                                                           # Se l'interfaccia grafica è attiva
        if cls_vp:                                                                              # Se ha trovato la classe ViewProvider
            cls_vp(op_obj.ViewObject)                                                           # Collega il ViewProvider (doppio click)
        if cls_panel:                                                                           # Se ha trovato la classe Panel
            apri_pannello_task(cls_panel(op_obj))                                               # Apre subito il pannello e lo traduce all'apertura


class Lathe_Roughing_Cmd:                                                                       # Comando 6: Sgrossatura
    def GetResources(self):                                                                     # Risorse grafiche e testi del pulsante
        return {
            "Pixmap": get_icon_file("Lathe_Roughing.svg"),                                      # Icona SVG
            "MenuText": tr_str("1. Sgrossatura"),                                               # Testo menu
            "ToolTip": tr_str("Ciclo di sgrossatura longitudinale o frontale con riconoscimento automatico del profilo 3D.")
        }

    def IsActive(self):                                                                         # Attivo con documento aperto
        return FreeCAD.ActiveDocument is not None

    def Activated(self):                                                                        # Azione al click
        _avvia_operazione_cam("LatheRoughing", "Op_Sgrossatura", "Sgrossatura")                 # Avvia Sgrossatura


class Lathe_Finishing_Cmd:                                                                      # Comando 7: Finitura
    def GetResources(self):                                                                     # Risorse grafiche e testi del pulsante
        return {
            "Pixmap": get_icon_file("Lathe_Finishing.svg"),                                     # Icona SVG
            "MenuText": tr_str("2. Finitura"),                                                  # Testo menu
            "ToolTip": tr_str("Passata continua di finitura sul profilo reale del pezzo finito con compensazione raggio.")
        }

    def IsActive(self):                                                                         # Attivo con documento aperto
        return FreeCAD.ActiveDocument is not None

    def Activated(self):                                                                        # Azione al click
        _avvia_operazione_cam("LatheFinishing", "Op_Finitura", "Finitura")                      # Avvia Finitura


class Lathe_Grooving_Cmd:                                                                       # Comando 8: Gola
    def GetResources(self):                                                                     # Risorse grafiche e testi del pulsante
        return {
            "Pixmap": get_icon_file("Lathe_Grooving.svg"),                                      # Icona SVG
            "MenuText": tr_str("3. Gola"),                                                      # Testo menu
            "ToolTip": tr_str("Scavo di gole radiali esterne, interne o frontali con ciclo a tuffi multipli e pulizia fondo.")
        }

    def IsActive(self):                                                                         # Attivo con documento aperto
        return FreeCAD.ActiveDocument is not None

    def Activated(self):                                                                        # Azione al click
        _avvia_operazione_cam("LatheGrooving", "Op_Gola", "Gola")                               # Avvia Gola


class Lathe_Threading_Cmd:                                                                      # Comando 9: Filettatura
    def GetResources(self):                                                                     # Risorse grafiche e testi del pulsante
        return {
            "Pixmap": get_icon_file("Lathe_Threading.svg"),                                     # Icona SVG
            "MenuText": tr_str("4. Filettatura"),                                               # Testo menu
            "ToolTip": tr_str("Filettatura cilindrica o conica (Metrica ISO, Gas BSP, NPT, Trapezoidale) a sezione costante.")
        }

    def IsActive(self):                                                                         # Attivo con documento aperto
        return FreeCAD.ActiveDocument is not None

    def Activated(self):                                                                        # Azione al click
        _avvia_operazione_cam("LatheThreading", "Op_Filettatura", "Filettatura")                # Avvia Filettatura


class Lathe_Drilling_Cmd:                                                                       # Comando 10: Foratura Asse
    def GetResources(self):                                                                     # Risorse grafiche e testi del pulsante
        return {
            "Pixmap": get_icon_file("Lathe_Drilling.svg"),                                      # Icona SVG
            "MenuText": tr_str("5. Foratura Asse"),                                             # Testo menu
            "ToolTip": tr_str("Centrinatura, foratura profonda a scarico truciolo (G83/G73) e maschiatura sull'asse Z.")
        }

    def IsActive(self):                                                                         # Attivo con documento aperto
        return FreeCAD.ActiveDocument is not None

    def Activated(self):                                                                        # Azione al click
        _avvia_operazione_cam("LatheDrilling", "Op_Foratura", "Foratura Asse")                  # Avvia Foratura Asse


class Lathe_Parting_Cmd:                                                                        # Comando 11: Troncatura
    def GetResources(self):                                                                     # Risorse grafiche e testi del pulsante
        return {
            "Pixmap": get_icon_file("Lathe_Parting.svg"),                                       # Icona SVG
            "MenuText": tr_str("6. Troncatura"),                                                # Testo menu
            "ToolTip": tr_str("Taglio finale del pezzo finito dalla barra con smusso/raccordo automatico sullo spigolo.")
        }

    def IsActive(self):                                                                         # Attivo con documento aperto
        return FreeCAD.ActiveDocument is not None

    def Activated(self):                                                                        # Azione al click
        _avvia_operazione_cam("LatheParting", "Op_Troncatura", "Troncatura")                    # Avvia Troncatura


# ==============================================================================
# BARRA 3: VERIFICA 3D E GENERAZIONE G-CODE (POST-PROCESSOR)
# ==============================================================================
class Lathe_Simulation_Cmd:                                                                     # Comando 12: Simulazione Cinematica 3D
    def GetResources(self):                                                                     # Risorse grafiche e testi del pulsante
        return {
            "Pixmap": get_icon_file("Lathe_Simulation.svg"),                                    # Icona SVG
            "MenuText": tr_str("1. Simulazione 3D"),                                            # Testo menu
            "ToolTip": tr_str("Simula in 3D il movimento della torretta, l'asportazione sul grezzo e verifica le collisioni.")
        }

    def IsActive(self):                                                                         # Attivo con documento aperto
        return FreeCAD.ActiveDocument is not None

    def Activated(self):                                                                        # Azione al click
        mod = _carica_modulo_sicuro(["LatheSimulation"])                                        # Carica LatheSimulation.py
        panel = mod.LatheSimulationPanel()                                                      # Crea il pannello di simulazione
        apri_pannello_task(panel)                                                               # Mostra il pannello a destra


class Lathe_PostProcess_Cmd:                                                                    # Comando 13: Post-Processor G-Code
    def GetResources(self):                                                                     # Risorse grafiche e testi del pulsante
        return {
            "Pixmap": get_icon_file("Lathe_PostProcess.svg"),                                   # Icona SVG
            "MenuText": tr_str("2. Genera G-Code"),                                             # Testo menu
            "ToolTip": tr_str("Genera, visualizza ed esporta il programma G-Code per Fanuc/Haas, Siemens, Mach3 e LinuxCNC.")
        }

    def IsActive(self):                                                                         # Attivo con documento aperto
        return FreeCAD.ActiveDocument is not None

    def Activated(self):                                                                        # Azione al click
        mod = _carica_modulo_sicuro(["LathePostProcessor", "LathePost"])                        # Carica LathePostProcessor.py (o LathePost.py)
        panel = mod.LathePostProcessorPanel()                                                   # Crea l'istanza del pannello G-Code
        apri_pannello_task(panel)                                                               # Apre la finestra a destra


# REGISTRAZIONE DI TUTTI I COMANDI IN FREECAD (NOMI ESATTI DI INITGUI.PY + ALIAS CON _CMD)
COMANDI_DA_REGISTRARE = {                                                                       # Registra sia i nomi diretti di InitGui.py sia i nomi con _Cmd
    "Lathe_Setup": Lathe_Setup_Cmd,                                                             # Nome usato da InitGui.py per Setup Macchina
    "Lathe_Setup_Cmd": Lathe_Setup_Cmd,                                                         # Alias _Cmd
    "Lathe_Stock": Lathe_Stock_Cmd,                                                             # Nome usato da InitGui.py per Grezzo
    "Lathe_Stock_Cmd": Lathe_Stock_Cmd,                                                         # Alias _Cmd
    "Lathe_Part": Lathe_Part_Cmd,                                                               # Nome usato da InitGui.py per Pezzo Finito
    "Lathe_Part_Cmd": Lathe_Part_Cmd,                                                           # Alias _Cmd
    "Lathe_ToolManager": Lathe_ToolLibrary_Cmd,                                                 # Nome esatto richiesto da InitGui.py per Magazzino Utensili
    "Lathe_ToolLibrary": Lathe_ToolLibrary_Cmd,                                                 # Alias senza _Cmd
    "Lathe_ToolLibrary_Cmd": Lathe_ToolLibrary_Cmd,                                             # Alias con _Cmd
    "Lathe_Tools": Lathe_ToolLibrary_Cmd,                                                       # Alias breve
    "Lathe_Tools_Cmd": Lathe_ToolLibrary_Cmd,                                                   # Alias breve con _Cmd
    "Lathe_Turret": Lathe_Turret_Cmd,                                                           # Nome usato da InitGui.py per Torretta 3D
    "Lathe_Turret_Cmd": Lathe_Turret_Cmd,                                                       # Alias _Cmd
    "Lathe_Roughing": Lathe_Roughing_Cmd,                                                       # Nome usato da InitGui.py per Sgrossatura
    "Lathe_Roughing_Cmd": Lathe_Roughing_Cmd,                                                   # Alias _Cmd
    "Lathe_Finishing": Lathe_Finishing_Cmd,                                                     # Nome usato da InitGui.py per Finitura
    "Lathe_Finishing_Cmd": Lathe_Finishing_Cmd,                                                 # Alias _Cmd
    "Lathe_Grooving": Lathe_Grooving_Cmd,                                                       # Nome usato da InitGui.py per Gola
    "Lathe_Grooving_Cmd": Lathe_Grooving_Cmd,                                                   # Alias _Cmd
    "Lathe_Threading": Lathe_Threading_Cmd,                                                     # Nome usato da InitGui.py per Filettatura
    "Lathe_Threading_Cmd": Lathe_Threading_Cmd,                                                 # Alias _Cmd
    "Lathe_Drilling": Lathe_Drilling_Cmd,                                                       # Nome usato da InitGui.py per Foratura Asse
    "Lathe_Drilling_Cmd": Lathe_Drilling_Cmd,                                                   # Alias _Cmd
    "Lathe_Parting": Lathe_Parting_Cmd,                                                         # Nome usato da InitGui.py per Troncatura
    "Lathe_Parting_Cmd": Lathe_Parting_Cmd,                                                     # Alias _Cmd
    "Lathe_Simulation": Lathe_Simulation_Cmd,                                                   # Nome usato da InitGui.py per Simulazione 3D
    "Lathe_Simulation_Cmd": Lathe_Simulation_Cmd,                                               # Alias _Cmd
    "Lathe_PostProcess": Lathe_PostProcess_Cmd,                                                 # Nome usato da InitGui.py per Post-Processor
    "Lathe_PostProcess_Cmd": Lathe_PostProcess_Cmd,                                             # Alias _Cmd
    "Lathe_PostProcessor": Lathe_PostProcess_Cmd,                                               # Alias esteso
    "Lathe_PostProcessor_Cmd": Lathe_PostProcess_Cmd,                                           # Alias esteso con _Cmd
    "Lathe_Post": Lathe_PostProcess_Cmd,                                                        # Alias corto
    "Lathe_Post_Cmd": Lathe_PostProcess_Cmd                                                     # Alias corto con _Cmd
}                                                                                               # Fine dizionario comandi

for cmd_name, cmd_class in COMANDI_DA_REGISTRARE.items():                                       # Registra ogni comando nell'ambiente grafico di FreeCAD
    FreeCADGui.addCommand(cmd_name, cmd_class())                                                # Aggiunge l'istanza del comando