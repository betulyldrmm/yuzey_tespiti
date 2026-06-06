# Mini Yüzey Hatası Tespit Uygulaması

Bu proje, alüminyum yüzeylerdeki hataları tespit etmeyi simüle eden küçük bir web uygulamasıdır. Backend tarafında FastAPI, frontend tarafında React kullanılmıştır.

## Özellikler

- Ürün adı, ürün etiketi ve eşik değeri girilebilir.
- Başlat, Durdur ve Resetle butonları vardır.
- Tespit edilen hatalar tabloda gösterilir.
- JSON veya CSV formatında rapor indirilebilir.
- Docker ile çalıştırılabilir.
- YOLO `best.pt` modeli `detection_service.py` üzerinden kullanılabilir.

## Proje Yapısı

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
  package.json

Dockerfile
README.md
```

## Çalıştırma

Backend için:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

Frontend için:

```bash
cd frontend
npm install
npm run dev
```

Frontend `http://localhost:5173`, backend ise `http://localhost:8000` adresinde çalışır. Frontend içindeki `/api` istekleri Vite proxy ile backend'e yönlendirilir.

## Docker ile Çalıştırma

```bash
docker build -t mini-yuzey-hatasi .
docker run --rm -p 8000:8000 mini-yuzey-hatasi
```

Sonra uygulama `http://localhost:8000` adresinden açılır.

## API Adresleri

- `GET /api/health`
- `POST /api/detections/start`
- `POST /api/detections/stop`
- `POST /api/detections/reset`
- `POST /api/reports/json`
- `POST /api/reports/csv`

Örnek başlatma isteği:

```json
{
  "product_name": "Alüminyum Rulo A",
  "product_tag": "AL-2026-001",
  "threshold": 0.65
}
```

## Model Kullanımı

Model işlemleri `backend/app/detection_service.py` dosyasındadır. Servis şu yollarda `best.pt` dosyasını arar:

- `backend/app/best.pt`
- `best.pt`
- `best.pt ve ornekler/yolov11n/best.pt`
- `best.pt ve örnekler/yolov11n/best.pt`

Model bulunursa `ultralytics.YOLO` ile yüklenir ve `model.predict()` kullanılarak tahmin yapılır. Sonuçlar şu bilgilere çevrilir:

- hata tipi
- güven skoru
- metre bilgisi
- zaman bilgisi
- bounding box

Model dosyası yoksa veya model çalışmazsa uygulama mock veri üretmeye devam eder. Şu an frontend görüntü göndermediği için Başlat butonu mock sonuç üretir. Gerçek model tahmini için `DetectionService.detect(image=...)` veya `DetectionService.detect(image_path=...)` kullanılabilir.
