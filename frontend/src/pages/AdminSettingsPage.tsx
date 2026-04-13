import { useState } from "react";
import { api } from "../api/client";

export function AdminSettingsPage() {
  const [msg, setMsg] = useState("");

  const regenerateQr = async () => {
    const res = await api.post("/mixes/qr/regenerate-all");
    setMsg(`Regenerated QR codes for ${res.data.updated} records`);
  };

  return (
    <div className="card">
      <h3>Admin Settings</h3>
      <p>Manage core maintenance actions for the concrete mix database.</p>
      <div className="actions">
        <button className="btn" onClick={regenerateQr}>Regenerate All QR Codes</button>
      </div>
      {msg ? <p>{msg}</p> : null}
    </div>
  );
}
