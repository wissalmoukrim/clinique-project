import Navbar from "../../components/Navbar";
import { DOCTOR_IMAGES } from "../../assets/images";

const medecins = [
  { name: "Dr Sara", specialite: "Cardiologie", experience: 10, image: DOCTOR_IMAGES[0] },
  { name: "Dr Fahd", specialite: "Cardiologie", experience: 7, image: DOCTOR_IMAGES[1] },
  { name: "Dr Kenza", specialite: "Cardiologie", experience: 12, image: DOCTOR_IMAGES[2] },
  { name: "Dr Wael", specialite: "Gynécologie", experience: 9, image: DOCTOR_IMAGES[3] },
  { name: "Dr Youness", specialite: "Gynécologie", experience: 6, image: DOCTOR_IMAGES[4] },
  { name: "Dr Rayan", specialite: "Pédiatrie", experience: 11, image: DOCTOR_IMAGES[5] },
  { name: "Dr Nadia", specialite: "Pédiatrie", experience: 8, image: DOCTOR_IMAGES[6] },
  { name: "Dr Amine", specialite: "Pédiatrie", experience: 5, image: DOCTOR_IMAGES[7] },
  { name: "Dr Karim", specialite: "Radiologie", experience: 13, image: DOCTOR_IMAGES[8] },
  { name: "Dr Salma", specialite: "Radiologie", experience: 7, image: DOCTOR_IMAGES[9] },
  { name: "Dr Hassan", specialite: "Médecine générale", experience: 15, image: DOCTOR_IMAGES[10] },
  { name: "Dr Amal", specialite: "Médecine générale", experience: 9, image: DOCTOR_IMAGES[11] },
];

const specialites = [...new Set(medecins.map((medecin) => medecin.specialite))];

function MedecinsPublic() {
  return (
    <>
      <Navbar publicMode />
      <main className="public-page doctors-page">
        <div className="section-heading">
          <span>Equipe médicale</span>
          <h1>Nos médecins par spécialité</h1>
          <p>
            Une équipe pluridisciplinaire avec des profils expérimentés pour accompagner chaque parcours de soin.
          </p>
        </div>

        {specialites.map((specialite) => (
          <section className="specialty-section" key={specialite}>
            <div className="specialty-heading">
              <h2>{specialite}</h2>
              <span>{medecins.filter((medecin) => medecin.specialite === specialite).length} médecins</span>
            </div>

            <div className="doctor-grid">
              {medecins
                .filter((medecin) => medecin.specialite === specialite)
                .map((medecin) => (
                  <article className="doctor-card" key={medecin.name}>
                    <img src={medecin.image} alt={medecin.name} />
                    <div>
                      <h3>{medecin.name}</h3>
                      <p>{medecin.specialite}</p>
                      <span className="experience-badge">{medecin.experience} ans d'expérience</span>
                    </div>
                  </article>
                ))}
            </div>
          </section>
        ))}
      </main>
    </>
  );
}

export default MedecinsPublic;
