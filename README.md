## Gereksinimler

Yazılımın çalışması için bilgisayarınızda **Python 3.8 veya üzeri** bir sürüm kurulu olmalıdır.

### Gerekli dış kütüphaneler

- `PyQt6`
- `pyserial`
- `RsInstrument`

---

## Çalıştırma

### 1. Dosyaları doğrulayın

Aşağıdaki dosyaların **aynı klasör içinde** bulunduğundan emin olun:

- `main.py` → Ana arayüz
- `ps_driver.py` → Güç kaynağı sürücüsü
- `rs_drivers.py` → Jeneratör ve analizör sürücüsü
- `dut_driver.py` → DUT sürücüsü
- `metadata.json` ve `rf_scenerio.json` → Test tanımlama dosyası
- `/attachments klasörü` → Test için ek dosyalar
---

### 2. Uygulamayı başlatın

Terminal üzerinden aşağıdaki komutu çalıştırın:

```bash
python main.py
```
