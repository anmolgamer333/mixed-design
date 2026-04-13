import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { MixDesign } from "../types";

interface Revision {
  id: number;
  revision_label: string;
  changed_parameter: string;
  old_value: string;
  new_value: string;
  warning_message: string;
  created_at: string;
}

export function MixDetailPage() {
  const { slug } = useParams();
  const [mix, setMix] = useState<MixDesign | null>(null);
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [param, setParam] = useState("water_cement_ratio");
  const [value, setValue] = useState("0.45");
  const [warnings, setWarnings] = useState<string[]>([]);

  const load = async () => {
    const res = await api.get<MixDesign>(`/mixes/${slug}`);
    setMix(res.data);
    const rev = await api.get<Revision[]>(`/mixes/${slug}/revisions`);
    setRevisions(rev.data);
  };

  useEffect(() => {
    load();
  }, [slug]);

  const tableRows = useMemo(() => {
    if (!mix) return [];
    return [
      ["Grade of concrete", "fck", mix.concrete_grade, "-", "Specified grade"],
      ["Target mean strength", "f'cm", mix.target_mean_strength, "MPa", "Design target"],
      ["Water-cement ratio", "w/c", mix.water_cement_ratio, "-", "Durability/performance control"],
      ["Water content", "W", mix.water_content_kg_m3, "kg/m3", "Base water demand"],
      ["Cement content", "C", mix.cement_content_kg_m3, "kg/m3", "Derived from w/c"],
      ["Fine aggregate quantity", "FA", mix.fine_agg_content_kg_m3, "kg/m3", "SSD basis"],
      ["Coarse aggregate quantity", "CA", mix.coarse_agg_content_kg_m3, "kg/m3", "SSD basis"],
      ["Admixture content", "Adm", `${mix.admixture_type} (${mix.admixture_dosage_pct}%)`, "%", "By cement mass"],
      ["Moisture correction", "MC", `${mix.moisture_correction_fine_pct}/${mix.moisture_correction_coarse_pct}`, "%", "Fine/Coarse"],
      ["Water adjustment", "Wadj", mix.field_water_adjustment_kg, "kg/m3", "From moisture-absorption"],
      ["Final batch quantities", "Batch", `W:${mix.final_batch_water_kg}, C:${mix.final_batch_cement_kg}, FA:${mix.final_batch_fine_agg_kg}, CA:${mix.final_batch_coarse_agg_kg}`, "kg/m3", "Field batch values"],
      ["Mix proportion", "-", mix.mix_proportion_by_weight, "by wt", "C:FA:CA with w/c"],
      ["Assumptions", "-", mix.assumptions, "-", mix.remarks]
    ];
  }, [mix]);

  const recalc = async () => {
    const res = await api.post(`/mixes/${slug}/recalculate`, {
      parameter: param,
      new_value: Number(value),
      save_revision: true
    });
    setWarnings(res.data.warnings || []);
    await load();
  };

  if (!mix) return <div className="card">Loading mix details...</div>;

  const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

  return (
    <>
      <div className="card">
        <h2>{mix.mix_name} <span className="badge">{mix.mix_id}</span></h2>
        <p>Grade: <strong>{mix.concrete_grade}</strong> | Method: {mix.design_method} | Exposure: {mix.exposure_condition}</p>
        <div className="actions">
          <a className="btn" href={`${base}/mixes/${mix.slug}/export/csv`}>Download CSV</a>
          <a className="btn" href={`${base}/mixes/${mix.slug}/export/xlsx`}>Download Excel</a>
          <a className="btn" href={`${base}/mixes/${mix.slug}/export/pdf`}>Download PDF</a>
          <button className="btn alt" onClick={() => window.print()}>Print</button>
          <button className="btn alt" onClick={() => navigator.clipboard.writeText(window.location.href)}>Copy Link</button>
          <a className="btn alt" href={`${base}/mixes/${mix.slug}/qr/png`}>Download QR PNG</a>
          <a className="btn alt" href={`${base}/mixes/${mix.slug}/qr/svg`}>Download QR SVG</a>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>Mix Design Table</h3>
          <table>
            <thead>
              <tr><th>Parameter</th><th>Symbol</th><th>Value</th><th>Unit</th><th>Remarks / Derived From</th></tr>
            </thead>
            <tbody>
              {tableRows.map((row, idx) => (
                <tr key={idx}>{row.map((cell, cIdx) => <td key={cIdx}>{cell as string}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>

        <div>
          <div className="card">
            <h3>QR Preview</h3>
            <img alt="QR Code" src={`${base}/mixes/${mix.slug}/qr/png`} style={{ maxWidth: 180 }} />
            <p><small>Scan to open direct record: <code>/mixes/{mix.slug}</code></small></p>
          </div>

          <div className="card">
            <h3>Editable Recalculation</h3>
            <div className="grid-2">
              <select value={param} onChange={(e) => setParam(e.target.value)}>
                <option value="water_cement_ratio">Water-cement ratio</option>
                <option value="slump_mm">Slump (mm)</option>
                <option value="admixture_dosage_pct">Admixture dosage (%)</option>
                <option value="moisture_correction_fine_pct">Moisture correction fine (%)</option>
                <option value="moisture_correction_coarse_pct">Moisture correction coarse (%)</option>
              </select>
              <input value={value} onChange={(e) => setValue(e.target.value)} />
            </div>
            <button className="btn" onClick={recalc} style={{ marginTop: 10 }}>Recalculate + Save Revision</button>
            {warnings.map((w, i) => <div className="warning" key={i}>{w}</div>)}
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Revision History</h3>
        <table>
          <thead>
            <tr><th>Label</th><th>Parameter</th><th>Old</th><th>New</th><th>Warnings</th><th>Date</th></tr>
          </thead>
          <tbody>
            {revisions.map((r) => (
              <tr key={r.id}>
                <td>{r.revision_label}</td>
                <td>{r.changed_parameter}</td>
                <td>{r.old_value}</td>
                <td>{r.new_value}</td>
                <td>{r.warning_message || "-"}</td>
                <td>{new Date(r.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
