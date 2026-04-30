import { useState } from "react";
import { createPatient } from "./api";

function PatientForm({ refresh }) {
  const [form, setForm] = useState({
    nom: "",
    prenom: "",
  });

  const token = localStorage.getItem("access");
  const user = JSON.parse(localStorage.getItem("user"));

  // 🔐 RBAC FRONTEND
  if (!["admin", "secretaire"].includes(user.role)) {
    return null;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      await createPatient(form, token);
      setForm({ nom: "", prenom: "" });
      refresh();
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h3>Ajouter Patient</h3>

      <input
        type="text"
        placeholder="Nom"
        value={form.nom}
        onChange={(e) => setForm({ ...form, nom: e.target.value })}
      />

      <input
        type="text"
        placeholder="Prenom"
        value={form.prenom}
        onChange={(e) => setForm({ ...form, prenom: e.target.value })}
      />

      <button type="submit">Ajouter</button>
    </form>
  );
}

export default PatientForm;