import serial
import time

class DutHandler:
    def __init__(self, port, baud, simulation_mode=False):
        self.port = port
        self.baud = baud
        self.simulation_mode = simulation_mode
        self.serial_conn = None
        self.sim_counter = 0 # Testere dişi dalga için sayaç

    def connect(self):
        if not self.simulation_mode:
            self.serial_conn = serial.Serial(self.port, self.baud, timeout=1)

    def read_line(self):
        """Veri varsa okur, yoksa None döner"""
        if self.simulation_mode:
            # --- SİMÜLASYON MODU (Testere Dişi Fonksiyonu) ---
            time.sleep(0.5) # Biraz gecikme
            
            # Testere Dişi Mantığı: 0'dan 100'e çıkar, sonra sıfırlanır
            self.sim_counter += 5
            if self.sim_counter > 100:
                self.sim_counter = 0
            
            # Sinyale göre fonksiyonel bir değer üretelim
            val = self.sim_counter
            return f"SIM_SAWTOOTH_VAL: {val}"
            
        else:
            # --- GERÇEK SERİ PORT MODU ---
            if self.serial_conn and self.serial_conn.in_waiting > 0:
                try:
                    return self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                except:
                    return None
            return None

    def close(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()