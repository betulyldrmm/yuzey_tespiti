from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class BoundingBox:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class DetectionResult:
    id: str
    defect_type: str
    confidence: float
    meter: float
    bbox: BoundingBox
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["bbox"] = asdict(self.bbox)
        return payload


class DetectionService:
    """YOLO defect detection service with mock fallback."""

    def __init__(self, model_path: str | None = None) -> None:
        self.model_path = Path(model_path) if model_path else self._find_default_model_path()
        self.model: Any | None = None

        if self.model_path:
            self.load_model(self.model_path)

    def load_model(self, model_path: str | Path) -> None:
        """Load a YOLO model from disk. Falls back to mock mode on failure."""
        resolved_path = Path(model_path)
        if not resolved_path.is_absolute():
            resolved_path = Path.cwd() / resolved_path

        self.model_path = resolved_path
        self.model = None

        if not resolved_path.exists():
            return

        try:
            from ultralytics import YOLO
        except ImportError:
            return

        try:
            self.model = YOLO(str(resolved_path))
        except Exception:
            self.model = None

    def detect(
        self,
        image: Any | None = None,
        image_path: str | Path | None = None,
        threshold: float = 0.5,
    ) -> list[DetectionResult]:
        """Detect defects from an image object or image path.

        Uses YOLO when a model and source image are available. Otherwise returns
        mock data so the application remains usable during development.
        """
        if self.model is not None and (image is not None or image_path is not None):
            return self._detect_with_model(image=image, image_path=image_path, threshold=threshold)

        return self._mock_detect(threshold=threshold)

    def _detect_with_model(
        self,
        image: Any | None,
        image_path: str | Path | None,
        threshold: float,
    ) -> list[DetectionResult]:
        source = image if image is not None else str(image_path)
        if source is None:
            return self._mock_detect(threshold=threshold)

        try:
            predictions = self.model.predict(source=source, conf=threshold, verbose=False)
        except Exception:
            return self._mock_detect(threshold=threshold)

        detections: list[DetectionResult] = []
        timestamp = datetime.now(timezone.utc).isoformat()

        for prediction in predictions:
            boxes = getattr(prediction, "boxes", None)
            if boxes is None:
                continue

            names = getattr(prediction, "names", None) or getattr(self.model, "names", {})
            image_height, image_width = self._get_image_shape(prediction)

            for box in boxes:
                confidence = self._read_scalar(box.conf)
                if confidence < threshold:
                    continue

                class_id = int(self._read_scalar(box.cls))
                x1, y1, x2, y2 = self._read_xyxy(box)
                bbox = BoundingBox(
                    x=int(round(x1)),
                    y=int(round(y1)),
                    width=int(round(max(x2 - x1, 0))),
                    height=int(round(max(y2 - y1, 0))),
                )

                detections.append(
                    DetectionResult(
                        id=str(uuid4()),
                        defect_type=str(names.get(class_id, f"class_{class_id}")),
                        confidence=round(confidence, 3),
                        meter=self._estimate_meter(x1=x1, x2=x2, image_width=image_width),
                        bbox=bbox,
                        timestamp=timestamp,
                    )
                )

        return sorted(detections, key=lambda item: item.meter)

    def _find_default_model_path(self) -> Path | None:
        base_dir = Path(__file__).resolve().parent
        project_root = base_dir.parents[1]
        candidates = [
            base_dir / "best.pt",
            project_root / "best.pt",
            project_root / "best.pt ve ornekler" / "yolov11n" / "best.pt",
            project_root / "best.pt ve örnekler" / "yolov11n" / "best.pt",
        ]

        return next((path for path in candidates if path.exists()), None)

    def _read_scalar(self, value: Any) -> float:
        if hasattr(value, "item"):
            return float(value.item())
        if hasattr(value, "__len__"):
            return float(value[0])
        return float(value)

    def _read_xyxy(self, box: Any) -> tuple[float, float, float, float]:
        values = box.xyxy[0]
        if hasattr(values, "tolist"):
            values = values.tolist()
        return float(values[0]), float(values[1]), float(values[2]), float(values[3])

    def _get_image_shape(self, prediction: Any) -> tuple[int | None, int | None]:
        shape = getattr(prediction, "orig_shape", None)
        if not shape or len(shape) < 2:
            return None, None
        return int(shape[0]), int(shape[1])

    def _estimate_meter(self, x1: float, x2: float, image_width: int | None) -> float:
        if not image_width:
            return round(random.uniform(0.0, 120.0), 2)

        center_x = (x1 + x2) / 2
        return round(max(center_x / image_width, 0.0) * 120.0, 2)

    def _mock_detect(self, threshold: float) -> list[DetectionResult]:
        defect_types = ["Cizik", "Leke", "Gocuk", "Catlak", "Kaplama Hatasi"]
        count = random.randint(5, 12)
        detections: list[DetectionResult] = []

        for _ in range(count):
            confidence = round(random.uniform(max(threshold, 0.1), 0.99), 3)
            if confidence < threshold:
                continue

            detections.append(
                DetectionResult(
                    id=str(uuid4()),
                    defect_type=random.choice(defect_types),
                    confidence=confidence,
                    meter=round(random.uniform(0.0, 120.0), 2),
                    bbox=BoundingBox(
                        x=random.randint(0, 1200),
                        y=random.randint(0, 700),
                        width=random.randint(25, 180),
                        height=random.randint(20, 160),
                    ),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

        return sorted(detections, key=lambda item: item.meter)
