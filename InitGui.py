import FreeCAD                                                                                  # Importa il modulo base di FreeCAD
import FreeCADGui                                                                               # Importa il modulo interfaccia grafica di FreeCAD


class LatheCAMWorkbench(FreeCADGui.Workbench):                                                  # Classe principale del Workbench Tornio CAM
    def __init__(self):                                                                         # Costruttore del Workbench
        import LatheResources                                                                   # Importato dentro il metodo per lo scope isolato di FreeCAD
        from LatheI18n import tr                                                                # Importa la funzione di traduzione
        LatheResources.ensure_workbench_folders()                                               # Crea subito tutte le cartelle librerie e le icone SVG
        self.__class__.MenuText = tr("WB_NAME")                                                 # Nome visibile nel selettore Workbench di FreeCAD
        self.__class__.ToolTip = tr("WB_TOOLTIP")                                               # Tooltip descrittivo del Workbench
        self.__class__.Icon = LatheResources.get_icon_path("lathe_workbench.svg", "Std_AxisCross") # Icona dedicata del Workbench

    def Initialize(self):                                                                       # Chiamato da FreeCAD quando si attiva il Workbench per la prima volta
        import LatheResources                                                                   # Importato dentro Initialize per lo scope isolato di FreeCAD
        import LatheCommands                                                                    # Importa e registra tutti i comandi di tornitura
        from LatheI18n import tr                                                                # Importa il traduttore

        LatheResources.ensure_workbench_folders()                                               # Verifica nuovamente la presenza di tutte le cartelle

        self.cmd_setup = [                                                                      # Gruppo 1: Configurazione Macchina, Grezzo, Utensili e Torretta
            "Lathe_Setup",                                                                      # 1. Setup Macchina e WCS (G54..G59)
            "Lathe_Stock",                                                                      # 2. Grezzo, Autocentrante/Griffe e Contropunta
            "Lathe_ToolManager",                                                                # 3. Magazzino Utensili e Tecnologia
            "Lathe_Turret"                                                                      # 4. Torretta Porta-Utensili 3D e Collisioni
        ]                                                                                       # Fine gruppo Setup

        self.cmd_ops = [                                                                        # Gruppo 2: Cicli di Lavorazione Tornio
            "Lathe_Roughing",                                                                   # Sgrossatura / Sfacciatura
            "Lathe_Finishing",                                                                  # Finitura Profilo
            "Lathe_Grooving",                                                                   # Gola / Scarico
            "Lathe_Threading",                                                                  # Filettatura
            "Lathe_Drilling",                                                                   # Foratura / Maschiatura
            "Lathe_Parting"                                                                     # Troncatura Pezzo
        ]                                                                                       # Fine gruppo Lavorazioni

        self.cmd_sim = [                                                                        # Gruppo 3: Simulazione e Post-Processor G-Code
            "Lathe_Simulation",                                                                 # Simulazione Cinematica 3D
            "Lathe_PostProcess"                                                                 # Esportazione G-Code ISO
        ]                                                                                       # Fine gruppo Simulazione

        self.appendToolbar(tr("TOOLBAR_SETUP"), self.cmd_setup)                                 # Crea la barra strumenti Setup Macchina
        self.appendToolbar(tr("TOOLBAR_OPS"), self.cmd_ops)                                     # Crea la barra strumenti Lavorazioni
        self.appendToolbar(tr("TOOLBAR_SIM"), self.cmd_sim)                                     # Crea la barra strumenti Verifica e G-Code

        menu_completo = self.cmd_setup + ["Separator"] + self.cmd_ops + ["Separator"] + self.cmd_sim # Unisce i comandi con separatori per il menu
        self.appendMenu(tr("MENU_MAIN"), menu_completo)                                         # Crea il menu principale "Tornio CAM" nella barra in alto

    def Activated(self):                                                                        # Chiamato ogni volta che si entra nel Workbench
        if FreeCAD.ActiveDocument is None:                                                      # Se non c'è ancora nessun documento aperto
            FreeCAD.Console.PrintMessage("Tornio CAM pronto. Apri o crea un documento per iniziare il Setup.\n")

    def Deactivated(self):                                                                      # Chiamato quando si passa a un altro Workbench
        return                                                                                  # Nessuna operazione speciale richiesta

    def GetClassName(self):                                                                     # Specifica il tipo di Workbench C++ sottostante
        return "Gui::PythonWorkbench"                                                           # Workbench Python standard


FreeCADGui.addWorkbench(LatheCAMWorkbench())                                                    # Registra ufficialmente il Workbench in FreeCAD