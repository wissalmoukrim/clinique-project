import { useState } from "react";
import Navbar from "../../components/Navbar";

function PrendreRdvPublic() {
  const [form, setForm] = useState({
    nom: "",
    telephone: "",
    specialite: "",
    date: "",
    heure: "",
  });
  const [message, setMessage] = useState("");

  const submit = (event) => {
    event.preventDefault();
    setMessage("Demande recue. Connectez-vous ou contactez l'accueil pour confirmer le rendez-vous.");
    setForm({ nom: "", telephone: "", specialite: "", date: "", heure: "" });
  };

  return (
    <>
      <Navbar publicMode />
      <main className="public-page">
        <section className="appointment-card">
          <h1>Prendre rendez-vous</h1>
          <form className="stack-form" onSubmit={submit}>
            <input placeholder="Nom complet" value={form.nom} onChange={(e) => setForm({ ...form, nom: e.target.value })} required />
            <input placeholder="Telephone" value={form.telephone} onChange={(e) => setForm({ ...form, telephone: e.target.value })} required />
            <select value={form.specialite} onChange={(e) => setForm({ ...form, specialite: e.target.value })} required>
              <option value="">Choisir specialite</option>
              <option>Cardiologie</option>
              <option>Gynecologie</option>
              <option>Pediatrie</option>
              <option>Radiologie</option>
            </select>
            <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} required />
            <input type="time" value={form.heure} onChange={(e) => setForm({ ...form, heure: e.target.value })} required />
            <button type="submit">Envoyer la demande</button>
          </form>
          {message && <p className="success-message">{message}</p>}
        </section>
      </main>
    </>
  );
}

export default PrendreRdvPublic;
