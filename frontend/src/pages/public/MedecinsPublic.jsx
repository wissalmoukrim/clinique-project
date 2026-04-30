import { useEffect, useState } from "react";
import { publicFetch } from "../../api/client";
import Navbar from "../../components/Navbar";

const FALLBACK_MEDECINS = [
  { id: "demo-1", username: "Dr Alaoui", specialite: "Cardiologie", experience: 12 },
  { id: "demo-2", username: "Dr Benali", specialite: "Pediatrie", experience: 8 },
  { id: "demo-3", username: "Dr Karimi", specialite: "Radiologie", experience: 10 },
];

function MedecinsPublic() {
  const [medecins, setMedecins] = useState([]);

  useEffect(() => {
    async function loadMedecins() {
      try {
        const data = await publicFetch("/medecins/");
        setMedecins(Array.isArray(data) && data.length ? data : FALLBACK_MEDECINS);
      } catch {
        setMedecins(FALLBACK_MEDECINS);
      }
    }

    loadMedecins();
  }, []);

  return (
    <>
      <Navbar publicMode />
      <main className="public-page">
        <h1>Nos medecins</h1>
        <div className="doctor-grid">
          {medecins.map((medecin, index) => (
            <article className="doctor-card" key={medecin.id}>
              <img
                src={`https://images.unsplash.com/photo-${index % 2 === 0 ? "1559839734-2b71ea197ec2" : "1612349317150-e413f6a5b16d"}?auto=format&fit=crop&w=500&q=80`}
                alt={medecin.username}
              />
              <div>
                <h2>{medecin.username}</h2>
                <p>{medecin.specialite || "Specialite medicale"}</p>
                <span>{medecin.experience || 5} ans d'experience</span>
              </div>
            </article>
          ))}
        </div>
      </main>
    </>
  );
}

export default MedecinsPublic;
