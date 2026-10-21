# -*- coding: utf-8 -*-                                                                         # Imposta la codifica UTF-8 per i caratteri speciali tedeschi (ä, ö, ü, ß)
import re                                                                                       # Importa il modulo espressioni regolari per la sostituzione di parole intere

LINGUA_CODICE = "de"                                                                            # Identificativo codice lingua Tedesca
LINGUA_NOME = "Deutsch"                                                                         # Nome esteso della lingua

TRADUZIONI = {                                                                                  # Dizionario completo delle frasi esatte Italiano -> Tedesco per tutti i 13 moduli
    # ==========================================================================
    # BARRE DEGLI STRUMENTI E TOOLTIP (13 COMANDI)
    # ==========================================================================
    "1. Setup Macchina (WCS)": "1. Maschineneinrichtung (WCS)",                                 # Comando 1 MenuText
    "Configura il sistema di coordinate macchina (WCS), l'origine Z0 e il punto di cambio utensile.": "Maschinenkoordinatensystem (WCS), Z0-Nullpunkt und Werkzeugwechselpunkt konfigurieren.",
    "2. Grezzo & Autocentrante": "2. Rohteil & Spannfutter",                                    # Comando 2 MenuText
    "Definisce le dimensioni del cilindro/tubo grezzo e le griffe del mandrino autocentrante.": "Rohteilabmessungen (Zylinder/Rohr) und 3-Backen-Spannfutter definieren.",
    "3. Pezzo Finito (Target 3D)": "3. Fertigteil (3D-Modell)",                                 # Comando 3 MenuText
    "Seleziona e posiziona il solido 3D del pezzo finito dentro il grezzo.": "3D-Fertigteil auswählen und im Rohteil ausrichten.",
    "4. Magazzino Utensili": "4. Werkzeugbibliothek",                                           # Comando 4 MenuText
    "Gestisce il magazzino utensili di tornitura, gole, filettatura e foratura.": "Dreh-, Stech-, Gewinde- und Bohrwerkzeuge in der Bibliothek verwalten.",
    "5. Torretta Portautensili 3D": "5. 3D-Werkzeugrevolver",                                   # Comando 5 MenuText
    "Configura il disco torretta 3D e monta gli utensili nelle stazioni.": "3D-Revolverscheibe konfigurieren und Werkzeuge auf Stationen bestücken.",
    "1. Sgrossatura": "1. Schruppen",                                                           # Comando 6 MenuText
    "Ciclo di sgrossatura longitudinale o frontale con riconoscimento automatico del profilo 3D.": "Längs- oder Planschruppzyklus mit automatischer 3D-Profilerkennung.",
    "2. Finitura": "2. Schlichten",                                                             # Comando 7 MenuText
    "Passata continua di finitura sul profilo reale del pezzo finito con compensazione raggio.": "Kontinuierlicher Schlichtschnitt am Fertigteilprofil mit Schneidenradiuskompensation.",
    "3. Gola": "3. Einstechen",                                                                 # Comando 8 MenuText
    "Scavo di gole radiali esterne, interne o frontali con ciclo a tuffi multipli e pulizia fondo.": "Außen-, Innen- oder Planeinstechen mit Mehrfachzustellung und Grundreinigung.",
    "4. Filettatura": "4. Gewindedrehen",                                                       # Comando 9 MenuText
    "Filettatura cilindrica o conica (Metrica ISO, Gas BSP, NPT, Trapezoidale) a sezione costante.": "Zylindrisches oder kegeliges Gewindedrehen (ISO Metrisch, BSP, NPT, Trapez).",
    "5. Foratura Asse": "5. Zentrieren & Bohren",                                               # Comando 10 MenuText
    "Centrinatura, foratura profonda a scarico truciolo (G83/G73) e maschiatura sull'asse Z.": "Anbohren, Tieflochbohren mit Spanbruch (G83/G73) und Gewindebohren auf der Z-Achse.",
    "6. Troncatura": "6. Abstechen",                                                            # Comando 11 MenuText
    "Taglio finale del pezzo finito dalla barra con smusso/raccordo automatico sullo spigolo.": "Abstechen des Fertigteils von der Stange mit automatischer Fase/Verrundung.",
    "1. Simulazione 3D": "1. 3D-Simulation",                                                    # Comando 12 MenuText
    "Simula in 3D il movimento della torretta, l'asportazione sul grezzo e verifica le collisioni.": "Simuliert 3D-Revolverbewegung, Materialabtrag am Rohteil und Kollisionsprüfung.",
    "2. Genera G-Code": "2. G-Code generieren",                                                 # Comando 13 MenuText
    "Genera, visualizza ed esporta il programma G-Code per Fanuc/Haas, Siemens, Mach3 e LinuxCNC.": "G-Code-Programm für Fanuc/Haas, Siemens, Mach3 und LinuxCNC erstellen und exportieren.",

    # ==========================================================================
    # PANNELLO 1: SETUP MACCHINA (WCS) E PANNELLO 2: GREZZO & AUTOCENTRANTE
    # ==========================================================================
    "Configurazione Setup Macchina (WCS)": "Maschineneinrichtung (WCS)",                        # Titolo Setup WCS
    "Sistema di Coordinate Pezzo (WCS)": "Werkstück-Koordinatensystem (WCS)",                   # Gruppo WCS
    "Origine WCS (Z0 Pezzo)": "WCS-Nullpunkt (Werkstück Z0)",                                   # Gruppo Origine Z0
    "Acquisisci Z0 da Faccia/Vertice 3D": "Z0 von 3D-Fläche/Punkt übernehmen",                  # Bottone acquisisci Z0
    "Posizione Cambio Utensile": "Werkzeugwechselpunkt",                                        # Gruppo cambio utensile
    "Punto Cambio Utensile (Home)": "Werkzeugwechselpunkt (Home)",                              # Variante cambio utensile
    "Archivio Grezzi / Mandrini": "Rohteil- / Spannfutter-Archiv",                              # Gruppo archivio grezzi
    "Carica Grezzo": "Rohteil laden",                                                           # Bottone carica grezzo
    "Carica Stock": "Rohteil laden",                                                            # Correzione stringa parziale
    "Elimina": "Löschen",                                                                       # Bottone elimina
    "Delete": "Löschen",                                                                        # Traduce Delete in Tedesco
    "Salva in Archivio Permanente all'OK": "Beim OK dauerhaft im Archiv speichern",             # Checkbox salva in archivio
    "Save in Archivio Permanente all'OK": "Beim OK dauerhaft im Archiv speichern",              # Correzione stringa parziale
    "1. Grezzo": "1. Rohteil",                                                                  # Scheda 1 grezzo
    "1. Stock": "1. Rohteil",                                                                   # Traduce 1. Stock
    "2. Presa & Limiti": "2. Spannung & Grenzen",                                               # Scheda 2 presa e limiti
    "2. Presa _Limiti": "2. Spannung & Grenzen",                                                # Variante con underscore
    "2. Grip _Limits": "2. Spannung & Grenzen",                                                 # Correzione stringa parziale
    "Dimensioni Barra & Sovrametalli": "Stangenmaße & Aufmaße",                                 # Gruppo dimensioni barra
    "Dimensioni Barra _Sovrametalli": "Stangenmaße & Aufmaße",                                  # Variante con underscore
    "Dimensions Bar _Sovrametalli": "Stangenmaße & Aufmaße",                                    # Correzione stringa parziale
    "Rileva Misure dal Pezzo 3D Selezionato": "Maße vom gewählten 3D-Bauteil übernehmen",       # Bottone rileva misure 3D
    "Rileva Misure dal Part 3D Selected": "Maße vom gewählten 3D-Bauteil übernehmen",           # Correzione stringa parziale
    "Tipo Barra:": "Stangentyp:",                                                               # Etichetta tipo barra
    "Type Bar:": "Stangentyp:",                                                                 # Correzione stringa parziale
    "Cilindro Pieno": "Vollzylinder",                                                           # Voce tendina cilindro pieno
    "Tubo Forato": "Hohlrohr",                                                                  # Voce tendina tubo forato
    "Diametro Base (mm):": "Basisdurchmesser (mm):",                                            # Diametro base
    "Diameter Base (mm):": "Basisdurchmesser (mm):",                                            # Correzione stringa parziale
    "Diametro Foro Int. (mm):": "Innenbohrung Ø (mm):",                                         # Diametro foro interno
    "Diameter Bore Int. (mm):": "Innenbohrung Ø (mm):",                                         # Correzione stringa parziale
    "Lunghezza Totale (mm):": "Gesamtlänge (mm):",                                              # Lunghezza totale
    "Total Length (mm):": "Gesamtlänge (mm):",                                                  # Traduce Total Length
    "Sovrametallo Fronte Z+ (mm):": "Planaufmaß Z+ (mm):",                                      # Sovrametallo frontale Z+
    "Allowance Fronte Z+ (mm):": "Planaufmaß Z+ (mm):",                                         # Correzione stringa parziale
    "Sovrametallo Raggio X+ (mm):": "Radialaufmaß X+ (mm):",                                    # Sovrametallo radiale X+
    "Allowance Radius X+ (mm):": "Radialaufmaß X+ (mm):",                                       # Correzione stringa parziale
    "Trasparenza Visiva (%):": "Sichttransparenz (%):",                                         # Trasparenza visiva %
    "Transparency Visiva (%):": "Sichttransparenz (%):",                                        # Correzione stringa parziale

    # ==========================================================================
    # PANNELLO 4 & 5: MAGAZZINO UTENSILI, TORRETTA E LAVORAZIONI CAM
    # ==========================================================================
    "Dati Generali & Stazione Torretta": "Allgemeine Daten & Revolverstation",                  # Gruppo dati generali utensile
    "Dati Generali e Stazione Torretta": "Allgemeine Daten & Revolverstation",                  # Gruppo dati generali utensile
    "Dati Generali _Stazione Torretta": "Allgemeine Daten & Revolverstation",                   # Con underscore
    "Dati Generali _Station Turret": "Allgemeine Daten & Revolverstation",                      # Correzione stringa parziale
    "Nome:": "Name:",                                                                           # Nome
    "Name:": "Name:",                                                                           # Name
    "N° Posizioni Torretta:": "Anzahl Revolverstationen:",                                      # Numero posizioni torretta
    "N° Posizioni Turret:": "Anzahl Revolverstationen:",                                        # Variante numero posizioni
    "Stazione Assegnata:": "Zugewiesene Station:",                                              # Stazione assegnata
    "Station Axisgnata:": "Zugewiesene Station:",                                               # Correzione stringa precedente
    "1. Geometria": "1. Geometrie",                                                             # Tab 1 Utensili
    "1. Geometry": "1. Geometrie",                                                              # Tab 1 Utensili
    "2. Custom 3D": "2. 3D-Modell",                                                             # Tab 2 Utensili
    "3. Tecnologia": "3. Technologie",                                                          # Tab 3 Utensili
    "3. Technology": "3. Technologie",                                                          # Tab 3 Utensili
    "Categoria Lavorazione": "Bearbeitungskategorie",                                           # Gruppo categoria
    "Geometria Inserto / Tagliente": "Schneidplatten-Geometrie",                                # Gruppo geometria inserto
    "Geometry Insert / Edge": "Schneidplatten-Geometrie",                                       # Variante gruppo geometria inserto
    "Forma Inserto:": "Plattenform:",                                                           # Forma inserto
    "Forma Insert:": "Plattenform:",                                                            # Variante forma inserto
    "Radius Tip/Drill (mm):": "Ecken- / Bohrradius (mm):",                                      # Raggio punta
    "Verso Taglio:": "Schnittrichtung:",                                                        # Verso di taglio
    "Verso Cutting:": "Schnittrichtung:",                                                       # Variante verso di taglio
    "Angolo Reg. Kapr (°):": "Einstellwinkel Kapr (°):",                                        # Angolo registrazione Kapr
    "Angle Reg. Kapr (°):": "Einstellwinkel Kapr (°):",                                         # Variante angolo Kapr
    "Dimensioni Corpo / Stelo": "Schaftabmessungen",                                            # Gruppo dimensioni stelo
    "Dimensioni Corpo / Shank": "Schaftabmessungen",                                            # Variante dimensioni stelo
    "Width Shank (mm):": "Schaftbreite (mm):",                                                  # Larghezza stelo
    "Height Shank (mm):": "Schafthöhe (mm):",                                                   # Altezza stelo
    "Length Total (mm):": "Gesamtlänge (mm):",                                                  # Lunghezza totale
    "Orientamento Spaziale 3D (Live)": "3D-Orientierung (Live)",                                # Gruppo orientamento 3D
    "Specchia X": "Spiegeln X",                                                                 # Checkbox Specchia X
    "Specchia Y": "Spiegeln Y",                                                                 # Checkbox Specchia Y
    "Specchia Z": "Spiegeln Z",                                                                 # Checkbox Specchia Z
    "Rotazione X (°):": "Drehung X (°):",                                                       # Rotazione X
    "Rotazione Y (°):": "Drehung Y (°):",                                                       # Rotazione Y
    "Rotazione Z (°):": "Drehung Z (°):",                                                       # Rotazione Z
    "1. Utensile e Modalità": "1. Werkzeug & Zyklusmodus",                                      # Gruppo 1 operazioni
    "2. Limiti Geometrici": "2. Geometriegrenzen",                                              # Gruppo 2 operazioni
    "3. Parametri di Taglio": "3. Schnittparameter",                                            # Gruppo 3 operazioni
    "4. Parametri di Taglio": "4. Schnittparameter",                                            # Gruppo 4 operazioni
    "Parametri Tecnologici": "Schnittparameter",                                                # Parametri tecnologici
    "Ricalcola / Anteprima": "Neu berechnen / Vorschau",                                        # Bottone ricalcola
    "Aggiorna Anteprima 3D": "3D-Vorschau aktualisieren",                                       # Bottone aggiorna
    "1. Controllo & Programma": "1. Steuerung & Programm",                                      # Tab 1 Post-Processor
    "2. Configuratore e-CAM (Template & Codici)": "2. e-CAM Konfigurator (Vorlagen & Codes)"    # Tab 2 Post-Processor
}                                                                                               # Fine dizionario Tedesco

TERMINI_PAROLE_INTERE = [                                                                       # Termini tecnici interi Italiano -> Tedesco
    ("Archivio Permanente", "Dauerarchiv"), ("Archivio Grezzi", "Rohteil-Archiv"),              # Locuzioni Grezzo
    ("Cilindro Pieno", "Vollzylinder"), ("Tubo Forato", "Hohlrohr"),                            # Tipi barra
    ("Rileva Misure", "Maße übernehmen"), ("Ø Esterno Effettivo", "Effektiver Außen-Ø"),        # Misure
    ("con Sovra", "mit Aufmaß"), ("Dati Generali", "Allgemeine Daten"),                         # Dati
    ("Archivio", "Archiv"), ("Permanente", "Dauerhaft"), ("Misure", "Maße"), ("Rileva", "Messen"),
    ("Carica", "Laden"), ("Grezzi", "Rohteile"), ("Grezzo", "Rohteil"), ("Mandrini", "Spannfutter"),
    ("Mandrino", "Spindel"), ("Sovrametalli", "Aufmaße"), ("Sovrametallo", "Aufmaß"), ("Sovra", "Aufmaß"),
    ("Pieno", "Voll"), ("Forato", "Hohl"), ("Effettivo", "Effektiv"), ("Visiva", "Optisch"),    # Aggettivi
    ("Fronte", "Stirn"), ("Frontale", "Plan"), ("Barra", "Stange"),                             # Geometria
    ("Sgrossatura", "Schruppen"), ("Finitura", "Schlichten"), ("Filettatura", "Gewindedrehen"), # Lavorazioni
    ("Foratura", "Bohren"), ("Troncatura", "Abstechen"), ("Gola", "Einstechen"),                # Lavorazioni
    ("Diametro", "Durchmesser"), ("Raggio", "Radius"), ("Lunghezza", "Länge"),                  # Geometria
    ("Larghezza", "Breite"), ("Altezza", "Höhe"), ("Profondità", "Tiefe"), ("Angolo", "Winkel"),
    ("Dimensioni", "Abmessungen"), ("Forma", "Form"), ("Corpo", "Körper"), ("Passo", "Steigung"),
    ("Utensile", "Werkzeug"), ("Utensili", "Werkzeuge"), ("Magazzino", "Bibliothek"),           # Utensili
    ("Torretta", "Revolver"), ("Stazione", "Station"), ("Stazioni", "Stationen"), ("Disco", "Scheibe"),
    ("Posizioni", "Positionen"), ("Posizione", "Position"), ("Assegnata", "Zugewiesen"),        # Stazioni
    ("Attiva", "Aktiv"), ("Attivo", "Aktiv"), ("Stelo", "Schaft"), ("Inserto", "Wendeplatte"),  # Componenti
    ("Punta", "Spitze"), ("Tagliente", "Schneide"), ("Pezzo", "Bauteil"), ("Finito", "Fertig"), # Pezzo
    ("Autocentrante", "Spannfutter"), ("Griffe", "Backen"), ("Presa", "Spannung"), ("Foro", "Bohrung"),
    ("Avanzamento", "Vorschub"), ("Velocità", "Geschw."), ("Taglio", "Schnitt"),                # Parametri
    ("Giri", "Drehzahl"), ("Passata", "Zustellung"), ("Passate", "Zustellungen"),               # Parametri
    ("Inizio", "Start"), ("Iniziale", "Start"), ("Fine", "Ende"), ("Finale", "Ende"),           # Limiti
    ("Sicurezza", "Sicherheit"), ("Totale", "Gesamt"), ("Massimo", "Max"), ("Minimo", "Min"),   # Limiti
    ("Esterna", "Außen"), ("Esterno", "Außen"), ("Interna", "Innen"), ("Interno", "Innen"),     # Direzioni
    ("Rotazione", "Drehung"), ("Specchia", "Spiegeln"), ("Origine", "Nullpunkt"),               # Orientamento
    ("Seleziona", "Auswählen"), ("Selezionato", "Ausgewählt"), ("Acquisisci", "Übernehmen"),    # Azioni
    ("Nuovo", "Neu"), ("Elimina", "Löschen"), ("Salva", "Speichern"), ("Ripristina", "Zurücksetzen"),
    ("Ricalcola", "Berechnen"), ("Aggiorna", "Aktualisieren"), ("Anteprima", "Vorschau"),       # Bottoni
    ("dal", "vom"), ("del", "des"), ("di", "von"), ("per", "pro"), ("con", "mit"), ("e", "&")   # Preposizioni
]                                                                                               # Fine lista termini Tedesco


def traduci(testo):                                                                             # Traduce dall'Italiano al Tedesco
    if not testo:                                                                               # Controllo stringa vuota
        return testo                                                                            # Ritorna vuoto
    s_orig = str(testo)                                                                         # Converte in stringa
    s_norm = re.sub(r"\s*_\s*", " & ", s_orig).strip()                                          # Ripristina eventuali '_' in ' & '

    if s_orig.strip() in TRADUZIONI:                                                            # 1A. Controllo frase esatta originale
        return TRADUZIONI[s_orig.strip()]                                                       # Restituisce la traduzione
    if s_norm in TRADUZIONI:                                                                    # 1B. Controllo frase normalizzata
        return TRADUZIONI[s_norm]                                                               # Restituisce la traduzione

    if s_norm.startswith("Velocità ("):                                                         # Etichetta dinamica velocità simulatore
        return s_norm.replace("Velocità (", "Geschwindigkeit (")                                # Traduce in Geschwindigkeit (...)
    if s_norm.startswith("Statistiche:"):                                                       # Etichetta dinamica statistiche post-processor
        return s_norm.replace("Statistiche:", "Statistik:").replace("righe generate", "Zeilen").replace("utensili impiegati", "Werkzeuge")

    risultato = s_norm                                                                          # 2. Traduzione per parole intere (\b...\b)
    for it_word, de_word in TERMINI_PAROLE_INTERE:                                              # Scorre i termini
        pattern = r"\b" + re.escape(it_word.strip()) + r"\b"                                    # Confine di parola
        if re.search(pattern, risultato, flags=re.IGNORECASE):                                  # Se presente
            risultato = re.sub(pattern, de_word.strip(), risultato, flags=re.IGNORECASE)        # Sostituisce parola intera
    return risultato                                                                            # Restituisce traduzione