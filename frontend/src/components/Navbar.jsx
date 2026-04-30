import { Link, NavLink, useNavigate } from "react-router-dom";
import { getCurrentUser, logout } from "../api/client";

const PRIVATE_LINKS = {
  admin: [{ to: "/admin", label: "Admin" }],
  medecin: [{ to: "/medecin", label: "Medecin" }],
  patient: [{ to: "/patient", label: "Patient" }],
  secretaire: [{ to: "/dashboard", label: "Reception" }],
  infirmier: [{ to: "/dashboard", label: "Hospitalisation" }],
  comptable: [{ to: "/dashboard", label: "Facturation" }],
  securite: [{ to: "/dashboard", label: "Visiteurs" }],
  chauffeur: [{ to: "/dashboard", label: "Ambulance" }],
};

function Navbar({ publicMode = false }) {
  const navigate = useNavigate();
  const user = getCurrentUser();
  const links = user ? PRIVATE_LINKS[user.role] || [] : [];

  const handleLogout = () => {
    logout();
    navigate("/", { replace: true });
  };

  if (publicMode || !user) {
    return (
      <header className="public-navbar">
        <Link className="brand" to="/">Clinique Medicale Elite</Link>
        <nav>
          <NavLink to="/">Accueil</NavLink>
          <NavLink to="/specialites">Specialites</NavLink>
          <NavLink to="/medecins-public">Medecins</NavLink>
          <NavLink to="/prendre-rdv">Prendre RDV</NavLink>
          <NavLink to="/contact">Contact</NavLink>
          <NavLink className="nav-button" to="/login">Login</NavLink>
        </nav>
      </header>
    );
  }

  return (
    <>
      <header className="topbar">
        <div>
          <strong>Clinique Medicale Elite</strong>
          <span>{user.username} ({user.role})</span>
        </div>
        <button type="button" onClick={handleLogout}>Logout</button>
      </header>

      <aside className="sidebar">
        <Link className="brand" to="/">CME</Link>
        <nav>
          {links.map((link) => (
            <NavLink key={link.to} to={link.to}>{link.label}</NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
}

export default Navbar;
