import FreeCAD                                                                                  # Importa il modulo base di FreeCAD
import FreeCADGui                                                                               # Importa il modulo interfaccia grafica di FreeCAD
import Part                                                                                     # Importa il modulo geometrico Part
import math                                                                                     # Importa le funzioni matematiche
import os                                                                                       # Importa il modulo per gestire percorsi e cartelle
import json                                                                                     # Importa il modulo JSON per salvare configurazioni grezzo/mandrino
from PySide import QtCore, QtGui                                                                # Importa i moduli grafici PySide
try:                                                                                            # Tenta di importare QtWidgets per compatibilità Qt5/Qt6
    from PySide import QtWidgets                                                                # Assegna QtWidgets
except ImportError:                                                                             # Fallback per versioni meno recenti
    QtWidgets = QtGui                                                                           # Usa QtGui come alias di QtWidgets


TIPI_GREZZO = ["Cilindro Pieno", "Tubo Forato", "Barra Quadra", "Barra Esagonale"]              # Elenco completo delle forme di barra supportate


def get_stock_lib_dir():                                                                        # Restituisce la cartella su disco per l'archivio grezzi e mandrini
    base_dir = os.path.dirname(os.path.abspath(__file__))                                       # Cartella del Workbench corrente
    lib_dir = os.path.join(base_dir, "StockLibrary")                                            # Sottocartella StockLibrary
    os.makedirs(lib_dir, exist_ok=True)                                                         # Crea la cartella se non esiste
    return lib_dir                                                                              # Restituisce il percorso completo


def get_stock_db_file():                                                                        # Restituisce il percorso del file JSON dei grezzi/mandrini
    return os.path.join(get_stock_lib_dir(), "stocks_db.json")                                  # Percorso completo di stocks_db.json


def load_stocks_db():                                                                           # Legge il database dei grezzi/mandrini salvati su disco
    db_path = get_stock_db_file()                                                               # Ottiene il percorso del file JSON
    if os.path.exists(db_path):                                                                 # Controlla se il file esiste
        try:                                                                                    # Tenta la lettura del file JSON
            with open(db_path, "r", encoding="utf-8") as f:                                     # Apre il file in modalità lettura
                return json.load(f)                                                             # Restituisce il dizionario caricato
        except Exception as e:                                                                  # Cattura eventuali errori di lettura
            FreeCAD.Console.PrintError(f"Errore lettura archivio grezzi: {e}\n")                # Stampa l'errore in console
    return {}                                                                                   # Restituisce un dizionario vuoto se non esiste


def save_stocks_db(db_data):                                                                    # Salva il database dei grezzi/mandrini su disco
    db_path = get_stock_db_file()                                                               # Ottiene il percorso del file JSON
    try:                                                                                        # Tenta la scrittura su disco
        with open(db_path, "w", encoding="utf-8") as f:                                         # Apre il file in scrittura
            json.dump(db_data, f, indent=4, ensure_ascii=False)                                 # Scrive il dizionario formattato
    except Exception as e:                                                                      # Cattura eventuali errori
        FreeCAD.Console.PrintError(f"Errore salvataggio archivio grezzi: {e}\n")                # Stampa l'errore in console


def get_wcs_origin(doc=None):                                                                   # Legge l'origine del WCS (Setup_Macchina)
    if doc is None:                                                                             # Se il documento non è specificato
        doc = FreeCAD.ActiveDocument                                                            # Usa il documento attivo
    if doc and doc.getObject("Setup_Macchina"):                                                 # Se esiste l'oggetto Setup_Macchina
        setup_obj = doc.getObject("Setup_Macchina")                                             # Ottiene il riferimento all'oggetto
        if hasattr(setup_obj, "Origine"):                                                       # Controlla che abbia la proprietà Origine
            return FreeCAD.Vector(setup_obj.Origine)                                            # Restituisce il vettore Origine del WCS
    return FreeCAD.Vector(0.0, 0.0, 0.0)                                                        # Restituisce (0,0,0) se il WCS non è presente


def applica_colori_e_trasparenza(vobj, shape, face_colors_3, face_alphas, trasp_default=0):     # Applica DiffuseColor con supporto trasparenza per tutte le versioni FreeCAD
    if not vobj or not shape or len(face_colors_3) != len(shape.Faces):                         # Verifica la corrispondenza esatta tra facce e colori
        return                                                                                  # Esce se i dati non corrispondono
    try:                                                                                        # Tenta di applicare tuple a 4 canali (R, G, B, Alpha/Trasparenza)
        cols_4 = [(c[0], c[1], c[2], a) for c, a in zip(face_colors_3, face_alphas)]            # Compone la lista a 4 elementi per ogni faccia
        vobj.DiffuseColor = cols_4                                                              # Assegna i colori con trasparenza selettiva solo sul grezzo
        vobj.Transparency = int(trasp_default)                                                  # Imposta anche la proprietà Transparency generale per sicurezza
    except Exception:                                                                           # Fallback se la versione di Coin3D accetta solo 3 canali
        vobj.Transparency = int(trasp_default)                                                  # Imposta PRIMA la trasparenza generale
        vobj.DiffuseColor = face_colors_3                                                       # Applica i colori RGB


def costruisci_geometria_grezzo_e_presa(                                                        # Genera i solidi di Grezzo, Autocentrante/Griffe e Contropunta
    wcs, forma_grezzo, d_ext, d_int, lung_tot, sovra_z, sovra_x, trasp_perc,                    # Parametri tipo, misure, sovrametalli Z+/X+ e trasparenza
    mostra_mandrino, d_mandrino, spess_mandrino, presa_griffe, h_griffe, marg_sic,              # Parametri autocentrante e griffe
    usa_contropunta, d_contropunta, lung_cono_cp                                                # Parametri contropunta
):                                                                                              # Inizio funzione geometrica
    sx = max(float(sovra_x), 0.0)                                                               # Sovrametallo radiale su X+ (mm sul raggio)
    r_chiave = max((float(d_ext) / 2.0) + sx, 1.0)                                              # Raggio effettivo (o semichiave S/2) maggiorato del sovrametallo X+
    r_int = max(min(float(d_int) / 2.0, r_chiave - 0.5), 0.0)                                   # Raggio del foro interno (se > 0)
    L = max(float(lung_tot), 2.0)                                                               # Lunghezza totale della barra grezza
    sz = float(sovra_z)                                                                         # Sovrametallo frontale davanti a Z = 0

    z_front = wcs.z + sz                                                                        # Quota Z della faccia anteriore del grezzo
    z_back = z_front - L                                                                        # Quota Z della faccia posteriore del grezzo
    pos_base_grezzo = FreeCAD.Vector(wcs.x, wcs.y, z_back)                                      # Punto di partenza posteriore del grezzo

    if forma_grezzo == "Barra Quadra":                                                          # Caso Barra Quadra (lato effettivo = d_ext + 2*sovra_x)
        r_ingombro_rot = r_chiave / math.cos(math.pi / 4.0)                                     # Raggio massimo sullo spigolo in rotazione (S_eff / sqrt(2))
        punti_q = [                                                                             # Vertici del quadrato centrato sull'asse WCS
            FreeCAD.Vector(wcs.x + r_chiave, wcs.y - r_chiave, z_back),                         # Vertice 1 (+X, -Y)
            FreeCAD.Vector(wcs.x + r_chiave, wcs.y + r_chiave, z_back),                         # Vertice 2 (+X, +Y)
            FreeCAD.Vector(wcs.x - r_chiave, wcs.y + r_chiave, z_back),                         # Vertice 3 (-X, +Y)
            FreeCAD.Vector(wcs.x - r_chiave, wcs.y - r_chiave, z_back),                         # Vertice 4 (-X, -Y)
            FreeCAD.Vector(wcs.x + r_chiave, wcs.y - r_chiave, z_back)                          # Chiusura poligono sul Vertice 1
        ]                                                                                       # Fine vertici quadrato
        solido_pieno = Part.Face(Part.makePolygon(punti_q)).extrude(FreeCAD.Vector(0, 0, L))    # Estrude il prisma a sezione quadrata lungo +Z
        num_griffe = 4                                                                          # Usa 4 griffe a 90° per serrare le 4 facce piane del quadro
    elif forma_grezzo == "Barra Esagonale":                                                     # Caso Barra Esagonale (chiave effettiva = d_ext + 2*sovra_x)
        r_ingombro_rot = r_chiave / math.cos(math.pi / 6.0)                                     # Raggio massimo sullo spigolo dell'esagono (S_eff / sqrt(3))
        punti_hex = []                                                                          # Lista vertici dell'esagono
        for i in range(6):                                                                      # Calcola i 6 vertici orientando una faccia piana a 0° (+X)
            ang_v = (i * math.pi / 3.0) + (math.pi / 6.0)                                       # Angolo del vertice (+30°, +90°, +150°...)
            px = wcs.x + r_ingombro_rot * math.cos(ang_v)                                       # Coordinata X del vertice esagonale
            py = wcs.y + r_ingombro_rot * math.sin(ang_v)                                       # Coordinata Y del vertice esagonale
            punti_hex.append(FreeCAD.Vector(px, py, z_back))                                    # Aggiunge il vertice
        punti_hex.append(punti_hex[0])                                                          # Chiude il poligono esagonale
        solido_pieno = Part.Face(Part.makePolygon(punti_hex)).extrude(FreeCAD.Vector(0, 0, L))  # Estrude il prisma esagonale lungo +Z
        num_griffe = 3                                                                          # Usa 3 griffe a 120° che appoggiano sulle facce piane dell'esagono
    else:                                                                                       # Caso Cilindro Pieno o Tubo Forato
        r_ingombro_rot = r_chiave                                                               # Il raggio massimo coincide col raggio esterno maggiorato
        solido_pieno = Part.makeCylinder(r_chiave, L, pos_base_grezzo, FreeCAD.Vector(0, 0, 1)) # Crea il cilindro pieno col raggio comprensivo di sovrametallo X+
        num_griffe = 3                                                                          # Autocentrante standard a 3 griffe a 120°

    if r_int > 0.05 and (forma_grezzo != "Cilindro Pieno"):                                     # Se c'è un foro interno (su Tubo, Quadro forato o Esagono forato)
        cil_int = Part.makeCylinder(r_int, L + 2.0, pos_base_grezzo - FreeCAD.Vector(0, 0, 1.0), FreeCAD.Vector(0, 0, 1)) # Cilindro di foratura
        try:                                                                                    # Tenta la sottrazione booleana del foro centrale
            solido_grezzo = solido_pieno.cut(cil_int)                                           # Ottiene la barra forata internamente
        except Exception:                                                                       # In caso di errore geometrico
            solido_grezzo = solido_pieno                                                        # Mantiene il solido pieno
    else:                                                                                       # Se non è previsto il foro interno
        solido_grezzo = solido_pieno                                                            # Usa direttamente il solido pieno

    shapes = []                                                                                 # Lista dei solidi da comporre
    face_colors_3 = []                                                                          # Lista tuple RGB a 3 valori
    face_alphas = []                                                                            # Lista valori di opacità/trasparenza per singola faccia

    trasp_norm = max(0.0, min(float(trasp_perc) / 100.0, 0.90))                                 # Converte la trasparenza (0..90%) in frazione 0.0..0.90
    opacita_grezzo = 1.0 - trasp_norm                                                           # Calcola l'opacità del grezzo (1.0 = opaco, 0.45 = semitrasparente)

    shapes.append(solido_grezzo)                                                                # Aggiunge il grezzo come primo solido
    face_colors_3.extend([(0.85, 0.65, 0.25)] * len(solido_grezzo.Faces))                       # Colora il grezzo in bronzo/ottone chiaro
    face_alphas.extend([opacita_grezzo] * len(solido_grezzo.Faces))                             # Applica la trasparenza alle facce del grezzo

    z_punta_griffe = z_back + max(float(presa_griffe), 0.0)                                     # Quota Z dove arrivano i morsetti delle griffe
    z_limite_sicurezza = z_punta_griffe + max(float(marg_sic), 0.0)                             # Quota Z limite di sicurezza anti-collisione mandrino

    if mostra_mandrino:                                                                         # Se è attiva la visualizzazione dell'autocentrante
        r_chuck = max(float(d_mandrino) / 2.0, r_ingombro_rot + 15.0)                           # Raggio del corpo autocentrante (si adatta se il grezzo cresce)
        sp_chuck = max(float(spess_mandrino), 20.0)                                             # Spessore assiale del corpo autocentrante
        pos_chuck = FreeCAD.Vector(wcs.x, wcs.y, z_back - sp_chuck)                             # Posizione del corpo mandrino dietro al grezzo
        corpo_mandrino = Part.makeCylinder(r_chuck, sp_chuck, pos_chuck, FreeCAD.Vector(0, 0, 1)) # Cilindro del corpo mandrino
        shapes.append(corpo_mandrino)                                                           # Aggiunge il corpo mandrino
        face_colors_3.extend([(0.22, 0.24, 0.27)] * len(corpo_mandrino.Faces))                  # Colora il mandrino in grigio antracite scuro
        face_alphas.extend([1.0] * len(corpo_mandrino.Faces))                                   # Mantiene il mandrino solido e opaco

        lung_griffa_z = max(float(presa_griffe), 5.0)                                           # Lunghezza assiale di presa delle griffe lungo Z
        alt_rad_griffa = max(float(h_griffe), min(r_chuck - r_chiave, 35.0))                    # Altezza radiale di ciascuna griffa
        larg_griffa = max(r_chuck * 0.20, 12.0)                                                 # Spessore tangenziale della griffa
        passo_ang = 360.0 / float(num_griffe)                                                   # 120° per 3 griffe (tondo/esagono), 90° per 4 griffe (quadro)

        for i in range(num_griffe):                                                             # Costruisce le griffe attorno alla barra maggiorata
            ang = i * passo_ang                                                                 # Angolo della griffa i-esima
            b1 = Part.makeBox(                                                                  # Base principale della griffa a contatto con r_chiave
                alt_rad_griffa, larg_griffa, lung_griffa_z,                                     # Dimensioni radiali, tangenziali e assiali
                FreeCAD.Vector(r_chiave, -larg_griffa / 2.0, z_back)                            # Posizionata a contatto con r_chiave (incluso sovrametallo X+)
            )                                                                                   # Fine blocco base griffa
            b2 = Part.makeBox(                                                                  # Gradino esterno della griffa
                alt_rad_griffa * 0.55, larg_griffa, lung_griffa_z * 0.6,                        # Dimensioni del gradino esterno
                FreeCAD.Vector(r_chiave + alt_rad_griffa * 0.45, -larg_griffa / 2.0, z_back)    # Posizionato sulla parte esterna della griffa
            )                                                                                   # Fine gradino griffa
            try:                                                                                # Unisce base e gradino
                griffa = b1.fuse(b2)                                                            # Crea il solido della griffa a gradino
            except Exception:                                                                   # Fallback
                griffa = b1                                                                     # Usa il blocco base
            griffa.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), ang)                # Ruota la griffa attorno a Z
            griffa.translate(FreeCAD.Vector(wcs.x, wcs.y, 0.0))                                 # Allinea all'asse X, Y del WCS
            shapes.append(griffa)                                                               # Aggiunge la griffa alla lista solidi
            face_colors_3.extend([(0.40, 0.42, 0.45)] * len(griffa.Faces))                      # Colora le griffe in acciaio temprato grigio medio
            face_alphas.extend([1.0] * len(griffa.Faces))                                       # Mantiene le griffe opache

        if marg_sic > 0.1:                                                                      # Disegna l'anello rosso del limite collisione griffe
            r_lim = max(r_ingombro_rot, r_chiave + alt_rad_griffa) + 4.0                        # Raggio dell'anello rosso di sicurezza
            pos_lim = FreeCAD.Vector(wcs.x, wcs.y, z_limite_sicurezza)                          # Posizionato esattamente a Z_Limite_Mandrino
            c_out = Part.makeCylinder(r_lim, 0.8, pos_lim, FreeCAD.Vector(0, 0, 1))             # Disco esterno dell'anello
            c_in = Part.makeCylinder(max(r_lim - 1.8, r_ingombro_rot), 0.8, pos_lim, FreeCAD.Vector(0, 0, 1)) # Foro interno dell'anello
            try:                                                                                # Scava l'anello rosso
                anello_collisione = c_out.cut(c_in)                                             # Ottiene l'anello circolare
                shapes.append(anello_collisione)                                                # Aggiunge l'anello di sicurezza
                face_colors_3.extend([(0.95, 0.15, 0.15)] * len(anello_collisione.Faces))       # Colora l'anello in Rosso vivo (Zona Vietata)
                face_alphas.extend([1.0] * len(anello_collisione.Faces))                        # Anello opaco ben visibile
            except Exception:                                                                   # Ignora eventuali errori
                pass                                                                            # Continua

    if usa_contropunta:                                                                         # Se è attivo il supporto contropunta a destra (Z+)
        r_cp = max(float(d_contropunta) / 2.0, 8.0)                                             # Raggio del corpo contropunta
        l_cono = max(float(lung_cono_cp), 15.0)                                                 # Lunghezza della punta conica rotante
        penetrazione = min(r_cp * 0.15, 3.0)                                                    # Leggero invito del cono nel centro frontale del grezzo
        pt_vertice_cp = FreeCAD.Vector(wcs.x, wcs.y, z_front - penetrazione)                    # Vertice del cono sul fronte del pezzo
        cono_cp = Part.makeCone(0.0, r_cp, l_cono, pt_vertice_cp, FreeCAD.Vector(0, 0, 1))      # Cono della contropunta che si apre verso +Z
        corpo_cp = Part.makeCylinder(r_cp, l_cono * 1.5, pt_vertice_cp + FreeCAD.Vector(0, 0, l_cono), FreeCAD.Vector(0, 0, 1)) # Cannotto contropunta
        try:                                                                                    # Unisce cono e cannotto
            contropunta = cono_cp.fuse(corpo_cp)                                                # Solido contropunta completo
        except Exception:                                                                       # Fallback
            contropunta = cono_cp                                                               # Usa solo il cono
        shapes.append(contropunta)                                                              # Aggiunge la contropunta
        face_colors_3.extend([(0.70, 0.72, 0.75)] * len(contropunta.Faces))                     # Colora la contropunta in acciaio chiaro
        face_alphas.extend([1.0] * len(contropunta.Faces))                                      # Contropunta opaca

    comp = Part.makeCompound(shapes)                                                            # Compone tutti gli elementi in un unico oggetto
    diam_max_rotazione = r_ingombro_rot * 2.0                                                   # Diametro massimo di inviluppo sugli spigoli in rotazione
    return comp, face_colors_3, face_alphas, z_limite_sicurezza, diam_max_rotazione             # Restituisce compound, colori, alpha, Z limite e Ø inviluppo


class LatheStockObject:                                                                         # Classe Proxy per l'oggetto parametrico Grezzo_Macchina
    def __init__(self, obj):                                                                    # Costruttore del Proxy
        self._is_executing = False                                                              # Flag per evitare ricalcoli ricorsivi
        self.ensure_properties(obj)                                                             # Garantisce la presenza di tutte le proprietà
        obj.Proxy = self                                                                        # Collega il Proxy all'oggetto FreeCAD

    def ensure_properties(self, obj):                                                           # Aggiunge tutte le proprietà se non esistono
        if not hasattr(obj, "StockName"):                                                       # Nome della configurazione grezzo/mandrino
            obj.addProperty("App::PropertyString", "StockName", "Grezzo", "Nome configurazione grezzo").StockName = "Barra D50 x 100"
        if not hasattr(obj, "FormaGrezzo"):                                                     # Cilindro, Tubo, Quadro o Esagono
            obj.addProperty("App::PropertyEnumeration", "FormaGrezzo", "Grezzo", "Tipologia semilavorato")
            obj.FormaGrezzo = TIPI_GREZZO                                                       # Assegna i 4 tipi di barra
        else:                                                                                   # Aggiorna la lista enum se l'oggetto era stato creato prima
            curr_val = str(obj.FormaGrezzo)                                                     # Memorizza il valore attuale
            obj.FormaGrezzo = TIPI_GREZZO                                                       # Aggiorna le opzioni includendo Quadro ed Esagono
            if curr_val in TIPI_GREZZO:                                                         # Se il valore precedente è valido
                obj.FormaGrezzo = curr_val                                                      # Lo ripristina
        if not hasattr(obj, "DiametroEsterno"):                                                 # Diametro esterno o Lato/Chiave S base (mm)
            obj.addProperty("App::PropertyFloat", "DiametroEsterno", "Grezzo", "Diametro esterno o Chiave S base (mm)").DiametroEsterno = 50.0
        if not hasattr(obj, "DiametroMaxRotazione"):                                            # Diametro massimo sugli spigoli in rotazione (per il CAM)
            obj.addProperty("App::PropertyFloat", "DiametroMaxRotazione", "Grezzo", "Diametro inviluppo sugli spigoli (mm)").DiametroMaxRotazione = 54.0
        if not hasattr(obj, "DiametroForoInterno"):                                             # Diametro foro interno per tubi o barre forate (mm)
            obj.addProperty("App::PropertyFloat", "DiametroForoInterno", "Grezzo", "Diametro foro interno (mm)").DiametroForoInterno = 0.0
        if not hasattr(obj, "LunghezzaTotale"):                                                 # Lunghezza totale della barra (mm)
            obj.addProperty("App::PropertyFloat", "LunghezzaTotale", "Grezzo", "Lunghezza totale grezzo (mm)").LunghezzaTotale = 100.0
        if not hasattr(obj, "SovrametalloFrontaleZ"):                                           # Materiale davanti a Z=0 da intestare (mm)
            obj.addProperty("App::PropertyFloat", "SovrametalloFrontaleZ", "Sovrametalli", "Sovrametallo frontale su Z+ (mm)").SovrametalloFrontaleZ = 1.5
        if not hasattr(obj, "SovrametalloRadialeX"):                                            # Sovrametallo sul raggio aggiunto in tempo reale (mm)
            obj.addProperty("App::PropertyFloat", "SovrametalloRadialeX", "Sovrametalli", "Sovrametallo radiale su X+ (mm)").SovrametalloRadialeX = 0.0
        if not hasattr(obj, "TrasparenzaGrezzo"):                                               # Percentuale di trasparenza grafica (0..90%)
            obj.addProperty("App::PropertyInteger", "TrasparenzaGrezzo", "Grezzo", "Trasparenza visiva (0-90%)").TrasparenzaGrezzo = 55
        if not hasattr(obj, "MostraMandrino"):                                                  # Mostra/nasconde l'autocentrante e le griffe
            obj.addProperty("App::PropertyBool", "MostraMandrino", "Autocentrante", "Visualizza autocentrante e griffe").MostraMandrino = True
        if not hasattr(obj, "DiametroMandrino"):                                                # Diametro corpo autocentrante (default 160 mm)
            obj.addProperty("App::PropertyFloat", "DiametroMandrino", "Autocentrante", "Diametro corpo autocentrante (mm)").DiametroMandrino = 160.0
        if not hasattr(obj, "SpessoreMandrino"):                                                # Spessore corpo autocentrante (default 55 mm)
            obj.addProperty("App::PropertyFloat", "SpessoreMandrino", "Autocentrante", "Spessore corpo autocentrante (mm)").SpessoreMandrino = 55.0
        if not hasattr(obj, "LunghezzaPresaGriffe"):                                            # Lunghezza di presa del pezzo nelle griffe (mm)
            obj.addProperty("App::PropertyFloat", "LunghezzaPresaGriffe", "Autocentrante", "Lunghezza presa pezzo nelle griffe (mm)").LunghezzaPresaGriffe = 20.0
        if not hasattr(obj, "AltezzaGriffe"):                                                   # Altezza radiale delle griffe (mm)
            obj.addProperty("App::PropertyFloat", "AltezzaGriffe", "Autocentrante", "Altezza radiale griffe (mm)").AltezzaGriffe = 30.0
        if not hasattr(obj, "MargineSicurezzaGriffe"):                                          # Margine di sicurezza davanti alle griffe (mm)
            obj.addProperty("App::PropertyFloat", "MargineSicurezzaGriffe", "Autocentrante", "Distanza sicurezza dalle griffe (mm)").MargineSicurezzaGriffe = 3.0
        if not hasattr(obj, "Z_Limite_Mandrino"):                                               # Quota Z limite calcolata automaticamente per il CAM
            obj.addProperty("App::PropertyFloat", "Z_Limite_Mandrino", "Autocentrante", "Quota Z minima anti-collisione griffe (mm)").Z_Limite_Mandrino = -75.5
        if not hasattr(obj, "UsaContropunta"):                                                  # Attiva/disattiva la contropunta sul lato destro Z+
            obj.addProperty("App::PropertyBool", "UsaContropunta", "Contropunta", "Supporto contropunta su Z+").UsaContropunta = False
        if not hasattr(obj, "DiametroContropunta"):                                             # Diametro del cono/cannotto contropunta (mm)
            obj.addProperty("App::PropertyFloat", "DiametroContropunta", "Contropunta", "Diametro contropunta (mm)").DiametroContropunta = 30.0
        if not hasattr(obj, "LunghezzaConoContropunta"):                                        # Lunghezza del cono rotante (mm)
            obj.addProperty("App::PropertyFloat", "LunghezzaConoContropunta", "Contropunta", "Lunghezza punta conica (mm)").LunghezzaConoContropunta = 25.0

    def onDocumentRestored(self, obj):                                                          # Chiamato da FreeCAD alla riapertura del documento
        self._is_executing = False                                                              # Ripristina il flag di esecuzione
        self.ensure_properties(obj)                                                             # Verifica la presenza di tutte le proprietà

    def execute(self, obj):                                                                     # Ricalcola la geometria 3D di Grezzo, Griffe e Contropunta
        if getattr(self, "_is_executing", False):                                               # Evita cicli ricorsivi
            return                                                                              # Esce subito
        self._is_executing = True                                                               # Attiva il blocco di esecuzione
        try:                                                                                    # Blocco protetto di generazione 3D
            self.ensure_properties(obj)                                                         # Verifica tutte le proprietà
            wcs = get_wcs_origin(obj.Document)                                                  # Legge l'origine del Setup_Macchina (WCS)
            forma_scelta = str(obj.FormaGrezzo)                                                 # Legge il tipo di barra
            d_int = obj.DiametroForoInterno if forma_scelta != "Cilindro Pieno" else 0.0        # Usa il diametro foro se non è cilindro pieno
            trasp = max(0, min(int(obj.TrasparenzaGrezzo), 90))                                 # Percentuale trasparenza (0..90%)
            comp, cols_3, alphas, z_lim, d_rot = costruisci_geometria_grezzo_e_presa(           # Costruisce i solidi 3D includendo SovrametalloRadialeX
                wcs, forma_scelta, obj.DiametroEsterno, d_int,                                  # Tipo barra, diametro/chiave base e foro
                obj.LunghezzaTotale, obj.SovrametalloFrontaleZ, obj.SovrametalloRadialeX, trasp,# Lunghezza, sovrametalli Z+/X+ e trasparenza
                obj.MostraMandrino, obj.DiametroMandrino, obj.SpessoreMandrino,                 # Quote corpo mandrino
                obj.LunghezzaPresaGriffe, obj.AltezzaGriffe, obj.MargineSicurezzaGriffe,        # Quote griffe e sicurezza
                obj.UsaContropunta, obj.DiametroContropunta, obj.LunghezzaConoContropunta       # Quote contropunta
            )                                                                                   # Fine generazione geometrica
            obj.Z_Limite_Mandrino = z_lim                                                       # Aggiorna la quota Z minima sicura per le lavorazioni
            obj.DiametroMaxRotazione = d_rot                                                    # Salva il diametro massimo sugli spigoli per il CAM
            obj.Shape = comp                                                                    # Assegna la Shape finale all'oggetto
            if hasattr(obj, "ViewObject") and obj.ViewObject:                                   # Applica colori e trasparenza nella vista 3D
                applica_colori_e_trasparenza(obj.ViewObject, obj.Shape, cols_3, alphas, trasp)  # Applica la trasparenza al grezzo
        except Exception as e:                                                                  # Cattura errori imprevisti
            FreeCAD.Console.PrintError(f"Errore ricalcolo Grezzo: {e}\n")                       # Stampa l'errore in console
        finally:                                                                                # Eseguito sempre in uscita
            self._is_executing = False                                                          # Rilascia il blocco

    def onChanged(self, obj, prop):                                                             # Intercetta le modifiche live dalle Proprietà di FreeCAD
        if getattr(self, "_is_executing", False):                                               # Evita loop ricorsivi
            return                                                                              # Esce
        props_live = [                                                                          # Proprietà che scatenano il ricalcolo 3D immediato
            "FormaGrezzo", "DiametroEsterno", "DiametroForoInterno",                            # Dimensioni grezzo
            "LunghezzaTotale", "SovrametalloFrontaleZ", "SovrametalloRadialeX",                 # Lunghezza e sovrametalli Z+ e X+
            "TrasparenzaGrezzo", "MostraMandrino", "DiametroMandrino",                          # Aspetto e mandrino
            "SpessoreMandrino", "LunghezzaPresaGriffe", "AltezzaGriffe",                        # Griffe
            "MargineSicurezzaGriffe", "UsaContropunta",                                         # Sicurezza e contropunta
            "DiametroContropunta", "LunghezzaConoContropunta"                                   # Dimensioni contropunta
        ]                                                                                       # Fine lista proprietà
        if prop in props_live:                                                                  # Se è cambiata una proprietà geometrica o il sovrametallo X+
            self.execute(obj)                                                                   # Aggiorna subito il 3D
        elif prop == "StockName":                                                               # Se cambia il nome del grezzo
            if hasattr(obj, "StockName") and obj.StockName:                                     # Verifica validità
                obj.Label = f"Grezzo ({obj.StockName})"                                         # Aggiorna l'etichetta nell'albero

    def __getstate__(self):                                                                     # Serializzazione per salvataggio file FCStd
        return None                                                                             # Nessun dato speciale

    def __setstate__(self, state):                                                              # Deserializzazione all'apertura file FCStd
        self._is_executing = False                                                              # Ripristina il flag
        return None                                                                             # Fine


class ViewProviderLatheStock:                                                                   # ViewProvider per gestire doppio click e icona del Grezzo
    def __init__(self, vobj):                                                                   # Costruttore ViewProvider
        vobj.Proxy = self                                                                       # Collega il Proxy alla vista

    def getIcon(self):                                                                          # Icona nell'albero
        return "Part_Cylinder"                                                                  # Icona cilindrica per il grezzo di tornitura

    def attach(self, vobj):                                                                     # Collega gli oggetti alla vista
        self.ViewObject = vobj                                                                  # Riferimento ViewObject
        self.Object = vobj.Object                                                               # Riferimento Object

    def updateData(self, vobj, prop):                                                           # Aggiornamento dati
        return                                                                                  # Gestito da execute

    def onDelete(self, vobj, subelements):                                                      # Autorizza l'eliminazione dall'albero
        return True                                                                             # Sempre consentito

    def doubleClicked(self, vobj):                                                              # Doppio click su Grezzo_Macchina nell'albero
        if not FreeCADGui.Control.activeDialog():                                               # Se non c'è già un pannello aperto
            panel = LatheStockPanel(edit_obj=vobj.Object)                                       # Apre il pannello caricando il Grezzo esistente
            FreeCADGui.Control.showDialog(panel)                                                # Mostra il pannello nella scheda Azioni
        return True                                                                             # Evento gestito

    def setEdit(self, vobj, mode):                                                              # Modalità Edit standard
        if mode == 0:                                                                           # Modifica base
            if not FreeCADGui.Control.activeDialog():                                           # Evita doppia apertura
                panel = LatheStockPanel(edit_obj=vobj.Object)                                   # Crea il pannello in modalità modifica
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


class LatheStockPanel:                                                                          # Pannello UI per Grezzo, Autocentrante/Griffe e Contropunta
    def __init__(self, edit_obj=None):                                                          # Costruttore del pannello (nuovo o modifica)
        doc = FreeCAD.ActiveDocument                                                            # Ottiene il documento attivo
        if edit_obj is None and doc and doc.getObject("Grezzo_Macchina"):                       # Se esiste già Grezzo_Macchina nel progetto
            edit_obj = doc.getObject("Grezzo_Macchina")                                         # Lo apre automaticamente in modifica senza duplicarlo

        self.edit_obj = edit_obj                                                                # Memorizza l'oggetto in modifica
        self.is_updating = True                                                                 # Blocca i segnali durante la costruzione della UI

        self.pulisci_anteprima_grezzo(doc)                                                      # Elimina eventuali anteprime temporanee rimaste appese
        if self.edit_obj and hasattr(self.edit_obj, "ViewObject") and self.edit_obj.ViewObject: # Se stiamo modificando un Grezzo esistente
            self.edit_obj.ViewObject.Visibility = False                                         # Nasconde l'originale durante l'anteprima live

        self.form = QtWidgets.QWidget()                                                         # Crea il contenitore principale della UI
        self.form.setMinimumWidth(240)                                                          # Larghezza minima compatta per non tagliare a destra
        self.layout = QtWidgets.QVBoxLayout(self.form)                                          # Layout verticale principale
        self.layout.setContentsMargins(4, 4, 4, 4)                                              # Margini ridotti per adattarsi al pannello laterale

        self.grp_db = QtWidgets.QGroupBox("Archivio Grezzi / Mandrini")                         # Gruppo archivio configurazioni su disco
        self.lyt_db = QtWidgets.QVBoxLayout(self.grp_db)                                        # Layout verticale archivio
        self.db_combo = QtWidgets.QComboBox()                                                   # Tendina con le configurazioni salvate
        self.db_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon) # Adatta la tendina al pannello
        self.db_combo.setMinimumContentsLength(10)                                              # Evita tagli a destra
        self.lyt_db.addWidget(self.db_combo)                                                    # Tendina su tutta la larghezza

        self.lyt_db_btns = QtWidgets.QHBoxLayout()                                              # Riga pulsanti Carica ed Elimina
        self.btn_load_db = QtWidgets.QPushButton("Carica Grezzo")                               # Pulsante carica da archivio
        self.btn_load_db.clicked.connect(self.carica_grezzo_da_db)                              # Collega il caricamento
        self.btn_del_db = QtWidgets.QPushButton("Elimina")                                      # Pulsante elimina da archivio
        self.btn_del_db.clicked.connect(self.elimina_grezzo_da_db)                              # Collega l'eliminazione
        self.lyt_db_btns.addWidget(self.btn_load_db)                                            # Aggiunge pulsante Carica
        self.lyt_db_btns.addWidget(self.btn_del_db)                                             # Aggiunge pulsante Elimina
        self.lyt_db.addLayout(self.lyt_db_btns)                                                 # Aggiunge la riga pulsanti

        self.lyt_name = QtWidgets.QFormLayout()                                                 # Form layout per il nome grezzo
        self.name_input = QtWidgets.QLineEdit("Barra D50 x 100")                                # Nome descrittivo del grezzo
        self.lyt_name.addRow("Nome:", self.name_input)                                          # Riga Nome
        self.lyt_db.addLayout(self.lyt_name)                                                    # Aggiunge al gruppo archivio

        self.chk_save_db = QtWidgets.QCheckBox("Salva in Archivio Permanente all'OK")           # Salvataggio automatico su disco
        self.chk_save_db.setChecked(True)                                                       # Attivo di default
        self.lyt_db.addWidget(self.chk_save_db)                                                 # Aggiunge al gruppo archivio
        self.layout.addWidget(self.grp_db)                                                      # Aggiunge al layout principale

        self.tabs = QtWidgets.QTabWidget()                                                      # Schede: 1. Dimensioni Grezzo | 2. Mandrino & Contropunta

        self.tab_stock = QtWidgets.QWidget()                                                    # SCHEDA 1: Geometria Grezzo e Sovrametalli
        self.lyt_stock = QtWidgets.QVBoxLayout(self.tab_stock)                                  # Layout verticale Scheda 1

        self.grp_dim = QtWidgets.QGroupBox("Dimensioni Barra e Sovrametalli")                   # Gruppo misure del grezzo
        self.lyt_dim = QtWidgets.QFormLayout(self.grp_dim)                                      # Form layout misure

        self.btn_auto_part = QtWidgets.QPushButton("Rileva Misure dal Pezzo 3D Selezionato")    # Calcola diametro e lunghezza dal modello 3D
        self.btn_auto_part.clicked.connect(self.calcola_da_pezzo_selezionato)                   # Collega il calcolo automatico

        self.shape_type_combo = QtWidgets.QComboBox()                                           # Scelta Cilindro / Tubo / Quadro / Esagono
        self.shape_type_combo.addItems(TIPI_GREZZO)                                             # Popola i 4 tipi di barra
        self.shape_type_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.shape_type_combo.setMinimumContentsLength(10)

        self.lbl_d_ext = QtWidgets.QLabel("Diametro Base (mm):")                                # Etichetta dinamica (Diametro Base o Lato/Chiave S)
        self.d_ext_spin = QtWidgets.QDoubleSpinBox(); self.d_ext_spin.setRange(2.0, 2000.0); self.d_ext_spin.setValue(50.0) # Diametro o Chiave S base
        self.d_int_spin = QtWidgets.QDoubleSpinBox(); self.d_int_spin.setRange(0.0, 1990.0); self.d_int_spin.setValue(0.0)  # Diametro foro interno
        self.lung_spin = QtWidgets.QDoubleSpinBox(); self.lung_spin.setRange(2.0, 5000.0); self.lung_spin.setValue(100.0)   # Lunghezza totale
        self.sovra_z_spin = QtWidgets.QDoubleSpinBox(); self.sovra_z_spin.setRange(0.0, 200.0); self.sovra_z_spin.setValue(1.5); self.sovra_z_spin.setSingleStep(0.5) # Sovrametallo Z+
        self.sovra_x_spin = QtWidgets.QDoubleSpinBox(); self.sovra_x_spin.setRange(0.0, 200.0); self.sovra_x_spin.setValue(0.0); self.sovra_x_spin.setSingleStep(0.5) # Sovrametallo X+
        self.trasp_spin = QtWidgets.QSpinBox(); self.trasp_spin.setRange(0, 90); self.trasp_spin.setValue(55); self.trasp_spin.setSingleStep(5) # Trasparenza %

        self.lbl_stock_status = QtWidgets.QLabel("Stato: Grezzo ancorato al WCS.")              # Etichetta di stato e inviluppo spigoli
        self.lbl_stock_status.setWordWrap(True)                                                 # Va a capo automaticamente
        self.lbl_stock_status.setStyleSheet("color: #FFAA00; font-weight: bold;")               # Colore arancione evidenziato

        self.lyt_dim.addRow(self.btn_auto_part)                                                 # Riga pulsante rilevamento automatico
        self.lyt_dim.addRow("Tipo Barra:", self.shape_type_combo)                               # Riga Cilindro / Tubo / Quadro / Esagono
        self.lyt_dim.addRow(self.lbl_d_ext, self.d_ext_spin)                                    # Riga Diametro Base / Chiave S
        self.lyt_dim.addRow("Diametro Foro Int. (mm):", self.d_int_spin)                        # Riga Diametro Foro Interno
        self.lyt_dim.addRow("Lunghezza Totale (mm):", self.lung_spin)                           # Riga Lunghezza Totale
        self.lyt_dim.addRow("Sovrametallo Fronte Z+ (mm):", self.sovra_z_spin)                  # Riga Sovrametallo Frontale Z+
        self.lyt_dim.addRow("Sovrametallo Raggio X+ (mm):", self.sovra_x_spin)                  # Riga Sovrametallo Radiale X+ (allarga live il grezzo!)
        self.lyt_dim.addRow("Trasparenza Visiva (%):", self.trasp_spin)                         # Riga Trasparenza
        self.lyt_dim.addRow(self.lbl_stock_status)                                              # Riga stato
        self.lyt_stock.addWidget(self.grp_dim)                                                  # Aggiunge alla Scheda 1

        self.tabs.addTab(self.tab_stock, "1. Grezzo")                                           # Titolo Scheda 1 compatto

        self.tab_chuck = QtWidgets.QWidget()                                                    # SCHEDA 2: Autocentrante, Griffe e Contropunta
        self.lyt_chuck = QtWidgets.QVBoxLayout(self.tab_chuck)                                  # Layout verticale Scheda 2

        self.grp_chuck = QtWidgets.QGroupBox("Autocentrante e Griffe (Limite Z-)")              # Gruppo mandrino e griffe
        self.lyt_c_form = QtWidgets.QFormLayout(self.grp_chuck)                                 # Form layout mandrino

        self.chk_show_chuck = QtWidgets.QCheckBox("Mostra Autocentrante e Griffe nel 3D")       # Attiva/disattiva la vista del mandrino
        self.chk_show_chuck.setChecked(True)                                                    # Attivo di default

        self.d_chuck_spin = QtWidgets.QDoubleSpinBox(); self.d_chuck_spin.setRange(50.0, 2000.0); self.d_chuck_spin.setValue(160.0) # Ø Mandrino
        self.sp_chuck_spin = QtWidgets.QDoubleSpinBox(); self.sp_chuck_spin.setRange(20.0, 500.0); self.sp_chuck_spin.setValue(55.0) # Spessore
        self.grip_z_spin = QtWidgets.QDoubleSpinBox(); self.grip_z_spin.setRange(1.0, 500.0); self.grip_z_spin.setValue(20.0)       # Presa griffe Z
        self.h_jaw_spin = QtWidgets.QDoubleSpinBox(); self.h_jaw_spin.setRange(10.0, 300.0); self.h_jaw_spin.setValue(30.0)         # Altezza griffe
        self.safe_jaw_spin = QtWidgets.QDoubleSpinBox(); self.safe_jaw_spin.setRange(0.0, 100.0); self.safe_jaw_spin.setValue(3.0)  # Margine sicurezza

        self.lbl_z_lim = QtWidgets.QLabel("Z Limite Collisione Griffe: -75.50 mm")              # Mostra la quota Z limite calcolata in tempo reale
        self.lbl_z_lim.setWordWrap(True)                                                        # Va a capo
        self.lbl_z_lim.setStyleSheet("color: #FF5555; font-weight: bold;")                      # Rosso per evidenziare il limite di collisione

        self.lyt_c_form.addRow(self.chk_show_chuck)                                             # Riga checkbox mostra mandrino
        self.lyt_c_form.addRow("Diametro Mandrino (mm):", self.d_chuck_spin)                    # Riga diametro mandrino
        self.lyt_c_form.addRow("Spessore Mandrino (mm):", self.sp_chuck_spin)                   # Riga spessore mandrino
        self.lyt_c_form.addRow("Presa Pezzo in Griffe (mm):", self.grip_z_spin)                 # Riga lunghezza presa griffe
        self.lyt_c_form.addRow("Altezza Griffe (mm):", self.h_jaw_spin)                         # Riga altezza griffe
        self.lyt_c_form.addRow("Margine Sicurezza (mm):", self.safe_jaw_spin)                   # Riga margine sicurezza
        self.lyt_c_form.addRow(self.lbl_z_lim)                                                  # Riga quota Z limite calcolata
        self.lyt_chuck.addWidget(self.grp_chuck)                                                # Aggiunge alla Scheda 2

        self.grp_tail = QtWidgets.QGroupBox("Contropunta (Supporto Destro Z+)")                 # Gruppo contropunta opzionale
        self.lyt_tail = QtWidgets.QFormLayout(self.grp_tail)                                    # Form layout contropunta

        self.chk_tail = QtWidgets.QCheckBox("Usa Contropunta sul centro frontale (Z+)")         # Attiva/disattiva la contropunta
        self.chk_tail.setChecked(False)                                                         # Disattivata di default
        self.d_tail_spin = QtWidgets.QDoubleSpinBox(); self.d_tail_spin.setRange(10.0, 300.0); self.d_tail_spin.setValue(30.0) # Ø Contropunta
        self.l_tail_spin = QtWidgets.QDoubleSpinBox(); self.l_tail_spin.setRange(10.0, 300.0); self.l_tail_spin.setValue(25.0) # Lunghezza cono

        self.lyt_tail.addRow(self.chk_tail)                                                     # Riga checkbox contropunta
        self.lyt_tail.addRow("Diametro Contropunta (mm):", self.d_tail_spin)                    # Riga diametro contropunta
        self.lyt_tail.addRow("Lunghezza Punta Conica (mm):", self.l_tail_spin)                  # Riga lunghezza cono
        self.lyt_chuck.addWidget(self.grp_tail)                                                 # Aggiunge alla Scheda 2

        self.tabs.addTab(self.tab_chuck, "2. Presa & Limiti")                                   # Titolo Scheda 2 compatto
        self.layout.addWidget(self.tabs)                                                        # Aggiunge il TabWidget al layout principale
        self.form.setLayout(self.layout)                                                        # Applica il layout finale

        self.preview_stock = doc.addObject("Part::Feature", "TMP_Stock_Preview")                # Crea l'oggetto temporaneo di anteprima
        self.preview_stock.Label = "ANTEPRIMA GREZZO (Provvisorio)"                             # Etichetta provvisoria

        self.aggiorna_combo_db()                                                                # Popola la tendina dell'archivio grezzi

        if self.edit_obj:                                                                       # Se stiamo modificando un Grezzo esistente
            self.carica_dati_da_oggetto(self.edit_obj)                                          # Ripristina tutte le quote salvate

        self.shape_type_combo.currentIndexChanged.connect(self.aggiorna_ui_forma)               # Collega cambio tipo barra
        self.d_ext_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio diametro/chiave base
        self.d_int_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio diametro interno
        self.lung_spin.valueChanged.connect(self.trigger_update)                                # Collega cambio lunghezza totale
        self.sovra_z_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio sovrametallo Z+
        self.sovra_x_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio sovrametallo X+ (aggiorna il 3D live)
        self.trasp_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio trasparenza
        self.chk_show_chuck.stateChanged.connect(self.trigger_update)                           # Collega spunta mostra mandrino
        self.d_chuck_spin.valueChanged.connect(self.trigger_update)                             # Collega cambio diametro mandrino
        self.sp_chuck_spin.valueChanged.connect(self.trigger_update)                            # Collega cambio spessore mandrino
        self.grip_z_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio presa griffe
        self.h_jaw_spin.valueChanged.connect(self.trigger_update)                               # Collega cambio altezza griffe
        self.safe_jaw_spin.valueChanged.connect(self.trigger_update)                            # Collega cambio margine sicurezza
        self.chk_tail.stateChanged.connect(self.trigger_update)                                 # Collega spunta contropunta
        self.d_tail_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio diametro contropunta
        self.l_tail_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio lunghezza cono

        self.is_updating = False                                                                # Sblocca gli aggiornamenti live
        self.aggiorna_ui_forma()                                                                # Adatta i controlli e disegna l'anteprima 3D

    def aggiorna_ui_forma(self):                                                                # Adatta le etichette e il foro interno in base al tipo barra
        forma_txt = self.shape_type_combo.currentText()                                         # Legge la forma selezionata
        if forma_txt == "Barra Quadra":                                                         # Se è una Barra Quadra
            self.lbl_d_ext.setText("Lato Quadro S (mm):")                                       # Cambia etichetta in Lato Quadro S
            self.d_int_spin.setEnabled(True)                                                    # Permette eventuale pre-foro centrale
        elif forma_txt == "Barra Esagonale":                                                    # Se è una Barra Esagonale
            self.lbl_d_ext.setText("Chiave Esagono S (mm):")                                    # Cambia etichetta in Chiave Esagono S
            self.d_int_spin.setEnabled(True)                                                    # Permette eventuale pre-foro centrale
        elif forma_txt == "Tubo Forato":                                                        # Se è un Tubo Forato
            self.lbl_d_ext.setText("Diametro Base (mm):")                                       # Etichetta Diametro Base
            self.d_int_spin.setEnabled(True)                                                    # Abilita il diametro foro interno
            if self.d_int_spin.value() <= 0.0:                                                  # Se il foro era a zero
                self.is_updating = True                                                         # Evita doppio ricalcolo
                self.d_int_spin.setValue(max(self.d_ext_spin.value() * 0.5, 1.0))               # Propone un diametro foro pari a metà del diametro esterno
                self.is_updating = False                                                        # Sblocca
        else:                                                                                   # Se è un Cilindro Pieno
            self.lbl_d_ext.setText("Diametro Base (mm):")                                       # Etichetta Diametro Base
            self.d_int_spin.setEnabled(False)                                                   # Disabilita il foro interno
        self.trigger_update()                                                                   # Ricalcola l'anteprima 3D

    def calcola_da_pezzo_selezionato(self):                                                     # Legge il BoundBox del pezzo 3D e imposta diametro netto + lunghezza
        sel = FreeCADGui.Selection.getSelection()                                               # Ottiene gli oggetti selezionati
        if not sel or not hasattr(sel[0], "Shape") or not sel[0].Shape:                         # Verifica che ci sia un solido selezionato
            self.lbl_stock_status.setText("Errore: Seleziona prima il solido del Pezzo nel 3D!")# Avvisa l'utente
            return                                                                              # Esce
        bb = sel[0].Shape.BoundBox                                                              # Legge il BoundBox 3D del pezzo finito
        r_max_pezzo = max(abs(bb.XMax), abs(bb.XMin), abs(bb.YMax), abs(bb.YMin))               # Calcola il raggio massimo netto del pezzo attorno a Z
        diam_netto_pezzo = r_max_pezzo * 2.0                                                    # Diametro netto del pezzo (il sovrametallo X+ viene sommato live!)
        lung_pezzo = bb.ZLength                                                                 # Lunghezza assiale del pezzo finito
        lung_calcolata = lung_pezzo + self.sovra_z_spin.value() + self.grip_z_spin.value() + self.safe_jaw_spin.value() # Somma pezzo + sovra Z + presa griffe

        self.is_updating = True                                                                 # Sospende aggiornamenti multipli
        self.d_ext_spin.setValue(math.ceil(diam_netto_pezzo))                                   # Imposta il diametro base del pezzo selezionato
        if self.sovra_x_spin.value() <= 0.0:                                                    # Se il sovrametallo X+ era a zero
            self.sovra_x_spin.setValue(2.0)                                                     # Propone 2.0 mm di sovrametallo sul raggio
        self.lung_spin.setValue(math.ceil(lung_calcolata))                                      # Arrotonda al millimetro superiore la lunghezza barra
        d_tot = int(self.d_ext_spin.value() + 2.0 * self.sovra_x_spin.value())                  # Calcola il diametro esterno effettivo con sovrametallo
        self.name_input.setText(f"{self.shape_type_combo.currentText()} {d_tot} x {int(self.lung_spin.value())}") # Nome descrittivo
        self.is_updating = False                                                                # Sblocca
        FreeCADGui.Selection.clearSelection()                                                   # Pulisce la selezione
        self.trigger_update()                                                                   # Aggiorna il 3D

    def trigger_update(self, *args):                                                            # Aggiorna in tempo reale l'anteprima 3D del Grezzo e Mandrino
        if self.is_updating:                                                                    # Se bloccato
            return                                                                              # Esce
        self.is_updating = True                                                                 # Attiva il semaforo
        try:                                                                                    # Blocco di disegno
            doc = FreeCAD.ActiveDocument                                                        # Documento attivo
            if not doc or not self.preview_stock:                                               # Verifica validità
                return                                                                          # Esce
            wcs = get_wcs_origin(doc)                                                           # Origine WCS
            forma_scelta = self.shape_type_combo.currentText()                                  # Tipo barra scelto
            d_int = self.d_int_spin.value() if forma_scelta != "Cilindro Pieno" else 0.0        # Diametro foro interno
            trasp = self.trasp_spin.value()                                                     # Percentuale trasparenza (0..90%)
            comp, cols_3, alphas, z_lim, d_rot = costruisci_geometria_grezzo_e_presa(           # Genera la geometria 3D includendo sovra_x_spin
                wcs, forma_scelta, self.d_ext_spin.value(), d_int,                              # Tipo barra, diametro/chiave base e foro
                self.lung_spin.value(), self.sovra_z_spin.value(), self.sovra_x_spin.value(), trasp, # Lunghezza, sovrametalli Z+/X+ e trasparenza
                self.chk_show_chuck.isChecked(), self.d_chuck_spin.value(), self.sp_chuck_spin.value(),
                self.grip_z_spin.value(), self.h_jaw_spin.value(), self.safe_jaw_spin.value(),
                self.chk_tail.isChecked(), self.d_tail_spin.value(), self.l_tail_spin.value()
            )                                                                                   # Fine generazione
            self.lbl_z_lim.setText(f"Z Limite Collisione Griffe: {z_lim:.2f} mm")               # Aggiorna l'etichetta della quota Z limite
            d_eff = self.d_ext_spin.value() + (2.0 * self.sovra_x_spin.value())                 # Calcola la misura effettiva (Base + 2*SovraX)
            if forma_scelta in ["Barra Quadra", "Barra Esagonale"]:                             # Se è poligonale, mostra chiave effettiva e Ø spigoli
                self.lbl_stock_status.setText(f"Chiave Effettiva: {d_eff:.1f} mm | Ø Spigoli: {d_rot:.2f} mm") # Mostra entrambi i valori in tempo reale
            else:                                                                               # Se è circolare
                self.lbl_stock_status.setText(f"Ø Esterno Effettivo (con Sovra X+): {d_eff:.2f} mm") # Mostra il diametro esterno effettivo
            self.preview_stock.Shape = comp                                                     # Assegna la Shape all'anteprima
            if hasattr(self.preview_stock, "ViewObject") and self.preview_stock.ViewObject:     # Applica trasparenza e colori all'anteprima
                applica_colori_e_trasparenza(self.preview_stock.ViewObject, self.preview_stock.Shape, cols_3, alphas, trasp)
            doc.recompute()                                                                     # Rinfresca la vista 3D
        finally:                                                                                # Rilascia il semaforo
            self.is_updating = False                                                            # Fine aggiornamento

    def aggiorna_combo_db(self):                                                                # Popola la tendina con le configurazioni salvate su disco
        db = load_stocks_db()                                                                   # Legge il file JSON
        self.db_combo.clear()                                                                   # Svuota il combo
        nomi = sorted(db.keys())                                                                # Ordina alfabeticamente
        if nomi:                                                                                # Se ci sono voci salvate
            self.db_combo.addItems(nomi)                                                        # Le aggiunge
        else:                                                                                   # Se vuoto
            self.db_combo.addItem("(Archivio vuoto)")                                           # Mostra testo informativo

    def salva_grezzo_in_db(self, stock_obj):                                                    # Salva la configurazione del grezzo/mandrino su disco
        db = load_stocks_db()                                                                   # Carica il database
        key = stock_obj.StockName.strip() or "Barra D50 x 100"                                  # Chiave univoca
        db[key] = {                                                                             # Dizionario parametri
            "StockName": key,                                                                   # Nome
            "FormaGrezzo": str(stock_obj.FormaGrezzo),                                          # Cilindro / Tubo / Quadro / Esagono
            "DiametroEsterno": float(stock_obj.DiametroEsterno),                                # Diametro esterno o Chiave S
            "DiametroForoInterno": float(stock_obj.DiametroForoInterno),                        # Diametro interno
            "LunghezzaTotale": float(stock_obj.LunghezzaTotale),                                # Lunghezza totale
            "SovrametalloFrontaleZ": float(stock_obj.SovrametalloFrontaleZ),                    # Sovrametallo Z+
            "SovrametalloRadialeX": float(stock_obj.SovrametalloRadialeX),                      # Sovrametallo X+
            "TrasparenzaGrezzo": int(stock_obj.TrasparenzaGrezzo),                              # Trasparenza
            "MostraMandrino": bool(stock_obj.MostraMandrino),                                   # Mostra mandrino
            "DiametroMandrino": float(stock_obj.DiametroMandrino),                              # Ø Mandrino
            "SpessoreMandrino": float(stock_obj.SpessoreMandrino),                              # Spessore mandrino
            "LunghezzaPresaGriffe": float(stock_obj.LunghezzaPresaGriffe),                      # Presa griffe
            "AltezzaGriffe": float(stock_obj.AltezzaGriffe),                                    # Altezza griffe
            "MargineSicurezzaGriffe": float(stock_obj.MargineSicurezzaGriffe),                  # Margine sicurezza
            "UsaContropunta": bool(stock_obj.UsaContropunta),                                   # Contropunta
            "DiametroContropunta": float(stock_obj.DiametroContropunta),                        # Ø Contropunta
            "LunghezzaConoContropunta": float(stock_obj.LunghezzaConoContropunta)               # Lunghezza cono
        }                                                                                       # Fine record
        save_stocks_db(db)                                                                      # Salva su disco

    def carica_grezzo_da_db(self):                                                              # Carica nel pannello una configurazione salvata
        db = load_stocks_db()                                                                   # Legge il database
        key = self.db_combo.currentText()                                                       # Chiave selezionata
        if key not in db:                                                                       # Se non esiste
            return                                                                              # Esce
        data = db[key]                                                                          # Estrae i dati
        self.is_updating = True                                                                 # Sospende i segnali UI
        try:                                                                                    # Popola tutti i controlli
            self.name_input.setText(data.get("StockName", key))                                 # Nome
            forma_db = data.get("FormaGrezzo", "Cilindro Pieno")                                # Legge la forma dal DB
            if forma_db in TIPI_GREZZO:                                                         # Se valida
                self.shape_type_combo.setCurrentText(forma_db)                                  # Seleziona la forma nel combo
            self.d_ext_spin.setValue(float(data.get("DiametroEsterno", 50.0)))                  # Diametro esterno o Chiave S
            self.d_int_spin.setValue(float(data.get("DiametroForoInterno", 0.0)))               # Diametro interno
            self.lung_spin.setValue(float(data.get("LunghezzaTotale", 100.0)))                  # Lunghezza totale
            self.sovra_z_spin.setValue(float(data.get("SovrametalloFrontaleZ", 1.5)))           # Sovrametallo Z+
            self.sovra_x_spin.setValue(float(data.get("SovrametalloRadialeX", 0.0)))            # Sovrametallo X+
            self.trasp_spin.setValue(int(data.get("TrasparenzaGrezzo", 55)))                    # Trasparenza
            self.chk_show_chuck.setChecked(bool(data.get("MostraMandrino", True)))              # Mostra mandrino
            self.d_chuck_spin.setValue(float(data.get("DiametroMandrino", 160.0)))              # Ø Mandrino
            self.sp_chuck_spin.setValue(float(data.get("SpessoreMandrino", 55.0)))              # Spessore mandrino
            self.grip_z_spin.setValue(float(data.get("LunghezzaPresaGriffe", 20.0)))            # Presa griffe
            self.h_jaw_spin.setValue(float(data.get("AltezzaGriffe", 30.0)))                    # Altezza griffe
            self.safe_jaw_spin.setValue(float(data.get("MargineSicurezzaGriffe", 3.0)))         # Margine sicurezza
            self.chk_tail.setChecked(bool(data.get("UsaContropunta", False)))                   # Contropunta
            self.d_tail_spin.setValue(float(data.get("DiametroContropunta", 30.0)))             # Ø Contropunta
            self.l_tail_spin.setValue(float(data.get("LunghezzaConoContropunta", 25.0)))        # Lunghezza cono
        finally:                                                                                # Sblocca i segnali UI
            self.is_updating = False                                                            # Riabilita
        self.aggiorna_ui_forma()                                                                # Aggiorna etichette e vista 3D

    def elimina_grezzo_da_db(self):                                                             # Rimuove la configurazione selezionata dall'archivio
        db = load_stocks_db()                                                                   # Legge il database
        key = self.db_combo.currentText()                                                       # Voce selezionata
        if key in db:                                                                           # Se presente
            del db[key]                                                                         # Elimina dal dizionario
            save_stocks_db(db)                                                                  # Aggiorna il JSON su disco
            self.aggiorna_combo_db()                                                            # Aggiorna la tendina

    def carica_dati_da_oggetto(self, obj):                                                      # Popola la UI quando si riapre Grezzo_Macchina con doppio click
        obj.Proxy.ensure_properties(obj)                                                        # Verifica tutte le proprietà
        self.name_input.setText(str(getattr(obj, "StockName", "Barra D50 x 100")))              # Nome
        forma_obj = str(getattr(obj, "FormaGrezzo", "Cilindro Pieno"))                          # Legge la forma dall'oggetto
        if forma_obj in TIPI_GREZZO:                                                            # Se presente nella lista
            self.shape_type_combo.setCurrentText(forma_obj)                                     # Imposta il combo
        self.d_ext_spin.setValue(float(getattr(obj, "DiametroEsterno", 50.0)))                  # Diametro esterno o Chiave S
        self.d_int_spin.setValue(float(getattr(obj, "DiametroForoInterno", 0.0)))               # Diametro interno
        self.lung_spin.setValue(float(getattr(obj, "LunghezzaTotale", 100.0)))                  # Lunghezza totale
        self.sovra_z_spin.setValue(float(getattr(obj, "SovrametalloFrontaleZ", 1.5)))           # Sovrametallo Z+
        self.sovra_x_spin.setValue(float(getattr(obj, "SovrametalloRadialeX", 0.0)))            # Sovrametallo X+
        self.trasp_spin.setValue(int(getattr(obj, "TrasparenzaGrezzo", 55)))                    # Trasparenza
        self.chk_show_chuck.setChecked(bool(getattr(obj, "MostraMandrino", True)))              # Mostra mandrino
        self.d_chuck_spin.setValue(float(getattr(obj, "DiametroMandrino", 160.0)))              # Ø Mandrino
        self.sp_chuck_spin.setValue(float(getattr(obj, "SpessoreMandrino", 55.0)))              # Spessore mandrino
        self.grip_z_spin.setValue(float(getattr(obj, "LunghezzaPresaGriffe", 20.0)))            # Presa griffe
        self.h_jaw_spin.setValue(float(getattr(obj, "AltezzaGriffe", 30.0)))                    # Altezza griffe
        self.safe_jaw_spin.setValue(float(getattr(obj, "MargineSicurezzaGriffe", 3.0)))         # Margine sicurezza
        self.chk_tail.setChecked(bool(getattr(obj, "UsaContropunta", False)))                   # Contropunta
        self.d_tail_spin.setValue(float(getattr(obj, "DiametroContropunta", 30.0)))             # Ø Contropunta
        self.l_tail_spin.setValue(float(getattr(obj, "LunghezzaConoContropunta", 25.0)))        # Lunghezza cono

    def pulisci_anteprima_grezzo(self, doc):                                                    # Rimuove in modo sicuro l'oggetto di anteprima temporanea
        if not doc:                                                                             # Controlla esistenza documento
            return                                                                              # Esce
        if hasattr(self, "preview_stock") and self.preview_stock:                               # Se esiste il riferimento preview_stock
            try:                                                                                # Tenta la rimozione
                if doc.getObject(self.preview_stock.Name):                                      # Se è presente nel documento
                    doc.removeObject(self.preview_stock.Name)                                   # Lo elimina
            except Exception:                                                                   # Ignora errori
                pass                                                                            # Continua
            self.preview_stock = None                                                           # Azzera il riferimento
        for obj in list(doc.Objects):                                                           # Pulisce eventuali residui precedenti
            if obj.Name.startswith("TMP_Stock_Preview") or "ANTEPRIMA GREZZO" in getattr(obj, "Label", "").upper():
                try: doc.removeObject(obj.Name)                                                 # Rimuove l'oggetto temporaneo
                except Exception: pass                                                          # Ignora errori

    def getStandardButtons(self):                                                               # Pulsanti standard OK e Cancel del pannello Task
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel                # Restituisce OK | Cancel

    def accept(self):                                                                           # Conferma e salva l'oggetto Grezzo_Macchina
        doc = FreeCAD.ActiveDocument                                                            # Ottiene il documento attivo
        if not doc:                                                                             # Controllo sicurezza
            return False                                                                        # Esce

        nome_grezzo = self.name_input.text().strip() or "Barra D50 x 100"                       # Legge il nome grezzo
        if self.edit_obj and doc.getObject(self.edit_obj.Name):                                 # Se stavamo modificando un Grezzo esistente
            stock_obj = self.edit_obj                                                           # Usa l'oggetto esistente
        elif doc.getObject("Grezzo_Macchina"):                                                  # Se esiste già Grezzo_Macchina nel documento
            stock_obj = doc.getObject("Grezzo_Macchina")                                        # Lo riutilizza senza creare duplicati
        else:                                                                                   # Altrimenti crea il nuovo oggetto parametrico
            stock_obj = doc.addObject("Part::FeaturePython", "Grezzo_Macchina")                 # Crea Part::FeaturePython col nome richiesto da LatheCommands
            LatheStockObject(stock_obj)                                                         # Inizializza il Proxy
            ViewProviderLatheStock(stock_obj.ViewObject)                                        # Inizializza il ViewProvider con doppio click

        stock_obj.Proxy._is_executing = True                                                    # Sospende il ricalcolo finché tutte le proprietà non sono scritte
        try:                                                                                    # Assegna tutte le proprietà all'oggetto
            stock_obj.Proxy.ensure_properties(stock_obj)                                        # Garantisce la presenza delle proprietà
            stock_obj.StockName = nome_grezzo                                                   # Salva il nome
            stock_obj.Label = f"Grezzo ({nome_grezzo})"                                         # Etichetta nell'albero
            stock_obj.FormaGrezzo = self.shape_type_combo.currentText()                         # Salva Cilindro / Tubo / Quadro / Esagono
            stock_obj.DiametroEsterno = self.d_ext_spin.value()                                 # Salva diametro esterno o Chiave S base
            stock_obj.DiametroForoInterno = self.d_int_spin.value()                             # Salva diametro interno
            stock_obj.LunghezzaTotale = self.lung_spin.value()                                  # Salva lunghezza totale
            stock_obj.SovrametalloFrontaleZ = self.sovra_z_spin.value()                         # Salva sovrametallo Z+
            stock_obj.SovrametalloRadialeX = self.sovra_x_spin.value()                          # Salva sovrametallo X+
            stock_obj.TrasparenzaGrezzo = self.trasp_spin.value()                               # Salva trasparenza
            stock_obj.MostraMandrino = self.chk_show_chuck.isChecked()                          # Salva mostra mandrino
            stock_obj.DiametroMandrino = self.d_chuck_spin.value()                              # Salva diametro mandrino
            stock_obj.SpessoreMandrino = self.sp_chuck_spin.value()                             # Salva spessore mandrino
            stock_obj.LunghezzaPresaGriffe = self.grip_z_spin.value()                           # Salva presa griffe
            stock_obj.AltezzaGriffe = self.h_jaw_spin.value()                                   # Salva altezza griffe
            stock_obj.MargineSicurezzaGriffe = self.safe_jaw_spin.value()                       # Salva margine sicurezza
            stock_obj.UsaContropunta = self.chk_tail.isChecked()                                # Salva contropunta
            stock_obj.DiametroContropunta = self.d_tail_spin.value()                            # Salva diametro contropunta
            stock_obj.LunghezzaConoContropunta = self.l_tail_spin.value()                       # Salva lunghezza cono
        finally:                                                                                # Riabilita il Proxy
            stock_obj.Proxy._is_executing = False                                               # Sblocca

        stock_obj.Proxy.execute(stock_obj)                                                      # Costruisce la forma finale e calcola Z_Limite_Mandrino
        if hasattr(stock_obj, "ViewObject") and stock_obj.ViewObject:                           # Ripristina la visibilità
            stock_obj.ViewObject.Visibility = True                                              # Rende visibile Grezzo_Macchina

        if self.chk_save_db.isChecked():                                                        # Se è attiva la spunta di salvataggio su disco
            self.salva_grezzo_in_db(stock_obj)                                                  # Salva in StockLibrary

        self.pulisci_anteprima_grezzo(doc)                                                      # Elimina l'anteprima provvisoria TMP_Stock_Preview
        doc.recompute()                                                                         # Ricalcola il documento
        if FreeCADGui.ActiveDocument:                                                           # Se la GUI è attiva
            FreeCADGui.ActiveDocument.resetEdit()                                               # Esce dalla modalità Edit
        FreeCADGui.Control.closeDialog()                                                        # Chiude il pannello Task
        return True                                                                             # Conferma

    def reject(self):                                                                           # Annulla le modifiche e ripristina lo stato precedente
        doc = FreeCAD.ActiveDocument                                                            # Ottiene il documento attivo
        if doc:                                                                                 # Se il documento esiste
            self.pulisci_anteprima_grezzo(doc)                                                  # Elimina subito l'anteprima provvisoria
            if self.edit_obj and doc.getObject(self.edit_obj.Name):                             # Se stavamo modificando un Grezzo esistente
                if hasattr(self.edit_obj, "ViewObject") and self.edit_obj.ViewObject:           # Riaccende il Grezzo originale
                    self.edit_obj.ViewObject.Visibility = True                                  # Visibile
            doc.recompute()                                                                     # Aggiorna il documento
        if FreeCADGui.ActiveDocument:                                                           # Se la GUI è attiva
            FreeCADGui.ActiveDocument.resetEdit()                                               # Esce dalla modalità Edit
        FreeCADGui.Control.closeDialog()                                                        # Chiude il pannello
        return True                                                                             # Conferma