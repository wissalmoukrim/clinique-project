import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "../../api/client";
import Navbar from "../../components/Navbar";
import Chatbot from "../../components/Chatbot";

const SPECIALTIES = [
  "Cardiologie",
  "Gynecologie",
  "Pediatrie",
  "Chirurgie generale",
  "Radiologie",
  "Medecine generale",
];

const RDV_STATUS_LABELS = {
  en_attente: "EN_ATTENTE",
  confirme: "CONFIRME",
  annule: "ANNULE",
  termine: "TERMINE",
};

function PatientDashboard() {
  const [rendezvous, setRendezvous] = useState([]);
  const [factures, setFactures] = useState([]);
  const [consultations, setConsultations] = useState([]);
  const [medecins, setMedecins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [bookingOpen, setBookingOpen] = useState(false);
  const [cancelTarget, setCancelTarget] = useState(null);
  const [toast, setToast] = useState(null);
  const [form, setForm] = useState({ specialite: "", medecin_id: "", date: "", heure: "" });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const toastTimerRef = useRef(null);

  const showToast = useCallback((type, text) => {
    setToast({ type, text });
    window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToast(null), 3600);
  }, []);

  const loadDashboard = useCallback(async () => {
    try {
      const [rdvData, factureData, consultationData, medecinData] = await Promise.all([
        apiFetch("/rendezvous/"),
        apiFetch("/facturation/"),
        apiFetch("/consultations/"),
        apiFetch("/medecins/"),
      ]);

      setRendezvous(asArray(rdvData));
      setFactures(asArray(factureData));
      setConsultations(asArray(consultationData));
      setMedecins(asArray(medecinData));
    } catch (err) {
      showToast("error", err.message || "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const filteredDoctors = useMemo(() => {
    return medecins.filter((medecin) => !form.specialite || normalize(medecin.specialite) === normalize(form.specialite));
  }, [form.specialite, medecins]);

  const upcomingAppointments = rendezvous.filter((rdv) => isUpcoming(rdv) && !["annule", "termine"].includes(rdv.statut));

  const updateForm = (patch) => {
    setForm((current) => ({ ...current, ...patch }));
    setErrors({});
  };

  const submitAppointment = async (event) => {
    event.preventDefault();
    const nextErrors = {};
    if (!form.specialite) nextErrors.specialite = "Choisissez une specialite";
    if (!form.medecin_id) nextErrors.medecin_id = "Choisissez un medecin";
    if (!form.date) nextErrors.date = "Choisissez une date";
    if (!form.heure) nextErrors.heure = "Choisissez une heure";

    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      showToast("error", "Veuillez completer les champs obligatoires.");
      return;
    }

    setSubmitting(true);
    try {
      await apiFetch("/rendezvous/", {
        method: "POST",
        body: { medecin_id: form.medecin_id, date: form.date, heure: form.heure },
      });
      setForm({ specialite: "", medecin_id: "", date: "", heure: "" });
      setBookingOpen(false);
      showToast("success", "Votre demande de rendez-vous est en attente.");
      await loadDashboard();
    } catch (err) {
      showToast("error", err.message || "Creation du rendez-vous impossible.");
    } finally {
      setSubmitting(false);
    }
  };

  const cancelAppointment = async () => {
    if (!cancelTarget) return;
    setSubmitting(true);
    try {
      await apiFetch(`/rendezvous/${cancelTarget.id}/status/`, {
        method: "POST",
        body: { statut: "annule" },
      });
      setCancelTarget(null);
      showToast("success", "Rendez-vous annule avec succes.");
      await loadDashboard();
    } catch (err) {
      showToast("error", err.message || "Annulation impossible.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Navbar />
      <main className="page patient-dashboard">
        <header className="patient-hero">
          <div>
            <span>Espace patient</span>
            <h1>Clinique Medicale Elite</h1>
            <p>Suivez vos rendez-vous, vos documents medicaux et vos factures depuis un tableau de bord clair et securise.</p>
          </div>
          <button type="button" onClick={() => setBookingOpen(true)}>Prendre un rendez-vous</button>
        </header>

        {toast && <Toast type={toast.type} text={toast.text} onClose={() => setToast(null)} />}
        {loading && <p className="muted">Chargement...</p>}

        {!loading && (
          <>
            <div className="stats">
              <Stat label="Rendez-vous" value={rendezvous.length} />
              <Stat label="A venir" value={upcomingAppointments.length} />
              <Stat label="Consultations" value={consultations.length} />
              <Stat label="A payer" value={factures.filter((facture) => !isFacturePaid(facture)).length} />
            </div>

            <section className="booking-card">
              <div>
                <h2>Besoin d'une consultation ?</h2>
                <p>Choisissez une specialite, un medecin disponible, puis envoyez votre demande en quelques secondes.</p>
              </div>
              <button type="button" className="secondary-button" onClick={() => setBookingOpen(true)}>Nouveau rendez-vous</button>
            </section>

            <section className="panel">
              <div className="section-title">
                <h2>Mes rendez-vous</h2>
                <span>{upcomingAppointments.length} a venir</span>
              </div>
              <ResponsiveTable
                empty={<EmptyState icon="+" title="Aucun rendez-vous" text="Vos prochaines demandes apparaitront ici." />}
                columns={["Medecin", "Specialite", "Date", "Heure", "Statut", "Actions"]}
                rows={rendezvous.map((rdv) => [
                  doctorName(rdv),
                  rdv.specialite || "-",
                  formatDate(rdv.date),
                  formatTime(rdv.heure),
                  <span className={`badge badge-${rdv.statut}`}>{rdvStatusLabel(rdv.statut)}</span>,
                  canCancel(rdv) ? <button type="button" className="danger compact-button" onClick={() => setCancelTarget(rdv)}>Annuler</button> : "-",
                ])}
              />
            </section>

            <section className="panel">
              <h2>Historique medical</h2>
              <ResponsiveTable
                empty={<EmptyState icon="H" title="Aucune consultation" text="Vos comptes rendus medicaux seront disponibles apres vos consultations." />}
                columns={["Date consultation", "Medecin", "Diagnostic", "Traitement", "Notes"]}
                rows={consultations.map((consultation) => [
                  formatDate(consultation.date),
                  doctorName(consultation),
                  consultation.diagnostic || "-",
                  consultation.traitement || "-",
                  consultation.notes || "-",
                ])}
              />
            </section>

            <section className="panel">
              <h2>Mes factures</h2>
              <ResponsiveTable
                empty={<EmptyState icon="$" title="Aucune facture" text="Les factures de consultations et soins apparaitront ici." />}
                columns={["Reference", "Montant", "Date", "Statut"]}
                rows={factures.map((facture) => [
                  `FAC-${facture.id}`,
                  formatMoney(facture.montant),
                  formatDate(facture.date),
                  <span className={`badge badge-${isFacturePaid(facture) ? "paye" : "impaye"}`}>{facture.statut}</span>,
                ])}
              />
            </section>
          </>
        )}
        <Chatbot />
      </main>

      {bookingOpen && (
        <Modal title="Prendre un rendez-vous" onClose={() => setBookingOpen(false)}>
          <form className="stack-form appointment-modal-form" onSubmit={submitAppointment}>
            <SelectField label="Specialite" value={form.specialite} onChange={(value) => updateForm({ specialite: value, medecin_id: "" })} error={errors.specialite} options={SPECIALTIES} placeholder="Choisir une specialite" />
            <SelectField label="Medecin" value={form.medecin_id} onChange={(value) => updateForm({ medecin_id: value })} error={errors.medecin_id} options={filteredDoctors.map((medecin) => ({ value: medecin.id, label: doctorName(medecin) }))} placeholder={form.specialite ? "Choisir un medecin" : "Selectionnez d'abord une specialite"} />
            <Field label="Date" type="date" value={form.date} onChange={(value) => updateForm({ date: value })} error={errors.date} />
            <Field label="Heure" type="time" value={form.heure} onChange={(value) => updateForm({ heure: value })} error={errors.heure} />
            <p className="form-note">Statut initial: <strong>EN_ATTENTE</strong></p>
            <div className="modal-actions">
              <button type="button" className="secondary-button" onClick={() => setBookingOpen(false)}>Annuler</button>
              <button type="submit" disabled={submitting}>{submitting ? "Envoi..." : "Confirmer la demande"}</button>
            </div>
          </form>
        </Modal>
      )}

      {cancelTarget && (
        <Modal title="Annuler ce rendez-vous ?" onClose={() => setCancelTarget(null)}>
          <p className="modal-copy">Votre rendez-vous avec {doctorName(cancelTarget)} le {formatDate(cancelTarget.date)} a {formatTime(cancelTarget.heure)} sera marque comme ANNULE.</p>
          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={() => setCancelTarget(null)}>Conserver</button>
            <button type="button" className="danger" disabled={submitting} onClick={cancelAppointment}>Confirmer l'annulation</button>
          </div>
        </Modal>
      )}
    </>
  );
}

function ResponsiveTable({ columns, rows, empty }) {
  if (!rows.length) {
    return empty;
  }

  return (
    <div className="table-scroll patient-table-scroll">
      <table className="patient-table">
        <thead>
          <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, index) => <td key={columns[index]} data-label={columns[index]}>{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EmptyState({ icon, title, text }) {
  return (
    <div className="empty-state">
      <span>{icon}</span>
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

function Field({ label, value, onChange, error, type = "text" }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} aria-invalid={Boolean(error)} />
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
        {options.map((option) => {
          const value = typeof option === "string" ? option : option.value;
          const label = typeof option === "string" ? option : option.label;
          return <option key={value} value={value}>{label}</option>;
        })}
      </select>
      {error && <small>{error}</small>}
    </label>
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

function Stat({ label, value }) {
  return <div className="stat"><span>{label}</span><strong>{value}</strong></div>;
}

function rdvStatusLabel(statut) {
  return RDV_STATUS_LABELS[statut] || String(statut || "-").replace("_", " ").toUpperCase();
}

function doctorName(item) {
  const raw = item.medecin_display || item.display_name || item.medecin_full_name || item.full_name || item.medecin || item.username || "-";
  if (raw === "-") return raw;
  return raw.startsWith("Dr.") ? raw : `Dr. ${humanizeName(raw)}`;
}

function humanizeName(value) {
  return String(value).split(/[._\s-]+/).filter(Boolean).map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "long", year: "numeric" }).format(date);
}

function formatTime(value) {
  return value ? String(value).slice(0, 5) : "-";
}

function formatMoney(value) {
  return new Intl.NumberFormat("fr-MA", { style: "currency", currency: "MAD" }).format(Number(value || 0));
}

function isFacturePaid(facture) {
  return ["paye", "paye", "payé", "payÃ©", "payÃƒÂ©", "payÃƒÆ’Ã‚Â©"].includes(facture.statut);
}

function canCancel(rdv) {
  return isUpcoming(rdv) && ["en_attente", "confirme"].includes(rdv.statut);
}

function isUpcoming(rdv) {
  if (!rdv.date) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const date = new Date(rdv.date);
  return !Number.isNaN(date.getTime()) && date >= today;
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

export default PatientDashboard;
