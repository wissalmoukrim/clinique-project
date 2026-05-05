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
        <div className="stats">
          <Stat label="Espace" value="1" />
          <Stat label="Role" value={user?.role?.slice(0, 3).toUpperCase() || "-"} />
        </div>
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

function Stat({ label, value }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

const RDV_STATUS_LABELS = {
  en_attente: "EN ATTENTE",
  confirme: "CONFIRME",
  annule: "ANNULE",
  termine: "TERMINE",
};

function rdvStatusLabel(statut) {
  return RDV_STATUS_LABELS[statut] || String(statut || "-").replace("_", " ").toUpperCase();
}

const FACTURE_STATUS_LABELS = {
  impaye: "IMPAYE",
  paye: "PAYE",
};

function factureStatusLabel(statut) {
  return FACTURE_STATUS_LABELS[statut] || String(statut || "-").replace("_", " ").toUpperCase();
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

  const updateRdvStatus = async (rdvId, statut) => {
    setError("");
    setMessage("");

    try {
      await apiFetch(`/rendezvous/${rdvId}/update-status/`, {
        method: "PUT",
        body: { statut },
      });
      setMessage(statut === "confirme" ? "Rendez-vous confirme" : "Rendez-vous annule");
      await load();
    } catch (err) {
      setError(err.message || "Mise a jour impossible");
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
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rdvs.map((rdv) => (
              <tr key={rdv.id}>
                <td>{rdv.id}</td>
                <td>{rdv.patient}</td>
                <td>{rdv.medecin}</td>
                <td>{rdv.date}</td>
                <td>{rdv.heure}</td>
                <td><span className={`badge badge-${rdv.statut}`}>{rdvStatusLabel(rdv.statut)}</span></td>
                <td>
                  <div className="row-actions">
                    <button type="button" onClick={() => updateRdvStatus(rdv.id, "confirme")} disabled={rdv.statut === "confirme"}>
                      Confirmer
                    </button>
                    <button type="button" className="danger" onClick={() => updateRdvStatus(rdv.id, "annule")} disabled={rdv.statut === "annule"}>
                      Annuler
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
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
                <td>{f.id}</td><td>{f.patient}</td><td>{f.montant}</td><td>{f.date}</td><td><span className={`badge badge-${f.statut}`}>{factureStatusLabel(f.statut)}</span></td>
                <td><button type="button" onClick={() => pay(f.id)} disabled={f.statut === "paye"}>Encaisser</button></td>
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
  const [visites, setVisites] = useState([]);
  const [presentVisits, setPresentVisits] = useState([]);
  const [form, setForm] = useState({ nom: "", prenom: "", cin: "", telephone: "" });
  const [visitForm, setVisitForm] = useState({ visiteur_id: "", motif: "" });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    const [visiteursData, visitesData, presentsData] = await Promise.all([
      apiFetch("/visiteurs/"),
      apiFetch("/visites/"),
      apiFetch("/visites/presents/"),
    ]);
    setVisiteurs(Array.isArray(visiteursData) ? visiteursData : []);
    setVisites(Array.isArray(visitesData) ? visitesData : []);
    setPresentVisits(Array.isArray(presentsData) ? presentsData : []);
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

  const activeVisitorIds = new Set(presentVisits.map((entry) => entry.visiteur_id));

  const createVisite = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");

    try {
      await apiFetch("/visites/entree/", {
        method: "POST",
        body: visitForm,
      });
      setVisitForm({ visiteur_id: "", motif: "" });
      setMessage("Entree enregistree");
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const exitVisiteur = async (journalId) => {
    setError("");
    setMessage("");

    try {
      await apiFetch(`/visites/${journalId}/sortie/`, { method: "PUT" });
      setMessage("Sortie enregistree");
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <Status error={error} message={message} />
      <div className="stats">
        <Stat label="Visiteurs presents" value={presentVisits.length} />
      </div>
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
      <section className="panel">
        <h2>Visiteurs</h2>
        <table>
          <thead>
            <tr><th>ID</th><th>Nom</th><th>Prenom</th><th>CIN</th><th>Telephone</th><th>Presence</th></tr>
          </thead>
          <tbody>
            {visiteurs.map((visiteur) => (
              <tr key={visiteur.id}>
                <td>{visiteur.id}</td>
                <td>{visiteur.nom}</td>
                <td>{visiteur.prenom}</td>
                <td>{visiteur.cin || "-"}</td>
                <td>{visiteur.telephone || "-"}</td>
                <td>
                  {activeVisitorIds.has(visiteur.id) ? <span className="badge badge-en_cours">present</span> : <span className="badge badge-sorti">absent</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="panel">
        <h2>Action</h2>
        <form className="inline-form" onSubmit={createVisite}>
          <select
            value={visitForm.visiteur_id}
            onChange={(e) => setVisitForm({ ...visitForm, visiteur_id: e.target.value })}
            required
          >
            <option value="">Selectionner visiteur</option>
            {visiteurs.map((visiteur) => (
              <option key={visiteur.id} value={visiteur.id} disabled={activeVisitorIds.has(visiteur.id)}>
                {visiteur.nom} {visiteur.prenom}
              </option>
            ))}
          </select>
          <input
            placeholder="motif"
            value={visitForm.motif}
            onChange={(e) => setVisitForm({ ...visitForm, motif: e.target.value })}
            required
          />
          <button type="submit">Entree</button>
        </form>
      </section>
      <section className="panel">
        <h2>Visiteurs presents</h2>
        {presentVisits.length === 0 ? (
          <p>Aucun visiteur actuellement</p>
        ) : (
          <table>
            <thead>
              <tr><th>ID</th><th>Visiteur</th><th>Motif</th><th>Date entree</th><th>Statut</th><th>Action</th></tr>
            </thead>
            <tbody>
              {presentVisits.map((entry) => (
                <tr key={entry.id}>
                  <td>{entry.id}</td>
                  <td>{entry.visiteur}</td>
                  <td>{entry.motif}</td>
                  <td>{entry.date_entree}</td>
                  <td><span className="badge badge-en_cours">en_cours</span></td>
                  <td><button type="button" onClick={() => exitVisiteur(entry.id)}>Sortie</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
      <section className="panel">
        <h2>Historique</h2>
        <table>
          <thead>
            <tr><th>ID</th><th>Visiteur</th><th>Motif</th><th>Date entree</th><th>Date sortie</th><th>Statut</th></tr>
          </thead>
          <tbody>
            {visites.map((entry) => (
              <tr key={entry.id}>
                <td>{entry.id}</td>
                <td>{entry.visiteur}</td>
                <td>{entry.motif}</td>
                <td>{entry.date_entree}</td>
                <td>{entry.date_sortie || "-"}</td>
                <td><span className={`badge badge-${entry.statut}`}>{entry.statut}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
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
                <td>{m.id}</td><td>{m.ambulance}</td><td>{m.patient_nom}</td><td>{m.lieu_depart}</td><td>{m.lieu_arrivee}</td><td><span className="badge">{m.statut}</span></td>
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
