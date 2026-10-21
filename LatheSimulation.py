import FreeCAD                                                                                  # Importa il modulo base di FreeCAD
import FreeCADGui                                                                               # Importa il modulo interfaccia grafica di FreeCAD
import Part                                                                                     # Importa il modulo geometrico Part
import math                                                                                     # Importa le funzioni matematiche
import json                                                                                     # Importa il modulo JSON per decodificare i percorsi CAM
from PySide import QtCore, QtGui                                                                # Importa i moduli grafici PySide
try:                                                                                            # Tenta di importare QtWidgets per compatibilità Qt5/Qt6
    from PySide import QtWidgets                                                                # Assegna QtWidgets
except ImportError:                                                                             # Fallback per versioni meno recenti
    QtWidgets = QtGui                                                                           # Usa QtGui come alias di QtWidgets


def get_wcs_origin(doc=None):                                                                   # Restituisce il vettore origine del WCS (Setup_Macchina)
    if doc is None:                                                                             # Se non è specificato il documento
        doc = FreeCAD.ActiveDocument                                                            # Usa il documento attivo
    if doc and doc.getObject("Setup_Macchina"):                                                 # Se esiste Setup_Macchina
        s = doc.getObject("Setup_Macchina")                                                     # Ottiene l'oggetto Setup
        if hasattr(s, "Origine"):                                                               # Controlla la proprietà Origine
            return FreeCAD.Vector(s.Origine)                                                    # Restituisce il vettore Origine WCS
    return FreeCAD.Vector(0.0, 0.0, 0.0)                                                        # Fallback su (0,0,0)


def get_tool_change_coords(doc=None):                                                           # Legge le quote X e Z di Cambio Utensile dal Setup_Macchina
    if doc is None:                                                                             # Se non è specificato il documento
        doc = FreeCAD.ActiveDocument                                                            # Usa il documento attivo
    if doc and doc.getObject("Setup_Macchina"):                                                 # Se esiste Setup_Macchina
        s = doc.getObject("Setup_Macchina")                                                     # Ottiene l'oggetto Setup
        hx = float(getattr(s, "CambioUtensileX", 60.0))                                         # Quota X cambio utensile
        hz = float(getattr(s, "CambioUtensileZ", 60.0))                                         # Quota Z cambio utensile
        return hx, hz                                                                           # Restituisce la coppia (X, Z)
    return 60.0, 60.0                                                                           # Valori predefiniti (60, 60)


def get_stock_dimensions(doc=None):                                                             # Legge le dimensioni reali del cilindro grezzo
    if doc is None:                                                                             # Se non è specificato il documento
        doc = FreeCAD.ActiveDocument                                                            # Usa il documento attivo
    r_ext = 25.0                                                                                # Raggio esterno predefinito (mm)
    r_int = 0.0                                                                                 # Raggio foro interno predefinito (mm)
    z_front = 1.0                                                                               # Sovrametallo frontale Z+ (mm)
    z_back = -80.0                                                                              # Fine grezzo Z- (mm)
    if doc and doc.getObject("Grezzo_Macchina"):                                                # Se esiste l'oggetto Grezzo_Macchina
        g = doc.getObject("Grezzo_Macchina")                                                    # Ottiene l'oggetto Grezzo
        r_ext = max(float(getattr(g, "DiametroEsterno", 50.0)) / 2.0, 1.0)                      # Raggio esterno cilindro grezzo
        if str(getattr(g, "FormaGrezzo", "Cilindro")) == "Esagono":                             # Se è una barra esagonale
            r_ext = r_ext / math.cos(math.radians(30.0))                                        # Raggio circoscritto sugli spigoli
        r_int = max(float(getattr(g, "DiametroInterno", 0.0)) / 2.0, 0.0)                       # Raggio eventuale foro interno
        z_front = float(getattr(g, "SovrametalloFrontale", 1.0))                                # Quota Z anteriore
        l_tot = max(float(getattr(g, "LunghezzaTotale", 80.0)), 5.0)                            # Lunghezza totale barra
        z_back = z_front - l_tot                                                                # Quota Z posteriore
    return r_ext, r_int, z_front, z_back                                                        # Restituisce i 4 parametri del grezzo


def trova_utensile_operazione(doc, nome_utensile):                                              # Trova l'oggetto utensile nel documento dal Name o dalla Label
    if not doc or not nome_utensile:                                                            # Verifica validità parametri
        return None                                                                             # Non trovato
    obj = doc.getObject(nome_utensile)                                                          # Cerca direttamente per Name interno
    if obj:                                                                                     # Se trovato
        return obj                                                                              # Lo restituisce
    lib = doc.getObject("Libreria_Utensili")                                                    # Altrimenti cerca nel gruppo Magazzino Utensili
    if lib and hasattr(lib, "Group"):                                                           # Se il gruppo esiste
        for t in lib.Group:                                                                     # Scorre gli utensili
            if t.Label == nome_utensile or getattr(t, "ToolName", "") == nome_utensile:         # Confronta Label e ToolName
                return t                                                                        # Restituisce l'utensile trovato
    return None                                                                                 # Non trovato


def rileva_modalita_taglio_operazione(op_obj, t_obj):                                           # Determina il tipo di asportazione ("OD", "ID", "DRILL", "GROOVE_OD")
    op_name = op_obj.Name if op_obj else ""                                                     # Nome interno dell'operazione
    ciclo = str(getattr(op_obj, "TipoCiclo", "")) if op_obj else ""                             # Stringa TipoCiclo dell'operazione
    tipo_u = str(getattr(t_obj, "TipoLavorazione", "")) if t_obj else ""                        # Categoria utensile
    if "Foratura" in op_name or "Centrino" in ciclo or "Maschiatura" in ciclo or "Punta" in tipo_u or "Maschio" in tipo_u:
        return "DRILL"                                                                          # Foratura assiale centrata sull'asse Z
    if "Intern" in ciclo or "(ID)" in ciclo or "Bareno" in tipo_u:                              # Tornitura / Gola / Filettatura interna
        return "ID"                                                                             # Asportazione interna (allarga il foro)
    if "Gola" in op_name or "Troncatura" in op_name or "Gola" in ciclo or "Troncatura" in ciclo:
        return "GROOVE_OD"                                                                      # Gola o Troncatura con larghezza lama w_lama
    return "OD"                                                                                 # Tornitura / Sfacciatura / Filettatura esterna


class DynamicLatheStock2D:                                                                      # Motore di asportazione 2D -> 3D per rivoluzione (veloce e senza fette!)
    def __init__(self, doc, step_z=0.20):                                                       # Costruttore del profilo radiale del grezzo
        self.doc = doc                                                                          # Riferimento al documento FreeCAD
        self.wcs = get_wcs_origin(doc)                                                          # Origine WCS
        self.r_ext_init, self.r_int_init, self.z_front_init, self.z_back_init = get_stock_dimensions(doc)
        self.step_z = max(float(step_z), 0.10)                                                  # Risoluzione assiale Z (0.20 mm)
        self.n_samples = max(int(math.ceil((self.z_front_init - self.z_back_init) / self.step_z)) + 1, 20)
        self.dz = (self.z_front_init - self.z_back_init) / float(self.n_samples - 1)            # Passo esatto tra i campioni Z
        self.z_grid = [self.z_back_init + i * self.dz for i in range(self.n_samples)]           # Griglia delle quote Z da dietro a davanti
        self.reset()                                                                            # Inizializza i raggi esterni e interni

    def reset(self):                                                                            # Ripristina il grezzo vergine iniziale
        self.r_od = [self.r_ext_init] * self.n_samples                                          # Profilo esterno iniziale costante = r_ext_init
        self.r_id = [self.r_int_init] * self.n_samples                                          # Profilo interno iniziale costante = r_int_init

    def applica_segmento_taglio(self, x1, z1, x2, z2, cut_mode, w_lama=3.0, d_punta=10.0):      # Aggiorna matematicamente il profilo del grezzo lungo il segmento (x1,z1)->(x2,z2)
        modificato = False                                                                      # Flag che indica se il metallo è stato effettivamente toccato
        if cut_mode == "DRILL":                                                                 # 1. FORATURA ASSIALE: allarga il raggio interno r_id fino a d_punta/2
            r_foro = max(float(d_punta) / 2.0, 0.5)                                             # Raggio della punta
            z_min_cut = min(z1, z2)                                                             # Quota Z più profonda raggiunta dalla punta
            for i, zv in enumerate(self.z_grid):                                                # Scorre tutte le stazioni Z toccate dalla punta
                if zv >= z_min_cut and self.r_id[i] < r_foro:                                   # Se la punta è passata a questa quota Z
                    self.r_id[i] = min(r_foro, self.r_od[i])                                    # Allarga il foro interno
                    modificato = True                                                           # Segnala modifica

        elif cut_mode == "ID":                                                                  # 2. TORNITURA / GOLA INTERNA: alza il raggio interno r_id lungo il segmento
            z_a = min(z1, z2); z_b = max(z1, z2)                                                # Estremi Z del movimento
            dz_seg = z2 - z1                                                                    # Escursione Z
            for i, zv in enumerate(self.z_grid):                                                # Scorre la griglia Z
                if z_a - 0.15 <= zv <= z_b + 0.15:                                              # Se la quota Z cade nel segmento percorso
                    t = (zv - z1) / dz_seg if abs(dz_seg) > 1e-4 else 0.5                       # Frazione lineare lungo il segmento
                    t = max(0.0, min(1.0, t))                                                   # Clamping 0..1
                    r_ut = max(x1 + t * (x2 - x1), x1, x2) if abs(dz_seg) <= 1e-4 else (x1 + t * (x2 - x1))
                    if r_ut > self.r_id[i]:                                                     # Se l'utensile interno scava oltre il foro attuale
                        self.r_id[i] = min(r_ut, self.r_od[i])                                  # Aggiorna il raggio interno
                        modificato = True                                                       # Segnala modifica

        elif cut_mode == "GROOVE_OD":                                                           # 3. GOLA ESTERNA / TRONCATURA: considera la larghezza lama w_lama (da Z-w_lama a Z)
            w_eff = max(float(w_lama), 0.5)                                                     # Larghezza lama
            z_a = min(z1, z2) - w_eff                                                           # Il fianco sinistro della lama scava fino a z - w_lama
            z_b = max(z1, z2)                                                                   # Il fianco destro della lama è a z
            r_min_seg = max(min(x1, x2), 0.0)                                                   # Raggio raggiunto dalla lama
            for i, zv in enumerate(self.z_grid):                                                # Scorre la griglia Z
                if z_a <= zv <= z_b:                                                            # Dentro l'impronta della lama
                    if r_min_seg < self.r_od[i]:                                                # Se la lama scende sotto il diametro esterno attuale
                        self.r_od[i] = max(r_min_seg, self.r_id[i])                             # Abbassa il profilo esterno (gola o troncatura)
                        modificato = True                                                       # Segnala modifica

        else:                                                                                   # 4. TORNITURA ESTERNA / SFACCIATURA / CONI / PROFILATURA (OD)
            dz_seg = z2 - z1                                                                    # Spostamento lungo Z
            dr_seg = x2 - x1                                                                    # Spostamento lungo X
            if abs(dz_seg) < 0.05 and abs(dr_seg) > 0.02 and x2 < x1:                           # 4A. Sfacciatura / Taglio Radiale verso il centro (-X) a Z costante
                r_low = max(min(x1, x2), 0.0)                                                   # Raggio inferiore raggiunto nella sfacciatura
                z_cut = min(z1, z2)                                                             # Piano Z della sfacciatura
                for i, zv in enumerate(self.z_grid):                                            # Tutte le fette a destra di z_cut (sovrametallo frontale) vengono spianate!
                    if zv >= z_cut - 0.15:                                                      # Dal piano di sfacciatura verso la faccia anteriore
                        if r_low < self.r_od[i]:                                                # Se l'utensile scende sotto il raggio attuale
                            self.r_od[i] = max(r_low, self.r_id[i])                             # Spiana il materiale frontale
                            modificato = True                                                   # Segnala modifica
            else:                                                                               # 4B. Passata Longitudinale, Conica o Smusso lungo Z
                z_a = min(z1, z2); z_b = max(z1, z2)                                            # Intervallo Z coperto dal segmento
                for i, zv in enumerate(self.z_grid):                                            # Scorre le quote Z del grezzo
                    if z_a - 0.10 <= zv <= z_b + 0.10:                                          # Se il campione Z è dentro il tratto percorso dall'utensile
                        t = (zv - z1) / dz_seg if abs(dz_seg) > 1e-4 else 0.5                   # Interpolazione esatta (seguendo fedelmente anche i coni!)
                        t = max(0.0, min(1.0, t))                                               # Limita tra 0 e 1
                        r_ut = max(x1 + t * (x2 - x1), 0.0)                                     # Raggio della punta utensile alla quota zv
                        if r_ut < self.r_od[i]:                                                 # Se la punta utensile è più bassa della superficie attuale del grezzo
                            self.r_od[i] = max(r_ut, self.r_id[i])                              # Asporta il materiale esterno portandolo esattamente a r_ut!
                            modificato = True                                                   # Segnala modifica
        return modificato                                                                       # Restituisce True se il grezzo è cambiato

    def genera_shape_3d(self):                                                                  # Costruisce il solido 3D ruotando di 360° il profilo 2D aggiornato
        try:                                                                                    # Costruisce i blocchi continui dove r_od > r_id + 0.05 (gestisce anche la troncatura!)
            solidi = []                                                                         # Lista di solidi (se la troncatura arriva al centro il pezzo si divide in due)
            idx = 0                                                                             # Indice di scansione lungo la griglia Z
            while idx < self.n_samples:                                                         # Cerca i tratti dove c'è spessore di materiale
                while idx < self.n_samples and (self.r_od[idx] - self.r_id[idx]) <= 0.05:       # Salta le zone completamente troncate o spianate a zero
                    idx += 1                                                                    # Avanza
                if idx >= self.n_samples:                                                       # Fine della barra
                    break                                                                       # Esce dal ciclo
                start_i = idx                                                                   # Inizio del tratto solido
                while idx < self.n_samples and (self.r_od[idx] - self.r_id[idx]) > 0.05:        # Avanza finché c'è materiale
                    idx += 1                                                                    # Avanza
                end_i = idx - 1                                                                 # Fine del tratto solido

                if end_i > start_i:                                                             # Se il tratto ha almeno 2 stazioni Z
                    pts = []                                                                    # Lista vertici del poligono chiuso nel piano XZ
                    # Cammino inferiore (interno o asse Z) da start_i a end_i:
                    for k in range(start_i, end_i + 1):                                         # Scorre da sinistra a destra sul profilo interno
                        rk = max(self.r_id[k], 0.0)                                             # Raggio interno (0 se barra piena)
                        zk = self.z_grid[k]                                                     # Quota Z
                        p_new = FreeCAD.Vector(self.wcs.x + rk, self.wcs.y, self.wcs.z + zk)    # Punto 3D inferiore
                        if not pts or (p_new - pts[-1]).Length > 1e-3:                          # Evita punti duplicati
                            pts.append(p_new)                                                   # Aggiunge punto
                    # Cammino superiore (profilo esterno tornito) da end_i a start_i:
                    for k in range(end_i, start_i - 1, -1):                                     # Torna da destra a sinistra sul profilo esterno lavorato
                        rk = max(self.r_od[k], self.r_id[k] + 0.05)                             # Raggio esterno lavorato
                        zk = self.z_grid[k]                                                     # Quota Z
                        p_new = FreeCAD.Vector(self.wcs.x + rk, self.wcs.y, self.wcs.z + zk)    # Punto 3D superiore
                        if (p_new - pts[-1]).Length > 1e-3:                                     # Evita punti duplicati
                            pts.append(p_new)                                                   # Aggiunge punto
                    if len(pts) >= 3:                                                           # Chiude il poligono e genera la rivoluzione 360°
                        pts.append(pts[0])                                                      # Chiude l'anello di vertici
                        wire = Part.makePolygon(pts)                                            # Crea la polilinea chiusa
                        face = Part.Face(wire)                                                  # Crea la faccia 2D
                        sol = face.revolve(FreeCAD.Vector(self.wcs.x, self.wcs.y, self.wcs.z), FreeCAD.Vector(0, 0, 1), 360.0)
                        solidi.append(sol)                                                      # Aggiunge il solido ruotato
            if len(solidi) == 1:                                                                # Caso normale (un solo corpo grezzo lavorato)
                return solidi[0]                                                                # Restituisce direttamente il solido
            elif len(solidi) > 1:                                                               # Caso post-troncatura (spezzone + pezzo troncato)
                return Part.makeCompound(solidi)                                                # Restituisce il compound dei solidi
        except Exception as e:                                                                  # Fallback di sicurezza
            FreeCAD.Console.PrintWarning(f"Avviso ricostruzione grezzo 2D: {e}\n")              # Log avviso
        sol_fb, _ = crea_solido_grezzo_fallback(self.doc)                                       # Fallback cilindrico
        return sol_fb                                                                           # Restituisce solido base


def crea_solido_grezzo_fallback(doc):                                                           # Funzione di supporto per cilindro grezzo iniziale
    wcs = get_wcs_origin(doc)                                                                   # Origine WCS
    r_ext, r_int, z_front, z_back = get_stock_dimensions(doc)                                   # Quote grezzo
    altezza = max(z_front - z_back, 1.0)                                                        # Altezza
    p_base = FreeCAD.Vector(wcs.x, wcs.y, wcs.z + z_back)                                       # Base
    sol = Part.makeCylinder(r_ext, altezza, p_base, FreeCAD.Vector(0, 0, 1))                    # Cilindro
    return sol, r_ext                                                                           # Restituisce cilindro e raggio


def genera_frames_simulazione(doc, lista_operazioni, passo_interp_mm=1.0):                      # Interpola i percorsi CAM rispettando al 100% ogni vertice della linea verde!
    frames = []                                                                                 # Lista finale dei fotogrammi
    if not doc or not lista_operazioni:                                                         # Se non ci sono operazioni
        return frames                                                                           # Lista vuota

    hx, hz = get_tool_change_coords(doc)                                                        # Coordinate Home di cambio utensile
    curr_x, curr_z = hx, hz                                                                     # Posizione iniziale
    last_stazione = None                                                                        # Ultima stazione T usata

    for op_obj in lista_operazioni:                                                             # Scorre le operazioni CAM da simulare
        if not hasattr(op_obj, "PercorsoJSON"):                                                 # Verifica presenza percorso
            continue                                                                            # Salta se assente
        try:                                                                                    # Legge i movimenti esatti dell'operazione
            moves = json.loads(op_obj.PercorsoJSON or "[]")                                     # Lista [{"cmd", "x", "z", "f"}, ...]
        except Exception:                                                                       # Errore JSON
            moves = []                                                                          # Vuoto
        if not moves:                                                                           # Se non ci sono movimenti
            continue                                                                            # Passa alla successiva

        t_name = str(getattr(op_obj, "UtensileAssegnato", ""))                                  # Nome utensile
        t_obj = trova_utensile_operazione(doc, t_name)                                          # Oggetto utensile
        num_st = int(getattr(t_obj, "NumeroStazione", 1)) if t_obj else 1                       # Numero stazione
        sigla_st = str(getattr(t_obj, "Stazione", f"T{num_st:02d}")) if t_obj else "T01"        # Sigla stazione
        tool_real_name = t_obj.Name if t_obj else ""                                            # Name interno utensile
        cut_mode = rileva_modalita_taglio_operazione(op_obj, t_obj)                             # Modalità taglio ("OD", "ID", "DRILL", "GROOVE_OD")
        w_lama = float(getattr(op_obj, "LarghezzaLama", getattr(t_obj, "LarghezzaLamaGola", 3.0))) if (op_obj or t_obj) else 3.0
        d_punta = float(getattr(op_obj, "DiametroPunta", getattr(t_obj, "Larghezza", 10.0))) if (op_obj or t_obj) else 10.0

        if last_stazione is not None and last_stazione != num_st:                               # Se cambia utensile, ritira a Home
            frames.append({                                                                     # Frame di ritiro a cambio utensile
                "op_label": op_obj.Label, "tool_name": tool_real_name,
                "stazione_num": last_stazione, "stazione_str": f"Cambio -> {sigla_st}",
                "cmd": "G0", "x1": curr_x, "z1": curr_z, "x": hx, "z": hz, "f": 0.0,
                "is_cut": False, "cut_mode": cut_mode, "w_lama": w_lama, "d_punta": d_punta
            })
            curr_x, curr_z = hx, hz                                                             # Aggiorna quota corrente

        x0 = float(moves[0].get("x", hx))                                                       # X primo punto operazione
        z0 = float(moves[0].get("z", hz))                                                       # Z primo punto operazione
        frames.append({                                                                         # Frame di approccio iniziale operazione
            "op_label": op_obj.Label, "tool_name": tool_real_name,
            "stazione_num": num_st, "stazione_str": sigla_st,
            "cmd": "G0", "x1": curr_x, "z1": curr_z, "x": x0, "z": z0, "f": 0.0,
            "is_cut": False, "cut_mode": cut_mode, "w_lama": w_lama, "d_punta": d_punta
        })
        curr_x, curr_z = x0, z0                                                                 # Allinea su punto 0
        last_stazione = num_st                                                                  # Salva stazione

        for mv in moves[1:]:                                                                    # Scorre ogni singolo segmento della linea verde/rossa
            cmd = str(mv.get("cmd", "G1"))                                                      # Comando ("G0", "G1", "G32")
            nx = float(mv.get("x", curr_x))                                                     # X di arrivo esatta del segmento
            nz = float(mv.get("z", curr_z))                                                     # Z di arrivo esatta del segmento
            f_val = float(mv.get("f", 0.0))                                                     # Avanzamento F
            is_cutting = (cmd in ["G1", "G32"])                                                 # True se taglia materiale

            dist = math.hypot(nx - curr_x, nz - curr_z)                                         # Lunghezza segmento (mm)
            if dist < 1e-4:                                                                     # Ignora punti coincidenti
                continue                                                                        # Passa oltre

            step_mm = passo_interp_mm if is_cutting else (passo_interp_mm * 2.5)                # Passo campionamento
            n_sub = max(1, min(int(math.ceil(dist / max(step_mm, 0.2))), 100))                  # Numero sotto-passi

            px, pz = curr_x, curr_z                                                             # Inizio del sotto-passo
            for s in range(1, n_sub + 1):                                                       # Genera i fotogrammi che terminano esattamente su (nx, nz)
                t_fraz = float(s) / float(n_sub)                                                # Frazione (da 1/n_sub a 1.0 esatto)
                ix = curr_x + t_fraz * (nx - curr_x)                                            # X interpolata sulla retta del segmento
                iz = curr_z + t_fraz * (nz - curr_z)                                            # Z interpolata sulla retta del segmento
                frames.append({                                                                 # Aggiunge il fotogramma
                    "op_label": op_obj.Label, "tool_name": tool_real_name,
                    "stazione_num": num_st, "stazione_str": sigla_st,
                    "cmd": cmd, "x1": px, "z1": pz, "x": ix, "z": iz, "f": f_val,
                    "is_cut": is_cutting, "cut_mode": cut_mode,
                    "w_lama": w_lama, "d_punta": d_punta
                })
                px, pz = ix, iz                                                                 # Avanza l'inizio del sotto-passo successivo
            curr_x, curr_z = nx, nz                                                             # Fine esatta sul vertice della linea verde!

    return frames                                                                               # Restituisce la lista fotogrammi


class LatheSimulationPanel:                                                                     # Pannello Task per la Simulazione Cinematica 3D e Asportazione Grezzo
    def __init__(self):                                                                         # Costruttore del pannello
        self.doc = FreeCAD.ActiveDocument                                                       # Documento attivo
        self.frames = []                                                                        # Lista fotogrammi
        self.current_frame_idx = 0                                                              # Indice fotogramma corrente
        self.last_cut_frame_idx = 0                                                             # Ultimo fotogramma applicato al profilo del grezzo
        self.is_updating_slider = False                                                         # Semaforo per lo slider temporale
        self.backup_stato = {}                                                                  # Backup di Torretta, Utensili e Grezzo
        self.sim_stock_obj = None                                                               # Oggetto 3D temporaneo del grezzo che viene tornito
        self.stock_2d = DynamicLatheStock2D(self.doc, step_z=0.20) if self.doc else None        # Motore profilo 2D ad alta velocità

        self.pulisci_oggetti_temporanei()                                                       # Pulisce eventuali oggetti temporanei precedenti
        self.salva_stato_iniziale()                                                             # Fotografa lo stato iniziale della macchina

        self.timer = QtCore.QTimer()                                                            # Timer per l'animazione continua
        self.timer.timeout.connect(self.on_timer_tick)                                          # Collega il tick del timer

        self.form = QtWidgets.QWidget()                                                         # Contenitore principale della finestra a destra
        self.form.setMinimumWidth(240)                                                          # Larghezza minima compatta
        self.layout = QtWidgets.QVBoxLayout(self.form)                                          # Layout verticale
        self.layout.setContentsMargins(4, 4, 4, 4)                                              # Margini ridotti

        self.grp_sel = QtWidgets.QGroupBox("Selezione Operazioni e Modalità")                   # Gruppo 1: Selezione e Opzioni
        self.lyt_sel = QtWidgets.QFormLayout(self.grp_sel)                                      # Form layout

        self.op_combo = QtWidgets.QComboBox()                                                   # Tendina scelta operazione
        self.op_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.op_combo.setMinimumContentsLength(10)
        self.popola_combo_operazioni()                                                          # Popola con le operazioni CAM

        self.chk_cut_stock = QtWidgets.QCheckBox("Simula asportazione materiale sul Grezzo")    # Attiva la tornitura dinamica del grezzo
        self.chk_cut_stock.setChecked(True)                                                     # Attivo di default
        self.chk_coll = QtWidgets.QCheckBox("Verifica Collisioni 3D in tempo reale")            # Attiva controllo collisioni
        self.chk_coll.setChecked(True)                                                          # Attivo di default
        self.chk_pause_coll = QtWidgets.QCheckBox("Metti in Pausa se rileva collisione")        # Ferma se rileva urto
        self.chk_pause_coll.setChecked(False)                                                   # Disattivato di default per non bloccare il Play

        self.lyt_sel.addRow("Simula:", self.op_combo)                                           # Riga selezione operazione
        self.lyt_sel.addRow(self.chk_cut_stock)                                                 # Riga asportazione grezzo
        self.lyt_sel.addRow(self.chk_coll)                                                      # Riga verifica collisioni
        self.lyt_sel.addRow(self.chk_pause_coll)                                                # Riga pausa su collisione
        self.layout.addWidget(self.grp_sel)                                                     # Aggiunge Gruppo 1

        self.grp_play = QtWidgets.QGroupBox("Controlli Riproduzione e Velocità")                # Gruppo 2: Player su 2 righe e Velocità Turbo
        self.lyt_play = QtWidgets.QVBoxLayout(self.grp_play)                                    # Layout verticale Player

        self.lyt_btns_row1 = QtWidgets.QHBoxLayout()                                            # RIGA 1: Play e Pausa grandi (nessun pulsante tagliato!)
        self.btn_play = QtWidgets.QPushButton("▶ Play")                                         # Pulsante Play
        self.btn_play.setStyleSheet("font-weight: bold; background-color: #2E6B27; color: white; padding: 6px;")
        self.btn_play.clicked.connect(self.avvia_play)                                          # Collega Play

        self.btn_pause = QtWidgets.QPushButton("⏸ Pausa")                                       # Pulsante Pausa
        self.btn_pause.setStyleSheet("font-weight: bold; padding: 6px;")
        self.btn_pause.clicked.connect(self.metti_in_pausa)                                     # Collega Pausa

        self.lyt_btns_row1.addWidget(self.btn_play)                                             # Aggiunge Play
        self.lyt_btns_row1.addWidget(self.btn_pause)                                            # Aggiunge Pausa
        self.lyt_play.addLayout(self.lyt_btns_row1)                                             # Inserisce Riga 1

        self.lyt_btns_row2 = QtWidgets.QHBoxLayout()                                            # RIGA 2: Passo -1, Passo +1 e Reset
        self.btn_back = QtWidgets.QPushButton("⏮ -1")                                           # Pulsante passo indietro
        self.btn_back.clicked.connect(self.passo_indietro)                                      # Collega -1

        self.btn_fwd = QtWidgets.QPushButton("+1 ⏭")                                            # Pulsante passo avanti
        self.btn_fwd.clicked.connect(self.passo_avanti)                                         # Collega +1

        self.btn_reset = QtWidgets.QPushButton("⏹ Reset")                                       # Pulsante Reset inizio
        self.btn_reset.clicked.connect(self.torna_inizio)                                       # Collega Reset

        self.lyt_btns_row2.addWidget(self.btn_back)                                             # Aggiunge -1
        self.lyt_btns_row2.addWidget(self.btn_fwd)                                              # Aggiunge +1
        self.lyt_btns_row2.addWidget(self.btn_reset)                                            # Aggiunge Reset
        self.lyt_play.addLayout(self.lyt_btns_row2)                                             # Inserisce Riga 2

        self.slider_timeline = QtWidgets.QSlider(QtCore.Qt.Horizontal)                          # Barra di scorrimento temporale (Timeline)
        self.slider_timeline.setRange(0, 100)                                                   # Range iniziale
        self.slider_timeline.valueChanged.connect(self.on_slider_moved)                         # Collega scrubbing manuale
        self.lyt_play.addWidget(self.slider_timeline)                                           # Aggiunge timeline

        self.lyt_spd = QtWidgets.QFormLayout()                                                  # Form layout per il cursore velocità
        self.speed_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)                             # Cursore velocità (1..100)
        self.speed_slider.setRange(1, 100); self.speed_slider.setValue(40)                      # Valore predefinito
        self.speed_slider.valueChanged.connect(self.aggiorna_intervallo_timer)                  # Aggiorna in tempo reale velocità e moltiplicatore
        self.lbl_speed_val = QtWidgets.QLabel("Velocità (4.0x):")                               # Mostra chiaramente il moltiplicatore di velocità
        self.lyt_spd.addRow(self.lbl_speed_val, self.speed_slider)                              # Riga velocità
        self.lyt_play.addLayout(self.lyt_spd)                                                   # Aggiunge al gruppo Player
        self.layout.addWidget(self.grp_play)                                                    # Aggiunge Gruppo 2

        self.grp_dro = QtWidgets.QGroupBox("Controllo Numerico (DRO Tempo Reale)")              # Gruppo 3: Display DRO
        self.lyt_dro = QtWidgets.QVBoxLayout(self.grp_dro)                                      # Layout verticale DRO

        self.lbl_dro_op = QtWidgets.QLabel("Operazione: --")                                    # Etichetta operazione e stazione
        self.lbl_dro_op.setStyleSheet("font-weight: bold; color: #88C0D0;")
        self.lbl_dro_coords = QtWidgets.QLabel("X (Ø):   0.000 mm  (R: 0.000)\nZ    :   0.000 mm\nStato:   PRONTO")
        self.lbl_dro_coords.setStyleSheet("font-family: Consolas, monospace; font-size: 12px; font-weight: bold; background-color: #1E222A; color: #A3BE8C; padding: 6px; border-radius: 4px;")

        self.lbl_coll_alert = QtWidgets.QLabel("Controllo Collisioni: Nessuna interferenza.")   # Etichetta collisioni
        self.lbl_coll_alert.setWordWrap(True)
        self.lbl_coll_alert.setStyleSheet("color: #55FF55; font-weight: bold;")

        self.lyt_dro.addWidget(self.lbl_dro_op)                                                 # Aggiunge operazione
        self.lyt_dro.addWidget(self.lbl_dro_coords)                                             # Aggiunge DRO
        self.lyt_dro.addWidget(self.lbl_coll_alert)                                             # Aggiunge stato collisioni
        self.layout.addWidget(self.grp_dro)                                                     # Aggiunge Gruppo 3
        self.layout.addStretch()                                                                # Spinge tutto in alto
        self.form.setLayout(self.layout)                                                        # Applica il layout al widget principale

        if self.doc:                                                                            # Crea il pallino sulla punta utensile e il solido del grezzo in lavorazione
            self.tip_marker = self.doc.addObject("Part::Feature", "TMP_Sim_TipMarker")          # Sfera sulla punta utensile
            self.tip_marker.Label = "PUNTA UTENSILE ATTIVA"
            self.tip_marker.ViewObject.ShapeColor = (0.2, 1.0, 0.3)

            self.sim_stock_obj = self.doc.addObject("Part::Feature", "TMP_Sim_Stock")           # Solido del grezzo dinamico
            self.sim_stock_obj.Label = "GREZZO IN LAVORAZIONE (SIM)"
            self.sim_stock_obj.ViewObject.ShapeColor = (0.80, 0.60, 0.25)                       # Colore bronzo/ottone
            self.sim_stock_obj.ViewObject.Transparency = 20                                     # Leggera trasparenza per vedere bene l'inserto
            self.resetta_grezzo_simulato()                                                      # Costruisce il cilindro iniziale

        self.op_combo.currentIndexChanged.connect(self.ricarica_percorso_simulazione)           # Collega cambio operazione
        self.aggiorna_intervallo_timer()                                                        # Imposta velocità iniziale
        self.ricarica_percorso_simulazione()                                                    # Carica subito il percorso

    def resetta_grezzo_simulato(self):                                                          # Riporta il grezzo simulato allo stato cilindrico integro
        if not self.doc or not self.sim_stock_obj or not self.stock_2d: return                  # Controllo sicurezza
        self.stock_2d.reset()                                                                   # Azzera il profilo 2D
        self.sim_stock_obj.Shape = self.stock_2d.genera_shape_3d()                              # Rigenera il cilindro 3D integro
        self.last_cut_frame_idx = 0                                                             # Azzera l'indice di avanzamento taglio

    def salva_stato_iniziale(self):                                                             # Salva posizione di Torretta, Utensili e visibilità di Grezzo_Macchina
        if not self.doc: return                                                                 # Controllo sicurezza
        stock_orig = self.doc.getObject("Grezzo_Macchina")                                      # Cerca il Grezzo_Macchina originale
        if stock_orig and hasattr(stock_orig, "ViewObject") and stock_orig.ViewObject:          # Nasconde il grezzo statico mentre lavora quello dinamico
            self.backup_stato["stock_vis"] = bool(stock_orig.ViewObject.Visibility)
            stock_orig.ViewObject.Visibility = False

        turret = self.doc.getObject("Torretta_Macchina")                                        # Salva stato Torretta_Macchina
        if turret:
            self.backup_stato["turret"] = {
                "DistX_WCS": float(getattr(turret, "DistX_WCS", 25.0)),
                "DistZ_WCS": float(getattr(turret, "DistZ_WCS", 25.0)),
                "StazioneAttiva": int(getattr(turret, "StazioneAttiva", 1)),
                "Visibility": bool(turret.ViewObject.Visibility) if hasattr(turret, "ViewObject") and turret.ViewObject else True
            }
        self.backup_stato["tools"] = {}                                                         # Salva stato Utensili
        lib = self.doc.getObject("Libreria_Utensili")
        if lib and hasattr(lib, "Group"):
            for t in lib.Group:
                self.backup_stato["tools"][t.Name] = {
                    "OffsetTorretta": FreeCAD.Vector(getattr(t, "OffsetTorretta", FreeCAD.Vector(0, 0, 0))),
                    "RotazioneTorretta": list(getattr(t, "RotazioneTorretta", [0.0, 0.0, 0.0, 1.0])),
                    "Visibility": bool(t.ViewObject.Visibility) if hasattr(t, "ViewObject") and t.ViewObject else True
                }

    def ripristina_stato_iniziale(self):                                                        # Ripristina tutto allo stato originale quando si chiude il simulatore
        if not self.doc: return                                                                 # Controllo sicurezza
        stock_orig = self.doc.getObject("Grezzo_Macchina")                                      # Riaccende il Grezzo_Macchina originale
        if stock_orig and hasattr(stock_orig, "ViewObject") and stock_orig.ViewObject:
            stock_orig.ViewObject.Visibility = self.backup_stato.get("stock_vis", True)

        turret = self.doc.getObject("Torretta_Macchina")                                        # Ripristina la Torretta_Macchina
        if turret and "turret" in self.backup_stato:
            tb = self.backup_stato["turret"]
            turret.Proxy._is_executing = True
            try:
                turret.DistX_WCS = tb["DistX_WCS"]
                turret.DistZ_WCS = tb["DistZ_WCS"]
                turret.StazioneAttiva = tb["StazioneAttiva"]
            finally:
                turret.Proxy._is_executing = False
            turret.Proxy.execute(turret)
            if hasattr(turret, "ViewObject") and turret.ViewObject:
                turret.ViewObject.Visibility = tb["Visibility"]

        for t_name, bkp in self.backup_stato.get("tools", {}).items():                          # Ripristina gli utensili singoli
            t_obj = self.doc.getObject(t_name)
            if t_obj and hasattr(t_obj, "OffsetTorretta"):
                if not turret:
                    t_obj.Proxy._is_executing = True
                    try:
                        t_obj.OffsetTorretta = bkp["OffsetTorretta"]
                        t_obj.RotazioneTorretta = bkp["RotazioneTorretta"]
                    finally:
                        t_obj.Proxy._is_executing = False
                    t_obj.Proxy.execute(t_obj)
                if hasattr(t_obj, "ViewObject") and t_obj.ViewObject:
                    t_obj.ViewObject.Visibility = bkp["Visibility"]

    def popola_combo_operazioni(self):                                                          # Popola il menu a tendina con le operazioni presenti
        self.op_combo.clear()
        self.op_combo.addItem("★ Tutte le Operazioni in Sequenza", "ALL")
        if self.doc and self.doc.getObject("Operazioni_CAM"):
            ops_grp = self.doc.getObject("Operazioni_CAM")
            for op in ops_grp.Group:
                if hasattr(op, "PercorsoJSON"):
                    self.op_combo.addItem(f"• {op.Label}", op.Name)

    def ricarica_percorso_simulazione(self):                                                    # Ricalcola i fotogrammi assicurandosi che PercorsoJSON sia aggiornato
        self.metti_in_pausa()
        if not self.doc: return
        ops_grp = self.doc.getObject("Operazioni_CAM")
        lista_ops = []
        sel_data = self.op_combo.itemData(self.op_combo.currentIndex())
        if ops_grp and hasattr(ops_grp, "Group"):
            if sel_data == "ALL":
                lista_ops = list(ops_grp.Group)
            else:
                op_singola = self.doc.getObject(str(sel_data))
                if op_singola: lista_ops = [op_singola]

        for op in lista_ops:                                                                    # Rigenera i punti dell'operazione per essere identico alla linea verde!
            if hasattr(op, "Proxy") and hasattr(op.Proxy, "execute"):
                op.Proxy.execute(op)

        self.resetta_grezzo_simulato()                                                          # Ripristina il grezzo vergine
        self.frames = genera_frames_simulazione(self.doc, lista_ops, passo_interp_mm=1.0)       # Genera i fotogrammi
        self.current_frame_idx = 0
        self.is_updating_slider = True
        self.slider_timeline.setRange(0, max(len(self.frames) - 1, 0))
        self.slider_timeline.setValue(0)
        self.is_updating_slider = False

        if self.frames:
            self.applica_fotogramma(0)
        else:
            self.lbl_dro_op.setText("Nessuna operazione CAM trovata nel progetto!")

    def calcola_parametri_velocita(self):                                                       # Calcola intervallo ms e quanti fotogrammi avanzare per tick (fino a 40x!)
        val = self.speed_slider.value()                                                         # Valore slider 1..100
        if val <= 15:                                                                           # Movimento lento di precisione (1 frame alla volta)
            ms = int(110 - val * 5)                                                             # Da 105 ms a 35 ms
            steps = 1                                                                           # 1 singolo fotogramma per tick
        else:                                                                                   # Velocità alta / Turbo (fino a 45 frames per tick ogni 15 ms!)
            ms = 15                                                                             # Refresh rapido
            steps = max(1, int(round(((val - 10) / 90.0) ** 2.2 * 45.0)))                       # Da 1 fino a 45 fotogrammi per tick!
        return ms, steps                                                                        # Restituisce (ms, steps)

    def aggiorna_intervallo_timer(self):                                                        # Aggiorna l'etichetta del moltiplicatore e l'intervallo del QTimer
        ms, steps = self.calcola_parametri_velocita()                                           # Legge ms e steps
        fattore = round((steps * (100.0 / max(ms, 10))) / 6.0, 1)                               # Calcola il moltiplicatore visivo (es. 0.2x .. 50.0x)
        self.lbl_speed_val.setText(f"Velocità ({fattore}x):")                                   # Aggiorna il testo a fianco dello slider
        self.timer.setInterval(ms)                                                              # Aggiorna subito il QTimer

    def avvia_play(self):                                                                       # Avvia la riproduzione
        if not self.frames: return
        if self.current_frame_idx >= len(self.frames) - 1:                                      # Se era a fine corsa, riparte da zero col grezzo vergine
            self.resetta_grezzo_simulato()
            self.current_frame_idx = 0
        self.aggiorna_intervallo_timer()
        self.timer.start()

    def metti_in_pausa(self):                                                                   # Ferma il QTimer
        if self.timer.isActive():
            self.timer.stop()

    def passo_avanti(self):                                                                     # Avanza di un fotogramma (+1)
        self.metti_in_pausa()
        if self.current_frame_idx < len(self.frames) - 1:
            self.applica_fotogramma(self.current_frame_idx + 1)

    def passo_indietro(self):                                                                   # Torna indietro di un fotogramma (-1) ricalcolando il grezzo esatto
        self.metti_in_pausa()
        if self.current_frame_idx > 0:
            target = self.current_frame_idx - 1
            self.resetta_grezzo_simulato()
            self.applica_fotogramma(target)

    def torna_inizio(self):                                                                     # Riporta a zero e ripristina il grezzo integro
        self.metti_in_pausa()
        self.resetta_grezzo_simulato()
        if self.frames:
            self.applica_fotogramma(0)

    def on_slider_moved(self, val):                                                             # Gestisce lo spostamento manuale della barra temporale
        if self.is_updating_slider: return
        self.metti_in_pausa()
        target = int(val)
        if target < self.last_cut_frame_idx:                                                    # Se trascinato indietro, ricostruisce il grezzo fino a quel punto
            self.resetta_grezzo_simulato()
        self.applica_fotogramma(target)

    def on_timer_tick(self):                                                                    # Chiamato ad ogni battito del QTimer
        _, steps = self.calcola_parametri_velocita()                                            # Quanti fotogrammi percorrere in questo tick
        next_idx = self.current_frame_idx + steps                                               # Indice successivo
        if next_idx < len(self.frames):                                                         # Se dentro il percorso
            self.applica_fotogramma(next_idx)                                                   # Taglia tutti gli step intermedi e mostra next_idx
        else:                                                                                   # Fine simulazione raggiunta
            self.applica_fotogramma(len(self.frames) - 1)                                       # Completa l'ultimo fotogramma
            self.metti_in_pausa()                                                               # Ferma il timer
            self.lbl_dro_op.setText("Simulazione Completata! (Premi Reset o Play per rivedere)")

    def asporta_materiale_fino_a(self, target_idx):                                             # Aggiorna il profilo 2D su tutti i frame intermedi e rigenera il 3D una sola volta!
        if not self.chk_cut_stock.isChecked() or not self.sim_stock_obj or not self.stock_2d:
            self.last_cut_frame_idx = target_idx
            return
        if target_idx <= self.last_cut_frame_idx:
            return

        ha_tagliato = False                                                                     # Indica se almeno un frame intermedio ha asportato metallo
        for i in range(self.last_cut_frame_idx + 1, target_idx + 1):                            # Scorre TUTTI i fotogrammi intermedi senza saltarne nessuno!
            fr = self.frames[i]                                                                 # Fotogramma i-esimo
            if not fr.get("is_cut", False):                                                     # I movimenti rapidi G00 non asportano materiale
                continue
            mod = self.stock_2d.applica_segmento_taglio(                                        # Abbassa il profilo 2D del grezzo lungo (x1,z1)->(x,z)
                fr["x1"], fr["z1"], fr["x"], fr["z"],
                fr["cut_mode"], fr["w_lama"], fr["d_punta"]
            )
            if mod:                                                                             # Se il grezzo è stato toccato
                ha_tagliato = True                                                              # Segnala che serve rigenerare il solido di rivoluzione

        if ha_tagliato:                                                                         # Rigenera la Shape 3D per rivoluzione 360° una sola volta per tick!
            self.sim_stock_obj.Shape = self.stock_2d.genera_shape_3d()                          # Aggiorna il grezzo 3D in modo istantaneo e liscio

        self.last_cut_frame_idx = target_idx                                                    # Aggiorna l'ultimo frame processato

    def applica_fotogramma(self, idx):                                                          # Posiziona l'utensile esattamente sulla linea verde e aggiorna grezzo e DRO
        if not self.doc or not self.frames: return                                              # Controllo sicurezza
        idx = max(0, min(int(idx), len(self.frames) - 1))                                       # Limita indice

        self.asporta_materiale_fino_a(idx)                                                      # Aggiorna l'asportazione del grezzo fino al fotogramma idx
        self.current_frame_idx = idx                                                            # Salva indice corrente

        self.is_updating_slider = True                                                          # Allinea il cursore della timeline
        self.slider_timeline.setValue(idx)
        self.is_updating_slider = False

        fr = self.frames[idx]                                                                   # Dati del fotogramma corrente
        tx = float(fr["x"])                                                                     # Raggio X esatto del percorso
        tz = float(fr["z"])                                                                     # Quota Z esatta del percorso
        cmd = str(fr["cmd"])                                                                    # Comando attivo ("G0", "G1", "G32")
        f_val = float(fr["f"])                                                                  # Avanzamento F
        num_st = int(fr["stazione_num"])                                                        # Numero stazione
        sigla_st = str(fr["stazione_str"])                                                      # Sigla stazione
        t_name = str(fr["tool_name"])                                                           # Nome oggetto utensile

        wcs = get_wcs_origin(self.doc)                                                          # Origine WCS
        pos_punta_3d = FreeCAD.Vector(wcs.x + tx, wcs.y, wcs.z + tz)                            # Posizione 3D esatta sulla linea verde

        if hasattr(self, "tip_marker") and self.tip_marker:                                     # Aggiorna il pallino sulla punta utensile
            self.tip_marker.Shape = Part.makeSphere(1.1, pos_punta_3d)
            self.tip_marker.ViewObject.ShapeColor = (1.0, 0.2, 0.2) if cmd == "G0" else (0.2, 1.0, 0.3)

        turret = self.doc.getObject("Torretta_Macchina")                                        # Se esiste la Torretta 3D, muove la torretta portando la punta a (tx, tz)
        if turret and hasattr(turret, "Proxy") and hasattr(turret.Proxy, "muovi_punta_attiva_a"):
            turret.Proxy.muovi_punta_attiva_a(turret, tx, tz, num_stazione=num_st)
        else:                                                                                   # Altrimenti muove il singolo utensile compensando la posizione locale della punta
            lib = self.doc.getObject("Libreria_Utensili")
            if lib and hasattr(lib, "Group"):
                for t in lib.Group:
                    is_active_tool = (t.Name == t_name)
                    if hasattr(t, "ViewObject") and t.ViewObject:
                        t.ViewObject.Visibility = is_active_tool
                    if is_active_tool and hasattr(t, "OffsetTorretta"):
                        tip_loc = FreeCAD.Vector(0.0, 0.0, 0.0)
                        if hasattr(t, "Proxy") and hasattr(t.Proxy, "get_tip_local"):
                            tip_loc = t.Proxy.get_tip_local(t)                                  # Legge dove si trova la punta gialla rispetto all'origine dell'utensile
                        t.Proxy._is_executing = True
                        try:
                            t.OffsetTorretta = FreeCAD.Vector(tx - tip_loc.x, -tip_loc.y, tz - tip_loc.z)
                            t.RotazioneTorretta = [0.0, 0.0, 0.0, 1.0]
                        finally:
                            t.Proxy._is_executing = False
                        t.Proxy.execute(t)

        tipo_mov = "RAPIDO (G00)" if cmd == "G0" else ("FILETTO (G32)" if cmd == "G32" else "TAGLIO (G01)")
        self.lbl_dro_op.setText(f"[{sigla_st}] {fr['op_label']}  —  Frame {idx + 1}/{len(self.frames)}")
        self.lbl_dro_coords.setText(
            f"X (Ø): {tx * 2.0:8.3f} mm  (R: {tx:7.3f})\n"
            f"Z    : {tz:8.3f} mm\n"
            f"Modo : {tipo_mov}   F: {f_val:.3f} mm/g"
        )

        if self.chk_coll.isChecked():                                                           # Verifica collisioni contro il grezzo residuo
            self.esegui_controllo_collisione_frame(turret, t_name, cmd)

        FreeCADGui.updateGui()                                                                  # Aggiorna la vista 3D

    def esegui_controllo_collisione_frame(self, turret_obj, active_tool_name, cmd):             # Controlla collisioni contro il grezzo attualmente rimasto
        bersaglio = self.sim_stock_obj if (self.sim_stock_obj and self.chk_cut_stock.isChecked()) else self.doc.getObject("Grezzo_Macchina")
        if not bersaglio or not hasattr(bersaglio, "Shape") or bersaglio.Shape.isNull():
            return

        collisioni = []
        if turret_obj and hasattr(turret_obj, "Shape") and not turret_obj.Shape.isNull():
            try:
                if turret_obj.Shape.common(bersaglio.Shape).Volume > 0.2:
                    collisioni.append("Disco Torretta")
            except Exception: pass

        if cmd == "G0":                                                                         # Verifica urto in rapido G00
            t_obj = self.doc.getObject(active_tool_name) if active_tool_name else None
            if t_obj and hasattr(t_obj, "Shape") and not t_obj.Shape.isNull():
                try:
                    if t_obj.Shape.common(bersaglio.Shape).Volume > 2.0:
                        collisioni.append(f"Urto in Rapido G00 ({t_obj.Label})")
                except Exception: pass

        if collisioni:
            msg = "COLLISIONE: " + ", ".join(collisioni) + "!"
            self.lbl_coll_alert.setStyleSheet("color: #FF3333; font-weight: bold;")
            self.lbl_coll_alert.setText(msg)
            if self.chk_pause_coll.isChecked():
                self.metti_in_pausa()
        else:
            self.lbl_coll_alert.setStyleSheet("color: #55FF55; font-weight: bold;")
            self.lbl_coll_alert.setText("Controllo Collisioni: Nessuna interferenza.")

    def pulisci_oggetti_temporanei(self):                                                       # Rimuove in modo sicuro il marker punta e il grezzo temporaneo
        if not self.doc: return                                                                 # Controllo sicurezza
        for attr in ["tip_marker", "sim_stock_obj"]:                                            # Rimuove riferimenti salvati
            if hasattr(self, attr) and getattr(self, attr):
                try:
                    obj = getattr(self, attr)
                    if self.doc.getObject(obj.Name):
                        self.doc.removeObject(obj.Name)
                except Exception: pass
                setattr(self, attr, None)
        for obj in list(self.doc.Objects):                                                      # [CORRETTO] Usa obj.Name.startswith senza il doppio .Name!
            if obj.Name.startswith("TMP_Sim_"):
                try:
                    self.doc.removeObject(obj.Name)
                except Exception: pass

    def getStandardButtons(self):                                                               # Pulsante di chiusura del pannello
        return QtWidgets.QDialogButtonBox.Close

    def accept(self):                                                                           # Chiusura con conferma
        self.chiudi_simulatore()
        return True

    def reject(self):                                                                           # Chiusura con Esc / Close
        self.chiudi_simulatore()
        return True

    def chiudi_simulatore(self):                                                                # Ferma il timer e ripristina la scena originale
        self.metti_in_pausa()
        self.pulisci_oggetti_temporanei()
        self.ripristina_stato_iniziale()
        if self.doc: self.doc.recompute()
        if FreeCADGui.ActiveDocument: FreeCADGui.ActiveDocument.resetEdit()
        FreeCADGui.Control.closeDialog()