import { useEffect, useState } from "react";
import { apiFetch } from "../../api/client";
import Navbar from "../../components/Navbar";

function MedecinDashboard() {
  const [rendezvous, setRendezvous] = useState([]);
  const [consultationForm, setConsultationForm] = useState({
    rdv_id: "",
    diagnostic: "",
    traitement: "",
  });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const loadRendezvous = async () => {
    setError("");
    try {
      const data = await apiFetch("/rendezvous/");
      setRendezvous(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRendezvous();
  }, []);

  const createConsultation = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");

    try {
      await apiFetch("/consultations/", {
        method: "POST",
        body: consultationForm,
      });
      setConsultationForm({ rdv_id: "", diagnostic: "", traitement: "" });
      setMessage("Consultation ajoutee");
    } catch (err) {
      setError(err.message || "Creation consultation impossible");
    }
  };

  const updateRdvStatus = async (rdvId, statut) => {
    setError("");
    setMessage("");

    try {
      await apiFetch(`/rendezvous/${rdvId}/status/`, {
        method: "POST",
        body: { statut },
      });
      setMessage("Rendez-vous mis a jour");
      await loadRendezvous();
    } catch (err) {
      setError(err.message || "Mise a jour impossible");
    }
  };

  return (
    <>
      <Navbar />
      <main className="page">
        <h1>Dashboard Medecin</h1>

        {error && <p className="error-message">{error}</p>}
        {message && <p className="success-message">{message}</p>}

        <section className="panel">
          <h2>Add Consultation</h2>
          <form className="inline-form" onSubmit={createConsultation}>
            <input
              type="number"
              placeholder="rdv_id"
              value={consultationForm.rdv_id}
              onChange={(e) => setConsultationForm({ ...consultationForm, rdv_id: e.target.value })}
              required
            />
            <input
              placeholder="diagnostic"
              value={consultationForm.diagnostic}
              onChange={(e) => setConsultationForm({ ...consultationForm, diagnostic: e.target.value })}
              required
            />
            <input
              placeholder="traitement"
              value={consultationForm.traitement}
              onChange={(e) => setConsultationForm({ ...consultationForm, traitement: e.target.value })}
            />
            <button type="submit">Add</button>
          </form>
        </section>

        <section className="panel">
          <h2>Mes rendez-vous</h2>

          {loading && <p>Chargement...</p>}
          {!loading && (
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Patient</th>
                  <th>Date</th>
                  <th>Heure</th>
                  <th>Statut</th>
                  <th>Update</th>
                </tr>
              </thead>
              <tbody>
                {rendezvous.map((rdv) => (
                  <tr key={rdv.id}>
                    <td>{rdv.id}</td>
                    <td>{rdv.patient}</td>
                    <td>{rdv.date}</td>
                    <td>{rdv.heure}</td>
                    <td>{rdv.statut}</td>
                    <td>
                      <button type="button" onClick={() => updateRdvStatus(rdv.id, "validé")}>
                        Update
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </main>
    </>
  );
}

export default MedecinDashboard;
