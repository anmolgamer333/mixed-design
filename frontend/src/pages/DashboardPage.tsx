import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

interface DashboardSummary {
  total_mixes: number;
  approved: number;
  trial: number;
  archived: number;
  recent: Array<{ mix_id: string; mix_name: string; slug: string; grade: string; updated_at: string }>;
}

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    api.get("/mixes/dashboard/summary").then((res) => setSummary(res.data));
  }, []);

  if (!summary) return <div className="card">Loading dashboard...</div>;

  return (
    <>
      <div className="grid-4">
        <div className="card stat"><strong>{summary.total_mixes}</strong><small>Total Mixes</small></div>
        <div className="card stat"><strong>{summary.approved}</strong><small>Approved</small></div>
        <div className="card stat"><strong>{summary.trial}</strong><small>Trial</small></div>
        <div className="card stat"><strong>{summary.archived}</strong><small>Archived</small></div>
      </div>

      <div className="card">
        <h3>Recent Mix Designs</h3>
        <table>
          <thead>
            <tr>
              <th>Mix ID</th>
              <th>Name</th>
              <th>Grade</th>
              <th>Updated</th>
              <th>Open</th>
            </tr>
          </thead>
          <tbody>
            {summary.recent.map((item) => (
              <tr key={item.mix_id}>
                <td>{item.mix_id}</td>
                <td>{item.mix_name}</td>
                <td><span className="badge">{item.grade}</span></td>
                <td>{new Date(item.updated_at).toLocaleString()}</td>
                <td><Link className="btn alt" to={`/mixes/${item.slug}`}>Open</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
