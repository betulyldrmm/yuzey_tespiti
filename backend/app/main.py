from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .detection_service import DetectionResult, DetectionService


class ProductRequest(BaseModel):
    product_name: str = Field(min_length=1, max_length=120)
    product_tag: str = Field(min_length=1, max_length=120)
    threshold: float = Field(ge=0.0, le=1.0)


class DetectionResponse(BaseModel):
    status: Literal["running", "stopped", "idle"]
    detections: list[dict]


class ReportRequest(ProductRequest):
    detections: list[dict] = Field(default_factory=list)


app = FastAPI(title="Mini Yuzey Hatasi Tespit Uygulamasi")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detection_service = DetectionService()
state: dict[str, object] = {"status": "idle", "detections": []}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/detections/start", response_model=DetectionResponse)
def start_detection(payload: ProductRequest) -> DetectionResponse:
    detections = [result.to_dict() for result in detection_service.detect(threshold=payload.threshold)]
    state["status"] = "running"
    state["detections"] = detections
    return DetectionResponse(status="running", detections=detections)


@app.post("/api/detections/stop", response_model=DetectionResponse)
def stop_detection() -> DetectionResponse:
    state["status"] = "stopped"
    return DetectionResponse(status="stopped", detections=list(state["detections"]))


@app.post("/api/detections/reset", response_model=DetectionResponse)
def reset_detection() -> DetectionResponse:
    state["status"] = "idle"
    state["detections"] = []
    return DetectionResponse(status="idle", detections=[])


@app.post("/api/reports/json")
def create_json_report(payload: ReportRequest) -> dict:
    return _build_report(payload)


@app.post("/api/reports/csv")
def create_csv_report(payload: ReportRequest) -> Response:
    report = _build_report(payload)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Urun Adi", report["product_name"]])
    writer.writerow(["Urun Etiketi", report["product_tag"]])
    writer.writerow(["Esik Degeri", report["threshold"]])
    writer.writerow(["Toplam Hata Sayisi", report["total_defects"]])
    writer.writerow([])
    writer.writerow(["Hata Tipi", "Metre", "Guven Skoru", "Zaman", "Bounding Box"])

    for detection in report["detections"]:
        writer.writerow(
            [
                detection.get("defect_type", ""),
                detection.get("meter", ""),
                detection.get("confidence", ""),
                detection.get("timestamp", ""),
                detection.get("bbox", ""),
            ]
        )

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="yuzey-hata-raporu.csv"'},
    )


def _build_report(payload: ReportRequest) -> dict:
    detections = payload.detections
    return {
        "product_name": payload.product_name,
        "product_tag": payload.product_tag,
        "threshold": payload.threshold,
        "total_defects": len(detections),
        "defect_summary": [
            {
                "defect_type": detection.get("defect_type"),
                "meter": detection.get("meter"),
            }
            for detection in detections
        ],
        "detections": detections,
    }


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str) -> FileResponse:
    index_file = frontend_dist / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend build not found")
    return FileResponse(index_file)


if __name__ == "__main__":
    import uvicorn

    module_name = "app.main:app" if __package__ == "app" else "backend.app.main:app"
    uvicorn.run(module_name, host="127.0.0.1", port=8000, reload=True)
