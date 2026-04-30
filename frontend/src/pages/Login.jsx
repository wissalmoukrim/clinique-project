import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { getAccessToken, getCurrentUser, login } from "../api/client";

export function getRedirectPath(role) {
  switch (role) {
    case "admin":
      return "/admin";
    case "medecin":
      return "/medecin";
    case "patient":
      return "/patient";
    default:
      return "/dashboard";
  }
}

function Login() {
  const navigate = useNavigate();
  const token = getAccessToken();
  const user = getCurrentUser();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (token && user) {
    return <Navigate to={getRedirectPath(user.role)} replace />;
  }

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await login(username, password);
      navigate(getRedirectPath(data.user.role), { replace: true });
    } catch (err) {
      setError(err.message || "Erreur login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>Connexion</h1>

        {error && <p className="error-message">{error}</p>}

        <label htmlFor="username">Username</label>
        <input
          id="username"
          type="text"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoComplete="username"
          required
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          required
        />

        <button type="submit" disabled={loading}>
          {loading ? "Connexion..." : "Se connecter"}
        </button>
      </form>
    </main>
  );
}

export default Login;
