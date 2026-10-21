import FreeCAD                                                                                  # Importa il modulo base di FreeCAD
import FreeCADGui                                                                               # Importa il modulo interfaccia grafica di FreeCAD
import Part                                                                                     # Importa il modulo geometrico Part
import math                                                                                     # Importa le funzioni matematiche
import os                                                                                       # Importa il modulo per la gestione dei percorsi su disco
import json                                                                                     # Importa il modulo per leggere e scrivere il database JSON
import ImportGui                                                                                # Importa il gestore di file STEP/IGES
from PySide import QtCore, QtGui                                                                # Importa i moduli base PySide
try:                                                                                            # Tenta di importare QtWidgets per compatibilità Qt5/Qt6
    from PySide import QtWidgets                                                                # Assegna QtWidgets se disponibile
except ImportError:                                                                             # Gestisce il fallback per versioni precedenti
    QtWidgets = QtGui                                                                           # Usa QtGui come alias di QtWidgets


CATEGORIE_UTENSILI = [                                                                          # Elenco completo categorie utensili supportate
    "Esterno (ISO)",                                                                            # Tornitura esterna con inserto ISO
    "Bareno (Interno)",                                                                         # Tornitura interna / Barenatura
    "Gola / Troncatura",                                                                        # Utensile a lama per gole e troncatura
    "Filettatura",                                                                              # Utensile per filettatura esterna/interna
    "Punta da Trapano",                                                                         # Punta elicoidale per foratura assiale
    "Fresa",                                                                                    # Fresa a candela per motorizzati
    "Maschio"                                                                                   # Maschio per filettatura assiale
]                                                                                               # Fine elenco categorie

FORME_INSERTO_ISO = [                                                                           # Forme standard inserti ISO commerciali
    "Rombico 80° (C)",                                                                          # CNMG / CCMT (80 gradi)
    "Rombico 55° (D)",                                                                          # DNMG / DCMT (55 gradi)
    "Rombico 35° (V)",                                                                          # VNMG / VCMT (35 gradi finitura/copiatura)
    "Triangolare 60° (T)",                                                                      # TNMG / TCMT (60 gradi)
    "Quadrato 90° (S)"                                                                          # SNMG / SCMT (90 gradi)
]                                                                                               # Fine elenco forme inserto

QUADRANTI_ISO = [                                                                               # Quadranti standard ISO 1..9 per orientamento punta
    "Q1 - Esterno Sinistro",                                                                    # Quadrante 1
    "Q2 - Bareno Interno Destro",                                                               # Quadrante 2
    "Q3 - Esterno Destro Standard",                                                             # Quadrante 3 (più comune su tornio posteriore)
    "Q4 - Esterno Frontale",                                                                    # Quadrante 4
    "Q5 - Gola / Profilatura Raggio",                                                           # Quadrante 5
    "Q6 - Troncatura / Gola Fronte",                                                            # Quadrante 6
    "Q7 - Punta / Centro Assiale",                                                              # Quadrante 7
    "Q8 - Filettatura / Neutro X-",                                                             # Quadrante 8
    "Q9 - Centro Raggio Utensile"                                                               # Quadrante 9
]                                                                                               # Fine quadranti ISO


def get_library_dir():                                                                          # Restituisce il percorso della cartella archivio utensili
    base_dir = os.path.dirname(os.path.abspath(__file__))                                       # Ottiene la cartella del workbench corrente
    lib_dir = os.path.join(base_dir, "ToolLibrary")                                             # Definisce la sottocartella ToolLibrary
    os.makedirs(lib_dir, exist_ok=True)                                                         # Crea la cartella su disco se non esiste ancora
    return lib_dir                                                                              # Restituisce il percorso completo della cartella


def get_db_file():                                                                              # Restituisce il percorso del file JSON del database utensili
    return os.path.join(get_library_dir(), "tools_db.json")                                     # Combina la cartella archivio con il nome del file JSON


def load_tools_db():                                                                            # Carica il dizionario degli utensili salvati su disco
    db_path = get_db_file()                                                                     # Ottiene il percorso del file database
    if os.path.exists(db_path):                                                                 # Verifica se il file JSON esiste già
        try:                                                                                    # Tenta la lettura del file JSON
            with open(db_path, "r", encoding="utf-8") as f:                                     # Apre il file in lettura con codifica UTF-8
                return json.load(f)                                                             # Restituisce il dizionario caricato
        except Exception as e:                                                                  # Cattura eventuali errori di formato JSON
            FreeCAD.Console.PrintError(f"Errore lettura database utensili: {e}\n")              # Stampa l'errore nella console di FreeCAD
    return {}                                                                                   # Restituisce un dizionario vuoto se il file non esiste


def save_tools_db(db_data):                                                                     # Salva il dizionario degli utensili su disco
    db_path = get_db_file()                                                                     # Ottiene il percorso del file database
    try:                                                                                        # Tenta la scrittura del file JSON
        with open(db_path, "w", encoding="utf-8") as f:                                         # Apre il file in scrittura con codifica UTF-8
            json.dump(db_data, f, indent=4, ensure_ascii=False)                                 # Scrive i dati formattati in modo leggibile
    except Exception as e:                                                                      # Cattura eventuali errori di scrittura su disco
        FreeCAD.Console.PrintError(f"Errore salvataggio database utensili: {e}\n")              # Stampa l'errore nella console di FreeCAD


def get_wcs_origin(doc=None):                                                                   # Funzione per leggere l'origine del WCS (Setup_Macchina)
    if doc is None:                                                                             # Verifica se il documento non è stato passato
        doc = FreeCAD.ActiveDocument                                                            # Prende il documento attivo corrente
    if doc and doc.getObject("Setup_Macchina"):                                                 # Controlla se esiste l'oggetto Setup_Macchina
        setup_obj = doc.getObject("Setup_Macchina")                                             # Ottiene il riferimento al Setup_Macchina
        if hasattr(setup_obj, "Origine"):                                                       # Verifica che abbia la proprietà Origine
            return FreeCAD.Vector(setup_obj.Origine)                                            # Restituisce una copia del vettore Origine WCS
    return FreeCAD.Vector(0.0, 0.0, 0.0)                                                        # Restituisce l'origine globale se il WCS non esiste


def get_max_turret_stations(doc=None):                                                          # Legge il numero di posizioni della torretta (default 8)
    if doc is None:                                                                             # Verifica se il documento non è stato passato
        doc = FreeCAD.ActiveDocument                                                            # Prende il documento attivo corrente
    if doc and doc.getObject("Torretta_Macchina"):                                              # Controlla se esiste già l'oggetto Torretta_Macchina
        turret = doc.getObject("Torretta_Macchina")                                             # Ottiene il riferimento alla torretta
        if hasattr(turret, "NumeroPosizioni") and turret.NumeroPosizioni > 0:                   # Se la torretta definisce il numero di posizioni
            return int(turret.NumeroPosizioni)                                                  # Restituisce il numero di stazioni della torretta
    return 8                                                                                    # Valore predefinito 8 posizioni


def _crea_poligono_inserto_xy(shape_txt, L_ins, rot_deg, orient):                               # Costruisce la faccia 2D dell'inserto ISO e calcola il suo baricentro
    if "35" in shape_txt:                                                                       # Inserto VNMG / VCMT 35°
        ang_punta = 35.0                                                                        # Angolo di punta 35 gradi
    elif "55" in shape_txt:                                                                     # Inserto DNMG / DCMT 55°
        ang_punta = 55.0                                                                        # Angolo di punta 55 gradi
    elif "Triangolare" in shape_txt:                                                            # Inserto TNMG / TCMT 60°
        ang_punta = 60.0                                                                        # Angolo di punta 60 gradi
    elif "Quadrato" in shape_txt:                                                               # Inserto SNMG / SCMT 90°
        ang_punta = 90.0                                                                        # Angolo di punta 90 gradi
    else:                                                                                       # Inserto CNMG / CCMT 80° (default)
        ang_punta = 80.0                                                                        # Angolo di punta 80 gradi

    a_rad = math.radians(ang_punta)                                                             # Converte l'angolo di punta in radianti
    p0 = FreeCAD.Vector(0.0, 0.0, 0.0)                                                          # Punta tagliente esattamente in (0,0,0)
    p1 = FreeCAD.Vector(L_ins, 0.0, 0.0)                                                        # Primo spigolo lungo il tagliente principale
    p_last = FreeCAD.Vector(L_ins * math.cos(a_rad), -L_ins * math.sin(a_rad), 0.0)             # Spigolo lungo il tagliente secondario

    if "Triangolare" in shape_txt:                                                              # Se è triangolare ha 3 vertici
        pts = [p0, p1, p_last, p0]                                                              # Chiude il triangolo equilatero
        centro = (p0 + p1 + p_last) * (1.0 / 3.0)                                               # Baricentro del triangolo per il foro vite
    else:                                                                                       # Se è rombico o quadrato ha 4 vertici
        p2 = p1 + p_last                                                                        # Vertice posteriore opposto alla punta
        pts = [p0, p1, p2, p_last, p0]                                                          # Chiude il rombo/quadrato
        centro = p2 * 0.5                                                                       # Centro geometrico del rombo per il foro vite

    wire = Part.makePolygon(pts)                                                                # Crea il contorno poligonale chiuso
    face = Part.Face(wire)                                                                      # Crea la faccia piana dell'inserto
    ang_rot = -(float(rot_deg) - 90.0) * orient                                                 # Calcola la rotazione dell'angolo di registrazione Kapr
    rot_z = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), ang_rot)                                  # Crea la rotazione attorno a Z
    face.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), ang_rot)                      # Ruota la faccia attorno alla punta (0,0,0)
    centro_ruotato = rot_z.multVec(centro)                                                      # Calcola la posizione ruotata del centro foro
    return face, centro_ruotato, ang_punta                                                      # Restituisce faccia, centro foro e angolo


def genera_forme_parametriche(                                                                  # Genera modelli 3D realistici di gambo e inserto
    tipo, shape_txt, hand_txt, rot, w, h, l,                                                    # Parametri base geometrici
    lama_w, gola_p, ang_fil,                                                                    # Parametri specifici gola/troncatura e filettatura
    mir_x, mir_y, rot_man, wcs_origin                                                           # Parametri orientamento 3D e origine WCS
):                                                                                              # Inizio generatore geometrico realistico
    insert_shape = None                                                                         # Inizializza il solido dell'inserto (giallo oro)
    gambo_finito = None                                                                         # Inizializza il solido del portautensile (acciaio brunito)
    orient = -1.0 if "Sinistro" in hand_txt else 1.0                                            # Verso di orientamento Destro (+1) o Sinistro (-1)

    if tipo == "Esterno (ISO)":                                                                 # 1. PORTAINSERTI ESTERNO ISO REALISTICO (es. PCLNR / PDJNR)
        W = max(float(w), 6.0)                                                                  # Larghezza stelo quadro
        H = max(float(h), 6.0)                                                                  # Altezza stelo quadro
        L = max(float(l), W * 2.5)                                                              # Lunghezza totale portautensile
        L_ins = max(min(W * 0.62, 14.0), 6.0)                                                   # Lunghezza tagliente inserto proporzionata allo stelo
        sp_ins = max(min(H * 0.24, 4.76), 2.5)                                                  # Spessore inserto ISO (es. 3.18 o 4.76 mm)

        face_ins, c_ins, _ = _crea_poligono_inserto_xy(shape_txt, L_ins, rot, orient)           # Crea il profilo 2D dell'inserto orientato
        solido_ins = face_ins.extrude(FreeCAD.Vector(0, 0, -sp_ins))                            # Estrude l'inserto per il suo spessore
        r_foro = L_ins * 0.20                                                                   # Raggio del foro centrale di fissaggio Torx
        foro_ins = Part.makeCylinder(r_foro, sp_ins + 1.0, FreeCAD.Vector(c_ins.x, c_ins.y, -sp_ins - 0.5), FreeCAD.Vector(0, 0, 1))
        svas_ins = Part.makeCone(r_foro * 1.45, r_foro, sp_ins * 0.45, FreeCAD.Vector(c_ins.x, c_ins.y, 0.0), FreeCAD.Vector(0, 0, -1))
        try:                                                                                    # Scava il foro centrale svasato nell'inserto
            insert_shape = solido_ins.cut(foro_ins.fuse(svas_ins))                              # Inserto forato realistico
        except Exception:                                                                       # Fallback
            insert_shape = solido_ins                                                           # Inserto pieno

        sotto_ins = face_ins.extrude(FreeCAD.Vector(0, 0, -H))                                  # Colonna di supporto sagomata sotto l'inserto
        dx_testa = max(c_ins.x + L_ins * 0.55, W * 0.65)                                        # Inizio del corpo stelo dietro la testa
        pts_gambo = [                                                                           # Profilo superiore sagomato del portainserti
            FreeCAD.Vector(0.0, 0.0, 0.0),                                                      # Punta anteriore (0,0)
            FreeCAD.Vector(dx_testa, 0.0, 0.0),                                                 # Fianco superiore verso lo stelo
            FreeCAD.Vector(L, 0.0, 0.0),                                                        # Fine posteriore superiore dello stelo
            FreeCAD.Vector(L, -W, 0.0),                                                         # Fine posteriore inferiore dello stelo
            FreeCAD.Vector(dx_testa * 1.35, -W, 0.0),                                           # Inizio dello smusso di spoglia inferiore della testa
            FreeCAD.Vector(dx_testa * 0.35, min(c_ins.y - L_ins * 0.45, -W * 0.42), 0.0),       # Collo scaricato sotto la sede inserto
            FreeCAD.Vector(0.0, 0.0, 0.0)                                                       # Chiusura sulla punta
        ]                                                                                       # Fine punti profilo gambo
        corpo_stelo = Part.Face(Part.makePolygon(pts_gambo)).extrude(FreeCAD.Vector(0, 0, -H))  # Estrude il corpo sagomato per l'altezza H
        gambo_grezzo = corpo_stelo.fuse(sotto_ins)                                              # Unisce lo stelo con il naso di supporto sotto l'inserto

        scala_tasca = 1.06                                                                      # Maggiorazione del 6% per scavare la sede dell'inserto
        mat_s = FreeCAD.Matrix()                                                                # Matrice di scala per la tasca
        mat_s.scale(scala_tasca, scala_tasca, 1.0)                                              # Scala sul piano XY lasciando la punta in (0,0,0)
        faccia_tasca = face_ins.transformGeometry(mat_s)                                        # Faccia allargata per lo scavo tasca
        volume_tasca = faccia_tasca.extrude(FreeCAD.Vector(0, 0, sp_ins + 2.0))                 # Volume di fresatura della sede inserto
        volume_tasca.translate(FreeCAD.Vector(0, 0, -sp_ins))                                   # Posiziona il fondo tasca a -sp_ins

        smusso_fronte = Part.makeBox(W * 2.0, W * 2.0, H, FreeCAD.Vector(-W * 2.0, -W, -H))     # Taglio di spoglia frontale per non tallonare sul pezzo
        smusso_fronte.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), -6.0)            # Spoglia frontale di 6 gradi
        try:                                                                                    # Esegue lo scavo della tasca e lo scarico frontale
            gambo_finito = gambo_grezzo.cut(volume_tasca).cut(smusso_fronte)                    # Gambo fresato con sede ribassata
            perno_vite = Part.makeCylinder(r_foro * 0.88, sp_ins * 0.85, FreeCAD.Vector(c_ins.x, c_ins.y, -sp_ins), FreeCAD.Vector(0, 0, 1))
            gambo_finito = gambo_finito.fuse(perno_vite)                                        # Aggiunge la testa della vite/perno scura dentro il foro dell'inserto!
        except Exception:                                                                       # Fallback
            gambo_finito = gambo_grezzo                                                         # Mantiene il gambo base

        insert_shape.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -90)              # Orienta l'inserto sul piano XZ di tornitura
        gambo_finito.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -90)              # Orienta il portautensile sul piano XZ di tornitura

    elif tipo == "Bareno (Interno)":                                                            # 2. BARENO INTERNO REALISTICO (Stelo tondo con spianature e collo scaricato)
        D = max(float(w), 6.0)                                                                  # Diametro del gambo cilindrico del bareno
        L = max(float(l), D * 3.0)                                                              # Lunghezza totale del bareno
        L_ins = max(min(D * 0.55, 11.0), 5.0)                                                   # Dimensione inserto proporzionata al foro minimo
        sp_ins = max(min(D * 0.18, 3.97), 2.0)                                                  # Spessore inserto interno (TCMT / CCMT / DCMT)

        face_ins, c_ins, _ = _crea_poligono_inserto_xy(shape_txt, L_ins, rot, orient)           # Profilo inserto del bareno
        solido_ins = face_ins.extrude(FreeCAD.Vector(0, 0, -sp_ins))                            # Estrusione spessore inserto
        r_foro = L_ins * 0.20                                                                   # Raggio foro vite Torx
        foro_ins = Part.makeCylinder(r_foro, sp_ins + 1.0, FreeCAD.Vector(c_ins.x, c_ins.y, -sp_ins - 0.5), FreeCAD.Vector(0, 0, 1))
        try:                                                                                    # Fora l'inserto del bareno
            insert_shape = solido_ins.cut(foro_ins)                                             # Inserto forato
        except Exception:                                                                       # Fallback
            insert_shape = solido_ins                                                           # Inserto pieno

        collo_l = min(D * 1.8, L * 0.35)                                                        # Lunghezza della testa anteriore ribassata
        r_gambo = D / 2.0                                                                       # Raggio del corpo cilindrico
        r_collo = r_gambo * 0.78                                                                # Raggio ridotto del collo anteriore per scarico truciolo
        asse_bar = FreeCAD.Vector(0, -r_gambo * 0.85, -r_gambo * 0.65)                          # Posizione dell'asse del gambo rispetto alla punta (0,0,0)

        cono_collo = Part.makeCone(r_collo, r_gambo, collo_l, asse_bar, FreeCAD.Vector(1, 0, 0))# Raccordo conico tra testa e gambo cilindrico
        cil_gambo = Part.makeCylinder(r_gambo, L - collo_l, asse_bar + FreeCAD.Vector(collo_l, 0, 0), FreeCAD.Vector(1, 0, 0)) # Stelo cilindrico
        naso_supp = face_ins.extrude(FreeCAD.Vector(0, 0, -r_gambo * 0.95))                     # Supporto frontale sotto l'inserto
        gambo_grezzo = cil_gambo.fuse(cono_collo).fuse(naso_supp)                               # Unisce stelo, collo conico e naso porta-inserto

        spianatura_sup = Part.makeBox(L, D * 2.0, D, FreeCAD.Vector(-5.0, -D * 1.5, 0.0))       # Piano superiore per non sporgere sopra il cielo dell'inserto
        mat_s = FreeCAD.Matrix(); mat_s.scale(1.06, 1.06, 1.0)                                  # Maggiorazione per lo scavo della tasca
        tasca_bar = face_ins.transformGeometry(mat_s).extrude(FreeCAD.Vector(0, 0, sp_ins + 2.0))
        tasca_bar.translate(FreeCAD.Vector(0, 0, -sp_ins))                                      # Posiziona la tasca
        try:                                                                                    # Esegue gli scavi di finitura sul bareno
            gambo_finito = gambo_grezzo.cut(spianatura_sup).cut(tasca_bar)                      # Scava piano superiore e tasca inserto
            perno_v = Part.makeCylinder(r_foro * 0.85, sp_ins * 0.85, FreeCAD.Vector(c_ins.x, c_ins.y, -sp_ins), FreeCAD.Vector(0, 0, 1))
            gambo_finito = gambo_finito.fuse(perno_v)                                           # Aggiunge la testa della vite Torx
        except Exception:                                                                       # Fallback
            gambo_finito = gambo_grezzo                                                         # Mantiene il bareno base

        insert_shape.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -90)              # Ruota su X
        gambo_finito.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -90)              # Ruota su X
        insert_shape.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0), -90)              # Allinea lungo l'asse mandrino Z
        gambo_finito.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0), -90)              # Allinea il bareno lungo l'asse Z

    elif tipo == "Gola / Troncatura":                                                           # 3. UTENSILE A LAMA PER GOLA E TRONCATURA (Tipo CoroCut / Q-Cut)
        W_stelo = max(float(w), 8.0)                                                            # Larghezza stelo portautensile
        H_stelo = max(float(h), 8.0)                                                            # Altezza stelo portautensile
        L_tot = max(float(l), 60.0)                                                             # Lunghezza totale utensile
        W_lama = max(min(float(lama_w), W_stelo * 0.8), 1.0)                                    # Spessore assiale della lama e dell'inserto (es. 3.0 mm)
        P_max = max(min(float(gola_p), L_tot * 0.45), 6.0)                                      # Sporgenza utile della lama di scarico (es. 20 mm)
        L_ins = max(W_lama * 3.2, 8.0)                                                          # Lunghezza dell'inserto da gola/taglio
        H_ins = max(W_lama * 1.4, 3.8)                                                          # Altezza dell'inserto da gola

        ins_box = Part.makeBox(L_ins, H_ins, W_lama, FreeCAD.Vector(0.0, -H_ins, -W_lama))      # Inserto rettangolare con spigolo di taglio frontale in (0,0,0)
        scavo_rompitruciolo = Part.makeCylinder(W_lama * 0.4, W_lama + 1.0, FreeCAD.Vector(L_ins * 0.25, 0.0, -W_lama - 0.5), FreeCAD.Vector(0, 0, 1))
        try:                                                                                    # Aggiunge l'incavo rompitruciolo superiore sull'inserto
            insert_shape = ins_box.cut(scavo_rompitruciolo)                                     # Inserto da gola sagomato
        except Exception:                                                                       # Fallback
            insert_shape = ins_box                                                              # Inserto rettangolare

        sp_lama = max(W_lama * 0.82, 0.8)                                                       # Il corpo lama è leggermente più sottile dell'inserto per non strisciare
        z_lama = -(W_lama + sp_lama) / 2.0                                                      # Centra la lama rispetto alla larghezza dell'inserto
        sotto_lama = Part.makeBox(P_max + 6.0, H_stelo * 0.85, sp_lama, FreeCAD.Vector(0.0, -H_stelo * 0.85, z_lama)) # Lama inferiore
        ganascia_sup = Part.makeBox(P_max, H_ins * 0.85, sp_lama, FreeCAD.Vector(L_ins * 0.85, -H_ins * 0.85, z_lama)) # Ganascia superiore elastica di bloccaggio
        sede_ins = Part.makeBox(L_ins * 0.92, H_ins * 0.95, W_lama + 2.0, FreeCAD.Vector(-0.5, -H_ins * 0.95, -W_lama - 1.0)) # Tasca alloggiamento inserto
        smusso_sotto = Part.makeBox(P_max, H_stelo, W_lama + 4.0, FreeCAD.Vector(0.0, -H_stelo * 1.5, -W_lama - 2.0))
        smusso_sotto.rotate(FreeCAD.Vector(0.0, -H_ins, 0.0), FreeCAD.Vector(0, 0, 1), -12.0)   # Scarico inclinato sotto la punta della lama

        lama_completa = sotto_lama.fuse(ganascia_sup)                                           # Unisce lama inferiore e ganascia superiore
        try:                                                                                    # Scava la sede dell'inserto e lo scarico inferiore
            lama_completa = lama_completa.cut(sede_ins).cut(smusso_sotto)                       # Lama sagomata pronta
        except Exception:                                                                       # Fallback
            pass                                                                                # Mantiene la lama base

        blocco_stelo = Part.makeBox(L_tot - P_max, H_stelo, W_stelo, FreeCAD.Vector(P_max, -H_stelo, -W_stelo)) # Corpo massiccio dello stelo quadro
        gambo_finito = blocco_stelo.fuse(lama_completa)                                         # Unisce stelo e lama anteriore

        insert_shape.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -90)              # Orienta sul piano XZ del tornio
        gambo_finito.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -90)              # Orienta sul piano XZ del tornio

    elif tipo == "Filettatura":                                                                 # 4. UTENSILE PER FILETTATURA (Tipo CoroThread 266)
        W = max(float(w), 8.0)                                                                  # Larghezza stelo
        H = max(float(h), 8.0)                                                                  # Altezza stelo
        L = max(float(l), 60.0)                                                                 # Lunghezza stelo
        ang_f = 55.0 if "55" in str(ang_fil) else (30.0 if "30" in str(ang_fil) else 60.0)      # Angolo del dente filettatore (60°, 55° o 30°)
        mezzo_a = math.radians(ang_f / 2.0)                                                     # Metà angolo profilo filetto
        L_dente = max(min(W * 0.55, 11.0), 6.0)                                                 # Altezza triangolo inserto
        dx_dente = L_dente * math.tan(mezzo_a)                                                  # Semilarghezza alla base del dente
        sp_ins = 3.5                                                                            # Spessore inserto filettatura

        p0 = FreeCAD.Vector(0.0, 0.0, 0.0)                                                      # Vertice tagliente del filetto in (0,0,0)
        p1 = FreeCAD.Vector(L_dente, dx_dente, 0.0)                                             # Fianco destro del dente
        p2 = FreeCAD.Vector(L_dente * 1.35, 0.0, 0.0)                                           # Coda posteriore dell'inserto
        p3 = FreeCAD.Vector(L_dente, -dx_dente, 0.0)                                            # Fianco sinistro del dente
        face_thr = Part.Face(Part.makePolygon([p0, p1, p2, p3, p0]))                            # Faccia losanga/pentagonale dell'inserto filettatore
        solido_ins = face_thr.extrude(FreeCAD.Vector(0, 0, -sp_ins))                            # Estrude l'inserto
        foro_thr = Part.makeCylinder(L_dente * 0.18, sp_ins + 1.0, FreeCAD.Vector(L_dente * 0.78, 0.0, -sp_ins - 0.5), FreeCAD.Vector(0, 0, 1))
        try:                                                                                    # Fora l'inserto filettatore
            insert_shape = solido_ins.cut(foro_thr)                                             # Inserto con foro centrale
        except Exception:                                                                       # Fallback
            insert_shape = solido_ins                                                           # Inserto pieno

        sotto_thr = face_thr.extrude(FreeCAD.Vector(0, 0, -H))                                  # Supporto sagomato sotto il dente
        stelo_thr = Part.makeBox(L - L_dente * 0.8, W, H, FreeCAD.Vector(L_dente * 0.8, -W + dx_dente, -H)) # Stelo portautensile arretrato rispetto al dente
        gambo_grezzo = stelo_thr.fuse(sotto_thr)                                                # Unisce stelo e supporto dente
        tasca_thr = face_thr.extrude(FreeCAD.Vector(0, 0, sp_ins + 1.0))                        # Volume di scavo della tasca
        tasca_thr.translate(FreeCAD.Vector(0, 0, -sp_ins))                                      # Posiziona la tasca
        try:                                                                                    # Scava la sede dell'inserto filettatore
            gambo_finito = gambo_grezzo.cut(tasca_thr)                                          # Gambo con tasca
        except Exception:                                                                       # Fallback
            gambo_finito = gambo_grezzo                                                         # Gambo base

        insert_shape.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -90)              # Orienta sul piano XZ del tornio
        gambo_finito.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -90)              # Orienta sul piano XZ del tornio

    elif tipo == "Punta da Trapano":                                                            # 5. PUNTA DA FORATURA REALISTICA (Con punta TiN dorata, eliche e codolo)
        D = max(float(w), 1.0)                                                                  # Diametro di foratura
        L = max(float(l), D * 2.5)                                                              # Lunghezza totale della punta
        tip_h = (D / 2.0) / math.tan(math.radians(118.0 / 2.0))                                 # Altezza del cono di punta a 118°
        l_tagliente = L * 0.62                                                                  # Lunghezza della parte scanalata (eliche)
        l_codolo = L - l_tagliente                                                              # Lunghezza del codolo cilindrico di presa

        h_ins_punta = min(tip_h + D * 0.35, L * 0.25)                                           # Lunghezza della cuspide rivestita TiN (dorata)
        cono_punta = Part.makeCone(0.0, D / 2.0, tip_h, FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1)) # Cono tagliente con vertice in (0,0,0)
        fascia_punta = Part.makeCylinder(D / 2.0, max(h_ins_punta - tip_h, 0.5), FreeCAD.Vector(0, 0, tip_h), FreeCAD.Vector(0, 0, 1))
        insert_shape = cono_punta.fuse(fascia_punta)                                            # Cuspide anteriore dorata

        corpo_elica = Part.makeCylinder(D / 2.0, l_tagliente, FreeCAD.Vector(0, 0, h_ins_punta), FreeCAD.Vector(0, 0, 1)) # Corpo dei taglienti
        r_gola = D * 0.28                                                                       # Raggio delle 2 gole di scarico truciolo
        gola1 = Part.makeCylinder(r_gola, l_tagliente * 0.92, FreeCAD.Vector(D * 0.36, 0, h_ins_punta * 0.5), FreeCAD.Vector(0, 0, 1))
        gola2 = Part.makeCylinder(r_gola, l_tagliente * 0.92, FreeCAD.Vector(-D * 0.36, 0, h_ins_punta * 0.5), FreeCAD.Vector(0, 0, 1))
        try:                                                                                    # Scava le gole longitudinali sul corpo e sulla punta
            insert_shape = insert_shape.cut(gola1).cut(gola2)                                   # Scarica i fianchi della punta
            corpo_elica = corpo_elica.cut(gola1).cut(gola2)                                     # Scarica le gole sul corpo punta
        except Exception:                                                                       # Fallback
            pass                                                                                # Mantiene cilindrico

        collo_raccordo = Part.makeCone(D / 2.0, D * 0.55, D * 0.25, FreeCAD.Vector(0, 0, h_ins_punta + l_tagliente), FreeCAD.Vector(0, 0, 1))
        codolo_presa = Part.makeCylinder(D * 0.55, l_codolo, FreeCAD.Vector(0, 0, h_ins_punta + l_tagliente + D * 0.25), FreeCAD.Vector(0, 0, 1))
        gambo_finito = corpo_elica.fuse(collo_raccordo).fuse(codolo_presa)                      # Unisce corpo scanalato e codolo di serraggio

    elif tipo == "Fresa":                                                                       # 6. FRESA A CANDELA REALISTICA (Testa tagliente dorata + stelo)
        D = max(float(w), 1.0)                                                                  # Diametro fresa
        L = max(float(l), D * 2.0)                                                              # Lunghezza totale fresa
        l_taglio = min(D * 1.8, L * 0.45)                                                       # Lunghezza utile dei taglienti
        insert_shape = Part.makeCylinder(D / 2.0, l_taglio, FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1)) # Parte tagliente anteriore (rivestita TiN)
        r_scavo = D * 0.22                                                                      # Raggio delle 4 gole dei taglienti
        for i in range(4):                                                                      # Scava le 4 gole a 90° sulla testa della fresa
            ang = math.radians(i * 90.0)                                                        # Angolo della gola
            g = Part.makeCylinder(r_scavo, l_taglio + 1.0, FreeCAD.Vector((D * 0.42) * math.cos(ang), (D * 0.42) * math.sin(ang), -0.5), FreeCAD.Vector(0, 0, 1))
            try: insert_shape = insert_shape.cut(g)                                             # Scava la gola
            except Exception: pass                                                              # Ignora errori
        gambo_finito = Part.makeCylinder(D / 2.0, L - l_taglio, FreeCAD.Vector(0, 0, l_taglio), FreeCAD.Vector(0, 0, 1)) # Codolo cilindrico posteriore

    elif tipo == "Maschio":                                                                     # 7. MASCHIO PER FILETTARE REALISTICO (Imbocco conico + gole + quadro trascinamento)
        D = max(float(w), 1.5)                                                                  # Diametro nominale maschio
        L = max(float(l), D * 3.0)                                                              # Lunghezza totale maschio
        tip_h = D * 0.8                                                                         # Lunghezza imbocco conico
        l_fil = min(D * 2.2, L * 0.40)                                                          # Lunghezza parte filettata
        cono_imb = Part.makeCone(D * 0.32, D / 2.0, tip_h, FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1)) # Imbocco conico
        cil_fil = Part.makeCylinder(D / 2.0, l_fil, FreeCAD.Vector(0, 0, tip_h), FreeCAD.Vector(0, 0, 1)) # Parte filettata
        insert_shape = cono_imb.fuse(cil_fil)                                                   # Testa filettante dorata
        for i in range(3):                                                                      # Scava i 3 canali dritti di scarico truciolo a 120°
            ang = math.radians(i * 120.0)                                                       # Angolo del canale
            g = Part.makeCylinder(D * 0.20, tip_h + l_fil + 1.0, FreeCAD.Vector((D * 0.44) * math.cos(ang), (D * 0.44) * math.sin(ang), -0.5), FreeCAD.Vector(0, 0, 1))
            try: insert_shape = insert_shape.cut(g)                                             # Scava il canale sul maschio
            except Exception: pass                                                              # Ignora errori
        r_stelo = D * 0.38                                                                      # Raggio del gambo ridotto dietro la filettatura
        z_stelo = tip_h + l_fil                                                                 # Quota inizio stelo
        l_stelo = max(L - z_stelo, D)                                                           # Lunghezza stelo
        gambo_finito = Part.makeCylinder(r_stelo, l_stelo, FreeCAD.Vector(0, 0, z_stelo), FreeCAD.Vector(0, 0, 1)) # Stelo cilindrico del maschio

    if insert_shape:                                                                            # Applica specchiature, rotazioni e WCS all'inserto
        if mir_x:                                                                               # Se attiva specchiatura X
            insert_shape = insert_shape.mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0))# Specchia su X
        if mir_y:                                                                               # Se attiva specchiatura Y
            insert_shape = insert_shape.mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0))# Specchia su Y
        insert_shape.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), rot_man) * insert_shape.Placement # Ruota attorno alla punta (0,0,0)
        insert_shape.translate(wcs_origin)                                                      # Trasla sul WCS (+ eventuale OffsetTorretta)

    if gambo_finito:                                                                            # Applica specchiature, rotazioni e WCS al gambo
        if mir_x:                                                                               # Se attiva specchiatura X
            gambo_finito = gambo_finito.mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0))# Specchia su X
        if mir_y:                                                                               # Se attiva specchiatura Y
            gambo_finito = gambo_finito.mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0))# Specchia su Y
        gambo_finito.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), rot_man) * gambo_finito.Placement # Ruota attorno alla punta (0,0,0)
        gambo_finito.translate(wcs_origin)                                                      # Trasla sul WCS (+ eventuale OffsetTorretta)

    return gambo_finito, insert_shape                                                           # Restituisce il gambo e l'inserto finiti


class LatheToolObject:                                                                          # Classe Proxy per l'oggetto Utensile parametrico
    def __init__(self, obj):                                                                    # Costruttore del Proxy
        self._is_executing = False                                                              # Flag interno per evitare ricalcoli ricorsivi
        self.ensure_properties(obj)                                                             # Garantisce la presenza di tutte le proprietà
        obj.Proxy = self                                                                        # Collega il Proxy all'oggetto FreeCAD

    def ensure_properties(self, obj):                                                           # Aggiunge o aggiorna tutte le proprietà geometriche e tecnologiche
        if not hasattr(obj, "ToolName"):                                                        # Nome descrittivo utensile
            obj.addProperty("App::PropertyString", "ToolName", "Dati", "Nome Utensile").ToolName = "Utensile Sgrosso 1"
        if not hasattr(obj, "Stazione"):                                                        # Codice stazione (es. T01..T12)
            obj.addProperty("App::PropertyString", "Stazione", "Dati", "Stazione torretta").Stazione = "T01"
        if not hasattr(obj, "NumeroStazione"):                                                  # Indice numerico stazione per la Torretta
            obj.addProperty("App::PropertyInteger", "NumeroStazione", "Dati", "Indice posizione su torretta").NumeroStazione = 1
        if not hasattr(obj, "OffsetTorretta"):                                                  # Offset di montaggio sulla Torretta 3D
            obj.addProperty("App::PropertyVector", "OffsetTorretta", "Dati", "Offset montaggio su torretta").OffsetTorretta = FreeCAD.Vector(0, 0, 0)
        if not hasattr(obj, "RotazioneTorretta"):                                               # Quaternione di rotazione trascinato dalla Torretta
            obj.addProperty("App::PropertyFloatList", "RotazioneTorretta", "Dati", "Quaternione rotazione torretta").RotazioneTorretta = [0.0, 0.0, 0.0, 1.0]
        if not hasattr(obj, "Modalita"):                                                        # Modalità Parametrico o Custom STEP
            obj.addProperty("App::PropertyEnumeration", "Modalita", "Dati", "Modalità generazione")
            obj.Modalita = ["Parametrico", "Custom"]                                            # Opzioni

        if not hasattr(obj, "TipoLavorazione"):                                                 # Categoria lavorazione utensile
            obj.addProperty("App::PropertyEnumeration", "TipoLavorazione", "Dati", "Categoria utensile")
            obj.TipoLavorazione = CATEGORIE_UTENSILI                                            # Assegna tutte le 7 categorie
        else:                                                                                   # Aggiorna le opzioni su utensili già esistenti
            curr_t = str(obj.TipoLavorazione)                                                   # Valore corrente
            obj.TipoLavorazione = CATEGORIE_UTENSILI                                            # Aggiorna lista includendo Gola e Filettatura
            if curr_t in CATEGORIE_UTENSILI: obj.TipoLavorazione = curr_t                       # Ripristina valore

        if not hasattr(obj, "FormaInserto"):                                                    # Forma inserto ISO (C, D, V, T, S)
            obj.addProperty("App::PropertyEnumeration", "FormaInserto", "Geometria Inserto", "Forma inserto ISO")
            obj.FormaInserto = FORME_INSERTO_ISO                                                # Assegna le 5 forme ISO
        else:                                                                                   # Aggiorna opzioni su oggetti esistenti
            curr_f = str(obj.FormaInserto)                                                      # Valore corrente
            obj.FormaInserto = FORME_INSERTO_ISO                                                # Aggiorna lista includendo Rombico 35° (V)
            if curr_f in FORME_INSERTO_ISO: obj.FormaInserto = curr_f                           # Ripristina

        if not hasattr(obj, "RaggioInserto"):                                                   # Raggio di punta inserto (mm)
            obj.addProperty("App::PropertyEnumeration", "RaggioInserto", "Geometria Inserto", "Raggio punta (mm)")
            obj.RaggioInserto = ["0.1", "0.2", "0.4", "0.8", "1.2", "1.6"]                      # Raggi standard commerciali
        if not hasattr(obj, "Verso"):                                                           # Verso utensile (R, L, N)
            obj.addProperty("App::PropertyEnumeration", "Verso", "Geometria Inserto", "Verso utensile")
            obj.Verso = ["Destro (R)", "Sinistro (L)", "Neutro (N)"]                            # Opzioni
        if not hasattr(obj, "AngoloReg"):                                                       # Angolo di registrazione Kapr (gradi)
            obj.addProperty("App::PropertyFloat", "AngoloReg", "Geometria Inserto", "Angolo di registrazione (deg)").AngoloReg = 93.0
        if not hasattr(obj, "LarghezzaLamaGola"):                                               # Larghezza lama/inserto per Gola e Troncatura (mm)
            obj.addProperty("App::PropertyFloat", "LarghezzaLamaGola", "Geometria Inserto", "Larghezza lama gola/troncatura (mm)").LarghezzaLamaGola = 3.0
        if not hasattr(obj, "ProfonditaMaxGola"):                                               # Sporgenza utile lama per Gola e Troncatura (mm)
            obj.addProperty("App::PropertyFloat", "ProfonditaMaxGola", "Geometria Inserto", "Profondità max gola/taglio (mm)").ProfonditaMaxGola = 22.0
        if not hasattr(obj, "AngoloFiletto"):                                                   # Angolo profilo per Filettatura
            obj.addProperty("App::PropertyEnumeration", "AngoloFiletto", "Geometria Inserto", "Angolo profilo filetto")
            obj.AngoloFiletto = ["60° (Metrico ISO)", "55° (GAS / Whitworth)", "30° (Trapezoidale)"]

        if not hasattr(obj, "Larghezza"):                                                       # Larghezza o Diametro gambo (mm)
            obj.addProperty("App::PropertyFloat", "Larghezza", "Dimensioni Corpo", "Larghezza o Diametro (mm)").Larghezza = 12.0
        if not hasattr(obj, "Altezza"):                                                         # Altezza gambo (mm)
            obj.addProperty("App::PropertyFloat", "Altezza", "Dimensioni Corpo", "Altezza gambo (mm)").Altezza = 12.0
        if not hasattr(obj, "Lunghezza"):                                                       # Lunghezza totale utensile (mm)
            obj.addProperty("App::PropertyFloat", "Lunghezza", "Dimensioni Corpo", "Lunghezza totale (mm)").Lunghezza = 100.0

        if not hasattr(obj, "ModoVelocita"):                                                    # G96 (m/min) o G97 (RPM)
            obj.addProperty("App::PropertyEnumeration", "ModoVelocita", "Tecnologia Taglio", "Modalità velocità mandrino")
            obj.ModoVelocita = ["G96 - Vel. Taglio Costante (m/min)", "G97 - Giri Fissi (RPM)"]
        if not hasattr(obj, "VelocitaTaglio"):                                                  # Valore velocità di taglio Vc o RPM
            obj.addProperty("App::PropertyFloat", "VelocitaTaglio", "Tecnologia Taglio", "Velocità di taglio Vc o Giri RPM").VelocitaTaglio = 180.0
        if not hasattr(obj, "AvanzamentoSgrosso"):                                              # Avanzamento in sgrossatura (mm/giro)
            obj.addProperty("App::PropertyFloat", "AvanzamentoSgrosso", "Tecnologia Taglio", "Avanzamento sgrossatura (mm/giro)").AvanzamentoSgrosso = 0.25
        if not hasattr(obj, "AvanzamentoFinitura"):                                             # Avanzamento in finitura (mm/giro)
            obj.addProperty("App::PropertyFloat", "AvanzamentoFinitura", "Tecnologia Taglio", "Avanzamento finitura (mm/giro)").AvanzamentoFinitura = 0.10
        if not hasattr(obj, "ProfonditaPassataMax"):                                            # Profondità di passata massima Ap (mm)
            obj.addProperty("App::PropertyFloat", "ProfonditaPassataMax", "Tecnologia Taglio", "Profondità passata max Ap (mm)").ProfonditaPassataMax = 2.0
        if not hasattr(obj, "QuadrantePuntaISO"):                                               # Quadrante ISO 1..9 per compensazione raggio G41/G42
            obj.addProperty("App::PropertyEnumeration", "QuadrantePuntaISO", "Tecnologia Taglio", "Quadrante orientamento punta ISO (1-9)")
            obj.QuadrantePuntaISO = QUADRANTI_ISO                                               # Assegna i 9 quadranti
            obj.QuadrantePuntaISO = "Q3 - Esterno Destro Standard"                              # Default Q3

        if not hasattr(obj, "SpecchiaX"):                                                       # Specchiatura X
            obj.addProperty("App::PropertyBool", "SpecchiaX", "Orientamento", "Specchia su asse X").SpecchiaX = False
        if not hasattr(obj, "SpecchiaY"):                                                       # Specchiatura Y
            obj.addProperty("App::PropertyBool", "SpecchiaY", "Orientamento", "Specchia su asse Y").SpecchiaY = False
        if not hasattr(obj, "RotX"):                                                            # Rotazione X
            obj.addProperty("App::PropertyFloat", "RotX", "Orientamento", "Rotazione asse X (deg)").RotX = 0.0
        if not hasattr(obj, "RotY"):                                                            # Rotazione Y
            obj.addProperty("App::PropertyFloat", "RotY", "Orientamento", "Rotazione asse Y (deg)").RotY = 0.0
        if not hasattr(obj, "RotZ"):                                                            # Rotazione Z
            obj.addProperty("App::PropertyFloat", "RotZ", "Orientamento", "Rotazione asse Z (deg)").RotZ = 0.0
        if not hasattr(obj, "CustomBaseShape"):                                                 # Geometria STEP per utensili custom
            obj.addProperty("Part::PropertyPartShape", "CustomBaseShape", "Custom", "Geometria STEP base")
        if not hasattr(obj, "CustomSolidColors"):                                               # Lista colori per utensili custom
            obj.addProperty("App::PropertyStringList", "CustomSolidColors", "Custom", "Colori RGB dei solidi custom")
        if not hasattr(obj, "InsertTagged"):                                                    # Flag inserto taggato
            obj.addProperty("App::PropertyBool", "InsertTagged", "Custom", "Inserto taggato").InsertTagged = False
        if not hasattr(obj, "VertexDefined"):                                                   # Flag punta definita
            obj.addProperty("App::PropertyBool", "VertexDefined", "Custom", "Punta definita").VertexDefined = False

    def onDocumentRestored(self, obj):                                                          # Chiamato da FreeCAD alla riapertura del file
        self._is_executing = False                                                              # Ripristina il flag di esecuzione
        self.ensure_properties(obj)                                                             # Verifica tutte le proprietà

    def execute(self, obj):                                                                     # Ricalcola la geometria 3D e i colori dell'utensile
        if getattr(self, "_is_executing", False):                                               # Evita cicli infiniti
            return                                                                              # Esce subito
        self._is_executing = True                                                               # Imposta il blocco
        try:                                                                                    # Blocco protetto di generazione
            self.ensure_properties(obj)                                                         # Verifica attributi
            wcs_origin = get_wcs_origin(obj.Document) + obj.OffsetTorretta                      # Somma origine WCS ed eventuale offset Torretta
            rot_x = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), obj.RotX)                         # Rotazione X
            rot_y = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), obj.RotY)                         # Rotazione Y
            rot_z = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), obj.RotZ)                         # Rotazione Z
            rot_local = rot_x * rot_y * rot_z                                                   # Rotazione locale dell'utensile
            q = list(getattr(obj, "RotazioneTorretta", [0.0, 0.0, 0.0, 1.0]))                   # Legge il quaternione di trascinamento della torretta
            rot_turret = FreeCAD.Rotation(q[0], q[1], q[2], q[3]) if len(q) == 4 else FreeCAD.Rotation() # Rotazione torretta
            rot_man = rot_turret * rot_local                                                    # Orientamento combinato (torretta * utensile)
            face_colors = []                                                                    # Lista colori per singola faccia

            if obj.Modalita == "Parametrico":                                                   # Caso 1: Utensile generato parametricamente
                tipo = str(obj.TipoLavorazione)                                                 # Categoria utensile
                w = max(obj.Larghezza, 1.0)                                                     # Larghezza/Diametro
                h = max(obj.Altezza, 1.0) if tipo in ["Esterno (ISO)", "Gola / Troncatura", "Filettatura"] else w # Altezza stelo
                l = max(obj.Lunghezza, 5.0)                                                     # Lunghezza totale
                gambo, inserto = genera_forme_parametriche(                                     # Genera i solidi realistici
                    tipo, str(obj.FormaInserto), str(obj.Verso), obj.AngoloReg, w, h, l,        # Parametri base
                    obj.LarghezzaLamaGola, obj.ProfonditaMaxGola, str(obj.AngoloFiletto),       # Parametri gola e filetto
                    obj.SpecchiaX, obj.SpecchiaY, rot_man, wcs_origin                           # Orientamento e WCS
                )                                                                               # Fine generazione
                shapes = []                                                                     # Lista solidi
                col_gambo = (0.72, 0.74, 0.77) if tipo in ["Punta da Trapano", "Fresa", "Maschio"] else (0.28, 0.30, 0.33) # Grigio acciaio o brunito
                col_ins = (0.92, 0.72, 0.12)                                                    # Giallo Oro TiN per inserto/taglienti
                if gambo:                                                                       # Se il gambo esiste
                    shapes.append(gambo)                                                        # Aggiunge il gambo
                    face_colors.extend([col_gambo] * len(gambo.Faces))                          # Colora le facce del gambo
                if inserto:                                                                     # Se l'inserto/cuspide esiste
                    shapes.append(inserto)                                                      # Aggiunge l'inserto
                    face_colors.extend([col_ins] * len(inserto.Faces))                          # Colora in oro le facce dell'inserto
                if shapes:                                                                      # Compone l'utensile
                    obj.Shape = Part.makeCompound(shapes)                                       # Assegna il Compound
            else:                                                                               # Caso 2: Utensile importato da STEP custom
                base_comp = obj.CustomBaseShape                                                 # Legge la forma STEP salvata
                if base_comp and not base_comp.isNull():                                        # Verifica validità
                    subshapes = list(base_comp.SubShapes) if hasattr(base_comp, "SubShapes") and base_comp.SubShapes else list(base_comp.Solids)
                    saved_cols = list(obj.CustomSolidColors)                                    # Colori salvati
                    transformed = []                                                            # Solidi trasformati
                    for idx, s in enumerate(subshapes):                                         # Cicla sui solidi custom
                        ns = s.copy()                                                           # Copia il solido
                        if obj.SpecchiaX: ns = ns.mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0))
                        if obj.SpecchiaY: ns = ns.mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0))
                        ns.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), rot_man) * ns.Placement
                        ns.translate(wcs_origin)                                                # Posiziona sul WCS
                        transformed.append(ns)                                                  # Aggiunge alla lista
                        col = (0.5, 0.5, 0.5)                                                   # Colore default
                        if idx < len(saved_cols):                                               # Legge il colore salvato
                            try:
                                parts = [float(x) for x in saved_cols[idx].split(",")]          # Converte RGB
                                if len(parts) >= 3: col = (parts[0], parts[1], parts[2])        # Tupla RGB
                            except Exception: pass                                              # Ignora errori
                        face_colors.extend([col] * len(ns.Faces))                               # Colora tutte le facce del solido
                    if transformed:                                                             # Compone l'utensile custom
                        obj.Shape = Part.makeCompound(transformed)                              # Assegna il Compound
            if hasattr(obj, "ViewObject") and obj.ViewObject and face_colors:                   # Applica i colori nella vista 3D
                if len(face_colors) == len(obj.Shape.Faces):                                    # Verifica corrispondenza facce
                    obj.ViewObject.DiffuseColor = face_colors                                   # Applica DiffuseColor
        except Exception as e:                                                                  # Cattura errori
            FreeCAD.Console.PrintError(f"Errore ricalcolo utensile: {e}\n")                     # Stampa errore
        finally:                                                                                # Eseguito sempre in uscita
            self._is_executing = False                                                          # Rilascia il blocco

    def onChanged(self, obj, prop):                                                             # Intercetta modifiche live dalle Proprietà
        if getattr(self, "_is_executing", False):                                               # Evita loop ricorsivi
            return                                                                              # Esce
        props_live = [                                                                          # Proprietà che aggiornano il 3D
            "Modalita", "TipoLavorazione", "FormaInserto", "RaggioInserto",                     # Tipo e inserto
            "Verso", "AngoloReg", "LarghezzaLamaGola", "ProfonditaMaxGola", "AngoloFiletto",    # Gola e filetto
            "Larghezza", "Altezza", "Lunghezza",                                                # Dimensioni corpo
            "SpecchiaX", "SpecchiaY", "RotX", "RotY", "RotZ",                                   # Orientamento
            "CustomBaseShape", "CustomSolidColors", "OffsetTorretta", "RotazioneTorretta"       # Custom e Torretta
        ]                                                                                       # Fine elenco
        if prop in props_live:                                                                  # Se è cambiata una proprietà geometrica
            self.execute(obj)                                                                   # Aggiorna il 3D
        elif prop == "NumeroStazione":                                                          # Se cambia il numero stazione
            if hasattr(obj, "NumeroStazione") and obj.NumeroStazione > 0:                       # Sincronizza la stringa Stazione
                self._is_executing = True                                                       # Blocca loop
                obj.Stazione = f"T{int(obj.NumeroStazione):02d}"                                # Imposta T01..Txx
                self._is_executing = False                                                      # Sblocca
        elif prop == "ToolName":                                                                # Se cambia il nome
            if hasattr(obj, "ToolName") and obj.ToolName:                                       # Allinea l'etichetta
                obj.Label = obj.ToolName                                                        # Imposta Label

    def __getstate__(self):                                                                     # Serializzazione
        return None                                                                             # Nessun dato speciale

    def __setstate__(self, state):                                                              # Deserializzazione
        self._is_executing = False                                                              # Inizializza flag
        return None                                                                             # Fine


class ViewProviderLatheTool:                                                                    # ViewProvider per gestire icona e doppio click
    def __init__(self, vobj):                                                                   # Costruttore ViewProvider
        vobj.Proxy = self                                                                       # Collega il ViewProvider

    def getIcon(self):                                                                          # Icona nell'albero
        return "Std_Tool1"                                                                      # Icona utensile

    def attach(self, vobj):                                                                     # Collega gli oggetti alla vista
        self.ViewObject = vobj                                                                  # Riferimento ViewObject
        self.Object = vobj.Object                                                               # Riferimento Object

    def updateData(self, vobj, prop):                                                           # Aggiornamento dati
        return                                                                                  # Gestito da execute

    def onDelete(self, vobj, subelements):                                                      # Autorizza cancellazione
        return True                                                                             # Sempre consentito

    def doubleClicked(self, vobj):                                                              # Doppio click sull'utensile nell'albero
        if not FreeCADGui.Control.activeDialog():                                               # Se non c'è già un dialogo aperto
            panel = LatheToolManager(edit_obj=vobj.Object)                                      # Apre il pannello sull'utensile
            FreeCADGui.Control.showDialog(panel)                                                # Mostra il pannello
        return True                                                                             # Evento gestito

    def setEdit(self, vobj, mode):                                                              # Modalità Edit standard
        if mode == 0:                                                                           # Modifica base
            if not FreeCADGui.Control.activeDialog():                                           # Evita doppia apertura
                panel = LatheToolManager(edit_obj=vobj.Object)                                  # Crea il pannello
                FreeCADGui.Control.showDialog(panel)                                            # Mostra il dialogo
            return True                                                                         # Conferma
        return False                                                                            # Rifiuta altre modalità

    def unsetEdit(self, vobj, mode):                                                            # Uscita da Edit
        FreeCADGui.Control.closeDialog()                                                        # Chiude il pannello
        return True                                                                             # Conferma

    def __getstate__(self):                                                                     # Serializzazione
        return None                                                                             # Nessuno stato extra

    def __setstate__(self, state):                                                              # Deserializzazione
        return None                                                                             # Nessuno stato extra


class LatheToolManager:                                                                         # Pannello Task per creazione, modifica e archivio utensili
    def __init__(self, edit_obj=None):                                                          # Inizializza il pannello (nuovo o modifica)
        self.edit_obj = edit_obj                                                                # Memorizza l'eventuale utensile in modifica
        self.is_updating = True                                                                 # Blocca i segnali durante la costruzione della UI
        self.oggetti_importati_dati = []                                                        # Lista [obj_preview, forma_base_originale, colore_rgb]
        self.insert_tagged = False                                                              # Flag inserto custom taggato
        self.vertex_defined = False                                                             # Flag punta custom azzerata
        self.visibilita_precedente = {}                                                         # Mappa visibilità degli altri utensili

        doc = FreeCAD.ActiveDocument                                                            # Ottiene il documento attivo
        self.pulisci_anteprima_residua(doc)                                                     # Elimina eventuali anteprime rimaste appese
        self.nascondi_altri_utensili(doc)                                                       # Nasconde gli altri utensili per liberare la vista sul WCS

        self.form = QtWidgets.QWidget()                                                         # Crea il widget principale del pannello
        self.form.setMinimumWidth(240)                                                          # Larghezza minima compatta per non uscire dai bordi
        self.layout = QtWidgets.QVBoxLayout(self.form)                                          # Crea il layout verticale principale
        self.layout.setContentsMargins(4, 4, 4, 4)                                              # Riduce i margini laterali per guadagnare spazio

        self.grp_db = QtWidgets.QGroupBox("Archivio Utensili (Database)")                       # Gruppo per caricare/salvare utensili tra sessioni
        self.lyt_db = QtWidgets.QVBoxLayout(self.grp_db)                                        # Layout verticale per il gruppo archivio
        self.db_combo = QtWidgets.QComboBox()                                                   # Menu a tendina con gli utensili presenti su disco
        self.db_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.db_combo.setMinimumContentsLength(10)                                              # Lunghezza minima compatta
        self.lyt_db.addWidget(self.db_combo)                                                    # Tendina su tutta la larghezza

        self.lyt_db_top = QtWidgets.QHBoxLayout()                                               # Riga pulsanti Carica ed Elimina
        self.btn_load_db = QtWidgets.QPushButton("Carica Utensile")                             # Pulsante carica utensile
        self.btn_load_db.clicked.connect(self.carica_utensile_da_db)                            # Collega il caricamento
        self.btn_del_db = QtWidgets.QPushButton("Elimina")                                      # Pulsante elimina utensile
        self.btn_del_db.clicked.connect(self.elimina_utensile_da_db)                            # Collega l'eliminazione
        self.lyt_db_top.addWidget(self.btn_load_db)                                             # Aggiunge pulsante Carica
        self.lyt_db_top.addWidget(self.btn_del_db)                                              # Aggiunge pulsante Elimina
        self.lyt_db.addLayout(self.lyt_db_top)                                                  # Inserisce la riga nel gruppo

        self.btn_load_all = QtWidgets.QPushButton("Importa Tutto il Magazzino nel Progetto")    # Pulsante importazione massiva
        self.btn_load_all.clicked.connect(self.importa_tutto_il_magazzino)                      # Collega l'importazione massiva
        self.lyt_db.addWidget(self.btn_load_all)                                                # Aggiunge il pulsante

        self.chk_save_db = QtWidgets.QCheckBox("Salva in Archivio Permanente all'OK")           # Salvataggio automatico su disco
        self.chk_save_db.setChecked(True)                                                       # Attivo di default
        self.lyt_db.addWidget(self.chk_save_db)                                                 # Aggiunge al gruppo archivio
        self.layout.addWidget(self.grp_db)                                                      # Aggiunge il gruppo al pannello

        self.grp_def = QtWidgets.QGroupBox("Dati Generali e Stazione Torretta")                 # Gruppo per nome e stazione torretta
        self.lyt_def = QtWidgets.QFormLayout(self.grp_def)                                      # Layout a modulo
        self.name_input = QtWidgets.QLineEdit("Utensile Sgrosso 1")                             # Campo nome utensile

        self.max_stat_spin = QtWidgets.QSpinBox()                                               # Spinbox numero totale posizioni torretta
        self.max_stat_spin.setRange(1, 36)                                                      # Da 1 a 36 posizioni
        self.max_stat_spin.setValue(get_max_turret_stations(doc))                               # Legge dalla torretta (o 8)
        self.max_stat_spin.valueChanged.connect(self.aggiorna_lista_stazioni)                   # Aggiorna T01..Txx

        self.stat_combo = QtWidgets.QComboBox()                                                 # Menu a tendina stazione
        self.popola_combo_stazioni(self.max_stat_spin.value())                                  # Popola le stazioni

        self.lyt_def.addRow("Nome:", self.name_input)                                           # Riga Nome
        self.lyt_def.addRow("N° Posizioni Torretta:", self.max_stat_spin)                       # Riga N° Posizioni
        self.lyt_def.addRow("Stazione Assegnata:", self.stat_combo)                             # Riga Stazione
        self.layout.addWidget(self.grp_def)                                                     # Aggiunge al layout principale

        self.tabs = QtWidgets.QTabWidget()                                                      # Contenitore a 3 schede: 1.Parametrico | 2.Custom | 3.Tecnologia

        self.tab_std = QtWidgets.QWidget()                                                      # SCHEDA 1: Generazione Parametrica Realistica
        self.lyt_std = QtWidgets.QVBoxLayout(self.tab_std)                                      # Layout verticale Scheda 1

        self.grp_tipo = QtWidgets.QGroupBox("Categoria Lavorazione")                            # Gruppo selezione categoria
        self.lyt_tipo = QtWidgets.QVBoxLayout(self.grp_tipo)                                    # Layout gruppo
        self.tool_type_combo = QtWidgets.QComboBox()                                            # Tendina categorie
        self.tool_type_combo.addItems(CATEGORIE_UTENSILI)                                       # Popola tutte le 7 categorie
        self.tool_type_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.tool_type_combo.setMinimumContentsLength(10)
        self.lyt_tipo.addWidget(self.tool_type_combo)                                           # Aggiunge la tendina
        self.lyt_std.addWidget(self.grp_tipo)                                                   # Aggiunge alla Scheda 1

        self.grp_geo = QtWidgets.QGroupBox("Geometria Inserto / Tagliente")                     # Gruppo parametri inserto/lama/filetto
        self.lyt_geo = QtWidgets.QFormLayout(self.grp_geo)                                      # Layout a modulo

        self.lbl_shape = QtWidgets.QLabel("Forma Inserto:")                                     # Etichetta Forma Inserto ISO
        self.shape_combo = QtWidgets.QComboBox()                                                # Menu forma inserto
        self.shape_combo.addItems(FORME_INSERTO_ISO)                                            # C, D, V, T, S
        self.shape_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.shape_combo.setMinimumContentsLength(10)

        self.lbl_rad = QtWidgets.QLabel("Raggio Punta (mm):")                                   # Etichetta Raggio Punta
        self.rad_combo = QtWidgets.QComboBox()                                                  # Menu raggio di punta
        self.rad_combo.addItems(["0.1", "0.2", "0.4", "0.8", "1.2", "1.6"])                     # Raggi standard
        self.rad_combo.setCurrentText("0.4")                                                    # Default 0.4 mm

        self.lbl_hand = QtWidgets.QLabel("Verso Taglio:")                                       # Etichetta Verso
        self.hand_combo = QtWidgets.QComboBox()                                                 # Menu verso di taglio
        self.hand_combo.addItems(["Destro (R)", "Sinistro (L)", "Neutro (N)"])                  # Versi disponibili

        self.lbl_rot = QtWidgets.QLabel("Angolo Reg. Kapr (°):")                                # Etichetta Angolo Registrazione
        self.rot_input = QtWidgets.QDoubleSpinBox()                                             # Spinbox angolo di registrazione
        self.rot_input.setRange(-180.0, 180.0); self.rot_input.setValue(93.0)                   # Default 93° (tipo PDJNR / PCLNR)

        self.lbl_lama_w = QtWidgets.QLabel("Larghezza Lama (mm):")                              # Etichetta Larghezza Lama Gola/Troncatura
        self.lama_w_spin = QtWidgets.QDoubleSpinBox()                                           # Spinbox larghezza lama
        self.lama_w_spin.setRange(0.5, 25.0); self.lama_w_spin.setValue(3.0); self.lama_w_spin.setSingleStep(0.5)

        self.lbl_gola_p = QtWidgets.QLabel("Profondità Max Gola (mm):")                         # Etichetta Sporgenza Lama
        self.gola_p_spin = QtWidgets.QDoubleSpinBox()                                           # Spinbox profondità massima gola/taglio
        self.gola_p_spin.setRange(3.0, 150.0); self.gola_p_spin.setValue(22.0)

        self.lbl_ang_fil = QtWidgets.QLabel("Profilo Filetto:")                                 # Etichetta Angolo Filetto
        self.ang_fil_combo = QtWidgets.QComboBox()                                              # Menu angolo filetto
        self.ang_fil_combo.addItems(["60° (Metrico ISO)", "55° (GAS / Whitworth)", "30° (Trapezoidale)"])
        self.ang_fil_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.ang_fil_combo.setMinimumContentsLength(10)

        self.lyt_geo.addRow(self.lbl_shape, self.shape_combo)                                   # Riga Forma Inserto
        self.lyt_geo.addRow(self.lbl_rad, self.rad_combo)                                       # Riga Raggio
        self.lyt_geo.addRow(self.lbl_hand, self.hand_combo)                                     # Riga Verso
        self.lyt_geo.addRow(self.lbl_rot, self.rot_input)                                       # Riga Angolo Registrazione
        self.lyt_geo.addRow(self.lbl_lama_w, self.lama_w_spin)                                  # Riga Larghezza Lama
        self.lyt_geo.addRow(self.lbl_gola_p, self.gola_p_spin)                                  # Riga Profondità Gola
        self.lyt_geo.addRow(self.lbl_ang_fil, self.ang_fil_combo)                               # Riga Angolo Filetto
        self.lyt_std.addWidget(self.grp_geo)                                                    # Aggiunge il gruppo alla Scheda 1

        self.grp_dim = QtWidgets.QGroupBox("Dimensioni Corpo / Stelo")                          # Gruppo dimensioni stelo/corpo
        self.lyt_dim = QtWidgets.QFormLayout(self.grp_dim)                                      # Layout a modulo
        self.w_input = QtWidgets.QDoubleSpinBox(); self.w_input.setRange(1.0, 100.0); self.w_input.setValue(12.0) # Larghezza/Diametro (default 12 mm)
        self.h_input = QtWidgets.QDoubleSpinBox(); self.h_input.setRange(1.0, 100.0); self.h_input.setValue(12.0) # Altezza stelo (default 12 mm)
        self.l_input = QtWidgets.QDoubleSpinBox(); self.l_input.setRange(5.0, 500.0); self.l_input.setValue(100.0)# Lunghezza totale (default 100 mm)

        self.lbl_w = QtWidgets.QLabel("Larghezza Stelo (mm):")                                  # Etichetta dinamica W
        self.lbl_h = QtWidgets.QLabel("Altezza Stelo (mm):")                                    # Etichetta dinamica H
        self.lbl_l = QtWidgets.QLabel("Lunghezza Totale (mm):")                                 # Etichetta dinamica L

        self.lyt_dim.addRow(self.lbl_w, self.w_input)                                           # Riga Larghezza
        self.lyt_dim.addRow(self.lbl_h, self.h_input)                                           # Riga Altezza
        self.lyt_dim.addRow(self.lbl_l, self.l_input)                                           # Riga Lunghezza
        self.lyt_std.addWidget(self.grp_dim)                                                    # Aggiunge alla Scheda 1
        self.tabs.addTab(self.tab_std, "1. Geometria")                                          # Titolo Scheda 1 compatto

        self.tab_cst = QtWidgets.QWidget()                                                      # SCHEDA 2: Importazione Custom STEP
        self.lyt_cst = QtWidgets.QVBoxLayout(self.tab_cst)                                      # Layout verticale Scheda 2
        self.btn_import = QtWidgets.QPushButton("1. Importa File 3D (STEP/FCStd)")              # Pulsante passo 1
        self.btn_import.clicked.connect(self.importa_file)                                      # Collega importa_file
        self.lyt_cst.addWidget(self.btn_import)                                                 # Aggiunge passo 1
        self.btn_set_insert = QtWidgets.QPushButton("2. Tagga Inserto da Selezione")            # Pulsante passo 2
        self.btn_set_insert.clicked.connect(self.tagga_inserto)                                 # Collega tagga_inserto
        self.lyt_cst.addWidget(self.btn_set_insert)                                             # Aggiunge passo 2
        self.btn_set_zero = QtWidgets.QPushButton("3. Definisci Punta da Vertice")              # Pulsante passo 3
        self.btn_set_zero.clicked.connect(self.definisci_punta)                                 # Collega definisci_punta
        self.lyt_cst.addWidget(self.btn_set_zero)                                               # Aggiunge passo 3
        self.lbl_status = QtWidgets.QLabel("Stato: In attesa di importazione...")               # Etichetta stato custom
        self.lbl_status.setWordWrap(True)                                                       # Va a capo automaticamente
        self.lbl_status.setStyleSheet("color: #FFAA00; font-weight: bold;")                     # Stile arancione
        self.lyt_cst.addWidget(self.lbl_status)                                                 # Aggiunge etichetta
        self.lyt_cst.addStretch()                                                               # Allinea in alto
        self.tabs.addTab(self.tab_cst, "2. Custom 3D")                                          # Titolo Scheda 2 compatto

        self.tab_tech = QtWidgets.QWidget()                                                     # SCHEDA 3: Tecnologia di Taglio & Quadrante ISO
        self.lyt_tech = QtWidgets.QVBoxLayout(self.tab_tech)                                    # Layout verticale Scheda 3
        self.grp_tech = QtWidgets.QGroupBox("Parametri di Taglio e Compensazione ISO")          # Gruppo tecnologia
        self.lyt_t_form = QtWidgets.QFormLayout(self.grp_tech)                                  # Form layout tecnologia

        self.speed_mode_combo = QtWidgets.QComboBox()                                           # Scelta G96 / G97
        self.speed_mode_combo.addItems(["G96 - Vel. Taglio Costante (m/min)", "G97 - Giri Fissi (RPM)"])
        self.speed_mode_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.speed_mode_combo.setMinimumContentsLength(10)

        self.vc_spin = QtWidgets.QDoubleSpinBox(); self.vc_spin.setRange(1.0, 15000.0); self.vc_spin.setValue(180.0); self.vc_spin.setSingleStep(10.0) # Vc / RPM
        self.f_rough_spin = QtWidgets.QDoubleSpinBox(); self.f_rough_spin.setRange(0.01, 20.0); self.f_rough_spin.setDecimals(3); self.f_rough_spin.setValue(0.25); self.f_rough_spin.setSingleStep(0.05) # f sgrosso
        self.f_fin_spin = QtWidgets.QDoubleSpinBox(); self.f_fin_spin.setRange(0.005, 10.0); self.f_fin_spin.setDecimals(3); self.f_fin_spin.setValue(0.10); self.f_fin_spin.setSingleStep(0.02) # f finitura
        self.ap_max_spin = QtWidgets.QDoubleSpinBox(); self.ap_max_spin.setRange(0.05, 50.0); self.ap_max_spin.setDecimals(2); self.ap_max_spin.setValue(2.0); self.ap_max_spin.setSingleStep(0.5) # Ap max

        self.quad_iso_combo = QtWidgets.QComboBox()                                             # Scelta Quadrante Punta ISO 1..9
        self.quad_iso_combo.addItems(QUADRANTI_ISO)                                             # Popola Q1..Q9
        self.quad_iso_combo.setCurrentText("Q3 - Esterno Destro Standard")                      # Default Q3
        self.quad_iso_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.quad_iso_combo.setMinimumContentsLength(10)

        self.lyt_t_form.addRow("Modo Velocità:", self.speed_mode_combo)                         # Riga G96/G97
        self.lyt_t_form.addRow("Valore Vc / RPM:", self.vc_spin)                                # Riga Vc / RPM
        self.lyt_t_form.addRow("Avanz. Sgrosso (mm/g):", self.f_rough_spin)                     # Riga Avanzamento Sgrosso
        self.lyt_t_form.addRow("Avanz. Finitura (mm/g):", self.f_fin_spin)                      # Riga Avanzamento Finitura
        self.lyt_t_form.addRow("Passata Max Ap (mm):", self.ap_max_spin)                        # Riga Profondità Passata Max
        self.lyt_t_form.addRow("Quadrante ISO:", self.quad_iso_combo)                           # Riga Quadrante Punta ISO
        self.lyt_tech.addWidget(self.grp_tech)                                                  # Aggiunge alla Scheda 3
        self.lyt_tech.addStretch()                                                              # Allinea in alto
        self.tabs.addTab(self.tab_tech, "3. Tecnologia")                                        # Titolo Scheda 3 compatto

        self.layout.addWidget(self.tabs)                                                        # Aggiunge il TabWidget al layout principale

        self.grp_rot = QtWidgets.QGroupBox("Orientamento Spaziale 3D (Live)")                   # Gruppo controlli di rotazione e specchio
        self.lyt_rot = QtWidgets.QFormLayout(self.grp_rot)                                      # Layout a modulo
        self.chk_mir_x = QtWidgets.QCheckBox("Specchia X")                                      # Specchia X
        self.chk_mir_y = QtWidgets.QCheckBox("Specchia Y")                                      # Specchia Y
        self.rx_spin = QtWidgets.QDoubleSpinBox(); self.rx_spin.setRange(-360.0, 360.0); self.rx_spin.setSingleStep(5.0)
        self.ry_spin = QtWidgets.QDoubleSpinBox(); self.ry_spin.setRange(-360.0, 360.0); self.ry_spin.setSingleStep(5.0)
        self.rz_spin = QtWidgets.QDoubleSpinBox(); self.rz_spin.setRange(-360.0, 360.0); self.rz_spin.setSingleStep(5.0)

        self.lyt_rot.addRow(self.chk_mir_x, self.chk_mir_y)                                     # Riga specchiature
        self.lyt_rot.addRow("Rotazione X (°):", self.rx_spin)                                   # Riga Rotazione X
        self.lyt_rot.addRow("Rotazione Y (°):", self.ry_spin)                                   # Riga Rotazione Y
        self.lyt_rot.addRow("Rotazione Z (°):", self.rz_spin)                                   # Riga Rotazione Z
        self.layout.addWidget(self.grp_rot)                                                     # Aggiunge al layout principale
        self.form.setLayout(self.layout)                                                        # Imposta il layout finale

        self.preview_group = doc.addObject("App::DocumentObjectGroup", "Anteprima_Utensile_TMP")# Crea il gruppo temporaneo di anteprima
        self.preview_group.Label = "ANTEPRIMA UTENSILE (Provvisorio)"                           # Etichetta temporanea

        self.aggiorna_combo_db()                                                                # Popola la tendina con gli utensili salvati su disco

        if self.edit_obj:                                                                       # Se siamo in modalità modifica di un utensile esistente
            self.carica_dati_da_oggetto(self.edit_obj)                                          # Popola tutti i controlli con i valori salvati
        else:                                                                                   # Se stiamo creando un nuovo utensile
            self.proponi_stazione_e_nome_liberi(doc)                                            # Seleziona la prima stazione T libera nel magazzino

        self.tool_type_combo.currentIndexChanged.connect(self.aggiorna_ui_tipo)                 # Collega cambio categoria utensile
        self.shape_combo.currentIndexChanged.connect(self.trigger_update)                       # Collega cambio forma inserto
        self.rad_combo.currentIndexChanged.connect(self.trigger_update)                         # Collega cambio raggio inserto
        self.hand_combo.currentIndexChanged.connect(self.trigger_update)                        # Collega cambio verso
        self.rot_input.valueChanged.connect(self.trigger_update)                                # Collega cambio angolo registrazione
        self.lama_w_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio larghezza lama gola
        self.gola_p_spin.valueChanged.connect(self.trigger_update)                              # Collega cambio profondità gola
        self.ang_fil_combo.currentIndexChanged.connect(self.trigger_update)                     # Collega cambio angolo filetto
        self.w_input.valueChanged.connect(self.trigger_update)                                  # Collega cambio larghezza
        self.h_input.valueChanged.connect(self.trigger_update)                                  # Collega cambio altezza
        self.l_input.valueChanged.connect(self.trigger_update)                                  # Collega cambio lunghezza
        self.rx_spin.valueChanged.connect(self.trigger_update)                                  # Collega cambio rotazione X
        self.ry_spin.valueChanged.connect(self.trigger_update)                                  # Collega cambio rotazione Y
        self.rz_spin.valueChanged.connect(self.trigger_update)                                  # Collega cambio rotazione Z
        self.chk_mir_x.stateChanged.connect(self.trigger_update)                                # Collega cambio specchiatura X
        self.chk_mir_y.stateChanged.connect(self.trigger_update)                                # Collega cambio specchiatura Y
        self.tabs.currentChanged.connect(self.on_tab_changed)                                   # Collega cambio scheda

        self.is_updating = False                                                                # Sblocca gli aggiornamenti live
        self.aggiorna_ui_tipo()                                                                 # Adatta la visibilità dei campi e lancia l'anteprima
        self.aggiorna_stato_controlli()                                                         # Abilita/disabilita i controlli di rotazione

    def popola_combo_stazioni(self, max_pos):                                                   # Popola il menu a tendina delle stazioni T01..Tmax
        curr = self.stat_combo.currentText()                                                    # Memorizza la stazione attualmente selezionata
        self.stat_combo.blockSignals(True)                                                      # Blocca i segnali del combo
        self.stat_combo.clear()                                                                 # Svuota le voci precedenti
        for i in range(1, max_pos + 1):                                                         # Cicla da 1 fino al numero massimo di posizioni
            self.stat_combo.addItem(f"T{i:02d}")                                                # Aggiunge T01..Txx
        if curr:                                                                                # Ripristina selezione precedente se valida
            idx = self.stat_combo.findText(curr)                                                # Cerca indice
            if idx >= 0: self.stat_combo.setCurrentIndex(idx)                                   # Imposta indice
        self.stat_combo.blockSignals(False)                                                     # Riabilita i segnali

    def aggiorna_lista_stazioni(self, val):                                                     # Chiamato quando cambia il numero posizioni torretta
        self.popola_combo_stazioni(val)                                                         # Aggiorna il combo stazioni
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if doc and doc.getObject("Torretta_Macchina"):                                          # Sincronizza con Torretta_Macchina se presente
            turret = doc.getObject("Torretta_Macchina")                                         # Oggetto torretta
            if hasattr(turret, "NumeroPosizioni"): turret.NumeroPosizioni = val                 # Aggiorna NumeroPosizioni

    def nascondi_altri_utensili(self, doc):                                                     # Nasconde gli utensili del magazzino durante l'editing
        if not doc: return                                                                      # Verifica documento
        lib_group = doc.getObject("Libreria_Utensili")                                          # Cerca il gruppo Magazzino Utensili
        if lib_group and hasattr(lib_group, "Group"):                                           # Se esiste
            for tool in lib_group.Group:                                                        # Cicla sugli utensili
                if hasattr(tool, "ViewObject") and tool.ViewObject:                             # Salva e nasconde
                    self.visibilita_precedente[tool.Name] = tool.ViewObject.Visibility          # Salva visibilità
                    tool.ViewObject.Visibility = False                                          # Nasconde per liberare il WCS
        if self.edit_obj and hasattr(self.edit_obj, "ViewObject") and self.edit_obj.ViewObject: # Nasconde anche l'originale in modifica
            self.edit_obj.ViewObject.Visibility = False                                         # Nasconde

    def proponi_stazione_e_nome_liberi(self, doc):                                              # Seleziona la prima stazione libera per nuovi utensili
        if not doc: return                                                                      # Verifica documento
        usate = set()                                                                           # Stazioni occupate
        count = 1                                                                               # Contatore nome
        lib_group = doc.getObject("Libreria_Utensili")                                          # Gruppo magazzino
        if lib_group and hasattr(lib_group, "Group"):                                           # Se esiste
            count = len(lib_group.Group) + 1                                                    # Numero progressivo
            for tool in lib_group.Group:                                                        # Legge stazioni occupate
                if hasattr(tool, "Stazione"): usate.add(str(tool.Stazione))                     # Aggiunge
        self.name_input.setText(f"Utensile {count}")                                            # Propone nome
        for i in range(self.stat_combo.count()):                                                # Cerca prima stazione libera
            st_txt = self.stat_combo.itemText(i)                                                # Testo stazione
            if st_txt not in usate:                                                             # Se libera
                self.stat_combo.setCurrentIndex(i)                                              # Seleziona
                break                                                                           # Esce

    def aggiorna_combo_db(self):                                                                # Ricarica la lista degli utensili nel menu Archivio
        db = load_tools_db()                                                                    # Legge il database JSON
        self.db_combo.clear()                                                                   # Svuota il combo
        nomi = sorted(db.keys())                                                                # Ordina alfabeticamente
        if nomi: self.db_combo.addItems(nomi)                                                   # Aggiunge i nomi
        else: self.db_combo.addItem("(Archivio vuoto)")                                         # Indica archivio vuoto

    def salva_utensile_in_db(self, tool_obj):                                                   # Salva l'utensile corrente (inclusi dati tecnologici) su disco
        db = load_tools_db()                                                                    # Carica il database
        key = tool_obj.ToolName.strip() or tool_obj.Label                                       # Chiave univoca
        safe_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in key)          # Nome sicuro per file .brep
        record = {                                                                              # Dizionario completo dell'utensile
            "ToolName": key,                                                                    # Nome
            "Stazione": str(tool_obj.Stazione),                                                 # Stazione T01..Txx
            "NumeroStazione": int(getattr(tool_obj, "NumeroStazione", 1)),                      # Indice stazione
            "Modalita": str(tool_obj.Modalita),                                                 # Parametrico / Custom
            "TipoLavorazione": str(tool_obj.TipoLavorazione),                                   # Categoria
            "FormaInserto": str(tool_obj.FormaInserto),                                         # Forma inserto ISO
            "RaggioInserto": str(tool_obj.RaggioInserto),                                       # Raggio punta
            "Verso": str(tool_obj.Verso),                                                       # Verso
            "AngoloReg": float(tool_obj.AngoloReg),                                             # Angolo registrazione Kapr
            "LarghezzaLamaGola": float(getattr(tool_obj, "LarghezzaLamaGola", 3.0)),            # Larghezza lama gola
            "ProfonditaMaxGola": float(getattr(tool_obj, "ProfonditaMaxGola", 22.0)),           # Profondità max gola
            "AngoloFiletto": str(getattr(tool_obj, "AngoloFiletto", "60° (Metrico ISO)")),      # Angolo filetto
            "Larghezza": float(tool_obj.Larghezza),                                             # Larghezza/Diametro
            "Altezza": float(tool_obj.Altezza),                                                 # Altezza
            "Lunghezza": float(tool_obj.Lunghezza),                                             # Lunghezza
            "ModoVelocita": str(getattr(tool_obj, "ModoVelocita", "G96 - Vel. Taglio Costante (m/min)")), # G96/G97
            "VelocitaTaglio": float(getattr(tool_obj, "VelocitaTaglio", 180.0)),                # Vc / RPM
            "AvanzamentoSgrosso": float(getattr(tool_obj, "AvanzamentoSgrosso", 0.25)),         # f sgrosso
            "AvanzamentoFinitura": float(getattr(tool_obj, "AvanzamentoFinitura", 0.10)),       # f finitura
            "ProfonditaPassataMax": float(getattr(tool_obj, "ProfonditaPassataMax", 2.0)),      # Ap max
            "QuadrantePuntaISO": str(getattr(tool_obj, "QuadrantePuntaISO", "Q3 - Esterno Destro Standard")), # Quadrante ISO
            "SpecchiaX": bool(tool_obj.SpecchiaX),                                              # Specchia X
            "SpecchiaY": bool(tool_obj.SpecchiaY),                                              # Specchia Y
            "RotX": float(tool_obj.RotX),                                                       # Rotazione X
            "RotY": float(tool_obj.RotY),                                                       # Rotazione Y
            "RotZ": float(tool_obj.RotZ),                                                       # Rotazione Z
            "InsertTagged": bool(getattr(tool_obj, "InsertTagged", False)),                     # Inserto taggato
            "VertexDefined": bool(getattr(tool_obj, "VertexDefined", False)),                   # Punta definita
            "CustomSolidColors": list(getattr(tool_obj, "CustomSolidColors", [])),              # Colori custom
            "BrepFile": ""                                                                      # File .brep custom
        }                                                                                       # Fine record
        if tool_obj.Modalita == "Custom" and hasattr(tool_obj, "CustomBaseShape") and not tool_obj.CustomBaseShape.isNull():
            brep_filename = f"{safe_name}.brep"                                                 # Nome file .brep
            brep_path = os.path.join(get_library_dir(), brep_filename)                          # Percorso completo
            try:                                                                                # Salva la geometria .brep
                tool_obj.CustomBaseShape.exportBrep(brep_path)                                  # Esporta .brep
                record["BrepFile"] = brep_filename                                              # Registra nel JSON
            except Exception as e:                                                              # Gestione errori
                FreeCAD.Console.PrintError(f"Errore salvataggio BREP custom: {e}\n")            # Stampa errore
        db[key] = record                                                                        # Aggiorna il dizionario
        save_tools_db(db)                                                                       # Salva su disco

    def carica_utensile_da_db(self):                                                            # Carica nel pannello i dati dell'utensile scelto dall'archivio
        db = load_tools_db()                                                                    # Legge il database
        key = self.db_combo.currentText()                                                       # Chiave selezionata
        if key not in db: return                                                                # Verifica esistenza
        data = db[key]                                                                          # Dati utensile
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        self.is_updating = True                                                                 # Sospende i segnali UI
        try:                                                                                    # Popola tutti i campi
            self.name_input.setText(data.get("ToolName", key))                                  # Nome
            st_num = int(data.get("NumeroStazione", 1))                                         # Numero stazione
            if st_num > self.max_stat_spin.value(): self.max_stat_spin.setValue(st_num)         # Adegua limite stazioni
            self.stat_combo.setCurrentText(data.get("Stazione", f"T{st_num:02d}"))              # Stazione
            if data.get("TipoLavorazione") in CATEGORIE_UTENSILI:                               # Categoria
                self.tool_type_combo.setCurrentText(data["TipoLavorazione"])                    # Imposta categoria
            if data.get("FormaInserto") in FORME_INSERTO_ISO:                                   # Forma inserto
                self.shape_combo.setCurrentText(data["FormaInserto"])                           # Imposta forma
            self.rad_combo.setCurrentText(str(data.get("RaggioInserto", "0.4")))                # Raggio
            self.hand_combo.setCurrentText(data.get("Verso", "Destro (R)"))                     # Verso
            self.rot_input.setValue(float(data.get("AngoloReg", 93.0)))                         # Angolo Kapr
            self.lama_w_spin.setValue(float(data.get("LarghezzaLamaGola", 3.0)))                # Larghezza lama
            self.gola_p_spin.setValue(float(data.get("ProfonditaMaxGola", 22.0)))               # Profondità gola
            self.ang_fil_combo.setCurrentText(data.get("AngoloFiletto", "60° (Metrico ISO)"))   # Angolo filetto
            self.w_input.setValue(float(data.get("Larghezza", 12.0)))                           # Larghezza
            self.h_input.setValue(float(data.get("Altezza", 12.0)))                             # Altezza
            self.l_input.setValue(float(data.get("Lunghezza", 100.0)))                          # Lunghezza
            self.speed_mode_combo.setCurrentText(data.get("ModoVelocita", "G96 - Vel. Taglio Costante (m/min)")) # G96/G97
            self.vc_spin.setValue(float(data.get("VelocitaTaglio", 180.0)))                     # Vc / RPM
            self.f_rough_spin.setValue(float(data.get("AvanzamentoSgrosso", 0.25)))             # f sgrosso
            self.f_fin_spin.setValue(float(data.get("AvanzamentoFinitura", 0.10)))              # f finitura
            self.ap_max_spin.setValue(float(data.get("ProfonditaPassataMax", 2.0)))             # Ap max
            if data.get("QuadrantePuntaISO") in QUADRANTI_ISO:                                  # Quadrante ISO
                self.quad_iso_combo.setCurrentText(data["QuadrantePuntaISO"])                   # Imposta quadrante
            self.chk_mir_x.setChecked(bool(data.get("SpecchiaX", False)))                       # Specchia X
            self.chk_mir_y.setChecked(bool(data.get("SpecchiaY", False)))                       # Specchia Y
            self.rx_spin.setValue(float(data.get("RotX", 0.0)))                                 # RotX
            self.ry_spin.setValue(float(data.get("RotY", 0.0)))                                 # RotY
            self.rz_spin.setValue(float(data.get("RotZ", 0.0)))                                 # RotZ

            for old_item in self.oggetti_importati_dati:                                        # Pulisce eventuali oggetti custom precedenti
                if old_item[0] and doc.getObject(old_item[0].Name): doc.removeObject(old_item[0].Name)
            self.oggetti_importati_dati.clear()                                                 # Svuota lista custom

            if data.get("Modalita") == "Custom" and data.get("BrepFile"):                       # Se è un utensile Custom STEP
                brep_path = os.path.join(get_library_dir(), data["BrepFile"])                   # Percorso .brep
                if os.path.exists(brep_path):                                                   # Se esiste su disco
                    comp = Part.Shape(); comp.importBrep(brep_path)                             # Carica la geometria
                    subshapes = list(comp.SubShapes) if hasattr(comp, "SubShapes") and comp.SubShapes else list(comp.Solids)
                    saved_cols = data.get("CustomSolidColors", [])                              # Colori salvati
                    for idx, s in enumerate(subshapes):                                         # Ricrea l'anteprima custom
                        col = (0.5, 0.5, 0.5)                                                   # Grigio base
                        if idx < len(saved_cols):                                               # Legge colore
                            try:
                                parts = [float(x) for x in saved_cols[idx].split(",")]
                                if len(parts) >= 3: col = (parts[0], parts[1], parts[2])
                            except Exception: pass
                        new_obj = doc.addObject("Part::Feature", f"TMP_Custom_Solid_{idx}")     # Solido anteprima
                        new_obj.Shape = s.copy(); new_obj.ViewObject.ShapeColor = col           # Assegna forma e colore
                        self.preview_group.addObject(new_obj)                                   # Aggiunge al gruppo
                        self.oggetti_importati_dati.append([new_obj, s.copy(), col])            # Salva in lista
                    self.insert_tagged = True; self.vertex_defined = True                       # Imposta flags
                    self.tabs.setCurrentIndex(1)                                                # Passa a scheda Custom
                    self.lbl_status.setText(f"Stato: '{key}' caricato dall'Archivio!")          # Messaggio
            else:                                                                               # Se Parametrico
                self.tabs.setCurrentIndex(0)                                                    # Passa a scheda Geometria
        finally:                                                                                # Sblocca i segnali
            self.is_updating = False                                                            # Riabilita
        self.aggiorna_ui_tipo()                                                                 # Aggiorna visibilità campi e anteprima
        self.aggiorna_stato_controlli()                                                         # Aggiorna controlli rotazione

    def importa_tutto_il_magazzino(self):                                                       # Importa tutti gli utensili dall'archivio nel documento
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc: return                                                                      # Verifica documento
        db = load_tools_db()                                                                    # Carica database
        if not db: return                                                                       # Se vuoto esce
        lib_group = doc.getObject("Libreria_Utensili")                                          # Cerca gruppo Magazzino Utensili
        if not lib_group:                                                                       # Se non esiste lo crea
            lib_group = doc.addObject("App::DocumentObjectGroup", "Libreria_Utensili")
            lib_group.Label = "Magazzino Utensili"

        esistenti = { getattr(o, "ToolName", o.Label): o for o in lib_group.Group }             # Mappa utensili già presenti
        for key, data in db.items():                                                            # Cicla su ogni utensile del DB
            if key in esistenti:                                                                # Riutilizza se già presente
                tool_obj = esistenti[key]
            else:                                                                               # Crea nuovo oggetto
                nome_int = key.replace(" ", "_")
                tool_obj = doc.addObject("Part::FeaturePython", nome_int)
                LatheToolObject(tool_obj)
                ViewProviderLatheTool(tool_obj.ViewObject)
                lib_group.addObject(tool_obj)

            tool_obj.Proxy._is_executing = True                                                 # Sospende ricalcolo
            try:                                                                                # Assegna tutti gli attributi
                tool_obj.Proxy.ensure_properties(tool_obj)
                tool_obj.ToolName = data.get("ToolName", key)
                tool_obj.Label = data.get("ToolName", key)
                tool_obj.Stazione = data.get("Stazione", "T01")
                tool_obj.NumeroStazione = int(data.get("NumeroStazione", 1))
                tool_obj.Modalita = data.get("Modalita", "Parametrico")
                if data.get("TipoLavorazione") in CATEGORIE_UTENSILI: tool_obj.TipoLavorazione = data["TipoLavorazione"]
                if data.get("FormaInserto") in FORME_INSERTO_ISO: tool_obj.FormaInserto = data["FormaInserto"]
                tool_obj.RaggioInserto = str(data.get("RaggioInserto", "0.4"))
                tool_obj.Verso = data.get("Verso", "Destro (R)")
                tool_obj.AngoloReg = float(data.get("AngoloReg", 93.0))
                tool_obj.LarghezzaLamaGola = float(data.get("LarghezzaLamaGola", 3.0))
                tool_obj.ProfonditaMaxGola = float(data.get("ProfonditaMaxGola", 22.0))
                tool_obj.AngoloFiletto = data.get("AngoloFiletto", "60° (Metrico ISO)")
                tool_obj.Larghezza = float(data.get("Larghezza", 12.0))
                tool_obj.Altezza = float(data.get("Altezza", 12.0))
                tool_obj.Lunghezza = float(data.get("Lunghezza", 100.0))
                tool_obj.ModoVelocita = data.get("ModoVelocita", "G96 - Vel. Taglio Costante (m/min)")
                tool_obj.VelocitaTaglio = float(data.get("VelocitaTaglio", 180.0))
                tool_obj.AvanzamentoSgrosso = float(data.get("AvanzamentoSgrosso", 0.25))
                tool_obj.AvanzamentoFinitura = float(data.get("AvanzamentoFinitura", 0.10))
                tool_obj.ProfonditaPassataMax = float(data.get("ProfonditaPassataMax", 2.0))
                if data.get("QuadrantePuntaISO") in QUADRANTI_ISO: tool_obj.QuadrantePuntaISO = data["QuadrantePuntaISO"]
                tool_obj.SpecchiaX = bool(data.get("SpecchiaX", False))
                tool_obj.SpecchiaY = bool(data.get("SpecchiaY", False))
                tool_obj.RotX = float(data.get("RotX", 0.0))
                tool_obj.RotY = float(data.get("RotY", 0.0))
                tool_obj.RotZ = float(data.get("RotZ", 0.0))
                tool_obj.InsertTagged = bool(data.get("InsertTagged", False))
                tool_obj.VertexDefined = bool(data.get("VertexDefined", False))
                tool_obj.CustomSolidColors = list(data.get("CustomSolidColors", []))
                if tool_obj.Modalita == "Custom" and data.get("BrepFile"):
                    brep_path = os.path.join(get_library_dir(), data["BrepFile"])
                    if os.path.exists(brep_path):
                        comp = Part.Shape(); comp.importBrep(brep_path)
                        tool_obj.CustomBaseShape = comp
            finally:                                                                            # Sblocca Proxy
                tool_obj.Proxy._is_executing = False
            tool_obj.Proxy.execute(tool_obj)                                                    # Costruisce la forma 3D
            if hasattr(tool_obj, "ViewObject") and tool_obj.ViewObject:
                tool_obj.ViewObject.Visibility = False                                          # Nasconde inizialmente per ordine visivo
        doc.recompute()                                                                         # Ricalcola documento

    def elimina_utensile_da_db(self):                                                           # Rimuove l'utensile selezionato dall'archivio su disco
        db = load_tools_db()                                                                    # Carica database
        key = self.db_combo.currentText()                                                       # Chiave selezionata
        if key in db:                                                                           # Se presente
            brep_file = db[key].get("BrepFile", "")                                             # Eventuale file .brep
            if brep_file:                                                                       # Rimuove anche il file .brep
                brep_path = os.path.join(get_library_dir(), brep_file)
                if os.path.exists(brep_path):
                    try: os.remove(brep_path)
                    except Exception: pass
            del db[key]                                                                         # Elimina dal dizionario
            save_tools_db(db)                                                                   # Salva JSON
            self.aggiorna_combo_db()                                                            # Aggiorna tendina

    def carica_dati_da_oggetto(self, obj):                                                      # Popola la UI quando si riapre un utensile con doppio click
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        obj.Proxy.ensure_properties(obj)                                                        # Verifica tutte le proprietà
        self.name_input.setText(str(getattr(obj, "ToolName", obj.Label)))                       # Nome
        if hasattr(obj, "NumeroStazione") and obj.NumeroStazione > self.max_stat_spin.value():
            self.max_stat_spin.setValue(int(obj.NumeroStazione))                                # Adegua numero posizioni
        self.stat_combo.setCurrentText(str(getattr(obj, "Stazione", "T01")))                    # Stazione
        self.tool_type_combo.setCurrentText(str(getattr(obj, "TipoLavorazione", "Esterno (ISO)"))) # Categoria
        self.shape_combo.setCurrentText(str(getattr(obj, "FormaInserto", "Rombico 80° (C)")))   # Forma inserto
        self.rad_combo.setCurrentText(str(getattr(obj, "RaggioInserto", "0.4")))                # Raggio
        self.hand_combo.setCurrentText(str(getattr(obj, "Verso", "Destro (R)")))                # Verso
        self.rot_input.setValue(float(getattr(obj, "AngoloReg", 93.0)))                         # Angolo Kapr
        self.lama_w_spin.setValue(float(getattr(obj, "LarghezzaLamaGola", 3.0)))                # Larghezza lama
        self.gola_p_spin.setValue(float(getattr(obj, "ProfonditaMaxGola", 22.0)))               # Profondità gola
        self.ang_fil_combo.setCurrentText(str(getattr(obj, "AngoloFiletto", "60° (Metrico ISO)"))) # Angolo filetto
        self.w_input.setValue(float(getattr(obj, "Larghezza", 12.0)))                           # Larghezza
        self.h_input.setValue(float(getattr(obj, "Altezza", 12.0)))                             # Altezza
        self.l_input.setValue(float(getattr(obj, "Lunghezza", 100.0)))                          # Lunghezza
        self.speed_mode_combo.setCurrentText(str(getattr(obj, "ModoVelocita", "G96 - Vel. Taglio Costante (m/min)")))
        self.vc_spin.setValue(float(getattr(obj, "VelocitaTaglio", 180.0)))                     # Vc / RPM
        self.f_rough_spin.setValue(float(getattr(obj, "AvanzamentoSgrosso", 0.25)))             # f sgrosso
        self.f_fin_spin.setValue(float(getattr(obj, "AvanzamentoFinitura", 0.10)))              # f finitura
        self.ap_max_spin.setValue(float(getattr(obj, "ProfonditaPassataMax", 2.0)))             # Ap max
        self.quad_iso_combo.setCurrentText(str(getattr(obj, "QuadrantePuntaISO", "Q3 - Esterno Destro Standard")))
        self.chk_mir_x.setChecked(bool(getattr(obj, "SpecchiaX", False)))                       # Specchia X
        self.chk_mir_y.setChecked(bool(getattr(obj, "SpecchiaY", False)))                       # Specchia Y
        self.rx_spin.setValue(float(getattr(obj, "RotX", 0.0)))                                 # RotX
        self.ry_spin.setValue(float(getattr(obj, "RotY", 0.0)))                                 # RotY
        self.rz_spin.setValue(float(getattr(obj, "RotZ", 0.0)))                                 # RotZ

        if getattr(obj, "Modalita", "Parametrico") == "Custom":                                 # Se l'utensile è Custom STEP
            self.tabs.setCurrentIndex(1)                                                        # Passa a scheda Custom
            self.insert_tagged = bool(getattr(obj, "InsertTagged", True))
            self.vertex_defined = bool(getattr(obj, "VertexDefined", True))
            base_comp = getattr(obj, "CustomBaseShape", None)
            saved_cols = list(getattr(obj, "CustomSolidColors", []))
            if base_comp and not base_comp.isNull():
                subshapes = list(base_comp.SubShapes) if hasattr(base_comp, "SubShapes") and base_comp.SubShapes else list(base_comp.Solids)
                for idx, s in enumerate(subshapes):
                    col = (0.5, 0.5, 0.5)
                    if idx < len(saved_cols):
                        try:
                            parts = [float(x) for x in saved_cols[idx].split(",")]
                            if len(parts) >= 3: col = (parts[0], parts[1], parts[2])
                        except Exception: pass
                    new_obj = doc.addObject("Part::Feature", f"TMP_Custom_Solid_{idx}")
                    new_obj.Shape = s.copy(); new_obj.ViewObject.ShapeColor = col
                    self.preview_group.addObject(new_obj)
                    self.oggetti_importati_dati.append([new_obj, s.copy(), col])
            self.lbl_status.setText("Stato: Utensile Custom caricato. Modifica o premi OK.")
        else:                                                                                   # Se è Parametrico
            self.tabs.setCurrentIndex(0)                                                        # Scheda Geometria

    def pulisci_anteprima_residua(self, doc):                                                   # Rimuove in modo sicuro ogni oggetto temporaneo
        if not doc: return                                                                      # Verifica documento
        if hasattr(self, "preview_group") and self.preview_group:                               # Rimuove figli e gruppo
            try:
                for ch in list(self.preview_group.Group):
                    if doc.getObject(ch.Name): doc.removeObject(ch.Name)
            except Exception: pass
            try:
                if doc.getObject(self.preview_group.Name): doc.removeObject(self.preview_group.Name)
            except Exception: pass
            self.preview_group = None
        for obj in list(doc.Objects):                                                           # Pulisce eventuali residui orfani
            nm = obj.Name; lb = getattr(obj, "Label", "")
            if nm.startswith("TMP_Anteprima_") or nm.startswith("TMP_Custom_Solid_") or nm.startswith("Anteprima_Utensile_TMP") or "ANTEPRIMA UTENSILE" in lb.upper():
                try:
                    if hasattr(obj, "Group"):
                        for ch in list(obj.Group):
                            if doc.getObject(ch.Name): doc.removeObject(ch.Name)
                    if doc.getObject(nm): doc.removeObject(nm)
                except Exception: pass

    def aggiorna_ui_tipo(self):                                                                 # Mostra/nasconde i controlli specifici per ogni categoria
        tipo = self.tool_type_combo.currentText()                                               # Categoria selezionata
        is_iso = tipo in ["Esterno (ISO)", "Bareno (Interno)"]                                  # Utensili a inserto ISO standard
        is_gola = (tipo == "Gola / Troncatura")                                                 # Utensile per gola e troncatura
        is_fil = (tipo == "Filettatura")                                                        # Utensile per filettatura
        is_assiale = tipo in ["Punta da Trapano", "Fresa", "Maschio"]                           # Utensili assiali rotondi

        self.grp_geo.setVisible(not is_assiale)                                                 # Nasconde il box inserto solo per punte/frese/maschi
        self.lbl_shape.setVisible(is_iso); self.shape_combo.setVisible(is_iso)                  # Forma ISO visibile per Esterno/Bareno
        self.lbl_rad.setVisible(is_iso or is_gola); self.rad_combo.setVisible(is_iso or is_gola)# Raggio punta visibile per ISO e Gola
        self.lbl_hand.setVisible(is_iso or is_gola or is_fil); self.hand_combo.setVisible(is_iso or is_gola or is_fil)
        self.lbl_rot.setVisible(is_iso); self.rot_input.setVisible(is_iso)                      # Angolo Kapr visibile per ISO
        self.lbl_lama_w.setVisible(is_gola); self.lama_w_spin.setVisible(is_gola)               # Larghezza lama solo per Gola/Troncatura
        self.lbl_gola_p.setVisible(is_gola); self.gola_p_spin.setVisible(is_gola)               # Profondità gola solo per Gola/Troncatura
        self.lbl_ang_fil.setVisible(is_fil); self.ang_fil_combo.setVisible(is_fil)              # Angolo filetto solo per Filettatura

        ha_stelo_quadro = tipo in ["Esterno (ISO)", "Gola / Troncatura", "Filettatura"]         # Utensili con stelo prismatico W x H
        self.lbl_h.setVisible(ha_stelo_quadro); self.h_input.setVisible(ha_stelo_quadro)        # Altezza H visibile solo per steli quadri
        if ha_stelo_quadro:                                                                     # Etichette per stelo quadro
            self.lbl_w.setText("Larghezza Stelo (mm):")
            self.lbl_h.setText("Altezza Stelo (mm):")
        elif tipo == "Bareno (Interno)":                                                        # Etichetta per bareno tondo
            self.lbl_w.setText("Diametro Bareno (mm):")
        else:                                                                                   # Etichetta per punta, fresa, maschio
            self.lbl_w.setText("Diametro Utensile (mm):")

        if not self.is_updating:                                                                # Suggerisce automaticamente il Quadrante ISO tipico
            if tipo == "Esterno (ISO)": self.quad_iso_combo.setCurrentText("Q3 - Esterno Destro Standard")
            elif tipo == "Bareno (Interno)": self.quad_iso_combo.setCurrentText("Q2 - Bareno Interno Destro")
            elif tipo == "Gola / Troncatura": self.quad_iso_combo.setCurrentText("Q6 - Troncatura / Gola Fronte")
            elif tipo == "Filettatura": self.quad_iso_combo.setCurrentText("Q8 - Filettatura / Neutro X-")
            else: self.quad_iso_combo.setCurrentText("Q7 - Punta / Centro Assiale")

        self.trigger_update()                                                                   # Ridisegna l'anteprima 3D

    def on_tab_changed(self, index):                                                            # Gestisce il cambio scheda
        self.aggiorna_stato_controlli()                                                         # Aggiorna abilitazione rotazioni
        if index in [0, 1]:                                                                     # Se si passa tra Geometria e Custom 3D
            self.trigger_update()                                                               # Aggiorna l'anteprima 3D

    def aggiorna_stato_controlli(self):                                                         # Abilita i controlli di orientamento quando opportuno
        if self.tabs.currentIndex() == 1:                                                       # Nella scheda Custom 3D
            self.grp_rot.setEnabled(self.vertex_defined)                                        # Abilitato dopo aver azzerato la punta
        else:                                                                                   # Nelle schede Geometria e Tecnologia
            self.grp_rot.setEnabled(True)                                                       # Sempre abilitato

    def trigger_update(self, *args):                                                            # Innesca il ricalcolo dell'anteprima live
        if not self.is_updating:                                                                # Controlla che non ci siano blocchi attivi
            self.is_updating = True                                                             # Attiva il semaforo
            try:                                                                                # Esegue il ridisegno
                self.aggiorna_anteprima_live()                                                  # Aggiorna il 3D
            finally:                                                                            # Sblocca sempre in uscita
                self.is_updating = False                                                        # Disattiva il semaforo

    def calcola_rotazione_indipendente(self):                                                   # Compone la rotazione manuale X, Y, Z
        rot_x = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), self.rx_spin.value())                 # Rotazione X
        rot_y = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), self.ry_spin.value())                 # Rotazione Y
        rot_z = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), self.rz_spin.value())                 # Rotazione Z
        return rot_x * rot_y * rot_z                                                            # Rotazione combinata

    def aggiorna_anteprima_live(self):                                                          # Disegna l'anteprima live ancorata al WCS
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if doc is None or not self.preview_group: return                                        # Verifica validità

        rot_manuale = self.calcola_rotazione_indipendente()                                     # Rotazione impostata negli spinbox
        wcs_origin = get_wcs_origin(doc)                                                        # Origine WCS

        for name in ["TMP_Anteprima_Inserto", "TMP_Anteprima_Gambo"]:                           # Rimuove le vecchie forme di anteprima
            obj = doc.getObject(name)
            if obj: doc.removeObject(name)

        if self.tabs.currentIndex() != 1:                                                       # Se siamo in modalità Parametrica (Scheda 0 o 2)
            for item in self.oggetti_importati_dati:                                            # Nasconde eventuali solidi custom
                if item[0] and hasattr(item[0], "ViewObject") and item[0].ViewObject:
                    item[0].ViewObject.Visibility = False

            w = self.w_input.value()                                                            # Larghezza/Diametro
            h = self.h_input.value() if self.h_input.isVisible() else w                         # Altezza stelo
            l = self.l_input.value()                                                            # Lunghezza totale
            tipo = self.tool_type_combo.currentText()                                           # Categoria scelta

            gambo_finito, insert_shape = genera_forme_parametriche(                             # Genera i solidi realistici
                tipo, self.shape_combo.currentText(), self.hand_combo.currentText(),
                self.rot_input.value(), w, h, l,
                self.lama_w_spin.value(), self.gola_p_spin.value(), self.ang_fil_combo.currentText(),
                self.chk_mir_x.isChecked(), self.chk_mir_y.isChecked(),
                rot_manuale, wcs_origin
            )                                                                                   # Fine generazione

            if insert_shape:                                                                    # Crea l'oggetto anteprima per l'inserto dorato
                insert_obj = doc.addObject("Part::Feature", "TMP_Anteprima_Inserto")
                insert_obj.Label = "Anteprima Inserto"
                insert_obj.Shape = insert_shape
                insert_obj.ViewObject.ShapeColor = (0.92, 0.72, 0.12)                           # Giallo Oro TiN
                self.preview_group.addObject(insert_obj)

            if gambo_finito:                                                                    # Crea l'oggetto anteprima per il gambo
                gambo_obj = doc.addObject("Part::Feature", "TMP_Anteprima_Gambo")
                gambo_obj.Label = "Anteprima Gambo"
                gambo_obj.Shape = gambo_finito
                if tipo in ["Punta da Trapano", "Fresa", "Maschio"]:                            # Utensili assiali
                    gambo_obj.ViewObject.ShapeColor = (0.72, 0.74, 0.77)                        # Grigio acciaio rettificato
                else:                                                                           # Portainserti da tornitura
                    gambo_obj.ViewObject.ShapeColor = (0.28, 0.30, 0.33)                        # Grigio scuro brunito
                self.preview_group.addObject(gambo_obj)
        else:                                                                                   # Se siamo nella Scheda 2 (Custom 3D)
            for item in self.oggetti_importati_dati:                                            # Aggiorna i solidi custom importati
                obj, forma_orig, col = item
                if obj and forma_orig is not None:
                    obj.ViewObject.Visibility = True
                    nuova_forma = forma_orig.copy()
                    if self.chk_mir_x.isChecked(): nuova_forma = nuova_forma.mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0))
                    if self.chk_mir_y.isChecked(): nuova_forma = nuova_forma.mirror(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0))
                    nuova_forma.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), rot_manuale) * nuova_forma.Placement
                    nuova_forma.translate(wcs_origin)
                    obj.Shape = nuova_forma
                    obj.ViewObject.ShapeColor = col

        doc.recompute()                                                                         # Aggiorna la scena 3D

    def importa_file(self):                                                                     # Passo 1 Custom: Importa file STEP/IGES/FCStd
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if not doc: return                                                                      # Controllo sicurezza
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Seleziona File Utensile", "", "File 3D (*.step *.stp *.iges *.igs *.FCStd)")
        if not file_path: return                                                                # Se annullato esce
        try:                                                                                    # Blocco di importazione
            self.insert_tagged = False; self.vertex_defined = False                             # Resetta i flag
            self.aggiorna_stato_controlli()                                                     # Blocca rotazioni finché non si definisce la punta
            self.is_updating = True                                                             # Azzera rotazioni
            self.rx_spin.setValue(0.0); self.ry_spin.setValue(0.0); self.rz_spin.setValue(0.0)
            self.chk_mir_x.setChecked(False); self.chk_mir_y.setChecked(False)
            self.is_updating = False

            oggetti_prima = set(doc.Objects)                                                    # Oggetti prima dell'import
            ImportGui.insert(file_path, doc.Name)                                               # Importa il file
            oggetti_dopo = set(doc.Objects)                                                     # Oggetti dopo l'import
            nuovi_oggetti = list(oggetti_dopo - oggetti_prima)                                  # Oggetti appena creati

            forme_estratte = []                                                                 # Raccoglie (forma, colore)
            for obj in nuovi_oggetti:
                try:
                    if hasattr(obj, "Shape") and obj.Shape and hasattr(obj.Shape, "Volume") and obj.Shape.Volume > 0:
                        if not hasattr(obj, "OutList") or len(obj.OutList) == 0:
                            forma = obj.Shape.copy()
                            if hasattr(obj, "getGlobalPlacement"): forma.Placement = obj.getGlobalPlacement()
                            elif hasattr(obj, "Placement"): forma.Placement = obj.Placement
                            colore = obj.ViewObject.ShapeColor[:3] if hasattr(obj, "ViewObject") and hasattr(obj.ViewObject, "ShapeColor") else (0.5, 0.5, 0.5)
                            forme_estratte.append((forma, colore))
                except Exception: pass

            for obj in nuovi_oggetti:                                                           # Rimuove la gerarchia sporca importata
                try:
                    if doc.getObject(obj.Name): doc.removeObject(obj.Name)
                except Exception: pass

            for old_item in self.oggetti_importati_dati:                                        # Pulisce eventuali solidi custom precedenti
                try:
                    if old_item[0] and doc.getObject(old_item[0].Name): doc.removeObject(old_item[0].Name)
                except Exception: pass
            self.oggetti_importati_dati.clear()

            for idx, (forma, colore) in enumerate(forme_estratte):                              # Crea i solidi puliti nell'anteprima
                new_obj = doc.addObject("Part::Feature", f"TMP_Custom_Solid_{idx}")
                new_obj.Shape = forma.copy(); new_obj.ViewObject.ShapeColor = colore
                self.preview_group.addObject(new_obj)
                self.oggetti_importati_dati.append([new_obj, forma.copy(), colore])

            self.lbl_status.setText("Stato: STEP Bonificato. 2. Tagga l'inserto (metallo).")
            self.trigger_update()
        except Exception as e:
            FreeCAD.Console.PrintError(f"Errore importazione: {e}\n")

    def tagga_inserto(self):                                                                    # Passo 2 Custom: Identifica e colora l'inserto in oro
        sel = FreeCADGui.Selection.getSelection()                                               # Selezione 3D
        if not sel:
            self.lbl_status.setText("Errore: Seleziona l'inserto nel 3D!")
            return
        custom_insert = sel[0]
        trovato = False
        for item in self.oggetti_importati_dati:
            if item[0] and item[0].Name == custom_insert.Name:
                item[2] = (0.92, 0.72, 0.12)                                                    # Registra il colore oro
                custom_insert.ViewObject.ShapeColor = (0.92, 0.72, 0.12)                        # Colora in oro nella vista
                trovato = True
        if not trovato:
            custom_insert.ViewObject.ShapeColor = (0.92, 0.72, 0.12)
        self.insert_tagged = True
        self.lbl_status.setText(f"Stato: Inserto [{custom_insert.Label}] taggato. Ora 3. Definisci Punta.")

    def definisci_punta(self):                                                                  # Passo 3 Custom: Azzera il vertice di punta sul WCS
        if not self.insert_tagged:
            self.lbl_status.setText("Errore: Devi prima taggare l'inserto!")
            return
        sel_ex = FreeCADGui.Selection.getSelectionEx()
        if not sel_ex or not sel_ex[0].SubElementNames:
            self.lbl_status.setText("Errore: Seleziona un vertice!")
            return
        sub_name = sel_ex[0].SubElementNames[0]
        if not sub_name.startswith("Vertex"):
            self.lbl_status.setText("Errore: Seleziona un VERTICE.")
            return

        obj = sel_ex[0].Object
        vertex = obj.Shape.getElement(sub_name)
        punta_pt = vertex.Point

        wcs_origin = get_wcs_origin(FreeCAD.ActiveDocument)
        rot_man = self.calcola_rotazione_indipendente()
        p_rel = punta_pt - wcs_origin
        p_local = rot_man.inverted().multVec(p_rel)
        if self.chk_mir_y.isChecked(): p_local.y = -p_local.y
        if self.chk_mir_x.isChecked(): p_local.x = -p_local.x

        for idx, item in enumerate(self.oggetti_importati_dati):
            obj_rif, forma_orig, col = item
            forma_spostata = forma_orig.copy()
            forma_spostata.translate(-p_local)
            self.oggetti_importati_dati[idx] = [obj_rif, forma_spostata, col]

        FreeCADGui.Selection.clearSelection()
        self.vertex_defined = True
        self.aggiorna_stato_controlli()
        self.lbl_status.setText("Stato: Punta azzerata sul WCS! Usa Rotazione e Specchio.")
        self.trigger_update()

    def getStandardButtons(self):                                                               # Pulsanti standard OK e Cancel
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

    def accept(self):                                                                           # Conferma la creazione o modifica dell'utensile
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if doc is None: return False                                                            # Controllo sicurezza

        nome_base = self.name_input.text().strip() or "Utensile"                                # Nome utensile
        nome_int = nome_base.replace(" ", "_")                                                  # Nome interno

        lib_group = doc.getObject("Libreria_Utensili")                                          # Cerca gruppo Magazzino Utensili
        if not lib_group:                                                                       # Se non esiste lo crea
            lib_group = doc.addObject("App::DocumentObjectGroup", "Libreria_Utensili")
            lib_group.Label = "Magazzino Utensili"

        if self.edit_obj and doc.getObject(self.edit_obj.Name):                                 # Se in modifica usa l'esistente
            tool_obj = self.edit_obj
        else:                                                                                   # Altrimenti crea nuovo oggetto parametrico
            tool_obj = doc.addObject("Part::FeaturePython", nome_int)
            LatheToolObject(tool_obj)
            ViewProviderLatheTool(tool_obj.ViewObject)
            lib_group.addObject(tool_obj)

        st_txt = self.stat_combo.currentText()                                                  # Stazione assegnata
        try: num_st = int(st_txt.replace("T", "").strip())                                      # Indice intero stazione
        except Exception: num_st = self.stat_combo.currentIndex() + 1

        tool_obj.Proxy._is_executing = True                                                     # Sospende il ricalcolo
        try:                                                                                    # Salva tutte le proprietà geometriche e tecnologiche
            tool_obj.Proxy.ensure_properties(tool_obj)
            tool_obj.ToolName = nome_base
            tool_obj.Label = nome_base
            tool_obj.Stazione = st_txt
            tool_obj.NumeroStazione = num_st
            tool_obj.TipoLavorazione = self.tool_type_combo.currentText()
            tool_obj.FormaInserto = self.shape_combo.currentText()
            tool_obj.RaggioInserto = self.rad_combo.currentText()
            tool_obj.Verso = self.hand_combo.currentText()
            tool_obj.AngoloReg = self.rot_input.value()
            tool_obj.LarghezzaLamaGola = self.lama_w_spin.value()
            tool_obj.ProfonditaMaxGola = self.gola_p_spin.value()
            tool_obj.AngoloFiletto = self.ang_fil_combo.currentText()
            tool_obj.Larghezza = self.w_input.value()
            tool_obj.Altezza = self.h_input.value()
            tool_obj.Lunghezza = self.l_input.value()
            tool_obj.ModoVelocita = self.speed_mode_combo.currentText()
            tool_obj.VelocitaTaglio = self.vc_spin.value()
            tool_obj.AvanzamentoSgrosso = self.f_rough_spin.value()
            tool_obj.AvanzamentoFinitura = self.f_fin_spin.value()
            tool_obj.ProfonditaPassataMax = self.ap_max_spin.value()
            tool_obj.QuadrantePuntaISO = self.quad_iso_combo.currentText()
            tool_obj.SpecchiaX = self.chk_mir_x.isChecked()
            tool_obj.SpecchiaY = self.chk_mir_y.isChecked()
            tool_obj.RotX = self.rx_spin.value()
            tool_obj.RotY = self.ry_spin.value()
            tool_obj.RotZ = self.rz_spin.value()

            if self.tabs.currentIndex() == 1 or (self.oggetti_importati_dati and self.vertex_defined): # Se Custom
                if self.tabs.currentIndex() == 1:
                    tool_obj.Modalita = "Custom"
                    tool_obj.InsertTagged = self.insert_tagged
                    tool_obj.VertexDefined = self.vertex_defined
                    forme_base = []; colori_str = []
                    for item in self.oggetti_importati_dati:
                        _, forma_orig, col = item
                        if forma_orig is not None:
                            forme_base.append(forma_orig.copy())
                            colori_str.append(f"{col[0]:.4f},{col[1]:.4f},{col[2]:.4f}")
                    if forme_base:
                        tool_obj.CustomBaseShape = Part.makeCompound(forme_base)
                        tool_obj.CustomSolidColors = colori_str
                else:
                    tool_obj.Modalita = "Parametrico"
            else:
                tool_obj.Modalita = "Parametrico"
        finally:                                                                                # Riabilita il Proxy
            tool_obj.Proxy._is_executing = False

        tool_obj.Proxy.execute(tool_obj)                                                        # Costruisce la forma finale e applica i colori
        if hasattr(tool_obj, "ViewObject") and tool_obj.ViewObject:
            tool_obj.ViewObject.Visibility = True                                               # Mostra l'utensile appena confermato

        if self.chk_save_db.isChecked():                                                        # Salva nell'archivio permanente su disco
            self.salva_utensile_in_db(tool_obj)

        self.pulisci_anteprima_residua(doc)                                                     # Elimina l'anteprima temporanea
        doc.recompute()                                                                         # Ricalcola il documento
        if FreeCADGui.ActiveDocument: FreeCADGui.ActiveDocument.resetEdit()                     # Esce da Edit
        FreeCADGui.Control.closeDialog()                                                        # Chiude il TaskPanel
        return True                                                                             # Conferma

    def reject(self):                                                                           # Annulla l'operazione e ripristina lo stato precedente
        doc = FreeCAD.ActiveDocument                                                            # Documento attivo
        if doc:
            self.pulisci_anteprima_residua(doc)                                                 # Rimuove l'anteprima temporanea
            for name, vis in self.visibilita_precedente.items():                                # Ripristina la visibilità precedente degli utensili
                obj = doc.getObject(name)
                if obj and hasattr(obj, "ViewObject") and obj.ViewObject:
                    obj.ViewObject.Visibility = vis
            if self.edit_obj and doc.getObject(self.edit_obj.Name):                             # Riaccende l'eventuale utensile in modifica
                if hasattr(self.edit_obj, "ViewObject") and self.edit_obj.ViewObject:
                    self.edit_obj.ViewObject.Visibility = True
            doc.recompute()
        if FreeCADGui.ActiveDocument: FreeCADGui.ActiveDocument.resetEdit()
        FreeCADGui.Control.closeDialog()
        return True