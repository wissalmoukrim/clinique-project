import { Navigate } from "react-router-dom";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch, getCurrentUser } from "../api/client";

function Dashboard() {
  const user = getCurrentUser();
  const path = ROLE_HOME[user?.role] || "/";

  return <Navigate to={path} replace />;
}

export const ROLE_LABELS = {
  secretaire: "Secretaire",
  infirmier: "Infirmier",
  comptable: "Comptable",
  securite: "Securite",
  chauffeur: "Chauffeur ambulance",
};

const ROLE_HOME = {
  secretaire: "/secretaire",
  infirmier: "/infirmier",
  comptable: "/comptable",
  securite: "/securite",
  chauffeur: "/chauffeur",
};

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

const MEDICAL_SPECIALTIES = [
  "Cardiologie",
  "Gynecologie",
  "Pediatrie",
  "Chirurgie generale",
  "Radiologie",
  "Medecine generale",
];

export function SecretairePanel() {
  const [patients, setPatients] = useState([]);
  const [rdvs, setRdvs] = useState([]);
  const [medecins, setMedecins] = useState([]);
  const [patientForm, setPatientForm] = useState({ full_name: "", email: "", telephone: "", adresse: "" });
  const [rdvForm, setRdvForm] = useState({ patient_id: "", specialite: "", medecin_id: "", date: "", heure: "" });
  const [patientErrors, setPatientErrors] = useState({});
  const [rdvErrors, setRdvErrors] = useState({});
  const [credentials, setCredentials] = useState(null);
  const [toast, setToast] = useState(null);
  const [confirmAction, setConfirmAction] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const toastTimerRef = useRef(null);

  const showToast = useCallback((type, text) => {
    setToast({ type, text });
    window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToast(null), 3600);
  }, []);

  const load = useCallback(async () => {
    const [patientsData, rdvsData, medecinsData] = await Promise.all([
      apiFetch("/patients/"),
      apiFetch("/rendezvous/"),
      apiFetch("/medecins/"),
    ]);
    setPatients(Array.isArray(patientsData) ? patientsData : []);
    setRdvs(Array.isArray(rdvsData) ? rdvsData : []);
    setMedecins(Array.isArray(medecinsData) ? medecinsData : []);
  }, []);

  useEffect(() => {
    load().catch((err) => showToast("error", err.message || "Erreur de chargement"));
  }, [load, showToast]);

  const filteredDoctors = useMemo(() => (
    medecins.filter((medecin) => !rdvForm.specialite || normalizeText(medecin.specialite) === normalizeText(rdvForm.specialite))
  ), [medecins, rdvForm.specialite]);

  const today = new Date().toISOString().slice(0, 10);
  const pendingCount = rdvs.filter((rdv) => rdv.statut === "en_attente").length;
  const confirmedCount = rdvs.filter((rdv) => rdv.statut === "confirme").length;
  const todayCount = rdvs.filter((rdv) => rdv.date === today).length;

  const updatePatientForm = (patch) => {
    setPatientForm((current) => ({ ...current, ...patch }));
    setPatientErrors({});
    setCredentials(null);
  };

  const updateRdvForm = (patch) => {
    setRdvForm((current) => ({ ...current, ...patch }));
    setRdvErrors({});
  };

  const createPatient = async (event) => {
    event.preventDefault();
    const errors = {};
    if (!patientForm.full_name.trim()) errors.full_name = "Nom complet obligatoire";
    if (!patientForm.email.trim()) errors.email = "Email obligatoire";
    if (patientForm.email && !patientForm.email.includes("@")) errors.email = "Email invalide";
    if (Object.keys(errors).length) {
      setPatientErrors(errors);
      showToast("error", "Veuillez verifier les informations du patient.");
      return;
    }

    setSubmitting(true);
    try {
      const data = await apiFetch("/patients/create-account/", { method: "POST", body: patientForm });
      setPatientForm({ full_name: "", email: "", telephone: "", adresse: "" });
      setCredentials({ username: data.username || data.email, password: data.temporary_password });
      showToast("success", "Patient cree avec identifiants temporaires.");
      await load();
    } catch (err) {
      showToast("error", err.message || "Creation patient impossible");
    } finally {
      setSubmitting(false);
    }
  };

  const createRdv = async (event) => {
    event.preventDefault();
    const errors = {};
    if (!rdvForm.patient_id) errors.patient_id = "Selectionnez un patient";
    if (!rdvForm.specialite) errors.specialite = "Selectionnez une specialite";
    if (!rdvForm.medecin_id) errors.medecin_id = "Selectionnez un medecin";
    if (!rdvForm.date) errors.date = "Selectionnez une date";
    if (!rdvForm.heure) errors.heure = "Selectionnez une heure";
    if (Object.keys(errors).length) {
      setRdvErrors(errors);
      showToast("error", "Veuillez completer la demande de rendez-vous.");
      return;
    }

    setSubmitting(true);
    try {
      await apiFetch("/rendezvous/", {
        method: "POST",
        body: {
          patient_id: rdvForm.patient_id,
          medecin_id: rdvForm.medecin_id,
          date: rdvForm.date,
          heure: rdvForm.heure,
        },
      });
      setRdvForm({ patient_id: "", specialite: "", medecin_id: "", date: "", heure: "" });
      showToast("success", "Rendez-vous ajoute en attente.");
      await load();
    } catch (err) {
      showToast("error", err.message || "Creation rendez-vous impossible");
    } finally {
      setSubmitting(false);
    }
  };

  const updateRdvStatus = async (rdvId, statut) => {
    setSubmitting(true);
    try {
      await apiFetch(`/rendezvous/${rdvId}/update-status/`, {
        method: "PUT",
        body: { statut },
      });
      setConfirmAction(null);
      showToast("success", statut === "confirme" ? "Rendez-vous confirme." : "Rendez-vous annule.");
      await load();
    } catch (err) {
      showToast("error", err.message || "Mise a jour impossible");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      {toast && <Toast type={toast.type} text={toast.text} onClose={() => setToast(null)} />}
      <section className="secretary-hero">
        <div>
          <span>Reception clinique</span>
          <h2>Accueil et gestion des rendez-vous</h2>
          <p>Creation de patients, planification des consultations et suivi des demandes en attente.</p>
        </div>
      </section>

      <div className="stats">
        <Stat label="Patients" value={patients.length} />
        <Stat label="En attente" value={pendingCount} />
        <Stat label="Confirmes" value={confirmedCount} />
        <Stat label="Aujourd'hui" value={todayCount} />
      </div>

      <div className="secretary-grid">
        <section className="panel">
          <h2>Nouveau patient</h2>
          <form className="stack-form" onSubmit={createPatient}>
            <Field label="Nom complet" placeholder="Nom et prenom" value={patientForm.full_name} onChange={(value) => updatePatientForm({ full_name: value })} error={patientErrors.full_name} />
            <Field label="Email" type="email" placeholder="patient@email.com" value={patientForm.email} onChange={(value) => updatePatientForm({ email: value })} error={patientErrors.email} />
            <Field label="Telephone" placeholder="+212 600 000 000" value={patientForm.telephone} onChange={(value) => updatePatientForm({ telephone: value })} />
            <Field label="Adresse" placeholder="Adresse complete" value={patientForm.adresse} onChange={(value) => updatePatientForm({ adresse: value })} />
            <button type="submit" disabled={submitting}>{submitting ? "Creation..." : "Creer le patient"}</button>
          </form>
          {credentials && (
            <div className="credentials-box">
              <p><strong>Identifiant :</strong> {credentials.username}</p>
              <p><strong>Mot de passe temporaire :</strong> {credentials.password}</p>
            </div>
          )}
        </section>

        <section className="panel">
          <h2>Nouveau rendez-vous</h2>
          <form className="stack-form" onSubmit={createRdv}>
            <SearchSelect label="Patient" placeholder="Rechercher nom ou email" value={rdvForm.patient_id} options={patients.map((patient) => ({ value: patient.id, label: patientName(patient), meta: patient.email || patient.username }))} onChange={(value) => updateRdvForm({ patient_id: value })} error={rdvErrors.patient_id} />
            <SelectField label="Specialite" placeholder="Choisir une specialite" value={rdvForm.specialite} options={MEDICAL_SPECIALTIES} onChange={(value) => updateRdvForm({ specialite: value, medecin_id: "" })} error={rdvErrors.specialite} />
            <SearchSelect label="Medecin" placeholder={rdvForm.specialite ? "Rechercher un medecin" : "Choisir une specialite d'abord"} value={rdvForm.medecin_id} options={filteredDoctors.map((medecin) => ({ value: medecin.id, label: doctorName(medecin), meta: medecin.specialite }))} onChange={(value) => updateRdvForm({ medecin_id: value })} error={rdvErrors.medecin_id} />
            <div className="form-pair">
              <Field label="Date" type="date" value={rdvForm.date} onChange={(value) => updateRdvForm({ date: value })} error={rdvErrors.date} />
              <Field label="Heure" type="time" value={rdvForm.heure} onChange={(value) => updateRdvForm({ heure: value })} error={rdvErrors.heure} />
            </div>
            <p className="form-note">Statut initial: <strong>EN_ATTENTE</strong></p>
            <button type="submit" disabled={submitting}>{submitting ? "Envoi..." : "Planifier"}</button>
          </form>
        </section>
      </div>

      <SecretaryTable
        title="Patients"
        searchPlaceholder="Rechercher patient..."
        rows={patients}
        columns={[
          ["display_name", "Patient", patientName],
          ["email", "Email", (patient) => patient.email || patient.username],
          ["telephone", "Telephone", (patient) => patient.telephone || "-"],
          ["adresse", "Adresse", (patient) => patient.adresse || "-"],
        ]}
      />

      <SecretaryTable
        title="Rendez-vous"
        searchPlaceholder="Rechercher rendez-vous..."
        rows={rdvs}
        columns={[
          ["patient", "Patient", patientName],
          ["medecin", "Medecin", doctorName],
          ["specialite", "Specialite", (rdv) => rdv.specialite || "-"],
          ["date", "Date", (rdv) => formatDateFr(rdv.date)],
          ["heure", "Heure", (rdv) => formatTime(rdv.heure)],
          ["statut", "Statut", (rdv) => <span className={`badge badge-${rdv.statut}`}>{rdvStatusLabel(rdv.statut)}</span>],
          ["actions", "Actions", (rdv) => (
            <div className="row-actions">
              <button type="button" onClick={() => setConfirmAction({ rdv, statut: "confirme" })} disabled={rdv.statut === "confirme" || rdv.statut === "annule"}>
                Confirmer
              </button>
              <button type="button" className="danger" onClick={() => setConfirmAction({ rdv, statut: "annule" })} disabled={rdv.statut === "annule"}>
                Annuler
              </button>
            </div>
          )],
        ]}
      />

      {confirmAction && (
        <Modal title={confirmAction.statut === "confirme" ? "Confirmer le rendez-vous" : "Annuler le rendez-vous"} onClose={() => setConfirmAction(null)}>
          <p className="modal-copy">
            Rendez-vous de {patientName(confirmAction.rdv)} avec {doctorName(confirmAction.rdv)} le {formatDateFr(confirmAction.rdv.date)} a {formatTime(confirmAction.rdv.heure)}.
          </p>
          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={() => setConfirmAction(null)}>Retour</button>
            <button type="button" className={confirmAction.statut === "annule" ? "danger" : ""} disabled={submitting} onClick={() => updateRdvStatus(confirmAction.rdv.id, confirmAction.statut)}>
              {confirmAction.statut === "confirme" ? "Confirmer" : "Annuler"}
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}

function Field({ label, value, onChange, error, type = "text", placeholder = "" }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type={type} placeholder={placeholder} value={value} onChange={(event) => onChange(event.target.value)} aria-invalid={Boolean(error)} />
      {error && <small>{error}</small>}
    </label>
  );
}

function SelectField({ label, value, onChange, error, options, placeholder }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} aria-invalid={Boolean(error)}>
        <option value="">{placeholder}</option>
        {options.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
      {error && <small>{error}</small>}
    </label>
  );
}

function SearchSelect({ label, value, options, onChange, placeholder, error }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const selected = options.find((option) => String(option.value) === String(value));
  const filtered = options.filter((option) => `${option.label} ${option.meta || ""}`.toLowerCase().includes(query.toLowerCase())).slice(0, 8);

  useEffect(() => {
    setQuery(selected?.label || "");
  }, [selected?.label]);

  return (
    <label className="field searchable-field">
      <span>{label}</span>
      <input
        value={query}
        placeholder={placeholder}
        onFocus={() => setOpen(true)}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
          onChange("");
        }}
        aria-invalid={Boolean(error)}
      />
      {open && (
        <div className="select-menu">
          {filtered.length ? filtered.map((option) => (
            <button
              type="button"
              key={option.value}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => {
                onChange(option.value);
                setQuery(option.label);
                setOpen(false);
              }}
            >
              <span>{option.label}</span>
              {option.meta && <small>{option.meta}</small>}
            </button>
          )) : <span>Aucun resultat</span>}
        </div>
      )}
      {error && <small>{error}</small>}
    </label>
  );
}

function SecretaryTable({ title, rows, columns, searchPlaceholder }) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 7;
  const filtered = rows.filter((row) => JSON.stringify(row).toLowerCase().includes(search.toLowerCase()));
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageRows = filtered.slice((page - 1) * pageSize, page * pageSize);

  useEffect(() => {
    setPage(1);
  }, [search, rows.length]);

  return (
    <section className="panel secretary-table-panel">
      <div className="table-toolbar">
        <h2>{title}</h2>
        <input type="search" placeholder={searchPlaceholder} value={search} onChange={(event) => setSearch(event.target.value)} />
      </div>
      <div className="table-scroll secretary-table-scroll">
        <table className="secretary-table">
          <thead>
            <tr>{columns.map(([, label]) => <th key={label}>{label}</th>)}</tr>
          </thead>
          <tbody>
            {pageRows.map((row) => (
              <tr key={row.id}>
                {columns.map(([key, label, render]) => <td key={key} data-label={label}>{render ? render(row) : row[key] || "-"}</td>)}
              </tr>
            ))}
            {!pageRows.length && <tr><td className="empty-cell" colSpan={columns.length}>Aucune donnee</td></tr>}
          </tbody>
        </table>
      </div>
      <div className="pagination">
        <span>{filtered.length} resultat(s)</span>
        <div>
          <button type="button" className="secondary-button" disabled={page === 1} onClick={() => setPage(page - 1)}>Precedent</button>
          <strong>{page} / {totalPages}</strong>
          <button type="button" className="secondary-button" disabled={page === totalPages} onClick={() => setPage(page + 1)}>Suivant</button>
        </div>
      </div>
    </section>
  );
}

function Modal({ title, children, onClose }) {
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal-card">
        <div className="modal-header">
          <h2>{title}</h2>
          <button type="button" className="secondary-button" onClick={onClose}>Fermer</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Toast({ type, text, onClose }) {
  return <div className={`toast toast-${type}`}><span>{text}</span><button type="button" onClick={onClose}>x</button></div>;
}

function patientName(item) {
  return item.display_name || item.full_name || item.patient_display || humanizeName(item.patient || item.username || "-");
}

function doctorName(item) {
  const raw = item.medecin_display || item.display_name || item.medecin_full_name || item.full_name || item.medecin || item.username || "-";
  return raw === "-" || raw.startsWith("Dr.") ? raw : `Dr. ${humanizeName(raw)}`;
}

function humanizeName(value) {
  return String(value).split(/[._\s-]+/).filter(Boolean).map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}

function formatDateFr(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "long", year: "numeric" }).format(date);
}

function formatTime(value) {
  return value ? String(value).slice(0, 5) : "-";
}

function normalizeText(value) {
  return String(value || "").trim().toLowerCase();
}

export function InfirmierPanel() {
  const [rows, setRows] = useState([]);
  const [toast, setToast] = useState(null);
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState({ observations: "", temperature: "", tension: "", frequence_cardiaque: "" });
  const [submitting, setSubmitting] = useState(false);
  const toastTimerRef = useRef(null);

  const showToast = useCallback((type, text) => {
    setToast({ type, text });
    window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToast(null), 3600);
  }, []);

  const load = useCallback(async () => {
    const data = await apiFetch("/hospitalisation/");
    setRows(Array.isArray(data) ? data : []);
  }, []);

  useEffect(() => {
    load().catch((err) => showToast("error", err.message || "Erreur de chargement"));
  }, [load, showToast]);

  const activeRows = rows.filter((row) => row.statut === "en_cours");

  const openMonitoring = (row) => {
    setSelected(row);
    setForm({
      observations: row.observations || "",
      temperature: row.temperature || "",
      tension: row.tension || "",
      frequence_cardiaque: row.frequence_cardiaque || "",
    });
  };

  const saveMonitoring = async (event) => {
    event.preventDefault();
    if (!selected) return;
    setSubmitting(true);
    try {
      await apiFetch(`/hospitalisation/${selected.id}/monitoring/`, { method: "PUT", body: form });
      setSelected(null);
      showToast("success", "Surveillance patient mise a jour.");
      await load();
    } catch (err) {
      showToast("error", err.message || "Mise a jour impossible");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      {toast && <Toast type={toast.type} text={toast.text} onClose={() => setToast(null)} />}
      <section className="role-hero">
        <span>INFIRMIER</span>
        <h2>Surveillance hospitalisation</h2>
        <p>Suivi des patients hospitalises, observations de soins et constantes vitales.</p>
      </section>
      <div className="stats">
        <Stat label="Hospitalises" value={rows.length} />
        <Stat label="En cours" value={activeRows.length} />
        <Stat label="Sorties" value={rows.filter((row) => row.statut === "termine").length} />
        <Stat label="Chambres" value={new Set(rows.map((row) => row.chambre).filter(Boolean)).size} />
      </div>
      <RoleTable
        title="Patients hospitalises"
        rows={rows}
        searchPlaceholder="Rechercher patient, chambre, statut..."
        emptyText="Aucun patient hospitalise pour le moment."
        columns={[
          ["patient", "Patient", patientName],
          ["chambre", "Chambre", (row) => row.chambre || "-"],
          ["statut", "Statut", (row) => <span className={`badge badge-${row.statut}`}>{statusLabel(row.statut)}</span>],
          ["date_entree", "Admission", (row) => formatDateFr(row.date_entree)],
          ["date_sortie", "Sortie", (row) => row.date_sortie ? formatDateFr(row.date_sortie) : "-"],
          ["vitals", "Constantes", (row) => vitalsSummary(row)],
          ["actions", "Actions", (row) => <button type="button" onClick={() => openMonitoring(row)}>Surveillance</button>],
        ]}
      />
      {selected && (
        <Modal title={`Surveillance - ${patientName(selected)}`} onClose={() => setSelected(null)}>
          <form className="stack-form" onSubmit={saveMonitoring}>
            <div className="form-pair">
              <Field label="Temperature" placeholder="37.0 C" value={form.temperature} onChange={(value) => setForm({ ...form, temperature: value })} />
              <Field label="Tension" placeholder="120/80" value={form.tension} onChange={(value) => setForm({ ...form, tension: value })} />
            </div>
            <Field label="Frequence cardiaque" placeholder="75 bpm" value={form.frequence_cardiaque} onChange={(value) => setForm({ ...form, frequence_cardiaque: value })} />
            <label className="field">
              <span>Observations de soins</span>
              <textarea value={form.observations} placeholder="Notes de surveillance, soins effectues, evolution..." onChange={(event) => setForm({ ...form, observations: event.target.value })} />
            </label>
            <div className="modal-actions">
              <button type="button" className="secondary-button" onClick={() => setSelected(null)}>Annuler</button>
              <button type="submit" disabled={submitting}>{submitting ? "Enregistrement..." : "Enregistrer"}</button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}

export function ComptablePanel() {
  const [factures, setFactures] = useState([]);
  const [patients, setPatients] = useState([]);
  const [form, setForm] = useState({ patient_id: "", montant: "" });
  const [errors, setErrors] = useState({});
  const [toast, setToast] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmPay, setConfirmPay] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const toastTimerRef = useRef(null);

  const showToast = useCallback((type, text) => {
    setToast({ type, text });
    window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToast(null), 3600);
  }, []);

  const load = useCallback(async () => {
    const [factureData, patientData] = await Promise.all([apiFetch("/facturation/"), apiFetch("/patients/")]);
    setFactures(Array.isArray(factureData) ? factureData : []);
    setPatients(Array.isArray(patientData) ? patientData : []);
  }, []);

  useEffect(() => {
    load().catch((err) => showToast("error", err.message || "Erreur de chargement"));
  }, [load, showToast]);

  const createFacture = async (event) => {
    event.preventDefault();
    const nextErrors = {};
    if (!form.patient_id) nextErrors.patient_id = "Selectionnez un patient";
    if (!form.montant) nextErrors.montant = "Montant obligatoire";
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      showToast("error", "Veuillez completer la facture.");
      return;
    }
    setSubmitting(true);
    try {
      await apiFetch("/facturation/", { method: "POST", body: form });
      setForm({ patient_id: "", montant: "" });
      setModalOpen(false);
      showToast("success", "Facture creee.");
      await load();
    } catch (err) {
      showToast("error", err.message || "Creation facture impossible");
    } finally {
      setSubmitting(false);
    }
  };

  const pay = async (id) => {
    setSubmitting(true);
    try {
      await apiFetch(`/facturation/${id}/payer/`, { method: "POST", body: { mode: "cash" } });
      setConfirmPay(null);
      showToast("success", "Paiement enregistre.");
      await load();
    } catch (err) {
      showToast("error", err.message || "Paiement impossible");
    } finally {
      setSubmitting(false);
    }
  };

  const paid = factures.filter((facture) => isPaid(facture));
  const unpaid = factures.filter((facture) => !isPaid(facture));
  const revenue = paid.reduce((total, facture) => total + Number(facture.montant || 0), 0);

  return (
    <>
      {toast && <Toast type={toast.type} text={toast.text} onClose={() => setToast(null)} />}
      <section className="role-hero">
        <span>COMPTABLE</span>
        <h2>Facturation et paiements</h2>
        <p>Creation de factures, suivi des paiements et encaissements securises.</p>
      </section>
      <div className="stats">
        <Stat label="Factures" value={factures.length} />
        <Stat label="Payees" value={paid.length} />
        <Stat label="En attente" value={unpaid.length} />
        <Stat label="Revenus" value={formatMoney(revenue)} />
      </div>
      <section className="action-band">
        <div>
          <h2>Nouvelle facture</h2>
          <p>Selectionnez un patient et saisissez le montant a facturer.</p>
        </div>
        <button type="button" onClick={() => setModalOpen(true)}>Creer une facture</button>
      </section>
      <RoleTable
        title="Factures"
        rows={factures}
        searchPlaceholder="Rechercher facture..."
        emptyText="Aucune facture disponible."
        columns={[
          ["id", "Reference", (facture) => `FAC-${facture.id}`],
          ["patient", "Patient", patientName],
          ["montant", "Montant", (facture) => formatMoney(facture.montant)],
          ["date", "Date", (facture) => formatDateFr(facture.date)],
          ["statut", "Statut", (facture) => <span className={`badge badge-${isPaid(facture) ? "paye" : "en_attente"}`}>{isPaid(facture) ? "PAYE" : "EN_ATTENTE"}</span>],
          ["action", "Action", (facture) => <button type="button" onClick={() => setConfirmPay(facture)} disabled={isPaid(facture)}>Encaisser</button>],
        ]}
      />
      {modalOpen && (
        <Modal title="Creer une facture" onClose={() => setModalOpen(false)}>
          <form className="stack-form" onSubmit={createFacture}>
            <SearchSelect label="Patient" placeholder="Rechercher patient" value={form.patient_id} options={patients.map((patient) => ({ value: patient.id, label: patientName(patient), meta: patient.email || patient.username }))} onChange={(value) => setForm({ ...form, patient_id: value })} error={errors.patient_id} />
            <Field label="Montant" type="number" placeholder="300.00" value={form.montant} onChange={(value) => setForm({ ...form, montant: value })} error={errors.montant} />
            <div className="modal-actions">
              <button type="button" className="secondary-button" onClick={() => setModalOpen(false)}>Annuler</button>
              <button type="submit" disabled={submitting}>{submitting ? "Creation..." : "Creer"}</button>
            </div>
          </form>
        </Modal>
      )}
      {confirmPay && (
        <Modal title="Confirmer le paiement" onClose={() => setConfirmPay(null)}>
          <p className="modal-copy">Confirmer l'encaissement de {formatMoney(confirmPay.montant)} pour {patientName(confirmPay)}.</p>
          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={() => setConfirmPay(null)}>Retour</button>
            <button type="button" disabled={submitting} onClick={() => pay(confirmPay.id)}>Confirmer</button>
          </div>
        </Modal>
      )}
    </>
  );
}

export function SecuritePanel() {
  const [visiteurs, setVisiteurs] = useState([]);
  const [visites, setVisites] = useState([]);
  const [presentVisits, setPresentVisits] = useState([]);
  const [form, setForm] = useState({ nom: "", prenom: "", cin: "", telephone: "" });
  const [visitForm, setVisitForm] = useState({ visiteur_id: "", motif: "" });
  const [errors, setErrors] = useState({});
  const [visitErrors, setVisitErrors] = useState({});
  const [toast, setToast] = useState(null);
  const [confirmAction, setConfirmAction] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const toastTimerRef = useRef(null);

  const showToast = useCallback((type, text) => {
    setToast({ type, text });
    window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToast(null), 3600);
  }, []);

  const load = useCallback(async () => {
    const [visiteursData, visitesData, presentsData] = await Promise.all([
      apiFetch("/visiteurs/"),
      apiFetch("/visites/"),
      apiFetch("/visites/presents/"),
    ]);
    setVisiteurs(Array.isArray(visiteursData) ? visiteursData : []);
    setVisites(Array.isArray(visitesData) ? visitesData : []);
    setPresentVisits(Array.isArray(presentsData) ? presentsData : []);
  }, []);

  useEffect(() => {
    load().catch((err) => showToast("error", err.message || "Erreur de chargement"));
  }, [load, showToast]);

  const createVisiteur = async (event) => {
    event.preventDefault();
    const nextErrors = {};
    if (!form.nom.trim()) nextErrors.nom = "Nom obligatoire";
    if (!form.prenom.trim()) nextErrors.prenom = "Prenom obligatoire";
    if (form.cin && visiteurs.some((visiteur) => normalizeText(visiteur.cin) === normalizeText(form.cin))) {
      nextErrors.cin = "CIN deja enregistre";
    }
    if (form.telephone && !/^[0-9+\-.\s()]+$/.test(form.telephone)) {
      nextErrors.telephone = "Telephone invalide";
    }
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      showToast("error", "Veuillez verifier les informations visiteur.");
      return;
    }
    setSubmitting(true);
    try {
      await apiFetch("/visiteurs/", { method: "POST", body: form });
      setForm({ nom: "", prenom: "", cin: "", telephone: "" });
      setErrors({});
      showToast("success", "Visiteur enregistre.");
      await load();
    } catch (err) {
      showToast("error", err.message || "Creation visiteur impossible");
    } finally {
      setSubmitting(false);
    }
  };

  const activeVisitorIds = useMemo(() => new Set(presentVisits.map((entry) => entry.visiteur_id)), [presentVisits]);
  const today = new Date().toISOString().slice(0, 10);
  const todayVisits = visites.filter((entry) => String(entry.date_entree || "").slice(0, 10) === today);
  const totalExits = visites.filter((entry) => normalizeVisitStatus(entry.statut) === "sorti").length;

  const requestEntry = (event) => {
    event.preventDefault();
    const nextErrors = {};
    if (!visitForm.visiteur_id) nextErrors.visiteur_id = "Selectionnez un visiteur";
    if (!visitForm.motif.trim()) nextErrors.motif = "Motif obligatoire";
    if (Object.keys(nextErrors).length) {
      setVisitErrors(nextErrors);
      showToast("error", "Veuillez completer l'entree visiteur.");
      return;
    }
    const visitor = visiteurs.find((item) => String(item.id) === String(visitForm.visiteur_id));
    setConfirmAction({ type: "entry", visitor });
  };

  const createVisite = async () => {
    setSubmitting(true);
    try {
      await apiFetch("/visites/entree/", {
        method: "POST",
        body: visitForm,
      });
      setVisitForm({ visiteur_id: "", motif: "" });
      setVisitErrors({});
      setConfirmAction(null);
      showToast("success", "Entree visiteur enregistree.");
      await load();
    } catch (err) {
      showToast("error", err.message || "Entree impossible");
    } finally {
      setSubmitting(false);
    }
  };

  const exitVisiteur = async (journalId) => {
    setSubmitting(true);
    try {
      await apiFetch(`/visites/${journalId}/sortie/`, { method: "PUT" });
      setConfirmAction(null);
      showToast("success", "Sortie visiteur enregistree.");
      await load();
    } catch (err) {
      showToast("error", err.message || "Sortie impossible");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      {toast && <Toast type={toast.type} text={toast.text} onClose={() => setToast(null)} />}
      <section className="role-hero security-hero">
        <span>SECURITE</span>
        <h2>Controle d'acces visiteurs</h2>
        <p>Enregistrement des visiteurs, validation des entrees et suivi des sorties a l'accueil de la clinique.</p>
      </section>
      <div className="stats">
        <Stat label="Visiteurs presents" value={presentVisits.length} />
        <Stat label="Visiteurs aujourd'hui" value={todayVisits.length} />
        <Stat label="Entrees" value={visites.length} />
        <Stat label="Sorties" value={totalExits} />
      </div>

      <div className="secretary-grid role-grid">
        <section className="panel">
          <h2>Enregistrer un visiteur</h2>
          <form className="stack-form" onSubmit={createVisiteur}>
            <Field label="Nom" placeholder="Nom du visiteur" value={form.nom} onChange={(value) => setForm({ ...form, nom: value })} error={errors.nom} />
            <Field label="Prenom" placeholder="Prenom du visiteur" value={form.prenom} onChange={(value) => setForm({ ...form, prenom: value })} error={errors.prenom} />
            <Field label="CIN" placeholder="Numero CIN" value={form.cin} onChange={(value) => setForm({ ...form, cin: value })} error={errors.cin} />
            <Field label="Telephone" placeholder="+212 600 000 000" value={form.telephone} onChange={(value) => setForm({ ...form, telephone: value })} error={errors.telephone} />
            <button type="submit" disabled={submitting}>{submitting ? "Enregistrement..." : "Enregistrer"}</button>
          </form>
        </section>

        <section className="panel">
          <h2>Controler une entree</h2>
          <form className="stack-form" onSubmit={requestEntry}>
            <SearchSelect
              label="Visiteur"
              placeholder="Rechercher visiteur"
              value={visitForm.visiteur_id}
              options={visiteurs.map((visiteur) => ({ value: visiteur.id, label: visitorName(visiteur), meta: activeVisitorIds.has(visiteur.id) ? "PRESENT" : visiteur.cin || visiteur.telephone || "ABSENT" }))}
              onChange={(value) => setVisitForm({ ...visitForm, visiteur_id: value })}
              error={visitErrors.visiteur_id}
            />
            <Field label="Motif de visite" placeholder="Consultation, accompagnant, livraison..." value={visitForm.motif} onChange={(value) => setVisitForm({ ...visitForm, motif: value })} error={visitErrors.motif} />
            <button type="submit" disabled={submitting}>Valider l'entree</button>
          </form>
        </section>
      </div>

      <RoleTable
        title="Registre visiteurs"
        rows={visiteurs.map((visiteur) => ({ ...visiteur, presence: activeVisitorIds.has(visiteur.id) ? "present" : "absent" }))}
        searchPlaceholder="Rechercher visiteur..."
        emptyText="Aucun visiteur enregistre."
        columns={[
          ["nom", "Visiteur", visitorName],
          ["cin", "CIN", (visiteur) => visiteur.cin || "-"],
          ["telephone", "Telephone", (visiteur) => visiteur.telephone || "-"],
          ["presence", "Presence", (visiteur) => <span className={`badge badge-${visiteur.presence}`}>{visiteur.presence === "present" ? "PRESENT" : "ABSENT"}</span>],
        ]}
      />

      <RoleTable
        title="Visiteurs presents"
        rows={presentVisits}
        searchPlaceholder="Rechercher present..."
        emptyText="Aucun visiteur actuellement present dans la clinique."
        columns={[
          ["visiteur", "Visiteur", (entry) => entry.visiteur],
          ["motif", "Motif", (entry) => entry.motif],
          ["date_entree", "Entree", (entry) => formatDateTime(entry.date_entree)],
          ["statut", "Statut", () => <span className="badge badge-present">PRESENT</span>],
          ["action", "Action", (entry) => <button type="button" className="danger" onClick={() => setConfirmAction({ type: "exit", entry })}>Valider sortie</button>],
        ]}
      />

      <RoleTable
        title="Historique des visites"
        rows={[...visites].sort((a, b) => String(b.date_entree).localeCompare(String(a.date_entree)))}
        searchPlaceholder="Rechercher historique..."
        emptyText="Aucun historique de visite."
        columns={[
          ["visiteur", "Visiteur", (entry) => entry.visiteur],
          ["motif", "Motif", (entry) => entry.motif],
          ["date_entree", "Entree", (entry) => formatDateTime(entry.date_entree)],
          ["date_sortie", "Sortie", (entry) => entry.date_sortie ? formatDateTime(entry.date_sortie) : "-"],
          ["statut", "Statut", (entry) => <span className={`badge badge-${normalizeVisitStatus(entry.statut)}`}>{visitStatusLabel(entry.statut)}</span>],
        ]}
      />

      {confirmAction?.type === "entry" && (
        <Modal title="Confirmer l'entree visiteur" onClose={() => setConfirmAction(null)}>
          <p className="modal-copy">Valider l'entree de {visitorName(confirmAction.visitor)} pour le motif: {visitForm.motif}.</p>
          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={() => setConfirmAction(null)}>Retour</button>
            <button type="button" disabled={submitting} onClick={createVisite}>Confirmer entree</button>
          </div>
        </Modal>
      )}

      {confirmAction?.type === "exit" && (
        <Modal title="Confirmer la sortie visiteur" onClose={() => setConfirmAction(null)}>
          <p className="modal-copy">Valider la sortie de {confirmAction.entry.visiteur}. L'heure de sortie sera enregistree automatiquement.</p>
          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={() => setConfirmAction(null)}>Retour</button>
            <button type="button" className="danger" disabled={submitting} onClick={() => exitVisiteur(confirmAction.entry.id)}>Confirmer sortie</button>
          </div>
        </Modal>
      )}
    </>
  );
}

export function ChauffeurPanel() {
  const [ambulances, setAmbulances] = useState([]);
  const [missions, setMissions] = useState([]);
  const [form, setForm] = useState({ ambulance_id: "", patient_nom: "", lieu_depart: "", lieu_arrivee: "" });
  const [errors, setErrors] = useState({});
  const [toast, setToast] = useState(null);
  const [confirmAction, setConfirmAction] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const toastTimerRef = useRef(null);

  const showToast = useCallback((type, text) => {
    setToast({ type, text });
    window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToast(null), 3600);
  }, []);

  const load = useCallback(async () => {
    const [ambulancesData, missionsData] = await Promise.all([apiFetch("/ambulance/"), apiFetch("/ambulance/missions/")]);
    setAmbulances(Array.isArray(ambulancesData) ? ambulancesData : []);
    setMissions(Array.isArray(missionsData) ? missionsData : []);
  }, []);

  useEffect(() => {
    load().catch((err) => showToast("error", err.message || "Erreur de chargement"));
  }, [load, showToast]);

  const createMission = async (event) => {
    event.preventDefault();
    const nextErrors = {};
    if (!form.ambulance_id) nextErrors.ambulance_id = "Selectionnez une ambulance";
    if (!form.patient_nom.trim()) nextErrors.patient_nom = "Patient obligatoire";
    if (!form.lieu_depart.trim()) nextErrors.lieu_depart = "Depart obligatoire";
    if (!form.lieu_arrivee.trim()) nextErrors.lieu_arrivee = "Arrivee obligatoire";
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      showToast("error", "Veuillez completer la mission.");
      return;
    }
    setSubmitting(true);
    try {
      await apiFetch("/ambulance/mission/create/", { method: "POST", body: form });
      setForm({ ambulance_id: "", patient_nom: "", lieu_depart: "", lieu_arrivee: "" });
      showToast("success", "Mission creee.");
      await load();
    } catch (err) {
      showToast("error", err.message || "Creation mission impossible");
    } finally {
      setSubmitting(false);
    }
  };

  const updateMission = async () => {
    if (!confirmAction) return;
    setSubmitting(true);
    const endpoint = confirmAction.action === "start"
      ? `/ambulance/mission/${confirmAction.mission.id}/start/`
      : `/ambulance/mission/${confirmAction.mission.id}/terminer/`;
    try {
      await apiFetch(endpoint, { method: "POST", body: {} });
      showToast("success", confirmAction.action === "start" ? "Mission demarree." : "Mission terminee.");
      setConfirmAction(null);
      await load();
    } catch (err) {
      showToast("error", err.message || "Mise a jour mission impossible");
    } finally {
      setSubmitting(false);
    }
  };

  const activeMissions = missions.filter((mission) => normalizeMissionStatus(mission.statut) === "en_cours");
  const completedMissions = missions.filter((mission) => normalizeMissionStatus(mission.statut) === "terminee");
  const availableAmbulances = ambulances.filter((ambulance) => ambulance.disponible);

  return (
    <>
      {toast && <Toast type={toast.type} text={toast.text} onClose={() => setToast(null)} />}
      <section className="role-hero">
        <span>CHAUFFEUR AMBULANCE</span>
        <h2>Missions ambulance</h2>
        <p>Gestion des ambulances assignees, trajets patients et suivi des missions.</p>
      </section>
      <div className="stats">
        <Stat label="Missions" value={missions.length} />
        <Stat label="Actives" value={activeMissions.length} />
        <Stat label="Terminees" value={completedMissions.length} />
        <Stat label="Disponibles" value={availableAmbulances.length} />
      </div>
      <div className="secretary-grid role-grid">
        <section className="panel">
          <h2>Nouvelle mission</h2>
          <form className="stack-form" onSubmit={createMission}>
            <SearchSelect label="Ambulance" placeholder="Rechercher ambulance" value={form.ambulance_id} options={ambulances.map((ambulance) => ({ value: ambulance.id, label: `${ambulance.matricule} - ${ambulance.type}`, meta: ambulance.disponible ? "Disponible" : "Occupee" }))} onChange={(value) => setForm({ ...form, ambulance_id: value })} error={errors.ambulance_id} />
            <Field label="Patient" placeholder="Nom du patient" value={form.patient_nom} onChange={(value) => setForm({ ...form, patient_nom: value })} error={errors.patient_nom} />
            <Field label="Lieu de depart" placeholder="Adresse de depart" value={form.lieu_depart} onChange={(value) => setForm({ ...form, lieu_depart: value })} error={errors.lieu_depart} />
            <Field label="Lieu d'arrivee" placeholder="Clinique Medicale Elite" value={form.lieu_arrivee} onChange={(value) => setForm({ ...form, lieu_arrivee: value })} error={errors.lieu_arrivee} />
            <button type="submit" disabled={submitting}>{submitting ? "Creation..." : "Creer mission"}</button>
          </form>
        </section>
        <section className="panel ambulance-cards">
          <h2>Mes ambulances</h2>
          {ambulances.length === 0 ? <EmptyPanel text="Aucune ambulance assignee." /> : ambulances.map((ambulance) => (
            <article key={ambulance.id} className="ambulance-card">
              <div>
                <h3>{ambulance.matricule}</h3>
                <p>{ambulance.type} - {ambulance.chauffeur_display || ambulance.chauffeur || "Chauffeur non assigne"}</p>
              </div>
              <span className={`badge badge-${ambulance.disponible ? "paye" : "en_attente"}`}>{ambulance.disponible ? "DISPONIBLE" : "OCCUPEE"}</span>
            </article>
          ))}
        </section>
      </div>
      <RoleTable
        title="Missions"
        rows={missions}
        searchPlaceholder="Rechercher mission..."
        emptyText="Aucune mission ambulance."
        columns={[
          ["ambulance", "Ambulance", (mission) => mission.ambulance],
          ["patient_nom", "Patient", (mission) => mission.patient_nom],
          ["lieu_depart", "Depart", (mission) => mission.lieu_depart],
          ["lieu_arrivee", "Arrivee", (mission) => mission.lieu_arrivee],
          ["statut", "Statut", (mission) => <span className={`badge badge-${normalizeMissionStatus(mission.statut)}`}>{missionStatusLabel(mission.statut)}</span>],
          ["action", "Action", (mission) => (
            <div className="row-actions">
              <button type="button" onClick={() => setConfirmAction({ mission, action: "start" })} disabled={normalizeMissionStatus(mission.statut) !== "en_attente"}>Demarrer</button>
              <button type="button" className="danger" onClick={() => setConfirmAction({ mission, action: "finish" })} disabled={normalizeMissionStatus(mission.statut) === "terminee"}>Terminer</button>
            </div>
          )],
        ]}
      />
      {confirmAction && (
        <Modal title={confirmAction.action === "start" ? "Demarrer la mission" : "Terminer la mission"} onClose={() => setConfirmAction(null)}>
          <p className="modal-copy">{confirmAction.mission.patient_nom} - {confirmAction.mission.lieu_depart} vers {confirmAction.mission.lieu_arrivee}</p>
          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={() => setConfirmAction(null)}>Retour</button>
            <button type="button" disabled={submitting} onClick={updateMission}>{confirmAction.action === "start" ? "Demarrer" : "Terminer"}</button>
          </div>
        </Modal>
      )}
    </>
  );
}

function RoleTable({ title, rows, columns, searchPlaceholder, emptyText }) {
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("date");
  const [page, setPage] = useState(1);
  const pageSize = 7;
  const filtered = rows.filter((row) => JSON.stringify(row).toLowerCase().includes(search.toLowerCase()));
  const sorted = [...filtered].sort((a, b) => compareRoleRows(a, b, sortBy));
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageRows = sorted.slice((page - 1) * pageSize, page * pageSize);

  useEffect(() => {
    setPage(1);
  }, [search, rows.length]);

  return (
    <section className="panel role-table-panel">
      <div className="table-toolbar">
        <h2>{title}</h2>
        <div className="toolbar-controls">
          <input type="search" placeholder={searchPlaceholder} value={search} onChange={(event) => setSearch(event.target.value)} />
          <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
            <option value="date">Date</option>
            <option value="status">Statut</option>
            <option value="name">Nom</option>
          </select>
        </div>
      </div>
      {rows.length === 0 ? (
        <EmptyPanel text={emptyText} />
      ) : (
        <>
          <div className="table-scroll role-table-scroll">
            <table className="role-table">
              <thead>
                <tr>{columns.map(([, label]) => <th key={label}>{label}</th>)}</tr>
              </thead>
              <tbody>
                {pageRows.map((row) => (
                  <tr key={row.id}>
                    {columns.map(([key, label, render]) => <td key={key} data-label={label}>{render ? render(row) : row[key] || "-"}</td>)}
                  </tr>
                ))}
                {!pageRows.length && <tr><td className="empty-cell" colSpan={columns.length}>Aucun resultat</td></tr>}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <span>{filtered.length} resultat(s)</span>
            <div>
              <button type="button" className="secondary-button" disabled={page === 1} onClick={() => setPage(page - 1)}>Precedent</button>
              <strong>{page} / {totalPages}</strong>
              <button type="button" className="secondary-button" disabled={page === totalPages} onClick={() => setPage(page + 1)}>Suivant</button>
            </div>
          </div>
        </>
      )}
    </section>
  );
}

function compareRoleRows(a, b, sortBy) {
  if (sortBy === "status") {
    return String(a.statut || a.presence || "").localeCompare(String(b.statut || b.presence || ""));
  }
  if (sortBy === "name") {
    return String(a.visiteur || a.patient_display || a.nom || a.patient_nom || "").localeCompare(String(b.visiteur || b.patient_display || b.nom || b.patient_nom || ""));
  }
  return String(b.date_entree || b.date || "").localeCompare(String(a.date_entree || a.date || ""));
}

function EmptyPanel({ text }) {
  return (
    <div className="empty-state compact-empty">
      <span>+</span>
      <h3>Aucune donnee</h3>
      <p>{text}</p>
    </div>
  );
}

function statusLabel(value) {
  const labels = {
    en_cours: "EN_COURS",
    termine: "TERMINE",
    en_attente: "EN_ATTENTE",
    terminee: "TERMINEE",
    paye: "PAYE",
    impaye: "EN_ATTENTE",
    annule: "ANNULE",
  };
  return labels[normalizeMissionStatus(value)] || labels[value] || String(value || "-").replace(" ", "_").toUpperCase();
}

function vitalsSummary(row) {
  const values = [
    row.temperature ? `${row.temperature}` : null,
    row.tension ? `${row.tension}` : null,
    row.frequence_cardiaque ? `${row.frequence_cardiaque}` : null,
  ].filter(Boolean);
  return values.length ? values.join(" / ") : "-";
}

function isPaid(facture) {
  return ["paye", "payé", "payÃ©", "payÃƒÂ©", "payÃƒÆ’Ã‚Â©"].includes(facture.statut);
}

function formatMoney(value) {
  return new Intl.NumberFormat("fr-MA", { style: "currency", currency: "MAD" }).format(Number(value || 0));
}

function normalizeMissionStatus(value) {
  const raw = String(value || "").toLowerCase();
  if (raw === "en cours") return "en_cours";
  if (raw === "terminée" || raw === "termine" || raw === "terminee") return "terminee";
  return raw;
}

function missionStatusLabel(value) {
  const normalized = normalizeMissionStatus(value);
  if (normalized === "en_attente") return "EN_ATTENTE";
  if (normalized === "en_cours") return "EN_COURS";
  if (normalized === "terminee") return "TERMINEE";
  return statusLabel(value);
}

function visitorName(visiteur) {
  if (!visiteur) return "-";
  return [visiteur.nom, visiteur.prenom].filter(Boolean).join(" ") || visiteur.visiteur || "-";
}

function normalizeVisitStatus(value) {
  const raw = String(value || "").toLowerCase();
  if (raw === "en cours" || raw === "en_cours") return "present";
  if (raw === "sorti") return "sorti";
  return raw;
}

function visitStatusLabel(value) {
  const normalized = normalizeVisitStatus(value);
  if (normalized === "present") return "PRESENT";
  if (normalized === "sorti") return "SORTI";
  if (normalized === "absent") return "ABSENT";
  return String(value || "-").replace("_", " ").toUpperCase();
}

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export default Dashboard;
