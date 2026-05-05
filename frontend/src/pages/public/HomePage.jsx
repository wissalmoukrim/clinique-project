import { Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import { IMAGES } from "../../assets/images";

const SERVICES = [
  { title: "Consultations specialisees", text: "Des parcours de soin coordonnes avec des medecins disponibles." },
  { title: "Rendez-vous en ligne", text: "Planifiez rapidement vos visites et suivez leur statut en toute simplicite." },
  { title: "Suivi securise", text: "Vos donnees medicales restent protegees par une authentification forte." },
];

const DOCTORS = [
  { name: "Dr Sara", specialty: "Cardiologie", image: IMAGES.doctorA },
  { name: "Dr Youssef", specialty: "Pediatrie", image: IMAGES.doctorB },
  { name: "Dr Salma", specialty: "Radiologie", image: IMAGES.doctorC },
];

function HomePage() {
  return (
    <>
      <Navbar publicMode />
      <main>
        <section
          className="hero"
          style={{ backgroundImage: `linear-gradient(90deg, rgba(7, 20, 45, 0.78) 0%, rgba(15, 23, 42, 0.62) 46%, rgba(37, 99, 235, 0.16) 100%), url(${IMAGES.clinicHero})` }}
        >
          <div className="hero-content">
            <p className="eyebrow">Clinique Medicale Elite</p>
            <h1>Votre santé, notre priorité</h1>
            <p>Prenez rendez-vous facilement et accédez à vos services médicaux en toute sécurité.</p>
            <div className="hero-actions">
              <Link className="primary-link" to="/prendre-rdv">Prendre RDV</Link>
              <Link className="secondary-link" to="/medecins-public">Voir les médecins</Link>
            </div>
          </div>
        </section>

        <section className="public-section">
          <div className="section-heading">
            <span>Services</span>
            <h2>Une experience fluide pour chaque etape du parcours patient</h2>
          </div>
          <div className="card-grid">
            {SERVICES.map((service) => (
              <article className="service-card" key={service.title}>
                <div className="service-icon">{service.title.slice(0, 1)}</div>
                <h3>{service.title}</h3>
                <p>{service.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="public-feature">
          <img src={IMAGES.consultation} alt="Consultation medicale" />
          <div>
            <span>Plateforme securisee</span>
            <h2>Une clinique connectee, sans perdre le contact humain</h2>
            <p>
              Les patients, medecins et equipes administratives disposent d'espaces adaptes a leurs besoins,
              avec des acces controles par role.
            </p>
          </div>
        </section>

        <section className="public-section">
          <div className="section-heading">
            <span>Equipe medicale</span>
            <h2>Des medecins disponibles pour vous accompagner</h2>
          </div>
          <div className="doctor-grid">
            {DOCTORS.map((doctor) => (
              <article className="doctor-card" key={doctor.name}>
                <img src={doctor.image} alt={doctor.name} />
                <div>
                  <h3>{doctor.name}</h3>
                  <span>{doctor.specialty}</span>
                  <Link className="secondary-link compact-link" to="/medecins-public">Voir profil</Link>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="cta-section">
          <div>
            <span>Besoin d'un rendez-vous ?</span>
            <h2>Votre prise en charge commence ici.</h2>
          </div>
          <Link className="primary-link" to="/prendre-rdv">Prendre RDV</Link>
        </section>

        <footer className="footer">
          <strong>Clinique Medicale Elite</strong>
          <span>Prise en charge rapide, accès sécurisé, équipe médicale qualifiée.</span>
        </footer>
      </main>
    </>
  );
}

export default HomePage;
