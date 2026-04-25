import { Navigate } from "react-router-dom";

function PrivateRoute({ children, roles }) {
  const isLoggedIn = localStorage.getItem("loggedIn");
  const role = localStorage.getItem("role");

  if (!isLoggedIn) {
    return <Navigate to="/" />;
  }

  if (roles && !roles.includes(role)) {
    return <Navigate to="/dashboard" />;
  }

  return children;
}

export default PrivateRoute;