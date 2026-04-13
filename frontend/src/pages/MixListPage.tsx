import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { MixDesign, MixListResponse } from "../types";

export function MixListPage() {
  const [items, setItems] = useState<MixDesign[]>([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState("");
  const [grade, setGrade] = useState("");
  const [sortBy, setSortBy] = useState("recent");

  const fetchData = async () => {
    const res = await api.get<MixListResponse>("/mixes", { params: { q: query || undefined, grade: grade || undefined, sort_by: sortBy, page_size: 50 } });
    setItems(res.data.items);
    setTotal(res.data.total);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const gradeOptions = useMemo(() => ["M20", "M25", "M30", "M35", "M40", "M45", "M50"], []);

  return (
    <div className="card">
      <h3>Mix Designs List</h3>
      <div className="grid-4" style={{ marginBottom: 10 }}>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by mix name, ID, remarks" />
        <select value={grade} onChange={(e) => setGrade(e.target.value)}>
          <option value="">All grades</option>
          {gradeOptions.map((g) => <option key={g}>{g}</option>)}
        </select>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          <option value="recent">Most recent</option>
          <option value="alphabetical">Alphabetical</option>
          <option value="grade">Strength grade</option>
          <option value="mix_id">Mix ID</option>
        </select>
        <button className="btn" onClick={fetchData}>Apply</button>
      </div>
      <p>Total records: <strong>{total}</strong></p>

      <table>
        <thead>
          <tr>
            <th>Mix ID</th>
            <th>Name</th>
            <th>Grade</th>
            <th>Method</th>
            <th>Cement</th>
            <th>Category</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((m) => (
            <tr key={m.id}>
              <td>{m.mix_id}</td>
              <td>{m.mix_name}</td>
              <td><span className="badge">{m.concrete_grade}</span></td>
              <td>{m.design_method}</td>
              <td>{m.cement_type}</td>
              <td>{m.category}</td>
              <td>{m.status}</td>
              <td className="actions">
                <Link className="btn alt" to={`/mixes/${m.slug}`}>Open</Link>
                <Link className="btn alt" to={`/mixes/${m.slug}/edit`}>Edit</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
