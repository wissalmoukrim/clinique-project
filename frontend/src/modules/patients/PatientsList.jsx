import { useEffect, useState } from "react";
import { getPatients, deletePatient } from "./api";
import PatientForm from "./PatientForm";

function PatientsList() {
  const [patients, setPatients] = useState([]);

  const token = localStorage.getItem("access");
  const user = JSON.parse(localStorage.getItem("user"));

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const data = await getPatients(token);
      setPatients(data);
    } catch (error) {
      console.error(error);
    }
  };

  // 🔐 RBAC DELETE
  const handleDelete = async (id) => {
    if (!["admin"].includes(user.role)) {
      alert("Non autorisé");
      return;
    }

    try {
      await deletePatient(id, token);
      fetchPatients();
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <h2>Patients</h2>

      {/* FORM */}
      <PatientForm refresh={fetchPatients} />

      {/* LIST */}
      <ul>
        {patients.map((p) => (
          <li key={p.id}>
            {p.nom} {p.prenom}

            {/* 🔐 bouton visible seulement admin */}
            {user.role === "admin" && (
              <button onClick={() => handleDelete(p.id)}>
                Supprimer
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default PatientsList;