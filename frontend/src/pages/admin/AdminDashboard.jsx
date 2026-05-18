import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch, getCurrentUser } from "../../api/client";
import Navbar from "../../components/Navbar";

const PAGE_SIZE = 6;
const EMPLOYEE_ROLES = ["medecin", "secretaire", "infirmier", "comptable", "securite", "chauffeur"];
const EMPTY_SECURITY = { summary: {}, logs: [], locked_users: [] };
const EMPTY_FORMS = {
  patient: { user_id: "", telephone: "", adresse: "" },
  medecin: { user_id: "", specialite: "", telephone: "", experience: "", disponible: true },
  ambulance: { matricule: "", type: "standard", disponible: true, chauffeur_id: "" },
  rdv: { patient_id: "", medecin_id: "", date: "", heure: "", statut: "en_attente" },
};

function AdminDashboard() {
  const currentUser = getCurrentUser();
  const [users, setUsers] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [patients, setPatients] = useState([]);
  const [medecins, setMedecins] = useState([]);
  const [rendezvous, setRendezvous] = useState([]);
  const [ambulances, setAmbulances] = useState([]);
  const [security, setSecurity] = useState(EMPTY_SECURITY);
  const [forms, setForms] = useState(EMPTY_FORMS);
  const [employeeForm, setEmployeeForm] = useState(emptyEmployeeForm());
  const [employeeErrors, setEmployeeErrors] = useState({});
  const [fieldErrors, setFieldErrors] = useState({});
  const [toast, setToast] = useState(null);
  const [modal, setModal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const toastTimerRef = useRef(null);

  const showToast = useCallback((type, text) => {
    setToast({ type, text });
    window.clearTimeout(toastTimerRef.current);
    toastTimerRef.current = window.setTimeout(() => setToast(null), 3600);
  }, []);

  const loadDashboard = useCallback(async () => {
    try {
      const [usersData, employeesData, patientsData, medecinsData, rendezvousData, ambulancesData, securityData] = await Promise.all([
        apiFetch("/auth/users/"),
        apiFetch("/auth/employees/"),
        apiFetch("/patients/"),
        apiFetch("/medecins/"),
        apiFetch("/rendezvous/"),
        apiFetch("/ambulance/"),
        apiFetch("/core/security/"),
      ]);

      setUsers(asArray(usersData));
      setEmployees(asArray(employeesData));
      setPatients(asArray(patientsData));
      setMedecins(asArray(medecinsData));
      setRendezvous(asArray(rendezvousData));
      setAmbulances(asArray(ambulancesData));
      setSecurity(securityData || EMPTY_SECURITY);
    } catch (err) {
      showToast("error", err.message || "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const usedPatientUserIds = useMemo(() => new Set(patients.map((patient) => String(patient.user_id))), [patients]);
  const usedMedecinUserIds = useMemo(() => new Set(medecins.map((medecin) => String(medecin.user_id))), [medecins]);
  const patientUsers = users.filter((user) => user.role === "patient" && !usedPatientUserIds.has(String(user.id)));
  const medecinUsers = users.filter((user) => user.role === "medecin" && !usedMedecinUserIds.has(String(user.id)));
  const chauffeurOptions = useMemo(() => toChauffeurOptions(employees), [employees]);

  const updateForm = (name, patch) => {
    setForms((current) => ({ ...current, [name]: { ...current[name], ...patch } }));
    setFieldErrors((current) => ({ ...current, [name]: null }));
  };

  const validate = (name, rules) => {
    const errors = {};
    Object.entries(rules).forEach(([field, label]) => {
      if (!String(forms[name][field] ?? "").trim()) {
        errors[field] = `${label} est obligatoire`;
      }
    });
    setFieldErrors((current) => ({ ...current, [name]: errors }));
    return Object.keys(errors).length === 0;
  };

  const createPatient = async (event) => {
    event.preventDefault();
    if (!validate("patient", { user_id: "Utilisateur" })) return;
    await submitCrud(() => apiFetch("/patients/", { method: "POST", body: forms.patient }), "Patient ajoute", () => {
      updateForm("patient", EMPTY_FORMS.patient);
    });
  };

  const createMedecin = async (event) => {
    event.preventDefault();
    if (!validate("medecin", { user_id: "Utilisateur", specialite: "Specialite" })) return;
    await submitCrud(() => apiFetch("/medecins/", { method: "POST", body: forms.medecin }), "Medecin ajoute", () => {
      updateForm("medecin", EMPTY_FORMS.medecin);
    });
  };

  const createAmbulance = async (event) => {
    event.preventDefault();
    if (!validate("ambulance", { matricule: "Matricule", type: "Type" })) return;
    await submitCrud(() => apiFetch("/ambulance/", { method: "POST", body: forms.ambulance }), "Ambulance ajoutee", () => {
      updateForm("ambulance", EMPTY_FORMS.ambulance);
    });
  };

  const createRdv = async (event) => {
    event.preventDefault();
    if (!validate("rdv", { patient_id: "Patient", medecin_id: "Medecin", date: "Date", heure: "Heure" })) return;
    await submitCrud(() => apiFetch("/rendezvous/", { method: "POST", body: forms.rdv }), "Rendez-vous ajoute", () => {
      updateForm("rdv", EMPTY_FORMS.rdv);
    });
  };

  const submitCrud = async (request, successText, afterSuccess) => {
    setSaving(true);
    try {
      await request();
      afterSuccess?.();
      showToast("success", successText);
      await loadDashboard();
    } catch (err) {
      showToast("error", err.message || "Operation impossible");
    } finally {
      setSaving(false);
    }
  };

  const openEdit = (type, item) => {
    setModal({ type: "edit", resource: type, item, values: toEditValues(type, item) });
  };

  const openDelete = (type, item) => {
    setModal({ type: "delete", resource: type, item });
  };

  const updateModalValues = (patch) => {
    setModal((current) => ({ ...current, values: { ...current.values, ...patch } }));
  };

  const saveEdit = async (event) => {
    event.preventDefault();
    const { resource, item, values } = modal;
    if (modal.type === "employee-edit") {
      await submitCrud(() => apiFetch(`/auth/employees/${item.id}/`, { method: "PUT", body: values }), "Employe modifie", () => setModal(null));
      return;
    }
    const endpoint = editEndpoint(resource, item.id);
    await submitCrud(() => apiFetch(endpoint, { method: "PUT", body: values }), "Modification enregistree", () => setModal(null));
  };

  const confirmDelete = async () => {
    const { resource, item } = modal;
    if (modal.type === "employee-delete") {
      if (String(item.id) === String(currentUser?.id)) {
        showToast("error", "Vous ne pouvez pas supprimer votre propre compte.");
        setModal(null);
        return;
      }
      await submitCrud(() => apiFetch(`/auth/employees/${item.id}/`, { method: "DELETE" }), "Employe supprime", () => setModal(null));
      return;
    }
    await submitCrud(() => apiFetch(deleteEndpoint(resource, item.id), { method: "DELETE" }), "Element supprime", () => setModal(null));
  };

  const charts = useMemo(() => makeCharts(patients, rendezvous, security), [patients, rendezvous, security]);
  const employeeStats = useMemo(() => ({
    total: employees.length,
    active: employees.filter((employee) => employee.actif !== false && employee.is_active !== false).length,
    doctors: employees.filter((employee) => employee.role === "medecin").length,
    locked: employees.filter((employee) => employee.is_locked).length,
  }), [employees]);

  const updateEmployeeForm = (patch) => {
    setEmployeeForm((current) => ({ ...current, ...patch }));
    setEmployeeErrors({});
  };

  const validateEmployee = () => {
    const errors = {};
    ["first_name", "last_name", "username", "email", "role", "password", "confirmPassword"].forEach((field) => {
      if (!String(employeeForm[field] || "").trim()) {
        errors[field] = "Champ obligatoire";
      }
    });
    if (employeeForm.email && !employeeForm.email.includes("@")) errors.email = "Email invalide";
    if (employeeForm.password && !isStrongPassword(employeeForm.password)) errors.password = "8 caracteres min., majuscule, minuscule, chiffre et caractere special";
    if (employeeForm.password !== employeeForm.confirmPassword) errors.confirmPassword = "Les mots de passe ne correspondent pas";
    if (employeeForm.role === "medecin" && !employeeForm.specialite.trim()) errors.specialite = "Specialite obligatoire";
    if (users.some((user) => user.username === employeeForm.username)) errors.username = "Username deja utilise";
    if (employeeForm.email && users.some((user) => user.email === employeeForm.email)) errors.email = "Email deja utilise";
    setEmployeeErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const createEmployee = async (event) => {
    event.preventDefault();
    if (!validateEmployee()) {
      showToast("error", "Veuillez verifier le formulaire employe.");
      return;
    }
    const { confirmPassword, ...payload } = employeeForm;
    await submitCrud(() => apiFetch("/auth/employees/", { method: "POST", body: payload }), "Employe cree", () => {
      setEmployeeForm(emptyEmployeeForm());
    });
  };

  return (
    <>
      <Navbar />
      <main className="page admin-dashboard">
        <header className="dashboard-heading">
          <div>
            <h1>Dashboard Admin</h1>
            <p>Operations cliniques, rendez-vous et securite en temps reel.</p>
          </div>
        </header>

        {toast && <Toast type={toast.type} text={toast.text} onClose={() => setToast(null)} />}
        {loading && <p className="muted">Chargement...</p>}

        {!loading && (
          <>
            <div className="stats">
              <Stat label="Patients" value={patients.length} trend={charts.patientTrend} />
              <Stat label="Medecins" value={medecins.length} />
              <Stat label="Rendez-vous" value={rendezvous.length} trend={charts.rdvTrend} />
              <Stat label="Ambulances" value={ambulances.length} />
              <Stat label="Alertes securite" value={security.summary?.alerts || 0} trend={charts.securityTrend} />
            </div>

            <section className="chart-grid">
              <MiniChart title="Rendez-vous par statut" data={charts.rdvStatus} />
              <MiniChart title="Patients par profil" data={charts.patientProfile} />
              <MiniChart title="Activite securite" data={charts.securityActivity} />
            </section>

            <section id="personnel" className="panel personnel-section">
              <div className="section-title">
                <h2>Personnel & utilisateurs</h2>
                <span>Admin seulement</span>
              </div>
              <div className="stats compact-stats">
                <Stat label="Employes" value={employeeStats.total} />
                <Stat label="Actifs" value={employeeStats.active} />
                <Stat label="Medecins" value={employeeStats.doctors} />
                <Stat label="Bloques" value={employeeStats.locked} />
              </div>
              <form className="employee-form" onSubmit={createEmployee}>
                <Field label="Prenom" placeholder="Prenom" value={employeeForm.first_name} onChange={(value) => updateEmployeeForm({ first_name: value })} error={employeeErrors.first_name} />
                <Field label="Nom" placeholder="Nom" value={employeeForm.last_name} onChange={(value) => updateEmployeeForm({ last_name: value })} error={employeeErrors.last_name} />
                <Field label="Username" placeholder="identifiant" value={employeeForm.username} onChange={(value) => updateEmployeeForm({ username: value })} error={employeeErrors.username} />
                <Field label="Email" type="email" placeholder="email@clinique.ma" value={employeeForm.email} onChange={(value) => updateEmployeeForm({ email: value })} error={employeeErrors.email} />
                <Field label="Telephone" placeholder="+212 600 000 000" value={employeeForm.telephone} onChange={(value) => updateEmployeeForm({ telephone: value })} />
                <SelectField label="Role" value={employeeForm.role} onChange={(value) => updateEmployeeForm({ role: value })} options={EMPLOYEE_ROLES} />
                <Field label="Mot de passe" type="password" placeholder="Mot de passe fort" value={employeeForm.password} onChange={(value) => updateEmployeeForm({ password: value })} error={employeeErrors.password} />
                <Field label="Confirmation" type="password" placeholder="Confirmer" value={employeeForm.confirmPassword} onChange={(value) => updateEmployeeForm({ confirmPassword: value })} error={employeeErrors.confirmPassword} />
                {employeeForm.role === "medecin" && (
                  <>
                    <Field label="Specialite" placeholder="Cardiologie" value={employeeForm.specialite} onChange={(value) => updateEmployeeForm({ specialite: value })} error={employeeErrors.specialite} />
                    <Field label="Experience" type="number" placeholder="8" value={employeeForm.experience} onChange={(value) => updateEmployeeForm({ experience: value })} />
                  </>
                )}
                <button type="submit" disabled={saving}>{saving ? "Creation..." : "Creer employe"}</button>
              </form>
            </section>

            <EmployeeTable
              employees={employees}
              currentUserId={currentUser?.id}
              onEdit={(employee) => setModal({ type: "employee-edit", item: employee, values: employeeToForm(employee) })}
              onDelete={(employee) => setModal({ type: "employee-delete", item: employee })}
            />

            <section className="form-grid">
              <FormPanel title="Nouveau medecin" onSubmit={createMedecin} saving={saving}>
                <SearchableSelect
                  label="Utilisateur medecin"
                  placeholder="Rechercher un compte medecin"
                  value={forms.medecin.user_id}
                  options={toUserOptions(medecinUsers)}
                  onChange={(value) => updateForm("medecin", { user_id: value })}
                  error={fieldErrors.medecin?.user_id}
                />
                <Field label="Specialite" placeholder="Cardiologie" value={forms.medecin.specialite} onChange={(value) => updateForm("medecin", { specialite: value })} error={fieldErrors.medecin?.specialite} />
                <Field label="Telephone" placeholder="+212 600 000 000" value={forms.medecin.telephone} onChange={(value) => updateForm("medecin", { telephone: value })} />
                <Field label="Experience" type="number" placeholder="8" value={forms.medecin.experience} onChange={(value) => updateForm("medecin", { experience: value })} />
              </FormPanel>

              <FormPanel title="Nouveau patient" onSubmit={createPatient} saving={saving}>
                <SearchableSelect
                  label="Utilisateur patient"
                  placeholder="Rechercher un compte patient"
                  value={forms.patient.user_id}
                  options={toUserOptions(patientUsers)}
                  onChange={(value) => updateForm("patient", { user_id: value })}
                  error={fieldErrors.patient?.user_id}
                />
                <Field label="Telephone" placeholder="+212 600 000 000" value={forms.patient.telephone} onChange={(value) => updateForm("patient", { telephone: value })} />
                <Field label="Adresse" placeholder="Adresse complete" value={forms.patient.adresse} onChange={(value) => updateForm("patient", { adresse: value })} />
              </FormPanel>

              <FormPanel title="Nouveau rendez-vous" onSubmit={createRdv} saving={saving}>
                <SearchableSelect label="Patient" placeholder="Rechercher un patient" value={forms.rdv.patient_id} options={toEntityOptions(patients)} onChange={(value) => updateForm("rdv", { patient_id: value })} error={fieldErrors.rdv?.patient_id} />
                <SearchableSelect label="Medecin" placeholder="Rechercher un medecin" value={forms.rdv.medecin_id} options={toDoctorOptions(medecins)} onChange={(value) => updateForm("rdv", { medecin_id: value })} error={fieldErrors.rdv?.medecin_id} />
                <Field label="Date" type="date" value={forms.rdv.date} onChange={(value) => updateForm("rdv", { date: value })} error={fieldErrors.rdv?.date} />
                <Field label="Heure" type="time" value={forms.rdv.heure} onChange={(value) => updateForm("rdv", { heure: value })} error={fieldErrors.rdv?.heure} />
              </FormPanel>

              <FormPanel title="Nouvelle ambulance" onSubmit={createAmbulance} saving={saving}>
                <Field label="Matricule" placeholder="AMB-2026-01" value={forms.ambulance.matricule} onChange={(value) => updateForm("ambulance", { matricule: value })} error={fieldErrors.ambulance?.matricule} />
                <SelectField label="Type" value={forms.ambulance.type} onChange={(value) => updateForm("ambulance", { type: value })} options={["standard", "medicalisee", "urgence"]} />
                <SearchableSelect label="Chauffeur" placeholder="Rechercher un chauffeur" value={forms.ambulance.chauffeur_id} options={chauffeurOptions} onChange={(value) => updateForm("ambulance", { chauffeur_id: value })} emptyLabel="Sans chauffeur" />
              </FormPanel>
            </section>

            <DataTable
              title="Patients"
              rows={patients}
              columns={[
                ["username", "Username"],
                ["telephone", "Telephone"],
                ["adresse", "Adresse"],
              ]}
              renderActions={(patient) => <TableActions onEdit={() => openEdit("patient", patient)} onDelete={() => openDelete("patient", patient)} />}
            />

            <DataTable
              title="Medecins"
              rows={medecins}
              columns={[
                ["username", "Username"],
                ["specialite", "Specialite"],
                ["telephone", "Telephone"],
                ["experience", "Experience"],
              ]}
              renderActions={(medecin) => <TableActions onEdit={() => openEdit("medecin", medecin)} onDelete={() => openDelete("medecin", medecin)} />}
            />

            <DataTable
              title="Rendez-vous"
              rows={rendezvous}
              columns={[
                ["patient", "Patient"],
                ["medecin", "Medecin"],
                ["date", "Date"],
                ["heure", "Heure"],
                ["statut", "Statut", (rdv) => <span className={`badge badge-${rdv.statut}`}>{rdv.statut}</span>],
              ]}
              renderActions={(rdv) => <TableActions onEdit={() => openEdit("rdv", rdv)} onDelete={() => openDelete("rdv", rdv)} />}
            />

            <DataTable
              title="Ambulances"
              rows={ambulances}
              columns={[
                ["matricule", "Matricule"],
                ["type", "Type"],
                ["disponible", "Disponible", (ambulance) => (ambulance.disponible ? "Oui" : "Non")],
                ["chauffeur", "Chauffeur", (ambulance) => ambulance.chauffeur_display || ambulance.chauffeur || "-"],
              ]}
              renderActions={(ambulance) => <TableActions onEdit={() => openEdit("ambulance", ambulance)} onAssign={() => openEdit("ambulance", ambulance)} onDelete={() => openDelete("ambulance", ambulance)} />}
            />

            <section className="panel">
              <h2>Securite</h2>
              <div className="stats compact-stats">
                <Stat label="Echecs login" value={security.summary?.failed_logins || 0} />
                <Stat label="Acces interdits" value={security.summary?.forbidden_access || 0} />
                <Stat label="Comptes bloques" value={security.summary?.locked_accounts || 0} />
                <Stat label="Utilisateurs actifs" value={security.summary?.active_users || 0} />
              </div>
              <DataTable
                embedded
                title="Audit logs"
                rows={security.logs || []}
                columns={[
                  ["timestamp", "Date", (log) => formatDate(log.timestamp)],
                  ["user", "User"],
                  ["action", "Action", (log) => <span className={`badge ${log.action}`}>{log.action}</span>],
                  ["resource", "Resource"],
                  ["ip_address", "IP"],
                  ["details", "Details"],
                ]}
              />
            </section>
          </>
        )}
      </main>
      {modal?.type === "edit" && (
        <Modal title={`Modifier ${resourceLabel(modal.resource)}`} onClose={() => setModal(null)}>
          <EditForm modal={modal} patients={patients} medecins={medecins} chauffeurs={chauffeurOptions} saving={saving} onChange={updateModalValues} onSubmit={saveEdit} />
        </Modal>
      )}
      {modal?.type === "employee-edit" && (
        <Modal title={`Modifier ${modal.item.full_name || modal.item.username}`} onClose={() => setModal(null)}>
          <EmployeeEditForm values={modal.values} saving={saving} onChange={updateModalValues} onSubmit={saveEdit} />
        </Modal>
      )}
      {modal?.type === "employee-delete" && (
        <Modal title="Supprimer employe" onClose={() => setModal(null)}>
          <p className="modal-copy">Cette action supprimera le compte {modal.item.username}. Les mots de passe ne sont jamais affiches.</p>
          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={() => setModal(null)}>Annuler</button>
            <button type="button" className="danger" disabled={saving || String(modal.item.id) === String(currentUser?.id)} onClick={confirmDelete}>{saving ? "Suppression..." : "Supprimer"}</button>
          </div>
        </Modal>
      )}
      {modal?.type === "delete" && (
        <Modal title="Confirmer la suppression" onClose={() => setModal(null)}>
          <p className="modal-copy">Cette action supprimera {resourceLabel(modal.resource)} #{modal.item.id}.</p>
          <div className="modal-actions">
            <button type="button" className="secondary-button" onClick={() => setModal(null)}>Annuler</button>
            <button type="button" className="danger" disabled={saving} onClick={confirmDelete}>{saving ? "Suppression..." : "Supprimer"}</button>
          </div>
        </Modal>
      )}
    </>
  );
}

function FormPanel({ title, onSubmit, children, saving }) {
  return (
    <section className="panel form-panel">
      <h2>{title}</h2>
      <form className="stack-form" onSubmit={onSubmit}>
        {children}
        <button type="submit" disabled={saving}>{saving ? "Enregistrement..." : "Enregistrer"}</button>
      </form>
    </section>
  );
}

function EmployeeTable({ employees, currentUserId, onEdit, onDelete }) {
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [page, setPage] = useState(1);
  const filtered = employees.filter((employee) => {
    const matchesSearch = JSON.stringify(employee).toLowerCase().includes(search.toLowerCase());
    const matchesRole = !roleFilter || employee.role === roleFilter;
    return matchesSearch && matchesRole;
  });
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageRows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  useEffect(() => {
    setPage(1);
  }, [search, roleFilter, employees.length]);

  return (
    <section className="panel employee-table-panel">
      <div className="table-toolbar">
        <h2>Liste du personnel</h2>
        <div className="toolbar-controls">
          <input type="search" placeholder="Rechercher employe..." value={search} onChange={(event) => setSearch(event.target.value)} />
          <select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value)}>
            <option value="">Tous les roles</option>
            {EMPLOYEE_ROLES.map((role) => <option key={role} value={role}>{role}</option>)}
          </select>
        </div>
      </div>
      <div className="table-scroll">
        <table className="employee-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
              <th>Nom complet</th>
              <th>Role</th>
              <th>Phone</th>
              <th>Status</th>
              <th>Date creation</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {pageRows.map((employee) => (
              <tr key={employee.id}>
                <td data-label="ID">{employee.id}</td>
                <td data-label="Username">{employee.username}</td>
                <td data-label="Email">{employee.email || "-"}</td>
                <td data-label="Nom complet">{employee.full_name || "-"}</td>
                <td data-label="Role"><span className="badge">{employee.role}</span></td>
                <td data-label="Phone">{employee.telephone || "-"}</td>
                <td data-label="Status"><span className={`badge badge-${employee.actif !== false && employee.is_active !== false ? "paye" : "annule"}`}>{employee.actif !== false && employee.is_active !== false ? "ACTIF" : "INACTIF"}</span></td>
                <td data-label="Date creation">{formatDate(employee.date_joined)}</td>
                <td data-label="Actions">
                  <div className="row-actions">
                    <button type="button" className="secondary-button" onClick={() => onEdit(employee)}>Edit</button>
                    <button type="button" className="danger" disabled={String(employee.id) === String(currentUserId)} onClick={() => onDelete(employee)}>Delete</button>
                  </div>
                </td>
              </tr>
            ))}
            {!pageRows.length && <tr><td className="empty-cell" colSpan="9">Aucun employe</td></tr>}
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

function EmployeeEditForm({ values, saving, onChange, onSubmit }) {
  return (
    <form className="stack-form" onSubmit={onSubmit}>
      <div className="form-pair">
        <Field label="Prenom" value={values.first_name} onChange={(value) => onChange({ first_name: value })} />
        <Field label="Nom" value={values.last_name} onChange={(value) => onChange({ last_name: value })} />
      </div>
      <Field label="Username" value={values.username} onChange={(value) => onChange({ username: value })} />
      <Field label="Email" type="email" value={values.email} onChange={(value) => onChange({ email: value })} />
      <Field label="Telephone" value={values.telephone} onChange={(value) => onChange({ telephone: value })} />
      <SelectField label="Role" value={values.role} onChange={(value) => onChange({ role: value })} options={EMPLOYEE_ROLES} />
      <SelectField label="Compte actif" value={String(values.is_active)} onChange={(value) => onChange({ is_active: value === "true", actif: value === "true" })} options={["true", "false"]} />
      {values.role === "medecin" && (
        <div className="form-pair">
          <Field label="Specialite" value={values.specialite} onChange={(value) => onChange({ specialite: value })} />
          <Field label="Experience" type="number" value={values.experience} onChange={(value) => onChange({ experience: value })} />
        </div>
      )}
      <p className="modal-copy">Le mot de passe actuel n'est jamais affiche. La reinitialisation peut etre ajoutee via une action dediee.</p>
      <ModalSubmit saving={saving} />
    </form>
  );
}

function Field({ label, value, onChange, error, type = "text", placeholder = "" }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type={type} placeholder={placeholder} value={value ?? ""} onChange={(event) => onChange(event.target.value)} aria-invalid={Boolean(error)} />
      {error && <small>{error}</small>}
    </label>
  );
}

function SelectField({ label, value, onChange, options }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
    </label>
  );
}

function SearchableSelect({ label, value, options, onChange, placeholder, error, emptyLabel }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const selected = options.find((option) => String(option.value) === String(value));
  const filtered = options.filter((option) => option.label.toLowerCase().includes(query.toLowerCase())).slice(0, 8);

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
          {emptyLabel && (
            <button
              type="button"
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => {
                onChange("");
                setQuery("");
                setOpen(false);
              }}
            >
              {emptyLabel}
            </button>
          )}
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
              {option.label}
            </button>
          )) : <span>Aucun resultat</span>}
        </div>
      )}
      {error && <small>{error}</small>}
    </label>
  );
}

function DataTable({ title, rows, columns, renderActions, embedded = false }) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const filtered = rows.filter((row) => JSON.stringify(row).toLowerCase().includes(search.toLowerCase()));
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageRows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  useEffect(() => {
    setPage(1);
  }, [search, rows.length]);

  const content = (
    <>
      <div className="table-toolbar">
        <h2>{title}</h2>
        <input type="search" placeholder="Rechercher..." value={search} onChange={(event) => setSearch(event.target.value)} />
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {columns.map(([, label]) => <th key={label}>{label}</th>)}
              {renderActions && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row) => (
              <tr key={row.id}>
                {columns.map(([key, label, render]) => (
                  <td key={key} data-label={label}>{render ? render(row) : display(row[key])}</td>
                ))}
                {renderActions && <td data-label="Actions">{renderActions(row)}</td>}
              </tr>
            ))}
            {!pageRows.length && (
              <tr><td colSpan={columns.length + (renderActions ? 1 : 0)} className="empty-cell">Aucune donnee</td></tr>
            )}
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
  );

  return embedded ? <div className="embedded-table">{content}</div> : <section className="panel">{content}</section>;
}

function EditForm({ modal, patients, medecins, chauffeurs, saving, onChange, onSubmit }) {
  const values = modal.values;
  if (modal.resource === "patient") {
    return <form className="stack-form" onSubmit={onSubmit}><Field label="Telephone" value={values.telephone} onChange={(value) => onChange({ telephone: value })} /><Field label="Adresse" value={values.adresse} onChange={(value) => onChange({ adresse: value })} /><ModalSubmit saving={saving} /></form>;
  }
  if (modal.resource === "medecin") {
    return <form className="stack-form" onSubmit={onSubmit}><Field label="Specialite" value={values.specialite} onChange={(value) => onChange({ specialite: value })} /><Field label="Telephone" value={values.telephone} onChange={(value) => onChange({ telephone: value })} /><Field label="Experience" type="number" value={values.experience} onChange={(value) => onChange({ experience: value })} /><SelectField label="Disponible" value={String(values.disponible)} onChange={(value) => onChange({ disponible: value === "true" })} options={["true", "false"]} /><ModalSubmit saving={saving} /></form>;
  }
  if (modal.resource === "rdv") {
    return <form className="stack-form" onSubmit={onSubmit}><SearchableSelect label="Patient" value={values.patient_id} options={toEntityOptions(patients)} onChange={(value) => onChange({ patient_id: value })} placeholder="Rechercher un patient" /><SearchableSelect label="Medecin" value={values.medecin_id} options={toDoctorOptions(medecins)} onChange={(value) => onChange({ medecin_id: value })} placeholder="Rechercher un medecin" /><Field label="Date" type="date" value={values.date} onChange={(value) => onChange({ date: value })} /><Field label="Heure" type="time" value={values.heure?.slice(0, 5)} onChange={(value) => onChange({ heure: value })} /><SelectField label="Statut" value={values.statut} onChange={(value) => onChange({ statut: value })} options={["en_attente", "confirme", "annule", "termine"]} /><ModalSubmit saving={saving} /></form>;
  }
  return <form className="stack-form" onSubmit={onSubmit}><Field label="Matricule" value={values.matricule} onChange={(value) => onChange({ matricule: value })} /><SelectField label="Type" value={values.type} onChange={(value) => onChange({ type: value })} options={["standard", "medicalisee", "urgence"]} /><SelectField label="Disponible" value={String(values.disponible)} onChange={(value) => onChange({ disponible: value === "true" })} options={["true", "false"]} /><SearchableSelect label="Chauffeur" value={values.chauffeur_id} options={chauffeurs} onChange={(value) => onChange({ chauffeur_id: value })} placeholder="Rechercher un chauffeur" emptyLabel="Retirer le chauffeur" /><ModalSubmit saving={saving} /></form>;
}

function ModalSubmit({ saving }) {
  return <div className="modal-actions"><button type="submit" disabled={saving}>{saving ? "Enregistrement..." : "Enregistrer"}</button></div>;
}

function TableActions({ onEdit, onAssign, onDelete }) {
  return <div className="row-actions"><button type="button" className="secondary-button" onClick={onEdit}>Edit</button>{onAssign && <button type="button" className="secondary-button" onClick={onAssign}>Assign Chauffeur</button>}<button type="button" className="danger" onClick={onDelete}>Delete</button></div>;
}

function Modal({ title, children, onClose }) {
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal-card">
        <div className="modal-header"><h2>{title}</h2><button type="button" className="secondary-button" onClick={onClose}>Fermer</button></div>
        {children}
      </div>
    </div>
  );
}

function Toast({ type, text, onClose }) {
  return <div className={`toast toast-${type}`}><span>{text}</span><button type="button" onClick={onClose}>x</button></div>;
}

function Stat({ label, value, trend }) {
  return <div className="stat"><span>{label}</span><strong>{value}</strong>{trend && <Sparkline values={trend} />}</div>;
}

function MiniChart({ title, data }) {
  const max = Math.max(1, ...data.map((item) => item.value));
  return <section className="panel chart-card"><h2>{title}</h2>{data.map((item) => <div className="chart-row" key={item.label}><span>{item.label}</span><div><i style={{ width: `${Math.max(7, (item.value / max) * 100)}%` }} /></div><strong>{item.value}</strong></div>)}</section>;
}

function Sparkline({ values }) {
  const max = Math.max(1, ...values);
  return <div className="sparkline">{values.map((value, index) => <i key={index} style={{ height: `${Math.max(14, (value / max) * 38)}px` }} />)}</div>;
}

function makeCharts(patients, rdvs, security) {
  const counts = rdvs.reduce((acc, rdv) => ({ ...acc, [rdv.statut]: (acc[rdv.statut] || 0) + 1 }), {});
  return {
    patientTrend: distribute(patients.length, 7),
    rdvTrend: distribute(rdvs.length, 7),
    securityTrend: distribute((security.logs || []).length, 7),
    rdvStatus: ["en_attente", "confirme", "annule", "termine"].map((label) => ({ label, value: counts[label] || 0 })),
    patientProfile: [
      { label: "Avec telephone", value: patients.filter((patient) => patient.telephone).length },
      { label: "Avec adresse", value: patients.filter((patient) => patient.adresse).length },
      { label: "Profil incomplet", value: patients.filter((patient) => !patient.telephone || !patient.adresse).length },
    ],
    securityActivity: [
      { label: "Echecs login", value: security.summary?.failed_logins || 0 },
      { label: "Acces interdits", value: security.summary?.forbidden_access || 0 },
      { label: "Comptes bloques", value: security.summary?.locked_accounts || 0 },
    ],
  };
}

function distribute(total, slots) {
  return Array.from({ length: slots }, (_, index) => Math.max(0, Math.round(total / slots + ((index % 3) - 1))));
}

function emptyEmployeeForm() {
  return {
    first_name: "",
    last_name: "",
    username: "",
    email: "",
    telephone: "",
    role: "secretaire",
    password: "",
    confirmPassword: "",
    specialite: "",
    experience: "",
  };
}

function employeeToForm(employee) {
  return {
    first_name: employee.first_name || "",
    last_name: employee.last_name || "",
    username: employee.username || "",
    email: employee.email || "",
    telephone: employee.telephone || "",
    role: employee.role || "secretaire",
    is_active: employee.is_active !== false,
    actif: employee.actif !== false,
    specialite: employee.specialite || "",
    experience: employee.experience || "",
  };
}

function isStrongPassword(value) {
  return value.length >= 8 && /[a-z]/.test(value) && /[A-Z]/.test(value) && /\d/.test(value) && /[^A-Za-z0-9]/.test(value);
}

function toEditValues(type, item) {
  if (type === "patient") return { telephone: item.telephone || "", adresse: item.adresse || "" };
  if (type === "medecin") return { specialite: item.specialite || "", telephone: item.telephone || "", experience: item.experience || "", disponible: item.disponible ?? true };
  if (type === "rdv") return { patient_id: item.patient_id || "", medecin_id: item.medecin_id || "", date: item.date || "", heure: item.heure?.slice(0, 5) || "", statut: item.statut || "en_attente" };
  return { matricule: item.matricule || "", type: item.type || "standard", disponible: item.disponible ?? true, chauffeur_id: item.chauffeur_id || "" };
}

function editEndpoint(type, id) {
  return ({ patient: `/patients/${id}/`, medecin: `/medecins/${id}/`, rdv: `/rendezvous/${id}/`, ambulance: `/ambulance/${id}/` })[type];
}

function deleteEndpoint(type, id) {
  return ({ patient: `/patients/delete/${id}/`, medecin: `/medecins/delete/${id}/`, rdv: `/rendezvous/${id}/delete/`, ambulance: `/ambulance/${id}/delete/` })[type];
}

function toUserOptions(users) {
  return users.map((user) => ({ value: user.id, label: `${user.username} (${user.role})` }));
}

function toEntityOptions(items) {
  return items.map((item) => ({ value: item.id, label: `${item.username || item.patient || item.id} #${item.id}` }));
}

function toDoctorOptions(items) {
  return items.map((item) => ({ value: item.id, label: `${item.username} - ${item.specialite || "General"} #${item.id}` }));
}

function toChauffeurOptions(items) {
  return items
    .filter((item) => item.role === "chauffeur" && item.personnel_id)
    .map((item) => ({ value: item.personnel_id, label: `${item.full_name || item.username} - ${item.username} #${item.personnel_id}` }));
}

function resourceLabel(type) {
  return ({ patient: "patient", medecin: "medecin", rdv: "rendez-vous", ambulance: "ambulance" })[type];
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function display(value) {
  return value || value === 0 ? value : "-";
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "-";
}

export default AdminDashboard;
