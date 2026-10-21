import FreeCAD                                                                                  # Importa il modulo base di FreeCAD
import FreeCADGui                                                                               # Importa il modulo interfaccia grafica di FreeCAD
import Part                                                                                     # Importa il modulo geometrico Part
import math                                                                                     # Importa le funzioni matematiche
import os                                                                                       # Importa il modulo per gestire percorsi e cartelle
import json                                                                                     # Importa il modulo JSON per salvare configurazioni macchina
from PySide import QtCore, QtGui                                                                # Importa i moduli grafici PySide
try:                                                                                            # Tenta di importare QtWidgets per compatibilità Qt5/Qt6
    from PySide import QtWidgets                                                                # Assegna QtWidgets
except ImportError:                                                                             # Fallback per versioni meno recenti
    QtWidgets = QtGui                                                                           # Usa QtGui come alias di QtWidgets


def get_machine_lib_dir():                                                                      # Restituisce la cartella su disco per l'archivio macchine
    base_dir = os.path.dirname(os.path.abspath(__file__))                                       # Cartella del Workbench corrente
    lib_dir = os.path.join(base_dir, "MachineLibrary")                                          # Sottocartella MachineLibrary
    os.makedirs(lib_dir, exist_ok=True)                                                         # Crea la cartella se non esiste
    return lib_dir                                                                              # Restituisce il percorso completo


def get_machine_db_file():                                                                      # Restituisce il percorso del file JSON dei profili macchina
    return os.path.join(get_machine_lib_dir(), "machines_db.json")                              # Percorso completo di machines_db.json


def load_machines_db():                                                                         # Legge il database dei profili macchina salvati su disco
    db_path = get_machine_db_file()                                                             # Ottiene il percorso del file JSON
    if os.path.exists(db_path):                                                                 # Controlla se il file esiste
        try:                                                                                    # Tenta la lettura del file JSON
            with open(db_path, "r", encoding="utf-8") as f:                                     # Apre il file in modalità lettura
                return json.load(f)                                                             # Restituisce il dizionario caricato
        except Exception as e:                                                                  # Cattura eventuali errori di lettura
            FreeCAD.Console.PrintError(f"Errore lettura archivio macchine: {e}\n")              # Stampa l'errore in console
    return {}                                                                                   # Restituisce un dizionario vuoto se non esiste


def save_machines_db(db_data):                                                                  # Salva il database dei profili macchina su disco
    db_path = get_machine_db_file()                                                             # Ottiene il percorso del file JSON
    try:                                                                                        # Tenta la scrittura su disco
        with open(db_path, "w", encoding="utf-8") as f:                                         # Apre il file in scrittura
            json.dump(db_data, f, indent=4, ensure_ascii=False)                                 # Scrive il dizionario formattato
    except Exception as e:                                                                      # Cattura eventuali errori
        FreeCAD.Console.PrintError(f"Errore salvataggio archivio macchine: {e}\n")              # Stampa l'errore in console


def costruisci_simbolo_wcs(origine, dim_assi=30.0, sic_x=5.0, sic_z=5.0, mostra_piani=True):    # Genera la terna 3D colorata del WCS e l'anello di sicurezza
    L = max(float(dim_assi), 10.0)                                                              # Lunghezza delle frecce degli assi
    r_asta = L * 0.035                                                                          # Raggio dello stelo cilindrico delle frecce
    r_cono = L * 0.09                                                                           # Raggio di base della punta conica
    h_cono = L * 0.22                                                                           # Altezza della punta conica
    l_asta = L - h_cono                                                                         # Lunghezza del tratto cilindrico

    shapes = []                                                                                 # Lista dei solidi che compongono il simbolo WCS
    face_colors = []                                                                            # Lista dei colori corrispondenti alle singole facce

    sfera_zero = Part.makeSphere(r_cono * 0.85, origine)                                        # Sfera centrale sul punto di origine (0,0,0) del WCS
    shapes.append(sfera_zero)                                                                   # Aggiunge la sfera centrale
    face_colors.extend([(0.95, 0.85, 0.1)] * len(sfera_zero.Faces))                             # Colora la sfera centrale in giallo oro

    cil_x = Part.makeCylinder(r_asta, l_asta, origine, FreeCAD.Vector(1, 0, 0))                 # Stelo asse X lungo +X
    con_x = Part.makeCone(r_cono, 0.0, h_cono, origine + FreeCAD.Vector(l_asta, 0, 0), FreeCAD.Vector(1, 0, 0)) # Punta freccia asse X
    asse_x = cil_x.fuse(con_x)                                                                  # Unisce stelo e punta dell'asse X
    shapes.append(asse_x)                                                                       # Aggiunge l'asse X
    face_colors.extend([(0.9, 0.15, 0.15)] * len(asse_x.Faces))                                 # Colora l'asse X in Rosso

    cil_y = Part.makeCylinder(r_asta, l_asta, origine, FreeCAD.Vector(0, 1, 0))                 # Stelo asse Y lungo +Y
    con_y = Part.makeCone(r_cono, 0.0, h_cono, origine + FreeCAD.Vector(0, l_asta, 0), FreeCAD.Vector(0, 1, 0)) # Punta freccia asse Y
    asse_y = cil_y.fuse(con_y)                                                                  # Unisce stelo e punta dell'asse Y
    shapes.append(asse_y)                                                                       # Aggiunge l'asse Y
    face_colors.extend([(0.15, 0.85, 0.15)] * len(asse_y.Faces))                                # Colora l'asse Y in Verde

    cil_z = Part.makeCylinder(r_asta, l_asta, origine, FreeCAD.Vector(0, 0, 1))                 # Stelo asse Z lungo +Z (Asse Mandrino)
    con_z = Part.makeCone(r_cono, 0.0, h_cono, origine + FreeCAD.Vector(0, 0, l_asta), FreeCAD.Vector(0, 0, 1)) # Punta freccia asse Z
    asse_z = cil_z.fuse(con_z)                                                                  # Unisce stelo e punta dell'asse Z
    shapes.append(asse_z)                                                                       # Aggiunge l'asse Z
    face_colors.extend([(0.15, 0.45, 0.95)] * len(asse_z.Faces))                                # Colora l'asse Z in Blu

    if mostra_piani and (sic_x > 0.1 or sic_z > 0.1):                                           # Se richiesto, disegna l'anello del piano di sicurezza Z+
        r_anello = max(float(sic_x), L * 0.5)                                                   # Raggio indicativo del piano di sicurezza
        pos_anello = origine + FreeCAD.Vector(0, 0, float(sic_z))                               # Posizionato a Z = Origine.z + SicurezzaZ
        ext_c = Part.makeCylinder(r_anello, 0.6, pos_anello, FreeCAD.Vector(0, 0, 1))           # Disco esterno sottile
        int_c = Part.makeCylinder(max(r_anello - 1.2, 0.5), 0.6, pos_anello, FreeCAD.Vector(0, 0, 1)) # Foro interno per creare l'anello
        try:                                                                                    # Tenta la creazione dell'anello di sicurezza
            anello = ext_c.cut(int_c)                                                           # Scava l'interno dell'anello
            shapes.append(anello)                                                               # Aggiunge l'anello al compound
            face_colors.extend([(0.0, 0.85, 0.85)] * len(anello.Faces))                         # Colora l'anello di sicurezza in Ciano
        except Exception:                                                                       # Ignora eventuali errori geometrici
            pass                                                                                # Continua senza bloccare

    comp = Part.makeCompound(shapes)                                                            # Compone tutti gli elementi in un'unica Shape
    return comp, face_colors                                                                    # Restituisce il compound e la mappa colori delle facce


class LatheSetupObject:                                                                         # Classe Proxy per l'oggetto parametrico Setup_Macchina
    def __init__(self, obj):                                                                    # Costruttore del Proxy
        self._is_executing = False                                                              # Flag per prevenire ricalcoli ricorsivi
        self.ensure_properties(obj)                                                             # Garantisce la creazione di tutte le proprietà
        obj.Proxy = self                                                                        # Collega il Proxy all'oggetto FreeCAD

    def ensure_properties(self, obj):                                                           # Aggiunge tutte le proprietà del Setup se mancanti
        if not hasattr(obj, "MachineName"):                                                     # Nome del profilo macchina/setup
            obj.addProperty("App::PropertyString", "MachineName", "Macchina", "Nome profilo tornio").MachineName = "Tornio CNC Standard"
        if not hasattr(obj, "Origine"):                                                         # Punto Zero Pezzo WCS (usato da Grezzo, Utensili e Torretta)
            obj.addProperty("App::PropertyVector", "Origine", "WCS", "Coordinate Origine Zero Pezzo (WCS)").Origine = FreeCAD.Vector(0.0, 0.0, 0.0)
        if not hasattr(obj, "SistemaCoordinate"):                                               # Offset di lavoro ISO G54..G59
            obj.addProperty("App::PropertyEnumeration", "SistemaCoordinate", "WCS", "Origine G-Code")
            obj.SistemaCoordinate = ["G54", "G55", "G56", "G57", "G58", "G59"]                  # Valori standard ISO
        if not hasattr(obj, "DimensioneSimbolo"):                                               # Dimensione frecce terna 3D
            obj.addProperty("App::PropertyFloat", "DimensioneSimbolo", "WCS", "Dimensione grafica assi WCS (mm)").DimensioneSimbolo = 30.0
        if not hasattr(obj, "MostraPianoSicurezza"):                                            # Mostra/nasconde l'anello ciano del piano di sicurezza
            obj.addProperty("App::PropertyBool", "MostraPianoSicurezza", "Sicurezza", "Mostra anello piano sicurezza").MostraPianoSicurezza = True
        if not hasattr(obj, "SicurezzaX"):                                                      # Sovrametallo/distanza rapida di sicurezza in X
            obj.addProperty("App::PropertyFloat", "SicurezzaX", "Sicurezza", "Distanza di sicurezza radiale X (mm)").SicurezzaX = 5.0
        if not hasattr(obj, "SicurezzaZ"):                                                      # Distanza rapida di sicurezza frontale in Z
            obj.addProperty("App::PropertyFloat", "SicurezzaZ", "Sicurezza", "Distanza di sicurezza frontale Z (mm)").SicurezzaZ = 5.0
        if not hasattr(obj, "CambioUtensileX"):                                                 # Quota X assoluta/relativa per cambio utensile sicuro
            obj.addProperty("App::PropertyFloat", "CambioUtensileX", "Sicurezza", "Posizione X Cambio Utensile / Home (mm)").CambioUtensileX = 100.0
        if not hasattr(obj, "CambioUtensileZ"):                                                 # Quota Z per cambio utensile sicuro
            obj.addProperty("App::PropertyFloat", "CambioUtensileZ", "Sicurezza", "Posizione Z Cambio Utensile / Home (mm)").CambioUtensileZ = 100.0
        if not hasattr(obj, "ModoProgrammazioneX"):                                             # Programmazione in Diametro o Raggio
            obj.addProperty("App::PropertyEnumeration", "ModoProgrammazioneX", "Cinematica", "Modalità coordinate X nel G-Code")
            obj.ModoProgrammazioneX = ["Diametrale (Diametro)", "Radiale (Raggio)"]             # Default Diametrale
        if not hasattr(obj, "PosizioneTorretta"):                                               # Torretta Posteriore (+X) o Anteriore (-X)
            obj.addProperty("App::PropertyEnumeration", "PosizioneTorretta", "Cinematica", "Configurazione lato torretta")
            obj.PosizioneTorretta = ["Posteriore (+X)", "Anteriore (-X)"]                       # Default Posteriore (+X)
        if not hasattr(obj, "GiriMaxMandrino"):                                                 # Limitatore giri G50/G92 S_max
            obj.addProperty("App::PropertyInteger", "GiriMaxMandrino", "Mandrino", "Giri massimi mandrino G50/G92 (RPM)").GiriMaxMandrino = 2500
        if not hasattr(obj, "SensoRotazioneDefault"):                                           # Senso rotazione mandrino predefinito
            obj.addProperty("App::PropertyEnumeration", "SensoRotazioneDefault", "Mandrino", "Senso rotazione mandrino default")
            obj.SensoRotazioneDefault = ["Orario (M03)", "Antiorario (M04)"]                    # M03 / M04
        if not hasattr(obj, "RefrigeranteDefault"):                                             # Stato refrigerante predefinito
            obj.addProperty("App::PropertyEnumeration", "RefrigeranteDefault", "Mandrino", "Gestione refrigerante")
            obj.RefrigeranteDefault = ["Attivo (M08)", "Spento (M09)"]                          # M08 / M09
        if not hasattr(obj, "PostProcessor"):                                                   # Controllo numerico per l'esportazione G-Code
            obj.addProperty("App::PropertyEnumeration", "PostProcessor", "Macchina", "Post-Processor CNC")
            obj.PostProcessor = ["Fanuc", "Siemens Sinumerik", "LinuxCNC", "Haas", "Mach3 / Mach4"] # Controlli supportati

    def onDocumentRestored(self, obj):                                                          # Eseguito alla riapertura di un file FCStd salvato
        self._is_executing = False                                                              # Sblocca il flag di esecuzione
        self.ensure_properties(obj)                                                             # Verifica la presenza di tutte le proprietà

    def execute(self, obj):                                                                     # Costruisce la geometria 3D del WCS e aggiorna gli oggetti dipendenti
        if getattr(self, "_is_executing", False):                                               # Evita loop ricorsivi
            return                                                                              # Esce subito
        self._is_executing = True                                                               # Imposta il semaforo di esecuzione
        try:                                                                                    # Blocco protetto di generazione 3D
            self.ensure_properties(obj)                                                         # Controlla tutte le proprietà
            comp, face_cols = costruisci_simbolo_wcs(                                           # Genera la terna RGB + anello di sicurezza
                obj.Origine, obj.DimensioneSimbolo,                                             # Passa origine e dimensione frecce
                obj.SicurezzaX, obj.SicurezzaZ, obj.MostraPianoSicurezza                        # Passa i parametri del piano di sicurezza
            )                                                                                   # Fine generazione simbolo
            obj.Shape = comp                                                                    # Assegna la Shape all'oggetto Setup_Macchina
            if hasattr(obj, "ViewObject") and obj.ViewObject and face_cols:                     # Se la vista grafica è disponibile
                if len(face_cols) == len(obj.Shape.Faces):                                      # Verifica corrispondenza facce/colori
                    obj.ViewObject.DiffuseColor = face_cols                                     # Colora gli assi in Rosso (X), Verde (Y), Blu (Z) e Oro (0)
            self.propaga_aggiornamento_wcs(obj.Document)                                        # Riallinea Utensili, Torretta e Grezzo se cambia l'Origine WCS
        except Exception as e:                                                                  # Cattura errori imprevisti
            FreeCAD.Console.PrintError(f"Errore ricalcolo Setup WCS: {e}\n")                    # Stampa l'errore in console
        finally:                                                                                # Blocco finale garantito
            self._is_executing = False                                                          # Rilascia il semaforo

    def propaga_aggiornamento_wcs(self, doc):                                                   # Aggiorna Grezzo, Torretta e Utensili quando si sposta il WCS
        if not doc:                                                                             # Controlla che il documento esista
            return                                                                              # Esce
        stock = doc.getObject("Grezzo_Macchina")                                                # Cerca l'oggetto Grezzo_Macchina
        if stock and hasattr(stock, "Proxy") and stock.Proxy:                                   # Se il grezzo ha un Proxy parametrico
            try: stock.Proxy.execute(stock)                                                     # Aggiorna la posizione del grezzo
            except Exception: pass                                                              # Ignora se non ancora pronto
        turret = doc.getObject("Torretta_Macchina")                                             # Cerca l'oggetto Torretta_Macchina
        if turret and hasattr(turret, "Proxy") and turret.Proxy:                                # Se esiste la torretta
            try: turret.Proxy.execute(turret)                                                   # Aggiorna torretta e utensili saldati
            except Exception: pass                                                              # Ignora errori
        lib = doc.getObject("Libreria_Utensili")                                                # Cerca il Magazzino Utensili
        if lib and hasattr(lib, "Group"):                                                       # Se ci sono utensili nel magazzino
            for t in lib.Group:                                                                 # Cicla sugli utensili
                if hasattr(t, "Proxy") and t.Proxy:                                             # Se l'utensile è parametrico
                    try: t.Proxy.execute(t)                                                     # Riallinea l'utensile al nuovo WCS
                    except Exception: pass                                                      # Ignora errori

    def onChanged(self, obj, prop):                                                             # Intercetta le modifiche live dalle Proprietà di FreeCAD
        if getattr(self, "_is_executing", False):                                               # Evita chiamate ricorsive
            return                                                                              # Esce
        props_grafiche = [                                                                      # Proprietà che richiedono il ridisegno della terna WCS
            "Origine", "DimensioneSimbolo", "SicurezzaX",                                       # Coordinate e dimensioni
            "SicurezzaZ", "MostraPianoSicurezza"                                                # Piani di sicurezza
        ]                                                                                       # Fine elenco
        if prop in props_grafiche:                                                              # Se è cambiata una proprietà grafica o di posizione
            self.execute(obj)                                                                   # Ricalcola subito il 3D in tempo reale
        elif prop in ["MachineName", "SistemaCoordinate"]:                                      # Se cambia il nome macchina o l'origine G54..G59
            if hasattr(obj, "MachineName") and hasattr(obj, "SistemaCoordinate"):               # Verifica presenza attributi
                obj.Label = f"Setup ({obj.SistemaCoordinate} - {obj.MachineName})"              # Aggiorna l'etichetta nell'albero

    def __getstate__(self):                                                                     # Serializzazione per salvataggio file FCStd
        return None                                                                             # Nessun dato speciale

    def __setstate__(self, state):                                                              # Deserializzazione all'apertura file FCStd
        self._is_executing = False                                                              # Ripristina il flag
        return None                                                                             # Fine


class ViewProviderLatheSetup:                                                                   # ViewProvider per gestire doppio click e visualizzazione WCS
    def __init__(self, vobj):                                                                   # Costruttore ViewProvider
        vobj.Proxy = self                                                                       # Collega il Proxy alla vista

    def getIcon(self):                                                                          # Icona nell'albero
        return "Std_AxisCross"                                                                  # Usa l'icona degli assi coordinati di FreeCAD

    def attach(self, vobj):                                                                     # Collega gli oggetti alla vista
        self.ViewObject = vobj                                                                  # Riferimento ViewObject
        self.Object = vobj.Object                                                               # Riferimento Object

    def updateData(self, vobj, prop):                                                           # Aggiornamento dati
        return                                                                                  # Gestito da execute

    def onDelete(self, vobj, subelements):                                                      # Autorizza l'eliminazione dall'albero
        return True                                                                             # Sempre consentito

    def doubleClicked(self, vobj):                                                              # Doppio click su Setup_Macchina nell'albero
        if not FreeCADGui.Control.activeDialog():                                               # Controlla che non ci sia già un pannello aperto
            panel = LatheSetupPanel(edit_obj=vobj.Object)                                       # Apre il pannello caricando il Setup esistente
            FreeCADGui.Control.showDialog(panel)                                                # Mostra il pannello nella scheda Azioni
        return True                                                                             # Evento gestito

    def setEdit(self, vobj, mode):                                                              # Ingresso in modalità Edit standard
        if mode == 0:                                                                           # Modifica base
            if not FreeCADGui.Control.activeDialog():                                           # Evita doppia apertura
                panel = LatheSetupPanel(edit_obj=vobj.Object)                                   # Crea il pannello in modalità modifica
                FreeCADGui.Control.showDialog(panel)                                            # Mostra il dialogo
            return True                                                                         # Conferma
        return False                                                                            # Rifiuta altre modalità

    def unsetEdit(self, vobj, mode):                                                            # Uscita dalla modalità Edit
        FreeCADGui.Control.closeDialog()                                                        # Chiude il pannello
        return True                                                                             # Conferma

    def __getstate__(self):                                                                     # Serializzazione
        return None                                                                             # Nessuno stato extra

    def __setstate__(self, state):                                                              # Deserializzazione
        return None                                                                             # Nessuno stato extra


class LatheSetupPanel:                                                                          # Pannello UI per la configurazione del Setup Macchina e WCS
    def __init__(self, edit_obj=None):                                                          # Costruttore del pannello (nuovo o modifica)
        doc = FreeCAD.ActiveDocument                                                            # Ottiene il documento attivo
        if edit_obj is None and doc and doc.getObject("Setup_Macchina"):                        # Se esiste già Setup_Macchina nel progetto
            edit_obj = doc.getObject("Setup_Macchina")                                          # Lo apre automaticamente in modifica senza duplicarlo

        self.edit_obj = edit_obj                                                                # Memorizza l'oggetto in modifica
        self.is_updating = True                                                                 # Blocca i segnali durante la costruzione della UI
        self.backup_dati = {}                                                                   # Salva i valori iniziali per ripristinarli in caso di Cancel

        self.pulisci_anteprima_setup(doc)                                                       # Elimina eventuali anteprime temporanee rimaste appese
        if self.edit_obj:                                                                       # Se stiamo modificando un Setup esistente
            self.salva_backup_originale(self.edit_obj)                                          # Memorizza i dati attuali per eventuale annullamento
            if hasattr(self.edit_obj, "ViewObject") and self.edit_obj.ViewObject:               # Verifica il ViewObject
                self.edit_obj.ViewObject.Visibility = False                                     # Nasconde l'originale durante l'anteprima live

        self.form = QtWidgets.QWidget()                                                         # Crea il contenitore principale della UI
        self.form.setMinimumWidth(240)                                                          # Larghezza minima compatta per non tagliare a destra
        self.layout = QtWidgets.QVBoxLayout(self.form)                                          # Layout verticale principale
        self.layout.setContentsMargins(4, 4, 4, 4)                                              # Riduce i margini per sfruttare tutta la colonna

        self.grp_db = QtWidgets.QGroupBox("Archivio Macchine (Salva / Richiama)")               # Gruppo archivio profili tornio su disco
        self.lyt_db = QtWidgets.QVBoxLayout(self.grp_db)                                        # Layout verticale archivio
        self.db_combo = QtWidgets.QComboBox()                                                   # Tendina con i profili macchina salvati
        self.db_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon) # Adatta la tendina alla larghezza del pannello
        self.db_combo.setMinimumContentsLength(10)                                              # Evita l'allargamento forzato a destra
        self.lyt_db.addWidget(self.db_combo)                                                    # Tendina su tutta la larghezza

        self.lyt_db_btns = QtWidgets.QHBoxLayout()                                              # Riga pulsanti Carica ed Elimina
        self.btn_load_db = QtWidgets.QPushButton("Carica Profilo")                              # Pulsante carica profilo da disco
        self.btn_load_db.clicked.connect(self.carica_profilo_da_db)                             # Collega il caricamento
        self.btn_del_db = QtWidgets.QPushButton("Elimina")                                      # Pulsante elimina profilo da disco
        self.btn_del_db.clicked.connect(self.elimina_profilo_da_db)                             # Collega l'eliminazione
        self.lyt_db_btns.addWidget(self.btn_load_db)                                            # Aggiunge pulsante Carica
        self.lyt_db_btns.addWidget(self.btn_del_db)                                             # Aggiunge pulsante Elimina
        self.lyt_db.addLayout(self.lyt_db_btns)                                                 # Aggiunge la riga pulsanti

        self.lyt_name = QtWidgets.QFormLayout()                                                 # Form layout per il nome macchina
        self.name_input = QtWidgets.QLineEdit("Tornio CNC Standard")                            # Campo testo per il nome del tornio
        self.lyt_name.addRow("Macchina:", self.name_input)                                      # Riga Nome Macchina
        self.lyt_db.addLayout(self.lyt_name)                                                    # Aggiunge al gruppo archivio

        self.chk_save_db = QtWidgets.QCheckBox("Salva in Archivio Permanente all'OK")           # Salvataggio automatico su disco all'OK
        self.chk_save_db.setChecked(True)                                                       # Attivo di default
        self.lyt_db.addWidget(self.chk_save_db)                                                 # Aggiunge al gruppo archivio
        self.layout.addWidget(self.grp_db)                                                      # Inserisce il gruppo archivio nel layout

        self.tabs = QtWidgets.QTabWidget()                                                      # Schede: 1. Origine WCS & Sicurezza | 2. Cinematica & CNC

        self.tab_wcs = QtWidgets.QWidget()                                                      # SCHEDA 1: Zero Pezzo (WCS) e Piani di Sicurezza
        self.lyt_wcs = QtWidgets.QVBoxLayout(self.tab_wcs)                                      # Layout verticale Scheda 1

        self.grp_orig = QtWidgets.QGroupBox("Origine Zero Pezzo (WCS)")                         # Gruppo coordinate Origine WCS
        self.lyt_orig = QtWidgets.QFormLayout(self.grp_orig)                                    # Form layout coordinate

        self.wcs_code_combo = QtWidgets.QComboBox()                                             # Scelta origine G54..G59
        self.wcs_code_combo.addItems(["G54", "G55", "G56", "G57", "G58", "G59"])                # Codici ISO standard

        self.ox_spin = QtWidgets.QDoubleSpinBox(); self.ox_spin.setRange(-10000, 10000); self.ox_spin.setDecimals(3) # Coordinata X Origine
        self.oy_spin = QtWidgets.QDoubleSpinBox(); self.oy_spin.setRange(-10000, 10000); self.oy_spin.setDecimals(3) # Coordinata Y Origine
        self.oz_spin = QtWidgets.QDoubleSpinBox(); self.oz_spin.setRange(-10000, 10000); self.oz_spin.setDecimals(3) # Coordinata Z Origine

        self.btn_pick_z = QtWidgets.QPushButton("Imposta Z=0 da Faccia/Vertice (Asse X=0, Y=0)") # Cattura la Z dalla faccia frontale del pezzo
        self.btn_pick_z.clicked.connect(self.cattura_z_frontale)                                # Collega la cattura Z frontale
        self.btn_pick_pt = QtWidgets.QPushButton("Imposta X, Y, Z dal Centro Selezione 3D")     # Cattura X, Y, Z dal centro dell'elemento selezionato
        self.btn_pick_pt.clicked.connect(self.cattura_centro_completo)                          # Collega la cattura completa

        self.dim_sym_spin = QtWidgets.QDoubleSpinBox()                                          # Dimensione grafica delle frecce WCS
        self.dim_sym_spin.setRange(10.0, 300.0); self.dim_sym_spin.setValue(30.0)               # Default 30 mm

        self.lbl_wcs_status = QtWidgets.QLabel("Stato: Origine WCS pronta.")                    # Etichetta di stato
        self.lbl_wcs_status.setWordWrap(True)                                                   # Va a capo automaticamente
        self.lbl_wcs_status.setStyleSheet("color: #FFAA00; font-weight: bold;")                 # Stile arancione

        self.lyt_orig.addRow("Origine ISO:", self.wcs_code_combo)                               # Riga G54..G59
        self.lyt_orig.addRow("Origine X (mm):", self.ox_spin)                                   # Riga X0
        self.lyt_orig.addRow("Origine Y (mm):", self.oy_spin)                                   # Riga Y0
        self.lyt_orig.addRow("Origine Z (mm):", self.oz_spin)                                   # Riga Z0
        self.lyt_orig.addRow(self.btn_pick_z)                                                   # Riga pulsante cattura Z frontale
        self.lyt_orig.addRow(self.btn_pick_pt)                                                  # Riga pulsante cattura centro 3D
        self.lyt_orig.addRow("Scala Frecce (mm):", self.dim_sym_spin)                           # Riga dimensione frecce
        self.lyt_orig.addRow(self.lbl_wcs_status)                                               # Riga stato
        self.lyt_wcs.addWidget(self.grp_orig)                                                   # Aggiunge il gruppo alla Scheda 1

        self.grp_safe = QtWidgets.QGroupBox("Piani di Sicurezza e Cambio Utensile")             # Gruppo quote di disimpegno rapido e Home
        self.lyt_safe = QtWidgets.QFormLayout(self.grp_safe)                                    # Form layout sicurezza

        self.safe_x_spin = QtWidgets.QDoubleSpinBox(); self.safe_x_spin.setRange(0.5, 500.0); self.safe_x_spin.setValue(5.0) # Sicurezza X
        self.safe_z_spin = QtWidgets.QDoubleSpinBox(); self.safe_z_spin.setRange(0.5, 500.0); self.safe_z_spin.setValue(5.0) # Sicurezza Z
        self.home_x_spin = QtWidgets.QDoubleSpinBox(); self.home_x_spin.setRange(-2000, 2000); self.home_x_spin.setValue(100.0) # Cambio utensile X
        self.home_z_spin = QtWidgets.QDoubleSpinBox(); self.home_z_spin.setRange(-2000, 2000); self.home_z_spin.setValue(100.0) # Cambio utensile Z
        self.chk_show_safe = QtWidgets.QCheckBox("Mostra anello piano sicurezza Z nel 3D")      # Mostra/nasconde l'anello ciano
        self.chk_show_safe.setChecked(True)                                                     # Attivo di default

        self.lyt_safe.addRow("Sicurezza Rapidi X (mm):", self.safe_x_spin)                      # Riga Sicurezza X
        self.lyt_safe.addRow("Sicurezza Rapidi Z (mm):", self.safe_z_spin)                      # Riga Sicurezza Z
        self.lyt_safe.addRow("Cambio Utensile X (mm):", self.home_x_spin)                       # Riga Home X
        self.lyt_safe.addRow("Cambio Utensile Z (mm):", self.home_z_spin)                       # Riga Home Z
        self.lyt_safe.addRow(self.chk_show_safe)                                                # Riga checkbox anello sicurezza
        self.lyt_wcs.addWidget(self.grp_safe)                                                   # Aggiunge alla Scheda 1

        self.tabs.addTab(self.tab_wcs, "1. WCS & Sicurezza")                                    # Titolo Scheda 1 compatto

        self.tab_cnc = QtWidgets.QWidget()                                                      # SCHEDA 2: Cinematica, Mandrino e Post-Processor
        self.lyt_cnc = QtWidgets.QVBoxLayout(self.tab_cnc)                                      # Layout verticale Scheda 2

        self.grp_kin = QtWidgets.QGroupBox("Cinematica e Programmazione Asse X")                # Gruppo configurazione assi tornio
        self.lyt_kin = QtWidgets.QFormLayout(self.grp_kin)                                      # Form layout cinematica

        self.x_mode_combo = QtWidgets.QComboBox()                                               # Scelta Diametrale / Radiale
        self.x_mode_combo.addItems(["Diametrale (Diametro)", "Radiale (Raggio)"])               # Opzioni programmazione X
        self.x_mode_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon) # Compatta la tendina
        self.x_mode_combo.setMinimumContentsLength(10)                                          # Evita tagli a destra

        self.turret_pos_combo = QtWidgets.QComboBox()                                           # Scelta Torretta Posteriore / Anteriore
        self.turret_pos_combo.addItems(["Posteriore (+X)", "Anteriore (-X)"])                   # Opzioni lato torretta
        self.turret_pos_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.turret_pos_combo.setMinimumContentsLength(10)

        self.lyt_kin.addRow("Quota Asse X:", self.x_mode_combo)                                 # Riga modalità X
        self.lyt_kin.addRow("Lato Torretta:", self.turret_pos_combo)                            # Riga lato torretta
        self.lyt_cnc.addWidget(self.grp_kin)                                                    # Aggiunge alla Scheda 2

        self.grp_spindle = QtWidgets.QGroupBox("Limiti Mandrino e Post-Processor")              # Gruppo mandrino e controllo CNC
        self.lyt_spindle = QtWidgets.QFormLayout(self.grp_spindle)                              # Form layout mandrino

        self.max_rpm_spin = QtWidgets.QSpinBox()                                                # Giri massimi mandrino (G50/G92)
        self.max_rpm_spin.setRange(100, 30000); self.max_rpm_spin.setSingleStep(100); self.max_rpm_spin.setValue(2500) # Default 2500 RPM

        self.spindle_dir_combo = QtWidgets.QComboBox()                                          # Senso rotazione predefinito
        self.spindle_dir_combo.addItems(["Orario (M03)", "Antiorario (M04)"])                   # M03 / M04

        self.coolant_combo = QtWidgets.QComboBox()                                              # Refrigerante predefinito
        self.coolant_combo.addItems(["Attivo (M08)", "Spento (M09)"])                           # M08 / M09

        self.post_combo = QtWidgets.QComboBox()                                                 # Scelta Post-Processor
        self.post_combo.addItems(["Fanuc", "Siemens Sinumerik", "LinuxCNC", "Haas", "Mach3 / Mach4"]) # Controlli CNC
        self.post_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.post_combo.setMinimumContentsLength(10)

        self.lyt_spindle.addRow("Giri Max (G50 S):", self.max_rpm_spin)                         # Riga Giri Max
        self.lyt_spindle.addRow("Rotazione Mandrino:", self.spindle_dir_combo)                  # Riga M03/M04
        self.lyt_spindle.addRow("Refrigerante:", self.coolant_combo)                            # Riga M08/M09
        self.lyt_spindle.addRow("Post-Processor:", self.post_combo)                             # Riga Post-Processor
        self.lyt_cnc.addWidget(self.grp_spindle)                                                # Aggiunge alla Scheda 2
        self.lyt_cnc.addStretch()                                                               # Allinea i gruppi in alto

        self.tabs.addTab(self.tab_cnc, "2. Macchina & CNC")                                     # Titolo Scheda 2 compatto
        self.layout.addWidget(self.tabs)                                                        # Aggiunge il TabWidget al layout principale
        self.form.setLayout(self.layout)                                                        # Imposta il layout finale

        self.preview_wcs = doc.addObject("Part::Feature", "TMP_WCS_Preview")                    # Crea l'oggetto temporaneo per l'anteprima del WCS
        self.preview_wcs.Label = "ANTEPRIMA WCS (Provvisorio)"                                  # Etichetta provvisoria

        self.aggiorna_combo_db()                                                                # Popola la tendina dei profili salvati su disco

        if self.edit_obj:                                                                       # Se stiamo modificando un Setup esistente
            self.carica_dati_da_oggetto(self.edit_obj)                                          # Popola tutti i controlli con i valori salvati

        self.ox_spin.valueChanged.connect(self.trigger_update)                                  # Collega cambio X0
        self.oy_spin.valueChanged.connect(self.trigger_update)                                  # Collega cambio Y0
        self.oz_spin.valueChanged.connect(self.trigger_update)                                  # Collega cambio Z0
        self.dim_sym_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio dimensione frecce
        self.safe_x_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio sicurezza X
        self.safe_z_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio sicurezza Z
        self.chk_show_safe.stateChanged.connect(self.trigger_update)                            # Collega spunta mostra anello sicurezza

        self.is_updating = False                                                                # Sblocca gli aggiornamenti live
        self.trigger_update()                                                                   # Disegna subito l'anteprima 3D del WCS

    def salva_backup_originale(self, obj):                                                      # Memorizza lo stato iniziale per eventuale Cancel
        self.backup_dati = {                                                                    # Copia tutti gli attributi principali
            "Origine": FreeCAD.Vector(getattr(obj, "Origine", FreeCAD.Vector(0, 0, 0))),        # Vettore Origine originale
            "Visibility": bool(obj.ViewObject.Visibility) if hasattr(obj, "ViewObject") and obj.ViewObject else True # Visibilità
        }                                                                                       # Fine backup

    def cattura_z_frontale(self):                                                               # Imposta Z dallo spigolo/faccia cliccata mantenendo X=0, Y=0
        sel_ex = FreeCADGui.Selection.getSelectionEx()                                          # Legge la selezione 3D corrente
        if not sel_ex:                                                                          # Se non è stato selezionato nulla
            self.lbl_wcs_status.setText("Errore: Seleziona una faccia o un vertice nel 3D!")    # Avvisa l'utente
            return                                                                              # Esce
        pt = self.estrai_punto_da_selezione(sel_ex[0])                                          # Estrae il punto 3D dall'elemento selezionato
        if pt is not None:                                                                      # Se il punto è valido
            self.is_updating = True                                                             # Sospende aggiornamenti multipli
            self.ox_spin.setValue(0.0)                                                          # Centra X sull'asse mandrino (X = 0)
            self.oy_spin.setValue(0.0)                                                          # Centra Y sull'asse mandrino (Y = 0)
            self.oz_spin.setValue(pt.z)                                                         # Imposta Z sulla quota della faccia frontale selezionata
            self.is_updating = False                                                            # Sblocca
            FreeCADGui.Selection.clearSelection()                                               # Pulisce la selezione
            self.lbl_wcs_status.setText(f"Zero Pezzo centrato sull'asse a Z = {pt.z:.3f} mm.")  # Conferma l'operazione
            self.trigger_update()                                                               # Aggiorna l'anteprima 3D

    def cattura_centro_completo(self):                                                          # Imposta X, Y, Z esatti dal centro della faccia/vertice cliccato
        sel_ex = FreeCADGui.Selection.getSelectionEx()                                          # Legge la selezione 3D corrente
        if not sel_ex:                                                                          # Se non c'è selezione
            self.lbl_wcs_status.setText("Errore: Seleziona un elemento nel 3D!")                # Avvisa l'utente
            return                                                                              # Esce
        pt = self.estrai_punto_da_selezione(sel_ex[0])                                          # Estrae il punto 3D
        if pt is not None:                                                                      # Se valido
            self.is_updating = True                                                             # Sospende aggiornamenti multipli
            self.ox_spin.setValue(pt.x)                                                         # Imposta X
            self.oy_spin.setValue(pt.y)                                                         # Imposta Y
            self.oz_spin.setValue(pt.z)                                                         # Imposta Z
            self.is_updating = False                                                            # Sblocca
            FreeCADGui.Selection.clearSelection()                                               # Pulisce la selezione
            self.lbl_wcs_status.setText(f"WCS impostato a ({pt.x:.2f}, {pt.y:.2f}, {pt.z:.2f}).") # Conferma
            self.trigger_update()                                                               # Aggiorna l'anteprima 3D

    def estrai_punto_da_selezione(self, sel_item):                                              # Ricava il punto 3D da Vertice, Bordo, Faccia o Oggetto
        try:                                                                                    # Blocco protetto di interrogazione geometrica
            if sel_item.SubElementNames:                                                        # Se è stato cliccato un sotto-elemento specifico
                sub = sel_item.Object.Shape.getElement(sel_item.SubElementNames[0])             # Ottiene la forma del sotto-elemento
                if hasattr(sub, "Point"):                                                       # Se è un Vertice (Vertex)
                    return sub.Point                                                            # Restituisce le coordinate del vertice
                if hasattr(sub, "Curve") and hasattr(sub.Curve, "Center"):                      # Se è un bordo circolare (es. diametro esterno pezzo)
                    return sub.Curve.Center                                                     # Restituisce il centro esatto del cerchio
                if hasattr(sub, "CenterOfMass"):                                                # Se è una faccia o una linea
                    return sub.CenterOfMass                                                     # Restituisce il baricentro
            if hasattr(sel_item.Object, "Shape") and sel_item.Object.Shape:                     # Se è stato selezionato l'intero solido
                return sel_item.Object.Shape.BoundBox.Center                                    # Restituisce il centro del BoundBox
        except Exception:                                                                       # In caso di geometria non standard
            pass                                                                                # Ritorna None
        return None                                                                             # Nessun punto trovato

    def trigger_update(self, *args):                                                            # Aggiorna in tempo reale la terna di anteprima nel 3D
        if self.is_updating:                                                                    # Se bloccato
            return                                                                              # Esce
        self.is_updating = True                                                                 # Attiva il semaforo
        try:                                                                                    # Blocco di disegno
            doc = FreeCAD.ActiveDocument                                                        # Documento attivo
            if not doc or not self.preview_wcs:                                                 # Verifica validità
                return                                                                          # Esce
            orig = FreeCAD.Vector(self.ox_spin.value(), self.oy_spin.value(), self.oz_spin.value()) # Vettore origine attuale
            comp, face_cols = costruisci_simbolo_wcs(                                           # Costruisce il simbolo 3D
                orig, self.dim_sym_spin.value(),                                                # Origine e dimensione frecce
                self.safe_x_spin.value(), self.safe_z_spin.value(),                             # Sicurezze X e Z
                self.chk_show_safe.isChecked()                                                  # Flag mostra anello sicurezza
            )                                                                                   # Fine costruzione
            self.preview_wcs.Shape = comp                                                       # Assegna la Shape all'anteprima
            if hasattr(self.preview_wcs, "ViewObject") and self.preview_wcs.ViewObject:         # Applica i colori RGB alle frecce di anteprima
                if len(face_cols) == len(self.preview_wcs.Shape.Faces):                         # Controlla corrispondenza facce
                    self.preview_wcs.ViewObject.DiffuseColor = face_cols                        # Applica Rosso, Verde, Blu, Oro e Ciano
            doc.recompute()                                                                     # Aggiorna la scena 3D
        finally:                                                                                # Rilascia il semaforo
            self.is_updating = False                                                            # Fine aggiornamento

    def aggiorna_combo_db(self):                                                                # Popola la tendina con i profili macchina salvati su disco
        db = load_machines_db()                                                                 # Legge il file JSON
        self.db_combo.clear()                                                                   # Svuota il combo
        nomi = sorted(db.keys())                                                                # Ordina alfabeticamente
        if nomi:                                                                                # Se ci sono profili salvati
            self.db_combo.addItems(nomi)                                                        # Li aggiunge alla tendina
        else:                                                                                   # Se l'archivio è vuoto
            self.db_combo.addItem("(Archivio vuoto)")                                           # Mostra testo informativo

    def salva_profilo_in_db(self, setup_obj):                                                   # Salva la configurazione del tornio su disco
        db = load_machines_db()                                                                 # Carica il database
        key = setup_obj.MachineName.strip() or "Tornio CNC Standard"                            # Usa il nome macchina come chiave
        db[key] = {                                                                             # Registra tutti i parametri della macchina
            "MachineName": key,                                                                 # Nome macchina
            "SistemaCoordinate": str(setup_obj.SistemaCoordinate),                              # G54..G59
            "DimensioneSimbolo": float(setup_obj.DimensioneSimbolo),                            # Scala frecce
            "MostraPianoSicurezza": bool(setup_obj.MostraPianoSicurezza),                       # Flag anello sicurezza
            "SicurezzaX": float(setup_obj.SicurezzaX),                                          # Sicurezza X
            "SicurezzaZ": float(setup_obj.SicurezzaZ),                                          # Sicurezza Z
            "CambioUtensileX": float(setup_obj.CambioUtensileX),                                # Home X
            "CambioUtensileZ": float(setup_obj.CambioUtensileZ),                                # Home Z
            "ModoProgrammazioneX": str(setup_obj.ModoProgrammazioneX),                          # Diametrale / Radiale
            "PosizioneTorretta": str(setup_obj.PosizioneTorretta),                              # Posteriore / Anteriore
            "GiriMaxMandrino": int(setup_obj.GiriMaxMandrino),                                  # Giri max G50
            "SensoRotazioneDefault": str(setup_obj.SensoRotazioneDefault),                      # M03 / M04
            "RefrigeranteDefault": str(setup_obj.RefrigeranteDefault),                          # M08 / M09
            "PostProcessor": str(setup_obj.PostProcessor)                                       # Post-Processor scelto
        }                                                                                       # Fine record
        save_machines_db(db)                                                                    # Scrive il file JSON su disco

    def carica_profilo_da_db(self):                                                             # Carica nel pannello i dati del profilo macchina selezionato
        db = load_machines_db()                                                                 # Legge il database
        key = self.db_combo.currentText()                                                       # Voce selezionata
        if key not in db:                                                                       # Se non esiste
            return                                                                              # Esce
        data = db[key]                                                                          # Estrae il dizionario dati
        self.is_updating = True                                                                 # Sospende i segnali UI
        try:                                                                                    # Popola tutti i campi del pannello
            self.name_input.setText(data.get("MachineName", key))                               # Nome macchina
            self.wcs_code_combo.setCurrentText(data.get("SistemaCoordinate", "G54"))            # G54..G59
            self.dim_sym_spin.setValue(float(data.get("DimensioneSimbolo", 30.0)))              # Scala frecce
            self.chk_show_safe.setChecked(bool(data.get("MostraPianoSicurezza", True)))         # Mostra piano sicurezza
            self.safe_x_spin.setValue(float(data.get("SicurezzaX", 5.0)))                       # Sicurezza X
            self.safe_z_spin.setValue(float(data.get("SicurezzaZ", 5.0)))                       # Sicurezza Z
            self.home_x_spin.setValue(float(data.get("CambioUtensileX", 100.0)))                # Cambio utensile X
            self.home_z_spin.setValue(float(data.get("CambioUtensileZ", 100.0)))                # Cambio utensile Z
            self.x_mode_combo.setCurrentText(data.get("ModoProgrammazioneX", "Diametrale (Diametro)")) # Modo X
            self.turret_pos_combo.setCurrentText(data.get("PosizioneTorretta", "Posteriore (+X)")) # Lato torretta
            self.max_rpm_spin.setValue(int(data.get("GiriMaxMandrino", 2500)))                  # Giri max
            self.spindle_dir_combo.setCurrentText(data.get("SensoRotazioneDefault", "Orario (M03)")) # M03/M04
            self.coolant_combo.setCurrentText(data.get("RefrigeranteDefault", "Attivo (M08)"))  # M08/M09
            self.post_combo.setCurrentText(data.get("PostProcessor", "Fanuc"))                  # Post-Processor
            self.lbl_wcs_status.setText(f"Profilo '{key}' caricato dall'Archivio!")             # Messaggio di conferma
        finally:                                                                                # Sblocca i segnali
            self.is_updating = False                                                            # Riabilita
        self.trigger_update()                                                                   # Aggiorna la vista 3D

    def elimina_profilo_da_db(self):                                                            # Elimina il profilo selezionato dall'archivio su disco
        db = load_machines_db()                                                                 # Carica il database
        key = self.db_combo.currentText()                                                       # Chiave selezionata
        if key in db:                                                                           # Se presente
            del db[key]                                                                         # Rimuove dal dizionario
            save_machines_db(db)                                                                # Aggiorna il file JSON
            self.aggiorna_combo_db()                                                            # Aggiorna la tendina

    def carica_dati_da_oggetto(self, obj):                                                      # Popola la UI quando si riapre Setup_Macchina con doppio click
        obj.Proxy.ensure_properties(obj)                                                        # Assicura che tutte le proprietà esistano
        self.name_input.setText(str(getattr(obj, "MachineName", "Tornio CNC Standard")))        # Nome macchina
        self.wcs_code_combo.setCurrentText(str(getattr(obj, "SistemaCoordinate", "G54")))       # G54..G59
        orig = getattr(obj, "Origine", FreeCAD.Vector(0, 0, 0))                                 # Legge il vettore Origine
        self.ox_spin.setValue(float(orig.x))                                                    # Coordinata X0
        self.oy_spin.setValue(float(orig.y))                                                    # Coordinata Y0
        self.oz_spin.setValue(float(orig.z))                                                    # Coordinata Z0
        self.dim_sym_spin.setValue(float(getattr(obj, "DimensioneSimbolo", 30.0)))              # Scala frecce
        self.chk_show_safe.setChecked(bool(getattr(obj, "MostraPianoSicurezza", True)))         # Mostra piano sicurezza
        self.safe_x_spin.setValue(float(getattr(obj, "SicurezzaX", 5.0)))                       # Sicurezza X
        self.safe_z_spin.setValue(float(getattr(obj, "SicurezzaZ", 5.0)))                       # Sicurezza Z
        self.home_x_spin.setValue(float(getattr(obj, "CambioUtensileX", 100.0)))                # Cambio utensile X
        self.home_z_spin.setValue(float(getattr(obj, "CambioUtensileZ", 100.0)))                # Cambio utensile Z
        self.x_mode_combo.setCurrentText(str(getattr(obj, "ModoProgrammazioneX", "Diametrale (Diametro)"))) # Modo X
        self.turret_pos_combo.setCurrentText(str(getattr(obj, "PosizioneTorretta", "Posteriore (+X)"))) # Lato torretta
        self.max_rpm_spin.setValue(int(getattr(obj, "GiriMaxMandrino", 2500)))                  # Giri max
        self.spindle_dir_combo.setCurrentText(str(getattr(obj, "SensoRotazioneDefault", "Orario (M03)"))) # M03/M04
        self.coolant_combo.setCurrentText(str(getattr(obj, "RefrigeranteDefault", "Attivo (M08)"))) # M08/M09
        self.post_combo.setCurrentText(str(getattr(obj, "PostProcessor", "Fanuc")))             # Post-Processor

    def pulisci_anteprima_setup(self, doc):                                                     # Rimuove in modo sicuro l'oggetto di anteprima temporanea
        if not doc:                                                                             # Controlla esistenza documento
            return                                                                              # Esce
        if hasattr(self, "preview_wcs") and self.preview_wcs:                                   # Se esiste il riferimento preview_wcs
            try:                                                                                # Tenta la rimozione
                if doc.getObject(self.preview_wcs.Name):                                        # Se è presente nel documento
                    doc.removeObject(self.preview_wcs.Name)                                     # Lo elimina
            except Exception:                                                                   # Ignora errori
                pass                                                                            # Continua
            self.preview_wcs = None                                                             # Azzera il riferimento
        for obj in list(doc.Objects):                                                           # Pulisce eventuali residui precedenti
            if obj.Name.startswith("TMP_WCS_Preview") or "ANTEPRIMA WCS" in getattr(obj, "Label", "").upper():
                try: doc.removeObject(obj.Name)                                                 # Rimuove l'oggetto temporaneo
                except Exception: pass                                                          # Ignora errori

    def getStandardButtons(self):                                                               # Pulsanti standard OK e Cancel del pannello Task
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel                # Restituisce OK | Cancel

    def accept(self):                                                                           # Conferma e salva l'oggetto Setup_Macchina
        doc = FreeCAD.ActiveDocument                                                            # Ottiene il documento attivo
        if not doc:                                                                             # Controllo sicurezza
            return False                                                                        # Esce

        nome_macchina = self.name_input.text().strip() or "Tornio CNC Standard"                 # Legge il nome macchina
        if self.edit_obj and doc.getObject(self.edit_obj.Name):                                 # Se stavamo modificando un Setup esistente
            setup_obj = self.edit_obj                                                           # Usa l'oggetto esistente
        elif doc.getObject("Setup_Macchina"):                                                   # Se esiste già Setup_Macchina nel documento
            setup_obj = doc.getObject("Setup_Macchina")                                         # Lo riutilizza senza creare duplicati
        else:                                                                                   # Altrimenti crea il nuovo oggetto parametrico
            setup_obj = doc.addObject("Part::FeaturePython", "Setup_Macchina")                  # Crea Part::FeaturePython col nome atteso dagli altri moduli
            LatheSetupObject(setup_obj)                                                         # Inizializza il Proxy
            ViewProviderLatheSetup(setup_obj.ViewObject)                                        # Inizializza il ViewProvider con doppio click

        setup_obj.Proxy._is_executing = True                                                    # Sospende il ricalcolo finché tutte le proprietà non sono scritte
        try:                                                                                    # Assegna tutte le proprietà all'oggetto
            setup_obj.Proxy.ensure_properties(setup_obj)                                        # Garantisce la presenza di tutte le proprietà
            setup_obj.MachineName = nome_macchina                                               # Salva il nome macchina
            setup_obj.SistemaCoordinate = self.wcs_code_combo.currentText()                     # Salva G54..G59
            setup_obj.Label = f"Setup ({setup_obj.SistemaCoordinate} - {nome_macchina})"        # Etichetta chiara nell'albero
            setup_obj.Origine = FreeCAD.Vector(self.ox_spin.value(), self.oy_spin.value(), self.oz_spin.value()) # Salva il vettore Origine WCS
            setup_obj.DimensioneSimbolo = self.dim_sym_spin.value()                             # Salva scala frecce
            setup_obj.MostraPianoSicurezza = self.chk_show_safe.isChecked()                     # Salva flag piano sicurezza
            setup_obj.SicurezzaX = self.safe_x_spin.value()                                     # Salva distanza sicurezza X
            setup_obj.SicurezzaZ = self.safe_z_spin.value()                                     # Salva distanza sicurezza Z
            setup_obj.CambioUtensileX = self.home_x_spin.value()                                # Salva quota X cambio utensile
            setup_obj.CambioUtensileZ = self.home_z_spin.value()                                # Salva quota Z cambio utensile
            setup_obj.ModoProgrammazioneX = self.x_mode_combo.currentText()                     # Salva modalità Diametrale/Radiale
            setup_obj.PosizioneTorretta = self.turret_pos_combo.currentText()                   # Salva lato torretta Posteriore/Anteriore
            setup_obj.GiriMaxMandrino = self.max_rpm_spin.value()                               # Salva limite giri G50/G92
            setup_obj.SensoRotazioneDefault = self.spindle_dir_combo.currentText()              # Salva senso rotazione M03/M04
            setup_obj.RefrigeranteDefault = self.coolant_combo.currentText()                    # Salva stato refrigerante M08/M09
            setup_obj.PostProcessor = self.post_combo.currentText()                             # Salva il Post-Processor
        finally:                                                                                # Riabilita il Proxy
            setup_obj.Proxy._is_executing = False                                               # Sblocca

        setup_obj.Proxy.execute(setup_obj)                                                      # Costruisce la terna finale e riallinea Utensili/Torretta/Grezzo
        if hasattr(setup_obj, "ViewObject") and setup_obj.ViewObject:                           # Ripristina la visibilità
            setup_obj.ViewObject.Visibility = True                                              # Rende visibile Setup_Macchina

        if self.chk_save_db.isChecked():                                                        # Se è attiva la spunta di salvataggio su disco
            self.salva_profilo_in_db(setup_obj)                                                 # Salva il profilo in MachineLibrary

        self.pulisci_anteprima_setup(doc)                                                       # Elimina l'anteprima provvisoria TMP_WCS_Preview
        doc.recompute()                                                                         # Ricalcola il documento
        if FreeCADGui.ActiveDocument:                                                           # Se la GUI è attiva
            FreeCADGui.ActiveDocument.resetEdit()                                               # Esce dalla modalità Edit
        FreeCADGui.Control.closeDialog()                                                        # Chiude il pannello Task
        return True                                                                             # Conferma

    def reject(self):                                                                           # Annulla le modifiche e ripristina lo stato precedente
        doc = FreeCAD.ActiveDocument                                                            # Ottiene il documento attivo
        if doc:                                                                                 # Se il documento esiste
            self.pulisci_anteprima_setup(doc)                                                   # Elimina subito l'anteprima provvisoria
            if self.edit_obj and doc.getObject(self.edit_obj.Name):                             # Se stavamo modificando un Setup esistente
                if "Origine" in self.backup_dati:                                               # Ripristina l'Origine precedente
                    self.edit_obj.Origine = self.backup_dati["Origine"]                         # Vettore Origine originale
                if hasattr(self.edit_obj, "ViewObject") and self.edit_obj.ViewObject:           # Ripristina la visibilità originale
                    self.edit_obj.ViewObject.Visibility = self.backup_dati.get("Visibility", True)
            doc.recompute()                                                                     # Aggiorna il documento
        if FreeCADGui.ActiveDocument:                                                           # Se la GUI è attiva
            FreeCADGui.ActiveDocument.resetEdit()                                               # Esce dalla modalità Edit
        FreeCADGui.Control.closeDialog()                                                        # Chiude il pannello
        return True                                                                             # Conferma