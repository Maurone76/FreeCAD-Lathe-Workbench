import FreeCAD                                                                                  # Importa il modulo base di FreeCAD
import FreeCADGui                                                                               # Importa il modulo interfaccia grafica di FreeCAD
import Part                                                                                     # Importa il modulo geometrico Part
import math                                                                                     # Importa le funzioni matematiche
import json                                                                                     # Importa il modulo JSON per salvare i punti del percorso CAM
from PySide import QtCore, QtGui                                                                # Importa i moduli grafici PySide
try:                                                                                            # Tenta di importare QtWidgets per compatibilità Qt5/Qt6
    from PySide import QtWidgets                                                                # Assegna QtWidgets
except ImportError:                                                                             # Fallback per versioni meno recenti
    QtWidgets = QtGui                                                                           # Usa QtGui come alias di QtWidgets

import LatheResources                                                                           # Importa il gestore delle icone SVG


TIPI_CICLO_SGROSSO = [                                                                          # Modalità operative supportate dal ciclo di sgrossatura
    "Sfacciatura + Sgrossatura Esterna",                                                        # Ciclo combinato: prima intesta a Z=0 e poi sgrossa lungo Z-
    "Solo Sgrossatura Esterna (OD)",                                                            # Solo passate longitudinali esterne lungo Z-
    "Solo Sfacciatura Frontale (Facing)",                                                       # Solo passate radiali di intestatura lungo X-
    "Sgrossatura Interna / Bareno (ID)"                                                         # Passate longitudinali interne in allargamento verso X+
]                                                                                               # Fine elenco cicli


def get_wcs_origin(doc=None):                                                                   # Restituisce il punto di origine del WCS (Setup_Macchina)
    if doc is None:                                                                             # Se non è passato il documento
        doc = FreeCAD.ActiveDocument                                                            # Usa il documento attivo
    if doc and doc.getObject("Setup_Macchina"):                                                 # Se esiste Setup_Macchina
        s = doc.getObject("Setup_Macchina")                                                     # Ottiene il riferimento al Setup
        if hasattr(s, "Origine"):                                                               # Verifica la proprietà Origine
            return FreeCAD.Vector(s.Origine)                                                    # Restituisce il vettore Origine WCS
    return FreeCAD.Vector(0.0, 0.0, 0.0)                                                        # Fallback su (0,0,0)


def get_setup_safe_clearances(doc=None):                                                        # Legge le distanze di sicurezza X e Z dal Setup_Macchina
    if doc is None:                                                                             # Se non è passato il documento
        doc = FreeCAD.ActiveDocument                                                            # Usa il documento attivo
    if doc and doc.getObject("Setup_Macchina"):                                                 # Se esiste Setup_Macchina
        s = doc.getObject("Setup_Macchina")                                                     # Ottiene l'oggetto Setup
        return float(getattr(s, "SicurezzaX", 2.0)), float(getattr(s, "SicurezzaZ", 2.0))       # Restituisce SicurezzaX e SicurezzaZ
    return 2.0, 2.0                                                                             # Valori di sicurezza predefiniti (2 mm)


def get_stock_info(doc=None):                                                                   # Legge tutte le quote del Grezzo_Macchina e il limite griffe
    if doc is None:                                                                             # Se non è passato il documento
        doc = FreeCAD.ActiveDocument                                                            # Usa il documento attivo
    info = {                                                                                    # Dizionario valori predefiniti del grezzo
        "r_ext": 25.0,                                                                          # Raggio esterno effettivo barra
        "r_rot": 25.0,                                                                          # Raggio massimo sugli spigoli (per quadro/esagono)
        "r_int": 0.0,                                                                           # Raggio foro interno (per tubo)
        "z_front": 1.5,                                                                         # Quota Z frontale grezzo (rispetto a WCS)
        "z_back": -98.5,                                                                        # Quota Z posteriore grezzo
        "z_lim_chuck": -75.5                                                                    # Quota Z limite collisione griffe mandrino
    }                                                                                           # Fine dizionario base
    if doc and doc.getObject("Grezzo_Macchina"):                                                # Se esiste Grezzo_Macchina nel progetto
        st = doc.getObject("Grezzo_Macchina")                                                   # Ottiene l'oggetto Grezzo
        d_base = float(getattr(st, "DiametroEsterno", 50.0))                                    # Diametro o chiave base
        sx = float(getattr(st, "SovrametalloRadialeX", 0.0))                                    # Sovrametallo radiale X+
        r_eff = max((d_base / 2.0) + sx, 1.0)                                                   # Raggio effettivo della barra
        d_rot = float(getattr(st, "DiametroMaxRotazione", r_eff * 2.0))                         # Diametro massimo in rotazione sugli spigoli
        r_rot = max(d_rot / 2.0, r_eff)                                                         # Raggio d'inviluppo massimo
        forma = str(getattr(st, "FormaGrezzo", "Cilindro Pieno"))                               # Tipo di barra
        r_int = (float(getattr(st, "DiametroForoInterno", 0.0)) / 2.0) if forma != "Cilindro Pieno" else 0.0
        sz = float(getattr(st, "SovrametalloFrontaleZ", 1.5))                                   # Sovrametallo frontale Z+
        lung = float(getattr(st, "LunghezzaTotale", 100.0))                                     # Lunghezza totale barra
        wcs = get_wcs_origin(doc)                                                               # Origine WCS
        z_lim_abs = float(getattr(st, "Z_Limite_Mandrino", wcs.z + sz - lung + 23.0))           # Limite assoluto griffe
        info["r_ext"] = r_eff                                                                   # Aggiorna raggio esterno
        info["r_rot"] = r_rot                                                                   # Aggiorna raggio inviluppo spigoli
        info["r_int"] = max(r_int, 0.0)                                                         # Aggiorna raggio interno
        info["z_front"] = sz                                                                    # Quota Z frontale relativa al WCS
        info["z_back"] = sz - lung                                                              # Quota Z posteriore relativa al WCS
        info["z_lim_chuck"] = z_lim_abs - wcs.z                                                 # Quota Z limite griffe relativa al WCS
    return info                                                                                 # Restituisce il dizionario completo


def trova_candidati_pezzo(doc=None):                                                            # Trova i solidi 3D del documento candidati ad essere il Pezzo Finito
    if doc is None:                                                                             # Verifica documento
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
    if not doc:                                                                                 # Se non c'è documento
        return []                                                                               # Restituisce lista vuota
    esclusi = {"Setup_Macchina", "Grezzo_Macchina", "Torretta_Macchina", "Libreria_Utensili", "Operazioni_CAM"}
    utensili_names = set()                                                                      # Insieme nomi utensili da escludere
    lib = doc.getObject("Libreria_Utensili")                                                    # Gruppo Magazzino Utensili
    if lib and hasattr(lib, "Group"):                                                           # Se esiste
        for t in lib.Group: utensili_names.add(t.Name)                                          # Esclude gli utensili del magazzino
    ops = doc.getObject("Operazioni_CAM")                                                       # Gruppo Operazioni CAM
    if ops and hasattr(ops, "Group"):                                                           # Se esiste
        for o in ops.Group: utensili_names.add(o.Name)                                          # Esclude le operazioni CAM

    candidati = []                                                                              # Lista oggetti 3D validi
    for obj in doc.Objects:                                                                     # Scorre tutti gli oggetti del progetto
        if obj.Name in esclusi or obj.Name in utensili_names or obj.Name.startswith("TMP_"):    # Salta oggetti di sistema e anteprime
            continue                                                                            # Passa al successivo
        if hasattr(obj, "ToolName") or hasattr(obj, "TipoCiclo"):                               # Salta utensili e cicli CAM
            continue                                                                            # Passa al successivo
        if hasattr(obj, "Shape") and obj.Shape and not obj.Shape.isNull():                      # Se ha una Shape geometrica valida
            if hasattr(obj.Shape, "Solids") and len(obj.Shape.Solids) > 0:                      # Se contiene almeno un solido 3D
                candidati.append(obj)                                                           # Aggiunge come candidato Pezzo Finito
    return candidati                                                                            # Restituisce i solidi trovati


def calcola_z_fine_da_pezzo(part_obj, doc=None):                                                # Calcola la quota Z finale esatta del pezzo rispetto al WCS
    if doc is None:                                                                             # Verifica documento
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
    wcs = get_wcs_origin(doc)                                                                   # Origine WCS
    if part_obj and hasattr(part_obj, "Shape") and part_obj.Shape and not part_obj.Shape.isNull():
        return float(part_obj.Shape.BoundBox.ZMin - wcs.z)                                      # Fine esatta del pezzo lungo Z riferita al WCS
    stock_info = get_stock_info(doc)                                                            # Fallback sul grezzo se non c'è il pezzo 3D
    return max(stock_info["z_lim_chuck"] + 5.0, -50.0)                                          # Quota di sicurezza davanti alle griffe


def campiona_profilo_pezzo(part_obj, wcs, z_da, z_a, modalita_id=False, num_campioni=120):      # Ricava il profilo (Z, R) sezionando/campionando il solido 3D del pezzo
    z_max = max(float(z_da), float(z_a))                                                        # Quota Z iniziale (più a destra, verso Z+)
    z_min = min(float(z_da), float(z_a))                                                        # Quota Z finale (più a sinistra, verso Z-)
    n = max(int(num_campioni), 20)                                                              # Numero di stazioni di campionamento lungo Z
    dz = (z_max - z_min) / float(n) if abs(z_max - z_min) > 1e-4 else 1.0                       # Passo di campionamento assiale

    if not part_obj or not hasattr(part_obj, "Shape") or part_obj.Shape.isNull():               # Se non è stato specificato un solido Pezzo 3D
        return [(z_max - i * dz, 0.0) for i in range(n + 1)]                                    # Restituisce raggio zero (cilindratura libera)

    shape = part_obj.Shape                                                                      # Forma 3D del pezzo finito
    bb = shape.BoundBox                                                                         # BoundBox del pezzo
    r_max_bb = max(abs(bb.XMax - wcs.x), abs(bb.XMin - wcs.x), abs(bb.YMax - wcs.y), abs(bb.YMin - wcs.y)) + 20.0
    profilo = []                                                                                # Lista di tuple (z_rel, raggio_pezzo)

    for i in range(n + 1):                                                                      # Cicla lungo l'asse Z da z_max a z_min
        z_rel = z_max - i * dz                                                                  # Quota Z relativa al WCS
        z_glob = wcs.z + z_rel                                                                  # Quota Z globale nel documento
        if z_glob < bb.ZMin - 0.05 or z_glob > bb.ZMax + 0.05:                                  # Se la quota Z è fuori dal pezzo 3D
            profilo.append((z_rel, 0.0 if not modalita_id else r_max_bb))                       # Raggio zero (esterno) o libero (interno)
            continue                                                                            # Passa alla quota Z successiva

        r_rilevato = None                                                                       # Raggio rilevato a questa quota Z
        for dir_vec in [FreeCAD.Vector(1, 0, 0), FreeCAD.Vector(0, 1, 0)]:                      # Sonda lungo +X e +Y per robustezza su spianature/chiavette
            p_start = FreeCAD.Vector(wcs.x, wcs.y, z_glob)                                      # Punto sull'asse mandrino alla quota Z corrente
            p_end = p_start + (dir_vec * r_max_bb)                                              # Punto esterno oltre il BoundBox
            seg = Part.makeLine(p_start, p_end)                                                 # Raggio sonda radiale
            try:                                                                                # Calcola l'intersezione tra il raggio sonda e il pezzo 3D
                comm = shape.common(seg)                                                        # Segmento interno al materiale del pezzo
                if comm and comm.Vertexes:                                                      # Se il raggio sonda interseca il pezzo
                    distanze = [ (v.Point - p_start).Length for v in comm.Vertexes ]            # Distanze radiali di tutti i vertici d'intersezione
                    if modalita_id:                                                             # Per barenatura interna interessa la parete interna (raggio minimo > 0)
                        d_val = min(distanze)                                                   # Raggio del foro interno del pezzo
                        r_rilevato = d_val if r_rilevato is None else min(r_rilevato, d_val)
                    else:                                                                       # Per tornitura esterna interessa il raggio massimo esterno
                        d_val = max(distanze)                                                   # Raggio esterno del pezzo a questa Z
                        r_rilevato = d_val if r_rilevato is None else max(r_rilevato, d_val)
            except Exception:                                                                   # Ignora eventuali errori geometrici locali
                pass                                                                            # Continua

        if r_rilevato is None:                                                                  # Se non ha toccato il pezzo a questa Z
            r_rilevato = 0.0 if not modalita_id else r_max_bb                                   # Libero
        profilo.append((z_rel, float(r_rilevato)))                                              # Aggiunge (z_rel, raggio) alla tabella profilo

    if not modalita_id:                                                                         # Applicazione monotona anti-sottosquadro per sgrossatura standard
        r_corrente = 0.0                                                                        # Impedisce all'utensile di scendere in gole strette durante la sgrossatura
        profilo_monotono = []                                                                   # Profilo protetto dai sottosquadri
        for z_r, r_val in profilo:                                                              # Scorre dalla fronte Z+ verso il mandrino Z-
            if r_val > r_corrente:                                                              # Se il diametro del pezzo cresce andando verso il mandrino
                r_corrente = r_val                                                              # Mantiene il raggio maggiore (non scava dentro le gole)
            profilo_monotono.append((z_r, r_corrente))                                          # Registra il raggio monotono sicuro
        return profilo_monotono                                                                 # Restituisce il profilo esterno anti-tallonamento
    return profilo                                                                              # Restituisce il profilo interno


def calcola_percorso_sgrossatura(                                                               # Genera la lista movimenti (G0/G1) e le Shapes 3D del percorso
    wcs, tipo_ciclo, part_obj, stock_info,                                                      # Riferimenti geometrici
    z_start, z_end, r_target_manuale, usa_pezzo_3d,                                             # Limiti di lavoro
    ap, sovra_x, sovra_z, distacco, angolo_distacco, sic_x, sic_z, feed_work                    # Parametri tecnologici e angolo di distacco
):                                                                                              # Inizio motore di calcolo percorso CAM
    moves = []                                                                                  # Lista movimenti: {"cmd": "G0"/"G1", "x": r, "z": z, "f": feed}
    edges_rapidi = []                                                                           # Segmenti 3D per i movimenti rapidi G00 (Rosso)
    edges_lavoro = []                                                                           # Segmenti 3D per i movimenti di lavoro G01 (Verde)

    r_grezzo = stock_info["r_rot"]                                                              # Raggio esterno massimo del grezzo (inclusi spigoli quadro/esagono)
    r_foro_grezzo = stock_info["r_int"]                                                         # Raggio foro interno del grezzo
    z_front_grezzo = stock_info["z_front"]                                                      # Quota Z della faccia grezza anteriore
    z_lim_griffe = stock_info["z_lim_chuck"]                                                    # Quota Z limite collisione griffe

    z_ini = float(z_start)                                                                      # Quota Z di inizio lavorazione
    z_fin = max(float(z_end), z_lim_griffe)                                                     # Blocca automaticamente Z_Fine prima delle griffe autocentrante!
    passo_ap = max(float(ap), 0.1)                                                              # Profondità di passata radiale/assiale (mm)
    sx = max(float(sovra_x), 0.0)                                                               # Sovrametallo radiale di finitura su X
    sz = max(float(sovra_z), 0.0)                                                               # Sovrametallo assiale di finitura su Z
    ret_len = max(float(distacco), 0.2)                                                         # Lunghezza del tratto di distacco a fine passata (mm)
    ang_rad = math.radians(max(0.0, min(float(angolo_distacco), 90.0)))                         # Angolo di distacco in radianti (0°..90°, default 45°)
    ret_dx = max(ret_len * math.sin(ang_rad), 0.1)                                              # Componente radiale X del distacco
    ret_dz = ret_len * math.cos(ang_rad)                                                        # Componente assiale Z del distacco

    safe_r = r_grezzo + max(float(sic_x), 1.0)                                                  # Raggio di sicurezza esterno per i rapidi G00
    safe_z = max(z_front_grezzo, z_ini) + max(float(sic_z), 1.0)                                # Quota Z di sicurezza frontale per i rapidi G00

    curr_pt = [safe_r, safe_z]                                                                  # Posizione corrente dell'utensile (Raggio X, Quota Z)
    moves.append({"cmd": "G0", "x": curr_pt[0], "z": curr_pt[1], "f": 0.0})                     # Punto iniziale di approccio in sicurezza

    def add_segment(cmd, next_r, next_z):                                                       # Funzione interna per registrare un movimento e creare la linea 3D
        p1 = FreeCAD.Vector(wcs.x + curr_pt[0], wcs.y, wcs.z + curr_pt[1])                      # Punto 3D di partenza sul piano XZ
        p2 = FreeCAD.Vector(wcs.x + next_r, wcs.y, wcs.z + next_z)                              # Punto 3D di arrivo sul piano XZ
        if (p2 - p1).Length > 1e-4:                                                             # Se lo spostamento non è nullo
            edge = Part.makeLine(p1, p2)                                                        # Crea il segmento geometrico 3D
            if cmd == "G0":                                                                     # Se è un movimento rapido
                edges_rapidi.append(edge)                                                       # Aggiunge ai rapidi (Rosso)
            else:                                                                               # Se è un movimento di taglio in lavoro
                edges_lavoro.append(edge)                                                       # Aggiunge al taglio (Verde)
            moves.append({"cmd": cmd, "x": float(next_r), "z": float(next_z), "f": float(feed_work if cmd == "G1" else 0.0)})
            curr_pt[0] = float(next_r)                                                          # Aggiorna X corrente
            curr_pt[1] = float(next_z)                                                          # Aggiorna Z corrente

    esegui_facing = tipo_ciclo in ["Sfacciatura + Sgrossatura Esterna", "Solo Sfacciatura Frontale (Facing)"]
    esegui_od = tipo_ciclo in ["Sfacciatura + Sgrossatura Esterna", "Solo Sgrossatura Esterna (OD)"]
    esegui_id = (tipo_ciclo == "Sgrossatura Interna / Bareno (ID)")                             # Verifica se è una barenatura interna

    if esegui_facing:                                                                           # 1. CICLO DI SFACCIATURA FRONTALE (FACING)
        z_target_face = 0.0 + sz                                                                # Quota Z finale della faccia intestata (0.0 + sovrametallo Z)
        z_partenza_face = max(z_front_grezzo, z_ini)                                            # Parte dalla faccia anteriore del grezzo
        r_arrivo_face = max(r_foro_grezzo - 0.5, -0.4)                                          # Scende leggermente sotto centro (-0.4 mm) per eliminare il testimone

        if z_partenza_face > z_target_face + 1e-4:                                              # Se c'è materiale frontale da intestare
            z_curr_f = z_partenza_face                                                          # Quota Z di calcolo passata
            while z_curr_f > z_target_face + 1e-4:                                              # Cicla per ogni passata di sfacciatura
                z_curr_f = max(z_curr_f - passo_ap, z_target_face)                              # Quota Z della passata corrente
                add_segment("G0", r_grezzo + max(sic_x, 1.0), z_curr_f)                         # Si porta in rapido fuori diametro alla quota Z di passata
                add_segment("G1", r_arrivo_face, z_curr_f)                                      # Taglia radialmente lungo -X fino al centro (o al foro)
                add_segment("G1", r_arrivo_face + ret_dx, z_curr_f + max(ret_dz, 0.2))          # Stacca con l'angolo impostato
                add_segment("G0", r_grezzo + max(sic_x, 1.0), z_curr_f + max(ret_dz, 0.2))      # Risale in rapido sopra il diametro esterno
        else:                                                                                   # Esegue comunque una passata di pulizia frontale a z_target_face
            add_segment("G0", r_grezzo + max(sic_x, 1.0), z_target_face)                        # Posizionamento rapido esterno
            add_segment("G1", r_arrivo_face, z_target_face)                                     # Taglio frontale fino al centro
            add_segment("G1", r_arrivo_face + ret_dx, z_target_face + max(ret_dz, 0.2))         # Distacco angolato
            add_segment("G0", r_grezzo + max(sic_x, 1.0), safe_z)                               # Ritorno in sicurezza

    if esegui_od:                                                                               # 2. CICLO DI SGROSSATURA ESTERNA LONGITUDINALE (OD)
        z_part_od = 0.0 + sz if esegui_facing else z_ini                                        # Parte da Z=0 se ha appena sfacciato, altrimenti da z_ini
        if usa_pezzo_3d and part_obj:                                                           # Se usa la sagoma del modello 3D del pezzo
            prof = campiona_profilo_pezzo(part_obj, wcs, z_part_od, z_fin, modalita_id=False)   # Campiona il profilo esterno (Z, R)
            prof_offset = [(z_p + sz, r_p + sx) for (z_p, r_p) in prof]                         # Applica i sovrametalli di finitura X e Z
            r_min_prof = min(r_p for (_, r_p) in prof_offset) if prof_offset else (r_target_manuale + sx)
        else:                                                                                   # Se lavora a diametro costante manuale
            r_cost = max(float(r_target_manuale) + sx, 0.0)                                     # Raggio cilindrico finale + sovrametallo X
            prof_offset = [(z_part_od, r_cost), (z_fin, r_cost)]                                # Profilo cilindrico dritto
            r_min_prof = r_cost                                                                 # Raggio minimo da raggiungere

        r_curr = r_grezzo                                                                       # Parte dal raggio esterno del grezzo
        while r_curr > r_min_prof + 1e-4:                                                       # Cicla scendendo di livello in livello con passo Ap
            r_curr = max(r_curr - passo_ap, r_min_prof)                                         # Raggio di lavoro della passata corrente

            z_arresto = z_fin                                                                   # Calcola fino a quale Z può arrivare senza invadere il pezzo
            for i in range(len(prof_offset) - 1):                                               # Scorre i segmenti del profilo campionato
                z1, r1 = prof_offset[i]                                                         # Inizio segmento
                z2, r2 = prof_offset[i + 1]                                                     # Fine segmento
                if r1 > r_curr + 1e-4:                                                          # Se già all'inizio il pezzo è più alto di r_curr
                    z_arresto = z1                                                              # Si ferma subito a z1
                    break                                                                       # Esce
                if r2 > r_curr + 1e-4 and abs(r2 - r1) > 1e-5:                                  # Se incontra uno spallamento o un cono
                    t = (r_curr - r1) / (r2 - r1)                                               # Frazione di intersezione lineare sul cono/spallamento
                    z_arresto = z1 + t * (z2 - z1)                                              # Quota Z esatta di arresto contro il profilo
                    break                                                                       # Esce

            if z_part_od - z_arresto > 0.05:                                                    # Se la corsa di taglio lungo Z è significativa (> 0.05 mm)
                add_segment("G0", r_curr + ret_dx, z_part_od + max(sic_z, 1.0))                 # Avvicinamento rapido sopra il punto d'inizio
                add_segment("G0", r_curr, z_part_od + max(sic_z, 1.0))                          # Scende in rapido al raggio della passata
                add_segment("G1", r_curr, z_arresto)                                            # Taglio longitudinale G01 lungo -Z fino a z_arresto
                add_segment("G1", r_curr + ret_dx, min(z_arresto + ret_dz, safe_z))             # Distacco con l'AngoloDistacco scelto (es. 45°)
                add_segment("G0", r_curr + ret_dx, z_part_od + max(sic_z, 1.0))                 # Ritorno rapido a destra verso Z+

        add_segment("G0", safe_r, safe_z)                                                       # Disimpegno finale in sicurezza esterno

    if esegui_id:                                                                               # 3. CICLO DI SGROSSATURA INTERNA / BARENATURA (ID)
        r_start_id = max(r_foro_grezzo, 2.0)                                                    # Parte dal raggio del pre-foro nel grezzo
        r_max_id = max(float(r_target_manuale) - sx, r_start_id + 0.5)                          # Raggio interno finale da raggiungere (meno sovrametallo X)
        r_safe_id = max(r_start_id - max(sic_x, 1.0), 0.5)                                      # Raggio di sicurezza verso il centro per il ritorno del bareno

        add_segment("G0", r_start_id, safe_z)                                                   # Porta il bareno davanti al foro in Z di sicurezza
        r_curr = r_start_id                                                                     # Raggio iniziale di barenatura
        while r_curr < r_max_id - 1e-4:                                                         # Cicla allargando il foro verso +X con passo Ap
            r_curr = min(r_curr + passo_ap, r_max_id)                                           # Raggio della passata interna corrente
            add_segment("G0", r_curr, z_ini + max(sic_z, 1.0))                                  # Posiziona il bareno al raggio di passata fuori dal foro
            add_segment("G1", r_curr, z_fin)                                                    # Passata interna di barenatura lungo -Z
            add_segment("G1", max(r_curr - ret_dx, r_safe_id), min(z_fin + ret_dz, safe_z))     # Stacca verso il centro (-X) con l'AngoloDistacco scelto
            add_segment("G0", max(r_curr - ret_dx, r_safe_id), z_ini + max(sic_z, 1.0))         # Esce in rapido dal foro lungo +Z

        add_segment("G0", safe_r, safe_z)                                                       # Ritorno finale in posizione sicura

    shapes_all = []                                                                             # Lista di tutte le linee per il Compound finale
    if edges_rapidi:                                                                            # Se ci sono movimenti rapidi
        shapes_all.extend(edges_rapidi)                                                         # Aggiunge i segmenti rapidi
    if edges_lavoro:                                                                            # Se ci sono movimenti di taglio
        shapes_all.extend(edges_lavoro)                                                         # Aggiunge i segmenti di taglio

    if shapes_all:                                                                              # Se il percorso contiene segmenti
        comp = Part.makeCompound(shapes_all)                                                    # Crea il Compound 3D del percorso utensile
    else:                                                                                       # Fallback se nessun segmento generato
        comp = Part.makeSphere(0.5, wcs)                                                        # Piccola sfera segnaposto

    comp_rapidi = Part.makeCompound(edges_rapidi) if edges_rapidi else None                     # Compound separato per i rapidi (per l'anteprima bicolore)
    comp_lavoro = Part.makeCompound(edges_lavoro) if edges_lavoro else None                     # Compound separato per il lavoro (per l'anteprima bicolore)
    return comp, comp_rapidi, comp_lavoro, moves, z_fin                                         # Restituisce geometrie, lista movimenti G-Code e Z effettiva


class LatheRoughingObject:                                                                      # Classe Proxy per l'operazione parametrica di Sgrossatura
    def __init__(self, obj):                                                                    # Costruttore del Proxy
        self._is_executing = False                                                              # Semaforo anti-ricorsione
        self.ensure_properties(obj)                                                             # Garantisce la presenza di tutte le proprietà
        obj.Proxy = self                                                                        # Collega il Proxy all'oggetto FreeCAD

    def ensure_properties(self, obj):                                                           # Crea tutte le proprietà dell'operazione se mancanti
        if not hasattr(obj, "OperationName"):                                                   # Nome operazione
            obj.addProperty("App::PropertyString", "OperationName", "Operazione", "Nome operazione").OperationName = "Sgrossatura 1"
        if not hasattr(obj, "TipoCiclo"):                                                       # Modalità ciclo di sgrossatura
            obj.addProperty("App::PropertyEnumeration", "TipoCiclo", "Operazione", "Tipo ciclo di sgrossatura")
            obj.TipoCiclo = TIPI_CICLO_SGROSSO                                                  # Assegna le 4 modalità
        if not hasattr(obj, "UtensileAssegnato"):                                               # Nome dell'utensile scelto dal Magazzino
            obj.addProperty("App::PropertyString", "UtensileAssegnato", "Operazione", "Utensile utilizzato").UtensileAssegnato = ""
        if not hasattr(obj, "PezzoRiferimento"):                                                # Nome dell'oggetto solido 3D del pezzo finito
            obj.addProperty("App::PropertyString", "PezzoRiferimento", "Geometria", "Nome oggetto Pezzo 3D").PezzoRiferimento = ""
        if not hasattr(obj, "UsaProfiloPezzo3D"):                                               # Flag per seguire la sagoma 3D del pezzo
            obj.addProperty("App::PropertyBool", "UsaProfiloPezzo3D", "Geometria", "Segui sagoma del Pezzo 3D").UsaProfiloPezzo3D = True
        if not hasattr(obj, "Z_Inizio"):                                                        # Quota Z di inizio lavorazione (mm)
            obj.addProperty("App::PropertyFloat", "Z_Inizio", "Geometria", "Quota Z iniziale (mm)").Z_Inizio = 1.5
        if not hasattr(obj, "Z_Fine"):                                                          # Quota Z finale verso il mandrino (mm)
            obj.addProperty("App::PropertyFloat", "Z_Fine", "Geometria", "Quota Z finale (mm)").Z_Fine = -60.0
        if not hasattr(obj, "DiametroFinaleManuale"):                                           # Diametro finale nel caso di cilindratura manuale (mm)
            obj.addProperty("App::PropertyFloat", "DiametroFinaleManuale", "Geometria", "Diametro finale manuale (mm)").DiametroFinaleManuale = 30.0
        if not hasattr(obj, "ProfonditaPassata"):                                               # Profondità di passata Ap sul raggio (mm)
            obj.addProperty("App::PropertyFloat", "ProfonditaPassata", "Parametri Taglio", "Profondità di passata Ap (mm)").ProfonditaPassata = 2.0
        if not hasattr(obj, "SovrametalloFinituraX"):                                           # Sovrametallo radiale lasciato per la finitura (mm)
            obj.addProperty("App::PropertyFloat", "SovrametalloFinituraX", "Parametri Taglio", "Sovrametallo finitura su X (mm)").SovrametalloFinituraX = 0.3
        if not hasattr(obj, "SovrametalloFinituraZ"):                                           # Sovrametallo assiale lasciato per la finitura (mm)
            obj.addProperty("App::PropertyFloat", "SovrametalloFinituraZ", "Parametri Taglio", "Sovrametallo finitura su Z (mm)").SovrametalloFinituraZ = 0.1
        if not hasattr(obj, "DistaccoRitorno"):                                                 # Lunghezza del distacco utensile a fine passata (mm)
            obj.addProperty("App::PropertyFloat", "DistaccoRitorno", "Parametri Taglio", "Lunghezza distacco utensile in ritorno (mm)").DistaccoRitorno = 1.0
        if not hasattr(obj, "AngoloDistacco"):                                                  # Angolo di distacco utensile in ritorno (0°..90°, default 45°)
            obj.addProperty("App::PropertyFloat", "AngoloDistacco", "Parametri Taglio", "Angolo di distacco in ritorno (gradi)").AngoloDistacco = 45.0
        if not hasattr(obj, "VelocitaTaglio"):                                                  # Velocità di taglio Vc o RPM
            obj.addProperty("App::PropertyFloat", "VelocitaTaglio", "Parametri Taglio", "Velocità di taglio Vc / RPM").VelocitaTaglio = 180.0
        if not hasattr(obj, "AvanzamentoLavoro"):                                               # Avanzamento di sgrossatura (mm/giro)
            obj.addProperty("App::PropertyFloat", "AvanzamentoLavoro", "Parametri Taglio", "Avanzamento F (mm/giro)").AvanzamentoLavoro = 0.25
        if not hasattr(obj, "PercorsoJSON"):                                                    # Stringa JSON con tutti i punti calcolati per Simulazione e G-Code
            obj.addProperty("App::PropertyString", "PercorsoJSON", "Dati CAM", "Punti percorso per Simulatore e G-Code").PercorsoJSON = "[]"

    def onDocumentRestored(self, obj):                                                          # Eseguito alla riapertura di un file salvato
        self._is_executing = False                                                              # Sblocca il flag
        self.ensure_properties(obj)                                                             # Verifica le proprietà

    def execute(self, obj):                                                                     # Ricalcola il percorso utensile 3D e i punti G-Code
        if getattr(self, "_is_executing", False):                                               # Evita loop ricorsivi
            return                                                                              # Esce subito
        self._is_executing = True                                                               # Blocca esecuzioni concorrenti
        try:                                                                                    # Blocco protetto di calcolo CAM
            self.ensure_properties(obj)                                                         # Verifica attributi
            doc = obj.Document                                                                  # Documento corrente
            wcs = get_wcs_origin(doc)                                                           # Origine WCS
            sic_x, sic_z = get_setup_safe_clearances(doc)                                       # Distanze di sicurezza dal Setup
            stock_info = get_stock_info(doc)                                                    # Informazioni dal Grezzo_Macchina
            part_obj = doc.getObject(obj.PezzoRiferimento) if (doc and obj.PezzoRiferimento) else None

            comp, _, _, moves, _ = calcola_percorso_sgrossatura(                                # Esegue il calcolo matematico delle passate
                wcs, str(obj.TipoCiclo), part_obj, stock_info,                                  # Riferimenti
                obj.Z_Inizio, obj.Z_Fine, obj.DiametroFinaleManuale / 2.0, obj.UsaProfiloPezzo3D,
                obj.ProfonditaPassata, obj.SovrametalloFinituraX, obj.SovrametalloFinituraZ,
                obj.DistaccoRitorno, obj.AngoloDistacco, sic_x, sic_z, obj.AvanzamentoLavoro    # Passa anche AngoloDistacco
            )                                                                                   # Fine calcolo
            obj.PercorsoJSON = json.dumps(moves)                                                # Salva i movimenti per il Simulatore e il Post-Processor
            obj.Shape = comp                                                                    # Assegna la geometria 3D del percorso all'oggetto
            if hasattr(obj, "ViewObject") and obj.ViewObject:                                   # Imposta il colore delle linee del percorso
                obj.ViewObject.LineColor = (0.15, 0.90, 0.25)                                   # Verde brillante per il tracciato utensile
                obj.ViewObject.LineWidth = 2.0                                                  # Spessore linea ben visibile nel 3D
        except Exception as e:                                                                  # Cattura errori imprevisti
            FreeCAD.Console.PrintError(f"Errore calcolo Sgrossatura: {e}\n")                    # Stampa in console
        finally:                                                                                # Rilascia il semaforo
            self._is_executing = False                                                          # Fine esecuzione

    def onChanged(self, obj, prop):                                                             # Intercetta modifiche live dalle Proprietà di FreeCAD
        if getattr(self, "_is_executing", False):                                               # Evita ricorsioni
            return                                                                              # Esce
        props_calcolo = [                                                                       # Proprietà che rigenerano il percorso
            "TipoCiclo", "PezzoRiferimento", "UsaProfiloPezzo3D",                               # Modello e ciclo
            "Z_Inizio", "Z_Fine", "DiametroFinaleManuale",                                      # Quote geometriche
            "ProfonditaPassata", "SovrametalloFinituraX", "SovrametalloFinituraZ",              # Parametri passata
            "DistaccoRitorno", "AngoloDistacco", "AvanzamentoLavoro"                            # Distacco, angolo e avanzamento
        ]                                                                                       # Fine lista
        if prop in props_calcolo:                                                               # Se è cambiato un parametro di lavorazione
            self.execute(obj)                                                                   # Ricalcola subito il percorso 3D
        elif prop == "OperationName":                                                           # Se cambia il nome operazione
            if hasattr(obj, "OperationName") and obj.OperationName:                             # Aggiorna la Label nell'albero
                obj.Label = obj.OperationName                                                   # Allinea Label

    def __getstate__(self):                                                                     # Serializzazione
        return None                                                                             # Nessuno stato extra

    def __setstate__(self, state):                                                              # Deserializzazione
        self._is_executing = False                                                              # Ripristina flag
        return None                                                                             # Fine


class ViewProviderLatheRoughing:                                                                # ViewProvider per icona e doppio click sull'operazione
    def __init__(self, vobj):                                                                   # Costruttore ViewProvider
        vobj.Proxy = self                                                                       # Collega il Proxy

    def getIcon(self):                                                                          # Icona nell'albero delle operazioni
        return LatheResources.get_icon_path("lathe_roughing.svg", "Part_Cut")                   # Icona SVG dedicata Sgrossatura

    def attach(self, vobj):                                                                     # Collega gli oggetti alla vista
        self.ViewObject = vobj                                                                  # Riferimento ViewObject
        self.Object = vobj.Object                                                               # Riferimento Object

    def updateData(self, vobj, prop):                                                           # Aggiornamento dati
        return                                                                                  # Gestito da execute

    def onDelete(self, vobj, subelements):                                                      # Autorizza cancellazione
        return True                                                                             # Sempre consentito

    def doubleClicked(self, vobj):                                                              # Doppio click sull'operazione nell'albero
        if not FreeCADGui.Control.activeDialog():                                               # Se non c'è già un pannello aperto
            panel = LatheRoughingPanel(edit_obj=vobj.Object)                                    # Apre il pannello caricando l'operazione
            FreeCADGui.Control.showDialog(panel)                                                # Mostra nella scheda Azioni
        return True                                                                             # Evento gestito

    def setEdit(self, vobj, mode):                                                              # Modalità Edit standard
        if mode == 0:                                                                           # Modifica base
            if not FreeCADGui.Control.activeDialog():                                           # Evita doppia apertura
                panel = LatheRoughingPanel(edit_obj=vobj.Object)                                # Crea il pannello
                FreeCADGui.Control.showDialog(panel)                                            # Mostra il dialogo
            return True                                                                         # Conferma
        return False                                                                            # Rifiuta altre modalità

    def unsetEdit(self, vobj, mode):                                                            # Chiusura modalità Edit
        FreeCADGui.Control.closeDialog()                                                        # Chiude il pannello
        return True                                                                             # Conferma

    def __getstate__(self):                                                                     # Serializzazione
        return None                                                                             # Nessun dato extra

    def __setstate__(self, state):                                                              # Deserializzazione
        return None                                                                             # Nessun dato extra


class LatheRoughingPanel:                                                                       # Pannello Task per programmare Sfacciatura e Sgrossatura
    def __init__(self, edit_obj=None):                                                          # Costruttore del pannello (nuovo o modifica)
        self.edit_obj = edit_obj                                                                # Memorizza eventuale operazione in modifica
        self.is_updating = True                                                                 # Blocca i segnali durante la creazione della UI

        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        self.pulisci_anteprima_percorso(doc)                                                    # Rimuove eventuali anteprime rimaste appese
        if self.edit_obj and hasattr(self.edit_obj, "ViewObject") and self.edit_obj.ViewObject: # Se stiamo modificando un'operazione esistente
            self.edit_obj.ViewObject.Visibility = False                                         # Nasconde il tracciato originale durante l'anteprima bicolore

        self.form = QtWidgets.QWidget()                                                         # Contenitore principale del pannello
        self.form.setMinimumWidth(240)                                                          # Larghezza minima compatta per non tagliare a destra
        self.layout = QtWidgets.QVBoxLayout(self.form)                                          # Layout verticale principale
        self.layout.setContentsMargins(4, 4, 4, 4)                                              # Margini ridotti

        self.grp_gen = QtWidgets.QGroupBox("Operazione e Scelta Utensile")                      # Gruppo dati generali e utensile
        self.lyt_gen = QtWidgets.QFormLayout(self.grp_gen)                                      # Form layout

        self.name_input = QtWidgets.QLineEdit("Sgrossatura Esterna 1")                          # Nome descrittivo dell'operazione
        self.cycle_combo = QtWidgets.QComboBox()                                                # Scelta modalità ciclo
        self.cycle_combo.addItems(TIPI_CICLO_SGROSSO)                                           # Popola le 4 modalità
        self.cycle_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cycle_combo.setMinimumContentsLength(10)

        self.tool_combo = QtWidgets.QComboBox()                                                 # Scelta utensile dal Magazzino Utensili
        self.tool_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.tool_combo.setMinimumContentsLength(10)
        self.popola_combo_utensili(doc)                                                         # Carica gli utensili disponibili

        self.lyt_gen.addRow("Nome:", self.name_input)                                           # Riga Nome Operazione
        self.lyt_gen.addRow("Strategia:", self.cycle_combo)                                     # Riga Strategia
        self.lyt_gen.addRow("Utensile:", self.tool_combo)                                       # Riga Utensile
        self.layout.addWidget(self.grp_gen)                                                     # Aggiunge al layout principale

        self.tabs = QtWidgets.QTabWidget()                                                      # Schede: 1. Geometria & Limiti | 2. Passate & Taglio

        self.tab_geo = QtWidgets.QWidget()                                                      # SCHEDA 1: Profilo Pezzo e Limiti Z / X
        self.lyt_geo = QtWidgets.QVBoxLayout(self.tab_geo)                                      # Layout verticale Scheda 1

        self.grp_part = QtWidgets.QGroupBox("Profilo Pezzo e Limiti Assiali")                   # Gruppo selezione pezzo e quote
        self.lyt_part = QtWidgets.QFormLayout(self.grp_part)                                    # Form layout

        self.chk_use_3d = QtWidgets.QCheckBox("Segui sagoma del Solido Pezzo 3D")               # Usa il modello 3D per calcolare gli spallamenti
        self.chk_use_3d.setChecked(True)                                                        # Attivo di default

        self.part_combo = QtWidgets.QComboBox()                                                 # Tendina con i solidi candidati ad essere il Pezzo
        self.part_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.part_combo.setMinimumContentsLength(10)
        self.popola_combo_pezzi(doc)                                                            # Cerca automaticamente il pezzo nel documento

        self.btn_pick_part = QtWidgets.QPushButton("Cattura Pezzo da Selezione 3D")             # Cattura il solido cliccato nella vista 3D
        self.btn_pick_part.clicked.connect(self.cattura_pezzo_selezionato)                      # Collega la cattura

        stock_info = get_stock_info(doc)                                                        # Legge i dati attuali del Grezzo_Macchina
        self.z_start_spin = QtWidgets.QDoubleSpinBox(); self.z_start_spin.setRange(-2000, 2000); self.z_start_spin.setDecimals(2); self.z_start_spin.setValue(stock_info["z_front"])
        self.z_end_spin = QtWidgets.QDoubleSpinBox(); self.z_end_spin.setRange(-2000, 2000); self.z_end_spin.setDecimals(2)
        self.btn_auto_zend = QtWidgets.QPushButton("Ricalcola Z Fine da Fine Pezzo 3D")         # Pulsante per riportare Z Fine alla fine del pezzo
        self.btn_auto_zend.clicked.connect(self.imposta_z_fine_da_pezzo_corrente)               # Collega il ricalcolo automatico di Z Fine
        self.d_man_spin = QtWidgets.QDoubleSpinBox(); self.d_man_spin.setRange(0.0, 2000.0); self.d_man_spin.setValue(stock_info["r_ext"] * 1.2)

        self.lbl_status = QtWidgets.QLabel(f"Limite Griffe Mandrino: Z = {stock_info['z_lim_chuck']:.2f} mm")
        self.lbl_status.setWordWrap(True)                                                       # Va a capo automaticamente
        self.lbl_status.setStyleSheet("color: #55FF55; font-weight: bold;")                     # Stile verde informativo

        self.lyt_part.addRow(self.chk_use_3d)                                                   # Riga checkbox usa pezzo 3D
        self.lyt_part.addRow("Solido Pezzo:", self.part_combo)                                  # Riga scelta solido pezzo
        self.lyt_part.addRow(self.btn_pick_part)                                                # Riga pulsante cattura da selezione
        self.lyt_part.addRow("Z Inizio (mm):", self.z_start_spin)                               # Riga Z Inizio
        self.lyt_part.addRow("Z Fine (mm):", self.z_end_spin)                                   # Riga Z Fine (auto-calcolata e modificabile a mano)
        self.lyt_part.addRow(self.btn_auto_zend)                                                # Riga pulsante ricalcolo automatico Z Fine
        self.lyt_part.addRow("Ø Finale Manuale (mm):", self.d_man_spin)                         # Riga Diametro Finale (se non usa il 3D o per ID)
        self.lyt_part.addRow(self.lbl_status)                                                   # Riga stato e numero passate
        self.lyt_geo.addWidget(self.grp_part)                                                   # Aggiunge alla Scheda 1

        self.tabs.addTab(self.tab_geo, "1. Geometria")                                          # Titolo Scheda 1

        self.tab_cut = QtWidgets.QWidget()                                                      # SCHEDA 2: Parametri di Passata, Sovrametalli e Distacco
        self.lyt_cut = QtWidgets.QVBoxLayout(self.tab_cut)                                      # Layout verticale Scheda 2

        self.grp_cut = QtWidgets.QGroupBox("Passata, Sovrametalli e Distacco Ritorno")          # Gruppo parametri di taglio
        self.lyt_c_form = QtWidgets.QFormLayout(self.grp_cut)                                   # Form layout

        self.ap_spin = QtWidgets.QDoubleSpinBox(); self.ap_spin.setRange(0.1, 50.0); self.ap_spin.setValue(2.0); self.ap_spin.setSingleStep(0.5)
        self.fin_x_spin = QtWidgets.QDoubleSpinBox(); self.fin_x_spin.setRange(0.0, 20.0); self.fin_x_spin.setDecimals(2); self.fin_x_spin.setValue(0.30); self.fin_x_spin.setSingleStep(0.1)
        self.fin_z_spin = QtWidgets.QDoubleSpinBox(); self.fin_z_spin.setRange(0.0, 20.0); self.fin_z_spin.setDecimals(2); self.fin_z_spin.setValue(0.10); self.fin_z_spin.setSingleStep(0.05)
        self.ret_spin = QtWidgets.QDoubleSpinBox(); self.ret_spin.setRange(0.1, 20.0); self.ret_spin.setValue(1.0); self.ret_spin.setSingleStep(0.5)
        self.ret_ang_spin = QtWidgets.QDoubleSpinBox(); self.ret_ang_spin.setRange(0.0, 90.0); self.ret_ang_spin.setDecimals(1); self.ret_ang_spin.setValue(45.0); self.ret_ang_spin.setSingleStep(5.0)
        self.vc_spin = QtWidgets.QDoubleSpinBox(); self.vc_spin.setRange(1.0, 15000.0); self.vc_spin.setValue(180.0); self.vc_spin.setSingleStep(10.0)
        self.feed_spin = QtWidgets.QDoubleSpinBox(); self.feed_spin.setRange(0.01, 10.0); self.feed_spin.setDecimals(3); self.feed_spin.setValue(0.25); self.feed_spin.setSingleStep(0.05)

        self.lyt_c_form.addRow("Prof. Passata Ap (mm):", self.ap_spin)                          # Riga Ap
        self.lyt_c_form.addRow("Sovram. Finitura X (mm):", self.fin_x_spin)                     # Riga Sovrametallo Finitura X
        self.lyt_c_form.addRow("Sovram. Finitura Z (mm):", self.fin_z_spin)                     # Riga Sovrametallo Finitura Z
        self.lyt_c_form.addRow("Lunghezza Distacco (mm):", self.ret_spin)                       # Riga Lunghezza Distacco
        self.lyt_c_form.addRow("Angolo Distacco (°):", self.ret_ang_spin)                       # Riga Angolo di Distacco Ritorno (0°..90°, default 45°)
        self.lyt_c_form.addRow("Velocità Vc / RPM:", self.vc_spin)                              # Riga Velocità
        self.lyt_c_form.addRow("Avanzamento F (mm/g):", self.feed_spin)                         # Riga Avanzamento
        self.lyt_cut.addWidget(self.grp_cut)                                                    # Aggiunge alla Scheda 2
        self.lyt_cut.addStretch()                                                               # Allinea in alto

        self.tabs.addTab(self.tab_cut, "2. Parametri")                                          # Titolo Scheda 2
        self.layout.addWidget(self.tabs)                                                        # Aggiunge il TabWidget al layout principale
        self.form.setLayout(self.layout)                                                        # Imposta il layout finale

        self.preview_rapidi = doc.addObject("Part::Feature", "TMP_Rough_Rapids")                # Oggetto temporaneo per i movimenti rapidi G00 (Rosso)
        self.preview_rapidi.Label = "ANTEPRIMA RAPIDI G00"                                      # Etichetta
        self.preview_rapidi.ViewObject.LineColor = (0.95, 0.20, 0.20)                           # Rosso acceso per i rapidi
        self.preview_rapidi.ViewObject.LineWidth = 1.5                                          # Spessore linea rapidi

        self.preview_lavoro = doc.addObject("Part::Feature", "TMP_Rough_Cut")                   # Oggetto temporaneo per le passate di lavoro G01 (Verde)
        self.preview_lavoro.Label = "ANTEPRIMA TAGLIO G01"                                      # Etichetta
        self.preview_lavoro.ViewObject.LineColor = (0.15, 0.95, 0.25)                           # Verde acceso per le passate di taglio
        self.preview_lavoro.ViewObject.LineWidth = 2.5                                          # Spessore linea lavoro

        if self.edit_obj:                                                                       # Se siamo in modifica di un'operazione esistente
            self.carica_dati_da_oggetto(self.edit_obj)                                          # Ripristina i dati salvati
        else:                                                                                   # Se è una nuova operazione
            self.imposta_z_fine_da_pezzo_corrente()                                             # Calcola automaticamente Z Fine fino alla fine del pezzo 3D
            self.on_tool_changed()                                                              # Eredita i parametri tecnologici dal primo utensile

        self.cycle_combo.currentIndexChanged.connect(self.aggiorna_ui_ciclo)                    # Collega cambio strategia
        self.tool_combo.currentIndexChanged.connect(self.on_tool_changed)                       # Collega cambio utensile (eredita Vc, F, Ap)
        self.chk_use_3d.stateChanged.connect(self.aggiorna_ui_ciclo)                            # Collega spunta usa pezzo 3D
        self.part_combo.currentIndexChanged.connect(self.on_part_changed)                       # Quando cambi Pezzo 3D ricalcola automaticamente Z Fine
        self.z_start_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio Z inizio
        self.z_end_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio Z fine (modificabile anche a mano)
        self.d_man_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio diametro manuale
        self.ap_spin.valueChanged.connect(self.trigger_update)                                  # Collega cambio Ap
        self.fin_x_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio sovrametallo X
        self.fin_z_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio sovrametallo Z
        self.ret_spin.valueChanged.connect(self.trigger_update)                                 # Collega cambio lunghezza distacco
        self.ret_ang_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio angolo distacco ritorno

        self.is_updating = False                                                                # Sblocca gli aggiornamenti live
        self.aggiorna_ui_ciclo()                                                                # Adatta i controlli e disegna subito il percorso 3D

    def popola_combo_utensili(self, doc):                                                       # Carica gli utensili del Magazzino Utensili
        self.tool_combo.clear()                                                                 # Svuota il combo
        if doc and doc.getObject("Libreria_Utensili"):                                          # Se esiste il Magazzino Utensili
            lib = doc.getObject("Libreria_Utensili")                                            # Gruppo magazzino
            for t in lib.Group:                                                                 # Cicla sugli utensili
                st = getattr(t, "Stazione", "T01")                                              # Stazione T
                self.tool_combo.addItem(f"[{st}] {t.Label}", t.Name)                            # Aggiunge voce e Name interno

    def popola_combo_pezzi(self, doc):                                                          # Cerca i solidi del progetto candidati a Pezzo Finito
        self.part_combo.clear()                                                                 # Svuota il combo
        candidati = trova_candidati_pezzo(doc)                                                  # Trova i solidi 3D
        if candidati:                                                                           # Se ci sono solidi validi
            for p in candidati:                                                                 # Cicla sui solidi
                self.part_combo.addItem(p.Label, p.Name)                                        # Aggiunge etichetta e Name interno
        else:                                                                                   # Se non c'è ancora un pezzo 3D
            self.part_combo.addItem("(Nessun Pezzo 3D - Usa Quota Manuale)", "")                # Modalità manuale

    def imposta_z_fine_da_pezzo_corrente(self):                                                 # Calcola e imposta Z Fine alla fine esatta del Pezzo 3D selezionato
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc: return                                                                      # Verifica documento
        p_name = self.part_combo.itemData(self.part_combo.currentIndex()) if self.part_combo.count() > 0 else ""
        part_obj = doc.getObject(p_name) if p_name else None                                    # Ottiene l'oggetto Pezzo 3D
        z_calc = calcola_z_fine_da_pezzo(part_obj, doc)                                         # Calcola la fine del pezzo (BoundBox.ZMin - WCS.z)
        prev = self.is_updating                                                                 # Memorizza stato semaforo
        self.is_updating = True                                                                 # Sospende segnali
        self.z_end_spin.setValue(z_calc)                                                        # Imposta Z Fine (restando liberamente modificabile a mano)
        self.is_updating = prev                                                                 # Ripristina semaforo
        self.trigger_update()                                                                   # Aggiorna il percorso 3D

    def on_part_changed(self):                                                                  # Chiamato quando l'utente cambia il Solido Pezzo nella tendina
        self.imposta_z_fine_da_pezzo_corrente()                                                 # Aggiorna automaticamente Z Fine alla fine del nuovo pezzo

    def cattura_pezzo_selezionato(self):                                                        # Imposta il Pezzo Finito dall'oggetto cliccato nel 3D
        sel = FreeCADGui.Selection.getSelection()                                               # Legge la selezione 3D
        if not sel:                                                                             # Se non c'è selezione
            self.lbl_status.setText("Seleziona prima il solido del Pezzo Finito nella vista 3D!")
            return                                                                              # Esce
        obj_sel = sel[0]                                                                        # Oggetto selezionato
        idx = self.part_combo.findData(obj_sel.Name)                                            # Cerca se è già nella tendina
        if idx < 0:                                                                             # Se non era in lista lo aggiunge
            self.part_combo.addItem(obj_sel.Label, obj_sel.Name)                                # Aggiunge al combo
            idx = self.part_combo.count() - 1                                                   # Ultimo indice
        self.part_combo.setCurrentIndex(idx)                                                    # Seleziona il pezzo
        FreeCADGui.Selection.clearSelection()                                                   # Pulisce la selezione
        self.imposta_z_fine_da_pezzo_corrente()                                                 # Imposta automaticamente Z Fine fino alla fine del pezzo catturato

    def on_tool_changed(self):                                                                  # Eredita automaticamente Vc, Avanzamento e Ap dall'utensile scelto
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc or self.tool_combo.count() == 0: return                                      # Verifica validità
        t_name = self.tool_combo.itemData(self.tool_combo.currentIndex())                       # Nome interno utensile
        t_obj = doc.getObject(t_name) if t_name else None                                       # Oggetto utensile
        if t_obj:                                                                               # Se l'utensile esiste
            prev_state = self.is_updating                                                       # Salva stato semaforo
            self.is_updating = True                                                             # Evita ricalcoli multipli
            self.vc_spin.setValue(float(getattr(t_obj, "VelocitaTaglio", 180.0)))               # Carica la velocità di taglio dell'utensile
            self.feed_spin.setValue(float(getattr(t_obj, "AvanzamentoSgrosso", 0.25)))          # Carica l'avanzamento di sgrossatura dell'utensile
            self.ap_spin.setValue(float(getattr(t_obj, "ProfonditaPassataMax", 2.0)))           # Carica la profondità di passata Ap dell'utensile
            self.is_updating = prev_state                                                       # Ripristina semaforo
            self.trigger_update()                                                               # Aggiorna il percorso

    def aggiorna_ui_ciclo(self):                                                                # Abilita/disabilita i campi in base alla strategia scelta
        ciclo = self.cycle_combo.currentText()                                                  # Strategia selezionata
        is_facing_only = (ciclo == "Solo Sfacciatura Frontale (Facing)")                        # Solo intestatura
        is_id = (ciclo == "Sgrossatura Interna / Bareno (ID)")                                  # Barenatura interna
        usa_3d = self.chk_use_3d.isChecked() and (not is_facing_only)                           # Uso sagoma 3D

        self.part_combo.setEnabled(usa_3d)                                                      # Abilita scelta solido pezzo
        self.btn_pick_part.setEnabled(usa_3d)                                                   # Abilita pulsante cattura pezzo
        self.z_end_spin.setEnabled(not is_facing_only)                                          # Z Fine attiva per tutte le sgrossature longitudinali
        self.btn_auto_zend.setEnabled(not is_facing_only)                                       # Pulsante auto Z Fine attivo
        self.d_man_spin.setEnabled((not usa_3d or is_id) and (not is_facing_only))              # Diametro manuale attivo se non usa 3D o per ID
        self.trigger_update()                                                                   # Aggiorna l'anteprima 3D

    def trigger_update(self, *args):                                                            # Rigenera in tempo reale il tracciato 3D bicolore (Rosso/Verde)
        if self.is_updating: return                                                             # Se bloccato esce
        self.is_updating = True                                                                 # Attiva il semaforo
        try:                                                                                    # Blocco di calcolo
            doc = FreeCAD.ActiveDocument                                                        # Documento attivo
            if not doc or not self.preview_rapidi or not self.preview_lavoro: return            # Verifica validità
            wcs = get_wcs_origin(doc)                                                           # Origine WCS
            sic_x, sic_z = get_setup_safe_clearances(doc)                                       # Distanze sicurezza Setup
            stock_info = get_stock_info(doc)                                                    # Informazioni Grezzo e limite griffe

            part_name = self.part_combo.itemData(self.part_combo.currentIndex()) if self.part_combo.count() > 0 else ""
            part_obj = doc.getObject(part_name) if part_name else None                          # Oggetto Pezzo 3D

            _, c_rap, c_lav, moves, z_eff = calcola_percorso_sgrossatura(                       # Calcola il percorso utensile
                wcs, self.cycle_combo.currentText(), part_obj, stock_info,
                self.z_start_spin.value(), self.z_end_spin.value(),
                self.d_man_spin.value() / 2.0, self.chk_use_3d.isChecked(),
                self.ap_spin.value(), self.fin_x_spin.value(), self.fin_z_spin.value(),
                self.ret_spin.value(), self.ret_ang_spin.value(), sic_x, sic_z, self.feed_spin.value()
            )                                                                                   # Fine calcolo

            self.preview_rapidi.Shape = c_rap if c_rap else Part.Shape()                        # Aggiorna le linee rosse dei rapidi G00
            self.preview_lavoro.Shape = c_lav if c_lav else Part.Shape()                        # Aggiorna le linee verdi di taglio G01

            n_tagli = sum(1 for m in moves if m["cmd"] == "G1")                                 # Conta i segmenti di taglio attivo
            if self.z_end_spin.value() < stock_info["z_lim_chuck"]:                             # Avvisa se Z Fine è stata limitata dalle griffe
                self.lbl_status.setStyleSheet("color: #FF5555; font-weight: bold;")             # Rosso avviso
                self.lbl_status.setText(f"Z Fine limitata a {z_eff:.2f} mm per non urtare le Griffe! ({n_tagli} tagli)")
            else:                                                                               # Tutto entro i limiti sicuri
                self.lbl_status.setStyleSheet("color: #55FF55; font-weight: bold;")             # Verde OK
                self.lbl_status.setText(f"Percorso OK: Z Fine={z_eff:.2f} mm | {n_tagli} tagli. (Griffe a Z={stock_info['z_lim_chuck']:.1f})")

            doc.recompute()                                                                     # Rinfresca la scena 3D
        finally:                                                                                # Rilascia il semaforo
            self.is_updating = False                                                            # Fine aggiornamento

    def carica_dati_da_oggetto(self, obj):                                                      # Popola la UI quando si riapre un'operazione con doppio click
        obj.Proxy.ensure_properties(obj)                                                        # Verifica tutte le proprietà
        self.name_input.setText(str(getattr(obj, "OperationName", obj.Label)))                  # Nome
        if str(obj.TipoCiclo) in TIPI_CICLO_SGROSSO:                                            # Strategia
            self.cycle_combo.setCurrentText(str(obj.TipoCiclo))                                 # Imposta strategia
        idx_t = self.tool_combo.findData(str(getattr(obj, "UtensileAssegnato", "")))            # Cerca l'utensile assegnato
        if idx_t >= 0: self.tool_combo.setCurrentIndex(idx_t)                                   # Seleziona l'utensile
        self.chk_use_3d.setChecked(bool(getattr(obj, "UsaProfiloPezzo3D", True)))               # Flag usa 3D
        idx_p = self.part_combo.findData(str(getattr(obj, "PezzoRiferimento", "")))             # Cerca il solido del pezzo
        if idx_p >= 0: self.part_combo.setCurrentIndex(idx_p)                                   # Seleziona il pezzo
        self.z_start_spin.setValue(float(getattr(obj, "Z_Inizio", 1.5)))                        # Z Inizio
        self.z_end_spin.setValue(float(getattr(obj, "Z_Fine", -50.0)))                          # Z Fine salvata
        self.d_man_spin.setValue(float(getattr(obj, "DiametroFinaleManuale", 30.0)))            # Diametro manuale
        self.ap_spin.setValue(float(getattr(obj, "ProfonditaPassata", 2.0)))                    # Ap
        self.fin_x_spin.setValue(float(getattr(obj, "SovrametalloFinituraX", 0.3)))             # Sovrametallo X
        self.fin_z_spin.setValue(float(getattr(obj, "SovrametalloFinituraZ", 0.1)))             # Sovrametallo Z
        self.ret_spin.setValue(float(getattr(obj, "DistaccoRitorno", 1.0)))                     # Lunghezza distacco
        self.ret_ang_spin.setValue(float(getattr(obj, "AngoloDistacco", 45.0)))                 # Angolo distacco
        self.vc_spin.setValue(float(getattr(obj, "VelocitaTaglio", 180.0)))                     # Vc / RPM
        self.feed_spin.setValue(float(getattr(obj, "AvanzamentoLavoro", 0.25)))                 # Avanzamento F

    def pulisci_anteprima_percorso(self, doc):                                                  # Rimuove in modo sicuro gli oggetti temporanei di anteprima
        if not doc: return                                                                      # Controllo sicurezza
        for attr in ["preview_rapidi", "preview_lavoro"]:                                       # Rimuove i riferimenti diretti
            if hasattr(self, attr) and getattr(self, attr):
                try:
                    obj = getattr(self, attr)
                    if doc.getObject(obj.Name): doc.removeObject(obj.Name)
                except Exception: pass
                setattr(self, attr, None)
        for obj in list(doc.Objects):                                                           # Rimuove eventuali residui
            if obj.Name.startswith("TMP_Rough_"):
                try: doc.removeObject(obj.Name)
                except Exception: pass

    def getStandardButtons(self):                                                               # Pulsanti OK e Cancel
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel                # Restituisce OK | Cancel

    def accept(self):                                                                           # Conferma e salva l'operazione nel gruppo Operazioni_CAM
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc: return False                                                                # Controllo sicurezza

        ops_group = doc.getObject("Operazioni_CAM")                                             # Cerca il gruppo contenitore delle lavorazioni CAM
        if not ops_group:                                                                       # Se non esiste ancora lo crea
            ops_group = doc.addObject("App::DocumentObjectGroup", "Operazioni_CAM")             # Crea gruppo FreeCAD
            ops_group.Label = "Operazioni CAM (Cicli Tornio)"                                   # Etichetta nell'albero

        nome_op = self.name_input.text().strip() or "Sgrossatura 1"                             # Nome operazione
        if self.edit_obj and doc.getObject(self.edit_obj.Name):                                 # Se stavamo modificando un'operazione esistente
            op_obj = self.edit_obj                                                              # Riutilizza l'oggetto
        else:                                                                                   # Altrimenti crea una nuova operazione parametrica
            op_obj = doc.addObject("Part::FeaturePython", "Op_Sgrossatura")                     # Crea Part::FeaturePython
            LatheRoughingObject(op_obj)                                                         # Inizializza Proxy
            ViewProviderLatheRoughing(op_obj.ViewObject)                                        # Inizializza ViewProvider con doppio click
            ops_group.addObject(op_obj)                                                         # Inserisce nel gruppo Operazioni_CAM

        t_name = self.tool_combo.itemData(self.tool_combo.currentIndex()) if self.tool_combo.count() > 0 else ""
        p_name = self.part_combo.itemData(self.part_combo.currentIndex()) if self.part_combo.count() > 0 else ""

        op_obj.Proxy._is_executing = True                                                       # Sospende execute durante la scrittura proprietà
        try:                                                                                    # Salva tutti i parametri
            op_obj.Proxy.ensure_properties(op_obj)
            op_obj.OperationName = nome_op
            op_obj.Label = nome_op
            op_obj.TipoCiclo = self.cycle_combo.currentText()
            op_obj.UtensileAssegnato = str(t_name or "")
            op_obj.PezzoRiferimento = str(p_name or "")
            op_obj.UsaProfiloPezzo3D = self.chk_use_3d.isChecked()
            op_obj.Z_Inizio = self.z_start_spin.value()
            op_obj.Z_Fine = self.z_end_spin.value()
            op_obj.DiametroFinaleManuale = self.d_man_spin.value()
            op_obj.ProfonditaPassata = self.ap_spin.value()
            op_obj.SovrametalloFinituraX = self.fin_x_spin.value()
            op_obj.SovrametalloFinituraZ = self.fin_z_spin.value()
            op_obj.DistaccoRitorno = self.ret_spin.value()
            op_obj.AngoloDistacco = self.ret_ang_spin.value()                                   # Salva l'angolo di distacco ritorno
            op_obj.VelocitaTaglio = self.vc_spin.value()
            op_obj.AvanzamentoLavoro = self.feed_spin.value()
        finally:                                                                                # Sblocca Proxy
            op_obj.Proxy._is_executing = False

        op_obj.Proxy.execute(op_obj)                                                            # Calcola e disegna il percorso finale
        if hasattr(op_obj, "ViewObject") and op_obj.ViewObject:
            op_obj.ViewObject.Visibility = True                                                 # Rende visibile il tracciato finale

        self.pulisci_anteprima_percorso(doc)                                                    # Rimuove le anteprime temporanee
        doc.recompute()                                                                         # Ricalcola il documento
        if FreeCADGui.ActiveDocument: FreeCADGui.ActiveDocument.resetEdit()                     # Esce da Edit
        FreeCADGui.Control.closeDialog()                                                        # Chiude il pannello
        return True                                                                             # Conferma

    def reject(self):                                                                           # Annulla e ripristina la vista precedente
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if doc:
            self.pulisci_anteprima_percorso(doc)                                                # Rimuove le anteprime temporanee
            if self.edit_obj and doc.getObject(self.edit_obj.Name):                             # Se eravamo in modifica
                if hasattr(self.edit_obj, "ViewObject") and self.edit_obj.ViewObject:
                    self.edit_obj.ViewObject.Visibility = True                                  # Riaccende l'operazione originale
            doc.recompute()                                                                     # Aggiorna il documento
        if FreeCADGui.ActiveDocument: FreeCADGui.ActiveDocument.resetEdit()                     # Esce da Edit
        FreeCADGui.Control.closeDialog()                                                        # Chiude il pannello
        return True                                                                             # Conferma