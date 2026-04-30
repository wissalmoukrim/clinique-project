import { Link } from "react-router-dom";
import Navbar from "../../components/Navbar";

const SERVICES = [
  "Consultations specialisees",
  "Rendez-vous en ligne",
  "Hospitalisation et suivi",
  "Ambulance et urgences",
  "Facturation et paiements",
  "Accueil visiteurs securise",
];

function HomePage() {
  return (
    <>
      <Navbar publicMode />
      <main>
        <section className="hero">
          <div className="hero-content">
            <p className="eyebrow">Clinique Medicale Elite</p>
            <h1>Une gestion moderne pour une clinique plus proche de ses patients</h1>
            <p>
              Une plateforme complete pour les patients, medecins et equipes internes:
              rendez-vous, consultations, hospitalisation, facturation et suivi operationnel.
            </p>
            <div className="hero-actions">
              <Link className="primary-link" to="/prendre-rdv">Prendre RDV</Link>
              <Link className="secondary-link" to="/medecins-public">Voir les medecins</Link>
            </div>
          </div>
        </section>

        <section className="public-section">
          <h2>Services de la clinique</h2>
          <div className="card-grid">
            {SERVICES.map((service) => (
              <article className="service-card" key={service}>
                <h3>{service}</h3>
                <p>Un service organise, securise et integre au dossier de la clinique.</p>
              </article>
            ))}
          </div>
        </section>
      </main>
    </>
  );
}

export default HomePage;
