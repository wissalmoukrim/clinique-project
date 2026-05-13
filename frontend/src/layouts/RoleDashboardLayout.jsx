import Navbar from "../components/Navbar";
import { getCurrentUser } from "../api/client";
import { ROLE_LABELS } from "../pages/Dashboard";

function RoleDashboardLayout({ children }) {
  const user = getCurrentUser();
  const roleLabel = ROLE_LABELS[user?.role] || user?.role || "-";

  return (
    <>
      <Navbar />
      <main className="page shell-page">
        <h1>Dashboard {roleLabel}</h1>
        <div className="stats">
          <Stat label="Espace" value="1" />
          <Stat label="Role" value={roleLabel.toUpperCase()} />
        </div>
        <section className="panel profile-panel">
          <h2>{user?.username}</h2>
          <p>Role: <strong>{roleLabel}</strong></p>
        </section>
        {children}
      </main>
    </>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default RoleDashboardLayout;
