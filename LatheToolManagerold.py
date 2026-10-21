import FreeCAD                                                          
import FreeCADGui                                                       
import Part                                                             
from PySide import QtCore, QtGui                                        
import math                                                             
try:                                                                    
    from PySide import QtWidgets                                        
except ImportError:                                                     
    QtWidgets = QtGui                                                   
import ImportGui                                                        

class LatheToolManager:                                                 
    def __init__(self):                                                 
        self.form = QtWidgets.QWidget()                                 
        self.layout = QtWidgets.QVBoxLayout(self.form)                  
        
        # --- DATI GENERALI ---
        self.grp_def = QtWidgets.QGroupBox("Dati Generali Utensile")    
        self.lyt_def = QtWidgets.QFormLayout(self.grp_def)              
        self.name_input = QtWidgets.QLineEdit("Utensile Sgrosso 1")     
        self.stat_combo = QtWidgets.QComboBox()                         
        for i in range(1, 9): self.stat_combo.addItem(f"T{i:02d}")      
        self.lyt_def.addRow("Nome:", self.name_input)                   
        self.lyt_def.addRow("Stazione:", self.stat_combo)               
        self.layout.addWidget(self.grp_def)                             
        
        self.tabs = QtWidgets.QTabWidget()                              
        
        # --- SCHEDA 1: GENERAZIONE STANDARD ---
        self.tab_std = QtWidgets.QWidget()                              
        self.lyt_std = QtWidgets.QVBoxLayout(self.tab_std)              
        
        # Selezione del Tipo di Utensile
        self.grp_tipo = QtWidgets.QGroupBox("Categoria Lavorazione")
        self.lyt_tipo = QtWidgets.QVBoxLayout(self.grp_tipo)
        self.tool_type_combo = QtWidgets.QComboBox()
        self.tool_type_combo.addItems(["Esterno (ISO)", "Bareno (Interno)", "Punta da Trapano", "Fresa", "Maschio"])
        self.lyt_tipo.addWidget(self.tool_type_combo)
        self.lyt_std.addWidget(self.grp_tipo)
        
        self.grp_geo = QtWidgets.QGroupBox("Geometria Inserto (ISO)")   
        self.lyt_geo = QtWidgets.QFormLayout(self.grp_geo)              
        self.shape_combo = QtWidgets.QComboBox()                        
        self.shape_combo.addItems(["Rombico 80° (C)", "Rombico 55° (D)", "Triangolare (T)", "Quadrato (S)"]) 
        self.rad_combo = QtWidgets.QComboBox()                          
        self.rad_combo.addItems(["0.2", "0.4", "0.8", "1.2"])           
        self.hand_combo = QtWidgets.QComboBox()                         
        self.hand_combo.addItems(["Destro (R)", "Sinistro (L)", "Neutro (N)"]) 
        self.rot_input = QtWidgets.QDoubleSpinBox()                     
        self.rot_input.setRange(-180.0, 180.0); self.rot_input.setValue(93.0)
        
        self.lyt_geo.addRow("Forma:", self.shape_combo)                 
        self.lyt_geo.addRow("Raggio (mm):", self.rad_combo)             
        self.lyt_geo.addRow("Verso:", self.hand_combo)                  
        self.lyt_geo.addRow("Angolo Reg. (deg):", self.rot_input)       
        self.lyt_std.addWidget(self.grp_geo)                            
        
        # Nuove Dimensioni Indipendenti
        self.grp_dim = QtWidgets.QGroupBox("Dimensioni Corpo Utensile")          
        self.lyt_dim = QtWidgets.QFormLayout(self.grp_dim)              
        
        self.w_input = QtWidgets.QDoubleSpinBox()                       
        self.w_input.setRange(1.0, 100.0); self.w_input.setValue(10.0)  # Larghezza/Diametro
        self.h_input = QtWidgets.QDoubleSpinBox()                       
        self.h_input.setRange(1.0, 100.0); self.h_input.setValue(10.0)  # Altezza
        self.l_input = QtWidgets.QDoubleSpinBox()                       
        self.l_input.setRange(1.0, 500.0); self.l_input.setValue(100.0) # Lunghezza
        
        self.lbl_w = QtWidgets.QLabel("Larghezza (mm):")
        self.lbl_h = QtWidgets.QLabel("Altezza (mm):")
        self.lbl_l = QtWidgets.QLabel("Lunghezza (mm):")
        
        self.lyt_dim.addRow(self.lbl_w, self.w_input)            
        self.lyt_dim.addRow(self.lbl_h, self.h_input)              
        self.lyt_dim.addRow(self.lbl_l, self.l_input)              
        self.lyt_std.addWidget(self.grp_dim)                            
        self.tabs.addTab(self.tab_std, "Generazione Parametrica")          
        
        # --- SCHEDA 2: IMPORTAZIONE CUSTOM ---
        self.tab_cst = QtWidgets.QWidget()                              
        self.lyt_cst = QtWidgets.QVBoxLayout(self.tab_cst)              
        self.btn_import = QtWidgets.QPushButton("1. Importa File 3D (STEP/FCStd)") 
        self.btn_import.clicked.connect(self.importa_file)              
        self.lyt_cst.addWidget(self.btn_import)                         
        self.btn_set_insert = QtWidgets.QPushButton("2. Tagga Inserto da Selezione") 
        self.btn_set_insert.clicked.connect(self.tagga_inserto)         
        self.lyt_cst.addWidget(self.btn_set_insert)                     
        self.btn_set_zero = QtWidgets.QPushButton("3. Definisci Punta (Zero) da Vertice") 
        self.btn_set_zero.clicked.connect(self.definisci_punta)         
        self.lyt_cst.addWidget(self.btn_set_zero)                       
        self.lbl_status = QtWidgets.QLabel("Stato: In attesa di importazione...") 
        self.lbl_status.setStyleSheet("color: #FFAA00; font-weight: bold;")
        self.lyt_cst.addWidget(self.lbl_status)                         
        self.tabs.addTab(self.tab_cst, "Importazione Custom")           
        self.layout.addWidget(self.tabs)                                
        
        # --- CONTROLLI DI ROTAZIONE E SPECCHIATURA ---
        self.grp_rot = QtWidgets.QGroupBox("Orientamento Spaziale 3D (Live Preview)")
        self.lyt_rot = QtWidgets.QFormLayout(self.grp_rot)
        
        self.chk_mir_x = QtWidgets.QCheckBox("Specchia Asse X (Ribalta)")
        self.chk_mir_y = QtWidgets.QCheckBox("Specchia Asse Y (Ribalta)")
        
        self.rx_spin = QtWidgets.QDoubleSpinBox(); self.rx_spin.setRange(-360, 360); self.rx_spin.setSingleStep(5)
        self.ry_spin = QtWidgets.QDoubleSpinBox(); self.ry_spin.setRange(-360, 360); self.ry_spin.setSingleStep(5)
        self.rz_spin = QtWidgets.QDoubleSpinBox(); self.rz_spin.setRange(-360, 360); self.rz_spin.setSingleStep(5)
        
        self.lyt_rot.addRow(self.chk_mir_x, self.chk_mir_y)
        self.lyt_rot.addRow("Rotazione Asse X (°):", self.rx_spin)
        self.lyt_rot.addRow("Rotazione Asse Y (°):", self.ry_spin)
        self.lyt_rot.addRow("Rotazione Asse Z (°):", self.rz_spin)
        self.layout.addWidget(self.grp_rot)
        self.form.setLayout(self.layout)                                
        
        doc = FreeCAD.ActiveDocument
        self.preview_group = doc.addObject("App::DocumentObjectGroup", "Anteprima_Utensile_TMP")
        self.preview_group.Label = "ANTEPRIMA UTENSILE (Provvisorio)"
        
        self.oggetti_importati_dati = [] 
        self.is_updating = False         
        
        self.insert_tagged = False
        self.vertex_defined = False
        
        # Segnali UI
        self.tool_type_combo.currentIndexChanged.connect(self.aggiorna_ui_tipo)
        self.shape_combo.currentIndexChanged.connect(self.trigger_update)
        self.hand_combo.currentIndexChanged.connect(self.trigger_update)
        self.rot_input.valueChanged.connect(self.trigger_update)
        self.w_input.valueChanged.connect(self.trigger_update)
        self.h_input.valueChanged.connect(self.trigger_update)
        self.l_input.valueChanged.connect(self.trigger_update) # Nuovo segnale lunghezza
        self.rx_spin.valueChanged.connect(self.trigger_update)
        self.ry_spin.valueChanged.connect(self.trigger_update)
        self.rz_spin.valueChanged.connect(self.trigger_update)
        self.chk_mir_x.stateChanged.connect(self.trigger_update)
        self.chk_mir_y.stateChanged.connect(self.trigger_update)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        self.aggiorna_ui_tipo()
        self.aggiorna_stato_controlli()
        self.trigger_update()

    def aggiorna_ui_tipo(self):
        tipo = self.tool_type_combo.currentText()
        if tipo == "Esterno (ISO)":
            self.grp_geo.setVisible(True)
            self.lbl_h.setVisible(True); self.h_input.setVisible(True)
            self.lbl_w.setText("Larghezza (mm):")
            self.lbl_h.setText("Altezza (mm):")
            self.lbl_l.setText("Lunghezza (mm):")
        elif tipo == "Bareno (Interno)":
            self.grp_geo.setVisible(True)
            self.lbl_h.setVisible(False); self.h_input.setVisible(False)
            self.lbl_w.setText("Diametro Gambo (mm):")
            self.lbl_l.setText("Lunghezza (mm):")
        else:
            self.grp_geo.setVisible(False)
            self.lbl_h.setVisible(False); self.h_input.setVisible(False)
            self.lbl_w.setText("Diametro Punta/Fresa (mm):")
            self.lbl_l.setText("Lunghezza Totale (mm):")
        self.trigger_update()
        
    def on_tab_changed(self, index):
        self.aggiorna_stato_controlli()
        self.trigger_update()
        
    def aggiorna_stato_controlli(self):
        if self.tabs.currentIndex() == 0:
            self.grp_rot.setEnabled(True)
        else:
            self.grp_rot.setEnabled(self.vertex_defined)

    def trigger_update(self, *args):
        if not self.is_updating:
            self.is_updating = True
            self.aggiorna_anteprima_live()
            self.is_updating = False

    def calcola_rotazione_indipendente(self):
        rot_x = FreeCAD.Rotation(FreeCAD.Vector(1,0,0), self.rx_spin.value())
        rot_y = FreeCAD.Rotation(FreeCAD.Vector(0,1,0), self.ry_spin.value())
        rot_z = FreeCAD.Rotation(FreeCAD.Vector(0,0,1), self.rz_spin.value())
        return rot_x * rot_y * rot_z

    def aggiorna_anteprima_live(self):                                  
        doc = FreeCAD.ActiveDocument
        if doc is None: return
        
        rot_manuale = self.calcola_rotazione_indipendente()
        
        for name in ["Anteprima_Inserto", "Anteprima_Gambo"]:
            obj = doc.getObject(name)
            if obj: doc.removeObject(name)
            
        if self.tabs.currentIndex() == 0:                               
            for item in self.oggetti_importati_dati:
                if item[0]: item[0].Visibility = False
            
            # Legge le tre misure
            w = self.w_input.value()
            h = self.h_input.value() if self.h_input.isVisible() else w # Se H è nascosto usa W (cilindro)
            l = self.l_input.value()
            tipo = self.tool_type_combo.currentText()
            
            insert_shape = None
            gambo_finito = None
            
            if tipo in ["Esterno (ISO)", "Bareno (Interno)"]:
                rot = self.rot_input.value()
                orient = -1.0 if "Sinistro" in self.hand_combo.currentText() else 1.0
                shape_txt = self.shape_combo.currentText()
                L_ins = 8.0 ; p1 = FreeCAD.Vector(0,0,0)
                if "Quadrato" in shape_txt:
                    wire = Part.makePolygon([p1, FreeCAD.Vector(L_ins, 0, 0), FreeCAD.Vector(L_ins, -L_ins, 0), FreeCAD.Vector(0, -L_ins, 0), p1])
                elif "Triangolare" in shape_txt:
                    wire = Part.makePolygon([p1, FreeCAD.Vector(L_ins, 0, 0), FreeCAD.Vector(L_ins/2, -L_ins * math.sin(math.radians(60)), 0), p1])
                elif "55" in shape_txt: 
                    wire = Part.makePolygon([p1, FreeCAD.Vector(L_ins, 0, 0), FreeCAD.Vector(L_ins + L_ins*math.cos(math.radians(55)), -L_ins*math.sin(math.radians(55)), 0), FreeCAD.Vector(L_ins*math.cos(math.radians(55)), -L_ins*math.sin(math.radians(55)), 0), p1])
                else: 
                    wire = Part.makePolygon([p1, FreeCAD.Vector(L_ins, 0, 0), FreeCAD.Vector(L_ins + L_ins*math.cos(math.radians(80)), -L_ins*math.sin(math.radians(80)), 0), FreeCAD.Vector(L_ins*math.cos(math.radians(80)), -L_ins*math.sin(math.radians(80)), 0), p1])
                    
                face = Part.Face(wire)
                face.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), -(rot - 90.0) * orient)
                insert_shape = face.extrude(FreeCAD.Vector(0, 0, -3.0))
                
                if tipo == "Esterno (ISO)":
                    pedistallo = face.extrude(FreeCAD.Vector(0, 0, -h))
                    # L, W, H per creare il solido indipendente
                    barra_lunga = Part.makeBox(l, w, h, FreeCAD.Vector(0, -w, -h))
                    gambo_finito = barra_lunga.fuse(pedistallo)
                    
                    fresa_tasca = face.extrude(FreeCAD.Vector(0, 0, 10.0))
                    fresa_tasca.translate(FreeCAD.Vector(0, 0, -3.0))
                    try: gambo_finito = gambo_finito.cut(fresa_tasca)
                    except: pass
                    
                    insert_shape.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), -90)
                    gambo_finito.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), -90)
                    
                elif tipo == "Bareno (Interno)":
                    pedistallo = face.extrude(FreeCAD.Vector(0, 0, -w))
                    # Cilindro diametro W e lunghezza L
                    barra_lunga = Part.makeCylinder(w/2.0, l, FreeCAD.Vector(0, -w/2.0, -w/2.0), FreeCAD.Vector(1,0,0))
                    gambo_finito = barra_lunga.fuse(pedistallo)
                    
                    fresa_tasca = face.extrude(FreeCAD.Vector(0, 0, 10.0))
                    fresa_tasca.translate(FreeCAD.Vector(0, 0, -3.0))
                    try: gambo_finito = gambo_finito.cut(fresa_tasca)
                    except: pass
                    
                    insert_shape.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), -90)
                    gambo_finito.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0), -90)
                    insert_shape.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,1,0), -90)
                    gambo_finito.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,1,0), -90)

            elif tipo == "Punta da Trapano":
                D = w; L = l
                tip_h = (D/2.0) / math.tan(math.radians(118/2.0)) 
                cone = Part.makeCone(0, D/2.0, tip_h, FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1))
                cyl = Part.makeCylinder(D/2.0, L, FreeCAD.Vector(0,0,tip_h), FreeCAD.Vector(0,0,1))
                gambo_finito = cone.fuse(cyl)
                
            elif tipo == "Fresa":
                D = w; L = l
                gambo_finito = Part.makeCylinder(D/2.0, L, FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1))
                
            elif tipo == "Maschio":
                D = w; L = l
                tip_h = D * 0.5
                cone = Part.makeCone(D/4.0, D/2.0, tip_h, FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1))
                cyl = Part.makeCylinder(D/2.0, L, FreeCAD.Vector(0,0,tip_h), FreeCAD.Vector(0,0,1))
                gambo_finito = cone.fuse(cyl)
                
            # APPLICA SPECCHIATURA E ROTAZIONE MANUALE SUL GENERATO
            if insert_shape:
                if self.chk_mir_x.isChecked(): insert_shape = insert_shape.mirror(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0))
                if self.chk_mir_y.isChecked(): insert_shape = insert_shape.mirror(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,1,0))
                insert_shape.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0), rot_manuale) * insert_shape.Placement
                insert_obj = doc.addObject("Part::Feature", "Anteprima_Inserto")
                insert_obj.Shape = insert_shape
                insert_obj.ViewObject.ShapeColor = (0.9, 0.7, 0.1)
                self.preview_group.addObject(insert_obj)
                
            if gambo_finito:
                if self.chk_mir_x.isChecked(): gambo_finito = gambo_finito.mirror(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0))
                if self.chk_mir_y.isChecked(): gambo_finito = gambo_finito.mirror(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,1,0))
                gambo_finito.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0), rot_manuale) * gambo_finito.Placement
                gambo_obj = doc.addObject("Part::Feature", "Anteprima_Gambo")
                gambo_obj.Shape = gambo_finito
                if tipo in ["Punta da Trapano", "Fresa", "Maschio"]: gambo_obj.ViewObject.ShapeColor = (0.8, 0.8, 0.8) 
                else: gambo_obj.ViewObject.ShapeColor = (0.35, 0.35, 0.35)
                self.preview_group.addObject(gambo_obj)
            
        else:                                                           
            for item in self.oggetti_importati_dati:
                obj, forma_orig, pos_orig = item
                if obj:
                    obj.Visibility = True 
                    if forma_orig is not None:
                        nuova_forma = forma_orig.copy()
                        if self.chk_mir_x.isChecked(): nuova_forma = nuova_forma.mirror(FreeCAD.Vector(0,0,0), FreeCAD.Vector(1,0,0))
                        if self.chk_mir_y.isChecked(): nuova_forma = nuova_forma.mirror(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,1,0))
                        obj.Shape = nuova_forma
                    if hasattr(obj, "Placement"):
                        obj.Placement = FreeCAD.Placement(FreeCAD.Vector(0,0,0), rot_manuale) * pos_orig
                    
        doc.recompute()

    def importa_file(self):                                             
        doc = FreeCAD.ActiveDocument                                    
        if not doc: return                                              
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Seleziona File Utensile", "", "File 3D (*.step *.stp *.iges *.igs *.FCStd)") 
        if file_path:                                                   
            try:
                self.insert_tagged = False
                self.vertex_defined = False
                self.aggiorna_stato_controlli()
                
                self.is_updating = True
                self.rx_spin.setValue(0); self.ry_spin.setValue(0); self.rz_spin.setValue(0)
                self.chk_mir_x.setChecked(False); self.chk_mir_y.setChecked(False)
                self.is_updating = False
                
                oggetti_prima = set(doc.Objects)                        
                ImportGui.insert(file_path, doc.Name)                   
                oggetti_dopo = set(doc.Objects)                         
                nuovi_oggetti = list(oggetti_dopo - oggetti_prima)
                
                forme_estratte = []
                for obj in nuovi_oggetti:
                    try:
                        if hasattr(obj, "Shape") and obj.Shape and hasattr(obj.Shape, "Volume") and obj.Shape.Volume > 0:
                            forma = obj.Shape.copy()
                            if hasattr(obj, "getGlobalPlacement"): forma.Placement = obj.getGlobalPlacement()
                            elif hasattr(obj, "Placement"): forma.Placement = obj.Placement
                            colore = obj.ViewObject.ShapeColor if hasattr(obj, "ViewObject") and hasattr(obj.ViewObject, "ShapeColor") else (0.5, 0.5, 0.5)
                            forme_estratte.append((forma, colore))
                    except: pass
                
                for obj in nuovi_oggetti:
                    try: doc.removeObject(obj.Name)
                    except: pass
                
                for old_item in self.oggetti_importati_dati: 
                    try: doc.removeObject(old_item[0].Name)
                    except: pass
                self.oggetti_importati_dati.clear()
                
                for idx, (forma, colore) in enumerate(forme_estratte):
                    new_obj = doc.addObject("Part::Feature", f"Custom_Solid_{idx}")
                    new_obj.Shape = forma
                    new_obj.ViewObject.ShapeColor = colore
                    self.preview_group.addObject(new_obj)
                    self.oggetti_importati_dati.append([new_obj, forma.copy(), FreeCAD.Placement()])
                    
                self.lbl_status.setText("Stato: STEP Bonificato. 2. Tagga l'inserto (metallo).") 
                self.trigger_update()
            except Exception as e:
                FreeCAD.Console.PrintError(f"Errore importazione: {e}\n") 

    def tagga_inserto(self):                                            
        sel = FreeCADGui.Selection.getSelection()                       
        if not sel:                                                     
            self.lbl_status.setText("Errore: Seleziona l'inserto nel 3D!") 
            return
        custom_insert = sel[0]                                          
        custom_insert.ViewObject.ShapeColor = (0.9, 0.7, 0.1)           
        
        self.insert_tagged = True 
        self.lbl_status.setText(f"Stato: Inserto [{custom_insert.Label}] taggato. Ora 3. Definisci Punta.") 

    def definisci_punta(self):
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
        
        for idx, item in enumerate(self.oggetti_importati_dati):                                     
            obj_rif, forma_orig, pos_orig = item
            nuova_pos = FreeCAD.Placement(pos_orig.Base - punta_pt, pos_orig.Rotation)
            self.oggetti_importati_dati[idx] = (obj_rif, forma_orig, nuova_pos)
                
        self.vertex_defined = True 
        self.aggiorna_stato_controlli()
        
        self.lbl_status.setText("Stato: Punta azzerata! Usa Rotazione e Specchio.") 
        self.trigger_update()

    def getStandardButtons(self):                                       
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel 

    def accept(self):                                                   
        doc = FreeCAD.ActiveDocument                                    
        nome_base = self.name_input.text()                              
        nome_int = nome_base.replace(" ", "_")                          
        lib_group = doc.getObject("Libreria_Utensili")                  
        if not lib_group:
            lib_group = doc.addObject("App::DocumentObjectGroup", "Libreria_Utensili") 
            lib_group.Label = "Magazzino Utensili"                      
            
        tool_group = doc.addObject("App::DocumentObjectGroup", nome_int) 
        tool_group.Label = nome_base                                    
        lib_group.addObject(tool_group)                                 
        
        if self.tabs.currentIndex() == 0:
            for name in ["Anteprima_Inserto", "Anteprima_Gambo"]:
                obj = doc.getObject(name)
                if obj:
                    tool_group.addObject(obj)
                    obj.Label = obj.Label.replace("Anteprima_", "")
            for item in self.oggetti_importati_dati:
                if item[0]: 
                    try: doc.removeObject(item[0].Name)
                    except: pass
        else:
            for item in self.oggetti_importati_dati:
                if item[0]: tool_group.addObject(item[0])
                
        if doc.getObject(self.preview_group.Name):
            doc.removeObject(self.preview_group.Name) 
            
        tool_group.addProperty("App::PropertyString", "Stazione", "Dati", "Stazione").Stazione = self.stat_combo.currentText()
        tipo = self.tool_type_combo.currentText() if self.tabs.currentIndex() == 0 else "Custom"
        tool_group.addProperty("App::PropertyString", "Tipo", "Dati", "Tipo Utensile").Tipo = tipo
        
        doc.recompute()                                                 
        FreeCADGui.Control.closeDialog()                                
        return True

    def reject(self):                                                   
        doc = FreeCAD.ActiveDocument
        if self.preview_group:                                          
            for obj in self.preview_group.Group: 
                try: doc.removeObject(obj.Name)
                except: pass
            doc.removeObject(self.preview_group.Name)
        doc.recompute()
        FreeCADGui.Control.closeDialog()                                
        return True