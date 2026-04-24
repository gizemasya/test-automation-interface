import time
import random
import numpy as np
from RsInstrument import RsInstrument

class SignalGeneratorDriver:
    def __init__(self, ip_address, simulate=False, conn_type="INSTR"):
        self.simulate = simulate
        self.ip_address = ip_address
        
        sim_str = "Simulate=True" if simulate else ""
        if conn_type == "INSTR":
            self.resource_str = f"TCPIP::{ip_address}::INSTR"
        else:
            self.resource_str = f"TCPIP::{ip_address}::{conn_type}::INSTR"
            
        self.options = f"QueryInstrumentStatus=True,{sim_str}"
        self.instr = None

    def connect(self):
        if not self.instr:
            self.instr = RsInstrument(self.resource_str, id_query=True, reset=False, options=self.options)

    def disconnect(self):
        if self.instr:
            self.instr.close()
            self.instr = None

    def get_idn(self):
        if self.simulate: return "SIM_GEN_IDN"
        if not self.instr: raise ConnectionError("Cihaza bağlı değil.")
        return self.instr.query_str("*IDN?")

    def apply_settings(self, freq, power):
        if not self.instr: raise ConnectionError("Cihaza bağlı değil.")
        self.instr.write_str(f"FREQ {freq} MHz")
        self.instr.write_str(f"POW {power} dBm")
        self.instr.write_str("OUTP ON")

    def set_rf_output(self, state):
        if self.simulate: return
        if not self.instr: raise ConnectionError("Cihaza bağlı değil.")
        cmd = "OUTP ON" if state else "OUTP OFF"
        self.instr.write_str(cmd)

    def preset(self):
        if not self.instr: raise ConnectionError("Cihaza bağlı değil.")
        self.instr.write_str("*RST")


class SpectrumAnalyzerDriver:
    def __init__(self, ip_address, simulate=False, conn_type="INSTR"):
        self.simulate = simulate
        self.ip_address = ip_address
        
        self.sim_center = 2400.0  
        self.sim_span = 10.0      
        
        sim_str = "Simulate=True" if simulate else ""
        if conn_type == "INSTR":
            self.resource_str = f"TCPIP::{ip_address}::INSTR"
        else:
            self.resource_str = f"TCPIP::{ip_address}::{conn_type}::INSTR"
            
        self.options = f"QueryInstrumentStatus=True,{sim_str}"
        self.instr = None

    def connect(self):
        if not self.instr:
            self.instr = RsInstrument(self.resource_str, id_query=True, reset=False, options=self.options)

    def disconnect(self):
        if self.instr:
            self.instr.close()
            self.instr = None

    def get_idn(self):
        if self.simulate: return "SIM_SA_IDN"
        if not self.instr: raise ConnectionError("Cihaza bağlı değil.")
        return self.instr.query_str("*IDN?")

    def apply_settings(self, center, span, ref, rbw):
        if self.simulate:
            self.sim_center = float(center)
            self.sim_span = float(span)
            
        if not self.instr: raise ConnectionError("Cihaza bağlı değil.")
        self.instr.write_str(f"FREQ:CENT {center} MHz")
        self.instr.write_str(f"FREQ:SPAN {span} MHz")
        self.instr.write_str(f"DISP:TRAC:Y:RLEV {ref} dBm")
        self.instr.write_str(f"BAND:RES {rbw} kHz")

    def set_run_mode(self, mode):
        """Single/Continuous durum komutunu cihaza iletir"""
        if self.simulate: return
        if not self.instr: raise ConnectionError("Cihaza bağlı değil.")
        if mode == 'SINGLE_SHOT':
            self.instr.write_str("INIT:CONT OFF")  # Sürekli ölçümü kapat
            self.instr.write_str("INIT:IMM; *WAI") # Tek ölçüm al ve bitene kadar bekle
        elif mode == 'CONTINUOUS':
            self.instr.write_str("INIT:CONT ON")   # Sürekli ölçümü aç

    def get_peak_marker(self):
        if self.simulate:
            return (self.sim_center + random.uniform(-self.sim_span/10, self.sim_span/10), -20.0 + random.uniform(-0.5, 0.5))
            
        if not self.instr: raise ConnectionError("Cihaza bağlı değil.")
        self.instr.write_str("CALC:MARK1:MAX")
        x_val = self.instr.query_float("CALC:MARK1:X?")
        y_val = self.instr.query_float("CALC:MARK1:Y?")
        
        return (x_val / 1e6, y_val)  

    def get_trace_data(self):
        if self.simulate:
            return np.random.normal(-115.0, 1.5, 501).tolist()
            
        if not self.instr: raise ConnectionError("Cihaza bağlı değil.")
        self.instr.write_str("FORMAT ASCII")
        trace_str = self.instr.query_str("TRAC? TRACE1")
        trace_data = [float(x) for x in trace_str.split(",")]
        return trace_data

    def preset(self):
        if not self.instr: raise ConnectionError("Cihaza bağlı değil.")
        self.instr.write_str("*RST")
