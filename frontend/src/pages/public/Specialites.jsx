import Navbar from "../../components/Navbar";

const SPECIALITES = [
  { nom: "Cardiologie", description: "Suivi cardiovasculaire, tension, ECG et prevention." },
  { nom: "Gynecologie", description: "Consultations de suivi, depistage et accompagnement." },
  { nom: "Pediatrie", description: "Soins et suivi medical des enfants." },
  { nom: "Chirurgie generale", description: "Avis chirurgical, suivi pre et post-operatoire." },
  { nom: "Radiologie", description: "Imagerie et examens de diagnostic." },
  { nom: "Medecine generale", description: "Consultations courantes et orientation medicale." },
];

function Specialites() {
  return (
    <>
      <Navbar publicMode />
      <main className="public-page">
        <h1>Specialites</h1>
        <div className="card-grid">
          {SPECIALITES.map((specialite) => (
            <article className="service-card" key={specialite.nom}>
              <h2>{specialite.nom}</h2>
              <p>{specialite.description}</p>
            </article>
          ))}
        </div>
      </main>
    </>
  );
}

export default Specialites;
