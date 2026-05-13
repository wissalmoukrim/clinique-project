import { Link, NavLink } from "react-router-dom";

const ROLE_LINKS = {
  admin: [
    { to: "/admin", label: "Vue generale", icon: "A" },
    { to: "/admin", label: "Patients", icon: "P" },
    { to: "/admin#personnel", label: "Personnel", icon: "U" },
    { to: "/admin", label: "Securite", icon: "S" },
  ],
  medecin: [
    { to: "/medecin", label: "Rendez-vous", icon: "R" },
    { to: "/medecin", label: "Consultations", icon: "C" },
  ],
  patient: [
    { to: "/patient", label: "Mes RDV", icon: "R" },
    { to: "/patient", label: "Factures", icon: "F" },
  ],
  secretaire: [{ to: "/secretaire", label: "Reception", icon: "R" }],
  infirmier: [{ to: "/infirmier", label: "Hospitalisation", icon: "H" }],
  comptable: [{ to: "/comptable", label: "Facturation", icon: "F" }],
  securite: [{ to: "/securite", label: "Visiteurs", icon: "V" }],
  chauffeur: [{ to: "/chauffeur", label: "Ambulance", icon: "A" }],
};

function Sidebar({ user }) {
  const links = ROLE_LINKS[user?.role] || [];

  return (
    <aside className="sidebar">
      <Link className="sidebar-brand" to="/">
        <span className="brand-mark">C</span>
        <span>
          Clinique
          <small>Medicale Elite</small>
        </span>
      </Link>

      <nav className="sidebar-nav">
        {links.map((link, index) => (
          <NavLink key={`${link.label}-${index}`} to={link.to}>
            <span className="nav-icon">{link.icon}</span>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;
