# -*- coding: utf-8 -*-                                                                         # Imposta la codifica UTF-8 per i caratteri speciali italiani
LINGUA_CODICE = "it"                                                                            # Identificativo codice lingua Italiana
LINGUA_NOME = "Italiano"                                                                        # Nome esteso della lingua

TRADUZIONI = {                                                                                  # Dizionario di riferimento lingua Italiana (mantiene i testi nativi invariati)
    "1. Setup Macchina (WCS)": "1. Setup Macchina (WCS)",                                       # Comando 1 barra strumenti
    "2. Grezzo & Autocentrante": "2. Grezzo & Autocentrante",                                   # Comando 2 barra strumenti
    "3. Pezzo Finito (Target 3D)": "3. Pezzo Finito (Target 3D)",                               # Comando 3 barra strumenti
    "4. Magazzino Utensili": "4. Magazzino Utensili",                                           # Comando 4 barra strumenti
    "5. Torretta Portautensili 3D": "5. Torretta Portautensili 3D",                             # Comando 5 barra strumenti
    "1. Sgrossatura": "1. Sgrossatura",                                                         # Comando 6 barra strumenti
    "2. Finitura": "2. Finitura",                                                               # Comando 7 barra strumenti
    "3. Gola": "3. Gola",                                                                       # Comando 8 barra strumenti
    "4. Filettatura": "4. Filettatura",                                                         # Comando 9 barra strumenti
    "5. Foratura Asse": "5. Foratura Asse",                                                     # Comando 10 barra strumenti
    "6. Troncatura": "6. Troncatura",                                                           # Comando 11 barra strumenti
    "1. Simulazione 3D": "1. Simulazione 3D",                                                   # Comando 12 barra strumenti
    "2. Genera G-Code": "2. Genera G-Code"                                                      # Comando 13 barra strumenti
}                                                                                               # Fine dizionario Italiano

TERMINI_PAROLE_INTERE = []                                                                      # Nessuna sostituzione necessaria per l'Italiano


def traduci(testo):                                                                             # Restituisce il testo in Italiano senza alterazioni
    if not testo:                                                                               # Controlla se la stringa è vuota
        return testo                                                                            # Restituisce stringa vuota
    return TRADUZIONI.get(str(testo).strip(), testo)                                            # Restituisce il testo originale