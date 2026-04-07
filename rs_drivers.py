from RsInstrument import RsInstrument

class SignalGeneratorDriver:
    def __init__(self, ip_address, simulate=True):
        # simulate=True ise cihaz olmasa da kod çalışır (Simülasyon Modu)
        sim_str = "Simulate=True" if simulate else ""
        self.resource_str = f"TCPIP::{ip_address}::INSTR"
        self.options = f"QueryInstrumentStatus=True,{sim_str}"

    def connect_and_set(self, freq, power):
        """Tek frekans ayarı yapar"""
        instr = RsInstrument(self.resource_str, id_query=True, reset=False, options=self.options)
        instr.write_str(f"FREQ {freq} MHz")
        instr.write_str(f"POW {power} dBm")
        instr.write_str("OUTP ON")
        instr.close()

    def preset(self):
        """Cihazı fabrika ayarlarına döndürür (*RST)"""
        instr = RsInstrument(self.resource_str, id_query=True, reset=False, options=self.options)
        instr.write_str("*RST")
        instr.close()

class SpectrumAnalyzerDriver:
    def __init__(self, ip_address, simulate=True):
        sim_str = "Simulate=True" if simulate else ""
        self.resource_str = f"TCPIP::{ip_address}::INSTR"
        self.options = f"QueryInstrumentStatus=True,{sim_str}"

    def configure_and_measure(self, center, span, ref, rbw):
        """Ayarları yapar ve Peak değerini okur"""
        instr = RsInstrument(self.resource_str, id_query=True, reset=False, options=self.options)
        
        # Ayarlar
        instr.write_str(f"FREQ:CENT {center} MHz")
        instr.write_str(f"FREQ:SPAN {span} MHz")
        instr.write_str(f"DISP:TRAC:Y:RLEV {ref} dBm")
        instr.write_str(f"BAND:RES {rbw} kHz")
        
        # Ölçüm
        instr.write_str("CALC:MARK1:MAX")
        val = instr.query_float("CALC:MARK1:Y?")
        
        instr.close()
        return val

    def preset(self):
        """Cihazı fabrika ayarlarına döndürür"""
        instr = RsInstrument(self.resource_str, id_query=True, reset=False, options=self.options)
        instr.write_str("*RST")
        instr.close()