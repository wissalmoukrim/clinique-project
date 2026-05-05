import { useNavigate } from "react-router-dom";
import { getCurrentUser, logout } from "../api/client";
import Sidebar from "./Sidebar";

function AppLayout() {
  const navigate = useNavigate();
  const user = getCurrentUser();

  const handleLogout = () => {
    logout();
    navigate("/", { replace: true });
  };

  return (
    <>
      <Sidebar user={user} />
      <header className="topbar">
        <div>
          <span>Bienvenue</span>
          <strong>{user?.username || "Utilisateur"}</strong>
        </div>
        <div className="topbar-actions">
          <span className="role-badge">{user?.role || "role"}</span>
          <button type="button" className="button secondary-button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>
    </>
  );
}

export default AppLayout;
