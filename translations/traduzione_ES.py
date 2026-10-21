# -*- coding: utf-8 -*-                                                                         # Imposta la codifica UTF-8 per i caratteri speciali spagnoli
import re                                                                                       # Importa il modulo espressioni regolari per la sostituzione di parole intere

LINGUA_CODICE = "es"                                                                            # Identificativo codice lingua Spagnola
LINGUA_NOME = "Español"                                                                         # Nome esteso della lingua

TRADUZIONI = {                                                                                  # Dizionario completo delle frasi esatte Italiano -> Spagnolo per tutti i 13 moduli
    # ==========================================================================
    # BARRE DEGLI STRUMENTI E TOOLTIP (13 COMANDI)
    # ==========================================================================
    "1. Setup Macchina (WCS)": "1. Configuración de Máquina (WCS)",                             # Comando 1 MenuText
    "Configura il sistema di coordinate macchina (WCS), l'origine Z0 e il punto di cambio utensile.": "Configura el sistema de coordenadas de máquina (WCS), el origen Z0 y el punto de cambio de herramienta.",
    "2. Grezzo & Autocentrante": "2. Bruto & Plato",                                            # Comando 2 MenuText
    "Definisce le dimensioni del cilindro/tubo grezzo e le griffe del mandrino autocentrante.": "Define las dimensiones del cilindro/tubo en bruto y las mordazas del plato autocentrante.",
    "3. Pezzo Finito (Target 3D)": "3. Pieza Terminada (Modelo 3D)",                            # Comando 3 MenuText
    "Seleziona e posiziona il solido 3D del pezzo finito dentro il grezzo.": "Selecciona y alinea el sólido 3D de la pieza terminada dentro del bruto.",
    "4. Magazzino Utensili": "4. Biblioteca de Herramientas",                                   # Comando 4 MenuText
    "Gestisce il magazzino utensili di tornitura, gole, filettatura e foratura.": "Gestiona la biblioteca de herramientas de torneado, ranurado, roscado y taladrado.",
    "5. Torretta Portautensili 3D": "5. Torreta Portaherramientas 3D",                          # Comando 5 MenuText
    "Configura il disco torretta 3D e monta gli utensili nelle stazioni.": "Configura el disco de torreta 3D y monta las herramientas en las estaciones.",
    "1. Sgrossatura": "1. Desbaste",                                                            # Comando 6 MenuText
    "Ciclo di sgrossatura longitudinale o frontale con riconoscimento automatico del profilo 3D.": "Ciclo de desbaste longitudinal o refrentado con reconocimiento automático del perfil 3D.",
    "2. Finitura": "2. Acabado",                                                                # Comando 7 MenuText
    "Passata continua di finitura sul profilo reale del pezzo finito con compensazione raggio.": "Pasada continua de acabado sobre el perfil real de la pieza terminada con compensación de radio.",
    "3. Gola": "3. Ranurado",                                                                   # Comando 8 MenuText
    "Scavo di gole radiali esterne, interne o frontali con ciclo a tuffi multipli e pulizia fondo.": "Mecanizado de ranuras radiales exteriores, interiores o frontales con penetraciones múltiples y limpieza de fondo.",
    "4. Filettatura": "4. Roscado",                                                             # Comando 9 MenuText
    "Filettatura cilindrica o conica (Metrica ISO, Gas BSP, NPT, Trapezoidale) a sezione costante.": "Roscado cilíndrico o cónico (Métrica ISO, Gas BSP, NPT, Trapezoidal) a sección constante.",
    "5. Foratura Asse": "5. Taladrado Axial",                                                   # Comando 10 MenuText
    "Centrinatura, foratura profonda a scarico truciolo (G83/G73) e maschiatura sull'asse Z.": "Centrado, taladrado profundo con descarga de viruta (G83/G73) y roscado con macho en el eje Z.",
    "6. Troncatura": "6. Tronzado",                                                             # Comando 11 MenuText
    "Taglio finale del pezzo finito dalla barra con smusso/raccordo automatico sullo spigolo.": "Corte final de la pieza terminada desde la barra con chaflán/radio automático en la arista.",
    "1. Simulazione 3D": "1. Simulación 3D",                                                    # Comando 12 MenuText
    "Simula in 3D il movimento della torretta, l'asportazione sul grezzo e verifica le collisioni.": "Simula en 3D el movimiento de la torreta, el arranque de material en el bruto y verifica colisiones.",
    "2. Genera G-Code": "2. Generar Código G",                                                  # Comando 13 MenuText
    "Genera, visualizza ed esporta il programma G-Code per Fanuc/Haas, Siemens, Mach3 e LinuxCNC.": "Genera, visualiza y exporta el programa G-Code para Fanuc/Haas, Siemens, Mach3 y LinuxCNC.",

    # ==========================================================================
    # PANNELLO 1: SETUP MACCHINA (WCS)
    # ==========================================================================
    "Configurazione Setup Macchina (WCS)": "Configuración de Máquina (WCS)",                    # Titolo Setup WCS
    "Sistema di Coordinate Pezzo (WCS)": "Sistema de Coordenadas de Pieza (WCS)",               # Gruppo WCS
    "Origine WCS (Z0 Pezzo)": "Origen WCS (Z0 Pieza)",                                          # Gruppo Origine Z0
    "Origine X:": "Origen X:",                                                                  # Origine X
    "Origine Y:": "Origen Y:",                                                                  # Origine Y
    "Origine Z:": "Origen Z:",                                                                  # Origine Z
    "Origine Z (Z0):": "Origen Z (Z0):",                                                        # Origine Z0
    "Origine Z0 (mm):": "Origen Z0 (mm):",                                                      # Origine Z0 in mm
    "Quota Z0 Pezzo:": "Cota Z0 de Pieza:",                                                     # Quota Z0
    "Acquisisci Z0 da Faccia/Vertice 3D": "Capturar Z0 de Cara/Vértice 3D",                     # Bottone acquisisci Z0
    "Acquisisci Z0 da Faccia 3D": "Capturar Z0 de Cara 3D",                                     # Variante bottone Z0
    "Allinea Z0 a Faccia Selezionata": "Alinear Z0 a Cara Seleccionada",                        # Variante allinea Z0
    "Posizione Cambio Utensile": "Posición de Cambio de Herramienta",                           # Gruppo cambio utensile
    "Punto Cambio Utensile (Home)": "Punto de Cambio de Herramienta (Home)",                    # Variante cambio utensile
    "Cambio Utensile X:": "Cambio de Herramienta X:",                                           # Quota X cambio
    "Cambio Utensile Z:": "Cambio de Herramienta Z:",                                           # Quota Z cambio
    "Cambio Utensile X (Raggio):": "Cambio de Herramienta X (Radio):",                          # Quota X raggio
    "Quota X Cambio (Raggio):": "Cota X de Cambio (Radio):",                                    # Quota X raggio
    "Quota Z Cambio:": "Cota Z de Cambio:",                                                     # Quota Z
    "Configurazione Torretta": "Configuración de Torreta",                                      # Gruppo torretta nel setup
    "Posizione Torretta:": "Posición de Torreta:",                                              # Posizione torretta
    "Posteriore (X+ Standard CNC)": "Trasera (X+ Estándar CNC)",                                # Opzione torretta posteriore
    "Anteriore (X- Tornio Parallelo)": "Delantera (X- Torno Paralelo)",                         # Opzione torretta anteriore
    "Giri Max Mandrino:": "RPM Máximas del Husillo:",                                           # Limite giri
    "Giri Max (G50):": "RPM Máx. (G50):",                                                       # Limite giri G50
    "Dimensione Icona WCS:": "Tamaño de Icono WCS:",                                            # Dimensione frecce WCS
    "Dimensione Assi WCS:": "Tamaño de Ejes WCS:",                                              # Variante dimensione assi
    "Mostra Assi WCS 3D": "Mostrar Ejes WCS 3D",                                                # Checkbox mostra WCS

    # ==========================================================================
    # PANNELLO 2: GREZZO & AUTOCENTRANTE (STOCK & CHUCK)
    # ==========================================================================
    "Archivio Grezzi / Mandrini": "Archivo de Brutos / Platos",                                 # Gruppo archivio grezzi
    "Carica Grezzo": "Cargar Bruto",                                                            # Bottone carica grezzo
    "Carica Stock": "Cargar Bruto",                                                             # Correzione stringa parziale
    "Elimina": "Eliminar",                                                                      # Bottone elimina
    "Delete": "Eliminar",                                                                       # Traduce Delete in Spagnolo
    "Salva in Archivio Permanente all'OK": "Guardar en Archivo Permanente al dar OK",           # Checkbox salva in archivio
    "Save in Archivio Permanente all'OK": "Guardar en Archivo Permanente al dar OK",            # Correzione stringa parziale
    "1. Grezzo": "1. Bruto",                                                                    # Scheda 1 grezzo
    "1. Stock": "1. Bruto",                                                                     # Traduce 1. Stock
    "2. Presa & Limiti": "2. Sujeción & Límites",                                               # Scheda 2 presa e limiti
    "2. Presa _Limiti": "2. Sujeción & Límites",                                                # Variante con underscore
    "2. Grip _Limits": "2. Sujeción & Límites",                                                 # Correzione stringa parziale
    "Dimensioni Barra & Sovrametalli": "Dimensiones de Barra & Sobremateriales",                # Gruppo dimensioni barra (CORRETTO!)
    "Dimensioni Barra _Sovrametalli": "Dimensiones de Barra & Sobremateriales",                 # Variante con underscore (CORRETTO!)
    "Dimensions Bar _Sovrametalli": "Dimensiones de Barra & Sobremateriales",                   # Correzione stringa parziale (CORRETTO!)
    "Rileva Misure dal Pezzo 3D Selezionato": "Detectar Medidas de la Pieza 3D Seleccionada",   # Bottone rileva misure 3D
    "Rileva Misure dal Part 3D Selected": "Detectar Medidas de la Pieza 3D Seleccionada",       # Correzione stringa parziale
    "Tipo Barra:": "Tipo de Barra:",                                                            # Etichetta tipo barra
    "Type Bar:": "Tipo de Barra:",                                                              # Correzione stringa parziale
    "Cilindro Pieno": "Cilindro Macizo",                                                        # Voce tendina cilindro pieno
    "Tubo Forato": "Tubo Perforado",                                                            # Voce tendina tubo forato
    "Diametro Base (mm):": "Diámetro Base (mm):",                                               # Diametro base
    "Diameter Base (mm):": "Diámetro Base (mm):",                                               # Correzione stringa parziale
    "Diametro Foro Int. (mm):": "Diámetro Agujero Int. (mm):",                                  # Diametro foro interno
    "Diameter Bore Int. (mm):": "Diámetro Agujero Int. (mm):",                                  # Correzione stringa parziale
    "Lunghezza Totale (mm):": "Longitud Total (mm):",                                           # Lunghezza totale
    "Total Length (mm):": "Longitud Total (mm):",                                               # Traduce Total Length
    "Sovrametallo Fronte Z+ (mm):": "Sobrematerial Frontal Z+ (mm):",                           # Sovrametallo frontale Z+
    "Allowance Fronte Z+ (mm):": "Sobrematerial Frontal Z+ (mm):",                              # Correzione stringa parziale
    "Sovrametallo Raggio X+ (mm):": "Sobrematerial Radial X+ (mm):",                            # Sovrametallo radiale X+
    "Allowance Radius X+ (mm):": "Sobrematerial Radial X+ (mm):",                               # Correzione stringa parziale
    "Trasparenza Visiva (%):": "Transparencia Visual (%):",                                     # Trasparenza visiva %
    "Transparency Visiva (%):": "Transparencia Visual (%):",                                    # Correzione stringa parziale
    "Configurazione Grezzo e Mandrino": "Configuración de Bruto y Plato",                       # Titolo Grezzo
    "Dimensioni Grezzo": "Dimensiones del Bruto",                                               # Gruppo dimensioni grezzo
    "Geometria Cilindro / Tubo Grezzo": "Geometría de Cilindro / Tubo en Bruto",                # Variante gruppo grezzo
    "Adatta automaticamente al Pezzo 3D": "Ajustar automáticamente a la Pieza 3D",              # Bottone adatta a pezzo
    "Adatta a Pezzo Finito": "Ajustar a Pieza Terminada",                                       # Variante bottone adatta
    "Autocentrante 3 Griffe": "Plato de 3 Mordazas",                                            # Gruppo autocentrante
    "Mandrino Autocentrante a 3 Griffe": "Plato Autocentrante de 3 Mordazas",                   # Variante gruppo autocentrante
    "Mostra Autocentrante 3D": "Mostrar Plato 3D",                                              # Checkbox mostra autocentrante
    "Visualizza Mandrino 3D": "Mostrar Plato 3D",                                               # Variante mostra mandrino
    "Diametro Autocentrante:": "Diámetro del Plato:",                                           # Diametro mandrino
    "Diametro Autocentrante (mm):": "Diámetro del Plato (mm):",                                 # Diametro mandrino mm
    "Diametro Mandrino (mm):": "Diámetro del Plato (mm):",                                      # Diametro mandrino mm
    "Presa Griffe su Grezzo:": "Agarre de Mordazas en Bruto:",                                  # Presa griffe
    "Presa Griffe (mm):": "Agarre de Mordazas (mm):",                                           # Presa griffe mm
    "Lunghezza Presa Griffe:": "Longitud de Agarre de Mordazas:",                               # Variante presa griffe
    "Sporgenza Fuori Mandrino:": "Voladizo Fuera del Plato:",                                   # Sporgenza pezzo
    "Limite Sicurezza Z Griffe (mm):": "Límite de Seguridad Z de Mordazas (mm):",               # Limite Z griffe
    "Trasparenza Grezzo:": "Transparencia del Bruto:",                                          # Trasparenza grezzo
    "Diametro Esterno:": "Diámetro Exterior:",                                                  # Diametro esterno
    "Diametro Esterno (mm):": "Diámetro Exterior (mm):",                                        # Diametro esterno mm
    "Diametro Interno:": "Diámetro Interior:",                                                  # Diametro interno
    "Diametro Interno (mm):": "Diámetro Interior (mm):",                                        # Diametro interno mm
    "Diametro Foro Interno:": "Diámetro de Agujero Interior:",                                  # Foro interno
    "Lunghezza Totale:": "Longitud Total:",                                                     # Lunghezza totale
    "Lunghezza Grezzo:": "Longitud del Bruto:",                                                 # Lunghezza grezzo
    "Lunghezza Grezzo (mm):": "Longitud del Bruto (mm):",                                       # Lunghezza grezzo mm
    "Sovrametallo Frontale:": "Sobrematerial Frontal:",                                         # Sovrametallo frontale
    "Sovrametallo Frontale (Z+):": "Sobrematerial Frontal (Z+):",                               # Sovrametallo Z+
    "Sovrametallo Radiale:": "Sobrematerial Radial:",                                           # Sovrametallo radiale

    # ==========================================================================
    # PANNELLO 3: PEZZO FINITO (TARGET PART 3D)
    # ==========================================================================
    "Selezione e Allineamento Pezzo Finito": "Selección y Alineación de Pieza Terminada",       # Titolo Pezzo Finito
    "Modello 3D Pezzo Finito": "Modelo 3D de Pieza Terminada",                                  # Gruppo modello 3D
    "Oggetto 3D Selezionato:": "Objeto 3D Seleccionado:",                                       # Oggetto 3D
    "Solido Target:": "Sólido Objetivo:",                                                       # Variante solido target
    "Usa Oggetto Selezionato nella Vista 3D": "Usar Objeto Seleccionado en la Vista 3D",        # Bottone usa selezione
    "Acquisisci Solido Selezionato": "Capturar Sólido Seleccionado",                            # Variante bottone acquisisci
    "Allinea al Centro e Fronte Grezzo": "Alinear al Centro y Frente del Bruto",                # Bottone allinea
    "Centra sull'Asse Z del Tornio": "Centrar en el Eje Z del Torno",                           # Variante centra
    "Inverti Orientamento Z (Ruota 180°)": "Invertir Orientación Z (Girar 180°)",               # Bottone ruota 180
    "Ruota Pezzo 180°": "Girar Pieza 180°",                                                     # Variante ruota
    "Offset Assiale Z:": "Desfase Axial Z:",                                                    # Offset Z
    "Spostamento Z (mm):": "Desplazamiento Z (mm):",                                            # Spostamento Z

    # ==========================================================================
    # PANNELLO 4 & 5: MAGAZZINO UTENSILI E TORRETTA 3D (TUTTE LE SCHEDE)
    # ==========================================================================
    "Dati Generali & Stazione Torretta": "Datos Generales & Estación de Torreta",               # Gruppo dati generali utensile con &
    "Dati Generali e Stazione Torretta": "Datos Generales & Estación de Torreta",               # Gruppo dati generali utensile
    "Dati Generali _Stazione Torretta": "Datos Generales & Estación de Torreta",                # Con underscore
    "Dati Generali _Station Turret": "Datos Generales & Estación de Torreta",                   # Correzione stringa parziale
    "Dati Generali Utensile": "Datos Generales de Herramienta",                                 # Variante dati generali
    "Nome:": "Nombre:",                                                                         # Nome
    "Name:": "Nombre:",                                                                         # Traduce Name
    "Nome Utensile:": "Nombre de Herramienta:",                                                 # Nome utensile
    "N° Posizioni Torretta:": "Nº Posiciones de Torreta:",                                      # Numero posizioni torretta
    "N° Posizioni Turret:": "Nº Posiciones de Torreta:",                                        # Variante numero posizioni
    "Stazione Assegnata:": "Estación Asignada:",                                                # Stazione assegnata
    "Station Axisgnata:": "Estación Asignada:",                                                 # Correzione stringa precedente
    "Stazione Torretta:": "Estación de Torreta:",                                               # Stazione torretta
    "Numero Stazione:": "Número de Estación:",                                                  # Numero stazione
    "1. Geometria": "1. Geometría",                                                             # Tab 1 Utensili
    "1. Geometry": "1. Geometría",                                                              # Tab 1 Utensili
    "2. Custom 3D": "2. Modelo 3D Propio",                                                      # Tab 2 Utensili
    "2. Modello 3D Custom": "2. Modelo 3D Propio",                                              # Variante Tab 2
    "3. Tecnologia": "3. Tecnología",                                                           # Tab 3 Utensili
    "3. Technology": "3. Tecnología",                                                           # Tab 3 Utensili
    "Categoria Lavorazione": "Categoría de Mecanizado",                                         # Gruppo categoria
    "Categoria Lavorazione:": "Categoría de Mecanizado:",                                       # Etichetta categoria
    "Geometria Inserto / Tagliente": "Geometría de Plaquita / Filo",                            # Gruppo geometria inserto
    "Geometry Insert / Edge": "Geometría de Plaquita / Filo",                                   # Variante gruppo geometria inserto
    "Forma Inserto:": "Forma de Plaquita:",                                                     # Forma inserto
    "Forma Insert:": "Forma de Plaquita:",                                                      # Variante forma inserto
    "Raggio Punta (mm):": "Radio de Punta (mm):",                                               # Raggio punta mm
    "Radius Tip/Drill (mm):": "Radio de Punta / Broca (mm):",                                   # Variante raggio punta
    "Raggio Punta (Nose R):": "Radio de Punta (Nose R):",                                       # Raggio punta
    "Raggio Inserto:": "Radio de Plaquita:",                                                    # Raggio inserto
    "Angolo Inserto:": "Ángulo de Plaquita:",                                                   # Angolo inserto
    "Verso Taglio:": "Sentido de Corte:",                                                       # Verso di taglio
    "Verso Cutting:": "Sentido de Corte:",                                                      # Variante verso di taglio
    "Angolo Reg. Kapr (°):": "Ángulo de Posición Kapr (°):",                                    # Angolo registrazione Kapr
    "Angle Reg. Kapr (°):": "Ángulo de Posición Kapr (°):",                                     # Variante angolo Kapr
    "Angolo Approccio (Kr):": "Ángulo de Ataque (Kr):",                                         # Angolo approccio Kr
    "Dimensioni Corpo / Stelo": "Dimensiones de Cuerpo / Mango",                                # Gruppo dimensioni stelo
    "Dimensioni Corpo / Shank": "Dimensiones de Cuerpo / Mango",                                # Variante dimensioni stelo
    "Larghezza Stelo (mm):": "Ancho de Mango (mm):",                                            # Larghezza stelo
    "Width Shank (mm):": "Ancho de Mango (mm):",                                                # Variante larghezza stelo
    "Altezza Stelo (mm):": "Altura de Mango (mm):",                                             # Altezza stelo
    "Height Shank (mm):": "Altura de Mango (mm):",                                              # Variante altezza stelo
    "Length Total (mm):": "Longitud Total (mm):",                                               # Variante lunghezza totale
    "Larghezza Tagliente:": "Ancho de Corte:",                                                  # Larghezza tagliente
    "Larghezza Lama (mm):": "Ancho de Lama (mm):",                                              # Larghezza lama troncatura/gola
    "Diametro Utensile (mm):": "Diámetro de Herramienta (mm):",                                 # Diametro utensile
    "Sezione Stelo:": "Sección del Mango:",                                                     # Sezione stelo
    "Lunghezza Stelo:": "Longitud del Mango:",                                                  # Lunghezza stelo
    "Sporgenza Utensile:": "Voladizo de Herramienta:",                                          # Sporgenza utensile
    "Orientamento Spaziale 3D (Live)": "Orientación Espacial 3D (En Vivo)",                     # Gruppo orientamento 3D
    "Specchia X": "Espejo X",                                                                   # Checkbox Specchia X
    "Specchia Y": "Espejo Y",                                                                   # Checkbox Specchia Y
    "Specchia Z": "Espejo Z",                                                                   # Checkbox Specchia Z
    "Rotazione X (°):": "Rotación X (°):",                                                      # Rotazione X
    "Rotazione Y (°):": "Rotación Y (°):",                                                      # Rotazione Y
    "Rotazione Z (°):": "Rotación Z (°):",                                                      # Rotazione Z
    "Offset X (mm):": "Desfase X (mm):",                                                        # Offset X
    "Offset Y (mm):": "Desfase Y (mm):",                                                        # Offset Y
    "Offset Z (mm):": "Desfase Z (mm):",                                                        # Offset Z
    "Modello 3D Personalizzato (STEP / Oggetto FreeCAD)": "Modelo 3D Personalizado (STEP / Objeto FreeCAD)",
    "Usa Modello 3D Personalizzato": "Usar Modelo 3D Personalizzato",                           # Checkbox modello custom
    "Importa File STEP...": "Importar Archivo STEP...",                                         # Bottone importa STEP
    "Acquisisci Oggetto 3D Selezionato": "Capturar Objeto 3D Seleccionado",                     # Bottone acquisisci 3D
    "Posizione Punta Tagliente (TCP)": "Posición de Punta de Corte (TCP)",                      # Gruppo TCP
    "Acquisisci TCP da Vertice 3D": "Capturar TCP desde Vértice 3D",                            # Bottone TCP
    "Parametri Tecnologici Default": "Parámetros de Corte por Defecto",                         # Gruppo tecnologia utensile
    "Velocità Taglio Default (Vc):": "Velocidad de Corte por Defecto (Vc):",                    # Vc default
    "Avanzamento Default (F):": "Avance por Defecto (F):",                                      # F default
    "Profondità Max (Ap):": "Profundidad Máx. (Ap):",                                           # Ap max
    "Verso Rotazione:": "Sentido de Giro:",                                                     # Verso rotazione mandrino
    "Verso Rotazione Mandrino:": "Sentido de Giro del Husillo:",                                # Variante verso rotazione
    "Antiorario (M03)": "Antihorario / Avance (M03)",                                           # M03
    "Orario (M04)": "Horario / Reversa (M04)",                                                  # M04
    "Magazzino Utensili Tornio": "Biblioteca de Herramientas de Torno",                         # Titolo magazzino
    "Elenco Utensili nel Magazzino": "Lista de Herramientas en Biblioteca",                     # Gruppo elenco utensili
    "➕ Nuovo Utensile": "➕ Nueva Herramienta",                                                # Bottone nuovo
    "🗑 Elimina Utensile": "🗑 Eliminar Herramienta",                                           # Bottone elimina
    "↺ Ripristina Default": "↺ Restaurar por Defecto",                                          # Bottone ripristina
    "Proprietà Utensile Selezionato": "Propiedades de Herramienta Seleccionada",                # Gruppo proprietà
    "Configurazione Torretta Portautensili 3D": "Configuración de Torreta Portaherramientas 3D",# Titolo torretta 3D
    "Geometria Disco Torretta": "Geometría del Disco de Torreta",                               # Gruppo disco torretta
    "Numero Stazioni:": "Número de Estaciones:",                                                # Numero stazioni
    "Stazione Attiva:": "Estación Activa:",                                                     # Stazione attiva
    "Ruota Torretta su Stazione:": "Girar Torreta a Estación:",                                 # Ruota torretta
    "Diametro Disco:": "Diámetro del Disco:",                                                   # Diametro disco
    "Diametro Disco (mm):": "Diámetro del Disco (mm):",                                         # Diametro disco mm
    "Spessore Disco:": "Espesor del Disco:",                                                    # Spessore disco
    "Spessore Disco (mm):": "Espesor del Disco (mm):",                                          # Spessore disco mm
    "Raggio Montaggio Utensili:": "Radio de Montaje de Herramientas:",                          # Raggio montaggio
    "Offset Centro X:": "Desfase Centro X:",                                                    # Offset X torretta
    "Offset Centro Z:": "Desfase Centro Z:",                                                    # Offset Z torreta
    "Utensili Montati sulle Stazioni": "Herramientas Montadas en Estaciones",                   # Gruppo stazioni
    "Mostra Disco Torretta 3D": "Mostrar Disco de Torreta 3D",                                  # Checkbox mostra torretta

    # ==========================================================================
    # PANNELLI 6..11: LAVORAZIONI CAM (SGROSSATURA, FINITURA, GOLA, FILETTO, FORO, TRONCATURA)
    # ==========================================================================
    "1. Utensile e Modalità": "1. Herramienta y Modo de Ciclo",                                 # Gruppo 1 operazioni
    "1. Utensile & Modalità": "1. Herramienta y Modo de Ciclo",                                 # Con &
    "1. Utensile e Ciclo": "1. Herramienta y Ciclo",                                            # Variante Gruppo 1
    "Utensile:": "Herramienta:",                                                                # Utensile
    "Utensile Assegnato:": "Herramienta Asignada:",                                             # Utensile assegnato
    "Ciclo:": "Ciclo:",                                                                         # Ciclo
    "Tipo Ciclo:": "Tipo de Ciclo:",                                                            # Tipo ciclo
    "Direzione:": "Dirección:",                                                                 # Direzione
    "Modalità:": "Modo:",                                                                       # Modalità
    "Acquisisci da 3D (Faccia/Bordo)": "Capturar de 3D (Cara/Arista)",                          # Bottone acquisisci 3D
    "Acquisisci Quote da Selezione 3D": "Capturar Cotas de Selección 3D",                       # Variante bottone 3D
    "Seleziona da Modello 3D": "Seleccionar del Modelo 3D",                                     # Variante bottone 3D
    "2. Limiti Geometrici": "2. Límites Geométricos",                                           # Gruppo 2 operazioni
    "2. Geometria e Quote": "2. Geometría y Cotas",                                             # Variante Gruppo 2
    "Geometria e Quote": "Geometría y Cotas",                                                   # Variante Gruppo 2
    "Limiti Geometrici": "Límites Geométricos",                                                 # Variante Gruppo 2
    "3. Parametri di Taglio": "3. Parámetros de Corte",                                         # Gruppo 3 operazioni
    "4. Parametri di Taglio": "4. Parámetros de Corte",                                         # Gruppo 4 operazioni
    "Parametri Tecnologici": "Parámetros de Corte",                                             # Variante parametri
    "Parametri di Taglio": "Parámetros de Corte",                                               # Variante parametri
    "Profondità Passata:": "Profundidad de Pasada:",                                            # Profondità passata
    "Profondità per Passata:": "Profundidad por Pasada:",                                       # Profondità per passata
    "Profondità Passata (mm):": "Profundidad de Pasada (mm):",                                  # Ap mm
    "Profondità Passata (Ap):": "Profundidad de Pasada (Ap):",                                  # Ap
    "Incremento Radiale (Ap):": "Paso Radial (Ap):",                                            # Ap radiale
    "Sovrametallo X:": "Sobrematerial X:",                                                      # Sovrametallo X
    "Sovrametallo Z:": "Sobrematerial Z:",                                                      # Sovrametallo Z
    "Sovrametallo X (mm):": "Sobrematerial X (mm):",                                            # Sovrametallo X mm
    "Sovrametallo Z (mm):": "Sobrematerial Z (mm):",                                            # Sovrametallo Z mm
    "Sovrametallo Radiale X:": "Sobrematerial Radial X:",                                       # Sovrametallo radiale X
    "Sovrametallo Assiale Z:": "Sobrematerial Axial Z:",                                        # Sovrametallo assiale Z
    "Sovrametallo Diametro:": "Sobrematerial en Diámetro:",                                     # Sovrametallo diametro
    "Avanzamento:": "Avance:",                                                                  # Avanzamento
    "Avanzamento (F):": "Avance (F):",                                                          # Avanzamento F
    "Avanzamento (mm/giro):": "Avance (mm/rev):",                                               # Avanzamento mm/giro
    "Avanzamento Lavoro (F):": "Avance de Trabajo (F):",                                        # Avanzamento lavoro
    "Velocità Taglio:": "Velocidad de Corte:",                                                  # Velocità taglio
    "Velocità Taglio (Vc):": "Velocidad de Corte (Vc):",                                        # Velocità taglio Vc
    "Velocità Taglio (m/min):": "Velocidad de Corte (m/min):",                                  # Velocità taglio m/min
    "Giri Mandrino:": "RPM del Husillo:",                                                       # Giri mandrino
    "Giri Mandrino (RPM):": "Velocidad de Husillo (RPM):",                                      # Giri mandrino RPM
    "Raggio Sicurezza:": "Radio de Seguridad:",                                                 # Raggio sicurezza
    "Raggio Sicurezza (mm):": "Radio de Seguridad (mm):",                                       # Raggio sicurezza mm
    "Distacco Sicurezza:": "Margen de Seguridad:",                                              # Distacco sicurezza
    "Distacco Sicurezza (mm):": "Margen de Seguridad (mm):",                                    # Distacco sicurezza mm
    "Rientro (Retract):": "Retracción (Retract):",                                              # Rientro
    "Quota Z Inizio:": "Cota Z Inicial:",                                                       # Quota Z inizio
    "Quota Z Fine:": "Cota Z Final:",                                                           # Quota Z fine
    "Quota Z Inizio (mm):": "Cota Z Inicial (mm):",                                             # Quota Z inizio mm
    "Quota Z Fine (mm):": "Cota Z Final (mm):",                                                 # Quota Z fine mm
    "Z Iniziale:": "Z Inicial:",                                                                # Z iniziale
    "Z Finale:": "Z Final:",                                                                    # Z finale
    "Z Inizio:": "Z Inicial:",                                                                  # Z inizio
    "Z Fine:": "Z Final:",                                                                      # Z fine
    "Z Taglio:": "Z de Tronzado:",                                                              # Z taglio troncatura
    "Quota Z Troncatura:": "Cota Z de Tronzado:",                                               # Quota Z troncatura
    "Diametro Iniziale:": "Diámetro Inicial:",                                                  # Diametro iniziale
    "Diametro Finale:": "Diámetro Final:",                                                      # Diametro finale
    "Diametro Massimo:": "Diámetro Máximo:",                                                    # Diametro massimo
    "Diametro Minimo:": "Diámetro Mínimo:",                                                     # Diametro minimo
    "Diametro Fondo:": "Diámetro de Fondo:",                                                    # Diametro fondo gola/filetto
    "Diametro Nominale:": "Diámetro Nominal:",                                                  # Diametro nominale filetto
    "Larghezza Gola:": "Ancho de Ranura:",                                                      # Larghezza gola
    "Larghezza Gola (mm):": "Ancho de Ranura (mm):",                                            # Larghezza gola mm
    "Profondità Gola:": "Profundidad de Ranura:",                                               # Profondità gola
    "Passo Filetto:": "Paso de Rosca:",                                                         # Passo filetto
    "Passo Filetto (mm):": "Paso de Rosca (mm):",                                               # Passo filetto mm
    "Passo (P):": "Paso (P):",                                                                  # Passo P
    "Altezza Filetto:": "Altura de Rosca:",                                                     # Altezza filetto
    "Profondità Filetto:": "Profundidad de Rosca:",                                             # Profondità filetto
    "Angolo Profilo:": "Ángulo de Perfil:",                                                     # Angolo profilo
    "Angolo Filetto (°):": "Ángulo de Rosca (°):",                                              # Angolo filetto
    "Passate a Vuoto:": "Pasadas en Vacío:",                                                    # Passate a vuoto
    "Numero Passate:": "Número de Pasadas:",                                                    # Numero passate
    "Passate di Taglio:": "Pasadas de Corte:",                                                  # Passate di taglio
    "Standard Filettatura:": "Norma de Rosca:",                                                 # Standard filettatura
    "Profondità Foro:": "Profundidad de Agujero:",                                              # Profondità foro
    "Profondità Foro (mm):": "Profundidad de Agujero (mm):",                                    # Profondità foro mm
    "Profondità Totale:": "Profundidad Total:",                                                 # Profondità totale
    "Diametro Punta:": "Diámetro de Broca:",                                                    # Diametro punta
    "Diametro Punta (mm):": "Diámetro de Broca (mm):",                                          # Diametro punta mm
    "Incremento Scarico (Q):": "Profundidad de Picoteo (Q):",                                   # Incremento Q
    "Profondità Tuffo (Q):": "Profundidad de Penetración (Q):",                                 # Profondità tuffo Q
    "Smusso Spigolo:": "Chaflán de Arista:",                                                    # Smusso spigolo
    "Raccordo / Smusso:": "Radio / Chaflán:",                                                   # Raccordo / Smusso
    "Compensazione Raggio Punta:": "Compensación de Radio de Punta:",                           # Compensazione raggio
    "Usa Profilo 3D Pezzo Finito": "Seguir Perfil 3D de Pieza Terminada",                       # Checkbox profilo 3D
    "Riconoscimento Automatico Profilo 3D": "Reconocimiento Automático de Perfil 3D",           # Checkbox riconoscimento 3D
    "Ricalcola / Anteprima": "Recalcular / Vista Previa",                                       # Bottone ricalcola
    "Aggiorna Anteprima 3D": "Actualizar Vista Previa 3D",                                      # Bottone aggiorna

    # ==========================================================================
    # PANNELLO 12 & 13: SIMULAZIONE 3D E POST-PROCESSOR E-CAM
    # ==========================================================================
    "Selezione Operazioni e Modalità": "Selección de Operaciones y Modo",                       # Simulazione gruppo 1
    "Simula:": "Simular:",                                                                      # Tendina simula
    "★ Tutte le Operazioni in Sequenza": "★ Todas las Operaciones en Secuencia",                # Tutte le operazioni
    "Simula asportazione materiale sul Grezzo": "Simular Arranque de Material en Bruto 3D",     # Checkbox asportazione 3D
    "Verifica Collisioni 3D in tempo reale": "Verificar Colisiones 3D en Tiempo Real",          # Checkbox collisioni
    "Metti in Pausa se rileva collisione": "Pausar Automáticamente si Detecta Colisión",        # Checkbox pausa collisione
    "Controlli Riproduzione e Velocità": "Controles de Reproducción y Velocidad",               # Gruppo controlli player
    "▶ Play": "▶ Play",                                                                         # Bottone Play
    "⏸ Pausa": "⏸ Pausa",                                                                       # Bottone Pausa
    "⏹ Reset": "⏹ Reiniciar",                                                                   # Bottone Reset
    "Controllo Numerico (DRO Tempo Reale)": "Control Numérico (DRO en Tiempo Real)",            # Gruppo DRO
    "Controllo Collisioni: Nessuna interferenza.": "Control de Colisiones: Sin interferencias.",# Stato collisioni OK
    "Simulazione Completata! (Premi Reset o Play per rivedere)": "¡Simulación Completada! (Pulsa Reiniciar o Play para repetir)",
    "Nessuna operazione CAM trovata nel progetto!": "¡No se encontraron operaciones CAM en el proyecto!",
    "1. Controllo & Programma": "1. Control CNC & Programa",                                    # Tab 1 Post-Processor
    "2. Configuratore e-CAM (Template & Codici)": "2. Configurador e-CAM (Plantillas & Códigos)",
    "Configurazione Controllo CNC e Operazioni": "Configuración de Control CNC y Operaciones",  # Gruppo CNC
    "Esporta:": "Exportar:",                                                                    # Tendina esporta
    "Controllo CNC:": "Control CNC:",                                                           # Tendina controllo CNC
    "Quote Asse X:": "Cotas Eje X:",                                                            # Tendina Diametro/Raggio
    "Modo Avanz.:": "Modo de Avance:",                                                          # Tendina modalità avanzamento
    "Velocità Carro:": "Velocidad del Carro:",                                                  # Casella velocità carro
    "Millimetri al Giro (mm/giro - G95)": "Milímetros por Revolución (mm/rev - G95)",           # Opzione G95
    "Millimetri al Secondo (mm/s -> G94)": "Milímetros por Segundo (mm/s -> G94)",              # Opzione mm/s -> G94
    "Millimetri al Minuto (mm/min - G94)": "Milímetros por Minuto (mm/min - G94)",              # Opzione mm/min G94
    "Programmazione al Diametro (X = 2*R)": "Programación en Diámetro (X = 2*R)",               # Opzione Diametro
    "Programmazione al Raggio (X = R)": "Programación en Radio (X = R)",                        # Opzione Raggio
    "Nome Prog.:": "Nombre Prog.:",                                                             # Nome programma
    "Opzioni di Formattazione G-Code": "Opciones de Formato de Código G",                       # Gruppo opzioni G-Code
    "Inserisci numeri di riga (N10, N20...)": "Incluir números de línea (N10, N20...)",         # Checkbox numeri N
    "Includi commenti descrittivi operazioni": "Incluir comentarios descriptivos de operaciones",
    "Comanda Refrigerante automatico (M08 / M09)": "Controlar Refrigerante Automático (M08 / M09)",
    "Usa ciclo compatto G76 per Filettatura (Mach3/Fanuc)": "Usar ciclo fijo G76 para Roscado (Mach3/Fanuc)",
    "Inverti segno X (X-) per vista Torretta Mach3": "Invertir signo X (X-) para Torreta Delantera Mach3",
    "Anteprima Live Programma G-Code": "Vista Previa en Vivo del Programa G-Code",              # Gruppo anteprima G-Code
    "📋 Copia Appunti": "📋 Copiar al Portapapeles",                                            # Bottone copia
    "💾 Salva File .NC": "💾 Guardar Archivo .NC",                                              # Bottone salva .NC
    "Gestione Profili Macchina e-CAM": "Gestión de Perfiles de Máquina e-CAM",                  # Gruppo profili e-CAM
    "Profilo Attivo:": "Perfil Activo:",                                                        # Profilo attivo
    "💾 Salva Profilo": "💾 Guardar Perfil",                                                    # Bottone salva profilo
    "Parametri Formattazione e Codici M": "Parámetros de Formato y Códigos M",                  # Gruppo formattazione e-CAM
    "Decimali X / Z:": "Decimales X / Z:",                                                      # Decimali X/Z
    "Inizio / Passo N:": "Inicio / Paso N:",                                                    # Inizio/Passo N
    "Stile Commenti:": "Estilo de Comentarios:",                                                # Stile commenti
    "Codici Acqua ON/OFF:": "Códigos Refrigerante ON/OFF:",                                     # Codici M acqua
    "Template Blocchi G-Code (Variabili: {PROG}, {DATE}, {DOC}, {TOOL}, {STATION}, {FEED_G}, {RPM}, {MAX_RPM}, {HOME_X}, {HOME_Z})": "Plantillas de Bloques G-Code (Vars: {PROG}, {DATE}, {DOC}, {TOOL}, {STATION}, {FEED_G}, {RPM}, {MAX_RPM}, {HOME_X}, {HOME_Z})",
    "Attiva Template Personalizzati e-CAM": "Activar Plantillas Personalizadas e-CAM",          # Checkbox attiva template
    "1. Blocco Inizio Programma (Header):": "1. Bloque de Inicio de Programa (Encabezado):",    # Header
    "2. Blocco Cambio Utensile (Tool Change):": "2. Bloque de Cambio de Herramienta:",          # Tool Change
    "3. Blocco Fine Programma (Footer):": "3. Bloque de Fin de Programa (Cierre):"              # Footer
}                                                                                               # Fine dizionario frasi esatte

# Vocabolario completo di parole intere (\bparola\b) verificato in Italiano -> Spagnolo
TERMINI_PAROLE_INTERE = [                                                                       # Lista coppie (Termine Italiano, Termine Spagnolo)
    ("Archivio Permanente", "Archivo Permanente"), ("Archivio Grezzi", "Archivo de Brutos"),    # Locuzioni pannello Grezzo
    ("Cilindro Pieno", "Cilindro Macizo"), ("Tubo Forato", "Tubo Perforado"),                   # Locuzioni tipo barra
    ("Rileva Misure", "Detectar Medidas"), ("Ø Esterno Effettivo", "Ø Exterior Efectivo"),      # Locuzioni pannello Grezzo
    ("con Sovra", "con Sobremat."), ("Dati Generali", "Datos Generales"),                       # Locuzioni generali
    ("Categoria Lavorazione", "Categoría de Mecanizado"), ("Angolo Reg", "Ángulo de Posición"), # Locuzioni utensili
    ("Angle Reg", "Ángulo de Posición"), ("Velocità di Taglio", "Velocidad de Corte"),          # Locuzioni taglio
    ("Velocità Taglio", "Velocidad de Corte"), ("Profondità per Passata", "Profundidad por Pasada"),
    ("Profondità Passata", "Profundidad de Pasada"), ("Pezzo Finito", "Pieza Terminada"),       # Locuzioni moduli
    ("Foratura Asse", "Taladrado Axial"), ("Passate a Vuoto", "Pasadas en Vacío"),              # Locuzioni cicli
    ("Scarico Truciolo", "Descarga de Viruta"), ("all'OK", "al dar OK"),                        # Locuzioni UI
    ("Archivio", "Archivo"), ("Permanente", "Permanente"), ("Misure", "Medidas"),               # Parole singole Grezzo
    ("Rileva", "Detectar"), ("Carica", "Cargar"), ("Applica", "Aplicar"), ("Azzera", "Reiniciar"),
    ("Grezzi", "Brutos"), ("Grezzo", "Bruto"), ("Mandrini", "Platos"), ("Mandrino", "Plato"),   # Singolari e plurali
    ("Sovrametalli", "Sobremateriales"), ("Sovrametallo", "Sobrematerial"), ("Sovra", "Sobremat."),
    ("Pieno", "Macizo"), ("Forato", "Perforado"), ("Visiva", "Visual"), ("Visivo", "Visual"),   # Aggettivi Grezzo
    ("Effettivo", "Efectivo"), ("Effettiva", "Efectiva"), ("Reale", "Real"),                    # Aggettivi misure
    ("Fronte", "Frente"), ("Frontale", "Frontal"), ("Base", "Base"),                            # Riferimenti geometrici
    ("Configurazione", "Configuración"), ("Impostazioni", "Ajustes"), ("Proprietà", "Propiedades"),
    ("Sgrossatura", "Desbaste"), ("Finitura", "Acabado"), ("Filettatura", "Roscado"),           # Lavorazioni
    ("Foratura", "Taladrado"), ("Troncatura", "Tronzado"), ("Gola", "Ranurado"),                # Lavorazioni
    ("Sfacciatura", "Refrentado"), ("Centrinatura", "Centrado"), ("Maschiatura", "Roscado con Macho"),
    ("Barenatura", "Mandrinado"), ("Tornitura", "Torneado"), ("Lavorazione", "Mecanizado"),     # Lavorazioni
    ("Longitudinale", "Longitudinal"), ("Radiale", "Radial"), ("Assiale", "Axial"),             # Direzioni
    ("Cilindrica", "Cilíndrica"), ("Conica", "Cónica"),                                         # Geometrie ciclo
    ("Esterna", "Exterior"), ("Esterno", "Exterior"), ("Interna", "Interior"), ("Interno", "Interior"),
    ("Destro", "Derecha"), ("Sinistro", "Izquierda"), ("Neutro", "Neutro"),                     # Verso utensile
    ("Posteriore", "Trasera"), ("Anteriore", "Delantera"), ("Superiore", "Superior"), ("Inferiore", "Inferior"),
    ("Diametro", "Diámetro"), ("Raggio", "Radio"), ("Lunghezza", "Longitud"),                   # Geometria
    ("Profondità", "Profundidad"), ("Profondita", "Profundidad"), ("Larghezza", "Ancho"), ("Altezza", "Altura"),
    ("Spessore", "Espesor"), ("Sezione", "Sección"), ("Angolo", "Ángulo"), ("Passo", "Paso"),   # Geometria
    ("Dimensioni", "Dimensiones"), ("Dimensione", "Tamaño"), ("Forma", "Forma"), ("Corpo", "Cuerpo"),
    ("Orientamento", "Orientación"), ("Spaziale", "Espacial"), ("Rotazione", "Rotación"),       # 3D Live
    ("Specchia", "Espejo"), ("Ribalta", "Voltear"), ("Inclinazione", "Inclinación"),            # 3D Live
    ("Passata", "Pasada"), ("Passate", "Pasadas"), ("Avanzamento", "Avance"),                   # Taglio
    ("Velocità", "Velocidad"), ("Velocita", "Velocidad"), ("Taglio", "Corte"),                  # Taglio
    ("Tecnologia", "Tecnología"), ("Tecnologici", "Corte"), ("Geometrici", "Geométricos"),      # Schede/Gruppi
    ("Geometria", "Geometría"), ("Parametri", "Parámetros"), ("Limiti", "Límites"),             # Schede/Gruppi
    ("Giri", "RPM"), ("Costante", "Constante"), ("Fissi", "Fijos"),                             # Mandrino
    ("Utensile", "Herramienta"), ("Utensili", "Herramientas"), ("Magazzino", "Biblioteca"), ("Libreria", "Biblioteca"),
    ("Torretta", "Torreta"), ("Stazione", "Estación"), ("Stazioni", "Estaciones"), ("Disco", "Disco"),
    ("Posizioni", "Posiciones"), ("Posizione", "Posición"), ("Assegnata", "Asignada"), ("Assegnato", "Asignado"),
    ("Attiva", "Activa"), ("Attivo", "Activo"), ("Montati", "Montadas"), ("Montato", "Montada"),# Stazioni (CORRETTO!)
    ("Stelo", "Mango"), ("Inserto", "Plaquita"), ("Punta", "Punta"), ("Tagliente", "Filo"),     # Componenti utensile
    ("Lama", "Lama"), ("Collare", "Collar"), ("Sporgenza", "Voladizo"),                         # Componenti utensile
    ("Pezzo", "Pieza"), ("Finito", "Terminada"), ("Modello", "Modelo"),                         # Pezzo/Grezzo
    ("Solido", "Sólido"), ("Oggetto", "Objeto"), ("Barra", "Barra"), ("Tubo", "Tubo"), ("Cilindro", "Cilindro"),
    ("Autocentrante", "Plato"), ("Griffe", "Mordazas"), ("Presa", "Sujeción"), ("Foro", "Agujero"),
    ("Origine", "Origen"), ("Punto", "Punto"), ("Quota", "Cota"), ("Quote", "Cotas"),           # WCS
    ("Inizio", "Inicio"), ("Iniziale", "Inicial"), ("Fine", "Fin"), ("Finale", "Final"),        # Limiti
    ("Massimo", "Máx."), ("Minimo", "Mín."), ("Totale", "Total"), ("Sicurezza", "Seguridad"),   # Limiti
    ("Distacco", "Margen"), ("Rientro", "Retracción"), ("Uscita", "Salida"), ("Ingresso", "Entrada"),
    ("Scarico", "Picoteo"), ("Truciolo", "Viruta"), ("Vuoto", "Vacío"), ("Pulizia", "Limpieza"),# Cicli
    ("Tuffo", "Penetración"), ("Tuffi", "Penetraciones"), ("Incremento", "Paso"), ("Sosta", "Pausa"),
    ("Smusso", "Chaflán"), ("Raccordo", "Radio"), ("Spigolo", "Arista"), ("Fondo", "Fondo"),    # Finitura/Gola
    ("Filetto", "Rosca"), ("Cresta", "Cresta"), ("Fianco", "Flanco"), ("Conicità", "Conicidad"),# Filettatura
    ("Modalità", "Modo"), ("Modalita", "Modo"), ("Categoria", "Categoría"), ("Verso", "Sentido"),
    ("Direzione", "Dirección"), ("Tipo", "Tipo"), ("Ciclo", "Ciclo"), ("Profilo", "Perfil"), ("Asse", "Eje"),
    ("Seleziona", "Seleccionar"), ("Selezionato", "Seleccionado"), ("Selezionata", "Seleccionada"),
    ("Acquisisci", "Capturar"), ("Faccia", "Cara"), ("Bordo", "Arista"), ("Vertice", "Vértice"), ("Centro", "Centro"),
    ("Allinea", "Alinear"), ("Adatta", "Ajustar"), ("Mostra", "Mostrar"), ("Visualizza", "Mostrar"),
    ("Inverti", "Invertir"), ("Usa", "Usar"), ("Calcola", "Calcular"), ("Ricalcola", "Recalcular"),
    ("Aggiorna", "Actualizar"), ("Anteprima", "Vista Previa"), ("Nuovo", "Nuevo"), ("Elimina", "Eliminar"),
    ("Salva", "Guardar"), ("Ripristina", "Restaurar"), ("Importa", "Importar"), ("Esporta", "Exportar"),
    ("Copia", "Copiar"), ("Appunti", "Portapapeles"), ("Chiudi", "Cerrar"), ("Annulla", "Cancelar"),
    ("Cambio", "Cambio"), ("Macchina", "Máquina"), ("Stile", "Estilo"), ("Numero", "Número"),   # Vari
    ("Nome", "Nombre"), ("Colore", "Color"), ("Trasparenza", "Transparencia"), ("Nessuno", "Ninguno"),
    ("Automatico", "Automático"), ("Automatica", "Automática"), ("Manuale", "Manual"),          # Vari
    ("dal", "de"), ("dalla", "de"), ("del", "de"), ("della", "de"), ("delle", "de"),            # Preposizioni
    ("dei", "de"), ("degli", "de"), ("di", "de"), ("per", "por"), ("su", "en"), ("sul", "en"),  # Preposizioni
    ("sulla", "en"), ("da", "de"), ("al", "a"), ("alla", "a"), ("con", "con"), ("e", "&")       # Preposizioni
]                                                                                               # Fine vocabolario parole intere


def traduci(testo):                                                                             # Funzione principale di traduzione verso lo Spagnolo
    if not testo:                                                                               # Se la stringa è vuota
        return testo                                                                            # Ritorna subito
    s_orig = str(testo)                                                                         # Converte in stringa
    s_norm = re.sub(r"\s*_\s*", " & ", s_orig).strip()                                          # Ripristina eventuali '_' (generati da '&' in Qt) in ' & '

    if s_orig.strip() in TRADUZIONI:                                                            # 1A. Controllo frase esatta originale
        return TRADUZIONI[s_orig.strip()]                                                       # Restituisce traduzione esatta
    if s_norm in TRADUZIONI:                                                                    # 1B. Controllo frase normalizzata (senza underscore)
        return TRADUZIONI[s_norm]                                                               # Restituisce traduzione esatta

    if s_norm.startswith("Velocità ("):                                                         # Etichetta dinamica velocità simulatore
        return s_norm.replace("Velocità (", "Velocidad (")                                      # Traduce in Velocidad (...)
    if s_norm.startswith("Statistiche:"):                                                       # Etichetta dinamica statistiche post-processor
        return s_norm.replace("Statistiche:", "Estadísticas:").replace("righe generate", "líneas").replace("utensili impiegati", "herramientas")

    risultato = s_norm                                                                          # 2. Traduzione intelligente di tutte le parole intere (\b...\b)
    for it_word, es_word in TERMINI_PAROLE_INTERE:                                              # Scorre il vocabolario completo
        pattern = r"\b" + re.escape(it_word.strip()) + r"\b"                                    # Confine rigoroso di parola intera
        if re.search(pattern, risultato, flags=re.IGNORECASE):                                  # Se il termine intero è presente
            risultato = re.sub(pattern, es_word.strip(), risultato, flags=re.IGNORECASE)        # Sostituisce il termine con l'equivalente spagnolo
    return risultato                                                                            # Restituisce la stringa completamente in Spagnolo