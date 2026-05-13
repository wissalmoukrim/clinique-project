import { Navigate } from "react-router-dom";
import { getAccessToken, getCurrentUser, isTokenExpired, logout } from "../api/client";

const ROLE_HOME = {
  admin: "/admin",
  medecin: "/medecin",
  patient: "/patient",
  secretaire: "/secretaire",
  infirmier: "/infirmier",
  comptable: "/comptable",
  securite: "/securite",
  chauffeur: "/chauffeur",
};

function ProtectedRoute({ children, allowedRoles = [] }) {
  const token = getAccessToken();
  const user = getCurrentUser();

  if (!token || !user || isTokenExpired(token)) {
    logout();
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to={ROLE_HOME[user.role] || "/"} replace />;
  }

  return children;
}

export default ProtectedRoute;
