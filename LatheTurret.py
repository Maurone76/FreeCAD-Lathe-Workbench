import FreeCAD                                                                                  # Importa il modulo base di FreeCAD
import FreeCADGui                                                                               # Importa il modulo interfaccia grafica di FreeCAD
import Part                                                                                     # Importa il modulo geometrico Part
import math                                                                                     # Importa le funzioni matematiche
import os                                                                                       # Importa il modulo per gestire percorsi e cartelle
import json                                                                                     # Importa il modulo JSON per salvare configurazioni e saldature
import ImportGui                                                                                # Importa il gestore per file STEP/IGES
from PySide import QtCore, QtGui                                                                # Importa i moduli grafici PySide
try:                                                                                            # Tenta di importare QtWidgets per compatibilità Qt5/Qt6
    from PySide import QtWidgets                                                                # Assegna QtWidgets
except ImportError:                                                                             # Fallback per versioni meno recenti
    QtWidgets = QtGui                                                                           # Usa QtGui come alias di QtWidgets


def get_turret_lib_dir():                                                                       # Restituisce la cartella su disco per l'archivio torrette
    base_dir = os.path.dirname(os.path.abspath(__file__))                                       # Cartella del Workbench corrente
    lib_dir = os.path.join(base_dir, "TurretLibrary")                                           # Sottocartella TurretLibrary
    os.makedirs(lib_dir, exist_ok=True)                                                         # Crea la cartella se non esiste
    return lib_dir                                                                              # Restituisce il percorso completo


def get_turret_db_file():                                                                       # Restituisce il percorso del file JSON delle torrette
    return os.path.join(get_turret_lib_dir(), "turrets_db.json")                                # Percorso completo di turrets_db.json


def load_turrets_db():                                                                          # Legge il database delle torrette salvate su disco
    db_path = get_turret_db_file()                                                              # Ottiene il percorso del file JSON
    if os.path.exists(db_path):                                                                 # Controlla se il file esiste
        try:                                                                                    # Tenta la lettura del file JSON
            with open(db_path, "r", encoding="utf-8") as f:                                     # Apre il file in modalità lettura
                return json.load(f)                                                             # Restituisce il dizionario caricato
        except Exception as e:                                                                  # Cattura eventuali errori di lettura
            FreeCAD.Console.PrintError(f"Errore lettura archivio torrette: {e}\n")              # Stampa l'errore in console
    return {}                                                                                   # Restituisce un dizionario vuoto se non esiste


def save_turrets_db(db_data):                                                                   # Salva il database delle torrette su disco
    db_path = get_turret_db_file()                                                              # Ottiene il percorso del file JSON
    try:                                                                                        # Tenta la scrittura su disco
        with open(db_path, "w", encoding="utf-8") as f:                                         # Apre il file in scrittura
            json.dump(db_data, f, indent=4, ensure_ascii=False)                                 # Scrive il dizionario formattato
    except Exception as e:                                                                      # Cattura eventuali errori
        FreeCAD.Console.PrintError(f"Errore salvataggio archivio torrette: {e}\n")              # Stampa l'errore in console


def get_wcs_origin(doc=None):                                                                   # Legge l'origine del WCS (Setup_Macchina)
    if doc is None:                                                                             # Se il documento non è specificato
        doc = FreeCAD.ActiveDocument                                                            # Usa il documento attivo
    if doc and doc.getObject("Setup_Macchina"):                                                 # Se esiste l'oggetto Setup_Macchina
        setup_obj = doc.getObject("Setup_Macchina")                                             # Ottiene il riferimento all'oggetto
        if hasattr(setup_obj, "Origine"):                                                       # Controlla che abbia la proprietà Origine
            return FreeCAD.Vector(setup_obj.Origine)                                            # Restituisce il vettore Origine del WCS
    return FreeCAD.Vector(0.0, 0.0, 0.0)                                                        # Restituisce (0,0,0) se il WCS non è presente


def calcola_rotazione_sede_locale(norm_loc):                                                    # Calcola la rotazione per allineare il gambo alla sede
    dir_xy = FreeCAD.Vector(norm_loc.x, norm_loc.y, 0.0)                                        # Proietta la direzione uscente della sede sul piano XY
    if dir_xy.Length > 0.001:                                                                   # Se la sede ha una direzione radiale valida
        ang_rad = math.atan2(dir_xy.y, dir_xy.x)                                                # Angolo della sede rispetto a +X
        delta_deg = math.degrees(ang_rad) - 180.0                                               # Differenza angolare rispetto alla Sede 1 (-X = 180°)
        return FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), delta_deg)                             # Rotazione attorno all'asse Z locale della torretta
    return FreeCAD.Rotation()                                                                   # Nessuna rotazione aggiuntiva per la Sede 1


def calcola_dati_sede_da_indice(idx_stazione, num_pos, diametro, prof_sede):                    # Calcola centro e normale locale per la stazione i-esima (1..N)
    n = max(int(num_pos), 3)                                                                    # Numero totale stazioni della torretta
    idx = ((max(int(idx_stazione), 1) - 1) % n)                                                 # Indice base zero (0..N-1)
    r_ap = max(float(diametro) / 2.0, 10.0)                                                     # Raggio apotema alla faccia esterna
    ang = math.pi + (idx * 2.0 * math.pi / float(n))                                            # Angolo radiale della stazione (Stazione 1 a 180° = -X)
    nx = math.cos(ang)                                                                          # Componente X del versore uscente dalla sede
    ny = math.sin(ang)                                                                          # Componente Y del versore uscente dalla sede
    norm_loc = FreeCAD.Vector(nx, ny, 0.0)                                                      # Normale uscente sul piano XY
    pt_loc = FreeCAD.Vector(nx * r_ap, ny * r_ap, float(prof_sede) / 2.0)                       # Punto sul bordo esterno a metà profondità sede frontale
    return pt_loc, norm_loc                                                                     # Restituisce punto base e normale locale


def costruisci_plateau_parametrico(num_pos, diametro, spessore, incavo_w, incavo_p):            # Genera il plateau poligonale sul piano XY con sedi frontali
    n = max(int(num_pos), 3)                                                                    # Garantisce almeno 3 lati per il poligono
    r_apotema = max(float(diametro) / 2.0, 10.0)                                                # Raggio alla faccia piana esterna (apotema = Ø/2 = 75 mm)
    mezzo_angolo = math.pi / float(n)                                                           # Metà dell'angolo di settore del poligono
    r_vertice = r_apotema / math.cos(mezzo_angolo)                                              # Raggio ai vertici del poligono
    sp = max(float(spessore), 5.0)                                                              # Spessore assiale del disco torretta lungo Z
    r_flangia = r_apotema * 0.44                                                                # Raggio del disco circolare centrale di battuta

    punti = []                                                                                  # Lista dei vertici del poligono nel piano XY (ruotato di 90° su X)
    for i in range(n):                                                                          # Calcola i vertici per ogni stazione
        ang = math.pi + (i * 2.0 * math.pi / float(n)) - mezzo_angolo                           # Angolo del vertice (Stazione 1 orientata verso -X)
        px = r_vertice * math.cos(ang)                                                          # Coordinata X del vertice
        py = r_vertice * math.sin(ang)                                                          # Coordinata Y del vertice
        punti.append(FreeCAD.Vector(px, py, 0.0))                                               # Aggiunge il vertice sul piano frontale Z = 0
    punti.append(punti[0])                                                                      # Chiude il poligono tornando al primo vertice

    wire = Part.makePolygon(punti)                                                              # Crea il profilo poligonale chiuso sul piano XY
    face = Part.Face(wire)                                                                      # Crea la faccia piana frontale del poligono
    disco = face.extrude(FreeCAD.Vector(0.0, 0.0, sp))                                          # Estrude lo spessore lungo +Z (faccia frontale a Z = 0)

    if incavo_w > 0.1 and incavo_p > 0.1:                                                       # Se sono richiesti gli incavi frontali (es. 10x10 mm)
        scavi = []                                                                              # Lista dei solidi di scavo per le sedi frontali
        lung_radiale = (r_vertice - r_flangia) + 5.0                                            # Lunghezza radiale dello scavo dal disco centrale fino all'esterno
        for i in range(n):                                                                      # Crea una sede radiale frontale per ciascuna delle N stazioni
            ang_stazione = math.pi + (i * 2.0 * math.pi / float(n))                             # Angolo radiale della stazione i-esima
            box = Part.makeBox(                                                                 # Crea il parallelepipedo di scavo sulla faccia frontale
                lung_radiale,                                                                   # Estensione radiale dalla flangia centrale oltre il bordo esterno
                incavo_w,                                                                       # Larghezza della sede portautensile (es. 10 mm)
                incavo_p + 1.0,                                                                 # Profondità assiale nella faccia frontale lungo Z (es. 10 mm)
                FreeCAD.Vector(r_flangia, -incavo_w / 2.0, -1.0)                                # Parte dal raggio della flangia centrale sul fronte Z = 0
            )                                                                                   # Fine creazione box di scavo frontale
            rot_deg = math.degrees(ang_stazione)                                                # Angolo di rotazione nel piano XY attorno all'asse Z
            box.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), rot_deg)               # Ruota la sede attorno a Z per posizionarla sulla faccia i-esima
            scavi.append(box)                                                                   # Aggiunge lo scavo alla lista
        if scavi:                                                                               # Se sono stati generati gli scavi frontali
            try:                                                                                # Tenta la sottrazione booleana delle sedi frontali
                disco = disco.cut(Part.makeCompound(scavi))                                     # Scava le N sedi radiali sulla faccia frontale del plateau
            except Exception:                                                                   # In caso di errore geometrico
                pass                                                                            # Mantiene il poligono base

    flangia_centrale = Part.makeCylinder(r_flangia, 2.0, FreeCAD.Vector(0, 0, -2.0), FreeCAD.Vector(0, 0, 1)) # Disco centrale frontale come in foto
    try:                                                                                        # Tenta l'unione della flangia centrale sul fronte
        disco = disco.fuse(flangia_centrale)                                                    # Unisce il disco centrale di battuta
    except Exception:                                                                           # Ignora eventuali errori
        pass                                                                                    # Continua
    return disco                                                                                # Restituisce il solido 3D del plateau


class LatheTurretObject:                                                                        # Classe Proxy per l'oggetto parametrico Torretta_Macchina
    def __init__(self, obj):                                                                    # Costruttore del Proxy
        self._is_executing = False                                                              # Flag per prevenire ricalcoli ricorsivi
        self.ensure_properties(obj)                                                             # Garantisce la creazione di tutte le proprietà
        obj.Proxy = self                                                                        # Collega il Proxy all'oggetto FreeCAD

    def ensure_properties(self, obj):                                                           # Aggiunge le proprietà native se mancanti
        if not hasattr(obj, "TurretName"):                                                      # Nome identificativo della torretta
            obj.addProperty("App::PropertyString", "TurretName", "Torretta", "Nome configurazione torretta").TurretName = "Torretta Ottagonale 150"
        if not hasattr(obj, "Modalita"):                                                        # Modalità Parametrica o Custom STEP
            obj.addProperty("App::PropertyEnumeration", "Modalita", "Torretta", "Tipo costruzione")
            obj.Modalita = ["Parametrica", "Custom"]                                            # Opzioni disponibili
        if not hasattr(obj, "NumeroPosizioni"):                                                 # Numero di stazioni (default 8)
            obj.addProperty("App::PropertyInteger", "NumeroPosizioni", "Geometria", "Numero posizioni torretta").NumeroPosizioni = 8
        if not hasattr(obj, "Diametro"):                                                        # Diametro torretta (default 150 mm)
            obj.addProperty("App::PropertyFloat", "Diametro", "Geometria", "Diametro plateau (mm)").Diametro = 150.0
        if not hasattr(obj, "Spessore"):                                                        # Spessore torretta (default 40 mm)
            obj.addProperty("App::PropertyFloat", "Spessore", "Geometria", "Spessore plateau (mm)").Spessore = 40.0
        if not hasattr(obj, "LarghezzaIncavo"):                                                 # Larghezza sede portautensili (default 10 mm)
            obj.addProperty("App::PropertyFloat", "LarghezzaIncavo", "Geometria", "Larghezza sede frontale (mm)").LarghezzaIncavo = 10.0
        if not hasattr(obj, "ProfonditaIncavo"):                                                # Profondità sede portautensili (default 10 mm)
            obj.addProperty("App::PropertyFloat", "ProfonditaIncavo", "Geometria", "Profondità sede frontale (mm)").ProfonditaIncavo = 10.0
        if not hasattr(obj, "DistX_WCS"):                                                       # Distanza di sicurezza in X dal WCS (default 25 mm)
            obj.addProperty("App::PropertyFloat", "DistX_WCS", "Posizione", "Distanza faccia torretta da WCS in X (mm)").DistX_WCS = 25.0
        if not hasattr(obj, "DistY_WCS"):                                                       # Offset in Y dal WCS (default 0 mm)
            obj.addProperty("App::PropertyFloat", "DistY_WCS", "Posizione", "Offset centro torretta in Y (mm)").DistY_WCS = 0.0
        if not hasattr(obj, "DistZ_WCS"):                                                       # Distanza di sicurezza in Z dal WCS (default 25 mm)
            obj.addProperty("App::PropertyFloat", "DistZ_WCS", "Posizione", "Distanza faccia torretta da WCS in Z (mm)").DistZ_WCS = 25.0
        if not hasattr(obj, "SpecchiaX"):                                                       # Specchiatura plateau su X
            obj.addProperty("App::PropertyBool", "SpecchiaX", "Orientamento", "Specchia plateau su X").SpecchiaX = False
        if not hasattr(obj, "SpecchiaY"):                                                       # Specchiatura plateau su Y
            obj.addProperty("App::PropertyBool", "SpecchiaY", "Orientamento", "Specchia plateau su Y").SpecchiaY = False
        if not hasattr(obj, "RotX"):                                                            # Rotazione plateau su X
            obj.addProperty("App::PropertyFloat", "RotX", "Orientamento", "Rotazione X (deg)").RotX = 0.0
        if not hasattr(obj, "RotY"):                                                            # Rotazione plateau su Y
            obj.addProperty("App::PropertyFloat", "RotY", "Orientamento", "Rotazione Y (deg)").RotY = 0.0
        if not hasattr(obj, "RotZ"):                                                            # Rotazione plateau su Z
            obj.addProperty("App::PropertyFloat", "RotZ", "Orientamento", "Rotazione Z (deg)").RotZ = 0.0
        if not hasattr(obj, "StazioneAttiva"):                                                  # Stazione corrente portata in posizione di lavoro
            obj.addProperty("App::PropertyInteger", "StazioneAttiva", "Torretta", "Stazione attiva in lavoro").StazioneAttiva = 1
        if not hasattr(obj, "CustomBaseShape"):                                                 # Geometria STEP importata per torretta custom
            obj.addProperty("Part::PropertyPartShape", "CustomBaseShape", "Custom", "Forma base STEP del plateau")
        if not hasattr(obj, "UtensiliSaldati"):                                                 # Dizionario JSON degli utensili saldati sulla torretta
            obj.addProperty("App::PropertyString", "UtensiliSaldati", "Montaggio", "Dati JSON utensili saldati").UtensiliSaldati = "{}"

    def onDocumentRestored(self, obj):                                                          # Ripristina lo stato all'apertura di un file salvato
        self._is_executing = False                                                              # Azzera il flag di blocco
        self.ensure_properties(obj)                                                             # Verifica tutte le proprietà

    def calcola_centro_e_rotazione(self, obj):                                                  # Calcola il centro 3D e la rotazione globale della torretta
        wcs = get_wcs_origin(obj.Document)                                                      # Legge l'origine del WCS
        r_ingombro = float(obj.Diametro) / 2.0 if obj.Modalita == "Parametrica" else 0.0        # Raggio del plateau per garantire la distanza dal WCS
        cx = wcs.x + r_ingombro + float(obj.DistX_WCS)                                          # Posiziona la faccia più vicina a +DistX_WCS (25 mm)
        cy = wcs.y + float(obj.DistY_WCS)                                                       # Posiziona sul piano Y del WCS + eventuale offset
        cz = wcs.z + float(obj.DistZ_WCS)                                                       # Posiziona la faccia frontale scostata in Z di +DistZ_WCS (25 mm)
        centro = FreeCAD.Vector(cx, cy, cz)                                                     # Vettore centro torretta nello spazio

        rx = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), obj.RotX)                                # Rotazione manuale X
        ry = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), obj.RotY)                                # Rotazione manuale Y
        rz = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), obj.RotZ)                                # Rotazione manuale Z
        rot_base = rx * ry * rz                                                                 # Rotazione base del plateau

        n = max(int(obj.NumeroPosizioni), 1)                                                    # Numero di stazioni
        st_att = max(1, min(int(obj.StazioneAttiva), n))                                        # Stazione attiva (1..N)
        angolo_index = -(st_att - 1) * (360.0 / float(n))                                       # Angolo di indexaggio attorno all'asse Z della torretta
        rot_index = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), angolo_index)                     # Rotazione attorno all'asse Z per portare la stazione in lavoro
        rot_tot = rot_base * rot_index                                                          # Rotazione complessiva della torretta
        return centro, rot_tot                                                                  # Restituisce centro e rotazione totale

    def muovi_punta_attiva_a(self, obj, target_x_wcs, target_z_wcs, num_stazione=None):         # Muove la torretta affinché la punta attiva vada in (target_x, target_z)
        self.ensure_properties(obj)                                                             # Verifica proprietà
        if num_stazione is not None:                                                            # Se è richiesto un cambio stazione
            obj.StazioneAttiva = int(num_stazione)                                              # Indexa la torretta sulla stazione richiesta
        doc = obj.Document                                                                      # Documento FreeCAD
        try: saldati = json.loads(obj.UtensiliSaldati or "{}")                                  # Legge gli utensili saldati
        except Exception: saldati = {}                                                          # Fallback

        st_curr = int(obj.StazioneAttiva)                                                       # Stazione attiva corrente
        rel_vec_attivo = None                                                                   # Vettore relativo della punta dell'utensile attivo
        for t_name, info in saldati.items():                                                    # Cerca l'utensile montato sulla stazione attiva
            t_obj = doc.getObject(t_name) if doc else None                                      # Oggetto utensile
            if t_obj and int(getattr(t_obj, "NumeroStazione", -1)) == st_curr:                  # Se corrisponde alla stazione attiva
                rel_vec_attivo = FreeCAD.Vector(*info.get("rel_pos", [0.0, 0.0, 0.0]))          # Trovato il vettore relativo
                break                                                                           # Esce dal ciclo
        if rel_vec_attivo is None and saldati:                                                  # Se non trova per numero stazione, prende il primo saldato
            first_info = next(iter(saldati.values()))                                           # Primo record disponibile
            rel_vec_attivo = FreeCAD.Vector(*first_info.get("rel_pos", [0.0, 0.0, 0.0]))        # Vettore relativo

        _, rot_tot = self.calcola_centro_e_rotazione(obj)                                       # Calcola la rotazione attuale della torretta
        r_ing = float(obj.Diametro) / 2.0 if obj.Modalita == "Parametrica" else 0.0             # Raggio d'ingombro del plateau
        if rel_vec_attivo is not None:                                                          # Se c'è un utensile saldato
            offset_punta = rot_tot.multVec(rel_vec_attivo)                                      # Vettore dal centro torretta alla punta utensile
            obj.DistX_WCS = float(target_x_wcs) - offset_punta.x - r_ing                        # Calcola DistX_WCS per portare la punta a target_x_wcs
            obj.DistZ_WCS = float(target_z_wcs) - offset_punta.z                                # Calcola DistZ_WCS per portare la punta a target_z_wcs
        else:                                                                                   # Se la torretta è ancora senza utensili saldati
            obj.DistX_WCS = float(target_x_wcs)                                                 # Sposta direttamente la faccia della torretta a target_x
            obj.DistZ_WCS = float(target_z_wcs)                                                 # Sposta la faccia frontale a target_z
        self.execute(obj)                                                                       # Aggiorna il 3D di torretta e utensili

    def execute(self, obj):                                                                     # Genera la forma della torretta e aggiorna gli utensili saldati
        if getattr(self, "_is_executing", False):                                               # Evita chiamate ricorsive
            return                                                                              # Esce subito
        self._is_executing = True                                                               # Blocca esecuzioni concorrenti
        try:                                                                                    # Blocco protetto di ricalcolo
            self.ensure_properties(obj)                                                         # Verifica attributi
            centro, rot_tot = self.calcola_centro_e_rotazione(obj)                              # Ottiene centro e rotazione della torretta

            if obj.Modalita == "Parametrica":                                                   # Costruzione torretta parametrica (default ottagono Ø150)
                forma = costruisci_plateau_parametrico(                                         # Genera il solido poligonale con sedi frontali
                    obj.NumeroPosizioni, obj.Diametro, obj.Spessore,                            # Passa N posizioni, diametro e spessore
                    obj.LarghezzaIncavo, obj.ProfonditaIncavo                                   # Passa larghezza e profondità incavo frontale (10x10)
                )                                                                               # Fine generazione solido
            else:                                                                               # Costruzione torretta Custom da file STEP
                if obj.CustomBaseShape and not obj.CustomBaseShape.isNull():                    # Se è stato importato uno STEP valido
                    forma = obj.CustomBaseShape.copy()                                          # Copia la forma STEP
                else:                                                                           # Fallback se non ancora importato
                    forma = costruisci_plateau_parametrico(obj.NumeroPosizioni, obj.Diametro, obj.Spessore, obj.LarghezzaIncavo, obj.ProfonditaIncavo)

            if obj.SpecchiaX:                                                                   # Se attiva specchiatura X
                forma = forma.mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0))          # Specchia il plateau su X
            if obj.SpecchiaY:                                                                   # Se attiva specchiatura Y
                forma = forma.mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0))          # Specchia il plateau su Y

            forma.Placement = FreeCAD.Placement(centro, rot_tot) * forma.Placement              # Posiziona e ruota la torretta nello spazio
            obj.Shape = forma                                                                   # Assegna la Shape finale all'oggetto Torretta

            if hasattr(obj, "ViewObject") and obj.ViewObject:                                   # Imposta l'aspetto grafico della torretta
                obj.ViewObject.ShapeColor = (0.25, 0.28, 0.32)                                  # Grigio antracite metallico per distinguere la torretta

            self.aggiorna_utensili_saldati(obj, centro, rot_tot)                                # Muove e ruota solidalmente gli utensili saldati sulla torretta
        except Exception as e:                                                                  # Cattura errori di ricalcolo
            FreeCAD.Console.PrintError(f"Errore ricalcolo torretta: {e}\n")                     # Stampa l'errore in console
        finally:                                                                                # Eseguito sempre in uscita
            self._is_executing = False                                                          # Rilascia il blocco

    def aggiorna_utensili_saldati(self, obj, centro_torretta, rot_torretta):                    # Mantiene gli utensili saldati solidali in posizione e orientamento
        doc = obj.Document                                                                      # Ottiene il documento FreeCAD
        if not doc:                                                                             # Se non c'è documento
            return                                                                              # Esce
        wcs = get_wcs_origin(doc)                                                               # Legge l'origine del WCS
        try:                                                                                    # Legge il dizionario JSON delle saldature
            saldati = json.loads(obj.UtensiliSaldati or "{}")                                   # Decodifica la stringa JSON
        except Exception:                                                                       # Se la stringa non è valida
            saldati = {}                                                                        # Usa dizionario vuoto

        for tool_name, info in saldati.items():                                                 # Cicla su ogni utensile saldato
            tool_obj = doc.getObject(tool_name)                                                 # Cerca l'oggetto utensile nel documento
            if not tool_obj:                                                                    # Se per nome interno non lo trova, cerca per Label
                lib = doc.getObject("Libreria_Utensili")                                        # Cerca nel Magazzino Utensili
                if lib:                                                                         # Se il magazzino esiste
                    for t in lib.Group:                                                         # Scorre gli utensili del magazzino
                        if t.Label == tool_name or getattr(t, "ToolName", "") == tool_name:     # Se il nome corrisponde
                            tool_obj = t                                                        # Trovato l'utensile
                            break                                                               # Esce dal ciclo interno
            if tool_obj and hasattr(tool_obj, "OffsetTorretta"):                                # Se l'utensile esiste nel progetto
                rel_vec = FreeCAD.Vector(*info.get("rel_pos", [0.0, 0.0, 0.0]))                 # Legge il vettore posizione punta relativo al centro torretta
                pos_globale_punta = centro_torretta + rot_torretta.multVec(rel_vec)             # Calcola dove si trova ora la punta con la torretta ruotata
                nuovo_offset = pos_globale_punta - wcs                                          # Calcola l'OffsetTorretta rispetto al WCS
                f_nm = FreeCAD.Vector(*info.get("faccia_norm", [-1.0, 0.0, 0.0]))               # Legge la direzione uscente della sede saldata
                rot_sede = calcola_rotazione_sede_locale(f_nm)                                  # Calcola l'inclinazione della sede sulla torretta
                rot_trascinamento = rot_torretta * rot_sede                                     # Compone la rotazione della torretta con quella della sede
                tool_obj.Proxy._is_executing = True                                             # Sospende il ricalcolo singolo
                try:                                                                            # Aggiorna posizione e rotazione dell'utensile
                    tool_obj.Proxy.ensure_properties(tool_obj)                                  # Assicura che esista anche RotazioneTorretta
                    tool_obj.OffsetTorretta = nuovo_offset                                      # Imposta il nuovo OffsetTorretta
                    tool_obj.RotazioneTorretta = list(rot_trascinamento.Q)                      # Imposta il quaternione di trascinamento della sede/torretta
                    if "rx" in info: tool_obj.RotX = float(info["rx"])                          # Imposta la rotazione X locale saldata
                    if "ry" in info: tool_obj.RotY = float(info["ry"])                          # Imposta la rotazione Y locale saldata
                    if "rz" in info: tool_obj.RotZ = float(info["rz"])                          # Imposta la rotazione Z locale saldata
                    if "mx" in info: tool_obj.SpecchiaX = bool(info["mx"])                      # Imposta la specchiatura X saldata
                    if "my" in info: tool_obj.SpecchiaY = bool(info["my"])                      # Imposta la specchiatura Y saldata
                finally:                                                                        # Sblocca il Proxy dell'utensile
                    tool_obj.Proxy._is_executing = False                                        # Riabilita execute sull'utensile
                tool_obj.Proxy.execute(tool_obj)                                                # Ridisegna l'utensile inclinato insieme alla sua sede

    def onChanged(self, obj, prop):                                                             # Intercetta le modifiche live dalle Proprietà di FreeCAD
        if getattr(self, "_is_executing", False):                                               # Evita loop ricorsivi
            return                                                                              # Esce
        props_live = [                                                                          # Proprietà che scatenano l'aggiornamento 3D immediato
            "Modalita", "NumeroPosizioni", "Diametro", "Spessore",                              # Parametri geometrici del plateau
            "LarghezzaIncavo", "ProfonditaIncavo",                                              # Parametri delle sedi frontali 10x10
            "DistX_WCS", "DistY_WCS", "DistZ_WCS",                                              # Posizione della torretta rispetto al WCS
            "SpecchiaX", "SpecchiaY", "RotX", "RotY", "RotZ",                                   # Orientamento spaziale
            "StazioneAttiva", "UtensiliSaldati"                                                 # Stazione attiva e saldature utensili
        ]                                                                                       # Fine lista proprietà live
        if prop in props_live:                                                                  # Se è stata toccata una proprietà geometrica o di posizione
            self.execute(obj)                                                                   # Aggiorna in tempo reale torretta e utensili saldati

    def __getstate__(self):                                                                     # Serializzazione per salvataggio file
        return None                                                                             # Nessun dato speciale

    def __setstate__(self, state):                                                              # Deserializzazione all'apertura file
        self._is_executing = False                                                              # Ripristina il flag
        return None                                                                             # Fine


class ViewProviderLatheTurret:                                                                  # ViewProvider per gestire doppio click e visualizzazione
    def __init__(self, vobj):                                                                   # Costruttore ViewProvider
        vobj.Proxy = self                                                                       # Collega il Proxy alla vista

    def getIcon(self):                                                                          # Icona nell'albero
        return "Part_Prism"                                                                     # Icona poligonale per la torretta

    def attach(self, vobj):                                                                     # Collega gli oggetti alla vista
        self.ViewObject = vobj                                                                  # Riferimento ViewObject
        self.Object = vobj.Object                                                               # Riferimento Object

    def updateData(self, vobj, prop):                                                           # Aggiornamento dati
        return                                                                                  # Gestito da execute

    def onDelete(self, vobj, subelements):                                                      # Autorizza eliminazione dall'albero
        return True                                                                             # Sempre consentito

    def doubleClicked(self, vobj):                                                              # Doppio click su Torretta_Macchina nell'albero
        if not FreeCADGui.Control.activeDialog():                                               # Se non c'è già un pannello aperto
            panel = LatheTurretPanel(edit_obj=vobj.Object)                                      # Apre il pannello di modifica della torretta
            FreeCADGui.Control.showDialog(panel)                                                # Mostra il pannello nel Task
        return True                                                                             # Evento gestito

    def setEdit(self, vobj, mode):                                                              # Modalità Edit standard
        if mode == 0:                                                                           # Modifica base
            if not FreeCADGui.Control.activeDialog():                                           # Evita aperture doppie
                panel = LatheTurretPanel(edit_obj=vobj.Object)                                  # Crea il pannello con l'oggetto esistente
                FreeCADGui.Control.showDialog(panel)                                            # Mostra il dialogo
            return True                                                                         # Conferma
        return False                                                                            # Altre modalità ignorate

    def unsetEdit(self, vobj, mode):                                                            # Chiusura modalità Edit
        FreeCADGui.Control.closeDialog()                                                        # Chiude il dialogo
        return True                                                                             # Conferma

    def __getstate__(self):                                                                     # Serializzazione
        return None                                                                             # Nessuno stato extra

    def __setstate__(self, state):                                                              # Deserializzazione
        return None                                                                             # Nessuno stato extra


class LatheTurretPanel:                                                                         # Pannello UI per creazione torretta, automazione e collisioni
    def __init__(self, edit_obj=None):                                                          # Costruttore del pannello Task
        self.edit_obj = edit_obj                                                                # Eventuale oggetto Torretta_Macchina esistente
        self.is_updating = True                                                                 # Blocca i segnali durante l'inizializzazione UI
        self.custom_shape_imported = None                                                       # Conserva la Shape importata da file STEP/FCStd
        self.faccia_punto_locale = None                                                         # Punto centro faccia selezionata (relativo al centro torretta)
        self.faccia_normale_locale = FreeCAD.Vector(-1.0, 0.0, 0.0)                             # Normale uscente della faccia selezionata sulla torretta
        self.saldati_temp = {}                                                                  # Dizionario di lavoro degli utensili saldati
        self.stato_originale_utensili = {}                                                      # Backup di OffsetTorretta/Rotazioni per eventuale Cancel

        doc = FreeCAD.ActiveDocument                                                            # Ottiene il documento attivo
        self.pulisci_anteprima_torretta(doc)                                                    # Rimuove eventuali anteprime residue
        self.salva_backup_utensili(doc)                                                         # Salva lo stato iniziale degli utensili del magazzino

        if self.edit_obj and hasattr(self.edit_obj, "ViewObject") and self.edit_obj.ViewObject: # Se esiste già una torretta
            self.edit_obj.ViewObject.Visibility = False                                         # Nasconde l'originale per mostrare l'anteprima live

        self.form = QtWidgets.QWidget()                                                         # Crea il contenitore principale della UI
        self.form.setMinimumWidth(240)                                                          # Imposta una larghezza minima contenuta per non tagliare a destra
        self.layout = QtWidgets.QVBoxLayout(self.form)                                          # Layout verticale principale
        self.layout.setContentsMargins(4, 4, 4, 4)                                              # Riduce i margini esterni per recuperare spazio orizzontale

        self.grp_db = QtWidgets.QGroupBox("Archivio Torrette (Salva / Richiama)")               # Gruppo database torrette su disco
        self.lyt_db = QtWidgets.QVBoxLayout(self.grp_db)                                        # Layout verticale archivio
        self.db_combo = QtWidgets.QComboBox()                                                   # Tendina torrette salvate su riga intera
        self.db_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.db_combo.setMinimumContentsLength(10)                                              # Lunghezza minima compatta
        self.lyt_db.addWidget(self.db_combo)                                                    # Aggiunge la tendina su tutta la larghezza

        self.lyt_db_btns = QtWidgets.QHBoxLayout()                                              # Seconda riga dedicata ai pulsanti Carica ed Elimina
        self.btn_load_db = QtWidgets.QPushButton("Carica Torretta")                             # Pulsante carica da archivio
        self.btn_load_db.clicked.connect(self.carica_torretta_da_db)                            # Collega il caricamento
        self.btn_del_db = QtWidgets.QPushButton("Elimina")                                      # Pulsante elimina da archivio
        self.btn_del_db.clicked.connect(self.elimina_torretta_da_db)                            # Collega l'eliminazione
        self.lyt_db_btns.addWidget(self.btn_load_db)                                            # Aggiunge il pulsante Carica
        self.lyt_db_btns.addWidget(self.btn_del_db)                                             # Aggiunge il pulsante Elimina
        self.lyt_db.addLayout(self.lyt_db_btns)                                                 # Inserisce la riga pulsanti nel gruppo

        self.lyt_name_form = QtWidgets.QFormLayout()                                            # Form layout per il campo Nome
        self.name_input = QtWidgets.QLineEdit("Torretta Ottagonale 150")                        # Nome della configurazione torretta
        self.lyt_name_form.addRow("Nome:", self.name_input)                                     # Riga Nome su tutta la larghezza disponibile
        self.lyt_db.addLayout(self.lyt_name_form)                                               # Aggiunge al gruppo archivio

        self.chk_show_turret = QtWidgets.QCheckBox("Mostra Torretta 3D nella vista")            # Checkbox su riga dedicata per non tagliare a destra
        self.chk_show_turret.setChecked(True)                                                   # Visibile di default
        self.chk_show_turret.stateChanged.connect(self.trigger_update)                          # Aggiorna subito la visibilità
        self.lyt_db.addWidget(self.chk_show_turret)                                             # Aggiunge la checkbox al gruppo

        self.chk_save_db = QtWidgets.QCheckBox("Salva in Archivio Permanente all'OK")           # Testo compatto per salvataggio su disco
        self.chk_save_db.setChecked(True)                                                       # Attivo di default
        self.lyt_db.addWidget(self.chk_save_db)                                                 # Aggiunge al gruppo archivio
        self.layout.addWidget(self.grp_db)                                                      # Aggiunge il gruppo al layout principale

        self.tabs = QtWidgets.QTabWidget()                                                      # Schede principali compatte

        self.tab_turret = QtWidgets.QWidget()                                                   # SCHEDA 1: Costruzione, Cinematica e Collisioni Torretta
        self.lyt_turret = QtWidgets.QVBoxLayout(self.tab_turret)                                # Layout verticale Scheda 1

        self.grp_mode = QtWidgets.QGroupBox("Geometria Plateau Torretta")                       # Gruppo parametri geometrici del plateau
        self.lyt_mode = QtWidgets.QFormLayout(self.grp_mode)                                    # Form layout per le quote

        self.mode_combo = QtWidgets.QComboBox()                                                 # Scelta Parametrica (Ottagonale) o Custom STEP
        self.mode_combo.addItems(["Parametrica (Sedi Frontali)", "Custom (STEP / FCStd)"])      # Voci compatte
        self.mode_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.mode_combo.setMinimumContentsLength(10)                                            # Lunghezza minima ridotta
        self.num_pos_spin = QtWidgets.QSpinBox(); self.num_pos_spin.setRange(3, 36); self.num_pos_spin.setValue(8) # Default 8 posizioni
        self.diam_spin = QtWidgets.QDoubleSpinBox(); self.diam_spin.setRange(30.0, 1000.0); self.diam_spin.setValue(150.0) # Default 150 mm
        self.spess_spin = QtWidgets.QDoubleSpinBox(); self.spess_spin.setRange(10.0, 300.0); self.spess_spin.setValue(40.0) # Default 40 mm
        self.inc_w_spin = QtWidgets.QDoubleSpinBox(); self.inc_w_spin.setRange(0.0, 100.0); self.inc_w_spin.setValue(12.0) # Default 12 mm
        self.inc_p_spin = QtWidgets.QDoubleSpinBox(); self.inc_p_spin.setRange(0.0, 100.0); self.inc_p_spin.setValue(12.0) # Default 12 mm

        self.btn_import_step = QtWidgets.QPushButton("Importa Plateau 3D (STEP/FCStd)")         # Pulsante compatto per importare STEP torretta
        self.btn_import_step.clicked.connect(self.importa_step_torretta)                        # Collega l'importazione del file 3D

        self.lyt_mode.addRow("Tipo Plateau:", self.mode_combo)                                  # Riga Tipo Plateau
        self.lyt_mode.addRow("N° Posizioni (Lati):", self.num_pos_spin)                         # Riga Numero Posizioni
        self.lyt_mode.addRow("Diametro (mm):", self.diam_spin)                                  # Riga Diametro 150 mm
        self.lyt_mode.addRow("Spessore (mm):", self.spess_spin)                                 # Riga Spessore
        self.lyt_mode.addRow("Larghezza Sede (mm):", self.inc_w_spin)                           # Riga Larghezza Sede
        self.lyt_mode.addRow("Profondità Sede (mm):", self.inc_p_spin)                          # Riga Profondità Sede
        self.lyt_mode.addRow(self.btn_import_step)                                              # Riga pulsante importa STEP
        self.lyt_turret.addWidget(self.grp_mode)                                                # Aggiunge il gruppo alla Scheda 1

        self.grp_pos = QtWidgets.QGroupBox("Posizione, Cinematica e Collisioni")                # Gruppo distanza dal WCS e test cinematico
        self.lyt_pos = QtWidgets.QFormLayout(self.grp_pos)                                      # Form layout posizione

        self.dist_x_spin = QtWidgets.QDoubleSpinBox(); self.dist_x_spin.setRange(-2000.0, 2000.0); self.dist_x_spin.setValue(25.0)
        self.dist_y_spin = QtWidgets.QDoubleSpinBox(); self.dist_y_spin.setRange(-2000.0, 2000.0); self.dist_y_spin.setValue(0.0)
        self.dist_z_spin = QtWidgets.QDoubleSpinBox(); self.dist_z_spin.setRange(-2000.0, 2000.0); self.dist_z_spin.setValue(25.0)

        self.t_mir_x = QtWidgets.QCheckBox("Specchia X")                                        # Specchiatura X del plateau
        self.t_mir_y = QtWidgets.QCheckBox("Specchia Y")                                        # Specchiatura Y del plateau
        self.t_rx_spin = QtWidgets.QDoubleSpinBox(); self.t_rx_spin.setRange(-360, 360); self.t_rx_spin.setSingleStep(5)
        self.t_ry_spin = QtWidgets.QDoubleSpinBox(); self.t_ry_spin.setRange(-360, 360); self.t_ry_spin.setSingleStep(5)
        self.t_rz_spin = QtWidgets.QDoubleSpinBox(); self.t_rz_spin.setRange(-360, 360); self.t_rz_spin.setSingleStep(5)
        self.active_stat_spin = QtWidgets.QSpinBox(); self.active_stat_spin.setRange(1, 36); self.active_stat_spin.setValue(1)

        self.btn_go_wcs = QtWidgets.QPushButton("Porta Punta Attiva su Zero WCS (0, 0)")        # Test cinematico: porta la punta attiva in (0,0)
        self.btn_go_wcs.clicked.connect(self.porta_punta_attiva_su_wcs)                         # Collega il movimento a Zero Pezzo
        self.btn_go_home = QtWidgets.QPushButton("Porta a Quota Cambio Utensile (Home)")        # Test cinematico: ritira alla quota di cambio utensile
        self.btn_go_home.clicked.connect(self.porta_torretta_a_home)                            # Collega il ritorno a Home
        self.btn_check_coll = QtWidgets.QPushButton("Verifica Collisioni 3D con Grezzo/Mandrino") # Controllo collisioni booleano
        self.btn_check_coll.clicked.connect(self.verifica_collisioni_3d)                        # Collega il controllo collisioni

        self.lbl_coll_status = QtWidgets.QLabel("Stato Cinematica: Pronta.")                    # Etichetta esito collisioni / cinematica
        self.lbl_coll_status.setWordWrap(True)                                                  # Va a capo automaticamente
        self.lbl_coll_status.setStyleSheet("color: #55FF55; font-weight: bold;")                # Verde di default

        self.lyt_pos.addRow("Distanza X da WCS (mm):", self.dist_x_spin)                        # Riga distanza X
        self.lyt_pos.addRow("Offset Y da WCS (mm):", self.dist_y_spin)                          # Riga offset Y
        self.lyt_pos.addRow("Distanza Z da WCS (mm):", self.dist_z_spin)                        # Riga distanza Z
        self.lyt_pos.addRow(self.t_mir_x, self.t_mir_y)                                         # Riga specchiature
        self.lyt_pos.addRow("Rotazione X (°):", self.t_rx_spin)                                 # Riga Rotazione X
        self.lyt_pos.addRow("Rotazione Y (°):", self.t_ry_spin)                                 # Riga Rotazione Y
        self.lyt_pos.addRow("Rotazione Z (°):", self.t_rz_spin)                                 # Riga Rotazione Z
        self.lyt_pos.addRow("Stazione Attiva (Index):", self.active_stat_spin)                  # Riga indexaggio stazione attiva
        self.lyt_pos.addRow(self.btn_go_wcs)                                                    # Riga pulsante Punta su WCS
        self.lyt_pos.addRow(self.btn_go_home)                                                   # Riga pulsante Torretta a Home
        self.lyt_pos.addRow(self.btn_check_coll)                                                # Riga pulsante Verifica Collisioni
        self.lyt_pos.addRow(self.lbl_coll_status)                                               # Riga esito collisioni
        self.lyt_turret.addWidget(self.grp_pos)                                                 # Aggiunge il gruppo posizione alla Scheda 1

        self.tabs.addTab(self.tab_turret, "1. Plateau & Test")                                  # Titolo scheda compatto

        self.tab_mount = QtWidgets.QWidget()                                                    # SCHEDA 2: Montaggio Automatico e Manuale Utensili
        self.lyt_mount = QtWidgets.QVBoxLayout(self.tab_mount)                                  # Layout verticale Scheda 2

        self.grp_sel_tool = QtWidgets.QGroupBox("Selezione e Posizionamento Rapido")            # Gruppo scelta utensile e auto-montaggio
        self.lyt_sel_tool = QtWidgets.QFormLayout(self.grp_sel_tool)                            # Form layout

        self.mount_tool_combo = QtWidgets.QComboBox()                                           # Tendina con gli utensili presenti in Magazzino Utensili
        self.mount_tool_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.mount_tool_combo.setMinimumContentsLength(10)

        self.btn_auto_slot = QtWidgets.QPushButton("Auto-Posiziona sulla sua Sede [Txx]")       # Incastra automaticamente l'utensile nella sua stazione T
        self.btn_auto_slot.clicked.connect(self.auto_posiziona_su_sua_stazione)                 # Collega l'auto-posizionamento singolo

        self.btn_auto_all = QtWidgets.QPushButton("Monta e Salda TUTTO il Magazzino (Auto)")    # Monta e salda in automatico tutti gli utensili del magazzino
        self.btn_auto_all.setStyleSheet("font-weight: bold; background-color: #1E4D6B; color: white; padding: 4px;")
        self.btn_auto_all.clicked.connect(self.monta_e_salda_tutto_il_magazzino)                # Collega il montaggio automatico totale

        self.btn_pick_face = QtWidgets.QPushButton("1. Oppure Clicca Faccia 3D sulla Torretta") # Cattura manuale di una qualsiasi faccia 3D
        self.btn_pick_face.clicked.connect(self.cattura_faccia_torretta)                        # Collega la cattura della faccia 3D

        self.sporgenza_spin = QtWidgets.QDoubleSpinBox()                                        # Distanza tra punta utensile e faccia esterna torretta
        self.sporgenza_spin.setRange(-500.0, 500.0); self.sporgenza_spin.setSingleStep(1.0); self.sporgenza_spin.setValue(28.0)

        self.lbl_mount_status = QtWidgets.QLabel("Stato: Scegli un utensile o usa Auto-Posiziona.") # Etichetta guida
        self.lbl_mount_status.setWordWrap(True)                                                 # Va a capo senza allargare il pannello
        self.lbl_mount_status.setStyleSheet("color: #FFAA00; font-weight: bold;")               # Colore evidenziato

        self.lyt_sel_tool.addRow("Utensile:", self.mount_tool_combo)                            # Riga scelta utensile
        self.lyt_sel_tool.addRow(self.btn_auto_slot)                                            # Riga auto-posiziona singolo
        self.lyt_sel_tool.addRow(self.btn_auto_all)                                             # Riga auto-monta tutto il magazzino
        self.lyt_sel_tool.addRow(self.btn_pick_face)                                            # Riga pulsante selezione faccia manuale
        self.lyt_sel_tool.addRow("2. Dist. Punta-Faccia (mm):", self.sporgenza_spin)            # Riga sporgenza punta dalla faccia esterna
        self.lyt_sel_tool.addRow(self.lbl_mount_status)                                         # Riga stato
        self.lyt_mount.addWidget(self.grp_sel_tool)                                             # Aggiunge alla Scheda 2

        self.grp_adj = QtWidgets.QGroupBox("3. Regolazione Fine e Saldatura Utensile")          # Regolazione fine sull'incavo
        self.lyt_adj = QtWidgets.QFormLayout(self.grp_adj)                                      # Form layout regolazioni

        self.m_tx_spin = QtWidgets.QDoubleSpinBox(); self.m_tx_spin.setRange(-500, 500); self.m_tx_spin.setSingleStep(1.0)
        self.m_ty_spin = QtWidgets.QDoubleSpinBox(); self.m_ty_spin.setRange(-500, 500); self.m_ty_spin.setSingleStep(1.0)
        self.m_tz_spin = QtWidgets.QDoubleSpinBox(); self.m_tz_spin.setRange(-500, 500); self.m_tz_spin.setSingleStep(1.0)
        self.m_mir_x = QtWidgets.QCheckBox("Specchia X")                                        # Specchia utensile su X
        self.m_mir_y = QtWidgets.QCheckBox("Specchia Y")                                        # Specchia utensile su Y
        self.m_rx_spin = QtWidgets.QDoubleSpinBox(); self.m_rx_spin.setRange(-360, 360); self.m_rx_spin.setSingleStep(5.0)
        self.m_ry_spin = QtWidgets.QDoubleSpinBox(); self.m_ry_spin.setRange(-360, 360); self.m_ry_spin.setSingleStep(5.0)
        self.m_rz_spin = QtWidgets.QDoubleSpinBox(); self.m_rz_spin.setRange(-360, 360); self.m_rz_spin.setSingleStep(5.0)

        self.btn_weld_tool = QtWidgets.QPushButton("4. Salda Utensile sulla Torretta")          # Pulsante per saldare la posizione dell'utensile
        self.btn_weld_tool.setStyleSheet("font-weight: bold; background-color: #2E5A27; color: white; padding: 5px;")
        self.btn_weld_tool.clicked.connect(self.salda_utensile_corrente)                        # Collega la funzione di saldatura

        self.btn_unweld_tool = QtWidgets.QPushButton("Scollega / Smonta Utensile dalla Torretta") # Pulsante per smontare l'utensile corrente
        self.btn_unweld_tool.clicked.connect(self.scollega_utensile_corrente)                   # Collega la funzione di smontaggio

        self.lyt_adj.addRow("Trasla X (mm):", self.m_tx_spin)                                   # Riga Traslazione X
        self.lyt_adj.addRow("Trasla Y (mm):", self.m_ty_spin)                                   # Riga Traslazione Y
        self.lyt_adj.addRow("Trasla Z (mm):", self.m_tz_spin)                                   # Riga Traslazione Z
        self.lyt_adj.addRow(self.m_mir_x, self.m_mir_y)                                         # Riga Specchiatura X e Y
        self.lyt_adj.addRow("Ruota X (°):", self.m_rx_spin)                                     # Riga Rotazione X
        self.lyt_adj.addRow("Ruota Y (°):", self.m_ry_spin)                                     # Riga Rotazione Y
        self.lyt_adj.addRow("Ruota Z (°):", self.m_rz_spin)                                     # Riga Rotazione Z
        self.lyt_adj.addRow(self.btn_weld_tool)                                                 # Riga pulsante Salda Utensile
        self.lyt_adj.addRow(self.btn_unweld_tool)                                               # Riga pulsante Scollega Utensile
        self.lyt_mount.addWidget(self.grp_adj)                                                  # Aggiunge alla Scheda 2

        self.tabs.addTab(self.tab_mount, "2. Montaggio")                                        # Titolo scheda compatto
        self.layout.addWidget(self.tabs)                                                        # Aggiunge il blocco schede al layout principale
        self.form.setLayout(self.layout)                                                        # Applica il layout al widget principale

        self.preview_turret = doc.addObject("Part::Feature", "TMP_Turret_Preview")              # Crea l'oggetto temporaneo per l'anteprima torretta
        self.preview_turret.Label = "ANTEPRIMA TORRETTA (Provvisorio)"                          # Etichetta provvisoria
        self.preview_turret.ViewObject.ShapeColor = (0.25, 0.28, 0.32)                          # Colore grigio antracite

        self.aggiorna_combo_db()                                                                # Popola la lista delle torrette salvate su disco

        if self.edit_obj:                                                                       # Se stiamo modificando una torretta già presente
            self.carica_dati_da_oggetto(self.edit_obj)                                          # Ripristina tutte le quote e gli utensili saldati

        self.popola_combo_utensili_magazzino(doc)                                               # Popola il combo utensili mostrando [SALDATO] dove presente
        self.mount_tool_combo.currentIndexChanged.connect(self.on_mount_tool_selected)          # Collega il cambio utensile nella Scheda 2

        self.mode_combo.currentIndexChanged.connect(self.aggiorna_ui_modalita)                  # Collega cambio modalità Parametrica/Custom
        self.num_pos_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio numero posizioni
        self.diam_spin.valueChanged.connect(self.trigger_update)                                # Collega cambio diametro
        self.spess_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio spessore
        self.inc_w_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio larghezza incavo
        self.inc_p_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio profondità incavo
        self.dist_x_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio distanza X dal WCS
        self.dist_y_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio offset Y dal WCS
        self.dist_z_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio distanza Z dal WCS
        self.t_mir_x.stateChanged.connect(self.trigger_update)                                  # Collega specchiatura X torretta
        self.t_mir_y.stateChanged.connect(self.trigger_update)                                  # Collega specchiatura Y torretta
        self.t_rx_spin.valueChanged.connect(self.trigger_update)                                # Collega rotazione X torretta
        self.t_ry_spin.valueChanged.connect(self.trigger_update)                                # Collega rotazione Y torretta
        self.t_rz_spin.valueChanged.connect(self.trigger_update)                                # Collega rotazione Z torretta
        self.active_stat_spin.valueChanged.connect(self.trigger_update)                         # Collega cambio stazione attiva

        self.sporgenza_spin.valueChanged.connect(self.aggiorna_anteprima_montaggio_utensile)    # Collega cambio distanza punta-faccia
        self.m_tx_spin.valueChanged.connect(self.aggiorna_anteprima_montaggio_utensile)         # Collega traslazione X utensile
        self.m_ty_spin.valueChanged.connect(self.aggiorna_anteprima_montaggio_utensile)         # Collega traslazione Y utensile
        self.m_tz_spin.valueChanged.connect(self.aggiorna_anteprima_montaggio_utensile)         # Collega traslazione Z utensile
        self.m_mir_x.stateChanged.connect(self.aggiorna_anteprima_montaggio_utensile)           # Collega specchiatura X utensile
        self.m_mir_y.stateChanged.connect(self.aggiorna_anteprima_montaggio_utensile)           # Collega specchiatura Y utensile
        self.m_rx_spin.valueChanged.connect(self.aggiorna_anteprima_montaggio_utensile)         # Collega rotazione X utensile
        self.m_ry_spin.valueChanged.connect(self.aggiorna_anteprima_montaggio_utensile)         # Collega rotazione Y utensile
        self.m_rz_spin.valueChanged.connect(self.aggiorna_anteprima_montaggio_utensile)         # Collega rotazione Z utensile

        self.is_updating = False                                                                # Sblocca gli aggiornamenti
        self.aggiorna_ui_modalita()                                                             # Adatta i controlli e disegna l'anteprima 3D
        self.on_mount_tool_selected()                                                           # Allinea i controlli per il primo utensile in lista

    def auto_posiziona_su_sua_stazione(self):                                                   # Posiziona automaticamente l'utensile scelto nella sua sede Txx
        tool_obj = self.get_selected_mount_tool()                                               # Ottiene l'utensile corrente
        if not tool_obj:                                                                        # Verifica validità
            return                                                                              # Esce
        num_st = int(getattr(tool_obj, "NumeroStazione", 1))                                    # Legge l'indice numerico della stazione (es. T03 -> 3)
        pt_loc, norm_loc = calcola_dati_sede_da_indice(                                         # Calcola matematicamente centro e normale della sede
            num_st, self.num_pos_spin.value(), self.diam_spin.value(), self.inc_p_spin.value()  # Parametri geometrici del plateau
        )                                                                                       # Fine calcolo sede
        self.faccia_punto_locale = pt_loc                                                       # Imposta il punto di riferimento sulla sede calcolata
        self.faccia_normale_locale = norm_loc                                                   # Imposta la normale radiale uscente della sede

        tipo_ut = str(getattr(tool_obj, "TipoLavorazione", "Esterno (ISO)"))                    # Verifica se è un utensile assiale (punta, fresa, maschio)
        if tipo_ut in ["Punta da Trapano", "Fresa", "Maschio"] and abs(self.m_ry_spin.value()) < 0.1 and abs(self.m_rx_spin.value()) < 0.1:
            self.is_updating = True                                                             # Orienta la punta verso il mandrino (-Z) se era ancora a 0°
            self.m_ry_spin.setValue(180.0)                                                      # Ruota di 180° su Y così la punta guarda -Z (verso l'autocentrante)
            self.is_updating = False                                                            # Sblocca

        self.aggiorna_anteprima_montaggio_utensile()                                            # Muove e ruota l'utensile nella sua sede
        self.lbl_mount_status.setText(f"[{tool_obj.Label}] posizionato sulla Sede T{num_st:02d}! Premi 4. Salda.")

    def monta_e_salda_tutto_il_magazzino(self):                                                 # Monta e salda automaticamente tutti gli utensili del Magazzino
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc: return                                                                      # Controllo sicurezza
        lib = doc.getObject("Libreria_Utensili")                                                # Gruppo Magazzino Utensili
        if not lib or not hasattr(lib, "Group") or not lib.Group:                               # Se non ci sono utensili
            self.lbl_mount_status.setText("Nessun utensile presente nel Magazzino Utensili!")   # Avvisa
            return                                                                              # Esce

        n_pos = self.num_pos_spin.value()                                                       # Numero stazioni torretta
        diam = self.diam_spin.value()                                                           # Diametro plateau
        prof = self.inc_p_spin.value()                                                          # Profondità sede frontale
        sporg = float(self.sporgenza_spin.value())                                              # Sporgenza punta standard

        for t_obj in lib.Group:                                                                 # Cicla su tutti gli utensili del magazzino
            num_st = int(getattr(t_obj, "NumeroStazione", 1))                                   # Legge la stazione T assegnata all'utensile
            pt_loc, norm_loc = calcola_dati_sede_da_indice(num_st, n_pos, diam, prof)           # Calcola posizione e angolo della sede corrispondente
            tipo_ut = str(getattr(t_obj, "TipoLavorazione", "Esterno (ISO)"))                   # Legge il tipo di utensile
            rx = float(getattr(t_obj, "RotX", 0.0))                                             # Rotazione X attuale
            ry = float(getattr(t_obj, "RotY", 0.0))                                             # Rotazione Y attuale
            rz = float(getattr(t_obj, "RotZ", 0.0))                                             # Rotazione Z attuale
            if tipo_ut in ["Punta da Trapano", "Fresa", "Maschio"] and abs(rx) < 0.1 and abs(ry) < 0.1:
                ry = 180.0                                                                      # Orienta le punte verso il mandrino (-Z)
            rel_pos = pt_loc + (norm_loc * sporg)                                               # Posizione della punta rispetto al centro torretta
            self.saldati_temp[t_obj.Name] = {                                                   # Registra la saldatura per l'utensile
                "label": t_obj.Label,                                                           # Etichetta
                "rel_pos": [rel_pos.x, rel_pos.y, rel_pos.z],                                   # Posizione relativa punta
                "faccia_pt": [pt_loc.x, pt_loc.y, pt_loc.z],                                    # Punto base sede
                "faccia_norm": [norm_loc.x, norm_loc.y, norm_loc.z],                            # Normale sede
                "sporgenza": sporg,                                                             # Sporgenza
                "tx": 0.0, "ty": 0.0, "tz": 0.0,                                                # Traslazioni fini
                "mx": bool(getattr(t_obj, "SpecchiaX", False)),                                 # Specchia X
                "my": bool(getattr(t_obj, "SpecchiaY", False)),                                 # Specchia Y
                "rx": rx, "ry": ry, "rz": rz                                                    # Rotazioni
            }                                                                                   # Fine record

        self.popola_combo_utensili_magazzino(doc)                                               # Aggiorna le diciture [SALDATO] nella tendina
        self.aggiorna_visibilita_utensili_montaggio()                                           # Rende visibili tutti gli utensili montati
        self.trigger_update()                                                                   # Posiziona e ruota tutti gli utensili sulla torretta 3D
        self.on_mount_tool_selected()                                                           # Allinea i controlli UI sull'utensile corrente
        self.lbl_mount_status.setText(f"Montati e saldati automaticamente {len(lib.Group)} utensili!")

    def porta_punta_attiva_su_wcs(self):                                                        # Sposta l'anteprima torretta portando la punta attiva su (0,0) WCS
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        st_curr = self.active_stat_spin.value()                                                 # Stazione attiva corrente
        rel_vec_attivo = None                                                                   # Vettore relativo della punta attiva
        for t_name, info in self.saldati_temp.items():                                          # Cerca l'utensile saldato sulla stazione attiva
            t_obj = doc.getObject(t_name) if doc else None                                      # Oggetto utensile
            if t_obj and int(getattr(t_obj, "NumeroStazione", -1)) == st_curr:                  # Se corrisponde alla stazione attiva
                rel_vec_attivo = FreeCAD.Vector(*info.get("rel_pos", [0.0, 0.0, 0.0]))          # Trovato vettore relativo
                break                                                                           # Esce
        if rel_vec_attivo is None and self.saldati_temp:                                        # Fallback sul primo utensile saldato
            first_info = next(iter(self.saldati_temp.values()))                                 # Primo record
            rel_vec_attivo = FreeCAD.Vector(*first_info.get("rel_pos", [0.0, 0.0, 0.0]))        # Vettore relativo

        _, rot_tot = self.calcola_centro_e_rotazione_correnti()                                 # Rotazione attuale della torretta
        r_ing = (self.diam_spin.value() / 2.0) if self.mode_combo.currentIndex() == 0 else 0.0  # Raggio d'ingombro
        self.is_updating = True                                                                 # Sospende segnali multipli
        if rel_vec_attivo is not None:                                                          # Se c'è un utensile saldato
            offset_punta = rot_tot.multVec(rel_vec_attivo)                                      # Vettore centro torretta -> punta attiva
            self.dist_x_spin.setValue(-offset_punta.x - r_ing)                                  # Porta la punta a X = 0 sul WCS
            self.dist_z_spin.setValue(-offset_punta.z)                                          # Porta la punta a Z = 0 sul WCS
            self.lbl_coll_status.setText(f"Punta Stazione {st_curr} portata esattamente su Zero WCS (0, 0).")
        else:                                                                                   # Se non ci sono ancora utensili saldati
            self.dist_x_spin.setValue(0.0)                                                      # Porta la faccia torretta a X = 0
            self.dist_z_spin.setValue(0.0)                                                      # Porta la faccia torretta a Z = 0
            self.lbl_coll_status.setText("Torretta portata su Zero WCS (nessun utensile saldato).")
        self.is_updating = False                                                                # Sblocca
        self.trigger_update()                                                                   # Aggiorna il 3D

    def porta_torretta_a_home(self):                                                            # Ritira la torretta alle quote CambioUtensile di Setup_Macchina
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        hx, hz = 50.0, 50.0                                                                     # Valori di sicurezza predefiniti
        if doc and doc.getObject("Setup_Macchina"):                                             # Legge le quote dal Setup_Macchina se presenti
            setup_obj = doc.getObject("Setup_Macchina")                                         # Oggetto Setup
            hx = float(getattr(setup_obj, "CambioUtensileX", 50.0))                             # Quota X cambio utensile
            hz = float(getattr(setup_obj, "CambioUtensileZ", 50.0))                             # Quota Z cambio utensile
        self.is_updating = True                                                                 # Sospende aggiornamenti multipli
        self.dist_x_spin.setValue(hx)                                                           # Imposta Distanza X
        self.dist_z_spin.setValue(hz)                                                           # Imposta Distanza Z
        self.is_updating = False                                                                # Sblocca
        self.lbl_coll_status.setStyleSheet("color: #55FF55; font-weight: bold;")                # Colore verde
        self.lbl_coll_status.setText(f"Torretta ritirata a Home / Cambio Utensile (X={hx}, Z={hz}).")
        self.trigger_update()                                                                   # Aggiorna il 3D

    def verifica_collisioni_3d(self):                                                           # Controlla collisioni booleane tra Torretta+Utensili e Grezzo+Mandrino
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc or not doc.getObject("Grezzo_Macchina"):                                     # Verifica presenza del Grezzo_Macchina
            self.lbl_coll_status.setStyleSheet("color: #FFAA00; font-weight: bold;")            # Giallo avviso
            self.lbl_coll_status.setText("Avviso: Definisci prima il Grezzo per verificare le collisioni!")
            return                                                                              # Esce
        stock_obj = doc.getObject("Grezzo_Macchina")                                            # Oggetto Grezzo + Autocentrante + Contropunta
        if not hasattr(stock_obj, "Shape") or stock_obj.Shape.isNull():                         # Verifica validità Shape del grezzo
            return                                                                              # Esce

        collisioni = []                                                                         # Lista degli elementi che vanno in collisione
        if self.preview_turret and hasattr(self.preview_turret, "Shape") and not self.preview_turret.Shape.isNull():
            try:                                                                                # Verifica collisione del disco/plateau torretta
                com_t = self.preview_turret.Shape.common(stock_obj.Shape)                       # Intersezione booleana 3D
                if com_t.Volume > 0.01:                                                         # Se c'è compenetrazione reale (> 0.01 mm³)
                    collisioni.append("Corpo Torretta")                                         # Segnala collisione del plateau
            except Exception: pass                                                              # Ignora errori geometrici

        for t_name in self.saldati_temp.keys():                                                 # Verifica collisione di ciascun utensile saldato
            t_obj = doc.getObject(t_name)                                                       # Oggetto utensile
            if t_obj and hasattr(t_obj, "Shape") and not t_obj.Shape.isNull():                  # Se ha una Shape valida
                try:                                                                            # Intersezione booleana tra utensile e Grezzo/Mandrino
                    com_u = t_obj.Shape.common(stock_obj.Shape)                                 # Calcola il volume di interferenza
                    if com_u.Volume > 0.01:                                                     # Se l'utensile tocca il grezzo o le griffe
                        collisioni.append(t_obj.Label)                                          # Aggiunge il nome dell'utensile in collisione
                except Exception: pass                                                          # Ignora errori

        if collisioni:                                                                          # Se è stata rilevata almeno una collisione
            elenco = ", ".join(collisioni)                                                      # Formatta i nomi in collisione
            self.lbl_coll_status.setStyleSheet("color: #FF4444; font-weight: bold;")            # Colore Rosso allarme
            self.lbl_coll_status.setText(f"COLLISIONE RILEVATA: [{elenco}] tocca Grezzo/Mandrino!")
        else:                                                                                   # Se non c'è nessuna interferenza
            self.lbl_coll_status.setStyleSheet("color: #55FF55; font-weight: bold;")            # Colore Verde OK
            self.lbl_coll_status.setText("NESSUNA COLLISIONE: Torretta e utensili sono in sicurezza.")

    def salva_backup_utensili(self, doc):                                                       # Memorizza la posizione iniziale degli utensili per Cancel
        if not doc: return                                                                      # Verifica esistenza documento
        lib = doc.getObject("Libreria_Utensili")                                                # Cerca il Magazzino Utensili
        if lib and hasattr(lib, "Group"):                                                       # Se esiste ed ha utensili
            for t in lib.Group:                                                                 # Scorre ogni utensile
                self.stato_originale_utensili[t.Name] = {                                       # Salva una copia dei parametri di posizionamento
                    "OffsetTorretta": FreeCAD.Vector(getattr(t, "OffsetTorretta", FreeCAD.Vector(0, 0, 0))),
                    "RotazioneTorretta": list(getattr(t, "RotazioneTorretta", [0.0, 0.0, 0.0, 1.0])),
                    "RotX": float(getattr(t, "RotX", 0.0)),
                    "RotY": float(getattr(t, "RotY", 0.0)),
                    "RotZ": float(getattr(t, "RotZ", 0.0)),
                    "SpecchiaX": bool(getattr(t, "SpecchiaX", False)),
                    "SpecchiaY": bool(getattr(t, "SpecchiaY", False)),
                    "Visibility": bool(t.ViewObject.Visibility) if hasattr(t, "ViewObject") and t.ViewObject else True
                }                                                                               # Fine dizionario backup

    def popola_combo_utensili_magazzino(self, doc):                                             # Carica nel combo della Scheda 2 gli utensili del Magazzino
        curr_data = self.mount_tool_combo.itemData(self.mount_tool_combo.currentIndex()) if self.mount_tool_combo.count() > 0 else None
        self.mount_tool_combo.blockSignals(True)                                                # Sospende i segnali del combo
        self.mount_tool_combo.clear()                                                           # Svuota il menu a tendina
        if doc:                                                                                 # Se il documento è attivo
            lib = doc.getObject("Libreria_Utensili")                                            # Cerca il gruppo Magazzino Utensili
            if lib and hasattr(lib, "Group") and lib.Group:                                     # Se ci sono utensili nel magazzino
                for t in lib.Group:                                                             # Cicla sugli utensili
                    st = getattr(t, "Stazione", "T01")                                          # Legge la stazione dell'utensile
                    stato_weld = " [SALDATO]" if t.Name in self.saldati_temp else ""            # Aggiunge l'indicatore se è già saldato
                    self.mount_tool_combo.addItem(f"[{st}] {t.Label}{stato_weld}", t.Name)      # Aggiunge voce
            else:                                                                               # Se il magazzino è vuoto
                self.mount_tool_combo.addItem("(Nessun utensile nel Magazzino)", "")            # Mostra avviso
        if curr_data:                                                                           # Ripristina selezione
            idx = self.mount_tool_combo.findData(curr_data)
            if idx >= 0: self.mount_tool_combo.setCurrentIndex(idx)
        self.mount_tool_combo.blockSignals(False)                                               # Riabilita i segnali

    def aggiorna_visibilita_utensili_montaggio(self):                                           # Mostra tutti i saldati + l'utensile attualmente selezionato
        doc = FreeCAD.ActiveDocument                                                            # Ottiene il documento attivo
        if not doc: return                                                                      # Controllo sicurezza
        lib = doc.getObject("Libreria_Utensili")                                                # Cerca il Magazzino Utensili
        if not lib or not hasattr(lib, "Group"): return                                         # Se non esiste esce
        sel_tool = self.get_selected_mount_tool()                                               # Utensile attualmente selezionato
        sel_name = sel_tool.Name if sel_tool else ""                                            # Nome dell'utensile selezionato
        for t in lib.Group:                                                                     # Scorre tutti gli utensili del magazzino
            if hasattr(t, "ViewObject") and t.ViewObject:                                       # Visibile se saldato o se in lavorazione
                t.ViewObject.Visibility = (t.Name in self.saldati_temp) or (t.Name == sel_name)

    def get_selected_mount_tool(self):                                                          # Restituisce l'oggetto utensile selezionato nella Scheda 2
        doc = FreeCAD.ActiveDocument                                                            # Ottiene il documento attivo
        if not doc or self.mount_tool_combo.count() == 0: return None                           # Verifica validità
        tool_name = self.mount_tool_combo.itemData(self.mount_tool_combo.currentIndex())        # Legge il Name interno
        if tool_name: return doc.getObject(tool_name)                                           # Restituisce l'oggetto FreeCAD
        return None                                                                             # Non trovato

    def on_mount_tool_selected(self):                                                           # Quando si sceglie un utensile da montare nella Scheda 2
        tool_obj = self.get_selected_mount_tool()                                               # Ottiene l'utensile selezionato
        if not tool_obj: return                                                                 # Esce se non valido
        st_str = getattr(tool_obj, "Stazione", "T01")                                           # Legge la sigla stazione (es. T03)
        self.btn_auto_slot.setText(f"Auto-Posiziona sulla sua Sede [{st_str}]")                 # Aggiorna il testo del pulsante automatico
        self.aggiorna_visibilita_utensili_montaggio()                                           # Mostra i saldati + l'utensile scelto
        self.is_updating = True                                                                 # Sospende i segnali mentre aggiorna gli spinbox
        try:                                                                                    # Carica i parametri dell'utensile scelto
            if tool_obj.Name in self.saldati_temp:                                              # CASO A: Utensile già saldato sulla torretta
                info = self.saldati_temp[tool_obj.Name]                                         # Legge i suoi parametri di montaggio salvati
                self.sporgenza_spin.setValue(float(info.get("sporgenza", 28.0)))                # Ripristina la sporgenza punta-faccia
                self.m_tx_spin.setValue(float(info.get("tx", 0.0)))                             # Ripristina traslazione fine X
                self.m_ty_spin.setValue(float(info.get("ty", 0.0)))                             # Ripristina traslazione fine Y
                self.m_tz_spin.setValue(float(info.get("tz", 0.0)))                             # Ripristina traslazione fine Z
                self.m_mir_x.setChecked(bool(info.get("mx", getattr(tool_obj, "SpecchiaX", False))))
                self.m_mir_y.setChecked(bool(info.get("my", getattr(tool_obj, "SpecchiaY", False))))
                self.m_rx_spin.setValue(float(info.get("rx", getattr(tool_obj, "RotX", 0.0))))
                self.m_ry_spin.setValue(float(info.get("ry", getattr(tool_obj, "RotY", 0.0))))
                self.m_rz_spin.setValue(float(info.get("rz", getattr(tool_obj, "RotZ", 0.0))))
                if "faccia_pt" in info and "faccia_norm" in info:                               # Ripristina il riferimento della sua sede
                    self.faccia_punto_locale = FreeCAD.Vector(*info["faccia_pt"])               # Punto centro faccia locale
                    self.faccia_normale_locale = FreeCAD.Vector(*info["faccia_norm"])           # Normale faccia locale
                self.lbl_mount_status.setText(f"[{tool_obj.Label}] è già SALDATO. Puoi ritoccarlo o cambiarne sede.")
            else:                                                                               # CASO B: Nuovo utensile non ancora saldato
                self.faccia_punto_locale = None                                                 # Azzera la faccia precedente
                self.faccia_normale_locale = FreeCAD.Vector(-1.0, 0.0, 0.0)                     # Reset normale di default
                self.sporgenza_spin.setValue(28.0)                                              # Reset sporgenza default 28 mm
                self.m_tx_spin.setValue(0.0); self.m_ty_spin.setValue(0.0); self.m_tz_spin.setValue(0.0)
                self.m_mir_x.setChecked(bool(getattr(tool_obj, "SpecchiaX", False)))
                self.m_mir_y.setChecked(bool(getattr(tool_obj, "SpecchiaY", False)))
                self.m_rx_spin.setValue(float(getattr(tool_obj, "RotX", 0.0)))
                self.m_ry_spin.setValue(float(getattr(tool_obj, "RotY", 0.0)))
                self.m_rz_spin.setValue(float(getattr(tool_obj, "RotZ", 0.0)))
                self.lbl_mount_status.setText(f"[{tool_obj.Label}] pronto: premi 'Auto-Posiziona' o clicca una faccia.")
        finally:                                                                                # Riabilita i segnali
            self.is_updating = False                                                            # Sblocca

    def cattura_faccia_torretta(self):                                                          # Passo 1 Montaggio manuale: Legge la faccia cliccata sulla torretta
        sel_ex = FreeCADGui.Selection.getSelectionEx()                                          # Ottiene la selezione estesa 3D
        if not sel_ex or not sel_ex[0].SubElementNames:                                         # Verifica che sia stata cliccata una faccia
            self.lbl_mount_status.setText("Errore: Clicca prima su una FACCIA della torretta!") # Avvisa l'utente
            return                                                                              # Esce
        sub_name = sel_ex[0].SubElementNames[0]                                                 # Nome del sotto-elemento (es. Face3)
        if not sub_name.startswith("Face"):                                                     # Controlla che sia effettivamente una faccia
            self.lbl_mount_status.setText("Errore: Devi selezionare una FACCIA (non un bordo)!")# Avvisa l'utente
            return                                                                              # Esce

        obj_sel = sel_ex[0].Object                                                              # Oggetto su cui è stata cliccata la faccia
        face = obj_sel.Shape.getElement(sub_name)                                               # Estrae la geometria della faccia
        pt_faccia_glob = face.CenterOfMass                                                      # Centro geometrico della faccia cliccata
        try:                                                                                    # Calcola la normale uscente al centro della faccia
            u_mid, v_mid = face.Surface.parameter(pt_faccia_glob)                               # Parametri UV al centro della faccia
            norm_glob = face.normalAt(u_mid, v_mid)                                             # Vettore normale uscente dalla faccia
        except Exception:                                                                       # Fallback
            norm_glob = face.normalAt(0, 0)                                                     # Normale a (0,0)

        centro_torr, rot_torr = self.calcola_centro_e_rotazione_correnti()                      # Legge centro e rotazione attuali dell'anteprima torretta
        rot_inv = rot_torr.inverted()                                                           # Rotazione inversa per passare al sistema locale della torretta
        pt_loc = rot_inv.multVec(pt_faccia_glob - centro_torr)                                  # Punto della faccia nel sistema locale della torretta
        vec_radiale_xy = FreeCAD.Vector(pt_loc.x, pt_loc.y, 0.0)                                # Vettore radiale nel piano XY della torretta
        if vec_radiale_xy.Length > 0.001:                                                       # Se il punto non è sull'asse centrale
            dir_esterna = rot_torr.multVec(vec_radiale_xy.normalize())                          # Direzione radiale uscente verso la faccia perimetrale
        else:                                                                                   # Fallback lungo -X
            dir_esterna = FreeCAD.Vector(-1.0, 0.0, 0.0)                                        # Direzione verso l'asse mandrino

        if abs(norm_glob.dot(dir_esterna)) > 0.5:                                               # Se è stata selezionata la faccia esterna del poligono
            if norm_glob.dot(dir_esterna) < 0:                                                  # Se la normale punta verso l'interno
                norm_glob = -norm_glob                                                          # La orienta verso l'esterno
            self.faccia_normale_locale = rot_inv.multVec(norm_glob).normalize()                 # Usa la normale alla faccia esterna
            self.faccia_punto_locale = pt_loc                                                   # Usa il centro della faccia cliccata
        else:                                                                                   # Se è stata cliccata la parete o il fondo della sede frontale
            r_ap = self.diam_spin.value() / 2.0                                                 # Raggio della faccia più esterna della torretta
            dir_rad_loc = vec_radiale_xy.normalize() if vec_radiale_xy.Length > 0.001 else FreeCAD.Vector(-1.0, 0.0, 0.0)
            self.faccia_normale_locale = dir_rad_loc                                            # Orienta la sporgenza radialmente fuori dalla sede
            self.faccia_punto_locale = FreeCAD.Vector(dir_rad_loc.x * r_ap, dir_rad_loc.y * r_ap, pt_loc.z)

        FreeCADGui.Selection.clearSelection()                                                   # Pulisce la selezione verde
        self.lbl_mount_status.setText(f"Faccia [{sub_name}] catturata! Regola e premi 4. Salda.")
        self.aggiorna_anteprima_montaggio_utensile()                                            # Posiziona e ruota subito l'utensile sulla sede cliccata

    def calcola_posizione_relativa_utensile(self):                                              # Calcola il vettore punta relativo al centro torretta
        if self.faccia_punto_locale is None:                                                    # Se non è ancora stata cliccata una faccia
            r_ap = self.diam_spin.value() / 2.0                                                 # Usa di default la Sede 1 (orientata verso -X)
            pt_base = FreeCAD.Vector(-r_ap, 0.0, self.inc_p_spin.value() / 2.0)                 # Punto sulla faccia esterna in corrispondenza della sede frontale
            norm_loc = FreeCAD.Vector(-1.0, 0.0, 0.0)                                           # Direzione uscente verso -X
        else:                                                                                   # Se l'utente ha selezionato una faccia specifica
            pt_base = self.faccia_punto_locale                                                  # Parte dal punto sulla faccia esterna della sede selezionata
            norm_loc = self.faccia_normale_locale                                               # Usa la direzione uscente di quella sede

        rot_sede = calcola_rotazione_sede_locale(norm_loc)                                      # Rotazione dell'alloggiamento rispetto alla Sede 1
        sporgenza = float(self.sporgenza_spin.value())                                          # Distanza punta utensile dalla faccia più esterna della torretta
        trasl_fine = FreeCAD.Vector(self.m_tx_spin.value(), self.m_ty_spin.value(), self.m_tz_spin.value())
        trasl_ruotata = rot_sede.multVec(trasl_fine)                                            # Ruota le traslazioni fini lungo gli assi della sede selezionata
        return pt_base + (norm_loc * sporgenza) + trasl_ruotata                                 # Posizione finale della punta rispetto al centro torretta

    def aggiorna_anteprima_montaggio_utensile(self, *args):                                     # Muove e ruota in tempo reale l'utensile sulla sede
        if self.is_updating: return                                                             # Evita esecuzioni durante il caricamento UI
        tool_obj = self.get_selected_mount_tool()                                               # Ottiene l'utensile attivo nella Scheda 2
        if not tool_obj or not hasattr(tool_obj, "OffsetTorretta"): return                      # Verifica validità

        if self.faccia_punto_locale is None and tool_obj.Name not in self.saldati_temp:         # Se non ha ancora una sede assegnata
            return                                                                              # Aspetta Auto-Posiziona o il click sulla faccia

        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        wcs = get_wcs_origin(doc)                                                               # Origine WCS
        centro_torr, rot_torr = self.calcola_centro_e_rotazione_correnti()                      # Centro e rotazione attuali della torretta
        rel_pos = self.calcola_posizione_relativa_utensile()                                    # Posizione relativa della punta sulla sede
        pos_glob_punta = centro_torr + rot_torr.multVec(rel_pos)                                # Posizione 3D globale della punta utensile

        rot_sede = calcola_rotazione_sede_locale(self.faccia_normale_locale)                    # Inclinazione della sede sulla torretta
        rot_trascinamento = rot_torr * rot_sede                                                 # Rotazione combinata (torretta + angolo sede)

        tool_obj.Proxy._is_executing = True                                                     # Sospende il ricalcolo intermedio
        try:                                                                                    # Applica le modifiche live all'utensile
            tool_obj.Proxy.ensure_properties(tool_obj)                                          # Assicura che esista RotazioneTorretta
            tool_obj.OffsetTorretta = pos_glob_punta - wcs                                      # Sposta l'utensile sulla sede della torretta
            tool_obj.RotazioneTorretta = list(rot_trascinamento.Q)                              # Ruota il corpo dell'utensile lungo la sede
            tool_obj.SpecchiaX = self.m_mir_x.isChecked()                                       # Applica specchiatura X
            tool_obj.SpecchiaY = self.m_mir_y.isChecked()                                       # Applica specchiatura Y
            tool_obj.RotX = self.m_rx_spin.value()                                              # Applica rotazione X
            tool_obj.RotY = self.m_ry_spin.value()                                              # Applica rotazione Y
            tool_obj.RotZ = self.m_rz_spin.value()                                              # Applica rotazione Z
        finally:                                                                                # Sblocca il Proxy
            tool_obj.Proxy._is_executing = False                                                # Riabilita execute
        tool_obj.Proxy.execute(tool_obj)                                                        # Aggiorna il 3D dell'utensile in tempo reale
        if tool_obj.Name in self.saldati_temp:                                                  # Se era già saldato, aggiorna live il record saldato
            self.registra_record_saldatura(tool_obj)                                            # Mantiene sincronizzata la saldatura
        doc.recompute()                                                                         # Rinfresca la vista 3D

    def registra_record_saldatura(self, tool_obj):                                              # Scrive i parametri correnti nel dizionario saldati_temp
        rel_pos = self.calcola_posizione_relativa_utensile()                                    # Calcola il vettore relativo al centro torretta
        f_pt = [self.faccia_punto_locale.x, self.faccia_punto_locale.y, self.faccia_punto_locale.z] if self.faccia_punto_locale else [-self.diam_spin.value()/2.0, 0.0, self.inc_p_spin.value()/2.0]
        f_nm = [self.faccia_normale_locale.x, self.faccia_normale_locale.y, self.faccia_normale_locale.z]
        self.saldati_temp[tool_obj.Name] = {                                                    # Registra i dati di saldatura per questo utensile
            "label": tool_obj.Label,                                                            # Etichetta utensile
            "rel_pos": [rel_pos.x, rel_pos.y, rel_pos.z],                                       # Posizione relativa saldata rispetto al centro torretta
            "faccia_pt": f_pt,                                                                  # Centro faccia di riferimento
            "faccia_norm": f_nm,                                                                # Normale faccia di riferimento (usata per l'angolo sede)
            "sporgenza": float(self.sporgenza_spin.value()),                                    # Distanza punta-faccia esterna
            "tx": float(self.m_tx_spin.value()),                                                # Traslazione X
            "ty": float(self.m_ty_spin.value()),                                                # Traslazione Y
            "tz": float(self.m_tz_spin.value()),                                                # Traslazione Z
            "mx": bool(self.m_mir_x.isChecked()),                                               # Specchio X
            "my": bool(self.m_mir_y.isChecked()),                                               # Specchio Y
            "rx": float(self.m_rx_spin.value()),                                                # Rotazione X
            "ry": float(self.m_ry_spin.value()),                                                # Rotazione Y
            "rz": float(self.m_rz_spin.value())                                                 # Rotazione Z
        }                                                                                       # Fine record saldatura

    def salda_utensile_corrente(self):                                                          # Salda e blocca l'utensile nella sua posizione e angolazione
        tool_obj = self.get_selected_mount_tool()                                               # Ottiene l'utensile corrente
        if not tool_obj: return                                                                 # Verifica validità
        if self.faccia_punto_locale is None:                                                    # Se non era ancora stata scelta una faccia, usa la sua Stazione T
            num_st = int(getattr(tool_obj, "NumeroStazione", 1))                                # Legge la stazione dell'utensile
            self.faccia_punto_locale, self.faccia_normale_locale = calcola_dati_sede_da_indice(
                num_st, self.num_pos_spin.value(), self.diam_spin.value(), self.inc_p_spin.value()
            )                                                                                   # Posiziona automaticamente sulla sua sede T
        self.aggiorna_anteprima_montaggio_utensile()                                            # Assicura che posizione e rotazione siano aggiornate
        self.registra_record_saldatura(tool_obj)                                                # Salva nel dizionario saldati_temp
        self.popola_combo_utensili_magazzino(FreeCAD.ActiveDocument)                            # Aggiorna la scritta [SALDATO] nella tendina
        self.aggiorna_visibilita_utensili_montaggio()                                           # Mantiene visibile l'utensile saldato
        self.lbl_mount_status.setText(f"Utensile [{tool_obj.Label}] SALDATO! Scegline un altro dalla tendina.")

    def scollega_utensile_corrente(self):                                                       # Smonta l'utensile selezionato dalla torretta e lo riporta sul WCS
        tool_obj = self.get_selected_mount_tool()                                               # Ottiene l'utensile corrente
        if not tool_obj: return                                                                 # Verifica validità
        if tool_obj.Name in self.saldati_temp:                                                  # Se era saldato sulla torretta
            del self.saldati_temp[tool_obj.Name]                                                # Lo rimuove dal dizionario dei saldati
        self.faccia_punto_locale = None                                                         # Azzera il riferimento faccia
        self.faccia_normale_locale = FreeCAD.Vector(-1.0, 0.0, 0.0)                             # Ripristina normale base
        tool_obj.Proxy._is_executing = True                                                     # Sospende execute
        try:                                                                                    # Riporta l'utensile sullo zero WCS
            tool_obj.Proxy.ensure_properties(tool_obj)                                          # Verifica proprietà
            tool_obj.OffsetTorretta = FreeCAD.Vector(0.0, 0.0, 0.0)                             # Azzera l'offset torretta
            tool_obj.RotazioneTorretta = [0.0, 0.0, 0.0, 1.0]                                   # Azzera la rotazione torretta
        finally:                                                                                # Sblocca
            tool_obj.Proxy._is_executing = False                                                # Riabilita
        tool_obj.Proxy.execute(tool_obj)                                                        # Ridisegna l'utensile sul WCS
        self.popola_combo_utensili_magazzino(FreeCAD.ActiveDocument)                            # Rimuove la scritta [SALDATO] dalla tendina
        if FreeCAD.ActiveDocument: FreeCAD.ActiveDocument.recompute()                           # Aggiorna la vista 3D
        self.lbl_mount_status.setText(f"Utensile [{tool_obj.Label}] scollegato dalla torretta.")

    def aggiorna_ui_modalita(self):                                                             # Mostra/nasconde i campi in base a Parametrica / Custom
        is_param = (self.mode_combo.currentIndex() == 0)                                        # True se è selezionata la torretta parametrica
        self.diam_spin.setEnabled(is_param)                                                     # Abilita diametro solo in modalità parametrica
        self.spess_spin.setEnabled(is_param)                                                    # Abilita spessore solo in modalità parametrica
        self.inc_w_spin.setEnabled(is_param)                                                    # Abilita larghezza sede solo in modalità parametrica
        self.inc_p_spin.setEnabled(is_param)                                                    # Abilita profondità sede solo in modalità parametrica
        self.btn_import_step.setVisible(not is_param)                                           # Mostra il pulsante STEP solo in modalità Custom
        self.trigger_update()                                                                   # Aggiorna l'anteprima 3D

    def importa_step_torretta(self):                                                            # Importa un file 3D STEP/FCStd per il plateau custom
        doc = FreeCAD.ActiveDocument                                                            # Ottiene il documento attivo
        if not doc: return                                                                      # Controllo sicurezza
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Importa Plateau Torretta 3D", "", "File 3D (*.step *.stp *.iges *.igs *.FCStd)")
        if not file_path: return                                                                # Se annullato esce
        try:                                                                                    # Blocco di importazione e pulizia
            prima = set(doc.Objects)                                                            # Oggetti prima dell'importazione
            ImportGui.insert(file_path, doc.Name)                                               # Importa il file nel documento
            dopo = set(doc.Objects)                                                             # Oggetti dopo l'importazione
            nuovi = list(dopo - prima)                                                          # Oggetti appena creati

            solidi = []                                                                         # Lista per raccogliere i solidi del plateau
            for obj in nuovi:                                                                   # Scorre gli oggetti importati
                if hasattr(obj, "Shape") and obj.Shape and hasattr(obj.Shape, "Volume") and obj.Shape.Volume > 0:
                    if not hasattr(obj, "OutList") or len(obj.OutList) == 0:                    # Prende solo le foglie solide
                        s = obj.Shape.copy()                                                    # Copia la forma
                        if hasattr(obj, "getGlobalPlacement"): s.Placement = obj.getGlobalPlacement()
                        solidi.append(s)                                                        # Aggiunge alla lista
            for obj in nuovi:                                                                   # Rimuove gli oggetti sporchi importati
                try:
                    if doc.getObject(obj.Name): doc.removeObject(obj.Name)
                except Exception: pass

            if solidi:                                                                          # Se sono stati trovati solidi validi
                comp = Part.makeCompound(solidi)                                                # Unisce i solidi in un Compound
                bb = comp.BoundBox                                                              # Calcola il BoundingBox per centrare il plateau
                comp.translate(-bb.Center)                                                      # Porta il centro del plateau custom in (0,0,0) locale
                self.custom_shape_imported = comp                                               # Salva la forma centrata
                self.trigger_update()                                                           # Aggiorna subito l'anteprima 3D
        except Exception as e:
            FreeCAD.Console.PrintError(f"Errore importazione STEP torretta: {e}\n")

    def calcola_centro_e_rotazione_correnti(self):                                              # Calcola centro e rotazione della torretta dai controlli UI
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        wcs = get_wcs_origin(doc)                                                               # Origine WCS
        is_param = (self.mode_combo.currentIndex() == 0)                                        # Controlla se è in modalità parametrica
        r_ing = (self.diam_spin.value() / 2.0) if is_param else 0.0                             # Raggio per mantenere la faccia a +DistX dal WCS
        cx = wcs.x + r_ing + self.dist_x_spin.value()                                           # Coordinata X centro torretta
        cy = wcs.y + self.dist_y_spin.value()                                                   # Coordinata Y centro torretta
        cz = wcs.z + self.dist_z_spin.value()                                                   # Coordinata Z fronte torretta
        centro = FreeCAD.Vector(cx, cy, cz)                                                     # Vettore centro

        rx = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), self.t_rx_spin.value())                  # Rotazione X
        ry = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), self.t_ry_spin.value())                  # Rotazione Y
        rz = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), self.t_rz_spin.value())                  # Rotazione Z
        rot_base = rx * ry * rz                                                                 # Rotazione base

        n = max(self.num_pos_spin.value(), 1)                                                   # Numero stazioni
        st_att = max(1, min(self.active_stat_spin.value(), n))                                  # Stazione attiva
        ang_idx = -(st_att - 1) * (360.0 / float(n))                                            # Angolo di indexaggio stazione attorno a Z
        rot_idx = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), ang_idx)                            # Rotazione attorno all'asse Z della torretta
        return centro, rot_base * rot_idx                                                       # Restituisce centro e rotazione totale

    def trigger_update(self, *args):                                                            # Aggiorna l'anteprima 3D della torretta e degli utensili saldati
        if self.is_updating: return                                                             # Se bloccato esce
        self.is_updating = True                                                                 # Attiva il semaforo
        try:                                                                                    # Blocco di aggiornamento
            doc = FreeCAD.ActiveDocument                                                        # Documento attivo
            if not doc or not self.preview_turret: return                                       # Verifica validità
            centro, rot_tot = self.calcola_centro_e_rotazione_correnti()                        # Calcola posizionamento torretta
            if self.mode_combo.currentIndex() == 0:                                             # Se Parametrica
                forma = costruisci_plateau_parametrico(
                    self.num_pos_spin.value(), self.diam_spin.value(), self.spess_spin.value(),
                    self.inc_w_spin.value(), self.inc_p_spin.value()
                )
            else:                                                                               # Se Custom STEP
                if self.custom_shape_imported and not self.custom_shape_imported.isNull():
                    forma = self.custom_shape_imported.copy()
                else:
                    forma = costruisci_plateau_parametrico(self.num_pos_spin.value(), self.diam_spin.value(), self.spess_spin.value(), self.inc_w_spin.value(), self.inc_p_spin.value())

            if self.t_mir_x.isChecked(): forma = forma.mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0))
            if self.t_mir_y.isChecked(): forma = forma.mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0))

            forma.Placement = FreeCAD.Placement(centro, rot_tot) * forma.Placement              # Applica posizione e rotazione
            self.preview_turret.Shape = forma                                                   # Aggiorna la Shape dell'anteprima
            self.preview_turret.ViewObject.Visibility = self.chk_show_turret.isChecked()        # Applica la visibilità scelta

            wcs = get_wcs_origin(doc)                                                           # Origine WCS per aggiornare anche gli utensili saldati
            for t_name, info in self.saldati_temp.items():                                      # Muove e ruota in tempo reale tutti gli utensili già saldati
                t_obj = doc.getObject(t_name)                                                   # Ottiene l'oggetto utensile
                if t_obj and hasattr(t_obj, "OffsetTorretta"):                                  # Se valido
                    rel_v = FreeCAD.Vector(*info.get("rel_pos", [0.0, 0.0, 0.0]))               # Legge posizione relativa saldata
                    p_glob = centro + rot_tot.multVec(rel_v)                                    # Nuova posizione globale punta
                    f_nm = FreeCAD.Vector(*info.get("faccia_norm", [-1.0, 0.0, 0.0]))           # Direzione uscente della sede saldata
                    rot_sede = calcola_rotazione_sede_locale(f_nm)                              # Rotazione della sede rispetto alla Sede 1
                    rot_trascinamento = rot_tot * rot_sede                                      # Rotazione complessiva trascinata dalla torretta
                    t_obj.Proxy._is_executing = True                                            # Sospende execute intermedio
                    try:                                                                        # Aggiorna posizioni e rotazioni
                        t_obj.Proxy.ensure_properties(t_obj)                                    # Garantisce presenza proprietà
                        t_obj.OffsetTorretta = p_glob - wcs                                     # Aggiorna OffsetTorretta
                        t_obj.RotazioneTorretta = list(rot_trascinamento.Q)                     # Aggiorna RotazioneTorretta
                        if "rx" in info: t_obj.RotX = float(info["rx"])
                        if "ry" in info: t_obj.RotY = float(info["ry"])
                        if "rz" in info: t_obj.RotZ = float(info["rz"])
                    finally:                                                                    # Sblocca
                        t_obj.Proxy._is_executing = False                                       # Riabilita
                    t_obj.Proxy.execute(t_obj)                                                  # Ricalcola l'utensile saldato

            curr_mount_tool = self.get_selected_mount_tool()                                    # Utensile in fase di montaggio non ancora saldato
            if curr_mount_tool and curr_mount_tool.Name not in self.saldati_temp and self.faccia_punto_locale is not None:
                rel_pos = self.calcola_posizione_relativa_utensile()                            # Calcola posizione relativa attuale
                p_glob = centro + rot_tot.multVec(rel_pos)                                      # Posizione globale
                rot_sede = calcola_rotazione_sede_locale(self.faccia_normale_locale)            # Rotazione sede
                rot_trascinamento = rot_tot * rot_sede                                          # Rotazione combinata
                curr_mount_tool.Proxy._is_executing = True                                      # Sospende execute
                try:                                                                            # Applica
                    curr_mount_tool.Proxy.ensure_properties(curr_mount_tool)                    # Verifica proprietà
                    curr_mount_tool.OffsetTorretta = p_glob - wcs                               # Aggiorna offset
                    curr_mount_tool.RotazioneTorretta = list(rot_trascinamento.Q)               # Aggiorna rotazione
                finally:                                                                        # Sblocca
                    curr_mount_tool.Proxy._is_executing = False                                 # Riabilita
                curr_mount_tool.Proxy.execute(curr_mount_tool)                                  # Ridisegna l'utensile

            doc.recompute()                                                                     # Ricalcola il documento
        finally:                                                                                # Sblocca il semaforo
            self.is_updating = False                                                            # Fine aggiornamento

    def aggiorna_combo_db(self):                                                                # Popola la tendina delle torrette salvate nell'Archivio
        db = load_turrets_db()                                                                  # Legge il file JSON
        self.db_combo.clear()                                                                   # Svuota il combo
        nomi = sorted(db.keys())                                                                # Ordina i nomi
        if nomi: self.db_combo.addItems(nomi)                                                   # Aggiunge i nomi
        else: self.db_combo.addItem("(Archivio vuoto)")                                         # Mostra testo informativo

    def salva_torretta_in_db(self, turret_obj):                                                 # Salva la configurazione della torretta su disco
        db = load_turrets_db()                                                                  # Carica il database
        key = turret_obj.TurretName.strip() or turret_obj.Label                                 # Chiave univoca
        safe_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in key)          # Nome sicuro per eventuale file .brep
        record = {                                                                              # Dizionario dati torretta
            "TurretName": key,
            "Modalita": str(turret_obj.Modalita),
            "NumeroPosizioni": int(turret_obj.NumeroPosizioni),
            "Diametro": float(turret_obj.Diametro),
            "Spessore": float(turret_obj.Spessore),
            "LarghezzaIncavo": float(turret_obj.LarghezzaIncavo),
            "ProfonditaIncavo": float(turret_obj.ProfonditaIncavo),
            "DistX_WCS": float(turret_obj.DistX_WCS),
            "DistY_WCS": float(turret_obj.DistY_WCS),
            "DistZ_WCS": float(turret_obj.DistZ_WCS),
            "SpecchiaX": bool(turret_obj.SpecchiaX),
            "SpecchiaY": bool(turret_obj.SpecchiaY),
            "RotX": float(turret_obj.RotX),
            "RotY": float(turret_obj.RotY),
            "RotZ": float(turret_obj.RotZ),
            "StazioneAttiva": int(turret_obj.StazioneAttiva),
            "UtensiliSaldati": str(turret_obj.UtensiliSaldati),
            "BrepFile": ""
        }                                                                                       # Fine record
        if turret_obj.Modalita == "Custom" and turret_obj.CustomBaseShape and not turret_obj.CustomBaseShape.isNull():
            brep_fn = f"{safe_name}.brep"
            brep_path = os.path.join(get_turret_lib_dir(), brep_fn)
            try:
                turret_obj.CustomBaseShape.exportBrep(brep_path)
                record["BrepFile"] = brep_fn
            except Exception as e:
                FreeCAD.Console.PrintError(f"Errore salvataggio BREP torretta: {e}\n")
        db[key] = record                                                                        # Aggiorna il dizionario
        save_turrets_db(db)                                                                     # Salva su disco

    def carica_torretta_da_db(self):                                                            # Richiama una torretta salvata dall'archivio
        db = load_turrets_db()                                                                  # Legge il database
        key = self.db_combo.currentText()                                                       # Voce selezionata
        if key not in db: return                                                                # Verifica validità
        data = db[key]                                                                          # Dati della torretta
        self.is_updating = True                                                                 # Blocca i segnali UI
        try:                                                                                    # Popola tutti i campi
            self.name_input.setText(data.get("TurretName", key))
            self.mode_combo.setCurrentIndex(1 if data.get("Modalita") == "Custom" else 0)
            self.num_pos_spin.setValue(int(data.get("NumeroPosizioni", 8)))
            self.diam_spin.setValue(float(data.get("Diametro", 150.0)))
            self.spess_spin.setValue(float(data.get("Spessore", 40.0)))
            self.inc_w_spin.setValue(float(data.get("LarghezzaIncavo", 12.0)))
            self.inc_p_spin.setValue(float(data.get("ProfonditaIncavo", 12.0)))
            self.dist_x_spin.setValue(float(data.get("DistX_WCS", 25.0)))
            self.dist_y_spin.setValue(float(data.get("DistY_WCS", 0.0)))
            self.dist_z_spin.setValue(float(data.get("DistZ_WCS", 25.0)))
            self.t_mir_x.setChecked(bool(data.get("SpecchiaX", False)))
            self.t_mir_y.setChecked(bool(data.get("SpecchiaY", False)))
            self.t_rx_spin.setValue(float(data.get("RotX", 0.0)))
            self.t_ry_spin.setValue(float(data.get("RotY", 0.0)))
            self.t_rz_spin.setValue(float(data.get("RotZ", 0.0)))
            self.active_stat_spin.setValue(int(data.get("StazioneAttiva", 1)))
            try: self.saldati_temp = json.loads(data.get("UtensiliSaldati", "{}"))
            except Exception: self.saldati_temp = {}
            if data.get("Modalita") == "Custom" and data.get("BrepFile"):
                brep_path = os.path.join(get_turret_lib_dir(), data["BrepFile"])
                if os.path.exists(brep_path):
                    s = Part.Shape(); s.importBrep(brep_path)
                    self.custom_shape_imported = s
        finally:                                                                                # Sblocca i segnali UI
            self.is_updating = False                                                            # Riabilita
        self.popola_combo_utensili_magazzino(FreeCAD.ActiveDocument)                            # Aggiorna le diciture [SALDATO]
        self.aggiorna_visibilita_utensili_montaggio()                                           # Mostra tutti gli utensili saldati
        self.aggiorna_ui_modalita()                                                             # Aggiorna la scena 3D

    def elimina_torretta_da_db(self):                                                           # Elimina la torretta selezionata dall'Archivio su disco
        db = load_turrets_db()                                                                  # Legge il database
        key = self.db_combo.currentText()                                                       # Chiave selezionata
        if key in db:                                                                           # Se presente
            brep_fn = db[key].get("BrepFile", "")
            if brep_fn:
                brep_path = os.path.join(get_turret_lib_dir(), brep_fn)
                if os.path.exists(brep_path):
                    try: os.remove(brep_path)
                    except Exception: pass
            del db[key]                                                                         # Rimuove dal dizionario
            save_turrets_db(db)                                                                 # Salva il JSON aggiornato
            self.aggiorna_combo_db()                                                            # Aggiorna la tendina

    def carica_dati_da_oggetto(self, obj):                                                      # Popola la UI quando si riapre una torretta con doppio click
        self.name_input.setText(str(getattr(obj, "TurretName", obj.Label)))
        self.mode_combo.setCurrentIndex(1 if getattr(obj, "Modalita", "Parametrica") == "Custom" else 0)
        self.num_pos_spin.setValue(int(getattr(obj, "NumeroPosizioni", 8)))
        self.diam_spin.setValue(float(getattr(obj, "Diametro", 150.0)))
        self.spess_spin.setValue(float(getattr(obj, "Spessore", 40.0)))
        self.inc_w_spin.setValue(float(getattr(obj, "LarghezzaIncavo", 12.0)))
        self.inc_p_spin.setValue(float(getattr(obj, "ProfonditaIncavo", 12.0)))
        self.dist_x_spin.setValue(float(getattr(obj, "DistX_WCS", 25.0)))
        self.dist_y_spin.setValue(float(getattr(obj, "DistY_WCS", 0.0)))
        self.dist_z_spin.setValue(float(getattr(obj, "DistZ_WCS", 25.0)))
        self.t_mir_x.setChecked(bool(getattr(obj, "SpecchiaX", False)))
        self.t_mir_y.setChecked(bool(getattr(obj, "SpecchiaY", False)))
        self.t_rx_spin.setValue(float(getattr(obj, "RotX", 0.0)))
        self.t_ry_spin.setValue(float(getattr(obj, "RotY", 0.0)))
        self.t_rz_spin.setValue(float(getattr(obj, "RotZ", 0.0)))
        self.active_stat_spin.setValue(int(getattr(obj, "StazioneAttiva", 1)))
        if hasattr(obj, "CustomBaseShape") and obj.CustomBaseShape and not obj.CustomBaseShape.isNull():
            self.custom_shape_imported = obj.CustomBaseShape.copy()
        try: self.saldati_temp = json.loads(getattr(obj, "UtensiliSaldati", "{}"))
        except Exception: self.saldati_temp = {}

    def pulisci_anteprima_torretta(self, doc):                                                  # Rimuove qualsiasi oggetto di anteprima della torretta
        if not doc: return                                                                      # Verifica documento
        if hasattr(self, "preview_turret") and self.preview_turret:
            try:
                if doc.getObject(self.preview_turret.Name): doc.removeObject(self.preview_turret.Name)
            except Exception: pass
            self.preview_turret = None
        for obj in list(doc.Objects):
            if obj.Name.startswith("TMP_Turret_Preview") or "ANTEPRIMA TORRETTA" in getattr(obj, "Label", "").upper():
                try: doc.removeObject(obj.Name)
                except Exception: pass

    def getStandardButtons(self):                                                               # Pulsanti standard OK e Cancel del pannello
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

    def accept(self):                                                                           # Salva la Torretta_Macchina e conferma le saldature utensili
        doc = FreeCAD.ActiveDocument                                                            # Ottiene il documento attivo
        if not doc: return False                                                                # Controllo sicurezza

        nome_torr = self.name_input.text().strip() or "Torretta Ottagonale 150"                 # Legge il nome della torretta
        if self.edit_obj and doc.getObject(self.edit_obj.Name):                                 # Se stavamo modificando una torretta esistente
            turret_obj = self.edit_obj                                                          # Usa l'oggetto esistente
        elif doc.getObject("Torretta_Macchina"):                                                # Se esiste già Torretta_Macchina nel documento
            turret_obj = doc.getObject("Torretta_Macchina")                                     # La riutilizza senza creare duplicati
        else:                                                                                   # Altrimenti crea il nuovo oggetto parametrico
            turret_obj = doc.addObject("Part::FeaturePython", "Torretta_Macchina")              # Crea Part::FeaturePython
            LatheTurretObject(turret_obj)                                                       # Inizializza il Proxy
            ViewProviderLatheTurret(turret_obj.ViewObject)                                      # Inizializza il ViewProvider con doppio click

        turret_obj.Proxy._is_executing = True                                                   # Sospende il ricalcolo durante l'assegnazione proprietà
        try:                                                                                    # Salva tutte le proprietà sull'oggetto
            turret_obj.Proxy.ensure_properties(turret_obj)
            turret_obj.TurretName = nome_torr
            turret_obj.Label = f"Torretta ({nome_torr})"
            turret_obj.Modalita = "Parametrica" if self.mode_combo.currentIndex() == 0 else "Custom"
            turret_obj.NumeroPosizioni = self.num_pos_spin.value()
            turret_obj.Diametro = self.diam_spin.value()
            turret_obj.Spessore = self.spess_spin.value()
            turret_obj.LarghezzaIncavo = self.inc_w_spin.value()
            turret_obj.ProfonditaIncavo = self.inc_p_spin.value()
            turret_obj.DistX_WCS = self.dist_x_spin.value()
            turret_obj.DistY_WCS = self.dist_y_spin.value()
            turret_obj.DistZ_WCS = self.dist_z_spin.value()
            turret_obj.SpecchiaX = self.t_mir_x.isChecked()
            turret_obj.SpecchiaY = self.t_mir_y.isChecked()
            turret_obj.RotX = self.t_rx_spin.value()
            turret_obj.RotY = self.t_ry_spin.value()
            turret_obj.RotZ = self.t_rz_spin.value()
            turret_obj.StazioneAttiva = self.active_stat_spin.value()
            turret_obj.UtensiliSaldati = json.dumps(self.saldati_temp)
            if self.custom_shape_imported and not self.custom_shape_imported.isNull():
                turret_obj.CustomBaseShape = self.custom_shape_imported
        finally:                                                                                # Riabilita il Proxy
            turret_obj.Proxy._is_executing = False

        turret_obj.Proxy.execute(turret_obj)                                                    # Costruisce la forma finale e aggiorna gli utensili saldati
        if hasattr(turret_obj, "ViewObject") and turret_obj.ViewObject:
            turret_obj.ViewObject.Visibility = self.chk_show_turret.isChecked()

        lib = doc.getObject("Libreria_Utensili")                                                # Gestisce la visibilità finale degli utensili del magazzino
        if lib and hasattr(lib, "Group"):
            for t in lib.Group:
                if hasattr(t, "ViewObject") and t.ViewObject:
                    if self.saldati_temp:
                        t.ViewObject.Visibility = (t.Name in self.saldati_temp)                 # Lascia visibili tutti gli utensili saldati sulla torretta

        if self.chk_save_db.isChecked():                                                        # Salva nell'Archivio Permanente
            self.salva_torretta_in_db(turret_obj)

        self.pulisci_anteprima_torretta(doc)                                                    # Elimina l'anteprima provvisoria
        doc.recompute()                                                                         # Aggiorna il documento
        if FreeCADGui.ActiveDocument: FreeCADGui.ActiveDocument.resetEdit()
        FreeCADGui.Control.closeDialog()
        return True

    def reject(self):                                                                           # Annulla le modifiche e ripristina lo stato precedente
        doc = FreeCAD.ActiveDocument                                                            # Ottiene il documento attivo
        if doc:
            self.pulisci_anteprima_torretta(doc)                                                # Rimuove l'anteprima temporanea della torretta
            for t_name, bkp in self.stato_originale_utensili.items():                           # Ripristina gli utensili alla posizione pre-apertura
                t_obj = doc.getObject(t_name)
                if t_obj and hasattr(t_obj, "OffsetTorretta"):
                    t_obj.Proxy._is_executing = True
                    try:
                        t_obj.Proxy.ensure_properties(t_obj)
                        t_obj.OffsetTorretta = bkp["OffsetTorretta"]
                        t_obj.RotazioneTorretta = bkp["RotazioneTorretta"]
                        t_obj.RotX = bkp["RotX"]
                        t_obj.RotY = bkp["RotY"]
                        t_obj.RotZ = bkp["RotZ"]
                        t_obj.SpecchiaX = bkp["SpecchiaX"]
                        t_obj.SpecchiaY = bkp["SpecchiaY"]
                    finally:
                        t_obj.Proxy._is_executing = False
                    t_obj.Proxy.execute(t_obj)
                    if hasattr(t_obj, "ViewObject") and t_obj.ViewObject:
                        t_obj.ViewObject.Visibility = bkp["Visibility"]
            if self.edit_obj and doc.getObject(self.edit_obj.Name):
                if hasattr(self.edit_obj, "ViewObject") and self.edit_obj.ViewObject:
                    self.edit_obj.ViewObject.Visibility = True
            doc.recompute()
        if FreeCADGui.ActiveDocument: FreeCADGui.ActiveDocument.resetEdit()
        FreeCADGui.Control.closeDialog()
        return True