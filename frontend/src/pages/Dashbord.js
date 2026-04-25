import { useEffect, useState } from "react";
import { apiFetch } from "../api/client";

function Dashboard() {
  const username = localStorage.getItem("username");
  const role = localStorage.getItem("role");

  const [rdvs, setRdvs] = useState([]);

  useEffect(() => {
    fetchRDV();
  }, []);

  const fetchRDV = async () => {
    try {
      const data = await apiFetch("/rendezvous/");
      setRdvs(data);
    } catch (err) {
      console.error(err);
    }
  };

  const updateStatut = async (id, statut) => {
    await apiFetch(`/rendezvous/${id}/status/`, {
      method: "POST",
      body: JSON.stringify({ statut })
    });

    fetchRDV();
  };

  const logout = () => {
    localStorage.clear();
    window.location.href = "/";
  };

  return (
    <div>
      <h1>Dashboard</h1>
      <h2>{username} ({role})</h2>

      {rdvs.map(r => (
        <div key={r.id}>
          <p>{r.patient} - {r.medecin}</p>
          <p>{r.date} {r.heure}</p>
          <p>{r.statut}</p>

          {(role === "admin" || role === "secretaire") && (
            <>
              <button onClick={() => updateStatut(r.id, "validé")}>Valider</button>
              <button onClick={() => updateStatut(r.id, "annulé")}>Annuler</button>
            </>
          )}
        </div>
      ))}

      <button onClick={logout}>Logout</button>
    </div>
  );
}

export default Dashboard;