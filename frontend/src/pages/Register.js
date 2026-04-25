import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch } from "../api/client";

function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("patient");

  const navigate = useNavigate();

  const handleRegister = async () => {
    try {
      await apiFetch("/auth/register/", {
        method: "POST",
        body: JSON.stringify({ username, password, role })
      });

      navigate("/");

    } catch (err) {
      alert(err.error);
    }
  };

  return (
    <div>
      <h1>Register</h1>

      <input value={username} onChange={e => setUsername(e.target.value)} placeholder="username" />
      <br /><br />

      <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="password" />
      <br /><br />

      <select value={role} onChange={e => setRole(e.target.value)}>
        <option value="patient">Patient</option>
        <option value="medecin">Médecin</option>
        <option value="secretaire">Secrétaire</option>
      </select>

      <br /><br />

      <button onClick={handleRegister}>Register</button>
    </div>
  );
}

export default Register;