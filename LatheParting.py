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


TIPI_CICLO_TRONCATURA = [                                                                       # Modalità operative supportate dal ciclo di Troncatura
    "1. Troncatura con Smusso / Raccordo Posteriore",                                           # Esegue lo smusso sullo spigolo sinistro del pezzo e poi tronca
    "2. Troncatura Diretta Continua",                                                           # Affondamento diretto lungo -X fino al distacco
    "3. Troncatura con Scarico Truciolo (Peck - G75)"                                           # Affondamento a step con ritrazione rompi-truciolo
]                                                                                               # Fine elenco cicli di troncatura


def calcola_percorso_troncatura(                                                                # Genera la lista movimenti (G0/G1) e le Shapes 3D della troncatura
    wcs, tipo_ciclo, stock_info,                                                                # Riferimenti geometrici
    z_faccia_sinistra, w_lama, comp_spessore_lama,                                              # Quota faccia finita del pezzo e compensazione larghezza lama
    d_inizio, r_arrivo, smusso_post,                                                            # Diametro esterno partenza, oltre-centro/foro e smusso posteriore
    usa_peck, passo_peck, rit_peck,                                                             # Parametri scarico truciolo
    rallenta_centro, d_inizio_rallenta, perc_feed_rallenta,                                     # Rallentamento avanzamento prima del distacco
    sic_x, sic_z, feed_lavoro                                                                   # Sicurezze e avanzamento base
):                                                                                              # Inizio motore di calcolo percorso troncatura
    moves = []                                                                                  # Lista movimenti: {"cmd": "G0"/"G1", "x": r, "z": z, "f": feed}
    edges_rapidi = []                                                                           # Segmenti 3D per i movimenti rapidi G00 (Rosso)
    edges_lavoro = []                                                                           # Segmenti 3D per i movimenti di taglio G01 (Rosso Scuro/Borgogna)

    r_grezzo = stock_info["r_rot"]                                                              # Raggio esterno massimo del grezzo
    z_lim_griffe = stock_info["z_lim_chuck"]                                                    # Quota Z limite collisione griffe mandrino
    w_tool = max(float(w_lama), 0.5)                                                            # Larghezza lama troncatrice (mm)

    # Se comp_spessore_lama è True, lo spigolo destro della lama tocca z_faccia_sinistra, ma il lato sinistro della lama va a z_faccia_sinistra - w_tool:
    z_taglio = float(z_faccia_sinistra)                                                         # Quota Z dello spigolo destro della lama (faccia posteriore del pezzo)
    z_bordo_sx_lama = (z_taglio - w_tool) if comp_spessore_lama else z_taglio                   # Quota Z effettiva raggiunta dal fianco sinistro della lama verso le griffe
    if z_bordo_sx_lama < z_lim_griffe:                                                          # Controllo anti-collisione del fianco sinistro lama contro le griffe
        z_taglio = z_lim_griffe + (w_tool if comp_spessore_lama else 0.0)                       # Sposta la quota di taglio davanti alle griffe!

    r_ini = max(float(d_inizio) / 2.0, 1.0)                                                     # Raggio esterno di inizio taglio
    r_fin = float(r_arrivo)                                                                     # Raggio finale (es. -0.5 mm oltre centro, oppure raggio foro tubo)
    if r_fin >= r_ini:                                                                          # Sicurezza geometrica
        r_fin = -0.5                                                                            # Scende oltre centro

    smusso = max(float(smusso_post), 0.0) if "Smusso" in tipo_ciclo else 0.0                    # Dimensione smusso posteriore a 45° (mm)
    peck_q = max(float(passo_peck), 0.2)                                                        # Incremento di affondamento peck (mm)
    peck_ret = max(float(rit_peck), 0.1)                                                        # Ritrazione rompi-truciolo (mm)

    f_base = max(float(feed_lavoro), 0.01)                                                      # Avanzamento principale di troncatura (mm/giro)
    f_slow = max(f_base * (max(10.0, min(float(perc_feed_rallenta), 100.0)) / 100.0), 0.005)    # Avanzamento ridotto sul perno finale (es. 40% di F)
    r_soglia_slow = max(float(d_inizio_rallenta) / 2.0, r_fin) if rallenta_centro else (r_fin - 10.0)

    safe_r = max(r_grezzo, r_ini) + max(float(sic_x), 1.5)                                      # Raggio di sicurezza esterno
    safe_z = max(stock_info["z_front"], z_taglio) + max(float(sic_z), 2.0)                      # Quota Z di sicurezza frontale

    curr_pt = [safe_r, safe_z]                                                                  # Posizione iniziale utensile
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

    r_start_plunge = r_ini                                                                      # Raggio da cui parte il tuffo finale di troncatura

    if smusso > 0.01 and (r_ini - smusso * 1.5) > r_fin:                                        # 1. PRE-TAGLIO E SMUSSO POSTERIORE DEL PEZZO
        r_pre = r_ini - smusso - 0.3                                                            # Scende appena sotto la profondità dello smusso per scaricare il fianco
        add_segment("G0", safe_r, z_taglio)                                                     # Si allinea in rapido alla quota Z di troncatura
        add_segment("G0", r_ini + 0.5, z_taglio)                                                # Scende vicino al diametro esterno
        add_segment("G1", r_pre, z_taglio, f_base)                                              # Pre-incisione radiale per liberare lo spazio allo smusso
        add_segment("G0", r_ini + 0.5, z_taglio)                                                # Risale fuori dal diametro
        add_segment("G0", r_ini + 0.5, z_taglio + smusso)                                       # Si sposta a destra di 'smusso' sul bordo del pezzo
        add_segment("G1", r_ini, z_taglio + smusso, f_base)                                     # Tocca il diametro esterno del pezzo
        add_segment("G1", r_ini - smusso, z_taglio, f_base * 0.8)                               # Esegue lo smusso posteriore a 45° entrando nel canale di taglio!
        r_start_plunge = r_ini - smusso                                                         # Il tuffo di troncatura prosegue direttamente dalla fine dello smusso
    else:                                                                                       # Posizionamento standard senza smusso
        add_segment("G0", safe_r, z_taglio)                                                     # Si allinea in rapido alla quota Z di troncatura
        add_segment("G0", r_ini + 0.5, z_taglio)                                                # Scende a 0.5 mm dal diametro esterno

    usa_p = usa_peck or ("Peck" in tipo_ciclo)                                                  # Verifica se eseguire lo scarico truciolo a step
    if usa_p:                                                                                   # 2A. TRONCATURA CON SCARICO TRUCIOLO (PECK)
        r_curr = r_start_plunge                                                                 # Raggio corrente raggiunto
        while r_curr > r_fin + 1e-4:                                                            # Cicla finché non tronca completamente il pezzo
            r_next = max(r_curr - peck_q, r_fin)                                                # Quota del peck successivo
            f_step = f_slow if (r_next <= r_soglia_slow) else f_base                            # Rallenta automaticamente negli ultimi millimetri verso il centro
            if r_curr > r_soglia_slow and r_next < r_soglia_slow:                               # Se il peck attraversa la soglia di rallentamento
                add_segment("G1", r_soglia_slow, z_taglio, f_base)                              # Taglia a velocità normale fino alla soglia
                add_segment("G1", r_next, z_taglio, f_slow)                                     # Completa il peck ad avanzamento ridotto
            else:                                                                               # Peck normale
                add_segment("G1", r_next, z_taglio, f_step)                                     # Affonda di un incremento Q
            if r_next > r_fin + 1e-4:                                                           # Se il pezzo non è ancora staccato
                add_segment("G0", min(r_next + peck_ret, safe_r), z_taglio)                     # Ritrae di peck_ret per rompere il truciolo
                add_segment("G0", r_next + 0.1, z_taglio)                                       # Ritorna vicino al fondo del canale
            r_curr = r_next                                                                     # Aggiorna quota raggiunta
    else:                                                                                       # 2B. TRONCATURA DIRETTA CONTINUA (CON EVENTUALE RALLENTAMENTO AL CENTRO)
        if rallenta_centro and r_start_plunge > r_soglia_slow > r_fin:                          # Se la soglia di rallentamento è compresa nella corsa
            add_segment("G1", r_soglia_slow, z_taglio, f_base)                                  # Taglia ad avanzamento pieno fino a Ø Rallentamento
            add_segment("G1", r_fin, z_taglio, f_slow)                                          # Rallenta per accompagnare dolcemente il distacco del pezzo
        else:                                                                                   # Taglio unico
            add_segment("G1", r_fin, z_taglio, f_base)                                          # Affonda fino a oltre-centro (o foro)

    add_segment("G0", safe_r, z_taglio)                                                         # Risale subito in rapido fuori dal diametro barra
    add_segment("G0", safe_r, safe_z)                                                           # Ritorna alla quota di sicurezza frontale

    shapes_all = []                                                                             # Lista globale dei segmenti 3D
    if edges_rapidi: shapes_all.extend(edges_rapidi)                                            # Unisce i rapidi
    if edges_lavoro:                                                                            # Se ci sono movimenti di lavoro
        shapes_all.extend(edges_lavoro)                                                         # Aggiunge i segmenti di taglio
        # Aggiunge un anello tratteggiato/circolare sul piano di troncatura per evidenziare dove cade il taglio nel 3D:
        p_piano_3d = FreeCAD.Vector(wcs.x, wcs.y, wcs.z + z_taglio)
        c_taglio = Part.makeCircle(r_ini, p_piano_3d, FreeCAD.Vector(0, 0, 1))
        shapes_all.append(c_taglio)

    comp = Part.makeCompound(shapes_all) if shapes_all else Part.makeSphere(0.5, wcs)           # Compound finale dell'operazione
    comp_rapidi = Part.makeCompound(edges_rapidi) if edges_rapidi else None                     # Compound rapidi per anteprima rossa
    comp_lavoro = Part.makeCompound(edges_lavoro) if edges_lavoro else None                     # Compound lavoro per anteprima borgogna/cremisi
    return comp, comp_rapidi, comp_lavoro, moves, z_taglio                                      # Restituisce geometrie, punti e Z effettiva di taglio


class LathePartingObject:                                                                       # Classe Proxy per l'operazione parametrica di Troncatura
    def __init__(self, obj):                                                                    # Costruttore del Proxy
        self._is_executing = False                                                              # Semaforo anti-ricorsione
        self.ensure_properties(obj)                                                             # Garantisce la creazione di tutte le proprietà
        obj.Proxy = self                                                                        # Collega il Proxy all'oggetto FreeCAD

    def ensure_properties(self, obj):                                                           # Aggiunge le proprietà native se mancanti
        if not hasattr(obj, "OperationName"):                                                   # Nome operazione
            obj.addProperty("App::PropertyString", "OperationName", "Operazione", "Nome operazione").OperationName = "Troncatura Finale"
        if not hasattr(obj, "TipoCiclo"):                                                       # Strategia di troncatura
            obj.addProperty("App::PropertyEnumeration", "TipoCiclo", "Operazione", "Modalità di troncatura")
            obj.TipoCiclo = TIPI_CICLO_TRONCATURA                                               # Assegna le 3 modalità
        if not hasattr(obj, "UtensileAssegnato"):                                               # Utensile selezionato dal Magazzino
            obj.addProperty("App::PropertyString", "UtensileAssegnato", "Operazione", "Utensile troncatore utilizzato").UtensileAssegnato = ""
        if not hasattr(obj, "LarghezzaLama"):                                                   # Larghezza lama troncatrice (mm)
            obj.addProperty("App::PropertyFloat", "LarghezzaLama", "Operazione", "Larghezza lama troncatrice (mm)").LarghezzaLama = 3.0
        if not hasattr(obj, "PezzoRiferimento"):                                                # Nome del solido Pezzo 3D
            obj.addProperty("App::PropertyString", "PezzoRiferimento", "Geometria Taglio", "Solido Pezzo 3D").PezzoRiferimento = ""
        if not hasattr(obj, "Z_PianoTaglio"):                                                   # Quota Z della faccia posteriore finita del pezzo (mm)
            obj.addProperty("App::PropertyFloat", "Z_PianoTaglio", "Geometria Taglio", "Quota Z faccia posteriore pezzo (mm)").Z_PianoTaglio = -50.0
        if not hasattr(obj, "CompensaSpessoreLama"):                                            # Considera che la lama scava a sinistra di Z_PianoTaglio
            obj.addProperty("App::PropertyBool", "CompensaSpessoreLama", "Geometria Taglio", "Allinea filo destro lama a Z Pezzo (scava a -W)").CompensaSpessoreLama = True
        if not hasattr(obj, "DiametroEsterno"):                                                 # Diametro esterno da cui iniziare a troncare (mm)
            obj.addProperty("App::PropertyFloat", "DiametroEsterno", "Geometria Taglio", "Diametro esterno inizio taglio (mm)").DiametroEsterno = 50.0
        if not hasattr(obj, "QuotaOltreCentro"):                                                # Raggio finale di distacco (negativo = oltre centro, es. -0.5 mm)
            obj.addProperty("App::PropertyFloat", "QuotaOltreCentro", "Geometria Taglio", "Raggio arrivo X (mm, es. -0.5 oltre centro)").QuotaOltreCentro = -0.5
        if not hasattr(obj, "SmussoPosteriore"):                                                # Smusso a 45° sullo spigolo sinistro del pezzo troncato (mm)
            obj.addProperty("App::PropertyFloat", "SmussoPosteriore", "Geometria Taglio", "Smusso posteriore pezzo a 45° (mm)").SmussoPosteriore = 0.5
        if not hasattr(obj, "UsaScaricoTruciolo"):                                              # Attiva/disattiva il pecking
            obj.addProperty("App::PropertyBool", "UsaScaricoTruciolo", "Parametri Taglio", "Affondamento a step con scarico truciolo").UsaScaricoTruciolo = False
        if not hasattr(obj, "PassoPeck"):                                                       # Incremento Q di affondamento (mm)
            obj.addProperty("App::PropertyFloat", "PassoPeck", "Parametri Taglio", "Passo incremento Peck Q (mm)").PassoPeck = 3.0
        if not hasattr(obj, "RitrazionePeck"):                                                  # Ritrazione rompi-truciolo (mm)
            obj.addProperty("App::PropertyFloat", "RitrazionePeck", "Parametri Taglio", "Ritrazione rompi-truciolo (mm)").RitrazionePeck = 0.3
        if not hasattr(obj, "RallentaAlCentro"):                                                # Riduce l'avanzamento sul perno centrale prima del distacco
            obj.addProperty("App::PropertyBool", "RallentaAlCentro", "Parametri Taglio", "Riduci avanzamento prima del distacco").RallentaAlCentro = True
        if not hasattr(obj, "DiametroInizioRallentamento"):                                     # Diametro sotto il quale entra l'avanzamento ridotto (mm)
            obj.addProperty("App::PropertyFloat", "DiametroInizioRallentamento", "Parametri Taglio", "Diametro inizio rallentamento (mm)").DiametroInizioRallentamento = 8.0
        if not hasattr(obj, "PercAvanzamentoRidotto"):                                          # Percentuale dell'avanzamento sul perno finale (es. 40%)
            obj.addProperty("App::PropertyFloat", "PercAvanzamentoRidotto", "Parametri Taglio", "Percentuale avanzamento al centro (%)").PercAvanzamentoRidotto = 40.0
        if not hasattr(obj, "VelocitaTaglio"):                                                  # Velocità di taglio Vc / RPM
            obj.addProperty("App::PropertyFloat", "VelocitaTaglio", "Parametri Taglio", "Velocità di taglio Vc / RPM").VelocitaTaglio = 110.0
        if not hasattr(obj, "AvanzamentoLavoro"):                                               # Avanzamento di troncatura (mm/giro)
            obj.addProperty("App::PropertyFloat", "AvanzamentoLavoro", "Parametri Taglio", "Avanzamento troncatura F (mm/giro)").AvanzamentoLavoro = 0.08
        if not hasattr(obj, "PercorsoJSON"):                                                    # Punti del percorso salvati per Simulatore e G-Code
            obj.addProperty("App::PropertyString", "PercorsoJSON", "Dati CAM", "Punti percorso per Simulatore e G-Code").PercorsoJSON = "[]"

    def onDocumentRestored(self, obj):                                                          # Chiamato alla riapertura del documento
        self._is_executing = False                                                              # Sblocca il flag
        self.ensure_properties(obj)                                                             # Verifica le proprietà

    def execute(self, obj):                                                                     # Ricalcola il percorso 3D della troncatura
        if getattr(self, "_is_executing", False):                                               # Evita loop ricorsivi
            return                                                                              # Esce subito
        self._is_executing = True                                                               # Attiva il semaforo
        try:                                                                                    # Blocco protetto di calcolo
            self.ensure_properties(obj)                                                         # Verifica attributi
            doc = obj.Document                                                                  # Documento corrente
            wcs = LatheRoughing.get_wcs_origin(doc)                                             # Origine WCS
            sic_x, sic_z = LatheRoughing.get_setup_safe_clearances(doc)                         # Sicurezze Setup
            stock_info = LatheRoughing.get_stock_info(doc)                                      # Dati Grezzo e limite griffe

            comp, _, _, moves, _ = calcola_percorso_troncatura(                                 # Calcola il percorso della troncatura
                wcs, str(obj.TipoCiclo), stock_info,
                obj.Z_PianoTaglio, obj.LarghezzaLama, obj.CompensaSpessoreLama,
                obj.DiametroEsterno, obj.QuotaOltreCentro, obj.SmussoPosteriore,
                obj.UsaScaricoTruciolo, obj.PassoPeck, obj.RitrazionePeck,
                obj.RallentaAlCentro, obj.DiametroInizioRallentamento, obj.PercAvanzamentoRidotto,
                sic_x, sic_z, obj.AvanzamentoLavoro
            )                                                                                   # Fine calcolo
            obj.PercorsoJSON = json.dumps(moves)                                                # Salva il percorso per il Simulatore e il Post-Processor
            obj.Shape = comp                                                                    # Assegna la Shape 3D
            if hasattr(obj, "ViewObject") and obj.ViewObject:                                   # Colora il tracciato in Cremisi / Borgogna brillante
                obj.ViewObject.LineColor = (0.90, 0.12, 0.35)                                   # Rosso Cremisi/Borgogna per la troncatura
                obj.ViewObject.LineWidth = 2.5                                                  # Spessore linea
        except Exception as e:                                                                  # Cattura errori imprevisti
            FreeCAD.Console.PrintError(f"Errore calcolo Troncatura: {e}\n")                     # Stampa in console
        finally:                                                                                # Rilascia il semaforo
            self._is_executing = False                                                          # Fine esecuzione

    def onChanged(self, obj, prop):                                                             # Intercetta modifiche live dalle Proprietà di FreeCAD
        if getattr(self, "_is_executing", False):                                               # Evita ricorsioni
            return                                                                              # Esce
        props_calcolo = [                                                                       # Proprietà che rigenerano il percorso
            "TipoCiclo", "LarghezzaLama", "Z_PianoTaglio", "CompensaSpessoreLama",              # Posizione e lama
            "DiametroEsterno", "QuotaOltreCentro", "SmussoPosteriore",                          # Diametri e smusso
            "UsaScaricoTruciolo", "PassoPeck", "RitrazionePeck",                                # Pecking
            "RallentaAlCentro", "DiametroInizioRallentamento", "PercAvanzamentoRidotto",        # Rallentamento al centro
            "AvanzamentoLavoro"                                                                 # Avanzamento
        ]                                                                                       # Fine lista
        if prop in props_calcolo:                                                               # Se cambia un parametro
            self.execute(obj)                                                                   # Aggiorna il percorso 3D
        elif prop == "OperationName":                                                           # Se cambia il nome operazione
            if hasattr(obj, "OperationName") and obj.OperationName:                             # Allinea l'etichetta nell'albero
                obj.Label = obj.OperationName                                                   # Imposta Label

    def __getstate__(self):                                                                     # Serializzazione
        return None                                                                             # Nessun dato speciale

    def __setstate__(self, state):                                                              # Deserializzazione
        self._is_executing = False                                                              # Ripristina flag
        return None                                                                             # Fine


class ViewProviderLatheParting:                                                                 # ViewProvider per icona e doppio click sull'operazione di Troncatura
    def __init__(self, vobj):                                                                   # Costruttore ViewProvider
        vobj.Proxy = self                                                                       # Collega il Proxy

    def getIcon(self):                                                                          # Icona nell'albero delle operazioni
        return LatheResources.get_icon_path("lathe_parting.svg", "Part_Slice")                  # Icona SVG dedicata Troncatura

    def attach(self, vobj):                                                                     # Collega gli oggetti alla vista
        self.ViewObject = vobj                                                                  # Riferimento ViewObject
        self.Object = vobj.Object                                                               # Riferimento Object

    def updateData(self, vobj, prop):                                                           # Aggiornamento dati
        return                                                                                  # Gestito da execute

    def onDelete(self, vobj, subelements):                                                      # Autorizza cancellazione
        return True                                                                             # Sempre consentito

    def doubleClicked(self, vobj):                                                              # Doppio click sull'operazione nell'albero
        if not FreeCADGui.Control.activeDialog():                                               # Se non c'è già un pannello aperto
            panel = LathePartingPanel(edit_obj=vobj.Object)                                     # Apre il pannello caricando l'operazione
            FreeCADGui.Control.showDialog(panel)                                                # Mostra nella scheda Azioni
        return True                                                                             # Evento gestito

    def setEdit(self, vobj, mode):                                                              # Modalità Edit standard
        if mode == 0:                                                                           # Modifica base
            if not FreeCADGui.Control.activeDialog():                                           # Evita doppia apertura
                panel = LathePartingPanel(edit_obj=vobj.Object)                                 # Crea il pannello
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


class LathePartingPanel:                                                                        # Pannello Task per programmare il ciclo di Troncatura Pezzo
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

        self.grp_gen = QtWidgets.QGroupBox("Operazione e Lama Troncatrice")                     # Gruppo dati generali
        self.lyt_gen = QtWidgets.QFormLayout(self.grp_gen)                                      # Form layout

        self.name_input = QtWidgets.QLineEdit("Troncatura Finale")                              # Nome operazione
        self.cycle_combo = QtWidgets.QComboBox()                                                # Scelta modalità di troncatura
        self.cycle_combo.addItems(TIPI_CICLO_TRONCATURA)                                        # Popola le 3 modalità
        self.cycle_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cycle_combo.setMinimumContentsLength(10)

        self.tool_combo = QtWidgets.QComboBox()                                                 # Scelta utensile dal Magazzino Utensili
        self.tool_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.tool_combo.setMinimumContentsLength(10)
        self.popola_combo_utensili(doc)                                                         # Carica gli utensili (preferendo quelli da Troncatura/Gola)

        self.lama_w_spin = QtWidgets.QDoubleSpinBox()                                           # Larghezza lama (mm)
        self.lama_w_spin.setRange(0.5, 25.0); self.lama_w_spin.setDecimals(2); self.lama_w_spin.setValue(3.0); self.lama_w_spin.setSingleStep(0.5)

        self.lyt_gen.addRow("Nome:", self.name_input)                                           # Riga Nome
        self.lyt_gen.addRow("Strategia:", self.cycle_combo)                                     # Riga Strategia
        self.lyt_gen.addRow("Utensile:", self.tool_combo)                                       # Riga Utensile
        self.lyt_gen.addRow("Largh. Lama W (mm):", self.lama_w_spin)                            # Riga Larghezza Lama
        self.layout.addWidget(self.grp_gen)                                                     # Aggiunge al layout principale

        self.tabs = QtWidgets.QTabWidget()                                                      # Schede: 1. Posizione Taglio | 2. Rallentamento & Peck

        self.tab_geo = QtWidgets.QWidget()                                                      # SCHEDA 1: Piano Z di Troncatura, Diametri e Smusso
        self.lyt_geo = QtWidgets.QVBoxLayout(self.tab_geo)                                      # Layout verticale Scheda 1

        self.grp_geo = QtWidgets.QGroupBox("Posizione Piano di Taglio e Smusso")                # Gruppo geometria taglio
        self.lyt_g_form = QtWidgets.QFormLayout(self.grp_geo)                                   # Form layout

        self.part_combo = QtWidgets.QComboBox()                                                 # Tendina con i solidi del Pezzo 3D per rilevare la fine del pezzo
        self.part_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.part_combo.setMinimumContentsLength(10)
        self.popola_combo_pezzi(doc)                                                            # Cerca i solidi 3D nel documento

        self.btn_auto_z = QtWidgets.QPushButton("Imposta Z da Fine Pezzo 3D")                   # Posiziona automaticamente il taglio alla fine esatta del pezzo
        self.btn_auto_z.clicked.connect(self.imposta_z_da_fine_pezzo)                           # Collega il calcolo automatico

        self.btn_pick_face = QtWidgets.QPushButton("Oppure Cattura Faccia Posteriore 3D")       # Cattura la faccia posteriore cliccata nel 3D
        self.btn_pick_face.clicked.connect(self.cattura_faccia_posteriore_3d)                   # Collega la cattura

        stock_info = LatheRoughing.get_stock_info(doc)                                          # Legge le quote del Grezzo_Macchina
        d_ext_grezzo = stock_info["r_ext"] * 2.0                                                # Diametro esterno barra
        r_arrivo_def = (stock_info["r_int"] - 0.5) if stock_info["r_int"] > 0.5 else -0.5       # Oltre-centro (-0.5 mm) o oltre il foro se è un tubo

        self.z_cut_spin = QtWidgets.QDoubleSpinBox(); self.z_cut_spin.setRange(-2000, 2000); self.z_cut_spin.setDecimals(2); self.z_cut_spin.setValue(-50.0)
        self.chk_comp_w = QtWidgets.QCheckBox("Compensa spessore lama (scava verso -Z)")        # Il filo destro lama lascia il pezzo alla lunghezza esatta!
        self.chk_comp_w.setChecked(True)                                                        # Attivo di default
        self.d_ext_spin = QtWidgets.QDoubleSpinBox(); self.d_ext_spin.setRange(1.0, 2000.0); self.d_ext_spin.setDecimals(2); self.d_ext_spin.setValue(d_ext_grezzo)
        self.r_end_spin = QtWidgets.QDoubleSpinBox(); self.r_end_spin.setRange(-20.0, 1000.0); self.r_end_spin.setDecimals(2); self.r_end_spin.setValue(r_arrivo_def); self.r_end_spin.setSingleStep(0.2)
        self.chamfer_spin = QtWidgets.QDoubleSpinBox(); self.chamfer_spin.setRange(0.0, 10.0); self.chamfer_spin.setDecimals(2); self.chamfer_spin.setValue(0.5); self.chamfer_spin.setSingleStep(0.1)

        self.lbl_status = QtWidgets.QLabel(f"Limite Griffe Mandrino: Z = {stock_info['z_lim_chuck']:.2f} mm")
        self.lbl_status.setWordWrap(True)                                                       # Va a capo automaticamente
        self.lbl_status.setStyleSheet("color: #FF4D79; font-weight: bold;")                     # Rosa/Cremisi informativo

        self.lyt_g_form.addRow("Solido Pezzo:", self.part_combo)                                # Riga scelta Pezzo 3D
        self.lyt_g_form.addRow(self.btn_auto_z)                                                 # Riga pulsante calcola Z da fine pezzo
        self.lyt_g_form.addRow(self.btn_pick_face)                                              # Riga pulsante cattura faccia 3D
        self.lyt_g_form.addRow("Z Faccia Sinistra (mm):", self.z_cut_spin)                      # Riga Quota Z di taglio
        self.lyt_g_form.addRow(self.chk_comp_w)                                                 # Riga compensa larghezza lama
        self.lyt_g_form.addRow("Ø Inizio Taglio (mm):", self.d_ext_spin)                        # Riga Diametro esterno inizio
        self.lyt_g_form.addRow("Raggio Arrivo X (mm):", self.r_end_spin)                        # Riga Raggio finale (-0.5 mm oltre centro)
        self.lyt_g_form.addRow("Smusso Pezzo 45° (mm):", self.chamfer_spin)                     # Riga Smusso posteriore
        self.lyt_g_form.addRow(self.lbl_status)                                                 # Riga stato
        self.lyt_geo.addWidget(self.grp_geo)                                                    # Aggiunge alla Scheda 1

        self.tabs.addTab(self.tab_geo, "1. Geometria")                                          # Titolo Scheda 1

        self.tab_cut = QtWidgets.QWidget()                                                      # SCHEDA 2: Rallentamento a Centrobarra e Scarico Truciolo
        self.lyt_cut = QtWidgets.QVBoxLayout(self.tab_cut)                                      # Layout verticale Scheda 2

        self.grp_cut = QtWidgets.QGroupBox("Rallentamento al Distacco e Scarico Truciolo")      # Gruppo parametri taglio
        self.lyt_c_form = QtWidgets.QFormLayout(self.grp_cut)                                   # Form layout

        self.chk_slow = QtWidgets.QCheckBox("Rallenta avanzamento sul perno centrale")          # Evita bave e rottura lama al distacco
        self.chk_slow.setChecked(True)                                                          # Attivo di default
        self.d_slow_spin = QtWidgets.QDoubleSpinBox(); self.d_slow_spin.setRange(0.5, 500.0); self.d_slow_spin.setDecimals(1); self.d_slow_spin.setValue(8.0); self.d_slow_spin.setSingleStep(1.0)
        self.perc_slow_spin = QtWidgets.QDoubleSpinBox(); self.perc_slow_spin.setRange(10.0, 100.0); self.perc_slow_spin.setDecimals(0); self.perc_slow_spin.setValue(40.0); self.perc_slow_spin.setSingleStep(5.0)

        self.chk_peck = QtWidgets.QCheckBox("Affondamento con Scarico Truciolo (Peck)")         # Attiva il pecking
        self.chk_peck.setChecked(False)                                                         # Opzionale (o attivato dalla strategia 3)
        self.peck_q_spin = QtWidgets.QDoubleSpinBox(); self.peck_q_spin.setRange(0.2, 50.0); self.peck_q_spin.setDecimals(2); self.peck_q_spin.setValue(3.0); self.peck_q_spin.setSingleStep(0.5)
        self.peck_ret_spin = QtWidgets.QDoubleSpinBox(); self.peck_ret_spin.setRange(0.05, 10.0); self.peck_ret_spin.setDecimals(2); self.peck_ret_spin.setValue(0.3); self.peck_ret_spin.setSingleStep(0.1)

        self.vc_spin = QtWidgets.QDoubleSpinBox(); self.vc_spin.setRange(1.0, 15000.0); self.vc_spin.setValue(110.0); self.vc_spin.setSingleStep(10.0)
        self.feed_spin = QtWidgets.QDoubleSpinBox(); self.feed_spin.setRange(0.005, 5.0); self.feed_spin.setDecimals(3); self.feed_spin.setValue(0.08); self.feed_spin.setSingleStep(0.01)

        self.lyt_c_form.addRow(self.chk_slow)                                                   # Riga checkbox rallenta al centro
        self.lyt_c_form.addRow("Ø Inizio Rallentam. (mm):", self.d_slow_spin)                   # Riga diametro inizio rallentamento
        self.lyt_c_form.addRow("Avanzamento Ridotto (%):", self.perc_slow_spin)                 # Riga % avanzamento ridotto
        self.lyt_c_form.addRow(self.chk_peck)                                                   # Riga checkbox Peck
        self.lyt_c_form.addRow("Incremento Peck Q (mm):", self.peck_q_spin)                     # Riga passo Peck Q
        self.lyt_c_form.addRow("Ritrazione Peck (mm):", self.peck_ret_spin)                     # Riga ritrazione Peck
        self.lyt_c_form.addRow("Velocità Vc / RPM:", self.vc_spin)                              # Riga velocità di taglio
        self.lyt_c_form.addRow("Avanzamento F (mm/g):", self.feed_spin)                         # Riga avanzamento base
        self.lyt_cut.addWidget(self.grp_cut)                                                    # Aggiunge alla Scheda 2
        self.lyt_cut.addStretch()                                                               # Allinea in alto

        self.tabs.addTab(self.tab_cut, "2. Parametri")                                          # Titolo Scheda 2
        self.layout.addWidget(self.tabs)                                                        # Aggiunge il TabWidget al layout principale
        self.form.setLayout(self.layout)                                                        # Applica il layout

        self.preview_rapidi = doc.addObject("Part::Feature", "TMP_Parting_Rapids")              # Oggetto temporaneo per i rapidi G00 (Rosso)
        self.preview_rapidi.Label = "ANTEPRIMA RAPIDI TRONCATURA"                               # Etichetta
        self.preview_rapidi.ViewObject.LineColor = (0.95, 0.20, 0.20)                           # Rosso per i rapidi
        self.preview_rapidi.ViewObject.LineWidth = 1.5                                          # Spessore linea rapidi

        self.preview_lavoro = doc.addObject("Part::Feature", "TMP_Parting_Cut")                 # Oggetto temporaneo per il taglio G01 (Cremisi/Borgogna)
        self.preview_lavoro.Label = "ANTEPRIMA TAGLIO TRONCATURA"                               # Etichetta
        self.preview_lavoro.ViewObject.LineColor = (0.92, 0.12, 0.38)                           # Cremisi/Borgogna per la troncatura
        self.preview_lavoro.ViewObject.LineWidth = 3.0                                          # Spessore linea lavoro

        if self.edit_obj:                                                                       # Se siamo in modifica di un'operazione esistente
            self.carica_dati_da_oggetto(self.edit_obj)                                          # Ripristina i dati salvati
        else:                                                                                   # Se è una nuova operazione
            self.imposta_z_da_fine_pezzo()                                                      # Imposta automaticamente Z alla fine del Pezzo 3D!
            self.on_tool_changed()                                                              # Eredita LarghezzaLamaGola, Vc e F dall'utensile scelto

        self.cycle_combo.currentIndexChanged.connect(self.aggiorna_ui_ciclo)                    # Collega cambio strategia
        self.tool_combo.currentIndexChanged.connect(self.on_tool_changed)                       # Collega cambio utensile
        self.lama_w_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio larghezza lama
        self.part_combo.currentIndexChanged.connect(self.imposta_z_da_fine_pezzo)               # Ricalcola Z quando cambia il Pezzo 3D
        self.z_cut_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio Z taglio live
        self.chk_comp_w.stateChanged.connect(self.trigger_update)                               # Collega spunta compensa spessore lama
        self.d_ext_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio Ø esterno
        self.r_end_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio raggio arrivo
        self.chamfer_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio smusso posteriore
        self.chk_slow.stateChanged.connect(self.aggiorna_ui_ciclo)                              # Collega spunta rallenta al centro
        self.d_slow_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio Ø rallentamento
        self.perc_slow_spin.valueChanged.connect(self.trigger_update)                           # Collega cambio % avanzamento ridotto
        self.chk_peck.stateChanged.connect(self.aggiorna_ui_ciclo)                              # Collega spunta Peck
        self.peck_q_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio passo Peck
        self.peck_ret_spin.valueChanged.connect(self.trigger_update)                            # Collega cambio ritrazione Peck
        self.feed_spin.valueChanged.connect(self.trigger_update)                                # Collega cambio avanzamento F

        self.is_updating = False                                                                # Sblocca gli aggiornamenti live
        self.aggiorna_ui_ciclo()                                                                # Adatta i controlli e disegna l'anteprima 3D

    def popola_combo_utensili(self, doc):                                                       # Carica gli utensili del Magazzino (selezionando quello da Troncatura/Gola)
        self.tool_combo.clear()                                                                 # Svuota il combo
        idx_part = -1                                                                           # Indice primo utensile da Troncatura/Gola trovato
        if doc and doc.getObject("Libreria_Utensili"):                                          # Se esiste il Magazzino Utensili
            lib = doc.getObject("Libreria_Utensili")                                            # Gruppo magazzino
            for i, t in enumerate(lib.Group):                                                   # Cicla sugli utensili
                st = getattr(t, "Stazione", "T01")                                              # Sigla stazione
                tipo_u = str(getattr(t, "TipoLavorazione", ""))                                 # Categoria utensile
                self.tool_combo.addItem(f"[{st}] {t.Label}", t.Name)                            # Aggiunge voce e Name interno
                if idx_part < 0 and ("Tronca" in tipo_u or "Gola" in tipo_u):                   # Se è un utensile da Gola / Troncatura
                    idx_part = i                                                                # Memorizza indice
        if idx_part >= 0:                                                                       # Se trovato
            self.tool_combo.setCurrentIndex(idx_part)                                           # Lo preseleziona

    def popola_combo_pezzi(self, doc):                                                          # Carica i solidi candidati a Pezzo Finito
        self.part_combo.clear()                                                                 # Svuota il combo
        candidati = LatheRoughing.trova_candidati_pezzo(doc)                                    # Trova i solidi 3D
        if candidati:                                                                           # Se ci sono solidi
            for p in candidati:                                                                 # Cicla sui solidi
                self.part_combo.addItem(p.Label, p.Name)                                        # Aggiunge etichetta e Name
        else:                                                                                   # Se non ci sono solidi 3D
            self.part_combo.addItem("(Nessun Pezzo 3D - Quota Manuale)", "")                    # Modalità manuale

    def imposta_z_da_fine_pezzo(self):                                                          # Posiziona Z Faccia Sinistra esattamente alla fine del Pezzo 3D
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc: return                                                                      # Controllo sicurezza
        p_name = self.part_combo.itemData(self.part_combo.currentIndex()) if self.part_combo.count() > 0 else ""
        part_obj = doc.getObject(p_name) if p_name else None                                    # Oggetto Pezzo 3D
        z_calc = LatheRoughing.calcola_z_fine_da_pezzo(part_obj, doc)                           # Fine esatta del pezzo (BoundBox.ZMin - WCS.z)
        prev = self.is_updating                                                                 # Salva stato semaforo
        self.is_updating = True                                                                 # Sospende segnali
        self.z_cut_spin.setValue(round(z_calc, 2))                                              # Imposta Z Faccia Sinistra
        self.is_updating = prev                                                                 # Ripristina semaforo
        self.trigger_update()                                                                   # Aggiorna il percorso 3D

    def cattura_faccia_posteriore_3d(self):                                                     # Rileva la quota Z di troncatura cliccando la faccia posteriore nel 3D
        sel_ex = FreeCADGui.Selection.getSelectionEx()                                          # Ottiene la selezione 3D
        if not sel_ex or not sel_ex[0].SubElementNames:                                         # Verifica selezione
            self.lbl_status.setText("Clicca prima sulla faccia posteriore del pezzo nel 3D!")
            return                                                                              # Esce
        sub_name = sel_ex[0].SubElementNames[0]                                                 # Sotto-elemento
        obj_sel = sel_ex[0].Object                                                              # Oggetto 3D
        elem = obj_sel.Shape.getElement(sub_name)                                               # Elemento geometrico
        wcs = LatheRoughing.get_wcs_origin(FreeCAD.ActiveDocument)                              # Origine WCS
        z_rel = elem.BoundBox.ZMin - wcs.z                                                      # Quota Z relativa al WCS

        self.is_updating = True                                                                 # Sospende segnali
        self.z_cut_spin.setValue(round(z_rel, 2))                                               # Imposta la quota Z rilevata
        self.is_updating = False                                                                # Sblocca
        FreeCADGui.Selection.clearSelection()                                                   # Pulisce la selezione
        self.lbl_status.setText(f"Piano di taglio catturato a Z = {z_rel:.2f} mm!")             # Conferma
        self.trigger_update()                                                                   # Aggiorna il 3D

    def on_tool_changed(self):                                                                  # Legge LarghezzaLamaGola, Vc e Avanzamento dall'utensile scelto
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc or self.tool_combo.count() == 0: return                                      # Verifica validità
        t_name = self.tool_combo.itemData(self.tool_combo.currentIndex())                       # Nome utensile
        t_obj = doc.getObject(t_name) if t_name else None                                       # Oggetto utensile
        if t_obj:                                                                               # Se esiste
            prev = self.is_updating                                                             # Salva stato semaforo
            self.is_updating = True                                                             # Sospende ricalcoli
            w_l = float(getattr(t_obj, "LarghezzaLamaGola", 3.0))                               # Legge larghezza lama
            self.lama_w_spin.setValue(max(w_l, 0.5))                                            # Imposta larghezza lama
            self.vc_spin.setValue(float(getattr(t_obj, "VelocitaTaglio", 110.0)))               # Legge Vc
            f_fin = float(getattr(t_obj, "AvanzamentoFinitura", 0.10))                          # Legge avanzamento
            self.feed_spin.setValue(round(max(f_fin * 0.8, 0.04), 3))                           # Imposta avanzamento di troncatura prudente
            self.is_updating = prev                                                             # Ripristina semaforo
            self.trigger_update()                                                               # Aggiorna l'anteprima

    def aggiorna_ui_ciclo(self):                                                                # Abilita/disabilita i controlli in base alla modalità scelta
        ciclo = self.cycle_combo.currentText()                                                  # Strategia selezionata
        ha_smusso = ("Smusso" in ciclo)                                                         # True se prevede smusso posteriore
        forza_peck = ("Peck" in ciclo)                                                          # True se è la strategia Peck G75

        self.chamfer_spin.setEnabled(ha_smusso)                                                 # Abilita campo smusso
        usa_p = forza_peck or self.chk_peck.isChecked()                                         # Verifica se peck attivo
        self.peck_q_spin.setEnabled(usa_p)                                                      # Abilita passo Q
        self.peck_ret_spin.setEnabled(usa_p)                                                    # Abilita ritrazione

        usa_s = self.chk_slow.isChecked()                                                       # Verifica se rallentamento al centro attivo
        self.d_slow_spin.setEnabled(usa_s)                                                      # Abilita diametro inizio rallentamento
        self.perc_slow_spin.setEnabled(usa_s)                                                   # Abilita % avanzamento ridotto
        self.trigger_update()                                                                   # Aggiorna il 3D

    def trigger_update(self, *args):                                                            # Aggiorna in tempo reale il tracciato 3D della troncatura
        if self.is_updating: return                                                             # Se bloccato esce
        self.is_updating = True                                                                 # Attiva semaforo
        try:                                                                                    # Blocco di calcolo
            doc = FreeCAD.ActiveDocument                                                        # Documento attivo
            if not doc or not self.preview_rapidi or not self.preview_lavoro: return            # Verifica validità
            wcs = LatheRoughing.get_wcs_origin(doc)                                             # Origine WCS
            sic_x, sic_z = LatheRoughing.get_setup_safe_clearances(doc)                         # Sicurezze Setup
            stock_info = LatheRoughing.get_stock_info(doc)                                      # Dati Grezzo e limite griffe

            _, c_rap, c_lav, moves, z_eff = calcola_percorso_troncatura(                        # Calcola il percorso
                wcs, self.cycle_combo.currentText(), stock_info,
                self.z_cut_spin.value(), self.lama_w_spin.value(), self.chk_comp_w.isChecked(),
                self.d_ext_spin.value(), self.r_end_spin.value(), self.chamfer_spin.value(),
                self.chk_peck.isChecked(), self.peck_q_spin.value(), self.peck_ret_spin.value(),
                self.chk_slow.isChecked(), self.d_slow_spin.value(), self.perc_slow_spin.value(),
                sic_x, sic_z, self.feed_spin.value()
            )                                                                                   # Fine calcolo

            self.preview_rapidi.Shape = c_rap if c_rap else Part.Shape()                        # Aggiorna i rapidi rossi
            self.preview_lavoro.Shape = c_lav if c_lav else Part.Shape()                        # Aggiorna il taglio cremisi/borgogna

            w_off = self.lama_w_spin.value() if self.chk_comp_w.isChecked() else 0.0            # Spazio occupato a sinistra dalla lama
            z_sx_richiesta = self.z_cut_spin.value() - w_off                                    # Quota del fianco sinistro lama
            if z_sx_richiesta < stock_info["z_lim_chuck"]:                                      # Se il fianco sinistro lama tocca le griffe
                self.lbl_status.setStyleSheet("color: #FF5555; font-weight: bold;")
                self.lbl_status.setText(f"ALLARME GRIFFE: Taglio spostato a Z={z_eff:.2f} mm per salvare la lama!")
            else:                                                                               # Tutto OK
                self.lbl_status.setStyleSheet("color: #FF4D79; font-weight: bold;")
                self.lbl_status.setText(f"Troncatura OK a Z={z_eff:.2f} mm (Lato Sx lama a Z={z_eff - w_off:.2f} mm).")

            doc.recompute()                                                                     # Rinfresca la scena 3D
        finally:                                                                                # Rilascia semaforo
            self.is_updating = False                                                            # Fine aggiornamento

    def carica_dati_da_oggetto(self, obj):                                                      # Popola la UI quando si riapre un'operazione con doppio click
        obj.Proxy.ensure_properties(obj)                                                        # Verifica proprietà
        self.name_input.setText(str(getattr(obj, "OperationName", obj.Label)))                  # Nome
        if str(obj.TipoCiclo) in TIPI_CICLO_TRONCATURA:                                         # Strategia
            self.cycle_combo.setCurrentText(str(obj.TipoCiclo))
        idx_t = self.tool_combo.findData(str(getattr(obj, "UtensileAssegnato", "")))            # Utensile
        if idx_t >= 0: self.tool_combo.setCurrentIndex(idx_t)
        self.lama_w_spin.setValue(float(getattr(obj, "LarghezzaLama", 3.0)))                    # Larghezza lama
        idx_p = self.part_combo.findData(str(getattr(obj, "PezzoRiferimento", "")))             # Pezzo 3D
        if idx_p >= 0: self.part_combo.setCurrentIndex(idx_p)
        self.z_cut_spin.setValue(float(getattr(obj, "Z_PianoTaglio", -50.0)))                   # Z Piano Taglio
        self.chk_comp_w.setChecked(bool(getattr(obj, "CompensaSpessoreLama", True)))            # Compensa spessore lama
        self.d_ext_spin.setValue(float(getattr(obj, "DiametroEsterno", 50.0)))                  # Ø Esterno
        self.r_end_spin.setValue(float(getattr(obj, "QuotaOltreCentro", -0.5)))                 # Raggio arrivo oltre centro
        self.chamfer_spin.setValue(float(getattr(obj, "SmussoPosteriore", 0.5)))                # Smusso posteriore
        self.chk_peck.setChecked(bool(getattr(obj, "UsaScaricoTruciolo", False)))               # Usa Peck
        self.peck_q_spin.setValue(float(getattr(obj, "PassoPeck", 3.0)))                        # Passo Peck Q
        self.peck_ret_spin.setValue(float(getattr(obj, "RitrazionePeck", 0.3)))                 # Ritrazione Peck
        self.chk_slow.setChecked(bool(getattr(obj, "RallentaAlCentro", True)))                  # Rallenta al centro
        self.d_slow_spin.setValue(float(getattr(obj, "DiametroInizioRallentamento", 8.0)))      # Ø Inizio rallentamento
        self.perc_slow_spin.setValue(float(getattr(obj, "PercAvanzamentoRidotto", 40.0)))       # % Avanzamento ridotto
        self.vc_spin.setValue(float(getattr(obj, "VelocitaTaglio", 110.0)))                     # Velocità Vc
        self.feed_spin.setValue(float(getattr(obj, "AvanzamentoLavoro", 0.08)))                 # Avanzamento F

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
            if obj.Name.startswith("TMP_Parting_"):
                try: doc.removeObject(obj.Name)
                except Exception: pass

    def getStandardButtons(self):                                                               # Pulsanti OK e Cancel
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel                # Restituisce OK | Cancel

    def accept(self):                                                                           # Conferma e salva l'operazione di Troncatura in Operazioni_CAM
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc: return False                                                                # Controllo sicurezza

        ops_group = doc.getObject("Operazioni_CAM")                                             # Cerca il gruppo Operazioni_CAM
        if not ops_group:                                                                       # Se non esiste lo crea
            ops_group = doc.addObject("App::DocumentObjectGroup", "Operazioni_CAM")
            ops_group.Label = "Operazioni CAM (Cicli Tornio)"

        nome_op = self.name_input.text().strip() or "Troncatura Finale"                         # Nome operazione
        if self.edit_obj and doc.getObject(self.edit_obj.Name):                                 # Se siamo in modifica
            op_obj = self.edit_obj                                                              # Riutilizza l'oggetto esistente
        else:                                                                                   # Altrimenti crea il nuovo oggetto parametrico
            op_obj = doc.addObject("Part::FeaturePython", "Op_Troncatura")                      # Crea Part::FeaturePython
            LathePartingObject(op_obj)                                                          # Inizializza Proxy
            ViewProviderLatheParting(op_obj.ViewObject)                                         # Inizializza ViewProvider
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
            op_obj.LarghezzaLama = self.lama_w_spin.value()
            op_obj.PezzoRiferimento = str(p_name or "")
            op_obj.Z_PianoTaglio = self.z_cut_spin.value()
            op_obj.CompensaSpessoreLama = self.chk_comp_w.isChecked()
            op_obj.DiametroEsterno = self.d_ext_spin.value()
            op_obj.QuotaOltreCentro = self.r_end_spin.value()
            op_obj.SmussoPosteriore = self.chamfer_spin.value()
            op_obj.UsaScaricoTruciolo = self.chk_peck.isChecked()
            op_obj.PassoPeck = self.peck_q_spin.value()
            op_obj.RitrazionePeck = self.peck_ret_spin.value()
            op_obj.RallentaAlCentro = self.chk_slow.isChecked()
            op_obj.DiametroInizioRallentamento = self.d_slow_spin.value()
            op_obj.PercAvanzamentoRidotto = self.perc_slow_spin.value()
            op_obj.VelocitaTaglio = self.vc_spin.value()
            op_obj.AvanzamentoLavoro = self.feed_spin.value()
        finally:                                                                                # Sblocca Proxy
            op_obj.Proxy._is_executing = False

        op_obj.Proxy.execute(op_obj)                                                            # Calcola e disegna il percorso finale
        if hasattr(op_obj, "ViewObject") and op_obj.ViewObject:
            op_obj.ViewObject.Visibility = True                                                 # Mostra il percorso cremisi/borgogna nel 3D

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