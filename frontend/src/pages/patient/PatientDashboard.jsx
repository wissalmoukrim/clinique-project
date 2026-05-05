import { useEffect, useState } from "react";
import { apiFetch } from "../../api/client";
import Navbar from "../../components/Navbar";

const RDV_STATUS_LABELS = {
  en_attente: "EN ATTENTE",
  confirme: "CONFIRME",
  annule: "ANNULE",
  termine: "TERMINE",
};

function rdvStatusLabel(statut) {
  return RDV_STATUS_LABELS[statut] || String(statut || "-").replace("_", " ").toUpperCase();
}

function formatDate(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(date);
}

function isFacturePaid(facture) {
  return ["paye", "payé", "payÃ©", "payÃƒÂ©"].includes(facture.statut);
}

function PatientDashboard() {
  const [rendezvous, setRendezvous] = useState([]);
  const [factures, setFactures] = useState([]);
  const [consultations, setConsultations] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [rdvData, factureData, consultationData] = await Promise.all([
          apiFetch("/rendezvous/"),
          apiFetch("/facturation/"),
          apiFetch("/consultations/"),
        ]);

        setRendezvous(Array.isArray(rdvData) ? rdvData : []);
        setFactures(Array.isArray(factureData) ? factureData : []);
        setConsultations(Array.isArray(consultationData) ? consultationData : []);
      } catch (err) {
        setError(err.message || "Erreur de chargement");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  return (
    <>
      <Navbar />
      <main className="page">
        <h1>Dashboard Patient</h1>

        {loading && <p>Chargement...</p>}
        {error && <p className="error-message">{error}</p>}

        {!loading && (
          <>
            <div className="stats">
              <Stat label="Rendez-vous" value={rendezvous.length} />
              <Stat label="Consultations" value={consultations.length} />
              <Stat label="Factures" value={factures.length} />
              <Stat label="A payer" value={factures.filter((facture) => !isFacturePaid(facture)).length} />
            </div>

            <section className="panel">
              <h2>Mes rendez-vous</h2>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Medecin</th>
                    <th>Date</th>
                    <th>Heure</th>
                    <th>Statut</th>
                  </tr>
                </thead>
                <tbody>
                  {rendezvous.map((rdv) => (
                    <tr key={rdv.id}>
                      <td>{rdv.id}</td>
                      <td>{rdv.medecin}</td>
                      <td>{rdv.date}</td>
                      <td>{rdv.heure}</td>
                      <td><span className={`badge badge-${rdv.statut}`}>{rdvStatusLabel(rdv.statut)}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section className="panel">
              <h2>Historique medical</h2>
              {consultations.length === 0 ? (
                <p>Aucune consultation disponible</p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Date consultation</th>
                      <th>Medecin</th>
                      <th>Diagnostic</th>
                      <th>Traitement</th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {consultations.map((consultation) => (
                      <tr key={consultation.id}>
                        <td>{formatDate(consultation.date)}</td>
                        <td>{consultation.medecin}</td>
                        <td>{consultation.diagnostic}</td>
                        <td>{consultation.traitement || "-"}</td>
                        <td>{consultation.notes || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>

            <section className="panel">
              <h2>Mes factures</h2>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Montant</th>
                    <th>Date</th>
                    <th>Statut</th>
                  </tr>
                </thead>
                <tbody>
                  {factures.map((facture) => (
                    <tr key={facture.id}>
                      <td>{facture.id}</td>
                      <td>{facture.montant}</td>
                      <td>{facture.date}</td>
                      <td><span className="badge">{facture.statut}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </>
        )}
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

export default PatientDashboard;
