# Mini Yuzey Hatasi Tespit Uygulamasi

Aluminyum yuzey hatalarinin tespit edilmesini simule eden FastAPI + React web uygulamasi.

## Ozellikler

- Urun adi, urun ID/etiketi ve confidence threshold girisi
- Baslat, Durdur, Resetle aksiyonlari
- Mock hata tespit sonucu tablosu
- JSON veya CSV rapor indirme
- Docker ile tek servis olarak calisma
- PyTorch `best.pt` entegrasyonu icin ayrilmis `detection_service.py` modulu

## Proje Yapisi

```text
backend/
  app/
    detection_service.py
    main.py
  requirements.txt
frontend/
  src/
    main.jsx
    styles.css
  index.html
  package.json
Dockerfile
README.md
```

## Lokal Calistirma

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Frontend varsayilan olarak `http://localhost:5173`, backend `http://localhost:8000` adresinde calisir. Vite gelistirme sunucusu `/api` isteklerini backend'e proxy eder.

## Docker ile Calistirma

```bash
docker build -t mini-yuzey-hatasi .
docker run --rm -p 8000:8000 mini-yuzey-hatasi
```

Uygulama Docker ile `http://localhost:8000` adresinden acilir.

## API Uclari

- `GET /api/health`
- `POST /api/detections/start`
- `POST /api/detections/stop`
- `POST /api/detections/reset`
- `POST /api/reports/json`
- `POST /api/reports/csv`

Baslatma istegi ornegi:

```json
{
  "product_name": "Aluminyum Rulo A",
  "product_tag": "AL-2026-001",
  "threshold": 0.65
}
```

## YOLO / PyTorch Model Entegrasyonu

Model entegrasyonu `backend/app/detection_service.py` icindedir. Servis varsayilan olarak asagidaki model yollarini arar:

- `backend/app/best.pt`
- `best.pt`
- `best.pt ve ornekler/yolov11n/best.pt`
- `best.pt ve örnekler/yolov11n/best.pt`

`ultralytics.YOLO` ile model yuklenir ve `model.predict()` ciktisi su formata donusturulur:

- hata tipi
- guven skoru
- metre bilgisi
- zaman bilgisi
- bounding box

Model dosyasi bulunamazsa, `ultralytics` kurulu degilse veya tahmin sirasinda hata olursa servis mock veriye geri doner. Mevcut frontend goruntu gondermedigi icin `Baslat` aksiyonu gelistirme modunda mock fallback kullanir; gercek tahmin icin `DetectionService.detect(image=...)` veya `DetectionService.detect(image_path=...)` kullanilmalidir.

Metre bilgisi su an bounding box merkezinin goruntu genisligindeki konumundan 0-120 m araligina olceklenerek hesaplanir. Gercek hatta bu hesap kamera/encoder kalibrasyonuna gore degistirilmelidir.
