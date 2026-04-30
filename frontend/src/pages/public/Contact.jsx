import Navbar from "../../components/Navbar";

function Contact() {
  return (
    <>
      <Navbar publicMode />
      <main className="public-page contact-grid">
        <section>
          <h1>Contact</h1>
          <p>Notre equipe d'accueil est disponible pour vous orienter et confirmer vos rendez-vous.</p>
          <div className="contact-card">
            <p><strong>Adresse:</strong> Avenue de la Sante, Casablanca</p>
            <p><strong>Telephone:</strong> +212 522 000 000</p>
            <p><strong>Email:</strong> contact@clinique-elite.ma</p>
          </div>
        </section>
        <section className="map-card">
          <h2>Localisation</h2>
          <p>Casablanca, Maroc</p>
          <div className="map-placeholder">Carte localisation</div>
        </section>
      </main>
    </>
  );
}

export default Contact;
