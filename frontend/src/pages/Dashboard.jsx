import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import { apiFetch, getCurrentUser } from "../api/client";

function Dashboard() {
  const user = getCurrentUser();

  return (
    <>
      <Navbar />
      <main className="page shell-page">
        <h1>Dashboard {user?.role}</h1>
        <section className="panel profile-panel">
          <h2>{user?.username}</h2>
          <p>Role: <strong>{user?.role}</strong></p>
        </section>

        {user?.role === "secretaire" && <SecretairePanel />}
        {user?.role === "infirmier" && <InfirmierPanel />}
        {user?.role === "comptable" && <ComptablePanel />}
        {user?.role === "securite" && <SecuritePanel />}
        {user?.role === "chauffeur" && <ChauffeurPanel />}
      </main>
    </>
  );
}

function SecretairePanel() {
  const [patients, setPatients] = useState([]);
  const [rdvs, setRdvs] = useState([]);
  const [patientForm, setPatientForm] = useState({ user_id: "", telephone: "", adresse: "" });
  const [rdvForm, setRdvForm] = useState({ patient_id: "", medecin_id: "", date: "", heure: "" });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    const [patientsData, rdvsData] = await Promise.all([apiFetch("/patients/"), apiFetch("/rendezvous/")]);
    setPatients(Array.isArray(patientsData) ? patientsData : []);
    setRdvs(Array.isArray(rdvsData) ? rdvsData : []);
  };

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  const createPatient = async (event) => {
    event.preventDefault();
    try {
      await apiFetch("/patients/", { method: "POST", body: patientForm });
      setPatientForm({ user_id: "", telephone: "", adresse: "" });
      setMessage("Patient ajoute");
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const createRdv = async (event) => {
    event.preventDefault();
    try {
      await apiFetch("/rendezvous/", { method: "POST", body: rdvForm });
      setRdvForm({ patient_id: "", medecin_id: "", date: "", heure: "" });
      setMessage("Rendez-vous ajoute");
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <Status error={error} message={message} />
      <section className="panel">
        <h2>Create Patient</h2>
        <form className="inline-form" onSubmit={createPatient}>
          <input type="number" placeholder="user_id" value={patientForm.user_id} onChange={(e) => setPatientForm({ ...patientForm, user_id: e.target.value })} required />
          <input placeholder="telephone" value={patientForm.telephone} onChange={(e) => setPatientForm({ ...patientForm, telephone: e.target.value })} />
          <input placeholder="adresse" value={patientForm.adresse} onChange={(e) => setPatientForm({ ...patientForm, adresse: e.target.value })} />
          <button type="submit">Add</button>
        </form>
      </section>
      <section className="panel">
        <h2>Create Rendez-vous</h2>
        <form className="inline-form" onSubmit={createRdv}>
          <input type="number" placeholder="patient_id" value={rdvForm.patient_id} onChange={(e) => setRdvForm({ ...rdvForm, patient_id: e.target.value })} required />
          <input type="number" placeholder="medecin_id" value={rdvForm.medecin_id} onChange={(e) => setRdvForm({ ...rdvForm, medecin_id: e.target.value })} required />
          <input type="date" value={rdvForm.date} onChange={(e) => setRdvForm({ ...rdvForm, date: e.target.value })} required />
          <input type="time" value={rdvForm.heure} onChange={(e) => setRdvForm({ ...rdvForm, heure: e.target.value })} required />
          <button type="submit">Add</button>
        </form>
      </section>
      <SimpleTable title="Patients" rows={patients} columns={["id", "username", "telephone"]} />
      <SimpleTable title="Rendez-vous" rows={rdvs} columns={["id", "patient", "medecin", "date", "heure", "statut"]} />
    </>
  );
}

function InfirmierPanel() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch("/hospitalisation/")
      .then((data) => setRows(Array.isArray(data) ? data : []))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <>
      <Status error={error} />
      <SimpleTable title="Patients hospitalises" rows={rows} columns={["id", "patient", "chambre", "date_entree", "date_sortie", "statut", "motif"]} />
    </>
  );
}

function ComptablePanel() {
  const [factures, setFactures] = useState([]);
  const [form, setForm] = useState({ patient_id: "", montant: "" });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    const data = await apiFetch("/facturation/");
    setFactures(Array.isArray(data) ? data : []);
  };

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  const createFacture = async (event) => {
    event.preventDefault();
    try {
      await apiFetch("/facturation/", { method: "POST", body: form });
      setForm({ patient_id: "", montant: "" });
      setMessage("Facture ajoutee");
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const pay = async (id) => {
    try {
      await apiFetch(`/facturation/${id}/payer/`, { method: "POST", body: { mode: "cash" } });
      setMessage("Paiement enregistre");
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <Status error={error} message={message} />
      <section className="panel">
        <h2>Create Facture</h2>
        <form className="inline-form" onSubmit={createFacture}>
          <input type="number" placeholder="patient_id" value={form.patient_id} onChange={(e) => setForm({ ...form, patient_id: e.target.value })} required />
          <input type="number" step="0.01" placeholder="montant" value={form.montant} onChange={(e) => setForm({ ...form, montant: e.target.value })} required />
          <button type="submit">Add</button>
        </form>
      </section>
      <section className="panel">
        <h2>Factures</h2>
        <table>
          <thead>
            <tr><th>ID</th><th>Patient</th><th>Montant</th><th>Date</th><th>Statut</th><th>Action</th></tr>
          </thead>
          <tbody>
            {factures.map((f) => (
              <tr key={f.id}>
                <td>{f.id}</td><td>{f.patient}</td><td>{f.montant}</td><td>{f.date}</td><td>{f.statut}</td>
                <td><button type="button" onClick={() => pay(f.id)}>Update</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

function SecuritePanel() {
  const [visiteurs, setVisiteurs] = useState([]);
  const [journal, setJournal] = useState([]);
  const [form, setForm] = useState({ nom: "", prenom: "", cin: "", telephone: "" });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    const [visiteursData, journalData] = await Promise.all([apiFetch("/visiteurs/"), apiFetch("/visiteurs/journal/")]);
    setVisiteurs(Array.isArray(visiteursData) ? visiteursData : []);
    setJournal(Array.isArray(journalData) ? journalData : []);
  };

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  const createVisiteur = async (event) => {
    event.preventDefault();
    try {
      await apiFetch("/visiteurs/", { method: "POST", body: form });
      setForm({ nom: "", prenom: "", cin: "", telephone: "" });
      setMessage("Visiteur ajoute");
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <Status error={error} message={message} />
      <section className="panel">
        <h2>Enregistrer visiteur</h2>
        <form className="inline-form" onSubmit={createVisiteur}>
          <input placeholder="nom" value={form.nom} onChange={(e) => setForm({ ...form, nom: e.target.value })} required />
          <input placeholder="prenom" value={form.prenom} onChange={(e) => setForm({ ...form, prenom: e.target.value })} required />
          <input placeholder="cin" value={form.cin} onChange={(e) => setForm({ ...form, cin: e.target.value })} />
          <input placeholder="telephone" value={form.telephone} onChange={(e) => setForm({ ...form, telephone: e.target.value })} />
          <button type="submit">Add</button>
        </form>
      </section>
      <SimpleTable title="Visiteurs" rows={visiteurs} columns={["id", "nom", "prenom", "cin", "telephone"]} />
      <SimpleTable title="Journal visites" rows={journal} columns={["id", "visiteur", "motif", "date_entree", "date_sortie", "statut"]} />
    </>
  );
}

function ChauffeurPanel() {
  const [ambulances, setAmbulances] = useState([]);
  const [missions, setMissions] = useState([]);
  const [form, setForm] = useState({ ambulance_id: "", patient_nom: "", lieu_depart: "", lieu_arrivee: "" });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    const [ambulancesData, missionsData] = await Promise.all([apiFetch("/ambulance/"), apiFetch("/ambulance/missions/")]);
    setAmbulances(Array.isArray(ambulancesData) ? ambulancesData : []);
    setMissions(Array.isArray(missionsData) ? missionsData : []);
  };

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  const createMission = async (event) => {
    event.preventDefault();
    try {
      await apiFetch("/ambulance/mission/create/", { method: "POST", body: form });
      setForm({ ambulance_id: "", patient_nom: "", lieu_depart: "", lieu_arrivee: "" });
      setMessage("Mission creee");
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const finishMission = async (id) => {
    try {
      await apiFetch(`/ambulance/mission/${id}/terminer/`, { method: "POST", body: {} });
      setMessage("Mission terminee");
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <Status error={error} message={message} />
      <SimpleTable title="Mes ambulances" rows={ambulances} columns={["id", "matricule", "type", "disponible"]} />
      <section className="panel">
        <h2>Create Mission Ambulance</h2>
        <form className="inline-form" onSubmit={createMission}>
          <input type="number" placeholder="ambulance_id" value={form.ambulance_id} onChange={(e) => setForm({ ...form, ambulance_id: e.target.value })} required />
          <input placeholder="patient_nom" value={form.patient_nom} onChange={(e) => setForm({ ...form, patient_nom: e.target.value })} required />
          <input placeholder="lieu_depart" value={form.lieu_depart} onChange={(e) => setForm({ ...form, lieu_depart: e.target.value })} required />
          <input placeholder="lieu_arrivee" value={form.lieu_arrivee} onChange={(e) => setForm({ ...form, lieu_arrivee: e.target.value })} required />
          <button type="submit">Add</button>
        </form>
      </section>
      <section className="panel">
        <h2>Missions</h2>
        <table>
          <thead>
            <tr><th>ID</th><th>Ambulance</th><th>Patient</th><th>Depart</th><th>Arrivee</th><th>Statut</th><th>Action</th></tr>
          </thead>
          <tbody>
            {missions.map((m) => (
              <tr key={m.id}>
                <td>{m.id}</td><td>{m.ambulance}</td><td>{m.patient_nom}</td><td>{m.lieu_depart}</td><td>{m.lieu_arrivee}</td><td>{m.statut}</td>
                <td><button type="button" onClick={() => finishMission(m.id)}>Update</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

function Status({ error, message }) {
  return (
    <>
      {error && <p className="error-message">{error}</p>}
      {message && <p className="success-message">{message}</p>}
    </>
  );
}

function SimpleTable({ title, rows, columns }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      <table>
        <thead>
          <tr>
            {columns.map((column) => <th key={column}>{column}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              {columns.map((column) => <td key={column}>{String(row[column] ?? "-")}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export default Dashboard;
