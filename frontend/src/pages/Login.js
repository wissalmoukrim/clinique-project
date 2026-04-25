import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api/client";

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const data = await apiFetch("/auth/login/", {
        method: "POST",
        body: JSON.stringify({ username, password })
      });

      localStorage.setItem("loggedIn", "true");
      localStorage.setItem("username", data.username);
      localStorage.setItem("role", data.role);

      navigate("/dashboard");

    } catch (err) {
      setMessage(err.error || "Login failed ❌");
    }
  };

  return (
    <div>
      <h1>Login</h1>

      <input value={username} onChange={e => setUsername(e.target.value)} placeholder="username" />
      <br /><br />
      <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="password" />

      <br /><br />

      <button onClick={handleLogin}>Login</button>

      <br /><br />

      <button onClick={() => navigate("/register")}>Register</button>

      <p>{message}</p>
    </div>
  );
}

export default Login;