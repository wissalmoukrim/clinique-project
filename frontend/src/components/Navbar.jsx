import { Link, NavLink } from "react-router-dom";
import { getCurrentUser } from "../api/client";
import AppLayout from "./AppLayout";

function Navbar({ publicMode = false }) {
  const user = getCurrentUser();

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

  return <AppLayout />;
}

export default Navbar;
