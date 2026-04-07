import serial
import time

class PowerSupplyDriver:
    """
    Agilent E3632A DC Power Supply (SCPI via Serial Port) Sürücüsü
    Görseldeki SCPI komut setine göre güncellenmiştir.
    """
    def __init__(self, port, baudrate=9600, simulate=False):
        self.port = port
        self.baudrate = baudrate
        self.simulate = simulate
        self.ser = None
        self.is_connected = False

    def connect(self):
        if self.simulate:
            self.is_connected = True
            time.sleep(0.5) # Bağlantı gecikmesi simülasyonu
            return True
            
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_TWO,
                timeout=2
            )
            self.is_connected = True
            
            # Başlangıç komutları
            self.send_command("SYST:REM")
            self.send_command("*CLS") # Clear Errors
            self.send_command("SYST:BEEP")
            time.sleep(0.2)
            self.send_command("SYST:BEEP")
            return True
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Güç Kaynağı bağlantı hatası ({self.port}): {e}")

    def disconnect(self):
        if self.simulate:
            self.is_connected = False
            return
            
        if self.ser and self.ser.is_open:
            try: self.send_command("SYST:LOC") 
            except: pass
            self.ser.close()
        self.is_connected = False

    def send_command(self, cmd):
        if self.simulate:
            time.sleep(0.1)
            return
            
        if not self.is_connected or not self.ser:
            raise ConnectionError("Güç Kaynağına bağlı değil!")
            
        full_cmd = cmd + "\n" # <LF> eklendi
        self.ser.write(full_cmd.encode('utf-8'))
        time.sleep(0.1) 

    def query(self, cmd):
        """Soru işareti (?) içeren cihazdan veri okuma komutları için eklendi"""
        if self.simulate:
            time.sleep(0.1)
            return "SIM_DATA"
            
        if not self.is_connected or not self.ser:
            raise ConnectionError("Güç Kaynağına bağlı değil!")
            
        full_cmd = cmd + "\n"
        self.ser.write(full_cmd.encode('utf-8'))
        time.sleep(0.1)
        # Gelen veriyi oku
        response = self.ser.readline().decode('utf-8').strip()
        return response

    # --- GÖRSELDEKİ SCPI KOMUTLARI ---
    
    def clear_errors(self):
        self.send_command("*CLS")

    def get_error(self):
        return self.query("SYST:ERR?")

    def reset(self):
        self.send_command("*RST")

    def get_version(self):
        return self.query("SYST:VERS?")

    def get_idn(self):
        return self.query("*IDN?")

    def get_output_state(self):
        return self.query("OUTP:STATE?")

    def set_output(self, state):
        """state: True (ON) or False (OFF)"""
        cmd = "OUTP:STAT ON" if state else "OUTP:STAT OFF"
        self.send_command(cmd)

    def measure_voltage(self):
        return self.query("MEAS:VOLT:DC?")

    def measure_current(self):
        return self.query("MEAS:CURR:DC?")

    def get_range(self):
        return self.query("SOUR:VOLT:RANG?")

    def set_voltage_current(self, voltage, current):
        """Voltaj (V) ve Akım (A) değerlerini ayarlar"""
        cmd = f"APPL {voltage}, {current}"
        self.send_command(cmd)

    # UI combobox ile uyumlu olması için bırakıldı
    def set_range(self, range_type):
        """range_type: 'LOW' (15V, 7A) or 'HIGH' (30V, 4A)"""
        if range_type.upper() == 'LOW':
            self.send_command("VOLT:RANG P15V")
        elif range_type.upper() == 'HIGH':
            self.send_command("VOLT:RANG P30V")