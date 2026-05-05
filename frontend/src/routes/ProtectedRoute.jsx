import { Navigate } from "react-router-dom";
import { getAccessToken, getCurrentUser, isTokenExpired, logout } from "../api/client";

const ROLE_HOME = {
  admin: "/admin",
  medecin: "/medecin",
  patient: "/patient",
  secretaire: "/dashboard",
  infirmier: "/dashboard",
  comptable: "/dashboard",
  securite: "/dashboard",
  chauffeur: "/dashboard",
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
