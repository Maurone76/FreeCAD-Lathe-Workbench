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


TIPI_CICLO_FILETTO = [                                                                          # Modalità operative supportate dal ciclo di Filettatura
    "Filettatura Esterna (OD)",                                                                 # Filettatura su diametro esterno (affonda verso -X)
    "Filettatura Interna (ID)"                                                                  # Filettatura dentro un foro (affonda verso +X)
]                                                                                               # Fine elenco tipi filettatura

TIPI_INGRESSO_DENTE = [                                                                         # Modalità di penetrazione dell'inserto nel filetto
    "Sul Fianco Modificato (29.5°)",                                                            # Penetrazione inclinata lungo il fianco (scarico truciolo ottimale)
    "Radiale Dritto (0°)",                                                                      # Penetrazione puramente radiale lungo X
    "Alternato sui Fianchi (Zig-Zag)"                                                           # Alterna fianco destro e sinistro per filetti a passo grosso
]                                                                                               # Fine elenco tipi ingresso

TABELLA_FILETTI_STD = {                                                                         # Tabella rapida filettature standard (Diametro Esterno, Passo mm, Angolo°)
    "Personalizzata (Manuale)": None,                                                           # Lascia liberi i campi attuali
    "M6 x 1.0 (ISO)": (6.0, 1.0, 60.0),                                                         # Metrico M6 passo grosso
    "M8 x 1.25 (ISO)": (8.0, 1.25, 60.0),                                                       # Metrico M8 passo grosso
    "M10 x 1.5 (ISO)": (10.0, 1.5, 60.0),                                                       # Metrico M10 passo grosso
    "M12 x 1.75 (ISO)": (12.0, 1.75, 60.0),                                                     # Metrico M12 passo grosso
    "M14 x 2.0 (ISO)": (14.0, 2.0, 60.0),                                                       # Metrico M14 passo grosso
    "M16 x 2.0 (ISO)": (16.0, 2.0, 60.0),                                                       # Metrico M16 passo grosso
    "M20 x 2.5 (ISO)": (20.0, 2.5, 60.0),                                                       # Metrico M20 passo grosso
    "M24 x 3.0 (ISO)": (24.0, 3.0, 60.0),                                                       # Metrico M24 passo grosso
    "M30 x 3.5 (ISO)": (30.0, 3.5, 60.0),                                                       # Metrico M30 passo grosso
    "G 1/4\" BSP (19 TPI - 55°)": (13.157, 1.337, 55.0),                                        # GAS Cilindrico 1/4 pollice
    "G 3/8\" BSP (19 TPI - 55°)": (16.662, 1.337, 55.0),                                        # GAS Cilindrico 3/8 pollice
    "G 1/2\" BSP (14 TPI - 55°)": (20.955, 1.814, 55.0),                                        # GAS Cilindrico 1/2 pollice
    "G 3/4\" BSP (14 TPI - 55°)": (26.441, 1.814, 55.0),                                        # GAS Cilindrico 3/4 pollice
    "G 1\" BSP (11 TPI - 55°)": (33.249, 2.309, 55.0),                                          # GAS Cilindrico 1 pollice
    "Tr 20 x 4 (Trapezoidale 30°)": (20.0, 4.0, 30.0)                                           # Trapezoidale Tr 20x4
}                                                                                               # Fine tabella preimpostazioni


def calcola_altezza_filetto_iso(passo, angolo_profilo, is_esterno=True):                        # Calcola l'altezza radiale del filetto H in base a passo e profilo
    p = max(float(passo), 0.1)                                                                  # Passo del filetto in mm
    ang = float(angolo_profilo)                                                                 # Angolo del profilo (60°, 55° o 30°)
    if abs(ang - 55.0) < 2.0:                                                                   # Filettatura Whitworth / GAS 55°
        return 0.6403 * p                                                                       # Altezza teorica filetto 55° (uguale per esterno e interno)
    if abs(ang - 30.0) < 2.0:                                                                   # Filettatura Trapezoidale 30°
        return (0.5 * p) + 0.25                                                                 # Altezza filetto trapezoidale con gioco di fondo
    return (0.6134 * p) if is_esterno else (0.5413 * p)                                         # Altezza ISO 60° (0.6134*P per albero esterno, 0.5413*P per madrevite)


def calcola_profondita_passate_costanti(h_totale, num_passate_taglio, num_passate_molla):       # Calcola la lista delle profondità cumulative con legge quadratica sqrt(k)
    h_tot = max(float(h_totale), 0.05)                                                          # Altezza radiale totale da asportare
    n_cut = max(int(num_passate_taglio), 1)                                                     # Numero di passate di asportazione
    n_spr = max(int(num_passate_molla), 0)                                                      # Numero di passate di pulizia a vuoto (spring passes)
    profondita = []                                                                             # Lista delle profondità cumulative ad ogni passata
    for k in range(1, n_cut + 1):                                                               # Cicla dalla passata 1 alla passata n_cut
        d_k = h_tot * math.sqrt(float(k) / float(n_cut))                                        # Legge a sezione di truciolo costante: d_k = H * sqrt(k / N)
        profondita.append(d_k)                                                                  # Aggiunge la profondità cumulativa
    for _ in range(n_spr):                                                                      # Aggiunge le passate di finitura/molleggio alla profondità finale
        profondita.append(h_tot)                                                                # Ripete la passata sul fondo nominale del filetto
    return profondita                                                                           # Restituisce la lista completa delle passate


def calcola_percorso_filettatura(                                                               # Genera la lista movimenti (G0/G32) e le Shapes 3D della filettatura
    wcs, tipo_ciclo, stock_info,                                                                # Riferimenti base
    z_start, z_end, d_nominale, passo, h_filetto, conicita_raggio,                              # Quote geometriche del filetto
    tipo_ingresso, angolo_profilo, n_passate, n_molla, smusso_uscita,                           # Strategia di penetrazione, passate e uscita
    sic_x, sic_z                                                                                # Distanze di sicurezza
):                                                                                              # Inizio motore di calcolo percorso filettatura
    moves = []                                                                                  # Lista movimenti: {"cmd": "G0"/"G32", "x": r, "z": z, "f": passo}
    edges_rapidi = []                                                                           # Segmenti 3D per i movimenti rapidi G00 (Rosso)
    edges_lavoro = []                                                                           # Segmenti 3D per le passate sincronizzate G32 (Viola/Magenta)

    is_od = (tipo_ciclo == "Filettatura Esterna (OD)")                                          # True per filetto esterno, False per filetto interno
    r_grezzo = stock_info["r_rot"]                                                              # Raggio esterno massimo del grezzo
    z_lim_griffe = stock_info["z_lim_chuck"]                                                    # Quota Z limite collisione griffe mandrino

    p_val = max(float(passo), 0.2)                                                              # Passo di filettatura (mm/giro)
    z_ini = float(z_start)                                                                      # Quota Z di inizio effettivo del filetto (+ eventuale extra-corsa)
    z_fin = max(float(z_end), z_lim_griffe)                                                     # Blocca automaticamente Z Fine prima delle griffe autocentrante!
    r_nom = max(float(d_nominale) / 2.0, 1.0)                                                   # Raggio nominale di partenza del filetto (cresta per OD, pre-foro per ID)
    h_tot = max(float(h_filetto), 0.05)                                                         # Altezza radiale totale del filetto (mm)
    taper_dr = float(conicita_raggio)                                                           # Variazione radiale tra inizio e fine (0 = cilindrico, !=0 = conico)
    pull_out = max(float(smusso_uscita), 0.0)                                                   # Lunghezza smusso di disimpegno finale (0 = uscita dritta in gola)

    r_sic = (max(r_nom, r_grezzo) + max(float(sic_x), 1.5)) if is_od else max(r_nom - max(float(sic_x), 1.5), 0.5)
    safe_r_global = max(r_grezzo, r_nom) + max(float(sic_x), 2.0)                               # Raggio di sicurezza esterno generale
    safe_z_global = max(stock_info["z_front"], z_ini) + max(float(sic_z), 2.0)                  # Quota Z di sicurezza frontale generale

    curr_pt = [safe_r_global, safe_z_global]                                                    # Posizione iniziale utensile
    moves.append({                                                                              # Punto iniziale con metadati per il ciclo G76 del Post-Processor
        "cmd": "G0", "x": curr_pt[0], "z": curr_pt[1], "f": 0.0,
        "thread_meta": {                                                                        # Metadati completi per generazione G76 / CYCLE97
            "is_od": is_od, "r_nom": r_nom, "h_tot": h_tot, "pitch": p_val,
            "z_start": z_ini, "z_end": z_fin, "taper": taper_dr,
            "angle": float(angolo_profilo), "n_cuts": int(n_passate), "n_spring": int(n_molla)
        }
    })                                                                                          # Fine punto iniziale

    def add_segment(cmd, next_r, next_z):                                                       # Registra un segmento nella lista e genera la linea 3D
        p1 = FreeCAD.Vector(wcs.x + curr_pt[0], wcs.y, wcs.z + curr_pt[1])                      # Punto 3D partenza sul piano XZ
        p2 = FreeCAD.Vector(wcs.x + next_r, wcs.y, wcs.z + next_z)                              # Punto 3D arrivo sul piano XZ
        if (p2 - p1).Length > 1e-4:                                                             # Se lo spostamento è reale
            edge = Part.makeLine(p1, p2)                                                        # Crea il segmento 3D
            if cmd == "G0":                                                                     # Movimento rapido di ritorno/posizionamento
                edges_rapidi.append(edge)                                                       # Aggiunge ai rapidi (Rosso)
            else:                                                                               # Movimento sincronizzato di filettatura (G32/G33)
                edges_lavoro.append(edge)                                                       # Aggiunge al taglio filetto (Viola/Magenta)
            moves.append({                                                                      # Registra il movimento
                "cmd": cmd,                                                                     # "G0" o "G32"
                "x": float(next_r),                                                             # Raggio X rispetto al WCS
                "z": float(next_z),                                                             # Quota Z rispetto al WCS
                "f": float(p_val if cmd != "G0" else 0.0)                                       # L'avanzamento in filettatura è esattamente uguale al Passo!
            })                                                                                  # Fine record
            curr_pt[0] = float(next_r)                                                          # Aggiorna X corrente
            curr_pt[1] = float(next_z)                                                          # Aggiorna Z corrente

    mezzo_ang = math.radians(max(float(angolo_profilo) / 2.0 - 0.5, 0.0))                       # Angolo di fianco ridotto di 0.5° (es. 29.5° su ISO 60°) per non strisciare
    lista_prof = calcola_profondita_passate_costanti(h_tot, n_passate, n_molla)                 # Ottiene tutte le profondità di passata d_k

    add_segment("G0", r_sic, z_ini)                                                             # Porta l'utensile al punto di partenza sincronizzato (r_sic, z_ini)

    for idx, d_k in enumerate(lista_prof):                                                      # Esegue ciascuna passata di filettatura
        if "Fianco" in tipo_ingresso:                                                           # Penetrazione inclinata lungo il fianco destro (29.5°)
            dz_shift = -d_k * math.tan(mezzo_ang)                                               # Spostamento assiale Z proporzionale alla profondità d_k
        elif "Alternato" in tipo_ingresso:                                                      # Penetrazione alternata sui due fianchi (Zig-Zag)
            segno_z = -1.0 if (idx % 2 == 0) else 1.0                                           # Alterna fianco destro (-) e fianco sinistro (+)
            dz_shift = segno_z * d_k * math.tan(mezzo_ang)                                      # Spostamento Z alternato
        else:                                                                                   # Penetrazione radiale dritta (0°)
            dz_shift = 0.0                                                                      # Nessuno spostamento assiale Z

        r_pass_ini = (r_nom - d_k) if is_od else (r_nom + d_k)                                  # Raggio di attacco della passata k-esima a Z Inizio
        r_pass_fin = r_pass_ini + taper_dr                                                      # Raggio a fine filetto (include eventuale conicità)
        z_attacco = z_ini + dz_shift                                                            # Quota Z di attacco sincronizzato per la passata k-esima

        add_segment("G0", r_sic, z_attacco)                                                     # Si allinea in rapido alla Z di attacco della passata
        add_segment("G0", r_pass_ini, z_attacco)                                                # Scende in rapido al raggio della passata k-esima

        if pull_out > 0.05 and abs(z_ini - z_fin) > pull_out * 1.5:                             # Se è richiesto lo smusso d'uscita a 45° (senza gola di scarico)
            z_inizio_uscita = z_fin + pull_out                                                  # Quota Z dove inizia il disimpegno inclinato
            fraz = (z_ini - z_inizio_uscita) / (z_ini - z_fin) if abs(z_ini - z_fin) > 1e-4 else 1.0
            r_pre_uscita = r_pass_ini + fraz * taper_dr                                         # Raggio prima dello smusso d'uscita
            add_segment("G32", r_pre_uscita, z_inizio_uscita)                                   # Taglio filetto sincronizzato G32 fino all'inizio dello smusso
            add_segment("G32", r_sic, z_fin)                                                    # Uscita sincronizzata inclinata fuori dal filetto fino a z_fin
        else:                                                                                   # Uscita standard dritta dentro la gola di scarico
            add_segment("G32", r_pass_fin, z_fin)                                               # Taglio filetto sincronizzato G32 fino a z_fin
            add_segment("G0", r_sic, z_fin)                                                     # Estrazione radiale rapida G00 fuori dal filetto

        add_segment("G0", r_sic, z_ini)                                                         # Ritorno rapido lungo +Z al punto iniziale per la passata successiva

    add_segment("G0", safe_r_global, safe_z_global)                                             # Disimpegno finale in posizione di sicurezza

    shapes_all = []                                                                             # Lista globale dei segmenti 3D
    if edges_rapidi: shapes_all.extend(edges_rapidi)                                            # Unisce i rapidi
    if edges_lavoro: shapes_all.extend(edges_lavoro)                                            # Unisce le passate di filettatura

    comp = Part.makeCompound(shapes_all) if shapes_all else Part.makeSphere(0.5, wcs)           # Compound finale dell'operazione
    comp_rapidi = Part.makeCompound(edges_rapidi) if edges_rapidi else None                     # Compound rapidi per anteprima rossa
    comp_lavoro = Part.makeCompound(edges_lavoro) if edges_lavoro else None                     # Compound lavoro per anteprima viola/magenta
    return comp, comp_rapidi, comp_lavoro, moves, z_fin, lista_prof[0] if lista_prof else 0.0   # Restituisce geometrie, punti, Z fine e profondità prima passata


class LatheThreadingObject:                                                                     # Classe Proxy per l'operazione parametrica di Filettatura
    def __init__(self, obj):                                                                    # Costruttore del Proxy
        self._is_executing = False                                                              # Semaforo anti-ricorsione
        self.ensure_properties(obj)                                                             # Garantisce la creazione di tutte le proprietà
        obj.Proxy = self                                                                        # Collega il Proxy all'oggetto FreeCAD

    def ensure_properties(self, obj):                                                           # Aggiunge le proprietà native se mancanti
        if not hasattr(obj, "OperationName"):                                                   # Nome operazione
            obj.addProperty("App::PropertyString", "OperationName", "Operazione", "Nome operazione").OperationName = "Filettatura M20x2.5"
        if not hasattr(obj, "TipoCiclo"):                                                       # Esterna OD o Interna ID
            obj.addProperty("App::PropertyEnumeration", "TipoCiclo", "Operazione", "Tipo filettatura")
            obj.TipoCiclo = TIPI_CICLO_FILETTO                                                  # Assegna OD / ID
        if not hasattr(obj, "UtensileAssegnato"):                                               # Utensile selezionato dal Magazzino
            obj.addProperty("App::PropertyString", "UtensileAssegnato", "Operazione", "Utensile filettatore utilizzato").UtensileAssegnato = ""
        if not hasattr(obj, "StandardPreimpostato"):                                            # Voce della tabella standard scelta
            obj.addProperty("App::PropertyString", "StandardPreimpostato", "Geometria Filetto", "Standard filetto selezionato").StandardPreimpostato = "M20 x 2.5 (ISO)"
        if not hasattr(obj, "DiametroNominale"):                                                # Diametro nominale di partenza del filetto (mm)
            obj.addProperty("App::PropertyFloat", "DiametroNominale", "Geometria Filetto", "Diametro nominale filetto (mm)").DiametroNominale = 20.0
        if not hasattr(obj, "PassoFiletto"):                                                    # Passo P della filettatura (mm/giro)
            obj.addProperty("App::PropertyFloat", "PassoFiletto", "Geometria Filetto", "Passo del filetto P (mm)").PassoFiletto = 2.5
        if not hasattr(obj, "AngoloProfilo"):                                                   # Angolo profilo dente (60°, 55° o 30°)
            obj.addProperty("App::PropertyFloat", "AngoloProfilo", "Geometria Filetto", "Angolo profilo filetto (gradi)").AngoloProfilo = 60.0
        if not hasattr(obj, "AltezzaFiletto"):                                                  # Altezza radiale totale del filetto H (mm)
            obj.addProperty("App::PropertyFloat", "AltezzaFiletto", "Geometria Filetto", "Altezza radiale filetto H (mm)").AltezzaFiletto = 1.534
        if not hasattr(obj, "Z_Inizio"):                                                        # Quota Z di partenza (inclusa extra-corsa di sincronizzazione)
            obj.addProperty("App::PropertyFloat", "Z_Inizio", "Geometria Filetto", "Quota Z iniziale con invito (mm)").Z_Inizio = 4.0
        if not hasattr(obj, "Z_Fine"):                                                          # Quota Z di fine filetto (mm)
            obj.addProperty("App::PropertyFloat", "Z_Fine", "Geometria Filetto", "Quota Z finale filetto (mm)").Z_Fine = -30.0
        if not hasattr(obj, "ConicitaRaggio"):                                                  # Differenza radiale X tra fine e inizio per filetti conici (mm)
            obj.addProperty("App::PropertyFloat", "ConicitaRaggio", "Geometria Filetto", "Conicità sul raggio dR (mm, 0=cilindrico)").ConicitaRaggio = 0.0
        if not hasattr(obj, "TipoIngresso"):                                                    # Strategia di penetrazione dente (Fianco 29.5°, Radiale, Alternato)
            obj.addProperty("App::PropertyEnumeration", "TipoIngresso", "Parametri Taglio", "Strategia di penetrazione inserto")
            obj.TipoIngresso = TIPI_INGRESSO_DENTE                                              # Assegna le 3 strategie
        if not hasattr(obj, "NumeroPassateTaglio"):                                             # Numero di passate progressive di taglio
            obj.addProperty("App::PropertyInteger", "NumeroPassateTaglio", "Parametri Taglio", "Numero passate di taglio").NumeroPassateTaglio = 8
        if not hasattr(obj, "PassateFinituraMolla"):                                            # Numero di passate finali a vuoto sul fondo
            obj.addProperty("App::PropertyInteger", "PassateFinituraMolla", "Parametri Taglio", "Passate di pulizia a vuoto (Spring Passes)").PassateFinituraMolla = 2
        if not hasattr(obj, "SmussoUscita"):                                                    # Lunghezza uscita inclinata a fine filetto (mm)
            obj.addProperty("App::PropertyFloat", "SmussoUscita", "Parametri Taglio", "Lunghezza smusso uscita finale (mm, 0=dritto)").SmussoUscita = 2.0
        if not hasattr(obj, "GiriMandrinoRPM"):                                                 # Giri fissi mandrino G97 obbligatori in filettatura!
            obj.addProperty("App::PropertyFloat", "GiriMandrinoRPM", "Parametri Taglio", "Giri mandrino fissi G97 (RPM)").GiriMandrinoRPM = 800.0
        if not hasattr(obj, "PercorsoJSON"):                                                    # Punti del percorso salvati per Simulatore e G-Code
            obj.addProperty("App::PropertyString", "PercorsoJSON", "Dati CAM", "Punti percorso per Simulatore e G-Code").PercorsoJSON = "[]"

    def onDocumentRestored(self, obj):                                                          # Chiamato alla riapertura del documento
        self._is_executing = False                                                              # Sblocca il flag
        self.ensure_properties(obj)                                                             # Verifica le proprietà

    def execute(self, obj):                                                                     # Ricalcola il percorso 3D della filettatura
        if getattr(self, "_is_executing", False):                                               # Evita loop ricorsivi
            return                                                                              # Esce subito
        self._is_executing = True                                                               # Attiva il semaforo
        try:                                                                                    # Blocco protetto di calcolo
            self.ensure_properties(obj)                                                         # Verifica attributi
            doc = obj.Document                                                                  # Documento corrente
            wcs = LatheRoughing.get_wcs_origin(doc)                                             # Origine WCS
            sic_x, sic_z = LatheRoughing.get_setup_safe_clearances(doc)                         # Sicurezze Setup
            stock_info = LatheRoughing.get_stock_info(doc)                                      # Dati Grezzo e limite griffe

            comp, _, _, moves, _, _ = calcola_percorso_filettatura(                             # Calcola il percorso multipassata
                wcs, str(obj.TipoCiclo), stock_info,
                obj.Z_Inizio, obj.Z_Fine, obj.DiametroNominale,
                obj.PassoFiletto, obj.AltezzaFiletto, obj.ConicitaRaggio,
                str(obj.TipoIngresso), obj.AngoloProfilo,
                obj.NumeroPassateTaglio, obj.PassateFinituraMolla, obj.SmussoUscita,
                sic_x, sic_z
            )                                                                                   # Fine calcolo
            obj.PercorsoJSON = json.dumps(moves)                                                # Salva il percorso per il Simulatore e il Post-Processor
            obj.Shape = comp                                                                    # Assegna la Shape 3D
            if hasattr(obj, "ViewObject") and obj.ViewObject:                                   # Colora il tracciato in Viola/Magenta brillante
                obj.ViewObject.LineColor = (0.85, 0.25, 0.95)                                   # Viola/Magenta per distinguere subito la filettatura
                obj.ViewObject.LineWidth = 2.5                                                  # Spessore linea
        except Exception as e:                                                                  # Cattura errori imprevisti
            FreeCAD.Console.PrintError(f"Errore calcolo Filettatura: {e}\n")                    # Stampa in console
        finally:                                                                                # Rilascia il semaforo
            self._is_executing = False                                                          # Fine esecuzione

    def onChanged(self, obj, prop):                                                             # Intercetta modifiche live dalle Proprietà di FreeCAD
        if getattr(self, "_is_executing", False):                                               # Evita ricorsioni
            return                                                                              # Esce
        props_calcolo = [                                                                       # Proprietà che rigenerano il percorso
            "TipoCiclo", "DiametroNominale", "PassoFiletto", "AngoloProfilo",                   # Quote base filetto
            "AltezzaFiletto", "Z_Inizio", "Z_Fine", "ConicitaRaggio",                           # Limiti e conicità
            "TipoIngresso", "NumeroPassateTaglio", "PassateFinituraMolla", "SmussoUscita"       # Strategia passate
        ]                                                                                       # Fine lista
        if prop in props_calcolo:                                                               # Se cambia un parametro della filettatura
            self.execute(obj)                                                                   # Aggiorna il percorso 3D
        elif prop == "OperationName":                                                           # Se cambia il nome operazione
            if hasattr(obj, "OperationName") and obj.OperationName:                             # Allinea l'etichetta nell'albero
                obj.Label = obj.OperationName                                                   # Imposta Label

    def __getstate__(self):                                                                     # Serializzazione
        return None                                                                             # Nessun dato speciale

    def __setstate__(self, state):                                                              # Deserializzazione
        self._is_executing = False                                                              # Ripristina flag
        return None                                                                             # Fine


class ViewProviderLatheThreading:                                                               # ViewProvider per icona e doppio click sull'operazione di Filettatura
    def __init__(self, vobj):                                                                   # Costruttore ViewProvider
        vobj.Proxy = self                                                                       # Collega il Proxy

    def getIcon(self):                                                                          # Icona nell'albero delle operazioni
        return LatheResources.get_icon_path("lathe_threading.svg", "Part_Helix")                # Icona SVG dedicata Filettatura

    def attach(self, vobj):                                                                     # Collega gli oggetti alla vista
        self.ViewObject = vobj                                                                  # Riferimento ViewObject
        self.Object = vobj.Object                                                               # Riferimento Object

    def updateData(self, vobj, prop):                                                           # Aggiornamento dati
        return                                                                                  # Gestito da execute

    def onDelete(self, vobj, subelements):                                                      # Autorizza cancellazione
        return True                                                                             # Sempre consentito

    def doubleClicked(self, vobj):                                                              # Doppio click sull'operazione nell'albero
        if not FreeCADGui.Control.activeDialog():                                               # Se non c'è già un pannello aperto
            panel = LatheThreadingPanel(edit_obj=vobj.Object)                                   # Apre il pannello caricando l'operazione
            FreeCADGui.Control.showDialog(panel)                                                # Mostra nella scheda Azioni
        return True                                                                             # Evento gestito

    def setEdit(self, vobj, mode):                                                              # Modalità Edit standard
        if mode == 0:                                                                           # Modifica base
            if not FreeCADGui.Control.activeDialog():                                           # Evita doppia apertura
                panel = LatheThreadingPanel(edit_obj=vobj.Object)                               # Crea il pannello
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


class LatheThreadingPanel:                                                                      # Pannello Task per programmare il ciclo di Filettatura
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

        self.grp_gen = QtWidgets.QGroupBox("Operazione, Utensile e Tabella Standard")           # Gruppo dati generali e tabella ISO/GAS
        self.lyt_gen = QtWidgets.QFormLayout(self.grp_gen)                                      # Form layout

        self.name_input = QtWidgets.QLineEdit("Filettatura M20x2.5")                            # Nome operazione
        self.cycle_combo = QtWidgets.QComboBox()                                                # Scelta Filettatura Esterna OD o Interna ID
        self.cycle_combo.addItems(TIPI_CICLO_FILETTO)                                           # Popola OD / ID
        self.cycle_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cycle_combo.setMinimumContentsLength(10)

        self.tool_combo = QtWidgets.QComboBox()                                                 # Scelta utensile dal Magazzino Utensili
        self.tool_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.tool_combo.setMinimumContentsLength(10)
        self.popola_combo_utensili(doc)                                                         # Carica gli utensili (preferendo quelli da Filettatura)

        self.std_combo = QtWidgets.QComboBox()                                                  # Menu a tendina con le filettature metriche ISO e GAS
        self.std_combo.addItems(list(TABELLA_FILETTI_STD.keys()))                               # Popola le voci della tabella
        self.std_combo.setCurrentText("M20 x 2.5 (ISO)")                                        # Preimpostazione iniziale M20x2.5
        self.std_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.std_combo.setMinimumContentsLength(10)

        self.lyt_gen.addRow("Nome:", self.name_input)                                           # Riga Nome
        self.lyt_gen.addRow("Posizione:", self.cycle_combo)                                     # Riga Esterna / Interna
        self.lyt_gen.addRow("Utensile:", self.tool_combo)                                       # Riga Utensile
        self.lyt_gen.addRow("Tabella Rapida:", self.std_combo)                                  # Riga Tabella Standard ISO/GAS
        self.layout.addWidget(self.grp_gen)                                                     # Aggiunge al layout principale

        self.tabs = QtWidgets.QTabWidget()                                                      # Schede: 1. Quote Filetto | 2. Passate & Infeed

        self.tab_geo = QtWidgets.QWidget()                                                      # SCHEDA 1: Quote Geometriche della Filettatura
        self.lyt_geo = QtWidgets.QVBoxLayout(self.tab_geo)                                      # Layout verticale Scheda 1

        self.grp_geo = QtWidgets.QGroupBox("Dimensioni e Limiti Assiali Filetto")               # Gruppo quote filetto
        self.lyt_g_form = QtWidgets.QFormLayout(self.grp_geo)                                   # Form layout

        self.btn_pick_cyl = QtWidgets.QPushButton("Cattura Cilindro da Faccia 3D")              # Rileva Ø Nominale, Z Inizio e Z Fine cliccando il cilindro nel 3D
        self.btn_pick_cyl.clicked.connect(self.cattura_cilindro_da_faccia_3d)                   # Collega la cattura 3D

        self.d_nom_spin = QtWidgets.QDoubleSpinBox(); self.d_nom_spin.setRange(1.0, 2000.0); self.d_nom_spin.setDecimals(3); self.d_nom_spin.setValue(20.0)
        self.pitch_spin = QtWidgets.QDoubleSpinBox(); self.pitch_spin.setRange(0.2, 50.0); self.pitch_spin.setDecimals(3); self.pitch_spin.setValue(2.5); self.pitch_spin.setSingleStep(0.25)
        self.ang_prof_spin = QtWidgets.QDoubleSpinBox(); self.ang_prof_spin.setRange(20.0, 90.0); self.ang_prof_spin.setDecimals(1); self.ang_prof_spin.setValue(60.0)
        self.h_thread_spin = QtWidgets.QDoubleSpinBox(); self.h_thread_spin.setRange(0.05, 50.0); self.h_thread_spin.setDecimals(3); self.h_thread_spin.setValue(1.534)
        self.btn_calc_h = QtWidgets.QPushButton("Ricalcola Altezza H da Passo ISO")             # Ricalcola l'altezza teorica H = 0.6134 * P
        self.btn_calc_h.clicked.connect(self.ricalcola_altezza_filetto_da_passo)                # Collega il ricalcolo di H

        self.z_start_spin = QtWidgets.QDoubleSpinBox(); self.z_start_spin.setRange(-2000, 2000); self.z_start_spin.setDecimals(2); self.z_start_spin.setValue(4.0)
        self.z_end_spin = QtWidgets.QDoubleSpinBox(); self.z_end_spin.setRange(-2000, 2000); self.z_end_spin.setDecimals(2); self.z_end_spin.setValue(-30.0)
        self.taper_spin = QtWidgets.QDoubleSpinBox(); self.taper_spin.setRange(-500.0, 500.0); self.taper_spin.setDecimals(3); self.taper_spin.setValue(0.0)

        self.lbl_status = QtWidgets.QLabel("Stato: Filetto pronto.")                            # Etichetta informativa nocciolo e prima passata
        self.lbl_status.setWordWrap(True)                                                       # Va a capo automaticamente
        self.lbl_status.setStyleSheet("color: #E066FF; font-weight: bold;")                     # Colore Viola/Magenta

        self.lyt_g_form.addRow(self.btn_pick_cyl)                                               # Riga pulsante cattura cilindro 3D
        self.lyt_g_form.addRow("Ø Nominale (mm):", self.d_nom_spin)                             # Riga Diametro Nominale
        self.lyt_g_form.addRow("Passo P (mm/giro):", self.pitch_spin)                           # Riga Passo Filetto
        self.lyt_g_form.addRow("Angolo Profilo (°):", self.ang_prof_spin)                       # Riga Angolo Profilo (60°, 55°, 30°)
        self.lyt_g_form.addRow("Altezza Filetto H (mm):", self.h_thread_spin)                   # Riga Altezza Radiale Filetto
        self.lyt_g_form.addRow(self.btn_calc_h)                                                 # Riga pulsante ricalcola H
        self.lyt_g_form.addRow("Z Inizio (+Invito) (mm):", self.z_start_spin)                   # Riga Z Inizio (con spazio sincronizzazione encoder)
        self.lyt_g_form.addRow("Z Fine Filetto (mm):", self.z_end_spin)                         # Riga Z Fine
        self.lyt_g_form.addRow("Conicità Raggio dR (mm):", self.taper_spin)                     # Riga Conicità (0 = cilindrico)
        self.lyt_g_form.addRow(self.lbl_status)                                                 # Riga stato e Ø nocciolo
        self.lyt_geo.addWidget(self.grp_geo)                                                    # Aggiunge alla Scheda 1

        self.tabs.addTab(self.tab_geo, "1. Geometria")                                          # Titolo Scheda 1

        self.tab_cut = QtWidgets.QWidget()                                                      # SCHEDA 2: Strategia di Penetrazione e Numero Passate
        self.lyt_cut = QtWidgets.QVBoxLayout(self.tab_cut)                                      # Layout verticale Scheda 2

        self.grp_cut = QtWidgets.QGroupBox("Strategia Penetrazione (G76) e Passate")            # Gruppo parametri passate
        self.lyt_c_form = QtWidgets.QFormLayout(self.grp_cut)                                   # Form layout

        self.infeed_combo = QtWidgets.QComboBox()                                               # Scelta penetrazione (Fianco 29.5°, Radiale, Alternato)
        self.infeed_combo.addItems(TIPI_INGRESSO_DENTE)                                         # Popola opzioni
        self.infeed_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.infeed_combo.setMinimumContentsLength(10)

        self.n_cuts_spin = QtWidgets.QSpinBox(); self.n_cuts_spin.setRange(1, 60); self.n_cuts_spin.setValue(8) # Numero passate progressive
        self.n_spring_spin = QtWidgets.QSpinBox(); self.n_spring_spin.setRange(0, 10); self.n_spring_spin.setValue(2) # Passate a vuoto di pulizia
        self.pullout_spin = QtWidgets.QDoubleSpinBox(); self.pullout_spin.setRange(0.0, 50.0); self.pullout_spin.setDecimals(2); self.pullout_spin.setValue(2.0); self.pullout_spin.setSingleStep(0.5)
        self.rpm_spin = QtWidgets.QDoubleSpinBox(); self.rpm_spin.setRange(10.0, 6000.0); self.rpm_spin.setDecimals(0); self.rpm_spin.setValue(800.0); self.rpm_spin.setSingleStep(50.0)

        self.lyt_c_form.addRow("Ingresso Dente:", self.infeed_combo)                            # Riga Tipo Ingresso
        self.lyt_c_form.addRow("N° Passate Taglio:", self.n_cuts_spin)                          # Riga Numero Passate
        self.lyt_c_form.addRow("Passate a Vuoto (Molla):", self.n_spring_spin)                  # Riga Spring Passes
        self.lyt_c_form.addRow("Smusso Uscita Z (mm):", self.pullout_spin)                      # Riga Smusso d'uscita finale
        self.lyt_c_form.addRow("Giri Fissi G97 (RPM):", self.rpm_spin)                          # Riga Giri Mandrino (in filettatura si usa sempre G97!)
        self.lyt_cut.addWidget(self.grp_cut)                                                    # Aggiunge alla Scheda 2
        self.lyt_cut.addStretch()                                                               # Allinea in alto

        self.tabs.addTab(self.tab_cut, "2. Passate")                                            # Titolo Scheda 2
        self.layout.addWidget(self.tabs)                                                        # Aggiunge il TabWidget al layout principale
        self.form.setLayout(self.layout)                                                        # Applica il layout

        self.preview_rapidi = doc.addObject("Part::Feature", "TMP_Thread_Rapids")               # Oggetto temporaneo per i rapidi G00 (Rosso)
        self.preview_rapidi.Label = "ANTEPRIMA RAPIDI FILETTO"                                  # Etichetta
        self.preview_rapidi.ViewObject.LineColor = (0.95, 0.20, 0.20)                           # Rosso per i rapidi
        self.preview_rapidi.ViewObject.LineWidth = 1.5                                          # Spessore linea rapidi

        self.preview_lavoro = doc.addObject("Part::Feature", "TMP_Thread_Cut")                  # Oggetto temporaneo per le passate G32 (Viola/Magenta)
        self.preview_lavoro.Label = "ANTEPRIMA TAGLIO FILETTO"                                  # Etichetta
        self.preview_lavoro.ViewObject.LineColor = (0.88, 0.25, 0.98)                           # Viola/Magenta per la filettatura
        self.preview_lavoro.ViewObject.LineWidth = 2.5                                          # Spessore linea lavoro

        if self.edit_obj:                                                                       # Se siamo in modifica di un'operazione esistente
            self.carica_dati_da_oggetto(self.edit_obj)                                          # Ripristina i dati salvati
        else:                                                                                   # Se è una nuova operazione
            self.on_tool_changed()                                                              # Eredita angolo filetto e RPM dall'utensile
            self.on_std_changed()                                                               # Applica la preimpostazione standard

        self.cycle_combo.currentIndexChanged.connect(self.ricalcola_altezza_filetto_da_passo)   # Ricalcola H se passa tra Esterna e Interna
        self.tool_combo.currentIndexChanged.connect(self.on_tool_changed)                       # Collega cambio utensile
        self.std_combo.currentIndexChanged.connect(self.on_std_changed)                         # Collega cambio voce tabella standard
        self.d_nom_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio Ø nominale
        self.pitch_spin.valueChanged.connect(self.on_pitch_changed)                             # Quando cambia il passo aggiorna automaticamente H e N° passate
        self.ang_prof_spin.valueChanged.connect(self.ricalcola_altezza_filetto_da_passo)        # Quando cambia l'angolo ricalcola H
        self.h_thread_spin.valueChanged.connect(self.trigger_update)                            # Collega cambio altezza H
        self.z_start_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio Z inizio
        self.z_end_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio Z fine
        self.taper_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio conicità
        self.infeed_combo.currentIndexChanged.connect(self.trigger_update)                      # Collega cambio tipo ingresso
        self.n_cuts_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio numero passate
        self.n_spring_spin.valueChanged.connect(self.trigger_update)                            # Collega cambio passate a vuoto
        self.pullout_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio smusso uscita

        self.is_updating = False                                                                # Sblocca gli aggiornamenti live
        self.trigger_update()                                                                   # Disegna subito l'anteprima 3D

    def popola_combo_utensili(self, doc):                                                       # Carica gli utensili del Magazzino (selezionando quello da Filettatura)
        self.tool_combo.clear()                                                                 # Svuota il combo
        idx_thr = -1                                                                            # Indice del primo utensile da Filettatura trovato
        if doc and doc.getObject("Libreria_Utensili"):                                          # Se esiste il Magazzino Utensili
            lib = doc.getObject("Libreria_Utensili")                                            # Gruppo magazzino
            for i, t in enumerate(lib.Group):                                                   # Cicla sugli utensili
                st = getattr(t, "Stazione", "T01")                                              # Sigla stazione
                tipo_u = str(getattr(t, "TipoLavorazione", ""))                                 # Categoria utensile
                self.tool_combo.addItem(f"[{st}] {t.Label}", t.Name)                            # Aggiunge voce e Name interno
                if idx_thr < 0 and "Filett" in tipo_u:                                          # Se è un utensile da Filettatura
                    idx_thr = i                                                                 # Memorizza l'indice
        if idx_thr >= 0:                                                                        # Se ha trovato un utensile filettatore
            self.tool_combo.setCurrentIndex(idx_thr)                                            # Lo preseleziona automaticamente

    def on_tool_changed(self):                                                                  # Legge AngoloFiletto e velocità dall'utensile scelto
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc or self.tool_combo.count() == 0: return                                      # Verifica validità
        t_name = self.tool_combo.itemData(self.tool_combo.currentIndex())                       # Nome utensile
        t_obj = doc.getObject(t_name) if t_name else None                                       # Oggetto utensile
        if t_obj:                                                                               # Se esiste
            prev = self.is_updating                                                             # Salva stato semaforo
            self.is_updating = True                                                             # Sospende ricalcoli
            ang_str = str(getattr(t_obj, "AngoloFiletto", "60° (Metrico ISO)"))                 # Legge il profilo filetto dell'utensile
            if "55" in ang_str: self.ang_prof_spin.setValue(55.0)                               # Imposta 55° se GAS/Whitworth
            elif "30" in ang_str: self.ang_prof_spin.setValue(30.0)                             # Imposta 30° se Trapezoidale
            else: self.ang_prof_spin.setValue(60.0)                                             # Imposta 60° se Metrico ISO
            self.is_updating = prev                                                             # Ripristina semaforo
            self.trigger_update()                                                               # Aggiorna l'anteprima

    def on_std_changed(self):                                                                   # Compila automaticamente Ø Nominale, Passo e Altezza H dalla Tabella
        voce = self.std_combo.currentText()                                                     # Voce scelta nella tendina standard
        dati = TABELLA_FILETTI_STD.get(voce)                                                    # Cerca i parametri nella tabella
        if not dati:                                                                            # Se è selezionato "Personalizzata (Manuale)"
            return                                                                              # Lascia i valori attuali
        d_std, p_std, ang_std = dati                                                            # Estrae Diametro, Passo e Angolo
        is_ext = (self.cycle_combo.currentIndex() == 0)                                         # True se esterna OD
        h_calc = calcola_altezza_filetto_iso(p_std, ang_std, is_esterno=is_ext)                 # Calcola l'altezza radiale H
        d_partenza = d_std if is_ext else round(d_std - 2.0 * h_calc, 3)                        # Per ID propone il diametro del pre-foro interno!
        n_consigliate = max(4, min(int(round(p_std * 3.5)), 24))                                # Numero di passate consigliato in base al passo

        prev = self.is_updating                                                                 # Salva stato semaforo
        self.is_updating = True                                                                 # Sospende ricalcoli multipli
        self.d_nom_spin.setValue(d_partenza)                                                    # Imposta il diametro nominale (o pre-foro per ID)
        self.pitch_spin.setValue(p_std)                                                         # Imposta il passo P
        self.ang_prof_spin.setValue(ang_std)                                                    # Imposta l'angolo del profilo
        self.h_thread_spin.setValue(round(h_calc, 3))                                           # Imposta l'altezza del filetto H
        self.n_cuts_spin.setValue(n_consigliate)                                                # Imposta il numero di passate consigliato
        if not self.edit_obj:                                                                   # Aggiorna il nome operazione se stiamo creando
            sigla = voce.split("(")[0].strip()                                                  # Estrae es. "M20 x 2.5"
            self.name_input.setText(f"Filettatura {sigla}")                                     # Imposta nome descrittivo
        self.is_updating = prev                                                                 # Ripristina semaforo
        self.trigger_update()                                                                   # Aggiorna il percorso 3D

    def on_pitch_changed(self):                                                                 # Quando l'utente cambia manualmente il Passo, aggiorna H
        self.ricalcola_altezza_filetto_da_passo()                                               # Ricalcola H e aggiorna l'anteprima

    def ricalcola_altezza_filetto_da_passo(self):                                               # Calcola H = 0.6134 * P (o 0.5413 * P per interno)
        is_ext = (self.cycle_combo.currentIndex() == 0)                                         # True se esterna OD
        h_calc = calcola_altezza_filetto_iso(self.pitch_spin.value(), self.ang_prof_spin.value(), is_esterno=is_ext)
        prev = self.is_updating                                                                 # Salva stato semaforo
        self.is_updating = True                                                                 # Sospende ricalcoli
        self.h_thread_spin.setValue(round(h_calc, 3))                                           # Aggiorna lo spinbox Altezza Filetto H
        self.is_updating = prev                                                                 # Ripristina semaforo
        self.trigger_update()                                                                   # Aggiorna il 3D

    def cattura_cilindro_da_faccia_3d(self):                                                    # Rileva Ø Nominale, Z Inizio e Z Fine cliccando la faccia cilindrica nel 3D
        sel_ex = FreeCADGui.Selection.getSelectionEx()                                          # Ottiene la selezione 3D
        if not sel_ex or not sel_ex[0].SubElementNames:                                         # Verifica che sia stata cliccata una faccia
            self.lbl_status.setText("Clicca prima sulla faccia cilindrica da filettare nel 3D!")
            return                                                                              # Esce
        sub_name = sel_ex[0].SubElementNames[0]                                                 # Nome sotto-elemento (es. Face2)
        obj_sel = sel_ex[0].Object                                                              # Oggetto 3D
        elem = obj_sel.Shape.getElement(sub_name)                                               # Elemento geometrico
        bb = elem.BoundBox                                                                      # BoundBox della faccia selezionata
        wcs = LatheRoughing.get_wcs_origin(FreeCAD.ActiveDocument)                              # Origine WCS

        r_rilevato = max(abs(bb.XMax - wcs.x), abs(bb.YMax - wcs.y))                            # Raggio dal BoundBox
        if hasattr(elem, "Surface") and hasattr(elem.Surface, "Radius"):                        # Se è una superficie cilindrica esatta
            r_rilevato = float(elem.Surface.Radius)                                             # Raggio matematico esatto

        invito_z = max(self.pitch_spin.value() * 2.0, 2.0)                                      # Extra-corsa iniziale (2 * Passo) per sincronizzare il mandrino
        z_ini_rel = (bb.ZMax - wcs.z) + invito_z                                                # Z Inizio davanti al bordo destro del cilindro
        z_fin_rel = bb.ZMin - wcs.z                                                             # Z Fine alla fine della faccia cilindrica

        self.is_updating = True                                                                 # Sospende aggiornamenti multipli
        self.std_combo.setCurrentIndex(0)                                                       # Passa a "Personalizzata (Manuale)" per non sovrascrivere il diametro
        self.d_nom_spin.setValue(round(r_rilevato * 2.0, 3))                                    # Imposta il Diametro Nominale rilevato
        self.z_start_spin.setValue(round(z_ini_rel, 2))                                         # Imposta Z Inizio (+ invito sincronizzazione)
        self.z_end_spin.setValue(round(z_fin_rel, 2))                                           # Imposta Z Fine alla fine del tratto cilindrico
        self.is_updating = False                                                                # Sblocca
        FreeCADGui.Selection.clearSelection()                                                   # Pulisce la selezione
        self.trigger_update()                                                                   # Aggiorna il percorso 3D

    def trigger_update(self, *args):                                                            # Aggiorna in tempo reale il tracciato 3D della filettatura
        if self.is_updating: return                                                             # Se bloccato esce
        self.is_updating = True                                                                 # Attiva semaforo
        try:                                                                                    # Blocco di calcolo
            doc = FreeCAD.ActiveDocument                                                        # Documento attivo
            if not doc or not self.preview_rapidi or not self.preview_lavoro: return            # Verifica validità
            wcs = LatheRoughing.get_wcs_origin(doc)                                             # Origine WCS
            sic_x, sic_z = LatheRoughing.get_setup_safe_clearances(doc)                         # Sicurezze Setup
            stock_info = LatheRoughing.get_stock_info(doc)                                      # Dati Grezzo e limite griffe

            _, c_rap, c_lav, _, z_eff, d_prima = calcola_percorso_filettatura(                  # Calcola il percorso multipassata
                wcs, self.cycle_combo.currentText(), stock_info,
                self.z_start_spin.value(), self.z_end_spin.value(),
                self.d_nom_spin.value(), self.pitch_spin.value(),
                self.h_thread_spin.value(), self.taper_spin.value(),
                self.infeed_combo.currentText(), self.ang_prof_spin.value(),
                self.n_cuts_spin.value(), self.n_spring_spin.value(), self.pullout_spin.value(),
                sic_x, sic_z
            )                                                                                   # Fine calcolo

            self.preview_rapidi.Shape = c_rap if c_rap else Part.Shape()                        # Aggiorna i rapidi rossi
            self.preview_lavoro.Shape = c_lav if c_lav else Part.Shape()                        # Aggiorna le passate viola/magenta

            is_od = (self.cycle_combo.currentIndex() == 0)                                      # True se esterna OD
            d_fin_fondo = (self.d_nom_spin.value() - 2.0 * self.h_thread_spin.value()) if is_od else (self.d_nom_spin.value() + 2.0 * self.h_thread_spin.value())
            if self.z_end_spin.value() < stock_info["z_lim_chuck"]:                             # Avviso limite griffe
                self.lbl_status.setStyleSheet("color: #FF5555; font-weight: bold;")
                self.lbl_status.setText(f"Z Fine limitata a {z_eff:.2f} mm per sicurezza Griffe!")
            else:                                                                               # Mostra diametro finale di fondo/nocciolo e 1ª passata
                self.lbl_status.setStyleSheet("color: #E066FF; font-weight: bold;")
                self.lbl_status.setText(f"Ø Fondo Finale: {d_fin_fondo:.2f} mm | 1ª Passata: {d_prima:.2f} mm (Tot: {self.n_cuts_spin.value()}+{self.n_spring_spin.value()})")

            doc.recompute()                                                                     # Rinfresca la scena 3D
        finally:                                                                                # Rilascia semaforo
            self.is_updating = False                                                            # Fine aggiornamento

    def carica_dati_da_oggetto(self, obj):                                                      # Popola la UI quando si riapre un'operazione con doppio click
        obj.Proxy.ensure_properties(obj)                                                        # Verifica proprietà
        self.name_input.setText(str(getattr(obj, "OperationName", obj.Label)))                  # Nome
        if str(obj.TipoCiclo) in TIPI_CICLO_FILETTO:                                            # Posizione OD/ID
            self.cycle_combo.setCurrentText(str(obj.TipoCiclo))
        idx_t = self.tool_combo.findData(str(getattr(obj, "UtensileAssegnato", "")))            # Utensile
        if idx_t >= 0: self.tool_combo.setCurrentIndex(idx_t)
        std_val = str(getattr(obj, "StandardPreimpostato", "Personalizzata (Manuale)"))         # Standard
        if std_val in TABELLA_FILETTI_STD: self.std_combo.setCurrentText(std_val)
        self.d_nom_spin.setValue(float(getattr(obj, "DiametroNominale", 20.0)))                 # Ø Nominale
        self.pitch_spin.setValue(float(getattr(obj, "PassoFiletto", 2.5)))                      # Passo P
        self.ang_prof_spin.setValue(float(getattr(obj, "AngoloProfilo", 60.0)))                 # Angolo profilo
        self.h_thread_spin.setValue(float(getattr(obj, "AltezzaFiletto", 1.534)))               # Altezza H
        self.z_start_spin.setValue(float(getattr(obj, "Z_Inizio", 4.0)))                        # Z Inizio
        self.z_end_spin.setValue(float(getattr(obj, "Z_Fine", -30.0)))                          # Z Fine
        self.taper_spin.setValue(float(getattr(obj, "ConicitaRaggio", 0.0)))                    # Conicità
        if str(getattr(obj, "TipoIngresso", "")) in TIPI_INGRESSO_DENTE:                        # Tipo ingresso
            self.infeed_combo.setCurrentText(str(obj.TipoIngresso))
        self.n_cuts_spin.setValue(int(getattr(obj, "NumeroPassateTaglio", 8)))                  # N° passate
        self.n_spring_spin.setValue(int(getattr(obj, "PassateFinituraMolla", 2)))               # Passate a vuoto
        self.pullout_spin.setValue(float(getattr(obj, "SmussoUscita", 2.0)))                    # Smusso uscita
        self.rpm_spin.setValue(float(getattr(obj, "GiriMandrinoRPM", 800.0)))                   # Giri RPM

    def pulisci_anteprima_percorso(self, doc):                                                  # Rimuove in modo sicuro le anteprime temporanee
        if not doc: return                                                                      # Controllo sicurezza
        for attr in ["preview_rapidi", "preview_lavoro"]:                                       # Rimuove riferimenti diretti
            if hasattr(self, attr) and getattr(self, attr):
                try:
                    obj = getattr(self, attr)
                    if doc.getObject(obj.Name): doc.removeObject(obj.Name)
                except Exception: pass
                setattr(self, attr, None)
        for obj in list(doc.Objects):                                                           # Rimuove eventuali residui
            if obj.Name.startswith("TMP_Thread_"):
                try: doc.removeObject(obj.Name)
                except Exception: pass

    def getStandardButtons(self):                                                               # Pulsanti OK e Cancel
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel                # Restituisce OK | Cancel

    def accept(self):                                                                           # Conferma e salva l'operazione di Filettatura in Operazioni_CAM
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc: return False                                                                # Controllo sicurezza

        ops_group = doc.getObject("Operazioni_CAM")                                             # Cerca il gruppo Operazioni_CAM
        if not ops_group:                                                                       # Se non esiste lo crea
            ops_group = doc.addObject("App::DocumentObjectGroup", "Operazioni_CAM")
            ops_group.Label = "Operazioni CAM (Cicli Tornio)"

        nome_op = self.name_input.text().strip() or "Filettatura 1"                             # Nome operazione
        if self.edit_obj and doc.getObject(self.edit_obj.Name):                                 # Se siamo in modifica
            op_obj = self.edit_obj                                                              # Riutilizza l'oggetto esistente
        else:                                                                                   # Altrimenti crea il nuovo oggetto parametrico
            op_obj = doc.addObject("Part::FeaturePython", "Op_Filettatura")                     # Crea Part::FeaturePython
            LatheThreadingObject(op_obj)                                                        # Inizializza Proxy
            ViewProviderLatheThreading(op_obj.ViewObject)                                       # Inizializza ViewProvider
            ops_group.addObject(op_obj)                                                         # Aggiunge al gruppo Operazioni_CAM

        t_name = self.tool_combo.itemData(self.tool_combo.currentIndex()) if self.tool_combo.count() > 0 else ""

        op_obj.Proxy._is_executing = True                                                       # Sospende execute durante il salvataggio proprietà
        try:                                                                                    # Scrive tutte le proprietà
            op_obj.Proxy.ensure_properties(op_obj)
            op_obj.OperationName = nome_op
            op_obj.Label = nome_op
            op_obj.TipoCiclo = self.cycle_combo.currentText()
            op_obj.UtensileAssegnato = str(t_name or "")
            op_obj.StandardPreimpostato = self.std_combo.currentText()
            op_obj.DiametroNominale = self.d_nom_spin.value()
            op_obj.PassoFiletto = self.pitch_spin.value()
            op_obj.AngoloProfilo = self.ang_prof_spin.value()
            op_obj.AltezzaFiletto = self.h_thread_spin.value()
            op_obj.Z_Inizio = self.z_start_spin.value()
            op_obj.Z_Fine = self.z_end_spin.value()
            op_obj.ConicitaRaggio = self.taper_spin.value()
            op_obj.TipoIngresso = self.infeed_combo.currentText()
            op_obj.NumeroPassateTaglio = self.n_cuts_spin.value()
            op_obj.PassateFinituraMolla = self.n_spring_spin.value()
            op_obj.SmussoUscita = self.pullout_spin.value()
            op_obj.GiriMandrinoRPM = self.rpm_spin.value()
        finally:                                                                                # Sblocca Proxy
            op_obj.Proxy._is_executing = False

        op_obj.Proxy.execute(op_obj)                                                            # Calcola e disegna il percorso finale
        if hasattr(op_obj, "ViewObject") and op_obj.ViewObject:
            op_obj.ViewObject.Visibility = True                                                 # Mostra il percorso viola/magenta nel 3D

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