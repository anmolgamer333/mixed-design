import { useState } from "react";
import { api } from "../api/client";

export function ImportExportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
  const serverBase = base.replace(/\/api$/, "");

  const upload = async () => {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    const res = await api.post("/mixes/import", fd, { headers: { "Content-Type": "multipart/form-data" } });
    setMessage(`Imported ${res.data.imported} of ${res.data.total_rows} rows`);
  };

  return (
    <>
      <div className="card">
        <h3>Bulk Import</h3>
        <p>Upload CSV or Excel to add many mix designs.</p>
        <input type="file" accept=".csv,.xlsx" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <div className="actions" style={{ marginTop: 10 }}>
          <button className="btn" onClick={upload}>Import File</button>
          <a className="btn alt" href={`${serverBase}/sample_data/mix_bulk_import_sample.csv`}>Sample Import File</a>
        </div>
        {message ? <p>{message}</p> : null}
      </div>

      <div className="card">
        <h3>Export Tools</h3>
        <div className="actions">
          <a className="btn" href={`${base}/mixes/database/export`}>Export Complete Database (JSON)</a>
          <a className="btn" href={`${base}/mixes/qr/sheet?limit=60`}>Generate QR Sheet PDF</a>
        </div>
      </div>
    </>
  );
}
