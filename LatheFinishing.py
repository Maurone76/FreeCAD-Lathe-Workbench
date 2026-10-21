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
import LatheRoughing                                                                            # Riutilizza le utility di lettura WCS, Grezzo e Pezzo 3D


TIPI_CICLO_FINITURA = [                                                                         # Modalità operative supportate dal ciclo di finitura
    "Finitura Completa (Faccia + Esterno)",                                                     # Pulisce la faccia frontale a Z=0 e poi scorre lungo il profilo esterno
    "Solo Finitura Esterna (OD)",                                                               # Segue solo il profilo longitudinale esterno da Z Inizio a Z Fine
    "Solo Finitura Frontale (Facing)",                                                          # Esegue solo la passata di finitura frontale lungo X
    "Finitura Interna / Bareno (ID)"                                                            # Segue il profilo interno del foro da Z Inizio a Z Fine
]                                                                                               # Fine elenco cicli di finitura

MODALITA_COMPENSAZIONE = [                                                                      # Opzioni di compensazione raggio punta inserto
    "G42 - Compensazione Destra (OD verso Mandrino)",                                           # Tipica per tornitura esterna verso -Z
    "G41 - Compensazione Sinistra (ID verso Mandrino)",                                         # Tipica per barenatura interna verso -Z
    "G40 - Nessuna Compensazione CNC (Centro Punta)"                                            # Percorso non compensato da CNC
]                                                                                               # Fine elenco compensazioni


def calcola_percorso_finitura(                                                                  # Genera la lista movimenti (G0/G1) e le Shapes 3D della finitura
    wcs, tipo_ciclo, part_obj, stock_info,                                                      # Riferimenti geometrici
    z_start, z_end, r_target_manuale, usa_pezzo_3d, consenti_sottosquadri,                      # Limiti geometrici e gestione gole/sottosquadri
    num_passate, step_pre_fin, sovra_x, sovra_z,                                                # Passate multiple (pre-finitura + passata a zero) e sovrametalli
    lead_in, lead_out, ang_out, sic_x, sic_z, feed_fin, comp_str                                # Approccio, uscita, sicurezze, avanzamento e codice G40/G41/G42
):                                                                                              # Inizio motore di calcolo percorso finitura
    moves = []                                                                                  # Lista movimenti: {"cmd": "G0"/"G1", "x": r, "z": z, "f": feed, "comp": G40/41/42}
    edges_rapidi = []                                                                           # Segmenti 3D per i movimenti rapidi G00 (Rosso)
    edges_lavoro = []                                                                           # Segmenti 3D per i movimenti di finitura G01 (Ciano/Azzurro)

    r_grezzo = stock_info["r_rot"]                                                              # Raggio esterno massimo del grezzo
    r_foro_grezzo = stock_info["r_int"]                                                         # Raggio foro interno del grezzo
    z_front_grezzo = stock_info["z_front"]                                                      # Quota Z frontale grezzo
    z_lim_griffe = stock_info["z_lim_chuck"]                                                    # Quota Z limite collisione griffe mandrino

    z_ini = float(z_start)                                                                      # Quota Z iniziale
    z_fin = max(float(z_end), z_lim_griffe)                                                     # Limita automaticamente Z Fine per non toccare le griffe
    sx_res = float(sovra_x)                                                                     # Sovrametallo residuo finale su X (normalmente 0.0 mm)
    sz_res = float(sovra_z)                                                                     # Sovrametallo residuo finale su Z (normalmente 0.0 mm)
    n_pass = max(1, min(int(num_passate), 5))                                                   # Numero di passate di finitura (1 = diretta, 2+ = pre-finitura + finitura)
    passo_extra = max(float(step_pre_fin), 0.05)                                                # Sovrametallo asportato dall'ultima passata (es. 0.15 mm)

    l_in = max(float(lead_in), 0.2)                                                             # Lunghezza tratto di ingresso morbido G01
    l_out = max(float(lead_out), 0.2)                                                           # Lunghezza tratto di uscita morbida G01
    ang_rad = math.radians(max(0.0, min(float(ang_out), 90.0)))                                 # Angolo di distacco in uscita (radianti)
    out_dx = max(l_out * math.sin(ang_rad), 0.1)                                                # Componente radiale X del distacco finale
    out_dz = l_out * math.cos(ang_rad)                                                          # Componente assiale Z del distacco finale

    safe_r = r_grezzo + max(float(sic_x), 1.5)                                                  # Raggio di sicurezza per i rapidi esterni
    safe_z = max(z_front_grezzo, z_ini) + max(float(sic_z), 1.5)                                # Quota Z di sicurezza frontale

    cod_comp = "G40"                                                                            # Estrae il codice ISO G40/G41/G42 dalla stringa
    if "G41" in str(comp_str): cod_comp = "G41"                                                 # Compensazione sinistra
    elif "G42" in str(comp_str): cod_comp = "G42"                                               # Compensazione destra

    curr_pt = [safe_r, safe_z]                                                                  # Punto iniziale della punta utensile
    moves.append({"cmd": "G0", "x": curr_pt[0], "z": curr_pt[1], "f": 0.0, "comp": "G40"})      # Posizionamento iniziale a compensazione disattivata

    def add_segment(cmd, next_r, next_z, comp_code="G40"):                                      # Registra un movimento nella lista e crea il segmento 3D
        p1 = FreeCAD.Vector(wcs.x + curr_pt[0], wcs.y, wcs.z + curr_pt[1])                      # Punto 3D iniziale sul piano XZ
        p2 = FreeCAD.Vector(wcs.x + next_r, wcs.y, wcs.z + next_z)                              # Punto 3D finale sul piano XZ
        if (p2 - p1).Length > 1e-4:                                                             # Verifica che il segmento abbia lunghezza reale
            edge = Part.makeLine(p1, p2)                                                        # Crea la linea 3D
            if cmd == "G0":                                                                     # Movimento rapido
                edges_rapidi.append(edge)                                                       # Aggiunge ai rapidi
            else:                                                                               # Movimento di lavoro in finitura
                edges_lavoro.append(edge)                                                       # Aggiunge al percorso di taglio
            moves.append({                                                                      # Aggiunge il dizionario movimento per Simulatore e G-Code
                "cmd": cmd,                                                                     # G0 o G1
                "x": float(next_r),                                                             # Raggio X rispetto al WCS
                "z": float(next_z),                                                             # Quota Z rispetto al WCS
                "f": float(feed_fin if cmd == "G1" else 0.0),                                   # Avanzamento di finitura
                "comp": comp_code                                                               # Stato compensazione raggio (G40/G41/G42)
            })                                                                                  # Fine record movimento
            curr_pt[0] = float(next_r)                                                          # Aggiorna X corrente
            curr_pt[1] = float(next_z)                                                          # Aggiorna Z corrente

    esegui_face = tipo_ciclo in ["Finitura Completa (Faccia + Esterno)", "Solo Finitura Frontale (Facing)"]
    esegui_od = tipo_ciclo in ["Finitura Completa (Faccia + Esterno)", "Solo Finitura Esterna (OD)"]
    esegui_id = (tipo_ciclo == "Finitura Interna / Bareno (ID)")                                # Verifica se è finitura interna

    if usa_pezzo_3d and part_obj:                                                               # Se segue la geometria reale del Pezzo 3D
        prof_base = LatheRoughing.campiona_profilo_pezzo(                                       # Campiona ad alta risoluzione (180 punti) il solido 3D
            part_obj, wcs, z_ini, z_fin, modalita_id=esegui_id, num_campioni=180
        )                                                                                       # Nota: se consenti_sottosquadri è attivo su OD, campiona senza filtro monotono
        if consenti_sottosquadri and not esegui_id:                                             # Se l'utente usa un inserto V 35° / D 55° che può scendere nei profili concavi
            z_max = max(z_ini, z_fin); z_min = min(z_ini, z_fin)                                # Estremi Z
            dz = (z_max - z_min) / 180.0 if abs(z_max - z_min) > 1e-4 else 1.0                  # Passo Z
            shape = part_obj.Shape; bb = shape.BoundBox                                         # Forma e BoundBox
            r_max_bb = max(abs(bb.XMax - wcs.x), abs(bb.XMin - wcs.x), abs(bb.YMax - wcs.y), abs(bb.YMin - wcs.y)) + 20.0
            prof_raw = []                                                                       # Lista profilo reale con eventuali avvallamenti dolci
            for i in range(181):                                                                # Cicla sui 181 punti
                zr = z_max - i * dz; zg = wcs.z + zr                                            # Quota Z relativa e globale
                p0 = FreeCAD.Vector(wcs.x, wcs.y, zg)                                           # Punto sull'asse
                seg = Part.makeLine(p0, p0 + FreeCAD.Vector(r_max_bb, 0, 0))                    # Raggio sonda lungo +X
                try:
                    c = shape.common(seg)                                                       # Intersezione col pezzo
                    rv = max((v.Point - p0).Length for v in c.Vertexes) if (c and c.Vertexes) else 0.0
                except Exception: rv = 0.0                                                      # Fallback
                prof_raw.append((zr, rv))                                                       # Aggiunge punto reale
            prof_base = prof_raw                                                                # Usa il profilo reale completo
    else:                                                                                       # Se lavora a diametro costante manuale
        r_man = max(float(r_target_manuale), 0.0)                                               # Raggio impostato manualmente
        prof_base = [(z_ini, r_man), (z_fin, r_man)]                                            # Profilo cilindrico semplice

    for idx_p in range(n_pass):                                                                 # Esegue le passate (dalla pre-finitura fino all'ultima passata a misura)
        passate_rimanenti = (n_pass - 1) - idx_p                                                # Vale 0 sull'ultima passata finale
        extra_offset = passate_rimanenti * passo_extra                                          # Sovrametallo temporaneo delle passate di pre-finitura

        if esegui_face:                                                                         # 1. PASSATA DI FINITURA FRONTALE (FACING)
            z_face = 0.0 + sz_res + extra_offset                                                # Quota Z della faccia finita
            r_start_f = (prof_base[0][1] + sx_res + extra_offset + l_in) if (esegui_od and prof_base) else (r_grezzo + l_in)
            r_end_f = max(r_foro_grezzo - 0.4, -0.4)                                            # Scende 0.4 mm oltre il centro per pulire il testimone

            add_segment("G0", r_start_f, z_face + l_in)                                         # Avvicinamento rapido davanti al diametro esterno
            add_segment("G1", r_start_f, z_face, cod_comp)                                      # Attiva compensazione e si porta a quota Z della faccia
            add_segment("G1", r_end_f, z_face, cod_comp)                                        # Passata continua di finitura frontale fino al centro
            add_segment("G1", r_end_f + out_dx * 0.5, z_face + max(out_dz, 0.3), "G40")         # Stacca dal centro disattivando la compensazione

        if esegui_od and prof_base:                                                             # 2. PASSATA CONTINUA DI FINITURA ESTERNA (OD)
            pts_od = [(zp + sz_res + extra_offset, rp + sx_res + extra_offset) for (zp, rp) in prof_base]
            z0, r0 = pts_od[0]                                                                  # Punto di attacco iniziale del profilo esterno

            add_segment("G0", max(r0 + l_in, curr_pt[0]), z0 + l_in)                            # Posizionamento rapido sopra l'inizio del profilo
            add_segment("G0", max(r0 - 0.5, 0.0), z0 + l_in)                                    # Scende in rapido davanti allo smusso/fronte iniziale
            add_segment("G1", r0, z0, cod_comp)                                                 # Ingresso morbido G01 sul primo punto con compensazione G42

            for (zp, rp) in pts_od[1:]:                                                         # Scorre lungo tutta la sagoma del pezzo (cilindri, coni, raccordi, spallamenti)
                add_segment("G1", rp, zp, cod_comp)                                             # Movimento di finitura continua G01

            z_last, r_last = pts_od[-1]                                                         # Ultimo punto raggiunto a Z Fine
            add_segment("G1", r_last + out_dx, min(z_last + out_dz, safe_z), "G40")             # Uscita morbida angolata disattivando G40
            add_segment("G0", safe_r, min(z_last + out_dz, safe_z))                             # Risale in rapido fuori dagli ingombri
            add_segment("G0", safe_r, safe_z)                                                   # Torna a Z di sicurezza iniziale

        if esegui_id and prof_base:                                                             # 3. PASSATA CONTINUA DI FINITURA INTERNA / BARENO (ID)
            pts_id = [(zp + sz_res + extra_offset, max(rp - sx_res - extra_offset, 1.0)) for (zp, rp) in prof_base]
            z0, r0 = pts_id[0]                                                                  # Punto iniziale all'imbocco del foro
            r_safe_id = max(r0 - l_in, r_foro_grezzo * 0.8, 0.5)                                # Raggio di sicurezza verso il centro del foro

            add_segment("G0", r_safe_id, safe_z)                                                # Porta il bareno sull'imbocco del foro
            add_segment("G0", r0, z0 + l_in)                                                    # Si allinea al raggio d'attacco appena fuori dal pezzo
            add_segment("G1", r0, z0, cod_comp)                                                 # Entra nel profilo interno attivando G41

            for (zp, rp) in pts_id[1:]:                                                         # Segue tutto il profilo interno del foro
                add_segment("G1", rp, zp, cod_comp)                                             # Taglio continuo interno G01

            z_last, r_last = pts_id[-1]                                                         # Fondo del foro lavorato
            r_exit_id = max(r_last - out_dx, 0.5)                                               # Stacca verso il centro (-X) per non rigare il foro finito
            add_segment("G1", r_exit_id, min(z_last + out_dz, safe_z), "G40")                   # Distacco radiale interno e revoca G40
            add_segment("G0", r_exit_id, safe_z)                                                # Esce in rapido dal foro lungo +Z
            add_segment("G0", safe_r, safe_z)                                                   # Ritorna alla posizione di sicurezza

    shapes_all = []                                                                             # Lista globale dei segmenti 3D
    if edges_rapidi: shapes_all.extend(edges_rapidi)                                            # Unisce i rapidi
    if edges_lavoro: shapes_all.extend(edges_lavoro)                                            # Unisce i movimenti di finitura

    comp = Part.makeCompound(shapes_all) if shapes_all else Part.makeSphere(0.5, wcs)           # Compound finale dell'operazione
    comp_rapidi = Part.makeCompound(edges_rapidi) if edges_rapidi else None                     # Compound rapidi per anteprima rossa
    comp_lavoro = Part.makeCompound(edges_lavoro) if edges_lavoro else None                     # Compound lavoro per anteprima azzurra
    return comp, comp_rapidi, comp_lavoro, moves, z_fin                                         # Restituisce le geometrie e i punti del percorso


class LatheFinishingObject:                                                                     # Classe Proxy per l'operazione parametrica di Finitura
    def __init__(self, obj):                                                                    # Costruttore del Proxy
        self._is_executing = False                                                              # Semaforo anti-ricorsione
        self.ensure_properties(obj)                                                             # Garantisce la creazione di tutte le proprietà
        obj.Proxy = self                                                                        # Collega il Proxy all'oggetto FreeCAD

    def ensure_properties(self, obj):                                                           # Aggiunge le proprietà native se non esistono
        if not hasattr(obj, "OperationName"):                                                   # Nome operazione
            obj.addProperty("App::PropertyString", "OperationName", "Operazione", "Nome operazione").OperationName = "Finitura Profilo 1"
        if not hasattr(obj, "TipoCiclo"):                                                       # Strategia di finitura
            obj.addProperty("App::PropertyEnumeration", "TipoCiclo", "Operazione", "Strategia di finitura")
            obj.TipoCiclo = TIPI_CICLO_FINITURA                                                 # Assegna le 4 strategie
        if not hasattr(obj, "UtensileAssegnato"):                                               # Utensile selezionato dal Magazzino
            obj.addProperty("App::PropertyString", "UtensileAssegnato", "Operazione", "Utensile utilizzato").UtensileAssegnato = ""
        if not hasattr(obj, "CompensazioneRaggio"):                                             # Compensazione raggio utensile G41/G42/G40
            obj.addProperty("App::PropertyEnumeration", "CompensazioneRaggio", "Operazione", "Compensazione raggio punta ISO")
            obj.CompensazioneRaggio = MODALITA_COMPENSAZIONE                                    # Opzioni G42, G41, G40
        if not hasattr(obj, "PezzoRiferimento"):                                                # Nome del solido Pezzo 3D
            obj.addProperty("App::PropertyString", "PezzoRiferimento", "Geometria", "Solido Pezzo 3D").PezzoRiferimento = ""
        if not hasattr(obj, "UsaProfiloPezzo3D"):                                               # Segui sagoma 3D
            obj.addProperty("App::PropertyBool", "UsaProfiloPezzo3D", "Geometria", "Segui sagoma del Pezzo 3D").UsaProfiloPezzo3D = True
        if not hasattr(obj, "ConsentiSottosquadri"):                                            # Permette a inserti tipo V 35° di entrare in profili concavi
            obj.addProperty("App::PropertyBool", "ConsentiSottosquadri", "Geometria", "Segui profili concavi / sottosquadri dolci").ConsentiSottosquadri = False
        if not hasattr(obj, "Z_Inizio"):                                                        # Quota Z iniziale (mm)
            obj.addProperty("App::PropertyFloat", "Z_Inizio", "Geometria", "Quota Z iniziale (mm)").Z_Inizio = 0.0
        if not hasattr(obj, "Z_Fine"):                                                          # Quota Z finale (mm)
            obj.addProperty("App::PropertyFloat", "Z_Fine", "Geometria", "Quota Z finale (mm)").Z_Fine = -50.0
        if not hasattr(obj, "DiametroFinaleManuale"):                                           # Diametro manuale (se non si usa il 3D)
            obj.addProperty("App::PropertyFloat", "DiametroFinaleManuale", "Geometria", "Diametro manuale (mm)").DiametroFinaleManuale = 30.0
        if not hasattr(obj, "NumeroPassate"):                                                   # Numero di passate di finitura (1..5)
            obj.addProperty("App::PropertyInteger", "NumeroPassate", "Parametri Taglio", "Numero passate di finitura (1 = diretta)").NumeroPassate = 1
        if not hasattr(obj, "StepPreFinitura"):                                                 # Spessore asportato nella passata aggiuntiva (mm)
            obj.addProperty("App::PropertyFloat", "StepPreFinitura", "Parametri Taglio", "Spessore passata pre-finitura (mm)").StepPreFinitura = 0.15
        if not hasattr(obj, "SovrametalloResiduoX"):                                            # Sovrametallo residuo su X (default 0.0 mm)
            obj.addProperty("App::PropertyFloat", "SovrametalloResiduoX", "Parametri Taglio", "Sovrametallo residuo X (mm)").SovrametalloResiduoX = 0.0
        if not hasattr(obj, "SovrametalloResiduoZ"):                                            # Sovrametallo residuo su Z (default 0.0 mm)
            obj.addProperty("App::PropertyFloat", "SovrametalloResiduoZ", "Parametri Taglio", "Sovrametallo residuo Z (mm)").SovrametalloResiduoZ = 0.0
        if not hasattr(obj, "LunghezzaApproccio"):                                              # Tratto di approccio morbido Lead-In (mm)
            obj.addProperty("App::PropertyFloat", "LunghezzaApproccio", "Parametri Taglio", "Lunghezza ingresso Lead-In (mm)").LunghezzaApproccio = 1.5
        if not hasattr(obj, "DistaccoRitorno"):                                                 # Tratto di uscita Lead-Out (mm)
            obj.addProperty("App::PropertyFloat", "DistaccoRitorno", "Parametri Taglio", "Lunghezza uscita Lead-Out (mm)").DistaccoRitorno = 1.5
        if not hasattr(obj, "AngoloDistacco"):                                                  # Angolo di distacco in uscita (gradi)
            obj.addProperty("App::PropertyFloat", "AngoloDistacco", "Parametri Taglio", "Angolo di distacco in uscita (gradi)").AngoloDistacco = 45.0
        if not hasattr(obj, "VelocitaTaglio"):                                                  # Velocità di taglio Vc / RPM
            obj.addProperty("App::PropertyFloat", "VelocitaTaglio", "Parametri Taglio", "Velocità di taglio Vc / RPM").VelocitaTaglio = 220.0
        if not hasattr(obj, "AvanzamentoFinitura"):                                             # Avanzamento di finitura (mm/giro)
            obj.addProperty("App::PropertyFloat", "AvanzamentoFinitura", "Parametri Taglio", "Avanzamento finitura F (mm/giro)").AvanzamentoFinitura = 0.10
        if not hasattr(obj, "PercorsoJSON"):                                                    # Punti del percorso in formato JSON per Simulazione e G-Code
            obj.addProperty("App::PropertyString", "PercorsoJSON", "Dati CAM", "Punti percorso per Simulatore e G-Code").PercorsoJSON = "[]"

    def onDocumentRestored(self, obj):                                                          # Chiamato alla riapertura del documento
        self._is_executing = False                                                              # Sblocca il flag
        self.ensure_properties(obj)                                                             # Verifica tutte le proprietà

    def execute(self, obj):                                                                     # Ricalcola il percorso di finitura 3D
        if getattr(self, "_is_executing", False):                                               # Evita loop ricorsivi
            return                                                                              # Esce subito
        self._is_executing = True                                                               # Attiva il blocco
        try:                                                                                    # Blocco protetto di calcolo
            self.ensure_properties(obj)                                                         # Verifica attributi
            doc = obj.Document                                                                  # Documento corrente
            wcs = LatheRoughing.get_wcs_origin(doc)                                             # Origine WCS
            sic_x, sic_z = LatheRoughing.get_setup_safe_clearances(doc)                         # Distanze di sicurezza dal Setup
            stock_info = LatheRoughing.get_stock_info(doc)                                      # Dati Grezzo e limite griffe
            part_obj = doc.getObject(obj.PezzoRiferimento) if (doc and obj.PezzoRiferimento) else None

            comp, _, _, moves, _ = calcola_percorso_finitura(                                   # Calcola la geometria e i punti della finitura
                wcs, str(obj.TipoCiclo), part_obj, stock_info,
                obj.Z_Inizio, obj.Z_Fine, obj.DiametroFinaleManuale / 2.0,
                obj.UsaProfiloPezzo3D, obj.ConsentiSottosquadri,
                obj.NumeroPassate, obj.StepPreFinitura,
                obj.SovrametalloResiduoX, obj.SovrametalloResiduoZ,
                obj.LunghezzaApproccio, obj.DistaccoRitorno, obj.AngoloDistacco,
                sic_x, sic_z, obj.AvanzamentoFinitura, str(obj.CompensazioneRaggio)
            )                                                                                   # Fine calcolo
            obj.PercorsoJSON = json.dumps(moves)                                                # Salva il percorso per il Simulatore e il Post-Processor
            obj.Shape = comp                                                                    # Assegna la Shape 3D
            if hasattr(obj, "ViewObject") and obj.ViewObject:                                   # Colora il tracciato di finitura in Ciano/Azzurro brillante
                obj.ViewObject.LineColor = (0.10, 0.82, 0.98)                                   # Azzurro per distinguerlo subito dal verde della sgrossatura
                obj.ViewObject.LineWidth = 2.5                                                  # Spessore linea evidente
        except Exception as e:                                                                  # Cattura eventuali errori
            FreeCAD.Console.PrintError(f"Errore calcolo Finitura: {e}\n")                       # Stampa in console
        finally:                                                                                # Rilascia il blocco
            self._is_executing = False                                                          # Fine esecuzione

    def onChanged(self, obj, prop):                                                             # Intercetta modifiche live dalle Proprietà di FreeCAD
        if getattr(self, "_is_executing", False):                                               # Evita ricorsioni
            return                                                                              # Esce
        props_calcolo = [                                                                       # Proprietà che rigenerano il percorso
            "TipoCiclo", "CompensazioneRaggio", "PezzoRiferimento",                             # Strategia e pezzo
            "UsaProfiloPezzo3D", "ConsentiSottosquadri",                                        # Opzioni profilo
            "Z_Inizio", "Z_Fine", "DiametroFinaleManuale",                                      # Limiti
            "NumeroPassate", "StepPreFinitura", "SovrametalloResiduoX", "SovrametalloResiduoZ", # Passate e sovrametalli
            "LunghezzaApproccio", "DistaccoRitorno", "AngoloDistacco", "AvanzamentoFinitura"    # Ingresso, uscita e avanzamento
        ]                                                                                       # Fine lista
        if prop in props_calcolo:                                                               # Se cambia un parametro geometrico/tecnologico
            self.execute(obj)                                                                   # Aggiorna il percorso 3D
        elif prop == "OperationName":                                                           # Se cambia il nome
            if hasattr(obj, "OperationName") and obj.OperationName:                             # Aggiorna l'etichetta nell'albero
                obj.Label = obj.OperationName                                                   # Allinea Label

    def __getstate__(self):                                                                     # Serializzazione
        return None                                                                             # Nessun dato speciale

    def __setstate__(self, state):                                                              # Deserializzazione
        self._is_executing = False                                                              # Ripristina flag
        return None                                                                             # Fine


class ViewProviderLatheFinishing:                                                               # ViewProvider per icona e doppio click sull'operazione di Finitura
    def __init__(self, vobj):                                                                   # Costruttore ViewProvider
        vobj.Proxy = self                                                                       # Collega il Proxy

    def getIcon(self):                                                                          # Icona nell'albero delle operazioni
        return LatheResources.get_icon_path("lathe_finishing.svg", "Part_Section")              # Icona SVG dedicata Finitura

    def attach(self, vobj):                                                                     # Collega gli oggetti alla vista
        self.ViewObject = vobj                                                                  # Riferimento ViewObject
        self.Object = vobj.Object                                                               # Riferimento Object

    def updateData(self, vobj, prop):                                                           # Aggiornamento dati
        return                                                                                  # Gestito da execute

    def onDelete(self, vobj, subelements):                                                      # Autorizza cancellazione
        return True                                                                             # Sempre consentito

    def doubleClicked(self, vobj):                                                              # Doppio click sull'operazione nell'albero
        if not FreeCADGui.Control.activeDialog():                                               # Se non c'è già un pannello aperto
            panel = LatheFinishingPanel(edit_obj=vobj.Object)                                   # Apre il pannello caricando l'operazione
            FreeCADGui.Control.showDialog(panel)                                                # Mostra il pannello nella scheda Azioni
        return True                                                                             # Evento gestito

    def setEdit(self, vobj, mode):                                                              # Modalità Edit standard
        if mode == 0:                                                                           # Modifica base
            if not FreeCADGui.Control.activeDialog():                                           # Evita doppia apertura
                panel = LatheFinishingPanel(edit_obj=vobj.Object)                               # Crea il pannello
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


class LatheFinishingPanel:                                                                      # Pannello Task per programmare il ciclo di Finitura
    def __init__(self, edit_obj=None):                                                          # Costruttore del pannello (nuovo o modifica)
        self.edit_obj = edit_obj                                                                # Memorizza eventuale operazione in modifica
        self.is_updating = True                                                                 # Blocca i segnali durante la creazione della UI

        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        self.pulisci_anteprima_percorso(doc)                                                    # Pulisce eventuali anteprime rimaste appese
        if self.edit_obj and hasattr(self.edit_obj, "ViewObject") and self.edit_obj.ViewObject: # Se siamo in modifica
            self.edit_obj.ViewObject.Visibility = False                                         # Nasconde l'originale durante l'anteprima bicolore

        self.form = QtWidgets.QWidget()                                                         # Contenitore principale del pannello
        self.form.setMinimumWidth(240)                                                          # Larghezza minima compatta per non tagliare a destra
        self.layout = QtWidgets.QVBoxLayout(self.form)                                          # Layout verticale principale
        self.layout.setContentsMargins(4, 4, 4, 4)                                              # Margini ridotti

        self.grp_gen = QtWidgets.QGroupBox("Operazione, Utensile e Compensazione")              # Gruppo dati generali
        self.lyt_gen = QtWidgets.QFormLayout(self.grp_gen)                                      # Form layout

        self.name_input = QtWidgets.QLineEdit("Finitura Profilo 1")                             # Nome operazione
        self.cycle_combo = QtWidgets.QComboBox()                                                # Scelta strategia di finitura
        self.cycle_combo.addItems(TIPI_CICLO_FINITURA)                                          # Popola le 4 strategie
        self.cycle_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cycle_combo.setMinimumContentsLength(10)

        self.tool_combo = QtWidgets.QComboBox()                                                 # Scelta utensile dal Magazzino Utensili
        self.tool_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.tool_combo.setMinimumContentsLength(10)
        self.popola_combo_utensili(doc)                                                         # Carica gli utensili

        self.comp_combo = QtWidgets.QComboBox()                                                 # Scelta compensazione raggio G42 / G41 / G40
        self.comp_combo.addItems(MODALITA_COMPENSAZIONE)                                        # Popola opzioni compensazione
        self.comp_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.comp_combo.setMinimumContentsLength(10)

        self.lyt_gen.addRow("Nome:", self.name_input)                                           # Riga Nome
        self.lyt_gen.addRow("Strategia:", self.cycle_combo)                                     # Riga Strategia
        self.lyt_gen.addRow("Utensile:", self.tool_combo)                                       # Riga Utensile
        self.lyt_gen.addRow("Compensazione:", self.comp_combo)                                  # Riga Compensazione Raggio G41/G42
        self.layout.addWidget(self.grp_gen)                                                     # Aggiunge al layout principale

        self.tabs = QtWidgets.QTabWidget()                                                      # Schede: 1. Geometria | 2. Tecnologia & Uscita

        self.tab_geo = QtWidgets.QWidget()                                                      # SCHEDA 1: Profilo Pezzo e Limiti Z / X
        self.lyt_geo = QtWidgets.QVBoxLayout(self.tab_geo)                                      # Layout verticale Scheda 1

        self.grp_part = QtWidgets.QGroupBox("Profilo Pezzo e Limiti di Finitura")               # Gruppo selezione pezzo e limiti
        self.lyt_part = QtWidgets.QFormLayout(self.grp_part)                                    # Form layout

        self.chk_use_3d = QtWidgets.QCheckBox("Segui sagoma esatta del Solido Pezzo 3D")        # Usa il modello 3D
        self.chk_use_3d.setChecked(True)                                                        # Attivo di default

        self.chk_undercut = QtWidgets.QCheckBox("Consenti ingresso in profili concavi dolci")   # Utile per inserti tipo V 35° (VNMG/VCMT)
        self.chk_undercut.setChecked(False)                                                     # Disattivato di default per sicurezza

        self.part_combo = QtWidgets.QComboBox()                                                 # Tendina con i solidi del Pezzo 3D
        self.part_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.part_combo.setMinimumContentsLength(10)
        self.popola_combo_pezzi(doc)                                                            # Cerca i solidi nel documento

        self.btn_pick_part = QtWidgets.QPushButton("Cattura Pezzo da Selezione 3D")             # Cattura il solido cliccato nel 3D
        self.btn_pick_part.clicked.connect(self.cattura_pezzo_selezionato)                      # Collega la cattura

        stock_info = LatheRoughing.get_stock_info(doc)                                          # Legge i dati del Grezzo_Macchina
        self.z_start_spin = QtWidgets.QDoubleSpinBox(); self.z_start_spin.setRange(-2000, 2000); self.z_start_spin.setDecimals(2); self.z_start_spin.setValue(0.0)
        self.z_end_spin = QtWidgets.QDoubleSpinBox(); self.z_end_spin.setRange(-2000, 2000); self.z_end_spin.setDecimals(2)
        self.btn_auto_zend = QtWidgets.QPushButton("Ricalcola Z Fine da Fine Pezzo 3D")         # Riporta Z Fine alla fine del pezzo
        self.btn_auto_zend.clicked.connect(self.imposta_z_fine_da_pezzo_corrente)               # Collega il ricalcolo automatico
        self.d_man_spin = QtWidgets.QDoubleSpinBox(); self.d_man_spin.setRange(0.0, 2000.0); self.d_man_spin.setValue(stock_info["r_ext"] * 1.2)

        self.lbl_status = QtWidgets.QLabel(f"Limite Griffe Mandrino: Z = {stock_info['z_lim_chuck']:.2f} mm")
        self.lbl_status.setWordWrap(True)                                                       # Va a capo automaticamente
        self.lbl_status.setStyleSheet("color: #00D2FF; font-weight: bold;")                     # Azzurro brillante informativo

        self.lyt_part.addRow(self.chk_use_3d)                                                   # Riga usa pezzo 3D
        self.lyt_part.addRow(self.chk_undercut)                                                 # Riga consenti sottosquadri dolci
        self.lyt_part.addRow("Solido Pezzo:", self.part_combo)                                  # Riga solido pezzo
        self.lyt_part.addRow(self.btn_pick_part)                                                # Riga cattura pezzo
        self.lyt_part.addRow("Z Inizio (mm):", self.z_start_spin)                               # Riga Z Inizio (default 0.0 dopo sfacciatura)
        self.lyt_part.addRow("Z Fine (mm):", self.z_end_spin)                                   # Riga Z Fine (auto-calcolata alla fine del pezzo)
        self.lyt_part.addRow(self.btn_auto_zend)                                                # Riga pulsante ricalcola Z Fine
        self.lyt_part.addRow("Ø Finale Manuale (mm):", self.d_man_spin)                         # Riga diametro manuale
        self.lyt_part.addRow(self.lbl_status)                                                   # Riga stato
        self.lyt_geo.addWidget(self.grp_part)                                                   # Aggiunge alla Scheda 1

        self.tabs.addTab(self.tab_geo, "1. Geometria")                                          # Titolo Scheda 1

        self.tab_cut = QtWidgets.QWidget()                                                      # SCHEDA 2: Passate, Approccio/Uscita e Avanzamento
        self.lyt_cut = QtWidgets.QVBoxLayout(self.tab_cut)                                      # Layout verticale Scheda 2

        self.grp_cut = QtWidgets.QGroupBox("Passate di Pulizia, Ingresso/Uscita e Taglio")      # Gruppo parametri finitura
        self.lyt_c_form = QtWidgets.QFormLayout(self.grp_cut)                                   # Form layout

        self.n_pass_spin = QtWidgets.QSpinBox(); self.n_pass_spin.setRange(1, 5); self.n_pass_spin.setValue(1) # 1 = passata singola, 2 = pre-finitura + finitura
        self.step_pre_spin = QtWidgets.QDoubleSpinBox(); self.step_pre_spin.setRange(0.02, 5.0); self.step_pre_spin.setDecimals(2); self.step_pre_spin.setValue(0.15); self.step_pre_spin.setSingleStep(0.05)
        self.fin_x_spin = QtWidgets.QDoubleSpinBox(); self.fin_x_spin.setRange(-5.0, 10.0); self.fin_x_spin.setDecimals(3); self.fin_x_spin.setValue(0.0); self.fin_x_spin.setSingleStep(0.02)
        self.fin_z_spin = QtWidgets.QDoubleSpinBox(); self.fin_z_spin.setRange(-5.0, 10.0); self.fin_z_spin.setDecimals(3); self.fin_z_spin.setValue(0.0); self.fin_z_spin.setSingleStep(0.02)
        self.lead_in_spin = QtWidgets.QDoubleSpinBox(); self.lead_in_spin.setRange(0.2, 20.0); self.lead_in_spin.setValue(1.5); self.lead_in_spin.setSingleStep(0.5)
        self.ret_spin = QtWidgets.QDoubleSpinBox(); self.ret_spin.setRange(0.2, 20.0); self.ret_spin.setValue(1.5); self.ret_spin.setSingleStep(0.5)
        self.ret_ang_spin = QtWidgets.QDoubleSpinBox(); self.ret_ang_spin.setRange(0.0, 90.0); self.ret_ang_spin.setDecimals(1); self.ret_ang_spin.setValue(45.0); self.ret_ang_spin.setSingleStep(5.0)
        self.vc_spin = QtWidgets.QDoubleSpinBox(); self.vc_spin.setRange(1.0, 15000.0); self.vc_spin.setValue(220.0); self.vc_spin.setSingleStep(10.0)
        self.feed_spin = QtWidgets.QDoubleSpinBox(); self.feed_spin.setRange(0.005, 5.0); self.feed_spin.setDecimals(3); self.feed_spin.setValue(0.10); self.feed_spin.setSingleStep(0.02)

        self.lyt_c_form.addRow("N° Passate Finitura:", self.n_pass_spin)                        # Riga numero passate (1..5)
        self.lyt_c_form.addRow("Step Pre-Finitura (mm):", self.step_pre_spin)                   # Riga spessore pre-finitura
        self.lyt_c_form.addRow("Sovram. Residuo X (mm):", self.fin_x_spin)                      # Riga sovrametallo residuo X (0 = quota nominale)
        self.lyt_c_form.addRow("Sovram. Residuo Z (mm):", self.fin_z_spin)                      # Riga sovrametallo residuo Z (0 = quota nominale)
        self.lyt_c_form.addRow("Ingresso Lead-In (mm):", self.lead_in_spin)                     # Riga lunghezza ingresso morbido
        self.lyt_c_form.addRow("Lunghezza Distacco (mm):", self.ret_spin)                       # Riga lunghezza distacco finale
        self.lyt_c_form.addRow("Angolo Distacco (°):", self.ret_ang_spin)                       # Riga angolo di distacco in uscita (0°..90°)
        self.lyt_c_form.addRow("Velocità Vc / RPM:", self.vc_spin)                              # Riga velocità di taglio
        self.lyt_c_form.addRow("Avanzamento F (mm/g):", self.feed_spin)                         # Riga avanzamento di finitura
        self.lyt_cut.addWidget(self.grp_cut)                                                    # Aggiunge alla Scheda 2
        self.lyt_cut.addStretch()                                                               # Allinea in alto

        self.tabs.addTab(self.tab_cut, "2. Parametri")                                          # Titolo Scheda 2
        self.layout.addWidget(self.tabs)                                                        # Aggiunge il TabWidget al layout principale
        self.form.setLayout(self.layout)                                                        # Applica il layout

        self.preview_rapidi = doc.addObject("Part::Feature", "TMP_Finish_Rapids")               # Oggetto temporaneo per i movimenti rapidi G00 (Rosso)
        self.preview_rapidi.Label = "ANTEPRIMA RAPIDI FINITURA"                                 # Etichetta
        self.preview_rapidi.ViewObject.LineColor = (0.95, 0.20, 0.20)                           # Rosso per i rapidi
        self.preview_rapidi.ViewObject.LineWidth = 1.5                                          # Spessore linea rapidi

        self.preview_lavoro = doc.addObject("Part::Feature", "TMP_Finish_Cut")                  # Oggetto temporaneo per la passata di finitura G01 (Ciano)
        self.preview_lavoro.Label = "ANTEPRIMA TAGLIO FINITURA"                                 # Etichetta
        self.preview_lavoro.ViewObject.LineColor = (0.10, 0.85, 1.00)                           # Azzurro/Ciano per il taglio di finitura
        self.preview_lavoro.ViewObject.LineWidth = 3.0                                          # Spessore linea finitura ben marcato

        if self.edit_obj:                                                                       # Se siamo in modifica di un'operazione esistente
            self.carica_dati_da_oggetto(self.edit_obj)                                          # Ripristina tutti i parametri salvati
        else:                                                                                   # Se è una nuova operazione di finitura
            self.imposta_z_fine_da_pezzo_corrente()                                             # Calcola automaticamente Z Fine fino alla fine del pezzo 3D
            self.on_tool_changed()                                                              # Eredita AvanzamentoFinitura e Vc dall'utensile scelto

        self.cycle_combo.currentIndexChanged.connect(self.aggiorna_ui_ciclo)                    # Collega cambio strategia
        self.tool_combo.currentIndexChanged.connect(self.on_tool_changed)                       # Collega cambio utensile
        self.comp_combo.currentIndexChanged.connect(self.trigger_update)                        # Collega cambio compensazione G41/G42/G40
        self.chk_use_3d.stateChanged.connect(self.aggiorna_ui_ciclo)                            # Collega spunta usa pezzo 3D
        self.chk_undercut.stateChanged.connect(self.trigger_update)                             # Collega spunta sottosquadri dolci
        self.part_combo.currentIndexChanged.connect(self.on_part_changed)                       # Quando cambi Pezzo 3D ricalcola Z Fine
        self.z_start_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio Z Inizio
        self.z_end_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio Z Fine
        self.d_man_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio diametro manuale
        self.n_pass_spin.valueChanged.connect(self.aggiorna_ui_ciclo)                           # Collega cambio numero passate
        self.step_pre_spin.valueChanged.connect(self.trigger_update)                            # Collega cambio step pre-finitura
        self.fin_x_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio sovrametallo residuo X
        self.fin_z_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio sovrametallo residuo Z
        self.lead_in_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio Lead-In
        self.ret_spin.valueChanged.connect(self.trigger_update)                                 # Collega cambio lunghezza distacco
        self.ret_ang_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio angolo distacco

        self.is_updating = False                                                                # Sblocca gli aggiornamenti live
        self.aggiorna_ui_ciclo()                                                                # Adatta i controlli e disegna l'anteprima 3D

    def popola_combo_utensili(self, doc):                                                       # Carica gli utensili del Magazzino Utensili
        self.tool_combo.clear()                                                                 # Svuota il combo
        if doc and doc.getObject("Libreria_Utensili"):                                          # Se esiste il Magazzino Utensili
            lib = doc.getObject("Libreria_Utensili")                                            # Gruppo magazzino
            for t in lib.Group:                                                                 # Cicla sugli utensili
                st = getattr(t, "Stazione", "T01")                                              # Sigla stazione
                self.tool_combo.addItem(f"[{st}] {t.Label}", t.Name)                            # Aggiunge voce e Name interno

    def popola_combo_pezzi(self, doc):                                                          # Carica i solidi candidati a Pezzo Finito
        self.part_combo.clear()                                                                 # Svuota il combo
        candidati = LatheRoughing.trova_candidati_pezzo(doc)                                    # Trova i solidi 3D
        if candidati:                                                                           # Se ci sono solidi
            for p in candidati:                                                                 # Cicla sui solidi
                self.part_combo.addItem(p.Label, p.Name)                                        # Aggiunge etichetta e Name
        else:                                                                                   # Se non ci sono solidi 3D
            self.part_combo.addItem("(Nessun Pezzo 3D - Usa Quota Manuale)", "")                # Modalità manuale

    def imposta_z_fine_da_pezzo_corrente(self):                                                 # Calcola automaticamente Z Fine fino alla fine del Pezzo 3D
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc: return                                                                      # Controllo sicurezza
        p_name = self.part_combo.itemData(self.part_combo.currentIndex()) if self.part_combo.count() > 0 else ""
        part_obj = doc.getObject(p_name) if p_name else None                                    # Oggetto Pezzo 3D
        z_calc = LatheRoughing.calcola_z_fine_da_pezzo(part_obj, doc)                           # Fine esatta del pezzo lungo Z
        prev = self.is_updating                                                                 # Salva stato semaforo
        self.is_updating = True                                                                 # Sospende segnali
        self.z_end_spin.setValue(z_calc)                                                        # Imposta Z Fine (modificabile anche a mano)
        self.is_updating = prev                                                                 # Ripristina semaforo
        self.trigger_update()                                                                   # Aggiorna il percorso

    def on_part_changed(self):                                                                  # Chiamato quando si cambia il Solido Pezzo
        self.imposta_z_fine_da_pezzo_corrente()                                                 # Ricalcola automaticamente Z Fine

    def cattura_pezzo_selezionato(self):                                                        # Cattura il solido cliccato nella vista 3D
        sel = FreeCADGui.Selection.getSelection()                                               # Selezione corrente
        if not sel:                                                                             # Se vuoto
            self.lbl_status.setText("Seleziona prima il solido del Pezzo nella vista 3D!")
            return                                                                              # Esce
        obj_sel = sel[0]                                                                        # Oggetto cliccato
        idx = self.part_combo.findData(obj_sel.Name)                                            # Cerca nel combo
        if idx < 0:                                                                             # Se non presente lo aggiunge
            self.part_combo.addItem(obj_sel.Label, obj_sel.Name)
            idx = self.part_combo.count() - 1
        self.part_combo.setCurrentIndex(idx)                                                    # Seleziona il pezzo
        FreeCADGui.Selection.clearSelection()                                                   # Pulisce la selezione
        self.imposta_z_fine_da_pezzo_corrente()                                                 # Aggiorna Z Fine

    def on_tool_changed(self):                                                                  # Legge AvanzamentoFinitura, Vc e Quadrante ISO dall'utensile
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc or self.tool_combo.count() == 0: return                                      # Verifica validità
        t_name = self.tool_combo.itemData(self.tool_combo.currentIndex())                       # Nome utensile
        t_obj = doc.getObject(t_name) if t_name else None                                       # Oggetto utensile
        if t_obj:                                                                               # Se esiste
            prev = self.is_updating                                                             # Salva stato
            self.is_updating = True                                                             # Sospende segnali
            vc_base = float(getattr(t_obj, "VelocitaTaglio", 180.0))                            # Legge la velocità dell'utensile
            self.vc_spin.setValue(round(vc_base * 1.15, 0))                                     # Propone +15% di Vc per la finitura lucida
            self.feed_spin.setValue(float(getattr(t_obj, "AvanzamentoFinitura", 0.10)))         # Legge l'AvanzamentoFinitura specifico dell'utensile!
            tipo_u = str(getattr(t_obj, "TipoLavorazione", "Esterno (ISO)"))                    # Legge categoria utensile
            if "Bareno" in tipo_u:                                                              # Se è un bareno interno
                self.comp_combo.setCurrentIndex(1)                                              # Propone G41 (Compensazione Sinistra ID)
            else:                                                                               # Se è un utensile esterno
                self.comp_combo.setCurrentIndex(0)                                              # Propone G42 (Compensazione Destra OD)
            self.is_updating = prev                                                             # Ripristina semaforo
            self.trigger_update()                                                               # Aggiorna l'anteprima

    def aggiorna_ui_ciclo(self):                                                                # Adatta l'interfaccia alla strategia scelta
        ciclo = self.cycle_combo.currentText()                                                  # Strategia corrente
        is_facing_only = (ciclo == "Solo Finitura Frontale (Facing)")                           # Solo sfacciatura
        is_id = (ciclo == "Finitura Interna / Bareno (ID)")                                     # Finitura interna
        usa_3d = self.chk_use_3d.isChecked() and (not is_facing_only)                           # Uso modello 3D

        self.part_combo.setEnabled(usa_3d)                                                      # Abilita combo pezzo
        self.btn_pick_part.setEnabled(usa_3d)                                                   # Abilita cattura pezzo
        self.chk_undercut.setEnabled(usa_3d and (not is_id))                                    # Sottosquadri attivi su OD 3D
        self.z_end_spin.setEnabled(not is_facing_only)                                          # Z Fine attiva sulle lavorazioni longitudinali
        self.btn_auto_zend.setEnabled(not is_facing_only)                                       # Pulsante auto Z Fine
        self.d_man_spin.setEnabled((not usa_3d) and (not is_facing_only))                       # Diametro manuale
        self.step_pre_spin.setEnabled(self.n_pass_spin.value() > 1)                             # Step pre-finitura attivo se N° Passate > 1
        self.trigger_update()                                                                   # Aggiorna il 3D

    def trigger_update(self, *args):                                                            # Aggiorna in tempo reale l'anteprima 3D del percorso di finitura
        if self.is_updating: return                                                             # Se bloccato esce
        self.is_updating = True                                                                 # Attiva semaforo
        try:                                                                                    # Blocco di calcolo
            doc = FreeCAD.ActiveDocument                                                        # Documento attivo
            if not doc or not self.preview_rapidi or not self.preview_lavoro: return            # Verifica validità
            wcs = LatheRoughing.get_wcs_origin(doc)                                             # Origine WCS
            sic_x, sic_z = LatheRoughing.get_setup_safe_clearances(doc)                         # Sicurezze Setup
            stock_info = LatheRoughing.get_stock_info(doc)                                      # Dati Grezzo e limite griffe

            p_name = self.part_combo.itemData(self.part_combo.currentIndex()) if self.part_combo.count() > 0 else ""
            part_obj = doc.getObject(p_name) if p_name else None                                # Oggetto Pezzo 3D

            _, c_rap, c_lav, moves, z_eff = calcola_percorso_finitura(                          # Calcola il percorso
                wcs, self.cycle_combo.currentText(), part_obj, stock_info,
                self.z_start_spin.value(), self.z_end_spin.value(),
                self.d_man_spin.value() / 2.0, self.chk_use_3d.isChecked(),
                self.chk_undercut.isChecked(), self.n_pass_spin.value(),
                self.step_pre_spin.value(), self.fin_x_spin.value(), self.fin_z_spin.value(),
                self.lead_in_spin.value(), self.ret_spin.value(), self.ret_ang_spin.value(),
                sic_x, sic_z, self.feed_spin.value(), self.comp_combo.currentText()
            )                                                                                   # Fine calcolo

            self.preview_rapidi.Shape = c_rap if c_rap else Part.Shape()                        # Aggiorna i rapidi rossi
            self.preview_lavoro.Shape = c_lav if c_lav else Part.Shape()                        # Aggiorna il taglio azzurro

            n_punti = sum(1 for m in moves if m["cmd"] == "G1")                                 # Conta i segmenti di finitura
            if self.z_end_spin.value() < stock_info["z_lim_chuck"]:                             # Avviso limite griffe
                self.lbl_status.setStyleSheet("color: #FF5555; font-weight: bold;")
                self.lbl_status.setText(f"Z Fine limitata a {z_eff:.2f} mm per sicurezza Griffe! ({n_punti} segmenti)")
            else:                                                                               # Percorso OK
                self.lbl_status.setStyleSheet("color: #00D2FF; font-weight: bold;")
                self.lbl_status.setText(f"Finitura OK: Z Fine={z_eff:.2f} mm | {n_punti} tratti G01.")

            doc.recompute()                                                                     # Rinfresca la vista 3D
        finally:                                                                                # Rilascia semaforo
            self.is_updating = False                                                            # Fine aggiornamento

    def carica_dati_da_oggetto(self, obj):                                                      # Popola la UI quando si riapre un'operazione con doppio click
        obj.Proxy.ensure_properties(obj)                                                        # Verifica proprietà
        self.name_input.setText(str(getattr(obj, "OperationName", obj.Label)))                  # Nome
        if str(obj.TipoCiclo) in TIPI_CICLO_FINITURA:                                           # Strategia
            self.cycle_combo.setCurrentText(str(obj.TipoCiclo))
        idx_t = self.tool_combo.findData(str(getattr(obj, "UtensileAssegnato", "")))            # Utensile
        if idx_t >= 0: self.tool_combo.setCurrentIndex(idx_t)
        if str(getattr(obj, "CompensazioneRaggio", "")) in MODALITA_COMPENSAZIONE:              # Compensazione G41/G42/G40
            self.comp_combo.setCurrentText(str(obj.CompensazioneRaggio))
        self.chk_use_3d.setChecked(bool(getattr(obj, "UsaProfiloPezzo3D", True)))               # Usa 3D
        self.chk_undercut.setChecked(bool(getattr(obj, "ConsentiSottosquadri", False)))         # Sottosquadri
        idx_p = self.part_combo.findData(str(getattr(obj, "PezzoRiferimento", "")))             # Pezzo 3D
        if idx_p >= 0: self.part_combo.setCurrentIndex(idx_p)
        self.z_start_spin.setValue(float(getattr(obj, "Z_Inizio", 0.0)))                        # Z Inizio
        self.z_end_spin.setValue(float(getattr(obj, "Z_Fine", -50.0)))                          # Z Fine
        self.d_man_spin.setValue(float(getattr(obj, "DiametroFinaleManuale", 30.0)))            # Diametro manuale
        self.n_pass_spin.setValue(int(getattr(obj, "NumeroPassate", 1)))                        # Numero passate
        self.step_pre_spin.setValue(float(getattr(obj, "StepPreFinitura", 0.15)))               # Step pre-finitura
        self.fin_x_spin.setValue(float(getattr(obj, "SovrametalloResiduoX", 0.0)))              # Sovrametallo residuo X
        self.fin_z_spin.setValue(float(getattr(obj, "SovrametalloResiduoZ", 0.0)))              # Sovrametallo residuo Z
        self.lead_in_spin.setValue(float(getattr(obj, "LunghezzaApproccio", 1.5)))              # Lead-In
        self.ret_spin.setValue(float(getattr(obj, "DistaccoRitorno", 1.5)))                     # Lunghezza distacco
        self.ret_ang_spin.setValue(float(getattr(obj, "AngoloDistacco", 45.0)))                 # Angolo distacco
        self.vc_spin.setValue(float(getattr(obj, "VelocitaTaglio", 220.0)))                     # Velocità Vc
        self.feed_spin.setValue(float(getattr(obj, "AvanzamentoFinitura", 0.10)))               # Avanzamento Finitura

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
            if obj.Name.startswith("TMP_Finish_"):
                try: doc.removeObject(obj.Name)
                except Exception: pass

    def getStandardButtons(self):                                                               # Pulsanti OK e Cancel
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel                # Restituisce OK | Cancel

    def accept(self):                                                                           # Conferma e salva l'operazione di Finitura in Operazioni_CAM
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc: return False                                                                # Controllo sicurezza

        ops_group = doc.getObject("Operazioni_CAM")                                             # Cerca il gruppo Operazioni_CAM
        if not ops_group:                                                                       # Se non esiste lo crea
            ops_group = doc.addObject("App::DocumentObjectGroup", "Operazioni_CAM")
            ops_group.Label = "Operazioni CAM (Cicli Tornio)"

        nome_op = self.name_input.text().strip() or "Finitura Profilo 1"                        # Nome operazione
        if self.edit_obj and doc.getObject(self.edit_obj.Name):                                 # Se siamo in modifica
            op_obj = self.edit_obj                                                              # Riutilizza l'oggetto esistente
        else:                                                                                   # Altrimenti crea il nuovo oggetto
            op_obj = doc.addObject("Part::FeaturePython", "Op_Finitura")                        # Crea Part::FeaturePython
            LatheFinishingObject(op_obj)                                                        # Inizializza Proxy
            ViewProviderLatheFinishing(op_obj.ViewObject)                                       # Inizializza ViewProvider
            ops_group.addObject(op_obj)                                                         # Aggiunge al gruppo Operazioni_CAM

        t_name = self.tool_combo.itemData(self.tool_combo.currentIndex()) if self.tool_combo.count() > 0 else ""
        p_name = self.part_combo.itemData(self.part_combo.currentIndex()) if self.part_combo.count() > 0 else ""

        op_obj.Proxy._is_executing = True                                                       # Sospende execute durante il salvataggio proprietà
        try:                                                                                    # Scrive tutte le proprietà
            op_obj.Proxy.ensure_properties(op_obj)
            op_obj.OperationName = nome_op
            op_obj.Label = nome_op
            op_obj.TipoCiclo = self.cycle_combo.currentText()
            op_obj.UtensileAssegnato = str(t_name or "")
            op_obj.CompensazioneRaggio = self.comp_combo.currentText()
            op_obj.PezzoRiferimento = str(p_name or "")
            op_obj.UsaProfiloPezzo3D = self.chk_use_3d.isChecked()
            op_obj.ConsentiSottosquadri = self.chk_undercut.isChecked()
            op_obj.Z_Inizio = self.z_start_spin.value()
            op_obj.Z_Fine = self.z_end_spin.value()
            op_obj.DiametroFinaleManuale = self.d_man_spin.value()
            op_obj.NumeroPassate = self.n_pass_spin.value()
            op_obj.StepPreFinitura = self.step_pre_spin.value()
            op_obj.SovrametalloResiduoX = self.fin_x_spin.value()
            op_obj.SovrametalloResiduoZ = self.fin_z_spin.value()
            op_obj.LunghezzaApproccio = self.lead_in_spin.value()
            op_obj.DistaccoRitorno = self.ret_spin.value()
            op_obj.AngoloDistacco = self.ret_ang_spin.value()
            op_obj.VelocitaTaglio = self.vc_spin.value()
            op_obj.AvanzamentoFinitura = self.feed_spin.value()
        finally:                                                                                # Sblocca Proxy
            op_obj.Proxy._is_executing = False

        op_obj.Proxy.execute(op_obj)                                                            # Calcola il percorso finale
        if hasattr(op_obj, "ViewObject") and op_obj.ViewObject:
            op_obj.ViewObject.Visibility = True                                                 # Mostra il percorso azzurro nel 3D

        self.pulisci_anteprima_percorso(doc)                                                    # Elimina l'anteprima temporanea
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