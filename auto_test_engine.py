# auto_test_engine.py
import time
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, Qt

class AutoTestWorker(QThread):
    """Otonom test adımlarını arka planda sırayla koşan iş parçacığı"""
    progress_signal = pyqtSignal(int, str) # İlerleme yüzdesi ve mesajı
    step_done_signal = pyqtSignal(int)     # Tamamlanan adımın indeksi
    finished_signal = pyqtSignal(bool)     # Testin başarı durumu (True: Bitti, False: İptal)

    def __init__(self, selected_steps, main_window):
        super().__init__()
        self.selected_steps = sorted(selected_steps) # Seçilen adımları küçükten büyüğe sırala
        self.main_window = main_window
        self.running = True

    def run(self):
        total = len(self.selected_steps)
        for i, step_idx in enumerate(self.selected_steps):
            if not self.running:
                self.finished_signal.emit(False)
                return

            self.progress_signal.emit(int((i / total) * 100), f"Koşuluyor: Test Adımı {step_idx}...")
            
            # --- OTONOM TEST KOMUTLARI BURADA TETİKLENİR ---
            # 1. İlgili adımın GUI parametrelerini otomatik doldur
            # (Gerçek veri entegrasyonunda burası adıma özel parametreleri çekecektir)
            
            # 2. Cihazlara komut gönderimi (Şimdilik simüle ediyoruz)
            self.main_window.debug_log({"source": "AUTONOMOUS", "event": "RUN_STEP", "msg": f"Otonom Komut tetiklendi: Adım {step_idx}"})
            
            # 3. Cihazların yanıt vermesi ve adımın tamamlanması için bekleme süresi
            waited = 0
            while waited < 2.0: # Her adım için 2 saniye simüle bekleme
                if not self.running:
                    self.finished_signal.emit(False)
                    return
                time.sleep(0.1)
                waited += 0.1

            # Adım başarıyla bitti, arayüze bildir (Tik atılması için)
            self.step_done_signal.emit(step_idx)

        self.progress_signal.emit(100, "Tüm seçili adımlar başarıyla tamamlandı!")
        time.sleep(0.5) # Kullanıcının %100'ü görmesi için kısa bekleme
        self.finished_signal.emit(True)

    def stop(self):
        self.running = False


class AutoTestProgressDialog(QDialog):
    """Otonom test koşulurken ekranda beliren Canlı İlerleme Penceresi"""
    def __init__(self, selected_steps, main_window, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Otonom Test İşleyişi")
        self.setFixedSize(450, 180)
        self.setWindowModality(Qt.WindowModality.ApplicationModal) # Diğer pencerelere tıklanmasın
        
        self.selected_steps = selected_steps
        self.main_window = main_window

        layout = QVBoxLayout(self)
        
        self.lbl_status = QLabel("Test başlatılıyor...")
        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #084298;")
        layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.btn_stop = QPushButton("TESTİ DURDUR")
        self.btn_stop.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; height: 35px;")
        self.btn_stop.clicked.connect(self.stop_test)
        layout.addWidget(self.btn_stop)

        # Worker Thread Başlat
        self.worker = AutoTestWorker(selected_steps, main_window)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.step_done_signal.connect(self.on_step_done)
        self.worker.finished_signal.connect(self.on_test_finished)
        self.worker.start()

    def update_progress(self, val, msg):
        self.progress_bar.setValue(val)
        self.lbl_status.setText(msg)

    def on_step_done(self, step_idx):
        # İşlemi biten test adımını global listeye ekle ve arayüzde tikini at
        self.main_window.completed_steps.add(step_idx)
        
        # Arayüzdeki ilgili widget'ın checkbox'ını sinyalleri bozmadan işaretle
        for w in self.main_window.step_widgets:
            if w.step_index == step_idx:
                w.checkbox.blockSignals(True)
                w.checkbox.setChecked(True)
                w.checkbox.blockSignals(False)
                break

    def stop_test(self):
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Test durduruluyor, lütfen bekleyin...")
        self.worker.stop()

    def on_test_finished(self, success):
        if success:
            QMessageBox.information(self, "Tamamlandı", "Seçilen otonom test senaryosu başarıyla tamamlandı.")
        else:
            QMessageBox.warning(self, "İptal Edildi", "Otonom test kullanıcının talebi üzerine durduruldu.")
        self.accept()

    def reject(self):
        # Çarpı butonuna basılırsa da güvenli durdurma yap
        self.stop_test()