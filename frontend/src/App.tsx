import { Link, NavLink, Route, Routes } from "react-router-dom";
import { DashboardPage } from "./pages/DashboardPage";
import { MixListPage } from "./pages/MixListPage";
import { MixDetailPage } from "./pages/MixDetailPage";
import { MixFormPage } from "./pages/MixFormPage";
import { ImportExportPage } from "./pages/ImportExportPage";
import { AdminSettingsPage } from "./pages/AdminSettingsPage";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/mixes", label: "Mix Designs" },
  { to: "/mixes/new", label: "Add Mix" },
  { to: "/import-export", label: "Import/Export" },
  { to: "/settings", label: "Admin Settings" }
];

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>CMIX</h1>
        <p>Concrete Mix Library</p>
        <nav>
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === "/"}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <strong>Concrete Mix Design Management</strong>
            <span> QR-enabled reference and revision platform</span>
          </div>
          <Link to="/mixes/new" className="btn">Create Mix</Link>
        </header>

        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/mixes" element={<MixListPage />} />
          <Route path="/mixes/new" element={<MixFormPage />} />
          <Route path="/mixes/:slug/edit" element={<MixFormPage />} />
          <Route path="/mixes/:slug" element={<MixDetailPage />} />
          <Route path="/import-export" element={<ImportExportPage />} />
          <Route path="/settings" element={<AdminSettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
