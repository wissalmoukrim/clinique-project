import { Navigate } from "react-router-dom";
import { getAccessToken, getCurrentUser, isTokenExpired, logout } from "../api/client";

function ProtectedRoute({ children, allowedRoles = [] }) {
  const token = getAccessToken();
  const user = getCurrentUser();

  if (!token || !user || isTokenExpired(token)) {
    logout();
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;
