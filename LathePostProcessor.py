import os                                                                                       # Importa os per salvare e caricare i profili Post-Processor su disco
import FreeCAD                                                                                  # Importa il modulo base di FreeCAD
import FreeCADGui                                                                               # Importa il modulo interfaccia grafica di FreeCAD
import Part                                                                                     # Importa il modulo geometrico Part per la verifica del profilo 3D
import math                                                                                     # Importa le funzioni matematiche
import json                                                                                     # Importa il modulo JSON per decodificare i percorsi CAM e i profili e-CAM
import datetime                                                                                 # Importa datetime per l'intestazione del programma CNC
from PySide import QtCore, QtGui                                                                # Importa i moduli grafici PySide
try:                                                                                            # Tenta di importare QtWidgets per compatibilità Qt5/Qt6
    from PySide import QtWidgets                                                                # Assegna QtWidgets
except ImportError:                                                                             # Fallback per versioni meno recenti
    QtWidgets = QtGui                                                                           # Usa QtGui come alias di QtWidgets


POST_PROFILES_FILE = os.path.join(os.path.dirname(__file__), "post_profiles_ecam.json")         # File JSON in cui salvare i profili personalizzati stile e-CAM

DIALETTI_CNC = [                                                                                # Elenco dei 4 controlli numerici base supportati dal Post-Processor
    "Mach3 / Mach4 Turn (Tornio)",                                                              # Mach3 / Mach4 Turn (senza G7/G8, G76 nativo Mach3 a 1 riga)
    "Fanuc / Haas (ISO Standard)",                                                              # Controllo standard industriale Fanuc / Haas
    "Siemens Sinumerik (840D / 828D)",                                                          # Controllo Siemens Sinumerik
    "LinuxCNC (Tornio)"                                                                         # Controllo LinuxCNC per tornio (con G7/G8 e G33 K)
]                                                                                               # Fine lista dialetti CNC

MODALITA_ASSE_X = [                                                                             # Modalità di programmazione della quota X sul tornio
    "Programmazione al Diametro (X = 2*R)",                                                     # Standard industriale: X esprime il diametro
    "Programmazione al Raggio (X = R)"                                                          # X esprime direttamente il raggio
]                                                                                               # Fine lista modalità X

MODALITA_AVANZAMENTO = [                                                                        # Modalità di avanzamento del carro (Feed Rate)
    "Millimetri al Giro (mm/giro - G95)",                                                       # Avanzamento classico sincronizzato coi giri mandrino
    "Millimetri al Secondo (mm/s -> G94)",                                                      # Velocità carro in mm/sec (convertita automaticamente in mm/min con G94)
    "Millimetri al Minuto (mm/min - G94)"                                                       # Velocità carro diretta in mm/min con G94
]                                                                                               # Fine lista modalità avanzamento

STILI_COMMENTO = [                                                                              # Stili di formattazione dei commenti nel G-Code
    "Parentesi Tonde ISO: (Commento)",                                                          # Standard Fanuc / Mach3 / LinuxCNC
    "Punto e Virgola: ; Commento"                                                               # Standard Siemens / Sinumerik / Mach4
]                                                                                               # Fine lista stili commento

DEFAULT_ECAM_TEMPLATES = {                                                                      # Template multi-riga predefiniti per ciascun controllo in stile e-CAM
    "Mach3 / Mach4 Turn (Tornio)": {                                                            # Configurazione predefinita Mach3 Turn
        "decimals": 3, "n_start": 10, "n_step": 10, "comm_style": 0,                            # 3 decimali, N10 passo 10, commenti tra parentesi
        "cool_on": "M08", "cool_off": "M09",                                                    # Codici refrigerante
        "header": "(PROGRAMMA MACH3 TURN: {PROG} - {DOC} - {DATE})\nG21 G18 G40 G80 G90 {FEED_G}\nG54",
        "tool_change": "M06 T{TOOL}{OFFSET} (UTENSILE: {TOOL_DESC})",                           # Cambio utensile Mach3 a 4 cifre
        "footer": "G00 X{HOME_X} Z{HOME_Z}\nM05\nM30"                                           # Chiusura programma Mach3
    },
    "Fanuc / Haas (ISO Standard)": {                                                            # Configurazione predefinita Fanuc / Haas
        "decimals": 3, "n_start": 10, "n_step": 10, "comm_style": 0,                            # 3 decimali, N10 passo 10, commenti tra parentesi
        "cool_on": "M08", "cool_off": "M09",                                                    # Codici refrigerante
        "header": "%\n{PROG} ({DOC} - {DATE})\nG21 G18 G40 G80 {FEED_G}\nG54\nG50 S{MAX_RPM}",  # Intestazione ISO con G50
        "tool_change": "G00 X{HOME_X} Z{HOME_Z}\nT{TOOL}{OFFSET} ({TOOL_DESC})",                # Cambio utensile Fanuc
        "footer": "G00 X{HOME_X} Z{HOME_Z}\nM05\nM30\n%"                                        # Chiusura programma Fanuc con %
    },
    "Siemens Sinumerik (840D / 828D)": {                                                        # Configurazione predefinita Siemens
        "decimals": 3, "n_start": 10, "n_step": 10, "comm_style": 1,                            # 3 decimali, commenti con punto e virgola
        "cool_on": "M08", "cool_off": "M09",                                                    # Codici refrigerante
        "header": "; MPF {PROG} - {DOC} ({DATE})\nG710 G18 G90 G40 {FEED_G}\nG54\nLIMS={MAX_RPM}",
        "tool_change": "G00 X{HOME_X} Z{HOME_Z}\nT{STATION} D1 ; {TOOL_DESC}",                  # Cambio utensile Siemens
        "footer": "G00 X{HOME_X} Z{HOME_Z}\nM05\nM30"                                           # Chiusura programma Siemens
    },
    "LinuxCNC (Tornio)": {                                                                      # Configurazione predefinita LinuxCNC
        "decimals": 3, "n_start": 10, "n_step": 10, "comm_style": 0,                            # 3 decimali, commenti tra parentesi
        "cool_on": "M08", "cool_off": "M09",                                                    # Codici refrigerante
        "header": "(PROGRAMMA LINUXCNC: {PROG} - {DOC} - {DATE})\nG21 G18 {X_MODE_G} G90 G40 {FEED_G}\nG54",
        "tool_change": "G00 X{HOME_X} Z{HOME_Z}\nT{STATION} M06 G43 ({TOOL_DESC})",             # Cambio utensile LinuxCNC
        "footer": "G00 X{HOME_X} Z{HOME_Z}\nM05\nM30"                                           # Chiusura programma LinuxCNC
    }
}                                                                                               # Fine template predefiniti e-CAM


def carica_profili_ecam():                                                                      # Carica i profili e-CAM dal file JSON (o restituisce i default)
    profili = dict(DEFAULT_ECAM_TEMPLATES)                                                      # Parte dai 4 profili predefiniti
    if os.path.exists(POST_PROFILES_FILE):                                                      # Se esiste il file JSON salvato dall'utente
        try:                                                                                    # Tenta la lettura
            with open(POST_PROFILES_FILE, "r", encoding="utf-8") as f:                          # Apre il file JSON
                dati_utente = json.load(f)                                                      # Decodifica il dizionario
            if isinstance(dati_utente, dict):                                                   # Se è un dizionario valido
                profili.update(dati_utente)                                                     # Aggiorna/aggiunge i profili salvati dall'utente
        except Exception:                                                                       # In caso di file corrotto
            pass                                                                                # Usa i predefiniti senza errori
    return profili                                                                              # Restituisce il dizionario dei profili


def salva_profili_ecam(profili_dict):                                                           # Salva i profili e-CAM personalizzati nel file JSON
    try:                                                                                        # Tenta il salvataggio su disco
        with open(POST_PROFILES_FILE, "w", encoding="utf-8") as f:                              # Apre in scrittura UTF-8
            json.dump(profili_dict, f, indent=2, ensure_ascii=False)                            # Scrive il JSON formattato
        return True                                                                             # Salvataggio riuscito
    except Exception:                                                                           # In caso di errore permessi
        return False                                                                            # Fallito


def get_setup_post_info(doc=None):                                                              # Legge i parametri macchina dal Setup_Macchina e dal Grezzo_Macchina
    if doc is None:                                                                             # Se non specificato usa il documento attivo
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
    info = {                                                                                    # Dizionario valori predefiniti
        "wcs_name": "G54",                                                                      # Origine pezzo standard
        "home_x": 60.0,                                                                         # Raggio X di cambio utensile
        "home_z": 60.0,                                                                         # Quota Z di cambio utensile
        "max_rpm": 2500,                                                                        # Limite massimo giri mandrino (G50 / LIMS)
        "stock_r": 25.0,                                                                        # Raggio esterno del grezzo
        "stock_z_front": 1.0                                                                    # Sovrametallo frontale Z+
    }                                                                                           # Fine dizionario base
    if doc and doc.getObject("Setup_Macchina"):                                                 # Se nel progetto è presente Setup_Macchina
        s = doc.getObject("Setup_Macchina")                                                     # Ottiene l'oggetto Setup
        info["home_x"] = float(getattr(s, "CambioUtensileX", 60.0))                             # Legge X cambio utensile
        info["home_z"] = float(getattr(s, "CambioUtensileZ", 60.0))                             # Legge Z cambio utensile
        info["max_rpm"] = int(getattr(s, "GiriMaxMandrino", 2500))                              # Legge eventuale limite giri
    if doc and doc.getObject("Grezzo_Macchina"):                                                # Legge anche il raggio del grezzo per l'approccio sicuro ravvicinato in Mach3
        g = doc.getObject("Grezzo_Macchina")                                                    # Ottiene l'oggetto Grezzo
        info["stock_r"] = max(float(getattr(g, "DiametroEsterno", 50.0)) / 2.0, 1.0)            # Raggio esterno grezzo
        info["stock_z_front"] = float(getattr(g, "SovrametalloFrontale", 1.0))                  # Quota Z frontale grezzo
    return info                                                                                 # Restituisce il dizionario


def trova_utensile_operazione(doc, nome_utensile):                                              # Cerca l'oggetto utensile nel documento dal Name o dalla Label
    if not doc or not nome_utensile:                                                            # Controllo sicurezza
        return None                                                                             # Non trovato
    obj = doc.getObject(nome_utensile)                                                          # Cerca per Name interno
    if obj:                                                                                     # Se esiste
        return obj                                                                              # Lo restituisce
    lib = doc.getObject("Libreria_Utensili")                                                    # Cerca dentro il Magazzino Utensili
    if lib and hasattr(lib, "Group"):                                                           # Se il gruppo esiste
        for t in lib.Group:                                                                     # Scorre tutti gli utensili
            if t.Label == nome_utensile or getattr(t, "ToolName", "") == nome_utensile:         # Confronta Label e ToolName
                return t                                                                        # Restituisce l'utensile
    return None                                                                                 # Non trovato


def estrai_raggio_profilo_3d_a_z(part_shape, wcs, z_wcs, r_default=0.0):                        # Interroga il solido 3D del Pezzo_Finito alla quota Z per evitare collisioni col cono
    if not part_shape or part_shape.isNull():                                                   # Se non c'è la shape del pezzo finito
        return r_default                                                                        # Restituisce il raggio minimo predefinito
    z_world = wcs.z + z_wcs                                                                     # Quota Z assoluta nel mondo 3D
    try:                                                                                        # Seziona con un raggio radiale il solido a quota z_world
        linea = Part.makeLine(                                                                  # Raggio radiale lungo l'asse X da R=0 a R=500
            FreeCAD.Vector(wcs.x, wcs.y, z_world),
            FreeCAD.Vector(wcs.x + 500.0, wcs.y, z_world)
        )
        inter = part_shape.section(linea)                                                       # Calcola l'intersezione tra il pezzo finito e la retta radiale
        if inter and inter.Vertexes:                                                            # Se tocca il pezzo finito
            return max(v.Point.x - wcs.x for v in inter.Vertexes)                               # Restituisce il raggio esterno massimo del pezzo a quella quota Z
    except Exception:                                                                           # Ignora errori geometrici su bordi tangenti
        pass                                                                                    # Continua
    return r_default                                                                            # Nessuna intersezione trovata


def ricalcola_e_verifica_percorso_operazione(doc, op_obj):                                      # Forza il ricalcolo dell'operazione e garantisce il rispetto del profilo 3D del Pezzo_Finito
    if hasattr(op_obj, "Proxy") and hasattr(op_obj.Proxy, "execute"):                           # Se l'operazione ha il metodo execute
        try:                                                                                    # Forza l'aggiornamento del percorso e della linea verde 3D
            op_obj.Proxy.execute(op_obj)                                                        # Esegue il ricalcolo nativo del modulo operazione
        except Exception:                                                                       # In caso di eccezione
            pass                                                                                # Continua con i dati esistenti

    try:                                                                                        # Legge i movimenti generati
        moves = json.loads(getattr(op_obj, "PercorsoJSON", "[]") or "[]")                       # Decodifica JSON
    except Exception:                                                                           # Errore JSON
        moves = []                                                                              # Lista vuota
    if not moves or not doc:                                                                    # Se non ci sono movimenti
        return moves                                                                            # Restituisce così com'è

    part_obj = doc.getObject("Pezzo_Finito")                                                    # Cerca il Pezzo_Finito nel documento
    if not part_obj or not hasattr(part_obj, "Shape") or part_obj.Shape.isNull():               # Se non c'è un Pezzo_Finito valido
        return moves                                                                            # Restituisce i movimenti standard

    if "Sgrossatura" not in op_obj.Name and "Rough" not in op_obj.Name:                         # Il controllo di arresto sui coni si applica alla Sgrossatura
        return moves                                                                            # Per le altre operazioni restituisce i movimenti nativi

    ciclo = str(getattr(op_obj, "TipoCiclo", "Esterna"))                                        # Legge il tipo di ciclo di sgrossatura
    if "Intern" in ciclo or "Frontale" in ciclo or "Sfacciatura" in ciclo:                      # Solo per sgrossatura longitudinale esterna
        return moves                                                                            # Restituisce movimenti nativi

    wcs = FreeCAD.Vector(0, 0, 0)                                                               # Origine WCS predefinita
    if doc.getObject("Setup_Macchina") and hasattr(doc.getObject("Setup_Macchina"), "Origine"): # Se esiste Setup_Macchina
        wcs = FreeCAD.Vector(doc.getObject("Setup_Macchina").Origine)                           # Legge il vettore Origine WCS

    sovra_x = float(getattr(op_obj, "SovrametalloX", getattr(op_obj, "SovrametalloDiametro", 0.5))) # Sovrametallo radiale X
    sovra_z = float(getattr(op_obj, "SovrametalloZ", 0.2))                                      # Sovrametallo assiale Z
    p_shape = part_obj.Shape                                                                    # Shape 3D del pezzo finito

    ha_corretto = False                                                                         # Indica se almeno una passata rettangolare è stata fermata sul cono
    nuovi_moves = [moves[0]]                                                                    # Mantiene il primo punto di approccio
    curr_x = float(moves[0].get("x", 25.0))                                                     # X corrente
    curr_z = float(moves[0].get("z", 2.0))                                                      # Z corrente

    for mv in moves[1:]:                                                                        # Scorre tutti i movimenti successivi
        cmd = str(mv.get("cmd", "G1"))                                                          # Comando ("G0" o "G1")
        nx = float(mv.get("x", curr_x))                                                         # X target
        nz = float(mv.get("z", curr_z))                                                         # Z target
        f_val = float(mv.get("f", 0.25))                                                        # Avanzamento F

        if cmd == "G1" and (nz < curr_z - 0.5) and abs(nx - curr_x) < 0.05:                     # Passata cilindrica orizzontale da destra a sinistra
            n_check = max(int(abs(curr_z - nz) / 0.25), 10)                                     # Campiona ogni 0.25 mm lungo Z
            z_stop = nz                                                                         # Quota Z in cui la passata deve fermarsi
            for k in range(1, n_check + 1):                                                     # Cammina da curr_z verso nz
                zk = curr_z + (nz - curr_z) * (float(k) / float(n_check))                       # Quota Z di test
                r_pezzo = estrai_raggio_profilo_3d_a_z(p_shape, wcs, zk - sovra_z, 0.0)         # Raggio del pezzo finito a quella quota Z
                if r_pezzo + sovra_x > nx + 0.02:                                               # La passata ha incontrato la rampa conica o uno spallamento!
                    z_stop = curr_z + (nz - curr_z) * (float(k - 1) / float(n_check))           # Si ferma subito prima di intaccare il cono!
                    ha_corretto = True                                                          # Segnala che la passata rettangolare è stata corretta
                    break                                                                       # Interrompe la scansione
            nz = z_stop                                                                         # Aggiorna la quota Z di arresto della passata

        nuovi_moves.append({"cmd": cmd, "x": round(nx, 4), "z": round(nz, 4), "f": f_val})      # Salva il movimento verificato
        curr_x, curr_z = nx, nz                                                                 # Aggiorna posizione corrente

    if ha_corretto:                                                                             # Se aveva trovato passate rettangolari che entravano nel pezzo
        try:                                                                                    # Aggiorna sia PercorsoJSON sia la linea verde a schermo!
            op_obj.PercorsoJSON = json.dumps(nuovi_moves)                                       # Salva i movimenti corretti nell'oggetto
            edges = []                                                                          # Lista segmenti 3D per ridisegnare la linea verde
            for k in range(len(nuovi_moves) - 1):                                               # Costruisce i segmenti 3D
                p1 = FreeCAD.Vector(wcs.x + nuovi_moves[k]["x"], wcs.y, wcs.z + nuovi_moves[k]["z"])
                p2 = FreeCAD.Vector(wcs.x + nuovi_moves[k + 1]["x"], wcs.y, wcs.z + nuovi_moves[k + 1]["z"])
                if (p2 - p1).Length > 1e-3:                                                     # Evita segmenti nulli
                    edges.append(Part.makeLine(p1, p2))                                         # Aggiunge linea
            if edges:                                                                           # Se ci sono linee valide
                op_obj.Shape = Part.makeCompound(edges)                                         # Aggiorna la linea verde a schermo in FreeCAD!
        except Exception:                                                                       # Ignora errori di sola lettura
            pass                                                                                # Continua
    return nuovi_moves                                                                          # Restituisce la lista movimenti fedele ai coni


def formatta_commento(testo, dialetto, comm_style_override=None):                               # Formatta un commento secondo la sintassi del controllo CNC o del profilo e-CAM
    pulito = str(testo).replace("(", "[").replace(")", "]").strip()                             # Rimuove parentesi tonde annidate
    if comm_style_override == 1 or (comm_style_override is None and "Siemens" in dialetto):     # Sintassi punto e virgola
        return f"; {pulito}"                                                                    # Restituisce ; Commento
    return f"({pulito})"                                                                        # Restituisce (Commento)


def espandi_template_ecam(testo_template, variabili_dict):                                      # Sostituisce i segnaposto {VAR} nel template e-CAM con i valori reali
    risultato = str(testo_template)                                                             # Copia il testo del template
    for k, v in variabili_dict.items():                                                         # Scorre tutte le variabili disponibili
        risultato = risultato.replace("{" + k + "}", str(v))                                    # Sostituisce {CHIAVE} con il valore
    return risultato                                                                            # Restituisce il blocco espanso


def genera_codice_nc(                                                                           # Motore principale di generazione G-Code (con supporto nativo e-CAM!)
    doc, lista_operazioni, dialetto,                                                            # Documento, operazioni e controllo CNC
    modo_diametro=True, usa_numeri_riga=True,                                                   # Opzioni diametro/raggio e numeri blocco N
    usa_commenti=True, usa_refrigerante=True,                                                   # Opzioni commenti e refrigerante M08
    usa_g76_filetto=False, inverti_x_mach3=False,                                               # Opzione G76 e inversione segno X per torretta Mach3
    feed_mode_idx=0, custom_feed_val=20.0,                                                      # 0=mm/giro (G95), 1=mm/sec (->G94), 2=mm/min (G94)
    prog_number="O1001", max_rpm=2500,                                                          # Nome programma e limite giri G50
    ecam_cfg=None                                                                               # Dizionario opzionale con i parametri e template personalizzati e-CAM
):                                                                                              # Inizio generazione G-Code
    lines = []                                                                                  # Lista delle righe finali del programma G-Code
    cfg = ecam_cfg if isinstance(ecam_cfg, dict) else {}                                        # Configurazione personalizzata e-CAM
    usa_tpl_ecam = bool(cfg.get("use_custom_templates", False))                                 # True se l'utente ha attivato i template personalizzati e-CAM
    n_dec = int(cfg.get("decimals", 3))                                                         # Numero di cifre decimali per X e Z (default 3)
    n_curr = int(cfg.get("n_start", 10))                                                        # Numero blocco iniziale (default N10)
    n_step = int(cfg.get("n_step", 10))                                                         # Passo numerazione blocchi (default 10)
    comm_style = cfg.get("comm_style", None)                                                    # Stile commento (0 = parentesi, 1 = punto e virgola)
    cod_cool_on = str(cfg.get("cool_on", "M08")).strip() or "M08"                               # Codice accensione refrigerante personalizzabile
    cod_cool_off = str(cfg.get("cool_off", "M09")).strip() or "M09"                             # Codice spegnimento refrigerante personalizzabile

    segno_x = -1.0 if inverti_x_mach3 else 1.0                                                  # Permette di invertire X se Mach3 mostra l'utensile dal lato opposto
    fatt_x = (2.0 if modo_diametro else 1.0) * segno_x                                          # Moltiplicatore per l'asse X (Diametro o Raggio * segno)

    setup_info = get_setup_post_info(doc)                                                       # Legge quote di cambio utensile e dimensioni grezzo
    is_mach3 = ("Mach3" in dialetto)                                                            # True se stiamo generando per Mach3 / Mach4 Turn
    is_fanuc = ("Fanuc" in dialetto)                                                            # True se Fanuc / Haas

    usa_feed_tempo = (feed_mode_idx in [1, 2])                                                  # True se l'utente ha scelto mm/sec o mm/min
    g_feed_time = "G98" if is_fanuc else "G94"                                                  # Codice G per avanzamento in mm/min
    g_feed_rev = "G99" if is_fanuc else "G95"                                                   # Codice G per avanzamento in mm/giro
    g_feed_attivo = g_feed_time if usa_feed_tempo else g_feed_rev                               # Codice G di avanzamento da inserire nell'intestazione
    feed_carro_mm_min = (float(custom_feed_val) * 60.0) if feed_mode_idx == 1 else float(custom_feed_val) # Se mm/s moltiplica per 60 per dare mm/min a G94!

    if is_mach3:                                                                                # Quota di sicurezza/cambio ottimizzata per la vista grafica di Mach3 Turn
        hx_val = (setup_info["stock_r"] + 5.0) * fatt_x                                         # 5 mm sopra il raggio del grezzo
        hz_val = setup_info["stock_z_front"] + 3.0                                              # 3 mm davanti alla faccia del grezzo (non +60 mm!)
    else:                                                                                       # Per Fanuc, Siemens e LinuxCNC usa le quote di cambio utensile macchina
        hx_val = setup_info["home_x"] * fatt_x                                                  # Quota X di cambio utensile
        hz_val = setup_info["home_z"]                                                           # Quota Z di cambio utensile

    def fmt_num(val):                                                                           # Formatta una coordinata X/Z col numero di decimali scelto in e-CAM
        return f"{float(val):.{n_dec}f}"                                                        # Restituisce la stringa formattata

    def add_line(codice, commento=""):                                                          # Funzione helper per aggiungere una riga formattata
        nonlocal n_curr                                                                         # Usa il contatore n_curr esterno
        cod_str = str(codice).strip()                                                           # Pulisce il comando G-Code
        comm_str = formatta_commento(commento, dialetto, comm_style) if (commento and usa_commenti) else ""
        if not cod_str and not comm_str:                                                        # Se sia codice che commento sono vuoti
            return                                                                              # Ignora riga vuota
        if not cod_str and comm_str:                                                            # Se è una riga di solo commento
            lines.append(comm_str)                                                              # Inserisce il commento senza numero N
            return                                                                              # Esce
        if cod_str in ["%"]:                                                                    # Carattere speciale % di inizio/fine trasmissione
            lines.append(cod_str)                                                               # Non numera la riga %
            return                                                                              # Esce
        prefisso_n = f"N{n_curr} " if usa_numeri_riga else ""                                   # Prefisso N10 se richiesto
        n_curr += n_step                                                                        # Incrementa contatore N
        if comm_str:                                                                            # Se c'è sia codice che commento a destra
            lines.append(f"{prefisso_n}{cod_str} {comm_str}")                                   # Unisce codice e commento
        else:                                                                                   # Solo codice
            lines.append(f"{prefisso_n}{cod_str}")                                              # Aggiunge riga

    # 1. INTESTAZIONE DEL PROGRAMMA (HEADER)
    data_oggi = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")                              # Data e ora di generazione
    nome_doc = doc.Label if doc else "Progetto_Tornio"                                          # Nome del documento FreeCAD
    descr_feed = f"CARRO {custom_feed_val:.1f} MM/S (F{feed_carro_mm_min:.0f} MM/MIN)" if feed_mode_idx == 1 else (f"CARRO {feed_carro_mm_min:.0f} MM/MIN" if feed_mode_idx == 2 else "AVANZ. MM/GIRO")

    vars_base = {                                                                               # Dizionario variabili globali per i template e-CAM
        "PROG": prog_number.strip(),                                                            # Nome/Numero programma
        "DOC": nome_doc,                                                                        # Nome progetto FreeCAD
        "DATE": data_oggi,                                                                      # Data e ora
        "FEED_G": g_feed_attivo,                                                                # G94/G95/G98/G99
        "X_MODE_G": "G7" if modo_diametro else "G8",                                            # G7/G8 (per LinuxCNC)
        "MAX_RPM": int(max_rpm),                                                                # Limite giri mandrino
        "HOME_X": fmt_num(hx_val),                                                              # X punto cambio utensile
        "HOME_Z": fmt_num(hz_val),                                                              # Z punto cambio utensile
        "COOLANT_ON": cod_cool_on,                                                              # Codice M accensione acqua
        "COOLANT_OFF": cod_cool_off                                                             # Codice M spegnimento acqua
    }                                                                                           # Fine dizionario variabili base

    if usa_tpl_ecam and str(cfg.get("header", "")).strip():                                     # Se è attivo il template Header personalizzato in stile e-CAM
        testo_hdr = espandi_template_ecam(cfg["header"], vars_base)                             # Espande le variabili {PROG}, {FEED_G}, ecc.
        for r_h in testo_hdr.splitlines():                                                      # Scorre ogni riga del template Header
            r_clean = r_h.strip()                                                               # Pulisce spazi
            if r_clean.startswith("(") or r_clean.startswith(";"):                              # Se è una riga di puro commento
                if usa_commenti: lines.append(r_clean)                                          # La aggiunge se i commenti sono abilitati
            elif r_clean:                                                                       # Se è una riga di comando G-Code
                add_line(r_clean)                                                               # La aggiunge (con eventuale numero N)
    elif is_mach3:                                                                              # Intestazione standard Mach3 / Mach4 Turn (SENZA G7/G8!)
        add_line("", f"PROGRAMMA MACH3 TURN: {prog_number} - {nome_doc} ({data_oggi})")         # Commento intestazione
        add_line("", f"MODALITA ASSE X: {'DIAMETRO' if modo_diametro else 'RAGGIO'} - {descr_feed}")
        add_line(f"G21 G18 G40 G80 G90 {g_feed_attivo}", f"METRICO, PIANO XZ, COMP. OFF, ASSOLUTO, {descr_feed}")
        add_line("G54", "ORIGINE PEZZO WCS")                                                    # Origine pezzo
    elif is_fanuc:                                                                              # Intestazione standard Fanuc / Haas
        lines.append("%")                                                                       # Carattere di inizio trasmissione ISO
        prog_clean = prog_number.strip().upper()                                                # Pulisce il numero programma
        if not prog_clean.startswith("O"): prog_clean = "O" + prog_clean                        # Garantisce il prefisso O
        add_line(prog_clean, f"PROGETTO: {nome_doc} - DATA: {data_oggi}")                       # Riga numero programma
        add_line(f"G21 G18 G40 G80 {g_feed_attivo}", f"METRICO, PIANO XZ, COMP. OFF, {descr_feed}")
        add_line("G54", "ORIGINE PEZZO WCS")                                                    # Richiamo origine
        add_line(f"G50 S{int(max_rpm)}", "LIMITE MASSIMO GIRI MANDRINO")                        # Limitatore giri G50
    elif "Siemens" in dialetto:                                                                 # Intestazione Siemens Sinumerik
        add_line("", f"MPF {prog_number} - PROGETTO: {nome_doc} ({data_oggi})")                 # Commento intestazione MPF
        add_line(f"G710 G18 G90 G40 {g_feed_attivo}", f"METRICO, PIANO XZ, ASSOLUTO, {descr_feed}")
        add_line("G54", "ORIGINE PEZZO WCS")                                                    # Origine pezzo
        add_line(f"LIMS={int(max_rpm)}", "LIMITE MASSIMO GIRI MANDRINO")                        # Limitatore giri Siemens
    else:                                                                                       # Intestazione LinuxCNC puro (con G7/G8 nativo)
        add_line("", f"PROGRAMMA LINUXCNC: {prog_number} - {nome_doc} ({data_oggi})")           # Commento iniziale
        modo_g7_g8 = "G7" if modo_diametro else "G8"                                            # G7 = Modo Diametro, G8 = Modo Raggio solo per LinuxCNC
        add_line(f"G21 G18 {modo_g7_g8} G90 G40 {g_feed_attivo}", f"METRICO, PIANO XZ, {'DIAMETRO' if modo_diametro else 'RAGGIO'}, {descr_feed}")
        add_line("G54", "ORIGINE PEZZO WCS")                                                    # Origine pezzo

    last_stazione = None                                                                        # Traccia l'ultimo utensile montato
    utensili_usati = set()                                                                      # Insieme degli utensili impiegati

    # 2. SCANSIONE DELLE OPERAZIONI CAM (CON RICALCOLO E VERIFICA PROFILO CONICO 3D!)
    for op_obj in lista_operazioni:                                                             # Cicla su ciascuna operazione richiesta
        if not hasattr(op_obj, "PercorsoJSON"):                                                 # Salta oggetti non CAM
            continue                                                                            # Passa oltre

        moves = ricalcola_e_verifica_percorso_operazione(doc, op_obj)                           # Assicura che il percorso rispetti i coni e i gradini del Pezzo_Finito!
        if not moves:                                                                           # Se l'operazione è vuota
            continue                                                                            # Passa oltre

        lines.append("")                                                                        # Riga vuota di separazione tra operazioni
        add_line("", "==========================================")                              # Separatore visivo
        add_line("", f"OPERAZIONE: {op_obj.Label.upper()}")                                     # Nome dell'operazione

        t_name = str(getattr(op_obj, "UtensileAssegnato", ""))                                  # Nome utensile assegnato
        t_obj = trova_utensile_operazione(doc, t_name)                                          # Oggetto utensile FreeCAD
        num_st = int(getattr(t_obj, "NumeroStazione", 1)) if t_obj else 1                       # Numero stazione (1..12)
        sigla_st = f"T{num_st:02d}"                                                             # Sigla stazione T01..T12
        descr_t = t_obj.Label if t_obj else "Utensile Standard"                                 # Descrizione utensile
        utensili_usati.add(f"{sigla_st} ({descr_t})")                                           # Registra nelle statistiche

        # 2A. CAMBIO UTENSILE
        if last_stazione != num_st:                                                             # Se l'utensile è diverso da quello già attivo
            vars_tool = dict(vars_base)                                                         # Copia le variabili base
            vars_tool.update({                                                                  # Aggiunge le variabili specifiche dell'utensile per e-CAM
                "TOOL": f"{num_st:02d}",                                                        # Numero utensile a 2 cifre (es. 01)
                "OFFSET": f"{num_st:02d}",                                                      # Numero correttore a 2 cifre (es. 01)
                "STATION": str(num_st),                                                         # Numero stazione semplice (es. 1)
                "TOOL_DESC": descr_t                                                            # Nome descrittivo utensile
            })
            if usa_tpl_ecam and str(cfg.get("tool_change", "")).strip():                        # Se è attivo il template Cambio Utensile personalizzato e-CAM
                if not is_mach3 or last_stazione is not None:                                   # Disimpegno sicuro
                    add_line(f"G00 X{fmt_num(hx_val)} Z{fmt_num(hz_val)}", "DISIMPEGNO CAMBIO UTENSILE")
                testo_tc = espandi_template_ecam(cfg["tool_change"], vars_tool)                 # Espande il template cambio utensile
                for r_tc in testo_tc.splitlines():                                              # Scorre le righe del template cambio utensile
                    if r_tc.strip(): add_line(r_tc.strip())                                     # Aggiunge la riga
            else:                                                                               # Cambio utensile predefinito del dialetto
                if not is_mach3 or last_stazione is not None:                                   # In Mach3 evita un G00 lontano prima del primo utensile per non spostare lo Stock grigio!
                    add_line(f"G00 X{fmt_num(hx_val)} Z{fmt_num(hz_val)}", "DISIMPEGNO SICURO CAMBIO UTENSILE")
                if is_mach3:                                                                    # Cambio utensile Mach3 Turn: M06 T0101
                    add_line(f"M06 T{num_st:02d}{num_st:02d}", f"UTENSILE: {descr_t}")          # Sintassi standard Mach3 Turn
                elif is_fanuc:                                                                  # Cambio utensile Fanuc a 4 cifre (es. T0101)
                    add_line(f"T{num_st:02d}{num_st:02d}", f"UTENSILE: {descr_t}")              # Richiamo stazione + correttore
                elif "Siemens" in dialetto:                                                     # Cambio utensile Siemens (T1 D1)
                    add_line(f"T{num_st} D1", f"UTENSILE: {descr_t}")                           # Richiamo utensile e tagliente D1
                else:                                                                           # Cambio utensile LinuxCNC (T1 M06 G43)
                    add_line(f"T{num_st} M06 G43", f"UTENSILE: {descr_t}")                      # Cambio utensile con compensazione lunghezza
            last_stazione = num_st                                                              # Aggiorna stazione attiva

        # 2B. AVVIO MANDRINO E REFRIGERANTE
        verso_rot = "M04" if (t_obj and "Orario (M04)" in str(getattr(t_obj, "VersoRotazione", ""))) else "M03"
        op_type_name = op_obj.Name                                                              # Tipo interno dell'operazione
        ciclo_str = str(getattr(op_obj, "TipoCiclo", ""))                                       # TipoCiclo dell'operazione
        is_threading_op = hasattr(op_obj, "GiriMandrinoRPM") or ("Filettatura" in op_type_name) # True se l'operazione corrente è una Filettatura

        if is_threading_op:                                                                     # Filettatura: usa sempre giri fissi G97 e avanzamento sincronizzato G95/G99!
            rpm_val = int(getattr(op_obj, "GiriMandrinoRPM", 800))                              # Legge gli RPM di filettatura
            if usa_feed_tempo:                                                                  # Se il programma era in G94 (mm/s), per filettare commuta temporaneamente in G95
                add_line(g_feed_rev, "SINCRONIZZAZIONE PASSO/GIRO PER FILETTATURA")             # Imposta G95/G99 per la filettatura
            add_line(f"G97 S{rpm_val} {verso_rot}", "GIRI FISSI PER FILETTATURA SINCRONIZZATA") # Imposta G97
        elif "Foratura" in op_type_name or "Centrino" in ciclo_str or "Maschiatura" in ciclo_str: # Foratura / Maschiatura sull'asse X=0: usa G97!
            vc_or_rpm = float(getattr(op_obj, "VelocitaTaglio", 80.0))                          # Legge Vc o RPM
            d_punta = max(float(getattr(op_obj, "DiametroPunta", 10.0)), 1.0)                   # Diametro punta
            rpm_calc = int(vc_or_rpm) if vc_or_rpm > 250 else int((vc_or_rpm * 1000.0) / (math.pi * d_punta))
            rpm_calc = max(100, min(rpm_calc, int(max_rpm)))                                    # Limita nel range valido
            add_line(f"G97 S{rpm_calc} {verso_rot}", "GIRI FISSI PER LAVORAZIONE IN ASSE")      # Imposta G97
        else:                                                                                   # Tornitura / Finitura / Gola / Troncatura
            vc_val = int(getattr(op_obj, "VelocitaTaglio", 150.0))                              # Legge Velocità di taglio Vc o RPM
            if is_mach3:                                                                        # Su Mach3 Turn usa G97 con gli RPM
                rpm_m3 = vc_val if vc_val > 300 else min(int((vc_val * 1000.0) / (math.pi * 40.0)), int(max_rpm))
                add_line(f"G97 S{rpm_m3} {verso_rot}", "AVVIO MANDRINO MACH3")                  # Avvio mandrino G97 S... M03
            elif vc_val > 400:                                                                  # Se l'utente aveva inserito direttamente gli RPM (>400)
                add_line(f"G97 S{vc_val} {verso_rot}", "AVVIO MANDRINO GIRI FISSI")             # Usa G97
            else:                                                                               # Velocità di taglio costante m/min
                add_line(f"G96 S{vc_val} {verso_rot}", f"VELOCITA TAGLIO COSTANTE {vc_val} M/MIN")

        if usa_refrigerante:                                                                    # Se è richiesto il refrigerante
            add_line(cod_cool_on, "ACCENSIONE REFRIGERANTE")                                    # Attiva acqua (M08 o codice personalizzato e-CAM)

        # 2C. GESTIONE CICLO FISSO G76 PER FILETTATURA (COERENTE CON MACH3 TURN E CON FANUC!)
        meta_thr = moves[0].get("thread_meta") if moves else None                               # Controlla se il primo movimento contiene i metadati di filettatura
        if meta_thr and usa_g76_filetto and (is_mach3 or is_fanuc):                             # Se è richiesto il ciclo G76 per Mach3 Turn oppure per Fanuc
            r_nom = float(meta_thr["r_nom"])                                                    # Raggio nominale partenza filetto
            h_tot = float(meta_thr["h_tot"])                                                    # Altezza radiale filetto (mm)
            pitch = float(meta_thr["pitch"])                                                    # Passo P (mm)
            z_ini = float(meta_thr["z_start"])                                                  # Quota Z di inizio
            z_fin = float(meta_thr["z_end"])                                                    # Quota Z di fine
            is_od = bool(meta_thr["is_od"])                                                     # Esterna OD o Interna ID
            ang_p = int(float(meta_thr["angle"]))                                               # Angolo profilo (es. 60)
            n_spr = int(meta_thr["n_spring"])                                                   # Passate a vuoto di pulizia
            n_cut = max(int(meta_thr["n_cuts"]), 1)                                             # Numero passate taglio

            r_sic_thr = (r_nom + 2.5) if is_od else max(r_nom - 2.0, 1.0)                       # Raggio di sicurezza e inizio ciclo G76
            r_fondo = (r_nom - h_tot) if is_od else (r_nom + h_tot)                             # Raggio finale di fondo filetto
            prima_passata_mm = max(h_tot / math.sqrt(n_cut), 0.05)                              # Profondità prima passata in mm
            infeed_ang = round(ang_p / 2.0 - 0.5, 1)                                            # Angolo d'ingresso sul fianco (es. 29.5° per filetto 60°)

            add_line(f"G00 X{fmt_num(r_sic_thr * fatt_x)} Z{fmt_num(z_ini)}", "APPROCCIO INIZIO FILETTO")

            if is_mach3:                                                                        # SINTASSI NATIVA MACH3 TURN G76 (A 1 SOLA RIGA CON PARAMETRI IN MM!)
                add_line(                                                                       # Mach3 G76: X=Fondo, Z=Fine, Q=SpringPasses, P=Passo, H=PrimaPassata(mm), I=InfeedAngle, R=X_Start, K=Z_Start, C=Clearance
                    f"G76 X{fmt_num(r_fondo * fatt_x)} Z{fmt_num(z_fin)} Q{n_spr} P{pitch:.3f} H{prima_passata_mm:.3f} I{infeed_ang} R{fmt_num(r_nom * fatt_x)} K{fmt_num(z_ini)} C{abs(r_sic_thr - r_nom):.3f}",
                    "CICLO FILETTATURA MACH3 TURN G76"
                )
            else:                                                                               # SINTASSI FANUC G76 (A 2 RIGHE CON P E Q IN MICRON)
                p_microns = int(round(h_tot * 1000.0))                                          # Altezza filetto P in micron
                q_prima_microns = int(round(prima_passata_mm * 1000.0))                         # Prima passata Q in micron
                add_line(f"G76 P{n_spr:02d}10{ang_p:02d} Q50 R0.05", "PARAMETRI CICLO G76 FANUC")
                add_line(f"G76 X{fmt_num(r_fondo * fatt_x)} Z{fmt_num(z_fin)} P{p_microns} Q{q_prima_microns} F{pitch:.3f}", "ESECUZIONE FILETTO G76 FANUC")

            add_line(f"G00 X{fmt_num(hx_val)} Z{fmt_num(hz_val)}", "DISIMPEGNO FINE FILETTATURA")
            if usa_feed_tempo:                                                                  # Ripristina G94/G98 dopo la filettatura se era attivo l'avanzamento a tempo
                add_line(g_feed_time, f"RIPRISTINO AVANZAMENTO LINEARE {descr_feed}")
            continue                                                                            # Passa direttamente all'operazione successiva!

        # 2D. SCRITTURA DEI MOVIMENTI PUNTO-PUNTO (G00 / G01 / G32 / G33)
        last_cmd = None                                                                         # Ultimo comando emesso
        last_x = None                                                                           # Ultima X emessa
        last_z = None                                                                           # Ultima Z emessa
        last_f = None                                                                           # Ultimo avanzamento F emesso

        for mv in moves:                                                                        # Scorre tutti i punti verificati
            cmd_raw = str(mv.get("cmd", "G1"))                                                  # Legge "G0", "G1" o "G32"
            x_val = float(mv.get("x", 0.0)) * fatt_x                                            # Converte X in Diametro o Raggio (con eventuale segno invertito)
            z_val = float(mv.get("z", 0.0))                                                     # Quota Z
            f_op_val = float(mv.get("f", 0.0))                                                  # Avanzamento originario dell'operazione

            if cmd_raw == "G0":                                                                 # Movimento Rapido
                g_str = "G00"                                                                   # Codice G00
            elif cmd_raw == "G32":                                                              # Passo di filettatura sincronizzato
                g_str = "G33" if ("Siemens" in dialetto or "LinuxCNC" in dialetto) else "G32"   # G32 su Mach3 e Fanuc, G33 su Siemens e LinuxCNC
            else:                                                                               # Movimento lineare di taglio
                g_str = "G01"                                                                   # Codice G01

            if g_str in ["G32", "G33"]:                                                         # Filettatura punto-punto: mantiene sempre il passo reale del filetto!
                f_eff = f_op_val                                                                # Passo filetto in mm
            elif usa_feed_tempo:                                                                # Avanzamento carro in mm/s o mm/min (G94)
                f_eff = feed_carro_mm_min                                                       # Valore convertito in mm/min (es. 20 mm/s -> F1200.0)
            else:                                                                               # Avanzamento classico in mm/giro (G95)
                f_eff = f_op_val                                                                # Valore in mm/giro dell'operazione

            parti = [g_str]                                                                     # Costruisce i token della riga CNC
            forza_xz = (last_cmd is None)                                                       # True sul primo movimento dell'operazione
            if forza_xz or abs(x_val - (last_x or 0.0)) > 1e-4 or g_str != last_cmd:            # Scrive X se cambia o su cambio modalità G
                parti.append(f"X{fmt_num(x_val)}")                                              # Aggiunge coordinata X formattata
                last_x = x_val                                                                  # Aggiorna ultima X
            if forza_xz or abs(z_val - (last_z or 0.0)) > 1e-4 or g_str != last_cmd:            # Scrive Z se cambia o su cambio modalità G
                parti.append(f"Z{fmt_num(z_val)}")                                              # Aggiunge coordinata Z formattata
                last_z = z_val                                                                  # Aggiorna ultima Z

            if g_str in ["G01", "G32", "G33"] and f_eff > 1e-5:                                 # Se è un movimento di lavoro con avanzamento valido
                if last_f is None or abs(f_eff - last_f) > 1e-5 or g_str in ["G32", "G33"]:     # Scrive F quando cambia (o sempre in filettatura)
                    if g_str == "G33" and "LinuxCNC" in dialetto:                               # Solo in LinuxCNC G33 il passo si indica con K
                        parti.append(f"K{f_eff:.3f}")                                           # Passo K per G33 LinuxCNC
                    elif usa_feed_tempo and g_str == "G01":                                     # In modalità G94 (mm/min) formatta F con 1 decimale (es. F1200.0)
                        parti.append(f"F{f_eff:.1f}")                                           # Avanzamento F in mm/min
                    else:                                                                       # In modalità G95 (mm/giro) o G32 formatta con 3 decimali
                        parti.append(f"F{f_eff:.3f}")                                           # Avanzamento F in mm/giro
                    last_f = f_eff                                                              # Aggiorna ultimo F

            if len(parti) > 1:                                                                  # Se c'è almeno una coordinata X o Z da muovere
                add_line(" ".join(parti))                                                       # Aggiunge la riga al programma G-Code
                last_cmd = g_str                                                                # Memorizza ultimo comando G

        if is_threading_op and usa_feed_tempo:                                                  # Se aveva commutato in G95 per la filettatura, torna a G94 per le lavorazioni successive
            add_line(g_feed_time, f"RIPRISTINO AVANZAMENTO LINEARE {descr_feed}")

    # 3. CHIUSURA DEL PROGRAMMA (FOOTER)
    lines.append("")                                                                            # Riga vuota prima della chiusura
    add_line("", "==========================================")                                  # Separatore finale
    if usa_refrigerante:                                                                        # Spegnimento refrigerante
        add_line(cod_cool_off, "SPEGNIMENTO REFRIGERANTE")                                      # M09 (o codice personalizzato e-CAM)

    if usa_tpl_ecam and str(cfg.get("footer", "")).strip():                                     # Se è attivo il template Footer personalizzato in stile e-CAM
        testo_ftr = espandi_template_ecam(cfg["footer"], vars_base)                             # Espande {HOME_X}, {HOME_Z}, ecc.
        for r_f in testo_ftr.splitlines():                                                      # Scorre le righe del Footer
            if r_f.strip(): add_line(r_f.strip())                                               # Aggiunge ogni riga del Footer
    else:                                                                                       # Chiusura standard
        add_line(f"G00 X{fmt_num(hx_val)} Z{fmt_num(hz_val)}", "DISIMPEGNO FINALE SICURO")      # Ritiro finale
        add_line("M05", "ARRESTO MANDRINO")                                                     # Ferma il mandrino
        if is_fanuc:                                                                            # Fine programma Fanuc
            add_line("M30", "FINE PROGRAMMA E RIAVVOLGIMENTO")                                  # M30
            lines.append("%")                                                                   # Carattere di fine file ISO
        else:                                                                                   # Fine programma Mach3 / Siemens / LinuxCNC
            add_line("M30", "FINE PROGRAMMA")                                                   # M30

    if doc:                                                                                     # Aggiorna la vista 3D se il percorso verde è stato riallineato ai coni
        FreeCADGui.updateGui()                                                                  # Refresh grafico

    return "\n".join(lines), len(lines), len(utensili_usati)                                    # Restituisce il testo completo, il numero righe e il numero utensili


class LathePostProcessorPanel:                                                                  # Pannello Task con Configuratore Post-Processor in stile e-CAM
    def __init__(self):                                                                         # Costruttore del pannello Post-Processor
        self.doc = FreeCAD.ActiveDocument                                                       # Documento attivo
        self.is_updating = True                                                                 # Semaforo durante la costruzione della UI
        self.profili_ecam = carica_profili_ecam()                                               # Carica i profili e-CAM dal file JSON

        self.form = QtWidgets.QWidget()                                                         # Contenitore principale della finestra a destra
        self.form.setMinimumWidth(280)                                                          # Larghezza minima compatta
        self.layout = QtWidgets.QVBoxLayout(self.form)                                          # Layout verticale principale
        self.layout.setContentsMargins(4, 4, 4, 4)                                              # Margini ridotti

        # ORGANIZZAZIONE A SCHEDE (TAB) IN STILE E-CAM:
        self.tabs = QtWidgets.QTabWidget()                                                      # Contenitore a 2 schede: 1. Controllo & Programma, 2. Configuratore e-CAM
        self.tab_main = QtWidgets.QWidget()                                                     # Scheda 1: Impostazioni rapide e opzioni G-Code
        self.tab_ecam = QtWidgets.QWidget()                                                     # Scheda 2: Personalizzazione blocchi template e codici (Stile e-CAM)
        self.lyt_tab_main = QtWidgets.QVBoxLayout(self.tab_main)                                # Layout Scheda 1
        self.lyt_tab_ecam = QtWidgets.QVBoxLayout(self.tab_ecam)                                # Layout Scheda 2
        self.lyt_tab_main.setContentsMargins(4, 4, 4, 4)                                        # Margini interni Scheda 1
        self.lyt_tab_ecam.setContentsMargins(4, 4, 4, 4)                                        # Margini interni Scheda 2

        # ======================================================================
        # SCHEDA 1: CONTROLLO CNC, VELOCITÀ CARRO E OPZIONI RAPIDE
        # ======================================================================
        self.grp_cfg = QtWidgets.QGroupBox("Configurazione Controllo CNC e Operazioni")         # Gruppo 1: Scelta CNC, Operazioni e Velocità Carro
        self.lyt_cfg = QtWidgets.QFormLayout(self.grp_cfg)                                      # Form layout

        self.op_combo = QtWidgets.QComboBox()                                                   # Tendina con "Tutte le Operazioni" o singola operazione
        self.op_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.op_combo.setMinimumContentsLength(10)
        self.popola_combo_operazioni()                                                          # Carica le operazioni da Operazioni_CAM

        self.dialect_combo = QtWidgets.QComboBox()                                              # Tendina scelta controllo CNC (Mach3, Fanuc, Siemens, LinuxCNC + profili utente)
        for k_prof in self.profili_ecam.keys():                                                 # Popola con tutti i profili disponibili
            self.dialect_combo.addItem(k_prof)                                                  # Aggiunge profilo al combo
        self.dialect_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.dialect_combo.setMinimumContentsLength(10)

        self.xmode_combo = QtWidgets.QComboBox()                                                # Scelta Programmazione al Diametro o al Raggio
        self.xmode_combo.addItems(MODALITA_ASSE_X)                                              # Popola opzioni X
        self.xmode_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.xmode_combo.setMinimumContentsLength(10)

        self.feed_mode_combo = QtWidgets.QComboBox()                                            # Scelta Avanzamento: mm/giro (G95), mm/s (->G94) o mm/min (G94)
        self.feed_mode_combo.addItems(MODALITA_AVANZAMENTO)                                     # Popola le 3 modalità di avanzamento carro
        self.feed_mode_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.feed_mode_combo.setMinimumContentsLength(10)

        self.custom_feed_spin = QtWidgets.QDoubleSpinBox()                                      # Casella numerica per la velocità del carro (es. 20.0 mm/s)
        self.custom_feed_spin.setRange(0.1, 10000.0)                                            # Range da 0.1 a 10000
        self.custom_feed_spin.setDecimals(2)                                                    # 2 cifre decimali
        self.custom_feed_spin.setValue(20.0)                                                    # Predefinito: 20.0 mm/s
        self.custom_feed_spin.setSuffix(" mm/s")                                                # Suffisso unità di misura
        self.custom_feed_spin.setEnabled(False)                                                 # Disabilitato finché si è in mm/giro

        self.prog_num_edit = QtWidgets.QLineEdit("O1001")                                       # Numero/Nome programma CNC
        self.max_rpm_spin = QtWidgets.QSpinBox()                                                # Limite massimo giri mandrino G50 / LIMS
        self.max_rpm_spin.setRange(100, 12000); self.max_rpm_spin.setValue(2500); self.max_rpm_spin.setSingleStep(100)

        self.lyt_cfg.addRow("Esporta:", self.op_combo)                                          # Riga scelta operazioni
        self.lyt_cfg.addRow("Controllo CNC:", self.dialect_combo)                               # Riga dialetto CNC
        self.lyt_cfg.addRow("Quote Asse X:", self.xmode_combo)                                  # Riga Diametro / Raggio
        self.lyt_cfg.addRow("Modo Avanz.:", self.feed_mode_combo)                               # Riga modalità avanzamento (mm/giro, mm/s, mm/min)
        self.lyt_cfg.addRow("Velocità Carro:", self.custom_feed_spin)                           # Riga valore velocità carro (es. 20 mm/s)
        self.lyt_cfg.addRow("Nome Prog.:", self.prog_num_edit)                                  # Riga Nome Programma
        self.lyt_cfg.addRow("Giri Max (G50):", self.max_rpm_spin)                               # Riga Limite Giri
        self.lyt_tab_main.addWidget(self.grp_cfg)                                               # Aggiunge Gruppo 1 alla Scheda 1

        self.grp_opt = QtWidgets.QGroupBox("Opzioni di Formattazione G-Code")                   # Gruppo 2: Opzioni di formattazione
        self.lyt_opt = QtWidgets.QVBoxLayout(self.grp_opt)                                      # Layout verticale opzioni

        self.chk_n_lines = QtWidgets.QCheckBox("Inserisci numeri di riga (N10, N20...)")        # Numerazione blocchi N
        self.chk_n_lines.setChecked(True)                                                       # Attivo di default
        self.chk_comments = QtWidgets.QCheckBox("Includi commenti descrittivi operazioni")      # Commenti nel G-Code
        self.chk_comments.setChecked(True)                                                      # Attivo di default
        self.chk_coolant = QtWidgets.QCheckBox("Comanda Refrigerante automatico (M08 / M09)")   # Gestione acqua M08/M09
        self.chk_coolant.setChecked(True)                                                       # Attivo di default
        self.chk_g76 = QtWidgets.QCheckBox("Usa ciclo compatto G76 per Filettatura (Mach3/Fanuc)") # Ciclo G76 nativo Mach3 (1 riga) o Fanuc (2 righe)
        self.chk_g76.setChecked(False)                                                          # Disattivato di default (usa G32 espanso)
        self.chk_inv_x = QtWidgets.QCheckBox("Inverti segno X (X-) per vista Torretta Mach3")   # Permette di specchiare X sopra/sotto in Mach3 Turn
        self.chk_inv_x.setChecked(False)                                                        # Disattivato di default (X+)

        self.lyt_opt.addWidget(self.chk_n_lines)                                                # Aggiunge spunta numeri N
        self.lyt_opt.addWidget(self.chk_comments)                                               # Aggiunge spunta commenti
        self.lyt_opt.addWidget(self.chk_coolant)                                                # Aggiunge spunta refrigerante
        self.lyt_opt.addWidget(self.chk_g76)                                                    # Aggiunge spunta G76
        self.lyt_opt.addWidget(self.chk_inv_x)                                                  # Aggiunge spunta inversione X Mach3
        self.lyt_tab_main.addWidget(self.grp_opt)                                               # Aggiunge Gruppo 2 alla Scheda 1

        # ======================================================================
        # SCHEDA 2: CONFIGURATORE POST-PROCESSOR IN STILE E-CAM
        # ======================================================================
        self.grp_prof = QtWidgets.QGroupBox("Gestione Profili Macchina e-CAM")                  # Salvataggio/Ripristino profili macchina personalizzati
        self.lyt_prof = QtWidgets.QVBoxLayout(self.grp_prof)                                    # Layout verticale
        self.lyt_prof_row = QtWidgets.QHBoxLayout()                                             # Riga nome profilo + bottoni
        self.edit_prof_name = QtWidgets.QLineEdit("Mach3 / Mach4 Turn (Tornio)")                # Nome del profilo da salvare/sovrascrivere
        self.btn_save_prof = QtWidgets.QPushButton("💾 Salva Profilo")                          # Salva nel file JSON
        self.btn_reset_prof = QtWidgets.QPushButton("↺ Ripristina Default")                     # Ripristina i template predefiniti
        self.btn_save_prof.clicked.connect(self.salva_profilo_corrente_ecam)                    # Collega salvataggio profilo
        self.btn_reset_prof.clicked.connect(self.ripristina_profilo_default_ecam)               # Collega ripristino default
        self.lyt_prof_row.addWidget(self.btn_save_prof)                                         # Aggiunge bottone salva
        self.lyt_prof_row.addWidget(self.btn_reset_prof)                                        # Aggiunge bottone reset
        self.lyt_prof.addWidget(self.edit_prof_name)                                            # Aggiunge casella nome profilo
        self.lyt_prof.addLayout(self.lyt_prof_row)                                              # Aggiunge bottoni
        self.lyt_tab_ecam.addWidget(self.grp_prof)                                              # Aggiunge al Tab e-CAM

        self.grp_fmt = QtWidgets.QGroupBox("Parametri Formattazione e Codici M")                # Formattazione numerica e codici M
        self.lyt_fmt = QtWidgets.QFormLayout(self.grp_fmt)                                      # Form layout

        self.spin_decimals = QtWidgets.QSpinBox()                                               # Numero cifre decimali coordinate X e Z
        self.spin_decimals.setRange(1, 5); self.spin_decimals.setValue(3)                       # Default: 3 decimali (es. X25.000)

        self.lyt_n_cfg = QtWidgets.QHBoxLayout()                                                # Riga per N iniziale e Passo N
        self.spin_n_start = QtWidgets.QSpinBox(); self.spin_n_start.setRange(1, 1000); self.spin_n_start.setValue(10)
        self.spin_n_step = QtWidgets.QSpinBox(); self.spin_n_step.setRange(1, 100); self.spin_n_step.setValue(10)
        self.lyt_n_cfg.addWidget(self.spin_n_start); self.lyt_n_cfg.addWidget(self.spin_n_step)

        self.combo_comm_style = QtWidgets.QComboBox()                                           # Scelta stile commenti: ( ... ) oppure ; ...
        self.combo_comm_style.addItems(STILI_COMMENTO)                                          # Popola stili

        self.lyt_cool_codes = QtWidgets.QHBoxLayout()                                           # Codici M per Refrigerante ON e OFF
        self.edit_cool_on = QtWidgets.QLineEdit("M08")                                          # Default M08
        self.edit_cool_off = QtWidgets.QLineEdit("M09")                                         # Default M09
        self.lyt_cool_codes.addWidget(self.edit_cool_on); self.lyt_cool_codes.addWidget(self.edit_cool_off)

        self.lyt_fmt.addRow("Decimali X / Z:", self.spin_decimals)                              # Riga decimali
        self.lyt_fmt.addRow("Inizio / Passo N:", self.lyt_n_cfg)                                # Riga numerazione N
        self.lyt_fmt.addRow("Stile Commenti:", self.combo_comm_style)                           # Riga stile commenti
        self.lyt_fmt.addRow("Codici Acqua ON/OFF:", self.lyt_cool_codes)                        # Riga codici refrigerante
        self.lyt_tab_ecam.addWidget(self.grp_fmt)                                               # Aggiunge al Tab e-CAM

        self.grp_tpl = QtWidgets.QGroupBox("Template Blocchi G-Code (Variabili: {PROG}, {DATE}, {DOC}, {TOOL}, {STATION}, {FEED_G}, {RPM}, {MAX_RPM}, {HOME_X}, {HOME_Z})")
        self.lyt_tpl = QtWidgets.QVBoxLayout(self.grp_tpl)                                      # Layout template

        self.chk_use_tpl = QtWidgets.QCheckBox("Attiva Template Personalizzati e-CAM")          # Abilita l'uso dei blocchi multi-riga personalizzati
        self.chk_use_tpl.setChecked(False)                                                      # Di default usa il generatore blindato standard

        self.lbl_tpl_hdr = QtWidgets.QLabel("1. Blocco Inizio Programma (Header):")             # Etichetta Header
        self.txt_tpl_hdr = QtWidgets.QPlainTextEdit()                                           # Editor multi-riga per l'Header G-Code
        self.txt_tpl_hdr.setMaximumHeight(62)                                                   # Altezza compatta
        self.txt_tpl_hdr.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")

        self.lbl_tpl_tc = QtWidgets.QLabel("2. Blocco Cambio Utensile (Tool Change):")          # Etichetta Tool Change
        self.txt_tpl_tc = QtWidgets.QPlainTextEdit()                                            # Editor multi-riga per il Cambio Utensile
        self.txt_tpl_tc.setMaximumHeight(48)                                                    # Altezza compatta
        self.txt_tpl_tc.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")

        self.lbl_tpl_ftr = QtWidgets.QLabel("3. Blocco Fine Programma (Footer):")               # Etichetta Footer
        self.txt_tpl_ftr = QtWidgets.QPlainTextEdit()                                           # Editor multi-riga per il Footer di fine programma
        self.txt_tpl_ftr.setMaximumHeight(55)                                                   # Altezza compatta
        self.txt_tpl_ftr.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")

        self.lyt_tpl.addWidget(self.chk_use_tpl)                                                # Aggiunge checkbox attivazione template
        self.lyt_tpl.addWidget(self.lbl_tpl_hdr); self.lyt_tpl.addWidget(self.txt_tpl_hdr)      # Aggiunge Header
        self.lyt_tpl.addWidget(self.lbl_tpl_tc); self.lyt_tpl.addWidget(self.txt_tpl_tc)        # Aggiunge Cambio Utensile
        self.lyt_tpl.addWidget(self.lbl_tpl_ftr); self.lyt_tpl.addWidget(self.txt_tpl_ftr)      # Aggiunge Footer
        self.lyt_tab_ecam.addWidget(self.grp_tpl)                                               # Aggiunge al Tab e-CAM

        self.tabs.addTab(self.tab_main, "1. Controllo & Programma")                             # Aggiunge Scheda 1
        self.tabs.addTab(self.tab_ecam, "2. Configuratore e-CAM (Template & Codici)")           # Aggiunge Scheda 2
        self.layout.addWidget(self.tabs)                                                        # Inserisce il TabWidget nel layout principale

        # ======================================================================
        # SEZIONE ANTEPRIMA LIVE G-CODE E PULSANTI ESPORTAZIONE (SEMPRE VISIBILE)
        # ======================================================================
        self.grp_prev = QtWidgets.QGroupBox("Anteprima Live Programma G-Code")                  # Gruppo 3: Editor di anteprima e pulsanti salvataggio
        self.lyt_prev = QtWidgets.QVBoxLayout(self.grp_prev)                                    # Layout verticale anteprima

        self.lbl_stats = QtWidgets.QLabel("Statistiche: 0 righe | 0 utensili")                  # Etichetta statistiche programma
        self.lbl_stats.setStyleSheet("color: #88C0D0; font-weight: bold;")                      # Colore azzurro

        self.txt_gcode = QtWidgets.QPlainTextEdit()                                             # Area di testo scorrevole con il G-Code (modificabile anche a mano)
        self.txt_gcode.setMinimumHeight(190)                                                    # Altezza minima
        self.txt_gcode.setStyleSheet("font-family: Consolas, monospace; font-size: 11px; background-color: #1E222A; color: #ECEFF4;")

        self.lyt_actions = QtWidgets.QHBoxLayout()                                              # Riga pulsanti Copia e Salva File
        self.btn_copy = QtWidgets.QPushButton("📋 Copia Appunti")                               # Copia il G-Code nella clipboard
        self.btn_copy.setStyleSheet("padding: 5px; font-weight: bold;")
        self.btn_copy.clicked.connect(self.copia_negli_appunti)                                 # Collega copia

        self.btn_save = QtWidgets.QPushButton("💾 Salva File .NC")                              # Apre la finestra di salvataggio file
        self.btn_save.setStyleSheet("padding: 5px; font-weight: bold; background-color: #2E6B27; color: white;")
        self.btn_save.clicked.connect(self.salva_file_nc)                                       # Collega salvataggio su disco

        self.lyt_actions.addWidget(self.btn_copy)                                               # Aggiunge pulsante Copia
        self.lyt_actions.addWidget(self.btn_save)                                               # Aggiunge pulsante Salva
        self.lyt_prev.addWidget(self.lbl_stats)                                                 # Aggiunge statistiche
        self.lyt_prev.addWidget(self.txt_gcode)                                                 # Aggiunge editor G-Code
        self.lyt_prev.addLayout(self.lyt_actions)                                               # Aggiunge riga pulsanti
        self.layout.addWidget(self.grp_prev)                                                    # Aggiunge Gruppo 3
        self.form.setLayout(self.layout)                                                        # Applica il layout finale

        # Carica i dati del primo controllo CNC nei campi del configuratore e-CAM:
        self.carica_dati_profilo_in_ui(self.dialect_combo.currentText())                        # Popola i template e-CAM iniziali

        # Collegamento segnali per rigenerare istantaneamente il G-Code ad ogni modifica:
        self.op_combo.currentIndexChanged.connect(self.rigenera_anteprima)
        self.dialect_combo.currentIndexChanged.connect(self.on_dialect_changed)
        self.xmode_combo.currentIndexChanged.connect(self.rigenera_anteprima)
        self.feed_mode_combo.currentIndexChanged.connect(self.on_feed_mode_changed)
        self.custom_feed_spin.valueChanged.connect(self.rigenera_anteprima)
        self.prog_num_edit.textChanged.connect(self.rigenera_anteprima)
        self.max_rpm_spin.valueChanged.connect(self.rigenera_anteprima)
        self.chk_n_lines.stateChanged.connect(self.rigenera_anteprima)
        self.chk_comments.stateChanged.connect(self.rigenera_anteprima)
        self.chk_coolant.stateChanged.connect(self.rigenera_anteprima)
        self.chk_g76.stateChanged.connect(self.rigenera_anteprima)
        self.chk_inv_x.stateChanged.connect(self.rigenera_anteprima)

        # Segnali della scheda Configuratore e-CAM:
        self.spin_decimals.valueChanged.connect(self.rigenera_anteprima)
        self.spin_n_start.valueChanged.connect(self.rigenera_anteprima)
        self.spin_n_step.valueChanged.connect(self.rigenera_anteprima)
        self.combo_comm_style.currentIndexChanged.connect(self.rigenera_anteprima)
        self.edit_cool_on.textChanged.connect(self.rigenera_anteprima)
        self.edit_cool_off.textChanged.connect(self.rigenera_anteprima)
        self.chk_use_tpl.stateChanged.connect(self.rigenera_anteprima)
        self.txt_tpl_hdr.textChanged.connect(self.rigenera_anteprima)
        self.txt_tpl_tc.textChanged.connect(self.rigenera_anteprima)
        self.txt_tpl_ftr.textChanged.connect(self.rigenera_anteprima)

        self.is_updating = False                                                                # Sblocca gli aggiornamenti
        self.rigenera_anteprima()                                                               # Genera subito il G-Code verificando il profilo 3D

    def on_dialect_changed(self, idx):                                                          # Quando l'utente cambia Controllo CNC aggiorna anche i template e-CAM
        nome_dial = self.dialect_combo.currentText()                                            # Legge il controllo selezionato
        self.carica_dati_profilo_in_ui(nome_dial)                                               # Carica i parametri del controllo nella scheda e-CAM
        self.rigenera_anteprima()                                                               # Rigenera l'anteprima G-Code

    def carica_dati_profilo_in_ui(self, nome_profilo):                                          # Popola i controlli della Scheda 2 (e-CAM) con i dati del profilo scelto
        prev_state = self.is_updating                                                           # Salva stato semaforo
        self.is_updating = True                                                                 # Blocca ricalcoli multipli
        p_data = self.profili_ecam.get(nome_profilo, DEFAULT_ECAM_TEMPLATES["Mach3 / Mach4 Turn (Tornio)"])
        self.edit_prof_name.setText(nome_profilo)                                               # Aggiorna nome profilo
        self.spin_decimals.setValue(int(p_data.get("decimals", 3)))                             # Imposta decimali
        self.spin_n_start.setValue(int(p_data.get("n_start", 10)))                              # Imposta N start
        self.spin_n_step.setValue(int(p_data.get("n_step", 10)))                                # Imposta N step
        self.combo_comm_style.setCurrentIndex(int(p_data.get("comm_style", 0)))                 # Imposta stile commenti
        self.edit_cool_on.setText(str(p_data.get("cool_on", "M08")))                            # Imposta codice acqua ON
        self.edit_cool_off.setText(str(p_data.get("cool_off", "M09")))                          # Imposta codice acqua OFF
        self.txt_tpl_hdr.setPlainText(str(p_data.get("header", "")))                            # Imposta template Header
        self.txt_tpl_tc.setPlainText(str(p_data.get("tool_change", "")))                        # Imposta template Tool Change
        self.txt_tpl_ftr.setPlainText(str(p_data.get("footer", "")))                            # Imposta template Footer
        self.is_updating = prev_state                                                           # Ripristina semaforo

    def costruisci_dict_ecam_corrente(self):                                                    # Raccoglie tutti i parametri della Scheda 2 (e-CAM) in un dizionario
        return {                                                                                # Dizionario configurazione e-CAM
            "use_custom_templates": self.chk_use_tpl.isChecked(),                               # Flag uso template personalizzati
            "decimals": self.spin_decimals.value(),                                             # Numero cifre decimali
            "n_start": self.spin_n_start.value(),                                               # Blocco N iniziale
            "n_step": self.spin_n_step.value(),                                                 # Passo blocchi N
            "comm_style": self.combo_comm_style.currentIndex(),                                 # Stile commento (0 o 1)
            "cool_on": self.edit_cool_on.text().strip(),                                        # Codice M accensione refrigerante
            "cool_off": self.edit_cool_off.text().strip(),                                      # Codice M spegnimento refrigerante
            "header": self.txt_tpl_hdr.toPlainText().strip(),                                   # Template Header
            "tool_change": self.txt_tpl_tc.toPlainText().strip(),                               # Template Cambio Utensile
            "footer": self.txt_tpl_ftr.toPlainText().strip()                                    # Template Footer
        }                                                                                       # Fine dizionario

    def salva_profilo_corrente_ecam(self):                                                      # Salva il profilo personalizzato nel file post_profiles_ecam.json
        nome_p = self.edit_prof_name.text().strip() or "Profilo Personalizzato Mach3"           # Legge il nome del profilo
        self.profili_ecam[nome_p] = self.costruisci_dict_ecam_corrente()                        # Aggiorna il dizionario profili
        if salva_profili_ecam(self.profili_ecam):                                               # Salva su disco in JSON
            if self.dialect_combo.findText(nome_p) < 0:                                         # Se è un nuovo nome profilo non ancora nella tendina
                self.dialect_combo.addItem(nome_p)                                              # Lo aggiunge alla tendina Controllo CNC
                self.dialect_combo.setCurrentText(nome_p)                                       # Lo seleziona
            self.lbl_stats.setStyleSheet("color: #A3BE8C; font-weight: bold;")                  # Verde conferma
            self.lbl_stats.setText(f"✔ Profilo e-CAM '{nome_p}' salvato con successo!")         # Messaggio conferma

    def ripristina_profilo_default_ecam(self):                                                  # Ripristina i template predefiniti per il controllo attivo
        nome_dial = self.dialect_combo.currentText()                                            # Controllo attuale
        base_key = "Mach3 / Mach4 Turn (Tornio)"                                                # Chiave di fallback
        for k in DEFAULT_ECAM_TEMPLATES.keys():                                                 # Cerca la chiave base corrispondente
            if k in nome_dial: base_key = k; break                                              # Trovata
        self.profili_ecam[nome_dial] = dict(DEFAULT_ECAM_TEMPLATES[base_key])                   # Ripristina i valori di fabbrica
        salva_profili_ecam(self.profili_ecam)                                                   # Aggiorna il file JSON
        self.carica_dati_profilo_in_ui(nome_dial)                                               # Ricarica nella UI
        self.rigenera_anteprima()                                                               # Rigenera l'anteprima G-Code

    def on_feed_mode_changed(self, idx):                                                        # Attiva/disattiva la casella Velocità Carro e aggiorna l'unità di misura
        self.is_updating = True                                                                 # Sospende ricalcolo intermedio
        if idx == 0:                                                                            # Modalità 0: mm/giro (G95)
            self.custom_feed_spin.setEnabled(False)                                             # Usa gli avanzamenti a giro delle operazioni
        elif idx == 1:                                                                          # Modalità 1: Millimetri al Secondo (mm/s -> G94)
            self.custom_feed_spin.setEnabled(True)                                              # Abilita l'inserimento della velocità in mm/s
            self.custom_feed_spin.setSuffix(" mm/s")                                            # Mostra suffisso mm/s
            if self.custom_feed_spin.value() > 200.0:                                           # Se veniva da mm/min (es. 1200), lo riporta a 20 mm/s
                self.custom_feed_spin.setValue(round(self.custom_feed_spin.value() / 60.0, 1))
        else:                                                                                   # Modalità 2: Millimetri al Minuto (mm/min - G94)
            self.custom_feed_spin.setEnabled(True)                                              # Abilita l'inserimento diretto in mm/min
            self.custom_feed_spin.setSuffix(" mm/min")                                          # Mostra suffisso mm/min
            if self.custom_feed_spin.value() <= 50.0:                                           # Se veniva da mm/s (es. 20 mm/s), lo converte in 1200 mm/min
                self.custom_feed_spin.setValue(round(self.custom_feed_spin.value() * 60.0, 0))
        self.is_updating = False                                                                # Riabilita ricalcolo
        self.rigenera_anteprima()                                                               # Rigenera subito il G-Code

    def popola_combo_operazioni(self):                                                          # Carica tutte le operazioni presenti in Operazioni_CAM
        self.op_combo.clear()                                                                   # Svuota il combo
        self.op_combo.addItem("★ Tutte le Operazioni in Sequenza", "ALL")                       # Prima voce: programma completo
        if self.doc and self.doc.getObject("Operazioni_CAM"):                                   # Se esiste il gruppo Operazioni_CAM
            ops_grp = self.doc.getObject("Operazioni_CAM")                                      # Gruppo operazioni
            for op in ops_grp.Group:                                                            # Scorre ogni operazione
                if hasattr(op, "PercorsoJSON"):                                                 # Verifica che sia un'operazione CAM
                    self.op_combo.addItem(f"• {op.Label}", op.Name)                             # Aggiunge voce e Name interno

    def rigenera_anteprima(self, *args):                                                        # Rigenera il testo G-Code nell'editor di anteprima
        if self.is_updating or not self.doc: return                                             # Evita ricalcoli multipli in avvio
        ops_grp = self.doc.getObject("Operazioni_CAM")                                          # Gruppo Operazioni_CAM
        lista_ops = []                                                                          # Lista operazioni da processare
        sel_data = self.op_combo.itemData(self.op_combo.currentIndex())                         # Scelta corrente ("ALL" o Name)
        if ops_grp and hasattr(ops_grp, "Group"):                                               # Se il gruppo contiene operazioni
            if sel_data == "ALL":                                                               # Tutte in sequenza
                lista_ops = list(ops_grp.Group)                                                 # Prende tutte le operazioni nell'ordine dell'albero
            else:                                                                               # Singola operazione
                op_singola = self.doc.getObject(str(sel_data))                                  # Ottiene l'operazione scelta
                if op_singola: lista_ops = [op_singola]                                         # Lista con un solo elemento

        modo_diam = (self.xmode_combo.currentIndex() == 0)                                      # True se Programmazione al Diametro
        dialetto = self.dialect_combo.currentText()                                             # Controllo CNC selezionato

        testo_nc, n_righe, n_tools = genera_codice_nc(                                          # Chiama il motore di generazione G-Code
            self.doc, lista_ops, dialetto,
            modo_diametro=modo_diam,
            usa_numeri_riga=self.chk_n_lines.isChecked(),
            usa_commenti=self.chk_comments.isChecked(),
            usa_refrigerante=self.chk_coolant.isChecked(),
            usa_g76_filetto=self.chk_g76.isChecked(),
            inverti_x_mach3=self.chk_inv_x.isChecked(),
            feed_mode_idx=self.feed_mode_combo.currentIndex(),
            custom_feed_val=self.custom_feed_spin.value(),
            prog_number=self.prog_num_edit.text(),
            max_rpm=self.max_rpm_spin.value(),
            ecam_cfg=self.costruisci_dict_ecam_corrente()                                       # Passa la configurazione e-CAM!
        )                                                                                       # Fine generazione

        self.txt_gcode.setPlainText(testo_nc)                                                   # Mostra il listato nell'editor
        self.lbl_stats.setText(f"Statistiche: {n_righe} righe generate | {n_tools} utensili impiegati")

    def copia_negli_appunti(self):                                                              # Copia il contenuto dell'editor G-Code negli appunti
        testo = self.txt_gcode.toPlainText()                                                    # Legge il testo
        cb = QtWidgets.QApplication.clipboard()                                                 # Ottiene la clipboard di sistema
        cb.setText(testo)                                                                       # Copia il testo
        self.lbl_stats.setStyleSheet("color: #A3BE8C; font-weight: bold;")                      # Verde conferma
        self.lbl_stats.setText("✔ Programma G-Code copiato negli Appunti!")                     # Messaggio di conferma

    def salva_file_nc(self):                                                                    # Salva il programma G-Code su file (.tap, .nc, .mpf, .ngc)
        dialetto = self.dialect_combo.currentText()                                             # Controllo scelto
        if "Mach3" in dialetto: ext_def = ".tap"                                                # Estensione classica per Mach3 (.tap)
        elif "Siemens" in dialetto: ext_def = ".mpf"                                            # Estensione Siemens (.mpf)
        elif "LinuxCNC" in dialetto: ext_def = ".ngc"                                           # Estensione LinuxCNC (.ngc)
        else: ext_def = ".nc"                                                                   # Estensione Fanuc (.nc)

        nome_suggerito = (self.prog_num_edit.text().strip() or "Programma_Tornio") + ext_def    # Nome file proposto

        filtri = "File G-Code Tornio (*.tap *.nc *.mpf *.ngc *.txt);;Tutti i file (*.*)"        # Filtri estensioni nella finestra di dialogo
        percorso_file, _ = QtWidgets.QFileDialog.getSaveFileName(                               # Apre la finestra standard Salva con nome
            self.form, "Esporta Programma G-Code Tornio", nome_suggerito, filtri
        )
        if not percorso_file:                                                                   # Se l'utente ha premuto Annulla
            return False                                                                        # Esce senza salvare

        try:                                                                                    # Scrive il contenuto dell'editor sul file scelto
            with open(percorso_file, "w", encoding="utf-8") as f:                               # Apre in scrittura UTF-8
                f.write(self.txt_gcode.toPlainText())                                           # Salva esattamente il testo visibile nell'editor
            self.lbl_stats.setStyleSheet("color: #A3BE8C; font-weight: bold;")                  # Verde conferma
            self.lbl_stats.setText(f"✔ Salvato con successo: {percorso_file}")                  # Mostra conferma
            FreeCAD.Console.PrintMessage(f"G-Code esportato correttamente in: {percorso_file}\n")
            return True                                                                         # Salvataggio riuscito
        except Exception as e:                                                                  # Gestione errore scrittura disco
            self.lbl_stats.setStyleSheet("color: #FF5555; font-weight: bold;")                  # Rosso errore
            self.lbl_stats.setText(f"Errore salvataggio: {e}")                                  # Mostra l'errore
            return False                                                                        # Fallito

    def getStandardButtons(self):                                                               # Pulsante di chiusura del pannello Task
        return QtWidgets.QDialogButtonBox.Close                                                 # Mostra Close

    def accept(self):                                                                           # Chiusura pannello
        FreeCADGui.Control.closeDialog()                                                        # Chiude il dialogo
        return True                                                                             # Conferma

    def reject(self):                                                                           # Chiusura pannello con Close / Esc
        FreeCADGui.Control.closeDialog()                                                        # Chiude il dialogo
        return True                                                                             # Conferma