import { useEffect, useState } from "react";
import { apiFetch } from "../../api/client";
import Navbar from "../../components/Navbar";

function MedecinDashboard() {
  const [rendezvous, setRendezvous] = useState([]);
  const [consultations, setConsultations] = useState([]);
  const [consultationForm, setConsultationForm] = useState({
    rdv_id: "",
    diagnostic: "",
    notes: "",
    traitement: "",
  });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const loadDashboard = async () => {
    setError("");
    try {
      const [rdvData, consultationData] = await Promise.all([
        apiFetch("/rendezvous/"),
        apiFetch("/consultations/"),
      ]);
      setRendezvous(Array.isArray(rdvData) ? rdvData : []);
      setConsultations(Array.isArray(consultationData) ? consultationData : []);
    } catch (err) {
      setError(err.message || "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const confirmedRendezvous = rendezvous.filter((rdv) => rdv.statut === "confirme");
  const consultedRdvIds = new Set(consultations.map((consultation) => consultation.rendezvous_id));
  const selectedRdv = confirmedRendezvous.find((rdv) => String(rdv.id) === String(consultationForm.rdv_id));

  const selectRdvForConsultation = (rdv) => {
    setMessage("");
    setError("");
    setConsultationForm({
      rdv_id: rdv.id,
      diagnostic: "",
      notes: "",
      traitement: "",
    });
  };

  const createConsultation = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");

    try {
      await apiFetch("/consultations/", {
        method: "POST",
        body: consultationForm,
      });
      setConsultationForm({ rdv_id: "", diagnostic: "", notes: "", traitement: "" });
      setMessage("Consultation ajoutee");
      loadDashboard();
    } catch (err) {
      setError(err.message || "Creation consultation impossible");
    }
  };

  return (
    <>
      <Navbar />
      <main className="page">
        <h1>Dashboard Medecin</h1>

        <div className="stats">
          <Stat label="Rendez-vous" value={rendezvous.length} />
          <Stat label="En attente" value={rendezvous.filter((rdv) => rdv.statut === "en_attente").length} />
          <Stat label="Confirmes" value={confirmedRendezvous.length} />
          <Stat label="Consultations" value={consultations.length} />
        </div>

        {error && <p className="error-message">{error}</p>}
        {message && <p className="success-message">{message}</p>}

        <section className="panel">
          <h2>Ajouter une consultation</h2>
          <form className="stack-form" onSubmit={createConsultation}>
            <input
              type="number"
              placeholder="ID du rendez-vous confirme"
              value={consultationForm.rdv_id}
              onChange={(e) => setConsultationForm({ ...consultationForm, rdv_id: e.target.value })}
              required
            />
            {selectedRdv && (
              <p>
                Patient: <strong>{selectedRdv.patient}</strong> - {selectedRdv.date} a {selectedRdv.heure}
              </p>
            )}
            <textarea
              placeholder="Diagnostic"
              value={consultationForm.diagnostic}
              onChange={(e) => setConsultationForm({ ...consultationForm, diagnostic: e.target.value })}
              required
            />
            <textarea
              placeholder="Notes"
              value={consultationForm.notes}
              onChange={(e) => setConsultationForm({ ...consultationForm, notes: e.target.value })}
            />
            <textarea
              placeholder="Traitement"
              value={consultationForm.traitement}
              onChange={(e) => setConsultationForm({ ...consultationForm, traitement: e.target.value })}
            />
            <button type="submit" disabled={!consultationForm.rdv_id}>Enregistrer</button>
          </form>
        </section>

        <section className="panel">
          <h2>Mes rendez-vous confirmes</h2>

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
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {confirmedRendezvous.map((rdv) => {
                  const alreadyConsulted = consultedRdvIds.has(rdv.id);

                  return (
                    <tr key={rdv.id}>
                      <td>{rdv.id}</td>
                      <td>{rdv.patient}</td>
                      <td>{rdv.date}</td>
                      <td>{rdv.heure}</td>
                      <td><span className={`badge badge-${rdv.statut}`}>{rdv.statut}</span></td>
                      <td>
                        <button
                          type="button"
                          onClick={() => selectRdvForConsultation(rdv)}
                          disabled={alreadyConsulted}
                        >
                          {alreadyConsulted ? "Deja creee" : "Ajouter consultation"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {confirmedRendezvous.length === 0 && (
                  <tr>
                    <td colSpan="6">Aucun rendez-vous confirme.</td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </section>
      </main>
    </>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default MedecinDashboard;
