import { useState } from "react";
import { publicFetch } from "../../api/client";
import Navbar from "../../components/Navbar";

function PrendreRdvPublic() {
  const [form, setForm] = useState({
    nom: "",
    email: "",
    telephone: "",
    specialite: "",
    date: "",
    heure: "",
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [credentials, setCredentials] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setMessage("");
    setError("");
    setCredentials(null);
    setLoading(true);

    try {
      const data = await publicFetch("/rendezvous/", {
        method: "POST",
        body: form,
      });

      const temporaryPassword = data.password_temporaire || data.password;

      if (data.account_created && temporaryPassword) {
        setMessage("Un compte patient a ete cree pour vous. Utilisez ces informations pour vous connecter.");
        setCredentials({ username: data.username, password: temporaryPassword });
      } else {
        setMessage("Votre rendez-vous a ete enregistre. Vous pouvez vous connecter avec votre compte patient existant.");
      }

      setForm({ nom: "", email: "", telephone: "", specialite: "", date: "", heure: "" });
    } catch (err) {
      setError(err.message || "Impossible de creer le rendez-vous.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar publicMode />
      <main className="public-page">
        <section className="appointment-card">
          <h1>Prendre rendez-vous</h1>
          <form className="stack-form" onSubmit={submit}>
            <input placeholder="Nom complet" value={form.nom} onChange={(e) => setForm({ ...form, nom: e.target.value })} required />
            <input type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
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
            <button type="submit" disabled={loading}>{loading ? "Envoi..." : "Envoyer la demande"}</button>
          </form>
          {error && <p className="error-message">{error}</p>}
          {message && <p className="success-message">{message}</p>}
          {credentials && (
            <div className="credentials-box">
              <p><strong>Username :</strong> {credentials.username}</p>
              <p><strong>Mot de passe temporaire :</strong> {credentials.password}</p>
            </div>
          )}
        </section>
      </main>
    </>
  );
}

export default PrendreRdvPublic;
