class Tool:                                             # Classe base che rappresenta un utensile da tornio generico
    def __init__(self, name, tool_number):              # Metodo eseguito quando si crea un nuovo utensile
        self.name = name                                # Salva il nome descrittivo (es. "Sgrossatore Esterno")
        self.tool_number = tool_number                  # Salva il numero identificativo dell'utensile
        self.is_live = False                            # Imposta di default l'utensile come NON motorizzato

class LiveTool(Tool):                                   # Classe per l'utensile motorizzato (eredita da Tool)
    def __init__(self, name, tool_number, max_rpm):     # Metodo eseguito per creare l'utensile motorizzato
        super().__init__(name, tool_number)             # Richiama l'inizializzazione della classe base Tool
        self.is_live = True                             # Sovrascrive la proprietà, impostandolo come motorizzato
        self.max_rpm = max_rpm                          # Salva il limite massimo di giri per questo utensile

class Turret:                                           # Classe che gestisce fisicamente la torretta del tornio
    def __init__(self, stations=8):                     # Metodo di avvio (imposta 8 stazioni di default)
        self.stations = stations                        # Salva la capacità totale della torretta
        self.slots = {}                                 # Crea un dizionario (una lista con chiavi) per le postazioni
        for i in range(1, stations + 1):                # Avvia un ciclo per contare da 1 al numero di stazioni
            self.slots[i] = None                        # Inizializza ogni stazione definendola vuota (None)

    def add_tool(self, station, tool):                  # Metodo per "montare" virtualmente un utensile in torretta
        if 1 <= station <= self.stations:               # Verifica che il numero di stazione richiesto esista
            self.slots[station] = tool                  # Inserisce l'oggetto utensile nella postazione corretta
        else:                                           # Se la stazione richiesta è fuori dai limiti
            print("Errore: Stazione non valida")        # Stampa un avviso nella console

    def get_mach3_code(self, station):                  # Metodo per generare il codice utensile per Mach3
        tool = self.slots.get(station)                  # Va a leggere cosa c'è nella stazione specificata
        if tool:                                        # Se la stazione non è vuota
            t_num = str(tool.tool_number).zfill(2)      # Trasforma il numero in testo aggiungendo lo zero (es. 1 -> 01)
            return f"T{t_num}{t_num}"                   # Mach3 richiede T + Num Utensile + Num Offset (es. T0101)
        return "T0000"                                  # Se la stazione è vuota, restituisce un codice di azzeramento