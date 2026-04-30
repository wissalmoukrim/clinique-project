import { useEffect, useState } from "react";
import { apiFetch } from "../../api/client";
import Navbar from "../../components/Navbar";

function PatientDashboard() {
  const [rendezvous, setRendezvous] = useState([]);
  const [factures, setFactures] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [rdvData, factureData] = await Promise.all([
          apiFetch("/rendezvous/"),
          apiFetch("/facturation/"),
        ]);

        setRendezvous(Array.isArray(rdvData) ? rdvData : []);
        setFactures(Array.isArray(factureData) ? factureData : []);
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
                      <td>{rdv.statut}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
                      <td>{facture.statut}</td>
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

export default PatientDashboard;
