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


TIPI_CICLO_FORATURA = [                                                                         # Modalità operative supportate dal ciclo di foratura/maschiatura
    "1. Centrino / Foratura Diretta (G81)",                                                     # Avanzamento continuo in asse Z
    "2. Foratura Profonda con Scarico Truciolo (G83 - Peck)",                                   # Scarico completo truciolo fuori dal foro
    "3. Foratura Rompitruciolo (G73 - Chip Break)",                                             # Rompitruciolo parziale senza uscita dal foro
    "4. Maschiatura Rigida Assiale (G84)"                                                       # Maschiatura sincronizzata con passo F
]                                                                                               # Fine elenco cicli


def calcola_percorso_foratura(                                                                  # Genera la lista movimenti (G0/G1) e le Shapes 3D della foratura
    wcs, tipo_ciclo, stock_info,                                                                # Riferimenti base
    z_start, z_fondo, diametro_punta, comp_cono,                                                # Quote e compensazione cono punta
    usa_peck, passo_peck, ritrazione_peck, passo_maschio,                                       # Parametri peck e maschiatura
    sic_x, sic_z, feed_lavoro                                                                   # Sicurezze e avanzamento
):                                                                                              # Inizio motore di calcolo percorso foratura
    moves = []                                                                                  # Lista movimenti: {"cmd": "G0"/"G1", "x": r, "z": z, "f": feed}
    edges_rapidi = []                                                                           # Segmenti 3D per i movimenti rapidi G00 (Rosso)
    edges_lavoro = []                                                                           # Segmenti 3D per i movimenti di taglio G01 (Arancione Corallo)

    z_ini = float(z_start)                                                                      # Quota Z di partenza frontale (es. 2.0 mm davanti al pezzo)
    z_f = float(z_fondo)                                                                        # Quota Z nominale del fondo foro richiesta
    d_tool = max(float(diametro_punta), 1.0)                                                    # Diametro della punta o del maschio (mm)
    p_maschio = max(float(passo_maschio), 0.1)                                                  # Passo del maschio (mm/giro) per G84
    peck_q = max(float(passo_peck), 0.2)                                                        # Incremento di affondamento peck (mm)
    peck_ret = max(float(ritrazione_peck), 0.1)                                                 # Ritrazione rompi-truciolo (mm)

    is_tapping = ("Maschiatura" in tipo_ciclo)                                                  # True se è un ciclo di maschiatura G84
    feed_eff = p_maschio if is_tapping else max(float(feed_lavoro), 0.02)                       # Per maschiatura l'avanzamento F è esattamente il passo!

    h_cono = (d_tool / 2.0) / math.tan(math.radians(118.0 / 2.0)) if comp_cono else 0.0           # Altezza del cono punta a 118° (circa 0.3 * D)
    z_fondo_effettivo = z_f - h_cono                                                            # Quota Z reale raggiunta dal vertice della punta per avere foro cilindrico a z_f

    z_lim_griffe = stock_info["z_lim_chuck"]                                                    # Quota Z limite collisione griffe mandrino
    if z_fondo_effettivo < z_lim_griffe:                                                        # Controllo di sicurezza anti-collisione con le griffe
        z_fondo_effettivo = z_lim_griffe                                                        # Blocca al limite griffe

    safe_z_front = max(stock_info["z_front"], z_ini) + max(float(sic_z), 2.0)                   # Quota Z di sicurezza frontale

    curr_pt = [0.0, safe_z_front]                                                               # Posizione iniziale in asse mandrino (X = 0)
    moves.append({"cmd": "G0", "x": curr_pt[0], "z": curr_pt[1], "f": 0.0})                     # Punto iniziale in sicurezza

    def add_segment(cmd, next_r, next_z, f_val=0.0):                                            # Funzione interna per registrare un movimento e creare la linea 3D
        p1 = FreeCAD.Vector(wcs.x + curr_pt[0], wcs.y, wcs.z + curr_pt[1])                      # Punto 3D partenza sul piano XZ
        p2 = FreeCAD.Vector(wcs.x + next_r, wcs.y, wcs.z + next_z)                              # Punto 3D arrivo sul piano XZ
        if (p2 - p1).Length > 1e-4:                                                             # Se lo spostamento è reale
            edge = Part.makeLine(p1, p2)                                                        # Crea il segmento 3D
            if cmd == "G0":                                                                     # Movimento rapido
                edges_rapidi.append(edge)                                                       # Aggiunge ai rapidi
            else:                                                                               # Movimento di foratura/maschiatura in lavoro
                edges_lavoro.append(edge)                                                       # Aggiunge al lavoro
            moves.append({                                                                      # Registra il dizionario movimento
                "cmd": cmd,
                "x": float(next_r),
                "z": float(next_z),
                "f": float(f_val if cmd == "G1" else 0.0)
            })                                                                                  # Fine record
            curr_pt[0] = float(next_r)                                                          # Aggiorna X corrente
            curr_pt[1] = float(next_z)                                                          # Aggiorna Z corrente

    add_segment("G0", 0.0, z_ini)                                                               # Posizionamento rapido in asse (X=0) davanti al pezzo

    if "Foratura Diretta" in tipo_ciclo:                                                        # 1. CICLO G81: FORATURA DIRETTA CONTINUA
        add_segment("G1", 0.0, z_fondo_effettivo, feed_eff)                                     # Affondo in G01 fino al fondo del foro
        add_segment("G0", 0.0, safe_z_front)                                                    # Ritorno rapido in sicurezza

    elif "Scarico Truciolo" in tipo_ciclo:                                                      # 2. CICLO G83: PECKING CON USCITA FUORI DAL FORO
        z_curr = z_ini                                                                          # Quota Z di partenza corrente
        while z_curr > z_fondo_effettivo + 1e-4:                                                # Cicla finché non raggiunge il fondo
            z_next = max(z_curr - peck_q, z_fondo_effettivo)                                    # Quota del peck corrente
            add_segment("G1", 0.0, z_next, feed_eff)                                            # Affonda di un incremento Q
            if z_next > z_fondo_effettivo + 1e-4:                                               # Se non è ancora in fondo
                add_segment("G0", 0.0, safe_z_front)                                            # Esce completamente dal foro in rapido per scaricare il truciolo
                add_segment("G0", 0.0, z_curr - 0.2)                                            # Rientra in rapido a 0.2 mm dal fondo precedentemente raggiunto
            z_curr = z_next                                                                     # Aggiorna la quota raggiunta
        add_segment("G0", 0.0, safe_z_front)                                                    # Ritorno finale in sicurezza

    elif "Rompitruciolo" in tipo_ciclo:                                                         # 3. CICLO G73: ROMBITRUCIOLO PARZIALE
        z_curr = z_ini                                                                          # Quota Z di partenza
        while z_curr > z_fondo_effettivo + 1e-4:                                                # Cicla fino al fondo
            z_next = max(z_curr - peck_q, z_fondo_effettivo)                                    # Quota del peck
            add_segment("G1", 0.0, z_next, feed_eff)                                            # Affonda di Q
            if z_next > z_fondo_effettivo + 1e-4:                                               # Se non è in fondo
                add_segment("G0", 0.0, min(z_next + ritrazione_peck, safe_z_front))               # Arretra di pochi decimi per spezzare il truciolo
                add_segment("G0", 0.0, z_next)                                                  # Riprende il taglio
            z_curr = z_next                                                                     # Aggiorna quota
        add_segment("G0", 0.0, safe_z_front)                                                    # Ritorno finale in sicurezza

    elif "Maschiatura" in tipo_ciclo:                                                           # 4. CICLO G84: MASCHIATURA RIGIDA ASSIALE SINCRONIZZATA
        add_segment("G1", 0.0, z_fondo_effettivo, feed_eff)                                     # Entra in maschiatura con avanzamento pari al passo
        # Per la retromarcia del maschio (inversione mandrino M04), generiamo il movimento G1 in salita:
        add_segment("G1", 0.0, safe_z_front, feed_eff)                                          # Svitamento sincronizzato del maschio fuori dal foro

    shapes_all = []                                                                             # Lista globale dei segmenti 3D
    if edges_rapidi: shapes_all.extend(edges_rapidi)                                            # Unisce i rapidi
    if edges_lavoro:                                                                            # Se ci sono movimenti di lavoro
        shapes_all.extend(edges_lavoro)                                                         # Aggiunge i segmenti di taglio
        # Aggiunge un cerchietto sul fondo del foro per evidenziare il diametro forato nel 3D:
        p_fondo_3d = FreeCAD.Vector(wcs.x, wcs.y, wcs.z + z_fondo_effettivo)
        c_fondo = Part.makeCircle(d_tool / 2.0, p_fondo_3d, FreeCAD.Vector(0, 0, 1))
        shapes_all.append(c_fondo)

    comp = Part.makeCompound(shapes_all) if shapes_all else Part.makeSphere(0.5, wcs)           # Compound finale dell'operazione
    comp_rapidi = Part.makeCompound(edges_rapidi) if edges_rapidi else None                     # Compound rapidi per anteprima rossa
    comp_lavoro = Part.makeCompound(edges_lavoro) if edges_lavoro else None                     # Compound lavoro per anteprima arancione corallo
    return comp, comp_rapidi, comp_lavoro, moves, z_fondo_effettivo                             # Restituisce geometrie, punti e Z effettiva


class LatheDrillingObject:                                                                      # Classe Proxy per l'operazione parametrica di Foratura
    def __init__(self, obj):                                                                    # Costruttore del Proxy
        self._is_executing = False                                                              # Semaforo anti-ricorsione
        self.ensure_properties(obj)                                                             # Garantisce la creazione di tutte le proprietà
        obj.Proxy = self                                                                        # Collega il Proxy all'oggetto FreeCAD

    def ensure_properties(self, obj):                                                           # Aggiunge le proprietà native se mancanti
        if not hasattr(obj, "OperationName"):                                                   # Nome operazione
            obj.addProperty("App::PropertyString", "OperationName", "Operazione", "Nome operazione").OperationName = "Foratura Diametro 10"
        if not hasattr(obj, "TipoCiclo"):                                                       # Ciclo di foratura / maschiatura
            obj.addProperty("App::PropertyEnumeration", "TipoCiclo", "Operazione", "Tipologia ciclo di foratura")
            obj.TipoCiclo = TIPI_CICLO_FORATURA                                                 # Assegna le 4 modalità
        if not hasattr(obj, "UtensileAssegnato"):                                               # Utensile selezionato dal Magazzino
            obj.addProperty("App::PropertyString", "UtensileAssegnato", "Operazione", "Utensile punta/maschio utilizzato").UtensileAssegnato = ""
        if not hasattr(obj, "DiametroPunta"):                                                   # Diametro dell'utensile (mm)
            obj.addProperty("App::PropertyFloat", "DiametroPunta", "Geometria Foro", "Diametro punta o maschio (mm)").DiametroPunta = 10.0
        if not hasattr(obj, "CompensaCono"):                                                    # Compensa l'altezza del cono a 118° (+0.3 * D)
            obj.addProperty("App::PropertyBool", "CompensaCono", "Geometria Foro", "Compensa cono punta 118° (+0.3*D)").CompensaCono = True
        if not hasattr(obj, "Z_Inizio"):                                                        # Quota Z di avvicinamento frontale (mm)
            obj.addProperty("App::PropertyFloat", "Z_Inizio", "Geometria Foro", "Quota Z di approccio iniziale (mm)").Z_Inizio = 2.0
        if not hasattr(obj, "Z_Fondo"):                                                         # Quota Z del fondo del foro (mm)
            obj.addProperty("App::PropertyFloat", "Z_Fondo", "Geometria Foro", "Quota Z fondo foro (mm)").Z_Fondo = -35.0
        if not hasattr(obj, "UsaPeck"):                                                         # Attiva il ciclo di pecking o chip-break
            obj.addProperty("App::PropertyBool", "UsaPeck", "Parametri Taglio", "Abilita ciclo di beccheggio (Peck/Chip Break)").UsaPeck = True
        if not hasattr(obj, "PassoPeck"):                                                       # Incremento per ogni peck Q (mm)
            obj.addProperty("App::PropertyFloat", "PassoPeck", "Parametri Taglio", "Incremento affondamento peck Q (mm)").PassoPeck = 3.0
        if not hasattr(obj, "RitrazionePeck"):                                                  # Ritrazione rompitruciolo (mm)
            obj.addProperty("App::PropertyFloat", "RitrazionePeck", "Parametri Taglio", "Ritrazione rompi-truciolo (mm)").RitrazionePeck = 0.5
        if not hasattr(obj, "PassoMaschio"):                                                    # Passo del maschio per G84 (mm/giro)
            obj.addProperty("App::PropertyFloat", "PassoMaschio", "Parametri Taglio", "Passo del maschio per G84 (mm/giro)").PassoMaschio = 1.5
        if not hasattr(obj, "VelocitaTaglio"):                                                  # Velocità di taglio Vc o RPM
            obj.addProperty("App::PropertyFloat", "VelocitaTaglio", "Parametri Taglio", "Velocità di taglio Vc / RPM").VelocitaTaglio = 60.0
        if not hasattr(obj, "AvanzamentoLavoro"):                                               # Avanzamento di foratura (mm/giro)
            obj.addProperty("App::PropertyFloat", "AvanzamentoLavoro", "Parametri Taglio", "Avanzamento di lavoro F (mm/giro)").AvanzamentoLavoro = 0.15
        if not hasattr(obj, "PercorsoJSON"):                                                    # Punti del percorso salvati per Simulatore e G-Code
            obj.addProperty("App::PropertyString", "PercorsoJSON", "Dati CAM", "Punti percorso per Simulatore e G-Code").PercorsoJSON = "[]"

    def onDocumentRestored(self, obj):                                                          # Chiamato alla riapertura del documento
        self._is_executing = False                                                              # Sblocca il flag
        self.ensure_properties(obj)                                                             # Verifica le proprietà

    def execute(self, obj):                                                                     # Ricalcola il percorso 3D della foratura
        if getattr(self, "_is_executing", False):                                               # Evita loop ricorsivi
            return                                                                              # Esce subito
        self._is_executing = True                                                               # Attiva il semaforo
        try:                                                                                    # Blocco protetto di calcolo
            self.ensure_properties(obj)                                                         # Verifica attributi
            doc = obj.Document                                                                  # Documento corrente
            wcs = LatheRoughing.get_wcs_origin(doc)                                             # Origine WCS
            sic_x, sic_z = LatheRoughing.get_setup_safe_clearances(doc)                         # Sicurezze Setup
            stock_info = LatheRoughing.get_stock_info(doc)                                      # Dati Grezzo e limite griffe

            comp, _, _, moves, _ = calcola_percorso_foratura(                                   # Genera il percorso della foratura
                wcs, str(obj.TipoCiclo), stock_info,
                obj.Z_Inizio, obj.Z_Fondo, obj.DiametroPunta, obj.CompensaCono,
                obj.UsaPeck, obj.PassoPeck, obj.RitrazionePeck, obj.PassoMaschio,
                sic_x, sic_z, obj.AvanzamentoLavoro
            )                                                                                   # Fine calcolo
            obj.PercorsoJSON = json.dumps(moves)                                                # Salva il percorso per il Simulatore e il Post-Processor
            obj.Shape = comp                                                                    # Assegna la Shape 3D
            if hasattr(obj, "ViewObject") and obj.ViewObject:                                   # Colora il tracciato in Arancione Corallo brillante
                obj.ViewObject.LineColor = (1.00, 0.45, 0.10)                                   # Arancione Corallo per la foratura
                obj.ViewObject.LineWidth = 2.5                                                  # Spessore linea
        except Exception as e:                                                                  # Cattura errori imprevisti
            FreeCAD.Console.PrintError(f"Errore calcolo Foratura: {e}\n")                       # Stampa in console
        finally:                                                                                # Rilascia il semaforo
            self._is_executing = False                                                          # Fine esecuzione

    def onChanged(self, obj, prop):                                                             # Intercetta modifiche live dalle Proprietà di FreeCAD
        if getattr(self, "_is_executing", False):                                               # Evita ricorsioni
            return                                                                              # Esce
        props_calcolo = [                                                                       # Proprietà che rigenerano il percorso
            "TipoCiclo", "DiametroPunta", "CompensaCono", "Z_Inizio", "Z_Fondo",                  # Quote e geometria
            "UsaPeck", "PassoPeck", "RitrazionePeck", "PassoMaschio", "AvanzamentoLavoro"         # Parametri di taglio
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


class ViewProviderLatheDrilling:                                                                # ViewProvider per icona e doppio click sull'operazione di Foratura
    def __init__(self, vobj):                                                                   # Costruttore ViewProvider
        vobj.Proxy = self                                                                       # Collega il Proxy

    def getIcon(self):                                                                          # Icona nell'albero delle operazioni
        return LatheResources.get_icon_path("lathe_drilling.svg", "Part_Cone")                  # Icona SVG dedicata Foratura

    def attach(self, vobj):                                                                     # Collega gli oggetti alla vista
        self.ViewObject = vobj                                                                  # Riferimento ViewObject
        self.Object = vobj.Object                                                               # Riferimento Object

    def updateData(self, vobj, prop):                                                           # Aggiornamento dati
        return                                                                                  # Gestito da execute

    def onDelete(self, vobj, subelements):                                                      # Autorizza cancellazione
        return True                                                                             # Sempre consentito

    def doubleClicked(self, vobj):                                                              # Doppio click sull'operazione nell'albero
        if not FreeCADGui.Control.activeDialog():                                               # Se non c'è già un pannello aperto
            panel = LatheDrillingPanel(edit_obj=vobj.Object)                                    # Apre il pannello caricando l'operazione
            FreeCADGui.Control.showDialog(panel)                                                # Mostra nella scheda Azioni
        return True                                                                             # Evento gestito

    def setEdit(self, vobj, mode):                                                              # Modalità Edit standard
        if mode == 0:                                                                           # Modifica base
            if not FreeCADGui.Control.activeDialog():                                           # Evita doppia apertura
                panel = LatheDrillingPanel(edit_obj=vobj.Object)                                # Crea il pannello
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


class LatheDrillingPanel:                                                                       # Pannello Task per programmare il ciclo di Foratura e Maschiatura
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

        self.grp_gen = QtWidgets.QGroupBox("Operazione e Scelta Utensile (Punta / Maschio)")    # Gruppo dati generali
        self.lyt_gen = QtWidgets.QFormLayout(self.grp_gen)                                      # Form layout

        self.name_input = QtWidgets.QLineEdit("Foratura Diametro 10")                           # Nome operazione
        self.cycle_combo = QtWidgets.QComboBox()                                                # Scelta ciclo (G81, G83, G73, G84)
        self.cycle_combo.addItems(TIPI_CICLO_FORATURA)                                          # Popola le 4 modalità
        self.cycle_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cycle_combo.setMinimumContentsLength(10)

        self.tool_combo = QtWidgets.QComboBox()                                                 # Scelta utensile dal Magazzino Utensili
        self.tool_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.tool_combo.setMinimumContentsLength(10)
        self.popola_combo_utensili(doc)                                                         # Carica gli utensili (preferendo punte e maschi)

        self.tool_d_spin = QtWidgets.QDoubleSpinBox()                                           # Diametro della punta/maschio (mm)
        self.tool_d_spin.setRange(0.5, 200.0); self.tool_d_spin.setDecimals(2); self.tool_d_spin.setValue(10.0); self.tool_d_spin.setSingleStep(0.5)

        self.lyt_gen.addRow("Nome:", self.name_input)                                           # Riga Nome
        self.lyt_gen.addRow("Strategia:", self.cycle_combo)                                     # Riga Strategia
        self.lyt_gen.addRow("Utensile:", self.tool_combo)                                       # Riga Utensile
        self.lyt_gen.addRow("Diametro Utensile (mm):", self.tool_d_spin)                        # Riga Diametro Utensile
        self.layout.addWidget(self.grp_gen)                                                     # Aggiunge al layout principale

        self.tabs = QtWidgets.QTabWidget()                                                      # Schede: 1. Geometria Foro | 2. Pecking & Taglio

        self.tab_geo = QtWidgets.QWidget()                                                      # SCHEDA 1: Quote e Profondità del Foro Assiale
        self.lyt_geo = QtWidgets.QVBoxLayout(self.tab_geo)                                      # Layout verticale Scheda 1

        self.grp_geo = QtWidgets.QGroupBox("Profondità e Posizione in Asse (X = 0)")            # Gruppo quote foro
        self.lyt_g_form = QtWidgets.QFormLayout(self.grp_geo)                                   # Form layout

        self.btn_pick_hole = QtWidgets.QPushButton("Cattura Profondità Foro da Faccia 3D")      # Rileva Z inizio e Z fondo cliccando il foro nel 3D
        self.btn_pick_hole.clicked.connect(self.cattura_foro_da_faccia_3d)                      # Collega la cattura 3D

        self.chk_cone = QtWidgets.QCheckBox("Compensa Cono Punta 118° (+0.3 * D)")              # Compensa automaticamente l'altezza della cuspide
        self.chk_cone.setChecked(True)                                                          # Attivo di default

        self.z_start_spin = QtWidgets.QDoubleSpinBox(); self.z_start_spin.setRange(-2000, 2000); self.z_start_spin.setDecimals(2); self.z_start_spin.setValue(2.0)
        self.z_fondo_spin = QtWidgets.QDoubleSpinBox(); self.z_fondo_spin.setRange(-2000, 2000); self.z_fondo_spin.setDecimals(2); self.z_fondo_spin.setValue(-35.0)

        self.lbl_status = QtWidgets.QLabel("Pronto. Clicca un foro nel 3D o imposta le quote.")
        self.lbl_status.setWordWrap(True)                                                       # Va a capo automaticamente
        self.lbl_status.setStyleSheet("color: #FF7700; font-weight: bold;")                     # Arancione

        self.lyt_g_form.addRow(self.btn_pick_hole)                                              # Riga pulsante cattura foro 3D
        self.lyt_g_form.addRow(self.chk_cone)                                                   # Riga checkbox cono punta 118°
        self.lyt_g_form.addRow("Z Inizio Approccio (mm):", self.z_start_spin)                   # Riga Z Inizio
        self.lyt_g_form.addRow("Z Fondo Foro (mm):", self.z_fondo_spin)                         # Riga Z Fondo
        self.lyt_g_form.addRow(self.lbl_status)                                                 # Riga stato
        self.lyt_geo.addWidget(self.grp_geo)                                                    # Aggiunge alla Scheda 1

        self.tabs.addTab(self.tab_geo, "1. Geometria")                                          # Titolo Scheda 1

        self.tab_cut = QtWidgets.QWidget()                                                      # SCHEDA 2: Parametri di Pecking e Maschiatura
        self.lyt_cut = QtWidgets.QVBoxLayout(self.tab_cut)                                      # Layout verticale Scheda 2

        self.grp_cut = QtWidgets.QGroupBox("Parametri di Beccheggio (Peck) e Maschiatura")      # Gruppo parametri
        self.lyt_c_form = QtWidgets.QFormLayout(self.grp_cut)                                   # Form layout

        self.chk_peck = QtWidgets.QCheckBox("Abilita Ciclo di Beccheggio (Peck)")               # Attiva il pecking G83/G73
        self.chk_peck.setChecked(True)                                                          # Attivo di default
        self.peck_q_spin = QtWidgets.QDoubleSpinBox(); self.peck_q_spin.setRange(0.2, 50.0); self.peck_q_spin.setDecimals(2); self.peck_q_spin.setValue(3.0); self.peck_q_spin.setSingleStep(0.5)
        self.peck_ret_spin = QtWidgets.QDoubleSpinBox(); self.peck_ret_spin.setRange(0.05, 10.0); self.peck_ret_spin.setDecimals(2); self.peck_ret_spin.setValue(0.5); self.peck_ret_spin.setSingleStep(0.1)
        self.pitch_tap_spin = QtWidgets.QDoubleSpinBox(); self.pitch_tap_spin.setRange(0.2, 20.0); self.pitch_tap_spin.setDecimals(3); self.pitch_tap_spin.setValue(1.5); self.pitch_tap_spin.setSingleStep(0.25)

        self.vc_spin = QtWidgets.QDoubleSpinBox(); self.vc_spin.setRange(1.0, 15000.0); self.vc_spin.setValue(60.0); self.vc_spin.setSingleStep(10.0)
        self.feed_spin = QtWidgets.QDoubleSpinBox(); self.feed_spin.setRange(0.01, 5.0); self.feed_spin.setDecimals(3); self.feed_spin.setValue(0.15); self.feed_spin.setSingleStep(0.05)

        self.lyt_c_form.addRow(self.chk_peck)                                                   # Riga checkbox Peck
        self.lyt_c_form.addRow("Incremento Peck Q (mm):", self.peck_q_spin)                     # Riga passo Peck Q
        self.lyt_c_form.addRow("Ritrazione Peck (mm):", self.peck_ret_spin)                     # Riga ritrazione Peck
        self.lyt_c_form.addRow("Passo Maschio G84 (mm/g):", self.pitch_tap_spin)                 # Riga passo maschio
        self.lyt_c_form.addRow("Velocità Vc / RPM:", self.vc_spin)                              # Riga velocità Vc
        self.lyt_c_form.addRow("Avanzamento F (mm/g):", self.feed_spin)                         # Riga avanzamento F
        self.lyt_cut.addWidget(self.grp_cut)                                                    # Aggiunge alla Scheda 2
        self.lyt_cut.addStretch()                                                               # Allinea in alto

        self.tabs.addTab(self.tab_cut, "2. Parametri")                                          # Titolo Scheda 2
        self.layout.addWidget(self.tabs)                                                        # Aggiunge il TabWidget al layout principale
        self.form.setLayout(self.layout)                                                        # Applica il layout

        self.preview_rapidi = doc.addObject("Part::Feature", "TMP_Drill_Rapids")                # Oggetto temporaneo per i rapidi G00 (Rosso)
        self.preview_rapidi.Label = "ANTEPRIMA RAPIDI FORATURA"                                 # Etichetta
        self.preview_rapidi.ViewObject.LineColor = (0.95, 0.20, 0.20)                           # Rosso per i rapidi
        self.preview_rapidi.ViewObject.LineWidth = 1.5                                          # Spessore linea rapidi

        self.preview_lavoro = doc.addObject("Part::Feature", "TMP_Drill_Cut")                   # Oggetto temporaneo per i tagli G01 (Arancione Corallo)
        self.preview_lavoro.Label = "ANTEPRIMA TAGLIO FORATURA"                                 # Etichetta
        self.preview_lavoro.ViewObject.LineColor = (1.00, 0.45, 0.10)                           # Arancione Corallo per la foratura
        self.preview_lavoro.ViewObject.LineWidth = 2.5                                          # Spessore linea lavoro

        if self.edit_obj:                                                                       # Se siamo in modifica di un'operazione esistente
            self.carica_dati_da_oggetto(self.edit_obj)                                          # Ripristina i dati salvati
        else:                                                                                   # Se è una nuova operazione
            self.on_tool_changed()                                                              # Eredita Diametro e Vc dall'utensile scelto

        self.cycle_combo.currentIndexChanged.connect(self.aggiorna_ui_ciclo)                    # Collega cambio ciclo
        self.tool_combo.currentIndexChanged.connect(self.on_tool_changed)                       # Collega cambio utensile
        self.tool_d_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio diametro utensile
        self.chk_cone.stateChanged.connect(self.trigger_update)                                 # Collega spunta cono punta
        
        self.z_start_spin.valueChanged.connect(self.trigger_update)                             # [AGGIUNTO] Collega cambio Z inizio live
        self.z_fondo_spin.valueChanged.connect(self.trigger_update)                             # [AGGIUNTO] Collega cambio Z fondo live

        self.chk_peck.stateChanged.connect(self.aggiorna_ui_ciclo)                              # Collega spunta Peck
        self.peck_q_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio passo Peck
        self.peck_ret_spin.valueChanged.connect(self.trigger_update)                            # Collega cambio ritrazione Peck
        self.pitch_tap_spin.valueChanged.connect(self.trigger_update)                           # Collega cambio passo maschio
        self.feed_spin.valueChanged.connect(self.trigger_update)                                # Collega cambio avanzamento F

        self.is_updating = False                                                                # Sblocca gli aggiornamenti live
        self.aggiorna_ui_ciclo()                                                                # Adatta l'interfaccia e disegna l'anteprima 3D

    def popola_combo_utensili(self, doc):                                                       # Carica gli utensili del Magazzino (preferendo Punte e Maschi)
        self.tool_combo.clear()                                                                 # Svuota il combo
        idx_drill = -1                                                                          # Indice primo utensile da foratura trovato
        if doc and doc.getObject("Libreria_Utensili"):                                          # Se esiste il Magazzino Utensili
            lib = doc.getObject("Libreria_Utensili")                                            # Gruppo magazzino
            for i, t in enumerate(lib.Group):                                                   # Cicla sugli utensili
                st = getattr(t, "Stazione", "T01")                                              # Sigla stazione
                tipo_u = str(getattr(t, "TipoLavorazione", ""))                                 # Categoria utensile
                self.tool_combo.addItem(f"[{st}] {t.Label}", t.Name)                            # Aggiunge voce e Name interno
                if idx_drill < 0 and ("Punta" in tipo_u or "Maschio" in tipo_u):                # Se è punta o maschio
                    idx_drill = i                                                               # Memorizza indice
        if idx_drill >= 0:                                                                      # Se ha trovato un utensile adatto
            self.tool_combo.setCurrentIndex(idx_drill)                                          # Lo preseleziona

    def on_tool_changed(self):                                                                  # Legge Diametro e Vc dall'utensile scelto
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc or self.tool_combo.count() == 0: return                                      # Verifica validità
        t_name = self.tool_combo.itemData(self.tool_combo.currentIndex())                       # Nome utensile
        t_obj = doc.getObject(t_name) if t_name else None                                       # Oggetto utensile
        if t_obj:                                                                               # Se esiste
            prev = self.is_updating                                                             # Salva stato semaforo
            self.is_updating = True                                                             # Sospende ricalcoli
            d_tool = float(getattr(t_obj, "Larghezza", 10.0))                                   # Legge diametro/larghezza dell'utensile
            self.tool_d_spin.setValue(max(d_tool, 1.0))                                         # Imposta il diametro
            tipo_u = str(getattr(t_obj, "TipoLavorazione", ""))                                 # Categoria utensile
            if "Maschio" in tipo_u:                                                             # Se è un maschio
                self.cycle_combo.setCurrentText("4. Maschiatura Rigida Assiale (G84)")          # Seleziona automaticamente G84
            elif "Punta" in tipo_u:                                                             # Se è una punta
                self.cycle_combo.setCurrentText("2. Foratura Profonda con Scarico Truciolo (G83 - Peck)")
            self.is_updating = prev                                                             # Ripristina semaforo
            self.trigger_update()                                                               # Aggiorna l'anteprima

    def cattura_foro_da_faccia_3d(self):                                                        # Rileva Z inizio e Z fondo cliccando il foro cilindrico nel 3D
        sel_ex = FreeCADGui.Selection.getSelectionEx()                                          # Ottiene la selezione 3D
        if not sel_ex or not sel_ex[0].SubElementNames:                                         # Verifica che sia stata cliccata una faccia
            self.lbl_status.setText("Clicca prima sulla parete interna del foro nel 3D!")
            return                                                                              # Esce
        sub_name = sel_ex[0].SubElementNames[0]                                                 # Sotto-elemento (es. Face1)
        obj_sel = sel_ex[0].Object                                                              # Oggetto 3D
        elem = obj_sel.Shape.getElement(sub_name)                                               # Elemento geometrico
        bb = elem.BoundBox                                                                      # BoundBox della faccia
        wcs = LatheRoughing.get_wcs_origin(FreeCAD.ActiveDocument)                              # Origine WCS

        r_foro = max(abs(bb.XMax - wcs.x), abs(bb.YMax - wcs.y))                                # Raggio foro dal BoundBox
        if hasattr(elem, "Surface") and hasattr(elem.Surface, "Radius"):                        # Se è cilindrico esatto
            r_foro = float(elem.Surface.Radius)                                                 # Raggio esatto

        z_front_foro = bb.ZMax - wcs.z                                                          # Quota Z anteriore del foro
        z_fondo_foro = bb.ZMin - wcs.z                                                          # Quota Z sul fondo del foro

        self.is_updating = True                                                                 # Sospende aggiornamenti multipli
        try:                                                                                    # Imposta le quote rilevate
            self.tool_d_spin.setValue(round(r_foro * 2.0, 2))                                   # Imposta il diametro punta pari al foro
            self.z_start_spin.setValue(round(max(z_front_foro + 2.0, 2.0), 2))                    # Z inizio davanti al pezzo
            self.z_fondo_spin.setValue(round(z_fondo_foro, 2))                                  # Z fondo sul fondo del foro rilevato
        finally:                                                                                # Sblocca
            self.is_updating = False                                                            # Riabilita
        FreeCADGui.Selection.clearSelection()                                                   # Pulisce la selezione
        self.lbl_status.setText(f"Foro rilevato da [{sub_name}] (Ø={r_foro*2.0:.1f} mm)!")       # Conferma
        self.trigger_update()                                                                   # Aggiorna il percorso 3D

    def aggiorna_ui_ciclo(self):                                                                # Adatta i controlli in base alla strategia (Foratura o Maschiatura)
        ciclo = self.cycle_combo.currentText()                                                  # Strategia corrente
        is_tapping = ("Maschiatura" in ciclo)                                                   # True se è G84
        is_pecking = ("Scarico Truciolo" in ciclo) or ("Rompitruciolo" in ciclo)                # True se è pecking G83 o G73

        self.chk_peck.setEnabled(not is_tapping)                                                # Il pecking non si usa in maschiatura
        self.peck_q_spin.setEnabled((not is_tapping) and self.chk_peck.isChecked())             # Abilita passo Q
        self.peck_ret_spin.setEnabled((not is_tapping) and self.chk_peck.isChecked())           # Abilita ritrazione
        self.pitch_tap_spin.setEnabled(is_tapping)                                              # Il passo del maschio si attiva solo in G84
        self.chk_cone.setEnabled(not is_tapping)                                                # Il maschio non ha il cono 118° della punta
        self.trigger_update()                                                                   # Aggiorna l'anteprima 3D

    def trigger_update(self, *args):                                                            # Aggiorna in tempo reale il tracciato 3D della foratura
        if self.is_updating: return                                                             # Se bloccato esce
        self.is_updating = True                                                                 # Attiva semaforo
        try:                                                                                    # Blocco di calcolo
            doc = FreeCAD.ActiveDocument                                                        # Documento attivo
            if not doc or not self.preview_rapidi or not self.preview_lavoro: return            # Verifica validità
            wcs = LatheRoughing.get_wcs_origin(doc)                                             # Origine WCS
            sic_x, sic_z = LatheRoughing.get_setup_safe_clearances(doc)                         # Sicurezze Setup
            stock_info = LatheRoughing.get_stock_info(doc)                                      # Dati Grezzo e limite griffe

            _, c_rap, c_lav, moves, z_eff = calcola_percorso_foratura(                          # Calcola il percorso
                wcs, self.cycle_combo.currentText(), stock_info,
                self.z_start_spin.value(), self.z_fondo_spin.value(),
                self.tool_d_spin.value(), self.chk_cone.isChecked(),
                self.chk_peck.isChecked(), self.peck_q_spin.value(), self.peck_ret_spin.value(),
                self.pitch_tap_spin.value(), sic_x, sic_z, self.feed_spin.value()
            )                                                                                   # Fine calcolo

            self.preview_rapidi.Shape = c_rap if c_rap else Part.Shape()                        # Aggiorna i rapidi rossi
            self.preview_lavoro.Shape = c_lav if c_lav else Part.Shape()                        # Aggiorna i tagli arancioni

            n_passi = sum(1 for m in moves if m["cmd"] == "G1")                                 # Conta movimenti di lavoro
            if self.z_fondo_spin.value() < stock_info["z_lim_chuck"]:                           # Avviso griffe
                self.lbl_status.setStyleSheet("color: #FF5555; font-weight: bold;")
                self.lbl_status.setText(f"Attenzione: Fondo foro limitato a Z={z_eff:.2f} mm per sicurezza Griffe!")
            else:                                                                               # Tutto OK
                self.lbl_status.setStyleSheet("color: #FF7700; font-weight: bold;")
                self.lbl_status.setText(f"Foratura OK: Z Fondo Effettivo={z_eff:.2f} mm | {n_passi} movimenti G01.")

            doc.recompute()                                                                     # Rinfresca la vista 3D
        finally:                                                                                # Rilascia semaforo
            self.is_updating = False                                                            # Fine aggiornamento

    def carica_dati_da_oggetto(self, obj):                                                      # Popola la UI quando si riapre un'operazione con doppio click
        obj.Proxy.ensure_properties(obj)                                                        # Verifica proprietà
        self.name_input.setText(str(getattr(obj, "OperationName", obj.Label)))                  # Nome
        if str(obj.TipoCiclo) in TIPI_CICLO_FORATURA:                                           # Strategia
            self.cycle_combo.setCurrentText(str(obj.TipoCiclo))
        idx_t = self.tool_combo.findData(str(getattr(obj, "UtensileAssegnato", "")))            # Utensile
        if idx_t >= 0: self.tool_combo.setCurrentIndex(idx_t)
        self.tool_d_spin.setValue(float(getattr(obj, "DiametroPunta", 10.0)))                   # Diametro punta
        self.chk_cone.setChecked(bool(getattr(obj, "CompensaCono", True)))                      # Compensa cono
        self.z_start_spin.setValue(float(getattr(obj, "Z_Inizio", 2.0)))                        # Z Inizio
        self.z_fondo_spin.setValue(float(getattr(obj, "Z_Fondo", -35.0)))                       # Z Fondo
        self.chk_peck.setChecked(bool(getattr(obj, "UsaPeck", True)))                           # Usa peck
        self.peck_q_spin.setValue(float(getattr(obj, "PassoPeck", 3.0)))                        # Passo Peck Q
        self.peck_ret_spin.setValue(float(getattr(obj, "RitrazionePeck", 0.5)))                 # Ritrazione Peck
        self.pitch_tap_spin.setValue(float(getattr(obj, "PassoMaschio", 1.5)))                  # Passo maschio
        self.vc_spin.setValue(float(getattr(obj, "VelocitaTaglio", 60.0)))                      # Velocità Vc
        self.feed_spin.setValue(float(getattr(obj, "AvanzamentoLavoro", 0.15)))                 # Avanzamento F

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
            if obj.Name.startswith("TMP_Drill_"):
                try: doc.removeObject(obj.Name)
                except Exception: pass

    def getStandardButtons(self):                                                               # Pulsanti OK e Cancel
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel                # Restituisce OK | Cancel

    def accept(self):                                                                           # Conferma e salva l'operazione di Foratura in Operazioni_CAM
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc: return False                                                                # Controllo sicurezza

        ops_group = doc.getObject("Operazioni_CAM")                                             # Cerca il gruppo Operazioni_CAM
        if not ops_group:                                                                       # Se non esiste lo crea
            ops_group = doc.addObject("App::DocumentObjectGroup", "Operazioni_CAM")
            ops_group.Label = "Operazioni CAM (Cicli Tornio)"

        nome_op = self.name_input.text().strip() or "Foratura 1"                                # Nome operazione
        if self.edit_obj and doc.getObject(self.edit_obj.Name):                                 # Se siamo in modifica
            op_obj = self.edit_obj                                                              # Riutilizza l'oggetto esistente
        else:                                                                                   # Altrimenti crea il nuovo oggetto parametrico
            op_obj = doc.addObject("Part::FeaturePython", "Op_Foratura")                        # Crea Part::FeaturePython
            LatheDrillingObject(op_obj)                                                         # Inizializza Proxy
            ViewProviderLatheDrilling(op_obj.ViewObject)                                        # Inizializza ViewProvider
            ops_group.addObject(op_obj)                                                         # Aggiunge al gruppo Operazioni_CAM

        t_name = self.tool_combo.itemData(self.tool_combo.currentIndex()) if self.tool_combo.count() > 0 else ""

        op_obj.Proxy._is_executing = True                                                       # Sospende execute durante il salvataggio proprietà
        try:                                                                                    # Scrive tutte le proprietà
            op_obj.Proxy.ensure_properties(op_obj)
            op_obj.OperationName = nome_op
            op_obj.Label = nome_op
            op_obj.TipoCiclo = self.cycle_combo.currentText()
            op_obj.UtensileAssegnato = str(t_name or "")
            op_obj.DiametroPunta = self.tool_d_spin.value()
            op_obj.CompensaCono = self.chk_cone.isChecked()
            op_obj.Z_Inizio = self.z_start_spin.value()
            op_obj.Z_Fondo = self.z_fondo_spin.value()
            op_obj.UsaPeck = self.chk_peck.isChecked()
            op_obj.PassoPeck = self.peck_q_spin.value()
            op_obj.RitrazionePeck = self.peck_ret_spin.value()
            op_obj.PassoMaschio = self.pitch_tap_spin.value()
            op_obj.VelocitaTaglio = self.vc_spin.value()
            op_obj.AvanzamentoLavoro = self.feed_spin.value()
        finally:                                                                                # Sblocca Proxy
            op_obj.Proxy._is_executing = False

        op_obj.Proxy.execute(op_obj)                                                            # Calcola e disegna il percorso finale
        if hasattr(op_obj, "ViewObject") and op_obj.ViewObject:
            op_obj.ViewObject.Visibility = True                                                 # Mostra il percorso arancione corallo nel 3D

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
        