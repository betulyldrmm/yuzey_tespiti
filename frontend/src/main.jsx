import React from "react";
import { createRoot } from "react-dom/client";
import { Download, Play, RotateCcw, Square } from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

function App() {
  const [productName, setProductName] = React.useState("Aluminyum Rulo A");
  const [productTag, setProductTag] = React.useState("AL-2026-001");
  const [threshold, setThreshold] = React.useState(0.65);
  const [detections, setDetections] = React.useState([]);
  const [status, setStatus] = React.useState("idle");
  const [error, setError] = React.useState("");
  const [reportType, setReportType] = React.useState("json");

  const productPayload = {
    product_name: productName,
    product_tag: productTag,
    threshold: Number(threshold),
  };

  async function postJson(path, body = undefined) {
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      throw new Error(`Istek basarisiz: ${response.status}`);
    }

    return response;
  }

  async function startDetection() {
    setError("");
    try {
      const response = await postJson("/api/detections/start", productPayload);
      const data = await response.json();
      setStatus(data.status);
      setDetections(data.detections);
    } catch (err) {
      setError(err.message);
    }
  }

  async function stopDetection() {
    setError("");
    try {
      const response = await postJson("/api/detections/stop");
      const data = await response.json();
      setStatus(data.status);
      setDetections(data.detections);
    } catch (err) {
      setError(err.message);
    }
  }

  async function resetDetection() {
    setError("");
    try {
      const response = await postJson("/api/detections/reset");
      const data = await response.json();
      setStatus(data.status);
      setDetections(data.detections);
    } catch (err) {
      setError(err.message);
    }
  }

  async function downloadReport() {
    setError("");
    const payload = { ...productPayload, detections };
    const endpoint = reportType === "csv" ? "/api/reports/csv" : "/api/reports/json";

    try {
      const response = await postJson(endpoint, payload);
      const blob = await response.blob();
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = href;
      link.download = reportType === "csv" ? "yuzey-hata-raporu.csv" : "yuzey-hata-raporu.json";
      link.click();
      URL.revokeObjectURL(href);
    } catch (err) {
      setError(err.message);
    }
  }

  const statusLabel = {
    idle: "Hazir",
    running: "Calisiyor",
    stopped: "Durduruldu",
  }[status];

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Aluminyum yuzey kalite kontrol</p>
          <h1>Mini Yuzey Hatasi Tespit Uygulamasi</h1>
        </div>
        <div className={`status-pill ${status}`}>{statusLabel}</div>
      </section>

      <section className="workspace">
        <aside className="control-panel">
          <label>
            Urun adi
            <input value={productName} onChange={(event) => setProductName(event.target.value)} />
          </label>

          <label>
            Urun ID / etiketi
            <input value={productTag} onChange={(event) => setProductTag(event.target.value)} />
          </label>

          <label>
            Esik degeri
            <div className="threshold-row">
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={threshold}
                onChange={(event) => setThreshold(event.target.value)}
              />
              <input
                className="threshold-input"
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={threshold}
                onChange={(event) => setThreshold(event.target.value)}
              />
            </div>
          </label>

          <div className="button-grid">
            <button onClick={startDetection}>
              <Play size={18} />
              Baslat
            </button>
            <button className="secondary" onClick={stopDetection}>
              <Square size={18} />
              Durdur
            </button>
            <button className="secondary" onClick={resetDetection}>
              <RotateCcw size={18} />
              Resetle
            </button>
          </div>

          <div className="report-controls">
            <div className="segmented" aria-label="Rapor formati">
              <button className={reportType === "json" ? "active" : ""} onClick={() => setReportType("json")}>
                JSON
              </button>
              <button className={reportType === "csv" ? "active" : ""} onClick={() => setReportType("csv")}>
                CSV
              </button>
            </div>
            <button className="download" onClick={downloadReport}>
              <Download size={18} />
              Rapor Olustur
            </button>
          </div>

          {error && <p className="error">{error}</p>}
        </aside>

        <section className="results-panel">
          <div className="metrics">
            <div>
              <span>Toplam hata</span>
              <strong>{detections.length}</strong>
            </div>
            <div>
              <span>Esik</span>
              <strong>{Number(threshold).toFixed(2)}</strong>
            </div>
            <div>
              <span>Urun</span>
              <strong>{productTag}</strong>
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Hata tipi</th>
                  <th>Metre bilgisi</th>
                  <th>Guven skoru</th>
                  <th>Zaman bilgisi</th>
                </tr>
              </thead>
              <tbody>
                {detections.length === 0 ? (
                  <tr>
                    <td className="empty" colSpan="4">
                      Tespit sonucu yok
                    </td>
                  </tr>
                ) : (
                  detections.map((detection) => (
                    <tr key={detection.id}>
                      <td>{detection.defect_type}</td>
                      <td>{detection.meter.toFixed(2)} m</td>
                      <td>{Math.round(detection.confidence * 100)}%</td>
                      <td>{new Date(detection.timestamp).toLocaleString("tr-TR")}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
