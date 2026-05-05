import { useEffect, useState } from "react";
import { apiFetch } from "../../api/client";
import Navbar from "../../components/Navbar";

function AdminDashboard() {
  const [patients, setPatients] = useState([]);
  const [medecins, setMedecins] = useState([]);
  const [rendezvous, setRendezvous] = useState([]);
  const [ambulances, setAmbulances] = useState([]);
  const [security, setSecurity] = useState({ summary: {}, logs: [], locked_users: [] });
  const [patientForm, setPatientForm] = useState({ user_id: "", telephone: "", adresse: "" });
  const [medecinForm, setMedecinForm] = useState({ user_id: "", specialite: "", telephone: "", experience: "" });
  const [ambulanceForm, setAmbulanceForm] = useState({ matricule: "", type: "standard" });
  const [rdvForm, setRdvForm] = useState({ patient_id: "", medecin_id: "", date: "", heure: "" });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const loadDashboard = async () => {
    setError("");
    try {
      const [patientsData, medecinsData, rendezvousData, ambulancesData, securityData] = await Promise.all([
        apiFetch("/patients/"),
        apiFetch("/medecins/"),
        apiFetch("/rendezvous/"),
        apiFetch("/ambulance/"),
        apiFetch("/core/security/"),
      ]);

      setPatients(Array.isArray(patientsData) ? patientsData : []);
      setMedecins(Array.isArray(medecinsData) ? medecinsData : []);
      setRendezvous(Array.isArray(rendezvousData) ? rendezvousData : []);
      setAmbulances(Array.isArray(ambulancesData) ? ambulancesData : []);
      setSecurity(securityData || { summary: {}, logs: [], locked_users: [] });
    } catch (err) {
      setError(err.message || "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const createPatient = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");

    try {
      await apiFetch("/patients/", { method: "POST", body: patientForm });
      setPatientForm({ user_id: "", telephone: "", adresse: "" });
      setMessage("Patient ajoute");
      await loadDashboard();
    } catch (err) {
      setError(err.message || "Creation patient impossible");
    }
  };

  const deletePatient = async (patientId) => {
    setMessage("");
    setError("");

    try {
      await apiFetch(`/patients/delete/${patientId}/`, { method: "DELETE" });
      setMessage("Patient supprime");
      await loadDashboard();
    } catch (err) {
      setError(err.message || "Suppression impossible");
    }
  };

  const createRdv = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");

    try {
      await apiFetch("/rendezvous/", { method: "POST", body: rdvForm });
      setRdvForm({ patient_id: "", medecin_id: "", date: "", heure: "" });
      setMessage("Rendez-vous ajoute");
      await loadDashboard();
    } catch (err) {
      setError(err.message || "Creation rendez-vous impossible");
    }
  };

  const createMedecin = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");

    try {
      await apiFetch("/medecins/", { method: "POST", body: medecinForm });
      setMedecinForm({ user_id: "", specialite: "", telephone: "", experience: "" });
      setMessage("Medecin ajoute");
      await loadDashboard();
    } catch (err) {
      setError(err.message || "Creation medecin impossible");
    }
  };

  const createAmbulance = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");

    try {
      await apiFetch("/ambulance/", { method: "POST", body: ambulanceForm });
      setAmbulanceForm({ matricule: "", type: "standard" });
      setMessage("Ambulance ajoutee");
      await loadDashboard();
    } catch (err) {
      setError(err.message || "Creation ambulance impossible");
    }
  };

  return (
    <>
      <Navbar />
      <main className="page">
        <h1>Dashboard Admin</h1>

        <div className="stats">
          <Stat label="Patients" value={patients.length} />
          <Stat label="Medecins" value={medecins.length} />
          <Stat label="Rendez-vous" value={rendezvous.length} />
          <Stat label="Ambulances" value={ambulances.length} />
          <Stat label="Alertes securite" value={security.summary?.alerts || 0} />
        </div>

        {loading && <p>Chargement...</p>}
        {error && <p className="error-message">{error}</p>}
        {message && <p className="success-message">{message}</p>}

        {!loading && (
          <>
            <section className="panel">
              <h2>Add Medecin</h2>
              <form className="inline-form" onSubmit={createMedecin}>
                <input
                  type="number"
                  placeholder="user_id"
                  value={medecinForm.user_id}
                  onChange={(e) => setMedecinForm({ ...medecinForm, user_id: e.target.value })}
                  required
                />
                <input
                  placeholder="specialite"
                  value={medecinForm.specialite}
                  onChange={(e) => setMedecinForm({ ...medecinForm, specialite: e.target.value })}
                  required
                />
                <input
                  placeholder="telephone"
                  value={medecinForm.telephone}
                  onChange={(e) => setMedecinForm({ ...medecinForm, telephone: e.target.value })}
                />
                <input
                  type="number"
                  placeholder="experience"
                  value={medecinForm.experience}
                  onChange={(e) => setMedecinForm({ ...medecinForm, experience: e.target.value })}
                />
                <button type="submit">Add</button>
              </form>
            </section>

            <section className="panel">
              <h2>Add Ambulance</h2>
              <form className="inline-form" onSubmit={createAmbulance}>
                <input
                  placeholder="matricule"
                  value={ambulanceForm.matricule}
                  onChange={(e) => setAmbulanceForm({ ...ambulanceForm, matricule: e.target.value })}
                  required
                />
                <select
                  value={ambulanceForm.type}
                  onChange={(e) => setAmbulanceForm({ ...ambulanceForm, type: e.target.value })}
                >
                  <option value="standard">standard</option>
                  <option value="medicalisee">medicalisee</option>
                  <option value="urgence">urgence</option>
                </select>
                <button type="submit">Add</button>
              </form>
            </section>

            <section className="panel">
              <h2>Add Patient</h2>
              <form className="inline-form" onSubmit={createPatient}>
                <input
                  type="number"
                  placeholder="user_id"
                  value={patientForm.user_id}
                  onChange={(e) => setPatientForm({ ...patientForm, user_id: e.target.value })}
                  required
                />
                <input
                  placeholder="telephone"
                  value={patientForm.telephone}
                  onChange={(e) => setPatientForm({ ...patientForm, telephone: e.target.value })}
                />
                <input
                  placeholder="adresse"
                  value={patientForm.adresse}
                  onChange={(e) => setPatientForm({ ...patientForm, adresse: e.target.value })}
                />
                <button type="submit">Add</button>
              </form>
            </section>

            <section className="panel">
              <h2>Add Rendez-vous</h2>
              <form className="inline-form" onSubmit={createRdv}>
                <input
                  type="number"
                  placeholder="patient_id"
                  value={rdvForm.patient_id}
                  onChange={(e) => setRdvForm({ ...rdvForm, patient_id: e.target.value })}
                  required
                />
                <input
                  type="number"
                  placeholder="medecin_id"
                  value={rdvForm.medecin_id}
                  onChange={(e) => setRdvForm({ ...rdvForm, medecin_id: e.target.value })}
                  required
                />
                <input
                  type="date"
                  value={rdvForm.date}
                  onChange={(e) => setRdvForm({ ...rdvForm, date: e.target.value })}
                  required
                />
                <input
                  type="time"
                  value={rdvForm.heure}
                  onChange={(e) => setRdvForm({ ...rdvForm, heure: e.target.value })}
                  required
                />
                <button type="submit">Add</button>
              </form>
            </section>

            <section className="panel">
              <h2>Patients</h2>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Username</th>
                    <th>Telephone</th>
                    <th>Adresse</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {patients.map((patient) => (
                    <tr key={patient.id}>
                      <td>{patient.id}</td>
                      <td>{patient.username}</td>
                      <td>{patient.telephone || "-"}</td>
                      <td>{patient.adresse || "-"}</td>
                      <td>
                        <button type="button" className="danger" onClick={() => deletePatient(patient.id)}>
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section className="panel">
              <h2>Securite</h2>
              <div className="stats compact-stats">
                <Stat label="Echecs login" value={security.summary?.failed_logins || 0} />
                <Stat label="Acces interdits" value={security.summary?.forbidden_access || 0} />
                <Stat label="Comptes bloques" value={security.summary?.locked_accounts || 0} />
                <Stat label="Utilisateurs actifs" value={security.summary?.active_users || 0} />
              </div>

              {security.locked_users?.length > 0 && (
                <>
                  <h3>Comptes bloques</h3>
                  <table>
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Role</th>
                        <th>Tentatives</th>
                        <th>Dernier echec</th>
                      </tr>
                    </thead>
                    <tbody>
                      {security.locked_users.map((user) => (
                        <tr key={user.id}>
                          <td>{user.id}</td>
                          <td>{user.username}</td>
                          <td>{user.role}</td>
                          <td>{user.login_attempts}</td>
                          <td>{formatDate(user.last_failed_login)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}

              <h3>Audit logs</h3>
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Resource</th>
                    <th>Resource ID</th>
                    <th>IP</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {security.logs?.map((log) => (
                    <tr key={log.id}>
                      <td>{formatDate(log.timestamp)}</td>
                      <td>{log.user}</td>
                      <td><span className={`badge ${log.action}`}>{log.action}</span></td>
                      <td>{log.resource || "-"}</td>
                      <td>{log.resource_id || log.object_id || "-"}</td>
                      <td>{log.ip_address || "-"}</td>
                      <td>{log.details || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section className="panel">
              <h2>Medecins</h2>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Username</th>
                    <th>Specialite</th>
                    <th>Telephone</th>
                  </tr>
                </thead>
                <tbody>
                  {medecins.map((medecin) => (
                    <tr key={medecin.id}>
                      <td>{medecin.id}</td>
                      <td>{medecin.username}</td>
                      <td>{medecin.specialite || "-"}</td>
                      <td>{medecin.telephone || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section className="panel">
              <h2>Rendez-vous</h2>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Patient</th>
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
                      <td>{rdv.patient}</td>
                      <td>{rdv.medecin}</td>
                      <td>{rdv.date}</td>
                      <td>{rdv.heure}</td>
                      <td><span className={`badge badge-${rdv.statut}`}>{rdv.statut}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section className="panel">
              <h2>Ambulances</h2>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Matricule</th>
                    <th>Type</th>
                    <th>Disponible</th>
                    <th>Chauffeur</th>
                  </tr>
                </thead>
                <tbody>
                  {ambulances.map((ambulance) => (
                    <tr key={ambulance.id}>
                      <td>{ambulance.id}</td>
                      <td>{ambulance.matricule}</td>
                      <td>{ambulance.type}</td>
                      <td>{ambulance.disponible ? "Oui" : "Non"}</td>
                      <td>{ambulance.chauffeur || "-"}</td>
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

function formatDate(value) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}

export default AdminDashboard;
