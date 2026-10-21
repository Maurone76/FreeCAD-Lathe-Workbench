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
import LatheRoughing                                                                            # Riutilizza le utility di lettura WCS e Grezzo


TIPI_CICLO_GOLA = [                                                                             # Modalità operative supportate dal ciclo di Gola
    "Gola Esterna Radiale (OD)",                                                                # Scava dall'esterno verso l'asse mandrino (-X)
    "Gola Interna Radiale (ID)",                                                                # Scava dall'interno di un foro verso l'esterno (+X)
    "Gola Frontale Assiale (Face)"                                                              # Scava sulla faccia frontale lungo l'asse mandrino (-Z)
]                                                                                               # Fine elenco cicli di gola


def calcola_stazioni_plunge(pos_start, pos_end_far, w_lama, stepover_perc, sovra_fianco):       # Calcola le posizioni di affondamento a tuffo centrando la prima passata
    z_right = max(float(pos_start), float(pos_end_far))                                         # Bordo destro / esterno della gola
    z_left = min(float(pos_start), float(pos_end_far))                                          # Bordo sinistro / interno della gola
    w_tot = z_right - z_left                                                                    # Larghezza totale della gola richiesta
    w_tool = max(float(w_lama), 0.5)                                                            # Larghezza effettiva della lama/inserto

    sf = max(float(sovra_fianco), 0.0) if w_tot > (w_tool + 2.0 * float(sovra_fianco) + 0.05) else 0.0
    z_max_punta = z_right - sf                                                                  # Posizione estrema destra della punta di riferimento (spigolo destro lama)
    z_min_punta = z_left + sf + w_tool                                                          # Posizione estrema sinistra della punta (la lama si estende di -w_tool)

    if z_max_punta <= z_min_punta + 1e-4:                                                       # Se la gola ha la stessa larghezza della lama (passata singola)
        z_centro = (z_right + z_left + w_tool) / 2.0                                            # Centra la lama nella gola
        return [z_centro], z_right, z_left                                                      # Restituisce una sola stazione di tuffo

    passo_lat = max(w_tool * (max(10.0, min(float(stepover_perc), 95.0)) / 100.0), 0.2)         # Passo laterale tra i tuffi (es. 75% della larghezza lama)
    z_mid = (z_max_punta + z_min_punta) / 2.0                                                   # Posizione centrale per il primo tuffo (scarica lo sforzo su tutta la lama)
    stazioni = [z_mid]                                                                          # La prima passata avviene sempre al centro della gola

    dist_metà = z_max_punta - z_mid                                                             # Semilarghezza da coprire a destra e a sinistra del centro
    n_passi = max(int(math.ceil(dist_metà / passo_lat)), 1)                                     # Numero di allargamenti per lato
    step_eff = dist_metà / float(n_passi)                                                       # Passo laterale equispaziato esatto

    for i in range(1, n_passi + 1):                                                             # Alterna i tuffi a destra e a sinistra del centro
        stazioni.append(z_mid + i * step_eff)                                                   # Tuffo sul lato destro
        stazioni.append(z_mid - i * step_eff)                                                   # Tuffo sul lato sinistro

    return stazioni, z_right, z_left                                                            # Restituisce la lista ordinata delle stazioni e i due bordi


def calcola_percorso_gola(                                                                      # Genera la lista movimenti (G0/G1) e le Shapes 3D della gola
    wcs, tipo_ciclo, stock_info,                                                                # Riferimenti base
    z_start, larg_gola, d_inizio, d_fondo,                                                      # Quote geometriche della gola
    w_lama, usa_peck, passo_peck, rit_peck, stepover_perc,                                      # Parametri lama, scarico truciolo (peck) e sormonto
    finitura_fianchi, sovra_fondo, sovra_fianco, smusso_bordi,                                  # Parametri di finitura pareti/fondo e smussi d'imbocco
    sic_x, sic_z, feed_plunge, feed_fin                                                         # Sicurezze e avanzamenti di tuffo e finitura
):                                                                                              # Inizio motore di calcolo percorso gola
    moves = []                                                                                  # Lista movimenti: {"cmd": "G0"/"G1", "x": r, "z": z, "f": feed}
    edges_rapidi = []                                                                           # Segmenti 3D per i movimenti rapidi G00 (Rosso)
    edges_lavoro = []                                                                           # Segmenti 3D per i movimenti di taglio G01 (Giallo/Ambra)

    r_grezzo = stock_info["r_rot"]                                                              # Raggio esterno massimo del grezzo
    z_lim_griffe = stock_info["z_lim_chuck"]                                                    # Quota Z limite collisione griffe mandrino
    w_tool = max(float(w_lama), 0.5)                                                            # Larghezza inserto da gola
    w_tot = max(float(larg_gola), w_tool)                                                       # Larghezza gola (almeno pari alla larghezza lama)
    peck_q = max(float(passo_peck), 0.2)                                                        # Incremento di affondamento peck (mm)
    peck_ret = max(float(rit_peck), 0.1)                                                        # Ritrazione rompi-truciolo (mm)
    smusso = max(float(smusso_bordi), 0.0)                                                      # Smusso sugli spigoli superiori della gola (mm)

    safe_r_od = max(r_grezzo, float(d_inizio) / 2.0) + max(float(sic_x), 1.5)                   # Raggio di sicurezza esterno
    safe_z_front = max(stock_info["z_front"], float(z_start)) + max(float(sic_z), 1.5)          # Quota Z di sicurezza frontale

    curr_pt = [safe_r_od, safe_z_front]                                                         # Posizione iniziale utensile
    moves.append({"cmd": "G0", "x": curr_pt[0], "z": curr_pt[1], "f": 0.0})                     # Punto iniziale in sicurezza

    def add_segment(cmd, next_r, next_z, f_val=0.0):                                            # Funzione interna per registrare un movimento e creare la linea 3D
        p1 = FreeCAD.Vector(wcs.x + curr_pt[0], wcs.y, wcs.z + curr_pt[1])                      # Punto 3D partenza sul piano XZ
        p2 = FreeCAD.Vector(wcs.x + next_r, wcs.y, wcs.z + next_z)                              # Punto 3D arrivo sul piano XZ
        if (p2 - p1).Length > 1e-4:                                                             # Se lo spostamento è reale
            edge = Part.makeLine(p1, p2)                                                        # Crea il segmento 3D
            if cmd == "G0":                                                                     # Movimento rapido
                edges_rapidi.append(edge)                                                       # Aggiunge ai rapidi
            else:                                                                               # Movimento di taglio
                edges_lavoro.append(edge)                                                       # Aggiunge al lavoro
            moves.append({                                                                      # Registra il dizionario movimento
                "cmd": cmd,
                "x": float(next_r),
                "z": float(next_z),
                "f": float(f_val if cmd == "G1" else 0.0)
            })                                                                                  # Fine record
            curr_pt[0] = float(next_r)                                                          # Aggiorna X corrente
            curr_pt[1] = float(next_z)                                                          # Aggiorna Z corrente

    z_eff_min = float(z_start)                                                                  # Traccia la quota Z più vicina al mandrino per controllo griffe

    if tipo_ciclo in ["Gola Esterna Radiale (OD)", "Gola Interna Radiale (ID)"]:                # 1. GOLE RADIALI ESTERNE (OD) O INTERNE (ID)
        is_od = (tipo_ciclo == "Gola Esterna Radiale (OD)")                                     # True se esterna, False se interna
        z_right = float(z_start)                                                                # Spalla destra della gola (verso Z+)
        z_left = max(z_right - w_tot, z_lim_griffe)                                             # Spalla sinistra della gola (limitata dalle griffe!)
        z_eff_min = z_left                                                                      # Quota minima raggiunta lungo Z

        r_ini = max(float(d_inizio) / 2.0, 0.5)                                                 # Raggio d'imbocco della gola
        r_fin = max(float(d_fondo) / 2.0, 0.0)                                                  # Raggio di fondo della gola
        if is_od and r_fin >= r_ini: r_fin = max(r_ini - 2.0, 0.0)                              # Garantisce che il fondo OD sia minore dell'imbocco
        if (not is_od) and r_fin <= r_ini: r_fin = r_ini + 2.0                                  # Garantisce che il fondo ID sia maggiore dell'imbocco

        r_sic = (r_ini + max(float(sic_x), 1.0)) if is_od else max(r_ini - max(float(sic_x), 1.0), 0.5)
        s_fondo = max(float(sovra_fondo), 0.0) if finitura_fianchi else 0.0                     # Sovrametallo sul fondo per eventuale passata di finitura
        s_fianco = max(float(sovra_fianco), 0.0) if finitura_fianchi else 0.0                   # Sovrametallo sui fianchi per eventuale passata di finitura
        r_plunge_target = (r_fin + s_fondo) if is_od else (r_fin - s_fondo)                     # Raggio dove si fermano i tuffi di sgrossatura

        stazioni_z, _, _ = calcola_stazioni_plunge(z_right, z_left, w_tool, stepover_perc, s_fianco)

        if not is_od:                                                                           # Avvicinamento iniziale per gola interna (entra nel foro)
            add_segment("G0", r_sic, safe_z_front)                                              # Allinea il bareno da gola davanti al foro

        for z_st in stazioni_z:                                                                 # Esegue i tuffi radiali su ogni stazione Z
            add_segment("G0", r_sic, z_st)                                                      # Si posiziona in rapido sopra la stazione Z del tuffo
            if usa_peck:                                                                        # Affondamento frazionato con scarico truciolo (Pecking)
                r_curr = r_ini                                                                  # Parte dal raggio d'imbocco
                add_segment("G0", r_curr + (0.3 if is_od else -0.3), z_st)                      # Si avvicina a 0.3 mm dal materiale
                if is_od:                                                                       # Pecking esterno verso -X
                    while r_curr > r_plunge_target + 1e-4:                                      # Finché non raggiunge il fondo gola
                        r_next = max(r_curr - peck_q, r_plunge_target)                          # Quota del peck corrente
                        add_segment("G1", r_next, z_st, feed_plunge)                            # Affonda in G01
                        if r_next > r_plunge_target + 1e-4:                                     # Se non è ancora arrivato in fondo
                            add_segment("G0", min(r_next + peck_ret, r_sic), z_st)              # Ritrae di peck_ret per spezzare il truciolo
                            add_segment("G0", r_next + 0.1, z_st)                               # Torna vicino al fondo precedente
                        r_curr = r_next                                                         # Aggiorna quota raggiunta
                else:                                                                           # Pecking interno verso +X
                    while r_curr < r_plunge_target - 1e-4:                                      # Finché non raggiunge il fondo gola interna
                        r_next = min(r_curr + peck_q, r_plunge_target)                          # Quota del peck corrente
                        add_segment("G1", r_next, z_st, feed_plunge)                            # Affonda in G01 verso +X
                        if r_next < r_plunge_target - 1e-4:                                     # Se non è arrivato in fondo
                            add_segment("G0", max(r_next - peck_ret, r_sic), z_st)              # Ritrae verso il centro
                            add_segment("G0", r_next - 0.1, z_st)                               # Torna vicino al taglio
                        r_curr = r_next                                                         # Aggiorna quota
            else:                                                                               # Tuffo diretto continuo fino al fondo
                add_segment("G1", r_plunge_target, z_st, feed_plunge)                           # Affonda in G01 fino al raggio di fondo

            add_segment("G0", r_sic, z_st)                                                      # Esce in rapido al raggio di sicurezza fuori dalla gola

        if finitura_fianchi and (z_right - z_left) > w_tool + 0.05:                             # Passata di profilatura/finitura dei due fianchi e del fondo
            z_centro_fin = (z_right + z_left + w_tool) / 2.0                                    # Punto d'incontro a metà fondo gola
            segno = 1.0 if is_od else -1.0                                                      # Verso radiale esterno (+1) o interno (-1)

            add_segment("G0", r_sic, z_right + smusso)                                          # 1. Fianco Destro: parte sopra l'imbocco destro (+ eventuale smusso)
            add_segment("G1", r_ini, z_right + smusso, feed_fin)                                # Tocca il diametro d'imbocco
            if smusso > 0.01:                                                                   # Se è richiesto lo smusso sugli spigoli della gola
                add_segment("G1", r_ini - segno * smusso, z_right, feed_fin)                    # Esegue lo smusso a 45° sullo spigolo destro
            add_segment("G1", r_fin, z_right, feed_fin)                                         # Scende lungo la spalla destra fino al fondo nominale
            add_segment("G1", r_fin, z_centro_fin, feed_fin)                                    # Pulisce la metà destra del fondo gola
            add_segment("G0", r_sic, z_centro_fin)                                              # Risale in rapido fuori dalla gola

            z_left_punta = z_left + w_tool                                                      # Posizione della punta affinché il fianco sinistro lama tocchi z_left
            add_segment("G0", r_sic, z_left_punta - smusso)                                     # 2. Fianco Sinistro: si porta sopra lo spigolo sinistro
            add_segment("G1", r_ini, z_left_punta - smusso, feed_fin)                           # Tocca il diametro d'imbocco
            if smusso > 0.01:                                                                   # Se è richiesto lo smusso sinistro
                add_segment("G1", r_ini - segno * smusso, z_left_punta, feed_fin)               # Esegue lo smusso a 45° sullo spigolo sinistro
            add_segment("G1", r_fin, z_left_punta, feed_fin)                                    # Scende lungo la spalla sinistra fino al fondo nominale
            add_segment("G1", r_fin, z_centro_fin, feed_fin)                                    # Pulisce la metà sinistra del fondo gola sovrapponendosi al centro
            add_segment("G0", r_sic, z_centro_fin)                                              # Risale in rapido fuori dalla gola

        if not is_od:                                                                           # Disimpegno finale dal foro per gola interna
            add_segment("G0", r_sic, safe_z_front)                                              # Esce assialmente dal foro in sicurezza
        add_segment("G0", safe_r_od, safe_z_front)                                              # Ritorna al punto di sicurezza generale

    else:                                                                                       # 2. GOLA FRONTALE ASSIALE (FACE GROOVING LUNGO -Z)
        r_outer = max(float(d_inizio) / 2.0, w_tool + 1.0)                                      # Raggio esterno della gola frontale
        r_inner = max(r_outer - w_tot, 0.0)                                                     # Raggio interno della gola frontale
        z_faccia = float(z_start)                                                               # Quota Z della faccia su cui scavare (es. 0.0)
        prof_ax = max(abs(float(d_fondo)), 0.5)                                                 # Profondità assiale della gola frontale (mm)
        z_fondo_ax = max(z_faccia - prof_ax, z_lim_griffe)                                      # Quota Z del fondo della gola frontale
        z_eff_min = z_fondo_ax                                                                  # Quota minima Z

        z_sic_ax = z_faccia + max(float(sic_z), 1.5)                                            # Quota Z di sicurezza davanti alla faccia
        s_fondo = max(float(sovra_fondo), 0.0) if finitura_fianchi else 0.0                     # Sovrametallo sul fondo Z
        s_fianco = max(float(sovra_fianco), 0.0) if finitura_fianchi else 0.0                   # Sovrametallo sulle pareti radiali
        z_plunge_target = z_fondo_ax + s_fondo                                                  # Quota Z dove si fermano i tuffi assiali

        stazioni_r, _, _ = calcola_stazioni_plunge(r_outer, r_inner, w_tool, stepover_perc, s_fianco)

        for r_st in stazioni_r:                                                                 # Esegue i tuffi assiali lungo -Z su ogni raggio
            add_segment("G0", r_st, z_sic_ax)                                                   # Si posiziona in rapido davanti al raggio del tuffo
            if usa_peck:                                                                        # Pecking assiale lungo -Z
                z_curr = z_faccia                                                               # Parte dalla faccia
                add_segment("G0", r_st, z_curr + 0.3)                                           # Si avvicina a 0.3 mm dalla faccia
                while z_curr > z_plunge_target + 1e-4:                                          # Finché non raggiunge il fondo assiale
                    z_next = max(z_curr - peck_q, z_plunge_target)                              # Quota del peck corrente
                    add_segment("G1", r_st, z_next, feed_plunge)                                # Affonda lungo -Z
                    if z_next > z_plunge_target + 1e-4:                                         # Se non è ancora arrivato sul fondo
                        add_segment("G0", r_st, min(z_next + peck_ret, z_sic_ax))               # Ritrae lungo +Z per spezzare il truciolo
                        add_segment("G0", r_st, z_next + 0.1)                                   # Ritorna vicino al taglio
                    z_curr = z_next                                                             # Aggiorna quota
            else:                                                                               # Tuffo assiale diretto
                add_segment("G1", r_st, z_plunge_target, feed_plunge)                           # Affonda fino a fondo gola

            add_segment("G0", r_st, z_sic_ax)                                                   # Esce in rapido lungo +Z fuori dalla gola frontale

        if finitura_fianchi and (r_outer - r_inner) > w_tool + 0.05:                            # Finitura pareti superiore/inferiore e fondo della gola frontale
            r_centro_fin = (r_outer + r_inner + w_tool) / 2.0                                   # Raggio intermedio sul fondo
            add_segment("G0", r_outer + smusso, z_sic_ax)                                       # Parete esterna superiore
            add_segment("G1", r_outer + smusso, z_faccia, feed_fin)                             # Tocca la faccia frontale
            if smusso > 0.01:                                                                   # Eventuale smusso esterno
                add_segment("G1", r_outer, z_faccia - smusso, feed_fin)                         # Smusso a 45°
            add_segment("G1", r_outer, z_fondo_ax, feed_fin)                                    # Scende lungo la parete esterna fino al fondo Z
            add_segment("G1", r_centro_fin, z_fondo_ax, feed_fin)                               # Pulisce metà fondo verso il centro
            add_segment("G0", r_centro_fin, z_sic_ax)                                           # Esce lungo +Z

            r_inner_punta = r_inner + w_tool                                                    # Raggio punta per la parete interna
            add_segment("G0", r_inner_punta - smusso, z_sic_ax)                                 # Parete interna inferiore
            add_segment("G1", r_inner_punta - smusso, z_faccia, feed_fin)                       # Tocca la faccia frontale
            if smusso > 0.01:                                                                   # Eventuale smusso interno
                add_segment("G1", r_inner_punta, z_faccia - smusso, feed_fin)                   # Smusso a 45°
            add_segment("G1", r_inner_punta, z_fondo_ax, feed_fin)                              # Scende lungo la parete interna
            add_segment("G1", r_centro_fin, z_fondo_ax, feed_fin)                               # Completa la pulizia del fondo
            add_segment("G0", r_centro_fin, z_sic_ax)                                           # Esce in rapido lungo +Z

        add_segment("G0", safe_r_od, safe_z_front)                                              # Ritorna in posizione di sicurezza

    shapes_all = []                                                                             # Lista globale dei segmenti 3D
    if edges_rapidi: shapes_all.extend(edges_rapidi)                                            # Unisce i rapidi
    if edges_lavoro: shapes_all.extend(edges_lavoro)                                            # Unisce i movimenti di taglio

    comp = Part.makeCompound(shapes_all) if shapes_all else Part.makeSphere(0.5, wcs)           # Compound finale dell'operazione
    comp_rapidi = Part.makeCompound(edges_rapidi) if edges_rapidi else None                     # Compound rapidi per anteprima rossa
    comp_lavoro = Part.makeCompound(edges_lavoro) if edges_lavoro else None                     # Compound lavoro per anteprima gialla/ambra
    return comp, comp_rapidi, comp_lavoro, moves, z_eff_min                                     # Restituisce geometrie, punti G-Code e Z minima


class LatheGroovingObject:                                                                      # Classe Proxy per l'operazione parametrica di Gola
    def __init__(self, obj):                                                                    # Costruttore del Proxy
        self._is_executing = False                                                              # Semaforo anti-ricorsione
        self.ensure_properties(obj)                                                             # Garantisce la creazione di tutte le proprietà
        obj.Proxy = self                                                                        # Collega il Proxy all'oggetto FreeCAD

    def ensure_properties(self, obj):                                                           # Aggiunge le proprietà native se mancanti
        if not hasattr(obj, "OperationName"):                                                   # Nome operazione
            obj.addProperty("App::PropertyString", "OperationName", "Operazione", "Nome operazione").OperationName = "Gola Esterna 1"
        if not hasattr(obj, "TipoCiclo"):                                                       # Modalità gola (OD, ID, Frontale)
            obj.addProperty("App::PropertyEnumeration", "TipoCiclo", "Operazione", "Tipologia di gola")
            obj.TipoCiclo = TIPI_CICLO_GOLA                                                     # Assegna le 3 modalità
        if not hasattr(obj, "UtensileAssegnato"):                                               # Utensile selezionato dal Magazzino
            obj.addProperty("App::PropertyString", "UtensileAssegnato", "Operazione", "Utensile da gola utilizzato").UtensileAssegnato = ""
        if not hasattr(obj, "LarghezzaLama"):                                                   # Larghezza effettiva dell'inserto/lama (mm)
            obj.addProperty("App::PropertyFloat", "LarghezzaLama", "Operazione", "Larghezza lama utensile (mm)").LarghezzaLama = 3.0
        if not hasattr(obj, "Z_InizioGola"):                                                    # Quota Z spalla destra (o quota Z faccia frontale)
            obj.addProperty("App::PropertyFloat", "Z_InizioGola", "Geometria Gola", "Quota Z spalla destra / inizio gola (mm)").Z_InizioGola = -20.0
        if not hasattr(obj, "LarghezzaGola"):                                                   # Larghezza totale della gola (mm)
            obj.addProperty("App::PropertyFloat", "LarghezzaGola", "Geometria Gola", "Larghezza totale della gola (mm)").LarghezzaGola = 6.0
        if not hasattr(obj, "DiametroInizioGola"):                                              # Diametro d'imbocco della gola (mm)
            obj.addProperty("App::PropertyFloat", "DiametroInizioGola", "Geometria Gola", "Diametro esterno/imbocco gola (mm)").DiametroInizioGola = 50.0
        if not hasattr(obj, "DiametroFondoGola"):                                               # Diametro sul fondo gola (o profondità assiale per Face)
            obj.addProperty("App::PropertyFloat", "DiametroFondoGola", "Geometria Gola", "Diametro fondo gola (o prof. assiale) (mm)").DiametroFondoGola = 40.0
        if not hasattr(obj, "SmussoBordi"):                                                     # Smusso a 45° sugli spigoli d'imbocco della gola (mm)
            obj.addProperty("App::PropertyFloat", "SmussoBordi", "Geometria Gola", "Smusso sugli spigoli della gola (mm)").SmussoBordi = 0.3
        if not hasattr(obj, "UsaScaricoTruciolo"):                                              # Attiva/disattiva il pecking (G75)
            obj.addProperty("App::PropertyBool", "UsaScaricoTruciolo", "Parametri Taglio", "Affondamento con scarico truciolo (Peck)").UsaScaricoTruciolo = True
        if not hasattr(obj, "PassoPeck"):                                                       # Incremento di affondamento per ogni peck (mm)
            obj.addProperty("App::PropertyFloat", "PassoPeck", "Parametri Taglio", "Profondità incremento Peck Q (mm)").PassoPeck = 1.5
        if not hasattr(obj, "RitrazionePeck"):                                                  # Distacco rompi-truciolo tra un peck e l'altro (mm)
            obj.addProperty("App::PropertyFloat", "RitrazionePeck", "Parametri Taglio", "Ritrazione rompi-truciolo (mm)").RitrazionePeck = 0.3
        if not hasattr(obj, "PassoLateralePerc"):                                               # Sormonto percentuale della lama tra i tuffi (10..95%)
            obj.addProperty("App::PropertyFloat", "PassoLateralePerc", "Parametri Taglio", "Passo laterale in % della larghezza lama").PassoLateralePerc = 75.0
        if not hasattr(obj, "FinituraFianchi"):                                                 # Esegue la passata continua finale su fianchi e fondo
            obj.addProperty("App::PropertyBool", "FinituraFianchi", "Parametri Taglio", "Esegui passata di finitura su fianchi e fondo").FinituraFianchi = True
        if not hasattr(obj, "SovrametalloFondo"):                                               # Sovrametallo lasciato sul fondo per la finitura (mm)
            obj.addProperty("App::PropertyFloat", "SovrametalloFondo", "Parametri Taglio", "Sovrametallo sul fondo gola (mm)").SovrametalloFondo = 0.15
        if not hasattr(obj, "SovrametalloFianco"):                                              # Sovrametallo lasciato sulle spalle per la finitura (mm)
            obj.addProperty("App::PropertyFloat", "SovrametalloFianco", "Parametri Taglio", "Sovrametallo sui fianchi gola (mm)").SovrametalloFianco = 0.15
        if not hasattr(obj, "VelocitaTaglio"):                                                  # Velocità di taglio Vc / RPM
            obj.addProperty("App::PropertyFloat", "VelocitaTaglio", "Parametri Taglio", "Velocità di taglio Vc / RPM").VelocitaTaglio = 120.0
        if not hasattr(obj, "AvanzamentoTuffo"):                                                # Avanzamento di affondamento a tuffo (mm/giro)
            obj.addProperty("App::PropertyFloat", "AvanzamentoTuffo", "Parametri Taglio", "Avanzamento a tuffo F (mm/giro)").AvanzamentoTuffo = 0.08
        if not hasattr(obj, "AvanzamentoFinitura"):                                             # Avanzamento di finitura fianchi (mm/giro)
            obj.addProperty("App::PropertyFloat", "AvanzamentoFinitura", "Parametri Taglio", "Avanzamento finitura fianchi (mm/giro)").AvanzamentoFinitura = 0.10
        if not hasattr(obj, "PercorsoJSON"):                                                    # Punti del percorso salvati per Simulatore e G-Code
            obj.addProperty("App::PropertyString", "PercorsoJSON", "Dati CAM", "Punti percorso per Simulatore e G-Code").PercorsoJSON = "[]"

    def onDocumentRestored(self, obj):                                                          # Chiamato alla riapertura del documento
        self._is_executing = False                                                              # Sblocca il flag
        self.ensure_properties(obj)                                                             # Verifica le proprietà

    def execute(self, obj):                                                                     # Ricalcola il percorso 3D della gola
        if getattr(self, "_is_executing", False):                                               # Evita loop ricorsivi
            return                                                                              # Esce subito
        self._is_executing = True                                                               # Attiva il semaforo
        try:                                                                                    # Blocco protetto di calcolo
            self.ensure_properties(obj)                                                         # Verifica attributi
            doc = obj.Document                                                                  # Documento corrente
            wcs = LatheRoughing.get_wcs_origin(doc)                                             # Origine WCS
            sic_x, sic_z = LatheRoughing.get_setup_safe_clearances(doc)                         # Sicurezze Setup
            stock_info = LatheRoughing.get_stock_info(doc)                                      # Dati Grezzo e limite griffe

            comp, _, _, moves, _ = calcola_percorso_gola(                                       # Genera il percorso utensile
                wcs, str(obj.TipoCiclo), stock_info,
                obj.Z_InizioGola, obj.LarghezzaGola,
                obj.DiametroInizioGola, obj.DiametroFondoGola,
                obj.LarghezzaLama, obj.UsaScaricoTruciolo,
                obj.PassoPeck, obj.RitrazionePeck, obj.PassoLateralePerc,
                obj.FinituraFianchi, obj.SovrametalloFondo, obj.SovrametalloFianco, obj.SmussoBordi,
                sic_x, sic_z, obj.AvanzamentoTuffo, obj.AvanzamentoFinitura
            )                                                                                   # Fine calcolo
            obj.PercorsoJSON = json.dumps(moves)                                                # Salva il percorso per il Simulatore e il Post-Processor
            obj.Shape = comp                                                                    # Assegna la Shape 3D
            if hasattr(obj, "ViewObject") and obj.ViewObject:                                   # Colora il tracciato della gola in Giallo/Ambra
                obj.ViewObject.LineColor = (1.00, 0.75, 0.10)                                   # Giallo Ambra ben distinguibile
                obj.ViewObject.LineWidth = 2.5                                                  # Spessore linea
        except Exception as e:                                                                  # Cattura errori imprevisti
            FreeCAD.Console.PrintError(f"Errore calcolo Gola: {e}\n")                           # Stampa in console
        finally:                                                                                # Rilascia il semaforo
            self._is_executing = False                                                          # Fine esecuzione

    def onChanged(self, obj, prop):                                                             # Intercetta modifiche live dalle Proprietà di FreeCAD
        if getattr(self, "_is_executing", False):                                               # Evita ricorsioni
            return                                                                              # Esce
        props_calcolo = [                                                                       # Proprietà che rigenerano il percorso
            "TipoCiclo", "LarghezzaLama", "Z_InizioGola", "LarghezzaGola",                      # Geometria base
            "DiametroInizioGola", "DiametroFondoGola", "SmussoBordi",                           # Quote diametrali e smussi
            "UsaScaricoTruciolo", "PassoPeck", "RitrazionePeck", "PassoLateralePerc",           # Parametri di tuffo
            "FinituraFianchi", "SovrametalloFondo", "SovrametalloFianco",                       # Finitura pareti
            "AvanzamentoTuffo", "AvanzamentoFinitura"                                           # Avanzamenti
        ]                                                                                       # Fine lista
        if prop in props_calcolo:                                                               # Se cambia un parametro geometrico/tecnologico
            self.execute(obj)                                                                   # Aggiorna il percorso 3D
        elif prop == "OperationName":                                                           # Se cambia il nome operazione
            if hasattr(obj, "OperationName") and obj.OperationName:                             # Allinea l'etichetta nell'albero
                obj.Label = obj.OperationName                                                   # Imposta Label

    def __getstate__(self):                                                                     # Serializzazione
        return None                                                                             # Nessun dato speciale

    def __setstate__(self, state):                                                              # Deserializzazione
        self._is_executing = False                                                              # Ripristina flag
        return None                                                                             # Fine


class ViewProviderLatheGrooving:                                                                # ViewProvider per icona e doppio click sull'operazione di Gola
    def __init__(self, vobj):                                                                   # Costruttore ViewProvider
        vobj.Proxy = self                                                                       # Collega il Proxy

    def getIcon(self):                                                                          # Icona nell'albero delle operazioni
        return LatheResources.get_icon_path("lathe_grooving.svg", "Part_JoinCutout")            # Icona SVG dedicata Gola

    def attach(self, vobj):                                                                     # Collega gli oggetti alla vista
        self.ViewObject = vobj                                                                  # Riferimento ViewObject
        self.Object = vobj.Object                                                               # Riferimento Object

    def updateData(self, vobj, prop):                                                           # Aggiornamento dati
        return                                                                                  # Gestito da execute

    def onDelete(self, vobj, subelements):                                                      # Autorizza cancellazione
        return True                                                                             # Sempre consentito

    def doubleClicked(self, vobj):                                                              # Doppio click sull'operazione nell'albero
        if not FreeCADGui.Control.activeDialog():                                               # Se non c'è già un pannello aperto
            panel = LatheGroovingPanel(edit_obj=vobj.Object)                                    # Apre il pannello caricando l'operazione
            FreeCADGui.Control.showDialog(panel)                                                # Mostra il pannello nella scheda Azioni
        return True                                                                             # Evento gestito

    def setEdit(self, vobj, mode):                                                              # Modalità Edit standard
        if mode == 0:                                                                           # Modifica base
            if not FreeCADGui.Control.activeDialog():                                           # Evita doppia apertura
                panel = LatheGroovingPanel(edit_obj=vobj.Object)                                # Crea il pannello
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


class LatheGroovingPanel:                                                                       # Pannello Task per programmare il ciclo di Gola / Scarico
    def __init__(self, edit_obj=None):                                                          # Costruttore del pannello (nuovo o modifica)
        self.edit_obj = edit_obj                                                                # Memorizza eventuale operazione in modifica
        self.is_updating = True                                                                 # Blocca i segnali durante la costruzione della UI

        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        self.pulisci_anteprima_percorso(doc)                                                    # Pulisce eventuali anteprime rimaste appese
        if self.edit_obj and hasattr(self.edit_obj, "ViewObject") and self.edit_obj.ViewObject: # Se siamo in modifica
            self.edit_obj.ViewObject.Visibility = False                                         # Nasconde l'originale durante l'anteprima bicolore

        self.form = QtWidgets.QWidget()                                                         # Contenitore principale del pannello
        self.form.setMinimumWidth(240)                                                          # Larghezza minima compatta per non tagliare a destra
        self.layout = QtWidgets.QVBoxLayout(self.form)                                          # Layout verticale principale
        self.layout.setContentsMargins(4, 4, 4, 4)                                              # Margini ridotti

        self.grp_gen = QtWidgets.QGroupBox("Operazione e Utensile da Gola")                     # Gruppo dati generali
        self.lyt_gen = QtWidgets.QFormLayout(self.grp_gen)                                      # Form layout

        self.name_input = QtWidgets.QLineEdit("Gola Esterna 1")                                 # Nome operazione
        self.cycle_combo = QtWidgets.QComboBox()                                                # Scelta tipologia gola (OD, ID, Frontale)
        self.cycle_combo.addItems(TIPI_CICLO_GOLA)                                              # Popola le 3 modalità
        self.cycle_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cycle_combo.setMinimumContentsLength(10)

        self.tool_combo = QtWidgets.QComboBox()                                                 # Scelta utensile dal Magazzino Utensili
        self.tool_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.tool_combo.setMinimumContentsLength(10)
        self.popola_combo_utensili(doc)                                                         # Carica gli utensili (preferendo quelli da Gola)

        self.lama_w_spin = QtWidgets.QDoubleSpinBox()                                           # Larghezza lama/inserto (letta dall'utensile o modificabile)
        self.lama_w_spin.setRange(0.5, 25.0); self.lama_w_spin.setDecimals(2); self.lama_w_spin.setValue(3.0); self.lama_w_spin.setSingleStep(0.5)

        self.lyt_gen.addRow("Nome:", self.name_input)                                           # Riga Nome
        self.lyt_gen.addRow("Tipo Gola:", self.cycle_combo)                                     # Riga Tipo Gola
        self.lyt_gen.addRow("Utensile:", self.tool_combo)                                       # Riga Utensile
        self.lyt_gen.addRow("Largh. Lama W (mm):", self.lama_w_spin)                            # Riga Larghezza Lama
        self.layout.addWidget(self.grp_gen)                                                     # Aggiunge al layout principale

        self.tabs = QtWidgets.QTabWidget()                                                      # Schede: 1. Quote Gola | 2. Pecking & Finitura

        self.tab_geo = QtWidgets.QWidget()                                                      # SCHEDA 1: Posizione e Dimensioni della Gola
        self.lyt_geo = QtWidgets.QVBoxLayout(self.tab_geo)                                      # Layout verticale Scheda 1

        self.grp_geo = QtWidgets.QGroupBox("Posizione e Dimensioni Gola")                       # Gruppo geometria gola
        self.lyt_g_form = QtWidgets.QFormLayout(self.grp_geo)                                   # Form layout

        self.btn_pick_groove = QtWidgets.QPushButton("Cattura Quota Gola da Faccia 3D")         # Rileva automaticamente Z, Larghezza e Ø Fondo cliccando sul 3D
        self.btn_pick_groove.clicked.connect(self.cattura_gola_da_faccia_3d)                    # Collega la cattura 3D

        stock_info = LatheRoughing.get_stock_info(doc)                                          # Legge le quote del Grezzo_Macchina
        d_ext_grezzo = stock_info["r_ext"] * 2.0                                                # Diametro esterno grezzo

        self.lbl_z_start = QtWidgets.QLabel("Z Spalla Destra (mm):")                            # Etichetta dinamica Z inizio
        self.z_start_spin = QtWidgets.QDoubleSpinBox(); self.z_start_spin.setRange(-2000, 2000); self.z_start_spin.setDecimals(2); self.z_start_spin.setValue(-20.0)
        self.w_groove_spin = QtWidgets.QDoubleSpinBox(); self.w_groove_spin.setRange(0.5, 500.0); self.w_groove_spin.setDecimals(2); self.w_groove_spin.setValue(6.0)
        self.lbl_d_ini = QtWidgets.QLabel("Ø Imbocco Gola (mm):")                               # Etichetta dinamica Ø imbocco
        self.d_ini_spin = QtWidgets.QDoubleSpinBox(); self.d_ini_spin.setRange(1.0, 2000.0); self.d_ini_spin.setDecimals(2); self.d_ini_spin.setValue(d_ext_grezzo)
        self.lbl_d_fin = QtWidgets.QLabel("Ø Fondo Gola (mm):")                                 # Etichetta dinamica Ø fondo (o profondità assiale)
        self.d_fin_spin = QtWidgets.QDoubleSpinBox(); self.d_fin_spin.setRange(0.0, 2000.0); self.d_fin_spin.setDecimals(2); self.d_fin_spin.setValue(max(d_ext_grezzo - 10.0, 10.0))
        self.chamfer_spin = QtWidgets.QDoubleSpinBox(); self.chamfer_spin.setRange(0.0, 10.0); self.chamfer_spin.setDecimals(2); self.chamfer_spin.setValue(0.3); self.chamfer_spin.setSingleStep(0.1)

        self.lbl_status = QtWidgets.QLabel("Pronto. Clicca il fondo gola nel 3D o imposta le quote.")
        self.lbl_status.setWordWrap(True)                                                       # Va a capo automaticamente
        self.lbl_status.setStyleSheet("color: #FFBB00; font-weight: bold;")                     # Giallo/Ambra

        self.lyt_g_form.addRow(self.btn_pick_groove)                                            # Riga pulsante cattura da faccia 3D
        self.lyt_g_form.addRow(self.lbl_z_start, self.z_start_spin)                             # Riga Z Spalla Destra
        self.lyt_g_form.addRow("Larghezza Gola (mm):", self.w_groove_spin)                      # Riga Larghezza Gola
        self.lyt_g_form.addRow(self.lbl_d_ini, self.d_ini_spin)                                 # Riga Diametro Imbocco
        self.lyt_g_form.addRow(self.lbl_d_fin, self.d_fin_spin)                                 # Riga Diametro Fondo
        self.lyt_g_form.addRow("Smusso Spigoli (mm):", self.chamfer_spin)                       # Riga Smusso d'imbocco
        self.lyt_g_form.addRow(self.lbl_status)                                                 # Riga stato
        self.lyt_geo.addWidget(self.grp_geo)                                                    # Aggiunge alla Scheda 1

        self.tabs.addTab(self.tab_geo, "1. Geometria")                                          # Titolo Scheda 1

        self.tab_cut = QtWidgets.QWidget()                                                      # SCHEDA 2: Scarico Truciolo (Peck) e Finitura Fianchi
        self.lyt_cut = QtWidgets.QVBoxLayout(self.tab_cut)                                      # Layout verticale Scheda 2

        self.grp_cut = QtWidgets.QGroupBox("Scarico Truciolo (Peck) e Finitura Fianchi")        # Gruppo parametri tecnologici gola
        self.lyt_c_form = QtWidgets.QFormLayout(self.grp_cut)                                   # Form layout

        self.chk_peck = QtWidgets.QCheckBox("Affondamento con Scarico Truciolo (Peck)")         # Attiva il pecking
        self.chk_peck.setChecked(True)                                                          # Attivo di default
        self.peck_q_spin = QtWidgets.QDoubleSpinBox(); self.peck_q_spin.setRange(0.2, 50.0); self.peck_q_spin.setDecimals(2); self.peck_q_spin.setValue(1.5); self.peck_q_spin.setSingleStep(0.5)
        self.peck_ret_spin = QtWidgets.QDoubleSpinBox(); self.peck_ret_spin.setRange(0.05, 10.0); self.peck_ret_spin.setDecimals(2); self.peck_ret_spin.setValue(0.3); self.peck_ret_spin.setSingleStep(0.1)
        self.stepover_spin = QtWidgets.QDoubleSpinBox(); self.stepover_spin.setRange(10.0, 95.0); self.stepover_spin.setDecimals(0); self.stepover_spin.setValue(75.0); self.stepover_spin.setSingleStep(5.0)

        self.chk_fin_walls = QtWidgets.QCheckBox("Esegui Passata di Finitura Fianchi e Fondo")  # Attiva profilatura finale spalle
        self.chk_fin_walls.setChecked(True)                                                     # Attivo di default
        self.sovra_fondo_spin = QtWidgets.QDoubleSpinBox(); self.sovra_fondo_spin.setRange(0.0, 5.0); self.sovra_fondo_spin.setDecimals(2); self.sovra_fondo_spin.setValue(0.15); self.sovra_fondo_spin.setSingleStep(0.05)
        self.sovra_fianco_spin = QtWidgets.QDoubleSpinBox(); self.sovra_fianco_spin.setRange(0.0, 5.0); self.sovra_fianco_spin.setDecimals(2); self.sovra_fianco_spin.setValue(0.15); self.sovra_fianco_spin.setSingleStep(0.05)

        self.vc_spin = QtWidgets.QDoubleSpinBox(); self.vc_spin.setRange(1.0, 15000.0); self.vc_spin.setValue(120.0); self.vc_spin.setSingleStep(10.0)
        self.f_plunge_spin = QtWidgets.QDoubleSpinBox(); self.f_plunge_spin.setRange(0.005, 5.0); self.f_plunge_spin.setDecimals(3); self.f_plunge_spin.setValue(0.08); self.f_plunge_spin.setSingleStep(0.01)
        self.f_fin_spin = QtWidgets.QDoubleSpinBox(); self.f_fin_spin.setRange(0.005, 5.0); self.f_fin_spin.setDecimals(3); self.f_fin_spin.setValue(0.10); self.f_fin_spin.setSingleStep(0.02)

        self.lyt_c_form.addRow(self.chk_peck)                                                   # Riga checkbox Peck
        self.lyt_c_form.addRow("Incremento Peck Q (mm):", self.peck_q_spin)                     # Riga passo Peck Q
        self.lyt_c_form.addRow("Ritrazione Peck (mm):", self.peck_ret_spin)                     # Riga ritrazione Peck
        self.lyt_c_form.addRow("Sormonto Lama (%):", self.stepover_spin)                        # Riga passo laterale %
        self.lyt_c_form.addRow(self.chk_fin_walls)                                              # Riga checkbox finitura fianchi
        self.lyt_c_form.addRow("Sovram. Fondo (mm):", self.sovra_fondo_spin)                    # Riga sovrametallo fondo
        self.lyt_c_form.addRow("Sovram. Fianchi (mm):", self.sovra_fianco_spin)                 # Riga sovrametallo fianchi
        self.lyt_c_form.addRow("Velocità Vc / RPM:", self.vc_spin)                              # Riga velocità di taglio
        self.lyt_c_form.addRow("Avanz. Tuffo F (mm/g):", self.f_plunge_spin)                    # Riga avanzamento a tuffo
        self.lyt_c_form.addRow("Avanz. Finitura (mm/g):", self.f_fin_spin)                      # Riga avanzamento finitura fianchi
        self.lyt_cut.addWidget(self.grp_cut)                                                    # Aggiunge alla Scheda 2
        self.lyt_cut.addStretch()                                                               # Allinea in alto

        self.tabs.addTab(self.tab_cut, "2. Parametri")                                          # Titolo Scheda 2
        self.layout.addWidget(self.tabs)                                                        # Aggiunge il TabWidget al layout principale
        self.form.setLayout(self.layout)                                                        # Applica il layout

        self.preview_rapidi = doc.addObject("Part::Feature", "TMP_Groove_Rapids")               # Oggetto temporaneo per i rapidi G00 (Rosso)
        self.preview_rapidi.Label = "ANTEPRIMA RAPIDI GOLA"                                     # Etichetta
        self.preview_rapidi.ViewObject.LineColor = (0.95, 0.20, 0.20)                           # Rosso per i rapidi
        self.preview_rapidi.ViewObject.LineWidth = 1.5                                          # Spessore linea rapidi

        self.preview_lavoro = doc.addObject("Part::Feature", "TMP_Groove_Cut")                  # Oggetto temporaneo per i tagli G01 (Giallo Ambra)
        self.preview_lavoro.Label = "ANTEPRIMA TAGLIO GOLA"                                     # Etichetta
        self.preview_lavoro.ViewObject.LineColor = (1.00, 0.78, 0.10)                           # Giallo Ambra per il taglio gola
        self.preview_lavoro.ViewObject.LineWidth = 2.5                                          # Spessore linea lavoro

        if self.edit_obj:                                                                       # Se siamo in modifica di un'operazione esistente
            self.carica_dati_da_oggetto(self.edit_obj)                                          # Ripristina i dati salvati
        else:                                                                                   # Se è una nuova operazione
            self.on_tool_changed()                                                              # Eredita LarghezzaLamaGola, Vc e F dall'utensile scelto

        self.cycle_combo.currentIndexChanged.connect(self.aggiorna_ui_ciclo)                    # Collega cambio tipo gola
        self.tool_combo.currentIndexChanged.connect(self.on_tool_changed)                       # Collega cambio utensile
        self.lama_w_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio larghezza lama
        self.z_start_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio Z inizio
        self.w_groove_spin.valueChanged.connect(self.trigger_update)                            # Collega cambio larghezza gola
        self.d_ini_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio Ø imbocco
        self.d_fin_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio Ø fondo
        self.chamfer_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio smusso
        self.chk_peck.stateChanged.connect(self.aggiorna_ui_ciclo)                              # Collega spunta Peck
        self.peck_q_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio passo Peck
        self.peck_ret_spin.valueChanged.connect(self.trigger_update)                            # Collega cambio ritrazione Peck
        self.stepover_spin.valueChanged.connect(self.trigger_update)                            # Collega cambio sormonto %
        self.chk_fin_walls.stateChanged.connect(self.aggiorna_ui_ciclo)                         # Collega spunta finitura fianchi
        self.sovra_fondo_spin.valueChanged.connect(self.trigger_update)                         # Collega cambio sovrametallo fondo
        self.sovra_fianco_spin.valueChanged.connect(self.trigger_update)                        # Collega cambio sovrametallo fianchi
        self.f_plunge_spin.valueChanged.connect(self.trigger_update)                            # Collega cambio avanzamento tuffo
        self.f_fin_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio avanzamento finitura

        self.is_updating = False                                                                # Sblocca gli aggiornamenti live
        self.aggiorna_ui_ciclo()                                                                # Adatta le etichette e disegna l'anteprima 3D

    def popola_combo_utensili(self, doc):                                                       # Carica gli utensili del Magazzino (selezionando per primo quello da Gola)
        self.tool_combo.clear()                                                                 # Svuota il combo
        idx_gola = -1                                                                           # Indice del primo utensile da Gola trovato
        if doc and doc.getObject("Libreria_Utensili"):                                          # Se esiste il Magazzino Utensili
            lib = doc.getObject("Libreria_Utensili")                                            # Gruppo magazzino
            for i, t in enumerate(lib.Group):                                                   # Cicla sugli utensili
                st = getattr(t, "Stazione", "T01")                                              # Sigla stazione
                tipo_u = str(getattr(t, "TipoLavorazione", ""))                                 # Categoria utensile
                self.tool_combo.addItem(f"[{st}] {t.Label}", t.Name)                            # Aggiunge voce e Name interno
                if idx_gola < 0 and "Gola" in tipo_u:                                           # Se è un utensile da Gola / Troncatura
                    idx_gola = i                                                                # Memorizza l'indice
        if idx_gola >= 0:                                                                       # Se ha trovato un utensile specifico da gola
            self.tool_combo.setCurrentIndex(idx_gola)                                           # Lo preseleziona automaticamente

    def on_tool_changed(self):                                                                  # Legge LarghezzaLamaGola, Vc e Avanzamenti dall'utensile scelto
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc or self.tool_combo.count() == 0: return                                      # Verifica validità
        t_name = self.tool_combo.itemData(self.tool_combo.currentIndex())                       # Nome utensile
        t_obj = doc.getObject(t_name) if t_name else None                                       # Oggetto utensile
        if t_obj:                                                                               # Se esiste
            prev = self.is_updating                                                             # Salva stato semaforo
            self.is_updating = True                                                             # Sospende ricalcoli multipli
            w_l = float(getattr(t_obj, "LarghezzaLamaGola", 3.0))                               # Legge la larghezza lama dell'utensile
            self.lama_w_spin.setValue(max(w_l, 0.5))                                            # Imposta la larghezza lama nel pannello
            if self.w_groove_spin.value() < w_l:                                                # Se la gola era più stretta della lama
                self.w_groove_spin.setValue(w_l)                                                # Adegua la larghezza gola
            self.vc_spin.setValue(float(getattr(t_obj, "VelocitaTaglio", 120.0)))               # Legge Vc
            f_fin = float(getattr(t_obj, "AvanzamentoFinitura", 0.10))                          # Legge avanzamento finitura
            self.f_fin_spin.setValue(f_fin)                                                     # Imposta avanzamento finitura fianchi
            self.f_plunge_spin.setValue(round(max(f_fin * 0.75, 0.04), 3))                      # Imposta avanzamento a tuffo prudente (75% della finitura)
            self.is_updating = prev                                                             # Ripristina semaforo
            self.trigger_update()                                                               # Aggiorna l'anteprima 3D

    def cattura_gola_da_faccia_3d(self):                                                        # Rileva automaticamente Z, Larghezza e Ø Fondo dalla faccia cliccata nel 3D
        sel_ex = FreeCADGui.Selection.getSelectionEx()                                          # Ottiene la selezione estesa 3D
        if not sel_ex or not sel_ex[0].SubElementNames:                                         # Verifica che sia stata cliccata una faccia o un bordo
            self.lbl_status.setText("Clicca prima sulla faccia cilindrica del fondo gola nel 3D!")
            return                                                                              # Esce
        sub_name = sel_ex[0].SubElementNames[0]                                                 # Nome del sotto-elemento (es. Face4)
        obj_sel = sel_ex[0].Object                                                              # Oggetto 3D del pezzo
        elem = obj_sel.Shape.getElement(sub_name)                                               # Elemento geometrico selezionato
        bb = elem.BoundBox                                                                      # BoundBox della faccia selezionata
        wcs = LatheRoughing.get_wcs_origin(FreeCAD.ActiveDocument)                              # Origine WCS

        self.is_updating = True                                                                 # Sospende aggiornamenti multipli
        try:                                                                                    # Calcola le quote della gola rispetto al WCS
            ciclo = self.cycle_combo.currentText()                                              # Tipo di gola corrente
            if ciclo != "Gola Frontale Assiale (Face)":                                         # Caso Gola Esterna OD o Interna ID
                z_right_rel = bb.ZMax - wcs.z                                                   # Spalla destra della faccia cilindrica
                larg_rilevata = max(bb.ZLength, self.lama_w_spin.value())                       # Larghezza assiale della faccia cilindrica
                r_fondo = max(abs(bb.XMax - wcs.x), abs(bb.YMax - wcs.y))                       # Raggio del cilindro di fondo gola
                if hasattr(elem, "Surface") and hasattr(elem.Surface, "Radius"):                # Se è una superficie cilindrica esatta
                    r_fondo = float(elem.Surface.Radius)                                        # Legge il raggio matematico esatto!
                d_fondo = r_fondo * 2.0                                                         # Diametro di fondo gola rilevato
                self.z_start_spin.setValue(z_right_rel)                                         # Imposta Z Spalla Destra
                self.w_groove_spin.setValue(larg_rilevata)                                      # Imposta Larghezza Gola
                self.d_fin_spin.setValue(d_fondo)                                               # Imposta Diametro Fondo Gola
                bb_part = obj_sel.Shape.BoundBox                                                # BoundBox dell'intero pezzo per stimare il diametro d'imbocco
                r_part_max = max(abs(bb_part.XMax - wcs.x), abs(bb_part.YMax - wcs.y))          # Raggio esterno del pezzo
                if "Esterna" in ciclo and r_part_max > r_fondo + 0.2:                           # Se è una gola esterna
                    self.d_ini_spin.setValue(r_part_max * 2.0)                                  # Imposta il diametro d'imbocco esterno
            else:                                                                               # Caso Gola Frontale Assiale
                r_max_f = max(abs(bb.XMax - wcs.x), abs(bb.YMax - wcs.y))                       # Raggio esterno della gola frontale
                r_min_f = min(abs(bb.XMax - wcs.x), abs(bb.XMin - wcs.x))                       # Raggio interno
                self.d_ini_spin.setValue(r_max_f * 2.0)                                         # Diametro esterno inizio gola frontale
                if r_max_f - r_min_f > self.lama_w_spin.value():                                # Se ha larghezza radiale
                    self.w_groove_spin.setValue(r_max_f - r_min_f)                              # Larghezza radiale gola
                self.d_fin_spin.setValue(max(abs(bb.ZMax - bb.ZMin), 2.0))                      # Profondità assiale della gola frontale
        finally:                                                                                # Sblocca il semaforo
            self.is_updating = False                                                            # Riabilita
        FreeCADGui.Selection.clearSelection()                                                   # Pulisce la selezione verde
        self.lbl_status.setText(f"Quote gola rilevate da [{sub_name}]!")                        # Conferma
        self.trigger_update()                                                                   # Aggiorna subito il percorso 3D

    def aggiorna_ui_ciclo(self):                                                                # Adatta le etichette e i campi in base al tipo di gola
        ciclo = self.cycle_combo.currentText()                                                  # Tipo gola selezionato
        is_face = (ciclo == "Gola Frontale Assiale (Face)")                                     # True se è una gola frontale
        is_id = (ciclo == "Gola Interna Radiale (ID)")                                          # True se è una gola interna

        if is_face:                                                                             # Etichette per Gola Frontale Assiale
            self.lbl_z_start.setText("Quota Z Faccia (mm):")
            self.lbl_d_ini.setText("Ø Esterno Gola (mm):")
            self.lbl_d_fin.setText("Profondità Assiale Z (mm):")
        elif is_id:                                                                             # Etichette per Gola Interna ID
            self.lbl_z_start.setText("Z Spalla Destra (mm):")
            self.lbl_d_ini.setText("Ø Foro Imbocco (mm):")
            self.lbl_d_fin.setText("Ø Fondo Gola Int. (mm):")
        else:                                                                                   # Etichette per Gola Esterna OD
            self.lbl_z_start.setText("Z Spalla Destra (mm):")
            self.lbl_d_ini.setText("Ø Esterno Imbocco (mm):")
            self.lbl_d_fin.setText("Ø Fondo Gola Est. (mm):")

        usa_p = self.chk_peck.isChecked()                                                       # Stato checkbox Peck
        self.peck_q_spin.setEnabled(usa_p)                                                      # Abilita passo Q
        self.peck_ret_spin.setEnabled(usa_p)                                                    # Abilita ritrazione Peck

        usa_f = self.chk_fin_walls.isChecked()                                                  # Stato checkbox finitura fianchi
        self.sovra_fondo_spin.setEnabled(usa_f)                                                 # Abilita sovrametallo fondo
        self.sovra_fianco_spin.setEnabled(usa_f)                                                # Abilita sovrametallo fianchi
        self.f_fin_spin.setEnabled(usa_f)                                                       # Abilita avanzamento finitura
        self.trigger_update()                                                                   # Ricalcola l'anteprima 3D

    def trigger_update(self, *args):                                                            # Aggiorna in tempo reale il tracciato 3D della gola
        if self.is_updating: return                                                             # Se bloccato esce
        self.is_updating = True                                                                 # Attiva semaforo
        try:                                                                                    # Blocco di calcolo
            doc = FreeCAD.ActiveDocument                                                        # Documento attivo
            if not doc or not self.preview_rapidi or not self.preview_lavoro: return            # Verifica validità
            wcs = LatheRoughing.get_wcs_origin(doc)                                             # Origine WCS
            sic_x, sic_z = LatheRoughing.get_setup_safe_clearances(doc)                         # Sicurezze Setup
            stock_info = LatheRoughing.get_stock_info(doc)                                      # Dati Grezzo e limite griffe

            _, c_rap, c_lav, moves, z_min_eff = calcola_percorso_gola(                          # Calcola il percorso della gola
                wcs, self.cycle_combo.currentText(), stock_info,
                self.z_start_spin.value(), self.w_groove_spin.value(),
                self.d_ini_spin.value(), self.d_fin_spin.value(),
                self.lama_w_spin.value(), self.chk_peck.isChecked(),
                self.peck_q_spin.value(), self.peck_ret_spin.value(), self.stepover_spin.value(),
                self.chk_fin_walls.isChecked(), self.sovra_fondo_spin.value(),
                self.sovra_fianco_spin.value(), self.chamfer_spin.value(),
                sic_x, sic_z, self.f_plunge_spin.value(), self.f_fin_spin.value()
            )                                                                                   # Fine calcolo

            self.preview_rapidi.Shape = c_rap if c_rap else Part.Shape()                        # Aggiorna i rapidi rossi
            self.preview_lavoro.Shape = c_lav if c_lav else Part.Shape()                        # Aggiorna i tagli giallo ambra

            n_tagli = sum(1 for m in moves if m["cmd"] == "G1")                                 # Conta i movimenti di taglio G01
            z_richiesta = self.z_start_spin.value() - self.w_groove_spin.value()                # Quota Z sinistra richiesta
            if z_richiesta < stock_info["z_lim_chuck"]:                                         # Se la gola invade la zona di sicurezza griffe
                self.lbl_status.setStyleSheet("color: #FF5555; font-weight: bold;")
                self.lbl_status.setText(f"Attenzione: Gola limitata a Z={z_min_eff:.2f} mm per sicurezza Griffe!")
            else:                                                                               # Tutto OK
                self.lbl_status.setStyleSheet("color: #FFBB00; font-weight: bold;")
                self.lbl_status.setText(f"Gola OK: Largh.={self.w_groove_spin.value():.1f} mm | {n_tagli} movimenti G01.")

            doc.recompute()                                                                     # Rinfresca la scena 3D
        finally:                                                                                # Rilascia semaforo
            self.is_updating = False                                                            # Fine aggiornamento

    def carica_dati_da_oggetto(self, obj):                                                      # Popola la UI quando si riapre un'operazione di Gola con doppio click
        obj.Proxy.ensure_properties(obj)                                                        # Verifica proprietà
        self.name_input.setText(str(getattr(obj, "OperationName", obj.Label)))                  # Nome
        if str(obj.TipoCiclo) in TIPI_CICLO_GOLA:                                               # Tipo gola
            self.cycle_combo.setCurrentText(str(obj.TipoCiclo))
        idx_t = self.tool_combo.findData(str(getattr(obj, "UtensileAssegnato", "")))            # Utensile
        if idx_t >= 0: self.tool_combo.setCurrentIndex(idx_t)
        self.lama_w_spin.setValue(float(getattr(obj, "LarghezzaLama", 3.0)))                    # Larghezza lama
        self.z_start_spin.setValue(float(getattr(obj, "Z_InizioGola", -20.0)))                  # Z Spalla Destra
        self.w_groove_spin.setValue(float(getattr(obj, "LarghezzaGola", 6.0)))                  # Larghezza gola
        self.d_ini_spin.setValue(float(getattr(obj, "DiametroInizioGola", 50.0)))               # Diametro imbocco
        self.d_fin_spin.setValue(float(getattr(obj, "DiametroFondoGola", 40.0)))                # Diametro fondo
        self.chamfer_spin.setValue(float(getattr(obj, "SmussoBordi", 0.3)))                     # Smusso bordi
        self.chk_peck.setChecked(bool(getattr(obj, "UsaScaricoTruciolo", True)))                # Usa Peck
        self.peck_q_spin.setValue(float(getattr(obj, "PassoPeck", 1.5)))                        # Passo Peck Q
        self.peck_ret_spin.setValue(float(getattr(obj, "RitrazionePeck", 0.3)))                 # Ritrazione Peck
        self.stepover_spin.setValue(float(getattr(obj, "PassoLateralePerc", 75.0)))             # Sormonto %
        self.chk_fin_walls.setChecked(bool(getattr(obj, "FinituraFianchi", True)))              # Finitura fianchi
        self.sovra_fondo_spin.setValue(float(getattr(obj, "SovrametalloFondo", 0.15)))          # Sovrametallo fondo
        self.sovra_fianco_spin.setValue(float(getattr(obj, "SovrametalloFianco", 0.15)))        # Sovrametallo fianco
        self.vc_spin.setValue(float(getattr(obj, "VelocitaTaglio", 120.0)))                     # Velocità Vc
        self.f_plunge_spin.setValue(float(getattr(obj, "AvanzamentoTuffo", 0.08)))              # Avanzamento tuffo
        self.f_fin_spin.setValue(float(getattr(obj, "AvanzamentoFinitura", 0.10)))              # Avanzamento finitura

    def pulisci_anteprima_percorso(self, doc):                                                  # Rimuove in modo sicuro gli oggetti temporanei di anteprima
        if not doc: return                                                                      # Controllo sicurezza
        for attr in ["preview_rapidi", "preview_lavoro"]:                                       # Rimuove riferimenti diretti
            if hasattr(self, attr) and getattr(self, attr):
                try:
                    obj = getattr(self, attr)
                    if doc.getObject(obj.Name): doc.removeObject(obj.Name)
                except Exception: pass
                setattr(self, attr, None)
        for obj in list(doc.Objects):                                                           # Rimuove eventuali residui
            if obj.Name.startswith("TMP_Groove_"):
                try: doc.removeObject(obj.Name)
                except Exception: pass

    def getStandardButtons(self):                                                               # Pulsanti OK e Cancel
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel                # Restituisce OK | Cancel

    def accept(self):                                                                           # Conferma e salva l'operazione di Gola in Operazioni_CAM
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc: return False                                                                # Controllo sicurezza

        ops_group = doc.getObject("Operazioni_CAM")                                             # Cerca il gruppo Operazioni_CAM
        if not ops_group:                                                                       # Se non esiste lo crea
            ops_group = doc.addObject("App::DocumentObjectGroup", "Operazioni_CAM")
            ops_group.Label = "Operazioni CAM (Cicli Tornio)"

        nome_op = self.name_input.text().strip() or "Gola Esterna 1"                            # Nome operazione
        if self.edit_obj and doc.getObject(self.edit_obj.Name):                                 # Se siamo in modifica
            op_obj = self.edit_obj                                                              # Riutilizza l'oggetto esistente
        else:                                                                                   # Altrimenti crea il nuovo oggetto parametrico
            op_obj = doc.addObject("Part::FeaturePython", "Op_Gola")                            # Crea Part::FeaturePython
            LatheGroovingObject(op_obj)                                                         # Inizializza Proxy
            ViewProviderLatheGrooving(op_obj.ViewObject)                                        # Inizializza ViewProvider
            ops_group.addObject(op_obj)                                                         # Aggiunge al gruppo Operazioni_CAM

        t_name = self.tool_combo.itemData(self.tool_combo.currentIndex()) if self.tool_combo.count() > 0 else ""

        op_obj.Proxy._is_executing = True                                                       # Sospende execute durante la scrittura proprietà
        try:                                                                                    # Salva tutti i parametri
            op_obj.Proxy.ensure_properties(op_obj)
            op_obj.OperationName = nome_op
            op_obj.Label = nome_op
            op_obj.TipoCiclo = self.cycle_combo.currentText()
            op_obj.UtensileAssegnato = str(t_name or "")
            op_obj.LarghezzaLama = self.lama_w_spin.value()
            op_obj.Z_InizioGola = self.z_start_spin.value()
            op_obj.LarghezzaGola = self.w_groove_spin.value()
            op_obj.DiametroInizioGola = self.d_ini_spin.value()
            op_obj.DiametroFondoGola = self.d_fin_spin.value()
            op_obj.SmussoBordi = self.chamfer_spin.value()
            op_obj.UsaScaricoTruciolo = self.chk_peck.isChecked()
            op_obj.PassoPeck = self.peck_q_spin.value()
            op_obj.RitrazionePeck = self.peck_ret_spin.value()
            op_obj.PassoLateralePerc = self.stepover_spin.value()
            op_obj.FinituraFianchi = self.chk_fin_walls.isChecked()
            op_obj.SovrametalloFondo = self.sovra_fondo_spin.value()
            op_obj.SovrametalloFianco = self.sovra_fianco_spin.value()
            op_obj.VelocitaTaglio = self.vc_spin.value()
            op_obj.AvanzamentoTuffo = self.f_plunge_spin.value()
            op_obj.AvanzamentoFinitura = self.f_fin_spin.value()
        finally:                                                                                # Sblocca Proxy
            op_obj.Proxy._is_executing = False

        op_obj.Proxy.execute(op_obj)                                                            # Calcola e disegna il percorso finale
        if hasattr(op_obj, "ViewObject") and op_obj.ViewObject:
            op_obj.ViewObject.Visibility = True                                                 # Mostra il percorso giallo ambra nel 3D

        self.pulisci_anteprima_percorso(doc)                                                    # Elimina le anteprime temporanee
        doc.recompute()                                                                         # Aggiorna il documento
        if FreeCADGui.ActiveDocument: FreeCADGui.ActiveDocument.resetEdit()                     # Esce da Edit
        FreeCADGui.Control.closeDialog()                                                        # Chiude il pannello
        return True                                                                             # Conferma

    def reject(self):                                                                           # Annulla e ripristina lo stato precedente
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if doc:
            self.pulisci_anteprima_percorso(doc)                                                # Pulisce anteprime
            if self.edit_obj and doc.getObject(self.edit_obj.Name):                             # Se in modifica
                if hasattr(self.edit_obj, "ViewObject") and self.edit_obj.ViewObject:
                    self.edit_obj.ViewObject.Visibility = True                                  # Riaccende l'originale
            doc.recompute()                                                                     # Ricalcola documento
        if FreeCADGui.ActiveDocument: FreeCADGui.ActiveDocument.resetEdit()                     # Esce da Edit
        FreeCADGui.Control.closeDialog()                                                        # Chiude il pannello
        return True                                                                             # Conferma