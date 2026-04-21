# main.py
import sys
import datetime
import csv
import time
import os
import math
import random 
import json 
import serial.tools.list_ports
import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QGroupBox, QFormLayout, QComboBox, 
                             QMessageBox, QCheckBox, QProgressDialog, QTabWidget,
                             QScrollArea, QFrame, QFileDialog)
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot, QLocale, Qt, QUrl, QTimer, QRegularExpression
from PyQt6.QtGui import QDoubleValidator, QFont, QDesktopServices, QRegularExpressionValidator

# --- SÜRÜCÜLER ---
from rs_drivers import SignalGeneratorDriver, SpectrumAnalyzerDriver
from dut_driver import DutHandler
from ps_driver import PowerSupplyDriver 

# ==========================================
# AYARLAR
# ==========================================
REFRESH_RATE = 0.1
CURRENT_SIGNAL = { "active": False, "freq": 0.0, "power": -140.0 }

# --- RENK PALETİ ---
STYLE_GREEN = "background-color: #d1e7dd; color: #146c43; font-weight: bold;" 
STYLE_RED   = "background-color: #f8d7da; color: #721c24; font-weight: bold;" 
STYLE_BLUE  = "background-color: #cfe2ff; color: #084298; font-weight: bold;" 
STYLE_YELLOW= "background-color: #fff3cd; color: #664d03; font-weight: bold;" 
STYLE_GRAY  = "background-color: #e2e3e5; color: #000000; font-weight: bold;" 

# ==========================================
# CUSTOM WIDGET: UDEMY STYLE TEST STEP
# ==========================================
class TestStepWidget(QFrame):
    toggled_signal = pyqtSignal(int, bool)
    set_params_signal = pyqtSignal() 
    
    def __init__(self, index, action, expected, attachments, step_data=""):
        super().__init__()
        self.step_index = index
        self.setStyleSheet("TestStepWidget { background-color: #eaf2f8; border-radius: 8px; margin-bottom: 6px; }")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        self.header_layout = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        
        self.style_active = "text-align: left; background: transparent; border: none; font-weight: bold; color: #084298;"
        self.style_disabled = "text-align: left; background: transparent; border: none; font-weight: bold; color: #adb5bd;" 
        
        self.btn_title = QPushButton(f"TEST ADIMI - {index}")
        self.btn_title.setStyleSheet(self.style_active)
        self.btn_title.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_title.clicked.connect(self.toggle_details)
        
        self.header_layout.addWidget(self.checkbox)
        self.header_layout.addWidget(self.btn_title, stretch=1)
        self.layout.addLayout(self.header_layout)

        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setContentsMargins(25, 0, 0, 5) 
        self.details_layout.setSpacing(5) 
        
        clean_action = str(action).strip()
        clean_expected = str(expected).strip()

        lbl_action = QLabel(f"<b>Adımlar:</b><br>{clean_action}")
        lbl_action.setWordWrap(True)
        lbl_action.setStyleSheet("color: #41464b; font-size: 12px; margin: 0px; padding: 0px;")
        self.details_layout.addWidget(lbl_action)

        lbl_exp = QLabel(f"<b>Beklenen Sonuç:</b><br>{clean_expected}")
        lbl_exp.setWordWrap(True)
        lbl_exp.setStyleSheet("color: #41464b; font-size: 12px; margin: 0px; padding: 0px;")
        self.details_layout.addWidget(lbl_exp)

        if attachments and len(attachments) > 0:
            lbl_att = QLabel("<b>Ekler:</b>")
            lbl_att.setStyleSheet("color: #41464b; font-size: 12px; margin: 0px; padding: 0px;")
            self.details_layout.addWidget(lbl_att)
            for att in attachments:
                att_name = att.get("filename", "Bilinmeyen Dosya")
                att_path = att.get("local_path", "")
                btn_file = QPushButton(f"📎 {att_name}")
                btn_file.setStyleSheet("text-align: left; background: transparent; border: none; color: #0d6efd; text-decoration: underline; font-size: 11px; margin: 0px; padding: 0px;")
                btn_file.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_file.clicked.connect(lambda checked=False, path=att_path: self.open_attachment(path))
                self.details_layout.addWidget(btn_file)

        self.btn_set_params = QPushButton("⚙️ ARAYÜZ PARAMETRELERİNİ OTOMATİK SET ET")
        self.btn_set_params.setStyleSheet("background-color: #fff3cd; color: #664d03; font-weight: bold; border-radius: 4px; padding: 6px; margin-top: 5px;")
        self.btn_set_params.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_set_params.clicked.connect(self.set_params_signal.emit)
        
        param_btn_layout = QHBoxLayout()
        param_btn_layout.addWidget(self.btn_set_params)
        param_btn_layout.addStretch() 
        self.details_layout.addLayout(param_btn_layout)

        if not str(step_data).strip():
            self.btn_set_params.setVisible(False)

        self.layout.addWidget(self.details_widget)
        self.details_widget.setVisible(False) 

    def toggle_details(self): self.details_widget.setVisible(not self.details_widget.isVisible())
    def on_checkbox_changed(self, state):
        is_checked = (state == Qt.CheckState.Checked.value)
        self.toggled_signal.emit(self.step_index, is_checked)
    def open_attachment(self, path):
        if not path: QMessageBox.warning(self, "Hata", "Dosya yolu tanımlanmamış."); return
        full_path = os.path.abspath(path)
        if os.path.exists(full_path): QDesktopServices.openUrl(QUrl.fromLocalFile(full_path))
        else: QMessageBox.warning(self, "Hata", f"Dosya bulunamadı:\n{full_path}")
    def set_step_enabled(self, is_enabled):
        self.setEnabled(is_enabled)
        self.btn_title.setStyleSheet(self.style_active if is_enabled else self.style_disabled)
        if not is_enabled: self.details_widget.setVisible(False)

# ==========================================
# WORKER 1: DUT
# ==========================================
class DutWorker(QThread):
    data_signal = pyqtSignal(dict)
    def __init__(self, port, baud, simulate=False):
        super().__init__()
        self.handler = DutHandler(port, baud, simulate)
        self.running = True
        self.simulate = simulate 
    def run(self):
        try:
            self.handler.connect()
            display_port = "SIM" if self.simulate else self.handler.port
            self.data_signal.emit({"source": "DUT", "event": "CONNECT", "ip_port": display_port, "msg": f"Bağlandı: {display_port}", "data_content": ""})
            while self.running:
                line = self.handler.read_line()
                if line: self.data_signal.emit({"source": "DUT", "event": "READ", "ip_port": display_port, "data_content": line, "msg": line})
                if not self.handler.simulation_mode: self.msleep(50)
            self.handler.close()
        except Exception as e: self.data_signal.emit({"source": "ERROR", "msg": str(e), "data_content": str(e)})
    def stop(self): self.running = False; self.quit(); self.wait()

# ==========================================
# WORKER 2: JENERATÖR
# ==========================================
class GeneratorWorker(QThread):
    log_signal = pyqtSignal(dict); error_signal = pyqtSignal(dict)
    def __init__(self, driver, mode, params):
        super().__init__()
        self.driver = driver
        self.mode = mode
        self.params = params
        self.running = True
        
    def update_virtual_signal(self, active, freq, power):
        global CURRENT_SIGNAL
        CURRENT_SIGNAL["active"] = active; CURRENT_SIGNAL["freq"] = float(freq); CURRENT_SIGNAL["power"] = float(power)
        
    def run(self):
        try:
            if self.mode == 'SINGLE':
                self.driver.apply_settings(self.params['freq'], self.params['power'])
                self.update_virtual_signal(True, self.params['freq'], self.params['power'])
                self.log_signal.emit({"source": "GENERATOR", "event": "SINGLE_SET", "msg": f"Tek Sinyal: {self.params['freq']}MHz @ {self.params['power']}dBm"})
            elif self.mode == 'PRESET':
                self.driver.preset()
                self.update_virtual_signal(False, 0, -140)
                self.log_signal.emit({"source": "GENERATOR", "event": "PRESET", "msg": "Preset atıldı."})
            elif self.mode == 'SWEEP':
                start, stop = float(self.params['start']), float(self.params['stop'])
                step, dwell = float(self.params['step']), float(self.params['dwell'])
                power = float(self.params['power'])
                self.log_signal.emit({"source": "GENERATOR", "event": "SWEEP_START", "msg": "Sweep Başladı"})
                current_freq = start
                while current_freq <= stop:
                    if not self.running: self.log_signal.emit({"source": "GENERATOR", "event": "SWEEP_STOP", "msg": "Sweep Durduruldu"}); break
                    self.driver.apply_settings(current_freq, power)
                    self.update_virtual_signal(True, current_freq, power)
                    self.log_signal.emit({"source": "GENERATOR", "event": "SWEEP_STEP", "freq": current_freq, "msg": f"Sweep: {current_freq} MHz"})
                    waited = 0
                    while waited < dwell:
                        if not self.running: break
                        time.sleep(0.1); waited += 0.1
                    current_freq += step
            elif self.mode == 'AM_SINE':
                freq = float(self.params['freq'])
                min_p, max_p = float(self.params['min_power']), float(self.params['max_power'])
                speed = float(self.params['speed'])
                self.log_signal.emit({"source": "GENERATOR", "event": "AM_START", "msg": "AM Başladı"})
                
                mid_val = (max_p + min_p) / 2
                amplitude = (max_p - min_p) / 2
                
                # --- ZAMANLAMA HATASI BURADA ÇÖZÜLDÜ ---
                start_time = time.time()
                
                while self.running:
                    # Gerçek geçen süreyi hesaplıyoruz
                    t = time.time() - start_time
                    
                    current_power = mid_val + amplitude * math.sin(speed * t)
                    self.driver.apply_settings(freq, f"{current_power:.2f}")
                    self.update_virtual_signal(True, freq, current_power)
                    self.log_signal.emit({"source": "GENERATOR", "event": "AM_STEP", "power": f"{current_power:.2f}", "msg": f"AM: {current_power:.2f} dBm"})
                    
                    # Sadece bekleme yapıyoruz, t'yi manuel artırmıyoruz
                    time.sleep(REFRESH_RATE)
                    
                self.log_signal.emit({"source": "GENERATOR", "event": "AM_STOP", "msg": "AM Durduruldu"})
        except Exception as e: self.error_signal.emit({"source": "ERROR", "msg": f"Gen Hatası: {e}"})
    def stop(self): self.running = False

# ==========================================
# WORKER 3: ANALİZÖR
# ==========================================
class AnalyzerWorker(QThread):
    log_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(dict)
    trace_signal = pyqtSignal(dict) 
    
    def __init__(self, driver, mode, params=None):
        super().__init__()
        self.driver = driver
        self.mode = mode
        self.params = params
        self.running = True
        self.needs_update = False 

    # SİMÜLASYON DEĞERLERİNİ CANLI SİNYAL İLE EZEN FONKSİYON
    def apply_simulation_effects(self, peak_x, peak_y, trace_y):
        global CURRENT_SIGNAL
        c = self.params['center']
        s = self.params['span']
        if s <= 0: s = 10.0
        
        if CURRENT_SIGNAL["active"]:
            gen_f = CURRENT_SIGNAL["freq"]
            gen_p = CURRENT_SIGNAL["power"]
            
            # Jeneratörün frekansı analizörün ekranındaysa, tepe noktasını AM gücüne eşitle
            if (c - s/2) <= gen_f <= (c + s/2):
                peak_x = gen_f
                peak_y = gen_p + random.uniform(-0.3, 0.3) # Ufak gürültü ekle
            else:
                peak_y = -110.0 + random.uniform(-2, 2)
        else:
            peak_y = -120.0 + random.uniform(-2, 2)
            
        return peak_x, peak_y, trace_y

    def run(self):
        try:
            if self.mode == 'PRESET':
                self.driver.preset()
                self.log_signal.emit({"source": "ANALYZER", "event": "PRESET", "msg": "Preset atıldı."})
                return
                
            if self.mode == 'SINGLE_SHOT':
                self.driver.apply_settings(self.params['center'], self.params['span'], self.params['ref'], self.params['rbw'])
                peak_x, peak_y = self.driver.get_peak_marker()
                trace_y = self.driver.get_trace_data()
                
                # Simülasyon modundaysa sahte veriyi Jeneratörün AM gücü ile değiştir
                if self.driver.simulate:
                    peak_x, peak_y, trace_y = self.apply_simulation_effects(peak_x, peak_y, trace_y)
                
                self.trace_signal.emit({
                    "center": self.params['center'], "span": self.params['span'], 
                    "peak_x": peak_x, "peak_y": peak_y, "trace_y": trace_y
                })
                self.log_signal.emit({"source": "ANALYZER", "event": "MEASURE", "msg": f"Tek Ölçüm: {peak_y:.2f} dBm @ {peak_x:.2f} MHz"})
                return
                
            elif self.mode == 'CONTINUOUS':
                self.log_signal.emit({"source": "ANALYZER", "event": "LOOP_START", "msg": "Sürekli Ölçüm Başladı..."})
                self.driver.apply_settings(self.params['center'], self.params['span'], self.params['ref'], self.params['rbw'])
                
                while self.running:
                    if self.needs_update:
                        self.driver.apply_settings(self.params['center'], self.params['span'], self.params['ref'], self.params['rbw'])
                        self.needs_update = False
                        
                    peak_x, peak_y = self.driver.get_peak_marker()
                    trace_y = self.driver.get_trace_data()
                    
                    # Simülasyon modundaysa sahte veriyi Jeneratörün AM gücü ile değiştir
                    if self.driver.simulate:
                        peak_x, peak_y, trace_y = self.apply_simulation_effects(peak_x, peak_y, trace_y)
                    
                    self.trace_signal.emit({
                        "center": self.params['center'], "span": self.params['span'], 
                        "peak_x": peak_x, "peak_y": peak_y, "trace_y": trace_y
                    })
                    
                    self.log_signal.emit({"source": "ANALYZER", "event": "MEASURE", "msg": f"Sürekli: {peak_y:.2f} dBm @ {peak_x:.2f} MHz"})
                    time.sleep(REFRESH_RATE)
        except Exception as e: self.error_signal.emit({"source": "ERROR", "msg": f"Spec Hatası: {e}"})
        
    def stop(self): self.running = False

# ==========================================
# MAIN GUI
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ATE POD Test Arayüzü")
        self.resize(1600, 950) 
        self.temp_filename = "temp_log_buffer.txt"
        self.metadata_path = "metadata.json" 
        self.temp_file_init() 
        
        self.sa_idn = "Bilinmiyor"
        self.gen_idn = "Bilinmiyor"
        self.current_json_data = None 
        
        central = QWidget()
        self.setCentralWidget(central)
        main_wrapper = QVBoxLayout(central)
        
        self.tabs = QTabWidget()
        main_wrapper.addWidget(self.tabs)

        # IP VALIDATOR
        ip_regex = QRegularExpression(r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
        ip_validator = QRegularExpressionValidator(ip_regex)

        # SEKME 1: ÖN KOŞULLAR
        self.tab_preconditions = QWidget()
        self.preconditions_layout = QVBoxLayout(self.tab_preconditions)
        self.tabs.addTab(self.tab_preconditions, "1. Ön Koşullar")
        
        file_select_layout = QHBoxLayout()
        self.btn_select_json = QPushButton("TEST SENARYOSU (JSON) SEÇ")
        self.btn_select_json.setStyleSheet(STYLE_BLUE)
        self.btn_select_json.clicked.connect(self.select_metadata_file)
        
        self.lbl_selected_json = QLabel("Seçilen Dosya: Yok")
        self.lbl_selected_json.setStyleSheet("font-size: 14px; font-weight: bold; color: #41464b;")
        
        file_select_layout.addWidget(self.btn_select_json)
        file_select_layout.addWidget(self.lbl_selected_json, stretch=1)
        self.preconditions_layout.addLayout(file_select_layout)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.preconditions_layout.addWidget(line)

        self.precond_dynamic_widget = QWidget()
        self.precond_dynamic_layout = QVBoxLayout(self.precond_dynamic_widget)
        self.precond_dynamic_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_precond = QScrollArea()
        scroll_precond.setWidgetResizable(True)
        scroll_precond.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_precond.setWidget(self.precond_dynamic_widget)
        self.preconditions_layout.addWidget(scroll_precond)

        self.btn_proceed = QPushButton("TÜM KOŞULLAR SAĞLANDI - TESTE BAŞLA")
        self.btn_proceed.setStyleSheet(STYLE_GRAY)
        self.btn_proceed.setEnabled(False)
        self.btn_proceed.setMinimumHeight(50)
        self.btn_proceed.clicked.connect(lambda: self.tabs.setCurrentIndex(1)) 
        self.preconditions_layout.addWidget(self.btn_proceed)

        self.precondition_checkboxes = []

        # SEKME 2: TEST PANELİ
        self.tab_test = QWidget()
        test_main_layout = QHBoxLayout(self.tab_test)
        self.tabs.addTab(self.tab_test, "2. Test Paneli")
        self.tabs.setTabEnabled(1, False)

        # SEKME 3: GRAFİK EKRANI
        self.tab_graph = QWidget()
        graph_main_layout = QVBoxLayout(self.tab_graph)
        self.tabs.addTab(self.tab_graph, "3. Grafik Görünümü")
        self.tabs.setTabEnabled(2, False)

        graph_top_layout = QHBoxLayout()
        self.lbl_graph_info = QLabel("<b>Merkez Frekans:</b> -- MHz  |  <b>Span:</b> -- MHz  |  <b>Peak:</b> -- dBm @ -- MHz")
        self.lbl_graph_info.setStyleSheet("font-size: 14px; background: #e9ecef; padding: 8px; border-radius: 4px; color: #212529;")
        
        self.btn_export_png = QPushButton("PNG OLARAK KAYDET")
        self.btn_export_png.setStyleSheet(STYLE_BLUE)
        self.btn_export_png.clicked.connect(self.export_graph_png)
        
        self.btn_export_csv = QPushButton("VERİYİ CSV KAYDET")
        self.btn_export_csv.setStyleSheet(STYLE_GREEN)
        self.btn_export_csv.clicked.connect(self.export_graph_csv)
        
        graph_top_layout.addWidget(self.lbl_graph_info, stretch=1)
        graph_top_layout.addWidget(self.btn_export_png)
        graph_top_layout.addWidget(self.btn_export_csv)
        graph_main_layout.addLayout(graph_top_layout)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w') 
        self.plot_widget.setTitle("RF Spektrum Çözümlemesi", color='k', size='14pt')
        self.plot_widget.setLabel('left', 'Genlik (Güç)', units='dBm', color='k')
        self.plot_widget.setLabel('bottom', 'Frekans', units='MHz', color='k')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()

        self.sa_curve = self.plot_widget.plot(pen=pg.mkPen('r', width=2), name="SA Ölçümü") 
        self.gen_marker = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('b', width=2, style=Qt.PenStyle.DashLine), label="GEN: {value:.2f} MHz", labelOpts={'position':0.9, 'color':'b', 'movable':True, 'fill':(255,255,255,200)})
        self.plot_widget.addItem(self.gen_marker)
        self.gen_marker.hide()

        graph_main_layout.addWidget(self.plot_widget)
        
        self.current_trace_x = []                       
        self.current_trace_y = []                       

        self.only_double = QDoubleValidator()
        self.only_double.setLocale(QLocale.c()) 
        
        left_layout = QVBoxLayout()
        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#controls_widget { background: transparent; }")
        
        controls_widget = QWidget()
        controls_widget.setObjectName("controls_widget") 
        controls_vbox = QVBoxLayout(controls_widget)
        controls_vbox.setContentsMargins(0,0,0,0)

        # 1. DUT 
        dut_grp = QGroupBox("1. DUT Bağlantısı"); dut_form = QFormLayout()
        self.combo_ports = QComboBox() 
        self.chk_sim_dut = QCheckBox("Simülasyon Modu"); self.chk_sim_dut.setChecked(True)
        self.btn_dut = QPushButton("BAĞLAN"); self.btn_dut.setStyleSheet(STYLE_GREEN); self.btn_dut.clicked.connect(self.toggle_dut)
        dut_form.addRow("Port Seçimi:", self.combo_ports); dut_form.addRow(self.chk_sim_dut); dut_form.addRow(self.btn_dut)
        dut_grp.setLayout(dut_form); controls_vbox.addWidget(dut_grp)

        # 2. GÜÇ KAYNAĞI
        ps_grp = QGroupBox("2. Güç Kaynağı")
        ps_form = QFormLayout()
        self.combo_ports_ps = QComboBox() 
        self.chk_sim_ps = QCheckBox("Simülasyon Modu"); self.chk_sim_ps.setChecked(True) 
        self.ps_volt = QLineEdit("12.0"); self.ps_volt.setValidator(self.only_double)
        self.ps_curr = QLineEdit("2.0"); self.ps_curr.setValidator(self.only_double)
        self.combo_ps_range = QComboBox(); self.combo_ps_range.addItems(["LOW (15V/7A)", "HIGH (30V/4A)"])
        
        ps_btn_layout1 = QHBoxLayout()
        self.btn_ps_connect = QPushButton("BAĞLAN"); self.btn_ps_connect.setStyleSheet(STYLE_GREEN); self.btn_ps_connect.clicked.connect(self.toggle_ps_connect)
        ps_btn_layout1.addWidget(self.btn_ps_connect)

        ps_btn_layout2 = QHBoxLayout()
        self.btn_ps_apply = QPushButton("SET DEĞERLERİ GÖNDER"); self.btn_ps_apply.setStyleSheet(STYLE_BLUE); self.btn_ps_apply.clicked.connect(self.ps_apply_values)
        ps_btn_layout2.addWidget(self.btn_ps_apply)

        ps_btn_layout3 = QHBoxLayout()
        self.btn_ps_out_on = QPushButton("OUTPUT ON"); self.btn_ps_out_on.setStyleSheet(STYLE_YELLOW); self.btn_ps_out_on.clicked.connect(lambda: self.ps_set_output(True))
        self.btn_ps_out_off = QPushButton("OUTPUT OFF"); self.btn_ps_out_off.setStyleSheet(STYLE_RED); self.btn_ps_out_off.clicked.connect(lambda: self.ps_set_output(False))
        ps_btn_layout3.addWidget(self.btn_ps_out_on); ps_btn_layout3.addWidget(self.btn_ps_out_off)
   
        self.btn_ps_err = QPushButton("HATA SORGULA"); self.btn_ps_err.setStyleSheet(STYLE_GRAY); self.btn_ps_err.clicked.connect(self.ps_get_error)
        self.lbl_ps_live_info = QLabel("<b>Voltaj:</b> -- V &nbsp;|&nbsp; <b>Akım:</b> -- A")
        self.lbl_ps_live_info.setStyleSheet("font-size: 13px; background: #e9ecef; padding: 6px; border-radius: 4px; color: #212529; text-align: center;")
        self.lbl_ps_live_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ps_form.addRow("Port:", self.combo_ports_ps); ps_form.addRow(self.chk_sim_ps); ps_form.addRow(ps_btn_layout1) 
        ps_form.addRow("Voltaj (V):", self.ps_volt); ps_form.addRow("Akım (A):", self.ps_curr); ps_form.addRow("Aralık:", self.combo_ps_range)
        ps_form.addRow(ps_btn_layout2); ps_form.addRow(ps_btn_layout3); ps_form.addRow(self.btn_ps_err); ps_form.addRow(self.lbl_ps_live_info) 
        ps_grp.setLayout(ps_form); controls_vbox.addWidget(ps_grp)

        # 3. JENERATÖR
        gen_grp = QGroupBox("3. Sinyal Jeneratörü"); gen_form = QFormLayout()
        self.ip_gen = QLineEdit("192.168.1.50"); self.ip_gen.setValidator(ip_validator)
        self.chk_sim_gen = QCheckBox("Simülasyon Modu"); self.chk_sim_gen.setChecked(False)
        self.combo_gen_conn = QComboBox(); self.combo_gen_conn.addItems(["INSTR", "hislip0", "inst0", "socket"])
        self.btn_gen_connect = QPushButton("BAĞLAN"); self.btn_gen_connect.setStyleSheet(STYLE_GREEN); self.btn_gen_connect.clicked.connect(self.toggle_gen_connect)

        self.combo_gen_mode = QComboBox(); self.combo_gen_mode.addItems(["Sabit Sinyal", "Sweep", "AM Modülasyon (Güç Değişimi)"])
        self.combo_gen_mode.currentIndexChanged.connect(self.update_gen_ui)
        self.freq_gen = QLineEdit("2400"); self.freq_gen.setValidator(self.only_double)
        self.pow_gen = QLineEdit("-10"); self.pow_gen.setValidator(self.only_double)
        self.sweep_start = QLineEdit("2400"); self.sweep_start.setValidator(self.only_double)
        self.sweep_stop = QLineEdit("2500"); self.sweep_stop.setValidator(self.only_double)
        self.sweep_step = QLineEdit("10"); self.sweep_step.setValidator(self.only_double)
        self.sweep_dwell = QLineEdit("0.5"); self.sweep_dwell.setValidator(self.only_double)
        self.am_min_pow = QLineEdit("-30"); self.am_min_pow.setValidator(self.only_double)
        self.am_max_pow = QLineEdit("-10"); self.am_max_pow.setValidator(self.only_double)
        self.am_speed = QLineEdit("1.0"); self.am_speed.setValidator(self.only_double)
        self.btn_gen_start = QPushButton("BAŞLAT"); self.btn_gen_start.setStyleSheet(STYLE_GREEN); self.btn_gen_start.clicked.connect(self.toggle_generator)
        
        gen_form.addRow("Cihaz IP:", self.ip_gen)
        gen_form.addRow("Bağlantı:", self.combo_gen_conn)
        gen_form.addRow(self.chk_sim_gen)
        gen_form.addRow(self.btn_gen_connect)
        gen_form.addRow("Mod Seçimi:", self.combo_gen_mode)
        gen_form.addRow("Frekans (MHz):", self.freq_gen); gen_form.addRow("Sabit Güç (dBm):", self.pow_gen)
        gen_form.addRow("Sweep Başlangıç (MHz):", self.sweep_start); gen_form.addRow("Sweep Bitiş (MHz):", self.sweep_stop)
        gen_form.addRow("Sweep Adım (MHz):", self.sweep_step); gen_form.addRow("Bekleme Süresi (s):", self.sweep_dwell)
        gen_form.addRow("AM Min Güç (dBm):", self.am_min_pow); gen_form.addRow("AM Max Güç (dBm):", self.am_max_pow)
        gen_form.addRow("AM Hızı (Rad/s):", self.am_speed); gen_form.addRow(self.btn_gen_start)
        gen_grp.setLayout(gen_form); controls_vbox.addWidget(gen_grp)

        # 4. ANALİZÖR
        sa_grp = QGroupBox("4. Spektrum Analizör"); sa_form = QFormLayout()
        self.ip_sa = QLineEdit("192.168.1.51"); self.ip_sa.setValidator(ip_validator)
        self.chk_sim_sa = QCheckBox("Simülasyon Modu"); self.chk_sim_sa.setChecked(False)
        self.combo_sa_conn = QComboBox(); self.combo_sa_conn.addItems(["INSTR", "hislip0", "inst0", "socket"])
        
        self.btn_sa_connect = QPushButton("BAĞLAN"); self.btn_sa_connect.setStyleSheet(STYLE_GREEN)
        self.btn_sa_connect.clicked.connect(self.toggle_sa_connect)
        
        self.sa_center = QLineEdit("2400"); self.sa_center.setValidator(self.only_double)
        self.sa_span = QLineEdit("10"); self.sa_span.setValidator(self.only_double)
        self.sa_ref = QLineEdit("0"); self.sa_ref.setValidator(self.only_double)
        self.sa_rbw = QLineEdit("100"); self.sa_rbw.setValidator(self.only_double)
        
        self.btn_sa_apply = QPushButton("AYARLARI UYGULA"); self.btn_sa_apply.setStyleSheet(STYLE_BLUE)
        self.btn_sa_apply.clicked.connect(self.apply_sa_settings)

        btn_layout = QHBoxLayout()
        self.btn_sa_single = QPushButton("TEK ÖLÇÜM"); self.btn_sa_single.setStyleSheet(STYLE_YELLOW); self.btn_sa_single.clicked.connect(lambda: self.run_analyzer('SINGLE_SHOT'))
        self.btn_sa_cont = QPushButton("SÜREKLİ ÖLÇÜM"); self.btn_sa_cont.setStyleSheet(STYLE_GREEN); self.btn_sa_cont.clicked.connect(self.toggle_continuous_measure)
        btn_layout.addWidget(self.btn_sa_single); btn_layout.addWidget(self.btn_sa_cont)
        
        sa_form.addRow("Cihaz IP:", self.ip_sa)
        sa_form.addRow("Bağlantı:", self.combo_sa_conn)
        sa_form.addRow(self.chk_sim_sa)
        sa_form.addRow(self.btn_sa_connect)
        sa_form.addRow("Center Freq (MHz):", self.sa_center); sa_form.addRow("Span (MHz):", self.sa_span)
        sa_form.addRow("Ref Level (dBm):", self.sa_ref); sa_form.addRow("RBW (kHz):", self.sa_rbw)
        sa_form.addRow(self.btn_sa_apply)
        sa_form.addRow(btn_layout)
        sa_grp.setLayout(sa_form); controls_vbox.addWidget(sa_grp)

        # 5. GLOBAL KONTROLLER
        glob_grp = QGroupBox("Genel Kontrol"); glob_lay = QVBoxLayout()
        self.btn_preset = QPushButton("TÜM CİHAZLARI SIFIRLA"); self.btn_preset.setStyleSheet(STYLE_RED); self.btn_preset.clicked.connect(self.preset_all_devices)
        self.btn_save = QPushButton("LOG CSV KAYDET"); self.btn_save.setStyleSheet(STYLE_BLUE); self.btn_save.clicked.connect(self.debug_log_save)
        self.btn_clr = QPushButton("EKRANI TEMİZLE"); self.btn_clr.setStyleSheet(STYLE_GRAY); self.btn_clr.clicked.connect(self.clear_display_log)
        self.chk_auto_clr = QCheckBox("Kaydettikten sonra temizle"); self.chk_auto_clr.setChecked(True)
        row_glob = QHBoxLayout(); row_glob.addWidget(self.btn_preset); row_glob.addWidget(self.btn_save); row_glob.addWidget(self.btn_clr)
        glob_lay.addLayout(row_glob); glob_lay.addWidget(self.chk_auto_clr)
        glob_grp.setLayout(glob_lay); controls_vbox.addWidget(glob_grp)
        
        controls_vbox.addStretch()
        controls_scroll.setWidget(controls_widget)
        left_layout.addWidget(controls_scroll)

        # --- SÜTUN 2: LOG EKRANI ---
        self.center_tabs = QTabWidget()
        self.tab_log = QWidget()
        log_lay = QVBoxLayout(self.tab_log)
        log_lay.setContentsMargins(0,0,0,0)
        self.log_area = QTextEdit(); self.log_area.setReadOnly(True)
        log_lay.addWidget(self.log_area)
        self.center_tabs.addTab(self.tab_log, "Log Ekranı")

        # --- SÜTUN 3: TEST ADIMLARI ---
        steps_grp = QGroupBox("Test Senaryosu (Adımlar)"); steps_layout = QVBoxLayout()
        self.steps_scroll = QScrollArea(); self.steps_scroll.setWidgetResizable(True)
        self.steps_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }") 
        self.steps_container = QWidget()
        self.steps_container.setStyleSheet("background: transparent;")
        self.steps_inner_layout = QVBoxLayout(self.steps_container)
        self.steps_inner_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.steps_scroll.setWidget(self.steps_container)
        steps_layout.addWidget(self.steps_scroll)
        steps_grp.setLayout(steps_layout)

        # 4 : 5 : 5
        test_main_layout.addLayout(left_layout, 4)
        test_main_layout.addWidget(self.center_tabs, 5)
        test_main_layout.addWidget(steps_grp, 5)

        # DRIVER MEMORY
        self.dut_thread = None; self.gen_worker = None; self.sa_worker = None
        self.preset_gen_worker = None; self.preset_sa_worker = None
        
        self.ps_driver = None; self.ps_is_connected = False 
        self.sa_driver = None; self.sa_is_connected = False
        self.gen_driver = None; self.gen_is_connected = False
        
        self.sa_current_params = {}
        self.step_widgets = [] 

        self.ps_monitor_timer = QTimer()
        self.ps_monitor_timer.timeout.connect(self.update_ps_live_info)
        
        self.port_update_timer = QTimer()
        self.port_update_timer.timeout.connect(self.check_and_update_ports)
        self.port_update_timer.start(1500)
        
        self.refresh_ports()
        self.update_gen_ui()
        self.load_metadata(None)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def _to_double(self, val_str):
        try: return float(val_str.replace(',', '.'))
        except: return 0.0

    def apply_test_parameters(self):
        if not self.current_json_data:
            QMessageBox.warning(self, "Hata", "Yüklü bir test senaryosu bulunamadı.")
            return
            
        try:
            tech_meta = self.current_json_data.get("metadata", {}).get("technical", {})
            param_meta = tech_meta.get("test_parametre_metadata", {})
            
            ps_v = float(param_meta.get("guc_kaynagi_voltaj_v", 12.0)) 
            ps_i = float(param_meta.get("guc_kaynagi_akim_a", 2.0))  
            
            freq_range = param_meta.get("frekans_araligi_mhz", {})
            start = float(freq_range.get("baslangic", 2400.0))
            stop = float(freq_range.get("bitis", 2500.0))
            step = float(freq_range.get("adim", 10.0))
            
            gen_power = float(param_meta.get("jenerator_cikis_gucu_dbm", -10.0))
            dwell_ms = float(param_meta.get("dwell_time_ms", 500.0))
            dwell_s = dwell_ms / 1000.0
            
            rbw_hz = float(param_meta.get("rbw_hz", 100000.0))
            rbw_khz = rbw_hz / 1000.0
            
            center = (start + stop) / 2.0
            span = (stop - start) + 50.0  
            if span <= 0: span = 100.0
            
            self.ps_volt.setText(str(ps_v))
            self.ps_curr.setText(str(ps_i))
            
            self.combo_gen_mode.setCurrentText("Sweep")
            self.update_gen_ui()
            self.sweep_start.setText(str(start))
            self.sweep_stop.setText(str(stop))
            self.sweep_step.setText(str(step))
            self.sweep_dwell.setText(str(dwell_s))
            self.pow_gen.setText(str(gen_power))
            self.freq_gen.setText(str(start)) 
            
            self.sa_center.setText(str(center))
            self.sa_span.setText(str(span))
            self.sa_rbw.setText(str(rbw_khz))
            
            self.debug_log({"source": "SYSTEM", "event": "INFO", "msg": "Parametreler otomatik dolduruldu."})
            QMessageBox.information(self, "Başarılı", "Parametreler arayüze başarıyla yüklendi.\nKomutları manuel olarak başlatabilirsiniz.")
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Parametreler ayrıştırılamadı:\n{str(e)}")

    def check_and_update_ports(self):
        current_ports = [p.device for p in serial.tools.list_ports.comports()]
        existing_ports = [self.combo_ports.itemText(i) for i in range(self.combo_ports.count())]
        
        if current_ports != existing_ports:
            selected_dut = self.combo_ports.currentText()
            selected_ps = self.combo_ports_ps.currentText()
            self.combo_ports.clear()
            self.combo_ports_ps.clear()
            for p in current_ports:
                self.combo_ports.addItem(p)
                self.combo_ports_ps.addItem(p)
            if selected_dut in current_ports: self.combo_ports.setCurrentText(selected_dut)
            if selected_ps in current_ports: self.combo_ports_ps.setCurrentText(selected_ps)

    # --- JENERATÖR BAĞLANTI FONKSİYONLARI ---
    def toggle_gen_connect(self):
        if not self.gen_is_connected:
            if not self.ip_gen.hasAcceptableInput() and not self.chk_sim_gen.isChecked():
                QMessageBox.warning(self, "Hata", "Geçersiz IP Formatı!"); return
                
            ip = self.ip_gen.text(); is_sim = self.chk_sim_gen.isChecked()
            conn_type = self.combo_gen_conn.currentText()
            
            self.gen_driver = SignalGeneratorDriver(ip, simulate=is_sim, conn_type=conn_type)
            try:
                self.gen_driver.connect()
                self.gen_idn = self.gen_driver.get_idn()
                self.debug_log({"source": "GENERATOR", "event": "CONNECT", "ip_port": ip, "idn": self.gen_idn, "msg": f"GEN Bağlandı. IDN: {self.gen_idn}"})
                
                self.btn_gen_connect.setText("BAĞLANTIYI KES"); self.btn_gen_connect.setStyleSheet(STYLE_RED)
                self.ip_gen.setEnabled(False); self.chk_sim_gen.setEnabled(False); self.combo_gen_conn.setEnabled(False)
                self.gen_is_connected = True
            except Exception as e:
                self.debug_log({"source": "ERROR", "msg": f"GEN Bağlantı Hatası: {e}"})
        else:
            if self.gen_worker and self.gen_worker.isRunning():
                self.toggle_generator() 
            if self.gen_driver:
                try: self.gen_driver.disconnect()
                except: pass
            
            self.debug_log({"source": "GENERATOR", "event": "DISCONNECT", "ip_port": self.ip_gen.text(), "msg": "GEN Bağlantısı Kesildi"})
            self.btn_gen_connect.setText("BAĞLAN"); self.btn_gen_connect.setStyleSheet(STYLE_GREEN)
            self.ip_gen.setEnabled(True); self.chk_sim_gen.setEnabled(True); self.combo_gen_conn.setEnabled(True)
            self.gen_is_connected = False; self.gen_driver = None

    # --- SA BAĞLANTI & CANLI AYAR FONKSİYONLARI ---
    def toggle_sa_connect(self):
        if not self.sa_is_connected:
            if not self.ip_sa.hasAcceptableInput() and not self.chk_sim_sa.isChecked():
                QMessageBox.warning(self, "Hata", "Geçersiz IP Formatı!"); return
                
            ip = self.ip_sa.text(); is_sim = self.chk_sim_sa.isChecked()
            conn_type = self.combo_sa_conn.currentText()
            
            self.sa_driver = SpectrumAnalyzerDriver(ip, simulate=is_sim, conn_type=conn_type)
            try:
                self.sa_driver.connect()
                self.sa_idn = self.sa_driver.get_idn()
                self.debug_log({"source": "ANALYZER", "event": "CONNECT", "ip_port": ip, "idn": self.sa_idn, "msg": f"SA Bağlandı. IDN: {self.sa_idn}"})
                
                self.btn_sa_connect.setText("BAĞLANTIYI KES"); self.btn_sa_connect.setStyleSheet(STYLE_RED)
                self.ip_sa.setEnabled(False); self.chk_sim_sa.setEnabled(False); self.combo_sa_conn.setEnabled(False)
                self.sa_is_connected = True
            except Exception as e:
                self.debug_log({"source": "ERROR", "msg": f"SA Bağlantı Hatası: {e}"})
        else:
            if self.sa_worker and self.sa_worker.isRunning():
                self.toggle_continuous_measure() 
            if self.sa_driver:
                try: self.sa_driver.disconnect()
                except: pass
            
            self.debug_log({"source": "ANALYZER", "event": "DISCONNECT", "ip_port": self.ip_sa.text(), "msg": "SA Bağlantısı Kesildi"})
            self.btn_sa_connect.setText("BAĞLAN"); self.btn_sa_connect.setStyleSheet(STYLE_GREEN)
            self.ip_sa.setEnabled(True); self.chk_sim_sa.setEnabled(True); self.combo_sa_conn.setEnabled(True)
            self.sa_is_connected = False; self.sa_driver = None

    def apply_sa_settings(self):
        if not self.sa_is_connected or not self.sa_driver:
            QMessageBox.warning(self, "Hata", "Önce Spektrum Analizöre Bağlanın!"); return
            
        c = self._to_double(self.sa_center.text())
        s = self._to_double(self.sa_span.text())
        r = self._to_double(self.sa_ref.text())
        rbw = self._to_double(self.sa_rbw.text())
        
        self.sa_current_params = {'center': c, 'span': s, 'ref': r, 'rbw': rbw}
        
        # Eğer okuma döngüsü açıksa, yeni parametreleri bayrakla thread'e gönder
        if self.sa_worker and self.sa_worker.isRunning():
            self.sa_worker.params = self.sa_current_params
            self.sa_worker.needs_update = True
        else:
            try:
                self.sa_driver.apply_settings(c, s, r, rbw)
                self.debug_log({"source": "ANALYZER", "event": "SETTINGS", "ip_port": self.ip_sa.text(), "msg": f"Ayarlar uygulandı: {c}MHz, {s}MHz span"})
            except Exception as e:
                self.debug_log({"source": "ERROR", "msg": f"SA Ayar Hatası: {e}"})

    # --- POWER SUPPLY FONKSİYONLARI ---
    def toggle_ps_connect(self):
        port = self.combo_ports_ps.currentText(); is_sim = self.chk_sim_ps.isChecked()
        if not self.ps_is_connected:
            self.ps_driver = PowerSupplyDriver(port, simulate=is_sim)
            try:
                self.ps_driver.connect()
                port_name = "SIM" if is_sim else port
                idn_info = "Bilinmiyor"
                try: idn_info = self.ps_driver.get_idn()
                except: idn_info = "SIM_PS_IDN" if is_sim else "IDN_ALINAMADI"
                
                self.debug_log({"source": "POWER_SUPPLY", "event": "CONNECT", "ip_port": port_name, "idn": idn_info, "msg": f"Güç Kaynağına Bağlandı. IDN: {idn_info}"})
                self.btn_ps_connect.setText("BAĞLANTIYI KES"); self.btn_ps_connect.setStyleSheet(STYLE_RED)
                self.combo_ports_ps.setEnabled(False); self.chk_sim_ps.setEnabled(False)
                self.ps_is_connected = True
                self.ps_monitor_timer.start(1000) 
            except Exception as e: self.debug_log({"source": "ERROR", "msg": f"PS Bağlantı Hatası: {e}"})
        else:
            if self.ps_driver:
                try: self.ps_driver.disconnect()
                except: pass
            port_name = "SIM" if self.chk_sim_ps.isChecked() else self.combo_ports_ps.currentText()
            self.debug_log({"source": "POWER_SUPPLY", "event": "DISCONNECT", "ip_port": port_name, "msg": "Bağlantı Kesildi"})
            self.btn_ps_connect.setText("BAĞLAN"); self.btn_ps_connect.setStyleSheet(STYLE_GREEN)
            self.combo_ports_ps.setEnabled(True); self.chk_sim_ps.setEnabled(True)
            self.ps_is_connected = False; self.ps_driver = None
            self.ps_monitor_timer.stop()
            self.lbl_ps_live_info.setText("<b>Voltaj:</b> -- V &nbsp;|&nbsp; <b>Akım:</b> -- A")

    def ps_apply_values(self):
        if not self.ps_is_connected or not self.ps_driver:
            QMessageBox.warning(self, "Hata", "Önce Güç Kaynağına Bağlanın!"); return
        v = self.ps_volt.text(); i = self.ps_curr.text()
        r = "LOW" if "15V" in self.combo_ps_range.currentText() else "HIGH"
        try:
            self.ps_driver.set_range(r); self.ps_driver.set_voltage_current(v, i)
            port_name = "SIM" if self.chk_sim_ps.isChecked() else self.combo_ports_ps.currentText()
            self.debug_log({"source": "POWER_SUPPLY", "event": "SET_VALUES", "ip_port": port_name, "volt": v, "curr": i, "range": r, "msg": f"Ayarlandı: {v}V, {i}A, Range: {r}"})
        except Exception as e:
            self.debug_log({"source": "ERROR", "msg": f"PS Ayar Hatası: {e}"})

    def ps_set_output(self, state):
        if not self.ps_is_connected or not self.ps_driver:
            QMessageBox.warning(self, "Hata", "Önce Güç Kaynağına Bağlanın!"); return
        try:
            self.ps_driver.set_output(state)
            port_name = "SIM" if self.chk_sim_ps.isChecked() else self.combo_ports_ps.currentText()
            msg = "Output ON (Güç Açık)" if state else "Output OFF (Güç Kapalı)"
            self.debug_log({"source": "POWER_SUPPLY", "event": "SET_OUTPUT", "ip_port": port_name, "msg": msg})
        except Exception as e:
            self.debug_log({"source": "ERROR", "msg": f"PS Çıkış Hatası: {e}"})

    def ps_get_error(self):
        if not self.ps_is_connected or not self.ps_driver:
            QMessageBox.warning(self, "Hata", "Önce Güç Kaynağına Bağlanın!"); return
        try:
            val = self.ps_driver.get_error()
            port = "SIM" if self.chk_sim_ps.isChecked() else self.combo_ports_ps.currentText()
            self.debug_log({"source": "POWER_SUPPLY", "event": "INFO", "ip_port": port, "msg": f"Hata Durumu: {val}"})
        except Exception as e:
            self.debug_log({"source": "ERROR", "msg": f"PS Hata Sorgusu: {e}"})

    def update_ps_live_info(self):
        if self.ps_is_connected and self.ps_driver:
            try:
                v = self.ps_driver.measure_voltage()
                i = self.ps_driver.measure_current()
                try: v_str = f"{float(v):.2f}"; i_str = f"{float(i):.2f}"
                except: v_str = str(v); i_str = str(i)
                self.lbl_ps_live_info.setText(f"<b>Voltaj:</b> {v_str} V &nbsp;|&nbsp; <b>Akım:</b> {i_str} A")
            except Exception:
                self.lbl_ps_live_info.setText("<b>Voltaj:</b> HATA &nbsp;|&nbsp; <b>Akım:</b> HATA")

    def preset_all_devices(self):
        if self.ps_is_connected and self.ps_driver:
            try:
                self.ps_driver.reset()
                port_name = "SIM" if self.chk_sim_ps.isChecked() else self.combo_ports_ps.currentText()
                self.debug_log({"source": "POWER_SUPPLY", "event": "PRESET", "ip_port": port_name, "msg": "Cihaz Sıfırlandı (*RST)"})
            except Exception as e:
                self.debug_log({"source": "ERROR", "msg": f"PS Reset Hatası: {e}"})
                
        if self.gen_is_connected and self.gen_driver:
            try: 
                self.gen_driver.preset()
                self.debug_log({"source": "GENERATOR", "event": "PRESET", "ip_port": self.ip_gen.text(), "msg": "Preset atıldı."})
            except: pass
            
        if self.sa_is_connected and self.sa_driver:
            try:
                self.sa_driver.preset()
                self.debug_log({"source": "ANALYZER", "event": "PRESET", "ip_port": self.ip_sa.text(), "msg": "Preset atıldı."})
            except: pass

    # ==========================================
    # JSON YÜKLEME 
    # ==========================================
    def select_metadata_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Test Senaryosu (JSON) Seç", "", "JSON Dosyaları (*.json)")
        if file_path:
            self.lbl_selected_json.setText(f"Seçilen Dosya: {os.path.basename(file_path)}")
            self.load_metadata(file_path)

    def load_metadata(self, filepath=None):
        self.clear_layout(self.precond_dynamic_layout)
        self.clear_layout(self.steps_inner_layout)
        self.precondition_checkboxes.clear()
        self.step_widgets.clear()
        self.current_json_data = None
        self.btn_proceed.setEnabled(False)
        self.btn_proceed.setStyleSheet(STYLE_GRAY)
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)

        try:
            if not filepath or not os.path.exists(filepath):
                lbl = QLabel("<b>Lütfen yukarıdan bir Test Senaryosu (JSON) dosyası seçin.</b><br>Dosya seçilmeden test adımları yüklenmez.")
                lbl.setStyleSheet("color: #41464b; font-size: 14px;")
                self.precond_dynamic_layout.addWidget(lbl)
                return

            with open(filepath, "r", encoding="utf-8") as f: data = json.load(f)
            self.current_json_data = data 
            executions = data.get("metadata", {}).get("execution", {}).get("executions", [])
            if not executions: raise ValueError("Executions listesi boş.")
            tests = executions[0].get("tests", [])
            if not tests: raise ValueError("Tests listesi boş.")
            preconditions_list = tests[0].get("preconditions", [])
            
            baslik = QLabel("<h2>Jira Test Ön Koşulları Doğrulaması</h2><p>Teste başlamadan önce onaylayın:</p>")
            self.precond_dynamic_layout.addWidget(baslik)

            if preconditions_list:
                self.chk_select_all = QCheckBox("Tümünü Seç / Kaldır")
                self.chk_select_all.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px; color: #084298;")
                self.chk_select_all.toggled.connect(self.toggle_all_preconditions)
                self.precond_dynamic_layout.addWidget(self.chk_select_all)
                line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setFrameShadow(QFrame.Shadow.Sunken); line.setStyleSheet("background-color: #084298;")
                self.precond_dynamic_layout.addWidget(line)

            for p in preconditions_list:
                cond = p.get("condition")
                if isinstance(cond, str):
                    for line in cond.split("\n"):
                        if line.strip():
                            cb = QCheckBox(line.strip()); cb.setStyleSheet("font-size: 14px; padding: 5px;")
                            cb.toggled.connect(self.check_preconditions_state)
                            self.precond_dynamic_layout.addWidget(cb); self.precondition_checkboxes.append(cb)
                elif isinstance(cond, list):
                    for item in cond:
                        if isinstance(item, dict) and "equipment_name" in item:
                            cb = QCheckBox(f"Cihaz: {item.get('equipment_name')} - {item.get('model')}")
                            cb.setStyleSheet("font-size: 14px; padding: 5px;")
                            cb.toggled.connect(self.check_preconditions_state)
                            self.precond_dynamic_layout.addWidget(cb); self.precondition_checkboxes.append(cb)

            if not self.precondition_checkboxes:
                self.tabs.setTabEnabled(1, True); self.tabs.setTabEnabled(2, True)
                self.btn_proceed.setEnabled(True); self.btn_proceed.setStyleSheet(STYLE_GREEN)

            steps_list = tests[0].get("steps", [])
            for s in steps_list:
                idx = s.get("index"); action = s.get("action", "Adım"); expected = s.get("expected_result", ""); attachments = s.get("attachments", [])
                step_data = s.get("data", "")
                step_widget = TestStepWidget(idx, action, expected, attachments, step_data)
                step_widget.toggled_signal.connect(self.on_step_toggled)
                step_widget.set_params_signal.connect(self.apply_test_parameters)
                self.steps_inner_layout.addWidget(step_widget)
                self.step_widgets.append(step_widget)

            self.update_steps_locking() 
            
        except Exception as e:
            lbl = QLabel(f"<b>Metadata okunurken hata oluştu:</b><br>{str(e)}")
            lbl.setStyleSheet("color: red; font-size: 14px;")
            self.precond_dynamic_layout.addWidget(lbl)

    def toggle_all_preconditions(self, checked):
        for cb in self.precondition_checkboxes: cb.setChecked(checked)

    def check_preconditions_state(self):
        all_checked = all(cb.isChecked() for cb in self.precondition_checkboxes)
        if hasattr(self, 'chk_select_all'):
            self.chk_select_all.blockSignals(True) 
            self.chk_select_all.setChecked(all_checked)
            self.chk_select_all.blockSignals(False)
        self.tabs.setTabEnabled(1, all_checked); self.tabs.setTabEnabled(2, all_checked)
        if hasattr(self, 'btn_proceed'):
            self.btn_proceed.setEnabled(all_checked)
            self.btn_proceed.setStyleSheet(STYLE_GREEN if all_checked else STYLE_GRAY)

    def on_step_toggled(self, step_index, is_checked):
        list_index = step_index - 1 
        if not is_checked:
            for i in range(list_index + 1, len(self.step_widgets)):
                self.step_widgets[i].checkbox.blockSignals(True)
                self.step_widgets[i].checkbox.setChecked(False)
                self.step_widgets[i].checkbox.blockSignals(False)
        self.update_steps_locking()
        self.check_test_completion()

    def update_steps_locking(self):
        for i, step_w in enumerate(self.step_widgets):
            if i == 0: step_w.set_step_enabled(True) 
            else:
                prev_step = self.step_widgets[i-1]
                step_w.set_step_enabled(prev_step.checkbox.isChecked()) 

    def check_test_completion(self):
        if not self.step_widgets: return
        all_checked = all(w.checkbox.isChecked() for w in self.step_widgets)
        if all_checked: QMessageBox.information(self, "Tebrikler", "Tüm Test Senaryosu Adımları Başarıyla Tamamlandı!")

    def update_gen_ui(self):
        mode = self.combo_gen_mode.currentText()
        self.freq_gen.setEnabled(True); self.pow_gen.setEnabled(True)
        self.sweep_start.setEnabled(False); self.sweep_stop.setEnabled(False)
        self.sweep_step.setEnabled(False); self.sweep_dwell.setEnabled(False)
        self.am_min_pow.setEnabled(False); self.am_max_pow.setEnabled(False); self.am_speed.setEnabled(False)
        self.btn_gen_start.setText("BAŞLAT") 
        if mode == "Sweep":
            self.freq_gen.setEnabled(False); self.sweep_start.setEnabled(True); self.sweep_stop.setEnabled(True)
            self.sweep_step.setEnabled(True); self.sweep_dwell.setEnabled(True)
        elif mode == "AM Modülasyon (Güç Değişimi)":
            self.pow_gen.setEnabled(False); self.am_min_pow.setEnabled(True); self.am_max_pow.setEnabled(True); self.am_speed.setEnabled(True)

    def set_gen_inputs_enabled(self, enabled):
        self.combo_gen_mode.setEnabled(enabled)
        self.freq_gen.setEnabled(enabled); self.pow_gen.setEnabled(enabled)
        self.sweep_start.setEnabled(enabled); self.sweep_stop.setEnabled(enabled)
        self.sweep_step.setEnabled(enabled); self.sweep_dwell.setEnabled(enabled)
        self.am_min_pow.setEnabled(enabled); self.am_max_pow.setEnabled(enabled); self.am_speed.setEnabled(enabled)
        if enabled: self.update_gen_ui() 

    def toggle_generator(self):
        if not self.gen_is_connected or not self.gen_driver:
            QMessageBox.warning(self, "Hata", "Önce Jeneratöre Bağlanın!"); return
            
        if self.gen_worker and self.gen_worker.isRunning():
            self.gen_worker.stop(); self.gen_worker.wait()
            self.btn_gen_start.setText("BAŞLAT"); self.btn_gen_start.setStyleSheet(STYLE_GREEN)
            self.set_gen_inputs_enabled(True); return 
            
        mode_text = self.combo_gen_mode.currentText(); params = {}; mode_code = ""
        
        if mode_text == "Sabit Sinyal":
            mode_code = 'SINGLE'; params = {'freq': self._to_double(self.freq_gen.text()), 'power': self._to_double(self.pow_gen.text())}
        elif mode_text == "Sweep":
            step_val = self._to_double(self.sweep_step.text())
            if step_val == 0.0: QMessageBox.warning(self, "Hata", "Sweep Adım değeri 0 olamaz!"); return
            mode_code = 'SWEEP'
            params = {'start': self._to_double(self.sweep_start.text()), 'stop': self._to_double(self.sweep_stop.text()), 'step': step_val, 'dwell': self._to_double(self.sweep_dwell.text()), 'power': self._to_double(self.pow_gen.text())}
        elif mode_text == "AM Modülasyon (Güç Değişimi)":
            mode_code = 'AM_SINE'
            params = {'freq': self._to_double(self.freq_gen.text()), 'min_power': self._to_double(self.am_min_pow.text()), 'max_power': self._to_double(self.am_max_pow.text()), 'speed': self._to_double(self.am_speed.text())}
                      
        self.gen_worker = GeneratorWorker(self.gen_driver, mode_code, params)
        self.gen_worker.log_signal.connect(self.debug_log); self.gen_worker.error_signal.connect(self.debug_log)
        
        if mode_code != 'SINGLE': 
            self.btn_gen_start.setText("DURDUR"); self.btn_gen_start.setStyleSheet(STYLE_RED)
            self.set_gen_inputs_enabled(False) 
            self.gen_worker.finished.connect(lambda: self.btn_gen_start.setText("BAŞLAT"))
            self.gen_worker.finished.connect(lambda: self.btn_gen_start.setStyleSheet(STYLE_GREEN))
            self.gen_worker.finished.connect(lambda: self.set_gen_inputs_enabled(True)) 
        self.gen_worker.start()

    def temp_file_init(self):
        try: open(self.temp_filename, 'w').close()
        except: pass

    # ==========================================
    # LOG VE GRAFİK GÜNCELLEME 
    # ==========================================
    @pyqtSlot(dict)
    def debug_log(self, data):
        now = datetime.datetime.now(); timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        msg = data.get("msg", ""); source = data.get("source", "UNKNOWN")
        event = data.get("event", "")
        color = "black"
        
        if source == "DUT": color = "green"
        elif source == "GENERATOR": color = "blue"
        elif source == "ANALYZER": color = "#d63384"
        elif source == "POWER_SUPPLY": color = "#e67e22" 
        elif source == "ERROR": color = "red"
        
        self.log_area.append(f'<span style="color:{color};">[{timestamp_str}] {msg}</span>')
        
        def g(key): return str(data.get(key, "0"))
        row = [
            timestamp_str, source, data.get('event', '0'), data.get('ip_port', '0'),
            str(data.get('freq', data.get('center', '0'))), str(data.get('power', data.get('ref', '0'))),
            g('start'), g('stop'), g('step'), g('dwell'), g('min_power'), g('max_power'), g('speed'),
            g('span'), g('rbw'), g('volt'), g('curr'), str(data.get('idn', '0')), data.get('data_content', '0')
        ]
        try: 
            with open(self.temp_filename, 'a', encoding='utf-8') as f: f.write("|".join(row) + "\n")
        except: pass

    @pyqtSlot(dict)
    def update_graph(self, data):
        try:
            center = data['center']; span = data['span']; peak_x = data['peak_x']; peak_y = data['peak_y']; trace_y = data['trace_y']
            if span <= 0: span = 10.0 
            
            self.lbl_graph_info.setText(f"<b>Merkez Frekans:</b> {center} MHz  |  <b>Span:</b> {span} MHz  |  <b>Peak:</b> {peak_y:.2f} dBm @ {peak_x:.2f} MHz")
            
            x = np.linspace(center - span/2, center + span/2, len(trace_y))
            self.current_trace_x = x
            self.current_trace_y = trace_y
            self.sa_curve.setData(x, trace_y)
            
        except Exception as e: print(f"Grafik çizim hatası: {e}")
                
        if CURRENT_SIGNAL["active"]:
            self.gen_marker.setValue(CURRENT_SIGNAL["freq"])
            self.gen_marker.label.setFormat(f"GEN: {CURRENT_SIGNAL['freq']:.2f} MHz")
            self.gen_marker.show()
        else: self.gen_marker.hide()

    # ==========================================
    # GRAFİK DIŞA AKTARIM FONKSİYONLARI
    # ==========================================
    def export_graph_png(self):
        now = datetime.datetime.now(); ms = now.strftime("%f")[:3]; time_str_file = now.strftime("%Y%m%d_%H%M%S")
        file_path = f"Spektrum_Grafik_{time_str_file}_{ms}.png"
        try:
            exporter = pg.exporters.ImageExporter(self.plot_widget.scene())
            exporter.export(file_path)
            QMessageBox.information(self, "Başarılı", f"Grafik PNG olarak kaydedildi:\n{file_path}")
        except Exception as e: QMessageBox.critical(self, "Hata", f"PNG kaydedilemedi: {e}")

    def export_graph_csv(self):
        if not len(self.current_trace_x):
            QMessageBox.warning(self, "Hata", "Kaydedilecek grafik verisi yok! Lütfen önce ölçüm alın."); return
            
        now = datetime.datetime.now(); ms = now.strftime("%f")[:3]; time_str_file = now.strftime("%Y%m%d_%H%M%S")
        time_str_log = now.strftime("%Y-%m-%d %H:%M:%S"); file_path = f"Grafik_Verisi_{time_str_file}_{ms}.csv"

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["# METADATA BİLGİLERİ"]); writer.writerow(["# Test Zamanı", f"{time_str_log}.{ms}"])
                writer.writerow(["# Spektrum Analizör IP", self.ip_sa.text()]); writer.writerow(["# Spektrum Analizör IDN", self.sa_idn])
                writer.writerow(["# Merkez Frekans (MHz)", self.sa_center.text()]); writer.writerow(["# Span (MHz)", self.sa_span.text()])
                writer.writerow([])
                writer.writerow(["Frekans (MHz)", "Guc (dBm)"])
                for i in range(len(self.current_trace_x)):
                    writer.writerow([f"{self.current_trace_x[i]:.4f}", f"{self.current_trace_y[i]:.2f}"])
            QMessageBox.information(self, "Başarılı", f"Grafik Datası kaydedildi:\n{file_path}")
        except Exception as e: QMessageBox.critical(self, "Hata", f"CSV kaydedilemedi: {e}")

    def debug_log_save(self):
        csv_name = f"Log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        if not os.path.exists(self.temp_filename): return
        with open(self.temp_filename, 'r', encoding='utf-8') as temp_f: lines = temp_f.readlines()
        total_lines = len(lines)
        if total_lines == 0: QMessageBox.information(self, "Bilgi", "Log boş."); return

        progress = QProgressDialog("CSV Kaydediliyor...", "İptal", 0, total_lines, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0); progress.setValue(0)

        try:
            with open(csv_name, 'w', newline='', encoding='utf-8') as f_out:
                writer = csv.writer(f_out, delimiter=';')
                writer.writerow(["TIME", "SOURCE", "EVENT", "PORT", "FREQ/CENTER", "POWER/REF", 
                                 "START", "STOP", "STEP", "DWELL", "AM_MIN", "AM_MAX", "AM_SPEED", 
                                 "SPAN", "RBW", "VOLT", "CURR", "IDN", "DATA"])
                for i, line in enumerate(lines):
                    if progress.wasCanceled(): break 
                    parts = line.strip().split('|')
                    if len(parts) == 18: parts.insert(17, "0")
                    writer.writerow(parts)
                    if i % 50 == 0: progress.setValue(i); QApplication.processEvents()
                progress.setValue(total_lines) 
            if not progress.wasCanceled():
                QMessageBox.information(self, "Başarılı", f"Veriler kaydedildi:\n{csv_name}")
                if self.chk_auto_clr.isChecked(): self.clear_display_log()
            else: QMessageBox.warning(self, "İptal", "Kaydetme işlemi iptal edildi.")
        except Exception as e: QMessageBox.critical(self, "Hata", str(e))

    def clear_display_log(self): self.log_area.clear(); self.temp_file_init()
    def refresh_ports(self): 
        self.combo_ports.clear()
        self.combo_ports_ps.clear()
        for p in serial.tools.list_ports.comports():
            self.combo_ports.addItem(p.device)
            self.combo_ports_ps.addItem(p.device)
    
    def toggle_dut(self):
        if not self.dut_thread:
            is_sim = self.chk_sim_dut.isChecked()
            self.dut_thread = DutWorker(self.combo_ports.currentText(), 115200, is_sim)
            self.dut_thread.data_signal.connect(self.debug_log); self.dut_thread.start()
            self.btn_dut.setText("BAĞLANTIYI KES"); self.btn_dut.setStyleSheet(STYLE_RED)
            self.combo_ports.setEnabled(False); self.chk_sim_dut.setEnabled(False)
        else:
            self.dut_thread.stop()
            port_name = "SIM" if self.chk_sim_dut.isChecked() else self.combo_ports.currentText()
            self.debug_log({"source":"DUT","event":"DISCONNECT","ip_port":port_name,"msg":"Kesildi","data_content":""})
            self.dut_thread = None
            self.btn_dut.setText("BAĞLAN"); self.btn_dut.setStyleSheet(STYLE_GREEN)
            self.combo_ports.setEnabled(True); self.chk_sim_dut.setEnabled(True)

    def toggle_continuous_measure(self):
        if not self.sa_is_connected or not self.sa_driver:
            QMessageBox.warning(self, "Hata", "Önce Spektrum Analizöre Bağlanın!"); return
            
        if self.sa_worker and self.sa_worker.isRunning():
            self.sa_worker.stop(); self.sa_worker.wait(); self.sa_worker = None
            self.btn_sa_cont.setText("SÜREKLİ ÖLÇÜM"); self.btn_sa_cont.setStyleSheet(STYLE_GREEN)
            self.debug_log({"source": "ANALYZER", "event": "LOOP_STOP", "ip_port": self.ip_sa.text(), "msg": "Ölçüm Durduruldu.", "data_content": "0"})
        else:
            params = {'center': self._to_double(self.sa_center.text()), 'span': self._to_double(self.sa_span.text()), 'ref': self._to_double(self.sa_ref.text()), 'rbw': self._to_double(self.sa_rbw.text())}
            self.sa_current_params = params
            self.sa_worker = AnalyzerWorker(self.sa_driver, 'CONTINUOUS', params)
            self.sa_worker.log_signal.connect(self.debug_log)
            self.sa_worker.trace_signal.connect(self.update_graph)
            self.sa_worker.start()
            self.btn_sa_cont.setText("DURDUR"); self.btn_sa_cont.setStyleSheet(STYLE_RED)

    def run_analyzer(self, mode):
        if not self.sa_is_connected or not self.sa_driver:
            QMessageBox.warning(self, "Hata", "Önce Spektrum Analizöre Bağlanın!"); return
            
        if mode == 'SINGLE_SHOT' and self.sa_worker and self.sa_worker.isRunning(): self.toggle_continuous_measure()
        params = {'center': self._to_double(self.sa_center.text()), 'span': self._to_double(self.sa_span.text()), 'ref': self._to_double(self.sa_ref.text()), 'rbw': self._to_double(self.sa_rbw.text())}
        self.sa_worker = AnalyzerWorker(self.sa_driver, mode, params)
        self.sa_worker.log_signal.connect(self.debug_log)
        self.sa_worker.trace_signal.connect(self.update_graph)
        self.sa_worker.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
