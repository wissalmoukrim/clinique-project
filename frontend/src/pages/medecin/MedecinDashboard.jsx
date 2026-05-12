import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "../../api/client";
import Navbar from "../../components/Navbar";

const EMPTY_FORM = {
  diagnostic: "",
  notes: "",
  traitement: "",
};

const RDV_STATUS_LABELS = {
  confirme: "CONFIRME",
  termine: "TERMINE",
  en_attente: "EN_ATTENTE",
  annule: "ANNULE",
};

function MedecinDashboard() {
  const [rendezvous, setRendezvous] = useState([]);
  const [consultations, setConsultations] = useState([]);
  const [selectedRdv, setSelectedRdv] = useState(null);
  const [consultationForm, setConsultationForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const [toast, setToast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const toastTimerRef = useRef(null);

  const showToast = useCallback((type, text) => {
    setToast({ type, text });
    window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToast(null), 3600);
  }, []);

  const loadDashboard = useCallback(async () => {
    try {
      const [rdvData, consultationData] = await Promise.all([
        apiFetch("/rendezvous/"),
        apiFetch("/consultations/"),
      ]);
      setRendezvous(Array.isArray(rdvData) ? rdvData : []);
      setConsultations(Array.isArray(consultationData) ? consultationData : []);
    } catch (err) {
      showToast("error", err.message || "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const confirmedRendezvous = useMemo(() => rendezvous.filter((rdv) => rdv.statut === "confirme"), [rendezvous]);
  const consultedRdvIds = useMemo(() => new Set(consultations.map((consultation) => consultation.rendezvous_id)), [consultations]);
  const pendingConsultations = confirmedRendezvous.filter((rdv) => !consultedRdvIds.has(rdv.id));
  const selectedPatientHistory = selectedRdv
    ? consultations.filter((consultation) => String(consultation.patient_id || consultation.patient) === String(selectedRdv.patient_id || selectedRdv.patient))
    : [];

  const openConsultation = (rdv) => {
    setSelectedRdv(rdv);
    setConsultationForm(EMPTY_FORM);
    setErrors({});
  };

  const updateForm = (patch) => {
    setConsultationForm((current) => ({ ...current, ...patch }));
    setErrors({});
  };

  const createConsultation = async (event) => {
    event.preventDefault();
    if (!selectedRdv) {
      showToast("error", "Selectionnez un rendez-vous confirme.");
      return;
    }

    const nextErrors = {};
    if (!consultationForm.diagnostic.trim()) {
      nextErrors.diagnostic = "Le diagnostic est obligatoire";
    }
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      showToast("error", "Veuillez completer les champs obligatoires.");
      return;
    }

    setSubmitting(true);
    try {
      await apiFetch("/consultations/", {
        method: "POST",
        body: {
          rdv_id: selectedRdv.id,
          diagnostic: consultationForm.diagnostic,
          notes: consultationForm.notes,
          traitement: consultationForm.traitement,
        },
      });
      setSelectedRdv(null);
      setConsultationForm(EMPTY_FORM);
      showToast("success", "Consultation enregistree avec succes.");
      await loadDashboard();
    } catch (err) {
      showToast("error", err.message || "Creation consultation impossible");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Navbar />
      <main className="page medecin-dashboard">
        <header className="doctor-hero">
          <div>
            <span>Espace medecin</span>
            <h1>Workspace de consultation</h1>
            <p>Consultez vos rendez-vous confirmes, ouvrez un dossier patient et enregistrez vos observations medicales.</p>
          </div>
        </header>

        {toast && <Toast type={toast.type} text={toast.text} onClose={() => setToast(null)} />}
        {loading && <p className="muted">Chargement...</p>}

        {!loading && (
          <>
            <div className="stats">
              <Stat label="Rendez-vous" value={rendezvous.length} />
              <Stat label="Confirmes" value={confirmedRendezvous.length} />
              <Stat label="Consultations" value={consultations.length} />
              <Stat label="A traiter" value={pendingConsultations.length} />
            </div>

            <section className="doctor-workspace">
              <div className="panel appointment-panel">
                <div className="section-title">
                  <h2>Rendez-vous confirmes</h2>
                  <span>{pendingConsultations.length} consultation(s) a creer</span>
                </div>
                {confirmedRendezvous.length === 0 ? (
                  <EmptyState title="Aucun rendez-vous confirme" text="Les rendez-vous valides par la reception apparaitront ici." />
                ) : (
                  <div className="appointment-list">
                    {confirmedRendezvous.map((rdv) => {
                      const alreadyConsulted = consultedRdvIds.has(rdv.id);
                      return (
                        <article className={`appointment-item ${selectedRdv?.id === rdv.id ? "active" : ""}`} key={rdv.id}>
                          <div>
                            <h3>{patientName(rdv)}</h3>
                            <p>{formatDate(rdv.date)} a {formatTime(rdv.heure)}</p>
                            <span className={`badge badge-${alreadyConsulted ? "termine" : rdv.statut}`}>
                              {alreadyConsulted ? "CONSULTE" : rdvStatusLabel(rdv.statut)}
                            </span>
                          </div>
                          <button type="button" onClick={() => openConsultation(rdv)} disabled={alreadyConsulted}>
                            {alreadyConsulted ? "Deja creee" : "Ajouter consultation"}
                          </button>
                        </article>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="panel consultation-panel">
                <div className="section-title">
                  <h2>Consultation medicale</h2>
                  {selectedRdv && <span>Dossier #{selectedRdv.id}</span>}
                </div>
                {!selectedRdv ? (
                  <EmptyState title="Selectionnez un rendez-vous" text="Cliquez sur Ajouter consultation depuis un rendez-vous confirme pour pre-remplir le contexte patient." />
                ) : (
                  <>
                    <div className="consultation-context">
                      <Info label="Patient" value={patientName(selectedRdv)} />
                      <Info label="Medecin" value={doctorName(selectedRdv)} />
                      <Info label="Rendez-vous" value={`#${selectedRdv.id}`} />
                      <Info label="Date" value={`${formatDate(selectedRdv.date)} a ${formatTime(selectedRdv.heure)}`} />
                    </div>

                    <form className="medical-form" onSubmit={createConsultation}>
                      <fieldset>
                        <legend>Diagnostic</legend>
                        <Field
                          label="Diagnostic clinique"
                          value={consultationForm.diagnostic}
                          onChange={(value) => updateForm({ diagnostic: value })}
                          error={errors.diagnostic}
                          placeholder="Resume du diagnostic, signes cliniques, orientation..."
                          required
                        />
                      </fieldset>

                      <fieldset>
                        <legend>Notes medicales</legend>
                        <Field
                          label="Observations"
                          value={consultationForm.notes}
                          onChange={(value) => updateForm({ notes: value })}
                          placeholder="Antecedents pertinents, examens, suivi recommande..."
                        />
                      </fieldset>

                      <fieldset>
                        <legend>Prescription et traitement</legend>
                        <Field
                          label="Traitement / ordonnance"
                          value={consultationForm.traitement}
                          onChange={(value) => updateForm({ traitement: value })}
                          placeholder="Instructions therapeutiques, medicaments, posologie, conseils..."
                        />
                      </fieldset>

                      <div className="modal-actions">
                        <button type="button" className="secondary-button" onClick={() => setSelectedRdv(null)}>Annuler</button>
                        <button type="submit" disabled={submitting}>{submitting ? "Enregistrement..." : "Enregistrer la consultation"}</button>
                      </div>
                    </form>
                  </>
                )}
              </div>
            </section>

            {selectedRdv && (
              <section className="panel">
                <div className="section-title">
                  <h2>Historique du patient</h2>
                  <span>{patientName(selectedRdv)}</span>
                </div>
                <HistoryTable consultations={selectedPatientHistory} currentRdvId={selectedRdv.id} />
              </section>
            )}

            <section className="panel">
              <h2>Consultations realisees</h2>
              <HistoryTable consultations={consultations} />
            </section>
          </>
        )}
      </main>
    </>
  );
}

function HistoryTable({ consultations, currentRdvId }) {
  const rows = consultations.filter((consultation) => consultation.rendezvous_id !== currentRdvId);
  if (!rows.length) {
    return <EmptyState title="Aucun historique disponible" text="Les consultations precedentes accessibles pour ce patient seront listees ici." />;
  }

  return (
    <div className="table-scroll doctor-table-scroll">
      <table className="doctor-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Patient</th>
            <th>Diagnostic</th>
            <th>Traitement</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((consultation) => (
            <tr key={consultation.id}>
              <td data-label="Date">{formatDate(consultation.date)}</td>
              <td data-label="Patient">{patientName(consultation)}</td>
              <td data-label="Diagnostic">{consultation.diagnostic || "-"}</td>
              <td data-label="Traitement">{consultation.traitement || "-"}</td>
              <td data-label="Notes">{consultation.notes || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Field({ label, value, onChange, error, placeholder }) {
  return (
    <label className="field">
      <span>{label}</span>
      <textarea value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} aria-invalid={Boolean(error)} />
      {error && <small>{error}</small>}
    </label>
  );
}

function Info({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EmptyState({ title, text }) {
  return (
    <div className="empty-state doctor-empty">
      <span>+</span>
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

function Toast({ type, text, onClose }) {
  return <div className={`toast toast-${type}`}><span>{text}</span><button type="button" onClick={onClose}>x</button></div>;
}

function Stat({ label, value }) {
  return <div className="stat"><span>{label}</span><strong>{value}</strong></div>;
}

function patientName(item) {
  return item.patient_display || item.patient_full_name || humanizeName(item.patient || item.username || "-");
}

function doctorName(item) {
  const raw = item.medecin_display || item.medecin_full_name || item.full_name || item.medecin || "-";
  return raw === "-" || raw.startsWith("Dr.") ? raw : `Dr. ${humanizeName(raw)}`;
}

function humanizeName(value) {
  return String(value).split(/[._\s-]+/).filter(Boolean).map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}

function rdvStatusLabel(statut) {
  return RDV_STATUS_LABELS[statut] || String(statut || "-").replace("_", " ").toUpperCase();
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

export default MedecinDashboard;
